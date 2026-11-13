"""학습2 툭 건드리기 (사용자 2026-11-11): 적재함 칸에 틀어진 채 들어간 퍽을 그 자리에서 살짝 건드려 똑바로 세움.
박스로 가져가 다시 쥐는 복구 (store_recover) 는 번거롭고 오래 걸림 → 이 짧은 동작을 강화학습으로 (성공을 겪으며) 배움.

에피소드: 팔은 방금 놓고 손 뺀 자세 (칸 바로 위 30 mm, 손 수직, 손가락 닫힘) · 퍽은 칸 안에서 무작위로 틀어짐
          (면 돌아감 · 기욺 · 턱에 걸쳐 뜸 · 한쪽 쏠림, 15 % 는 이미 바름) · 옆 칸은 무작위로 참.
행동: 관절 5 개 속도 (Training2Env 와 같음, max_joint_speed). 그리퍼는 닫은 채.
성공: 퍽이 칸 바닥에 앉고 (높이 2 mm 안) 기울기 5° · 면 10° 안 · 중심 3 mm 안 + 손끝이 퍽 윗면 15 mm 넘게 위, 10 스텝 이어짐.
감점: 다른 퍽 · 몸체 · 박스에 닿음 (Training2Env 와 같은 판정, 자기 칸 벽은 괜찮음), 퍽을 칸 밖으로 밀어냄, 시간.
"""
import numpy as np
import torch

from isaaclab.envs import DirectRLEnv
from isaaclab.utils import configclass
from isaaclab.utils.math import euler_xyz_from_quat, matrix_from_quat, quat_from_matrix

from cfg import CELLS, GRIPPER_CLOSE, GRIPPER_RESET, EnvCfg
from env import Training2Env


@configclass
class NudgeEnvCfg(EnvCfg):
    episode_length_s = 4.0                # 한 번 건드리기 최대 (사용자: 처음엔 안정적으로, 그다음 더 빠르게 비교)
    observation_space = 86                # Training2Env 80 + 6
    max_joint_speed = 0.70                # [rad/s] (빠르게 비교할 때 올림)
    perfect_frac: float = 0.15            # 이미 바른 퍽 비율 (건드리지 않고 빠지는 것도 배움)
    max_yaw_deg: float = 35.0
    max_tilt_deg: float = 10.0
    drop_mm: tuple = (1.0, 4.0)           # 퍽 바닥이 칸 턱 (rim) 위 이만큼에서 떨어짐 (턱을 뚫고 시작하면 튕겨 나감)
    shift_mm: tuple = (2.0, 6.0)          # 칸 중심에서 비킨 거리 (넣을 때 손 안 퍽 비킴과 비슷)
    min_yaw_deg: float = 5.0
    hold_steps: int = 10
    # 보상
    success: float = 10.0
    out: float = -5.0                     # 퍽을 칸 밖으로 밀어냄
    shaping: float = 1.0                  # (기울기 · 면 · 높이 · 쏠림) 줄인 만큼
    approach: float = 0.5                 # 퍽이 틀어져 있을 때 손끝 → 퍽 윗면 거리 줄인 만큼
    time: float = -0.01


class Training2NudgeEnv(Training2Env):
    cfg: NudgeEnvCfg

    def __init__(self, cfg: NudgeEnvCfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        dev, N = self.device, self.num_envs
        import pathgen as pg
        # 칸마다 시작 자세: 칸 위 (선 퍽 윗면 + 30 mm), 손 수직, 닫힘축 = 옆 칸 퍽이 없는 쪽 (다 찬 경우 기준)
        starts = []
        for c in CELLS:
            xy = np.array(pg.CELLS[c]['xy'])
            cax = pg.feasible_sign(np.r_[xy, pg.TOP + 0.03], pg.choose_close(c, [o for o in CELLS if o != c]), pg.team_unfold()[0][-1])
            q, e = pg.ik(np.r_[xy, pg.TOP + 0.03], np.array([0, 0, -1.0]), cax, pg.team_unfold()[0][-1])
            starts.append(pg.to_cmd(q))
        self.start_q = torch.tensor(np.array(starts), dtype=torch.float32, device=dev)
        self.cell = torch.zeros(N, dtype=torch.long, device=dev)
        self.ok_steps = torch.zeros(N, dtype=torch.long, device=dev)
        self.prev_phi_n = torch.full((N,), float('nan'), device=dev)
        self.cell_yaw = euler_xyz_from_quat(self.cell_quat)[2]

    # ------------------------------------------------------------------ 리셋
    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ids = torch.as_tensor(env_ids, device=self.device)
        self._log_and_curriculum(ids)
        DirectRLEnv._reset_idx(self, ids)
        dev, n, o, cf = self.device, len(ids), self.scene.env_origins[ids], self.cfg
        cell = torch.randint(0, 12, (n,), device=dev)
        occ = torch.rand(n, 12, device=dev) < torch.rand(n, 1, device=dev)          # 옆 칸 무작위로 참 (env 마다 비율도 무작위)
        occ[torch.arange(n), cell] = False
        self.cell[ids] = cell
        self.task_store[ids] = True
        self.stored[ids] = occ
        for f in ('on_box', 'cyl_on'):
            getattr(self, f)[ids] = False
        self.work_is_cyl[ids] = torch.rand(n, device=dev) < 0.3
        seat = self.stored_local[cell]
        self.src[ids], self.dst[ids] = seat, seat
        self.src_cell[ids], self.dst_cell[ids] = -1, cell
        up = torch.tensor([0, 0, 1.0], device=dev)
        for i in range(12):
            self.stored_p0[ids, i] = self.stored_local[i]
            self.stored_up0[ids, i] = up
        # 틀어진 퍽: 면 돌림 · 기울임 (무작위 수평축) · 떨어뜨릴 높이 · 쏠림 → 첫 스텝들에 물리로 그 자리에 걸쳐 앉음
        perfect = torch.rand(n, device=dev) < cf.perfect_frac
        ysgn = torch.where(torch.rand(n, device=dev) < 0.5, -1.0, 1.0)
        yaw = self.cell_yaw[cell] + torch.where(perfect, 0.0, ysgn * torch.deg2rad(cf.min_yaw_deg + torch.rand(n, device=dev) * (cf.max_yaw_deg - cf.min_yaw_deg)))
        tilt = torch.where(perfect, 0.0, torch.rand(n, device=dev) * np.radians(cf.max_tilt_deg))
        ax = torch.rand(n, device=dev) * 2 * np.pi
        import pathgen as pg
        rim = pg.RC['rim_z'] - pg.RC['floor_z']                                   # 칸 턱 높이 (바닥에서)
        dz = torch.where(perfect, 0.0005, rim + (cf.drop_mm[0] + torch.rand(n, device=dev) * (cf.drop_mm[1] - cf.drop_mm[0])) / 1000)
        ang = torch.rand(n, device=dev) * 2 * np.pi
        r_ = (cf.shift_mm[0] + torch.rand(n, device=dev) * (cf.shift_mm[1] - cf.shift_mm[0])) / 1000
        dxy = torch.where(perfect[:, None], 0.0, torch.stack([torch.cos(ang), torch.sin(ang)], -1) * r_[:, None])
        Rz = torch.zeros(n, 3, 3, device=dev); Rz[:, 0, 0] = torch.cos(yaw); Rz[:, 0, 1] = -torch.sin(yaw); Rz[:, 1, 0] = torch.sin(yaw); Rz[:, 1, 1] = torch.cos(yaw); Rz[:, 2, 2] = 1
        k = torch.stack([torch.cos(ax), torch.sin(ax), torch.zeros_like(ax)], -1)
        K = torch.zeros(n, 3, 3, device=dev); K[:, 0, 2] = k[:, 1]; K[:, 1, 2] = -k[:, 0]; K[:, 2, 0] = -k[:, 1]; K[:, 2, 1] = k[:, 0]
        Rt = torch.eye(3, device=dev)[None] + torch.sin(tilt)[:, None, None] * K + (1 - torch.cos(tilt))[:, None, None] * (K @ K)
        quat = quat_from_matrix(Rt @ Rz)
        pos = seat + torch.cat([dxy, dz[:, None]], -1) + torch.stack([torch.zeros(n, device=dev), torch.zeros(n, device=dev), 0.015 * torch.sin(tilt)], -1)
        unit = torch.tensor([0, 0, 0, 1.0], device=dev)
        cyl = self.work_is_cyl[ids][:, None]
        for obj, mine, park in ((self.work_b, ~cyl, [-0.55, 0.42, 0.03]), (self.work_c, cyl, [-0.55, 0.48, 0.03])):
            p_ = torch.where(mine, o + pos, o + torch.tensor(park, device=dev))
            obj.write_root_pose_to_sim_index(root_pose=torch.cat([p_, torch.where(mine, quat, unit.expand(n, 4))], -1), env_ids=ids)
            obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev), env_ids=ids)
        # 로봇: 칸 위 시작 자세, 손가락 닫힘
        r = self.robot
        r.write_root_pose_to_sim_index(root_pose=torch.cat([o, unit.repeat(n, 1)], -1), env_ids=ids)
        r.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev), env_ids=ids)
        q = r.data.default_joint_pos.torch[ids].clone()
        q[:, self.arm_ids] = self.start_q[cell]
        q[:, self.grip_ids] = GRIPPER_RESET
        r.write_joint_position_to_sim_index(position=q, env_ids=ids)
        r.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q), env_ids=ids)
        self.q_target[ids] = self.start_q[cell]
        self.grip_target[ids] = GRIPPER_CLOSE
        for k_ in ('grasped', 'ever_grasped', 'placed'):
            getattr(self, k_)[ids] = False
        self.clean[ids] = True
        self.ok_steps[ids] = 0
        self.prev_phi_n[ids] = float('nan')
        self.prev_actions[ids] = 0
        for v in self.ep_stats.values():
            v[ids] = 0
        self.ep_stats['min_clear'][ids] = 1.0
        self._follow_robot()
        self._stale = True

    def _pre_physics_step(self, actions):
        super()._pre_physics_step(actions)
        self.grip_target[:] = GRIPPER_CLOSE

    # ------------------------------------------------------------------ 상태 · 끝
    def _puck_err(self):
        o = self.scene.env_origins
        seat = self.stored_local[self.cell]
        rel = self.work_w - o - seat
        high = rel[:, 2]
        xy = rel[:, :2]
        tilt = torch.rad2deg(torch.acos(self.work_up[:, 2].clamp(-1, 1)))
        wq = self._work_state()[1]
        yaw = euler_xyz_from_quat(wq)[2] - self.cell_yaw[self.cell]
        yaw = torch.remainder(yaw + np.pi / 4, np.pi / 2) - np.pi / 4
        yaw = torch.where(self.work_is_cyl, torch.zeros_like(yaw), yaw)
        return high, xy, tilt, torch.rad2deg(yaw)

    def _get_dones(self):
        self._compute()
        self.ev['bad'] = self._bad_state()
        high, xy, tilt, yaw = self._puck_err()
        top = self.work_w[:, 2] + 0.03 * self.work_up[:, 2]
        hand_clear = (self.grasp_w[:, 2] - top) > 0.015
        good = (high.abs() < 0.002) & (tilt < 5) & (yaw.abs() < 10) & (xy.norm(dim=-1) < 0.003)
        self.ok_steps = torch.where(good & hand_clear, self.ok_steps + 1, torch.zeros_like(self.ok_steps))
        self.ev['success'] = self.ok_steps >= self.cfg.hold_steps
        self.ev['out'] = (xy.norm(dim=-1) > 0.012) | (high < -0.010) | (high > 0.040)
        self.puck_good = good
        terminated = self.ev['success'] | self.ev['severe'] | self.ev['out'] | self.ev['bad']
        if self.no_terminate:
            terminated = torch.zeros_like(terminated)
        return terminated, self.episode_length_buf >= self.max_episode_length - 1

    def _get_rewards(self):
        rw, ev, cf = self.cfg.reward, self.ev, self.cfg
        high, xy, tilt, yaw = self._puck_err()
        top = self.work_w + 0.03 * self.work_up
        phi = -(tilt / 10 + yaw.abs() / 10 + high.clamp(min=0) * 1000 / 3 + xy.norm(dim=-1) * 1000 / 3) \
              - cf.approach * torch.where(self.puck_good, torch.zeros_like(tilt), (top - self.grasp_w).norm(dim=-1) * 10)
        shaping = torch.where(torch.isnan(self.prev_phi_n), torch.zeros_like(phi), phi - self.prev_phi_n)
        self.prev_phi_n = phi
        coll = ev['collision'].float()
        self.clean &= ~ev['collision']
        self.ep_stats['collision_steps'] += coll
        self.ep_stats['min_clear'] = torch.minimum(self.ep_stats['min_clear'], self.d_min)
        a, pa = self.actions, self.prev_actions
        rew = (cf.shaping * shaping + rw.collision * coll + rw.terminate_collision * ev['severe'].float()
               + cf.out * ev['out'].float() + cf.success * (ev['success'] & self.clean).float()
               + rw.action_rate * (a - pa).square().sum(1) + cf.time)
        self.prev_actions = a.clone()
        return torch.nan_to_num(rew, nan=0.0, posinf=0.0, neginf=0.0)

    def _get_observations(self):
        base = super()._get_observations()
        high, xy, tilt, yaw = self._puck_err()
        y4 = torch.deg2rad(yaw) * 4
        extra = torch.stack([torch.sin(y4), torch.cos(y4), high * 100, tilt / 20, xy[:, 0] * 100, xy[:, 1] * 100], -1)
        return {'policy': torch.cat([base['policy'], torch.nan_to_num(extra).clamp(-10, 10)], -1), 'critic': base['critic']}

    def _log_and_curriculum(self, ids):
        if not self.dist:
            return
        log = self.extras.setdefault('log', {})
        log['Nudge/success'] = self.ev['success'][ids].float().mean()
        log['Nudge/clean_success'] = (self.ev['success'][ids] & self.clean[ids]).float().mean()
        log['Nudge/collision_free'] = self.clean[ids].float().mean()
        log['Nudge/out'] = self.ev.get('out', torch.zeros_like(self.clean))[ids].float().mean()
        log['Nudge/steps'] = self.episode_length_buf[ids].float().mean()
        if self.record is not None:
            for i in ids.tolist():
                self.record.append({'env': i, 'cell': CELLS[int(self.cell[i])], 'success': bool(self.ev['success'][i]), 'clean': bool(self.clean[i]),
                                    'out': bool(self.ev.get('out', self.clean)[i]) if 'out' in self.ev else False, 'steps': int(self.episode_length_buf[i])})
