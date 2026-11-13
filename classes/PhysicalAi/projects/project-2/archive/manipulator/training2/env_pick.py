"""스테이션 집기 (사용자 2026-11-12): 스테이션 박스가 차체와 평행하지 않고 (±20°) 조금 떨어져 있어도 (앞면 틈 1–12 cm) 박스 위 퍽을 집어 올림.
보정 학습 (r1–r4) 은 버림 → 툭 건드리기 (env_nudge) 처럼 짧은 동작만 직접 배우는 작은 정책.

에피소드: 장면 묶음 (gen_pick_bank.py) 하나 — 로봇 자세 · 박스 위 퍽 2–3 개 (선 네모 · 원기둥 · 누운 네모) · 작업 퍽 (J1 에서 가장 가까운) ·
          시작 자세 (작업 퍽 쥘 자리 60 mm 위, 손 수직 또는 15–45° 기울임, 그리퍼 열림).
행동: 관절 5 개 속도 + 그리퍼 (> 0 열림, Training2Env 와 같음).
성공: 퍽을 쥔 채 처음보다 30 mm 넘게 들어 올려 10 스텝 이어짐 (다른 퍽 · 몸체 · 박스에 안 닿음).
바로 실패 (사용자 2026-11-12: 바닥에서 아예 뜨면 안 됨): 바퀴 높이 차 > 1 mm, 심한 충돌, 퍽이 박스에서 밀려남 · 떨어짐.
"""
import numpy as np
import torch

from isaaclab.envs import DirectRLEnv
from isaaclab.utils import configclass
from isaaclab.utils.math import matrix_from_quat, quat_from_euler_xyz

from cfg import BOX_TOP, GRIPPER_OPEN, N_CYL, PUCK_SIZE, EnvCfg
from env import Training2Env


@configclass
class PickEnvCfg(EnvCfg):
    episode_length_s = 4.0
    observation_space = 91                # Training2Env 80 + 11
    max_joint_speed = 0.70                # [rad/s] 툭 건드리기와 같음 (처음엔 안정적으로)
    bank: str = 'logs/pick_bank_v2.npz'
    # 커리큘럼 (2026-11-12 p1 실패: 퍽 위에서 맴돌기만 → 쉬운 것부터): 시작 = 쥘 자세에서 10 mm 위 ~ 지금 단계 높이 (무작위), 성공률 넘으면 10 mm 씩 올림
    start_min: float = 0.010
    start_max: float = 0.060
    start_step: float = 0.010
    curr_window: int = 512
    curr_success: float = 0.5
    lift: float = 0.030                   # 들어 올릴 높이
    hold_steps: int = 10
    lift_fail_mm: float = 1.0             # 바퀴 높이 차 (빠른 팔 동작에서도 0.6–0.9 mm 는 나옴, 2026-11-12 측정)
    # 보상
    success: float = 10.0
    fail: float = -5.0                    # 바퀴 뜸 · 퍽 밀려남
    grasp: float = 2.0
    reach: float = 100.0                  # 손끝 → 쥘 자리 거리 줄인 만큼 [/m] (p1 10 → 다가가지 않음)
    in_hand: float = 2.0                  # 처음으로 퍽이 손가락 사이 (쥘 자리 12 mm 안)
    raise_: float = 20.0                  # 쥔 뒤 올린 만큼 [/m]
    tilt: float = -0.5                    # 몸체 기울기 [°] 당 (0.45° 넘은 만큼)
    time: float = -0.01


class Training2PickEnv(Training2Env):
    cfg: PickEnvCfg

    def __init__(self, cfg: PickEnvCfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        dev, N = self.device, self.num_envs
        b = np.load(cfg.bank)
        t = lambda a: torch.tensor(a, dtype=torch.float32, device=dev)
        self.b_robot, self.b_pucks, self.b_q0, self.b_q1 = t(b['robot']), t(b['pucks']), t(b['q0']), t(b['q1'])
        from collections import deque
        self.level = cfg.start_min
        self.recent_p = deque(maxlen=cfg.curr_window)
        self.reached = torch.zeros(N, dtype=torch.bool, device=dev)
        self.n_bank = len(self.b_robot)
        self.bi = torch.zeros(N, dtype=torch.long, device=dev)
        self.fixed = None                           # 평가: 장면 번호 고정
        self.wheel_ids = [i for i, nm in enumerate(self.robot.body_names) if 'wheel' in nm.lower()]
        self.z0 = torch.zeros(N, device=dev)
        self.hold = torch.zeros(N, dtype=torch.long, device=dev)
        self.prev_phi_p = torch.full((N,), float('nan'), device=dev)
        self.body_tilt = torch.zeros(N, device=dev); self.wheel_lift = torch.zeros(N, device=dev)
        self.puck_half = torch.zeros(N, device=dev)
        print(f'[env_pick] 장면 {self.n_bank} 개', flush=True)

    def set_fixed(self, ids):
        self.fixed = torch.as_tensor(list(ids), device=self.device)

    # ------------------------------------------------------------------ 리셋
    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ids = torch.as_tensor(env_ids, device=self.device)
        self._log_and_curriculum(ids)
        DirectRLEnv._reset_idx(self, ids)
        dev, n, o = self.device, len(ids), self.scene.env_origins[ids]
        bi = self.fixed[ids % len(self.fixed)] if self.fixed is not None else torch.randint(0, self.n_bank, (n,), device=dev)
        self.bi[ids] = bi
        rob, pk = self.b_robot[bi], self.b_pucks[bi]
        # 시작 = 쥘 자세 q1 → 60 mm 위 q0 사이 (관절 보간, 짧은 거리라 거의 곧은 선): 높이 h ∈ [start_min, level]
        h = self.cfg.start_min + torch.rand(n, device=dev) * (self.level - self.cfg.start_min)
        f = (h / 0.060)[:, None]
        q0 = self.b_q1[bi] + f * (self.b_q0[bi] - self.b_q1[bi])
        # 적재함: 무작위로 참 (집기와 상관 없지만 몸체 무게 · 실제 모습)
        self.stored[ids] = torch.rand(n, 12, device=dev) < torch.rand(n, 1, device=dev)
        self.task_store[ids] = True
        self.on_box[ids] = False; self.cyl_on[ids] = False
        zero = torch.zeros(n, device=dev)
        up = torch.tensor([0, 0, 1.0], device=dev)
        for i in range(12):
            self.stored_p0[ids, i] = self.stored_local[i]
            self.stored_up0[ids, i] = up
        # 작업 퍽 (맨 앞)
        shape = pk[:, 0, 3].long()
        lying = shape == 2
        self.work_is_cyl[ids] = shape == 1
        half = torch.where(lying, PUCK_SIZE[0] / 2, PUCK_SIZE[2] / 2)
        self.puck_half[ids] = half
        pos = torch.stack([pk[:, 0, 0], pk[:, 0, 1], BOX_TOP + half + 5e-4], -1)
        quat = quat_from_euler_xyz(torch.where(lying, np.pi / 2, 0.0), zero, pk[:, 0, 2])   # 누운 = x 축으로 90° (긴 축 = 박스 yaw 방향)
        self.src[ids] = pos
        self.dst[ids] = pos + torch.tensor([0, 0, self.cfg.lift], device=dev)
        self.src_cell[ids], self.dst_cell[ids] = -1, -1
        unit = torch.tensor([0, 0, 0, 1.0], device=dev)
        cyl = self.work_is_cyl[ids][:, None]
        for obj, mine, park in ((self.work_b, ~cyl, [-0.55, 0.42, 0.03]), (self.work_c, cyl, [-0.55, 0.48, 0.03])):
            p_ = torch.where(mine, o + pos, o + torch.tensor(park, device=dev))
            obj.write_root_pose_to_sim_index(root_pose=torch.cat([p_, torch.where(mine, quat, unit.expand(n, 4))], -1), env_ids=ids)
            obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev), env_ids=ids)
        # 나머지 퍽: 네모 · 누운 = 빈 칸 퍽 (kinematic, on_box), 원기둥 = cyl (선 것만)
        for j in range(n):
            e = int(ids[j]); free = [k for k in range(12) if not bool(self.stored[e, k])][::-1]; nc = 0
            for m in range(1, 3):
                if torch.isnan(pk[j, m, 0]):
                    continue
                x, y, yw, s = pk[j, m].tolist()
                if s == 1 and nc < N_CYL:
                    self.cyl_on[e, nc] = True; self.cyl_pos[e, nc] = torch.tensor([x, y, BOX_TOP + PUCK_SIZE[2] / 2 + 5e-4], device=dev); nc += 1
                elif free:
                    k = free.pop(); ly = s == 2
                    self.on_box[e, k] = True
                    self.box_pos[e, k] = torch.tensor([x, y, BOX_TOP + (PUCK_SIZE[0] if ly else PUCK_SIZE[2]) / 2 + 5e-4], device=dev)
                    self.box_quat[e, k] = quat_from_euler_xyz(torch.tensor([np.pi / 2 if ly else 0.0], device=dev), torch.zeros(1, device=dev),
                                                              torch.tensor([yw], device=dev))[0]
        # 로봇: 장면 자세 (박스 반대로 돌림 · 옮김), 시작 자세, 그리퍼 열림
        r = self.robot
        rq = quat_from_euler_xyz(zero, zero, rob[:, 2])
        rp = o + torch.stack([rob[:, 0], rob[:, 1], zero], -1)
        r.write_root_pose_to_sim_index(root_pose=torch.cat([rp, rq], -1), env_ids=ids)
        r.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev), env_ids=ids)
        q = r.data.default_joint_pos.torch[ids].clone()
        q[:, self.arm_ids] = q0
        q[:, self.grip_ids] = GRIPPER_OPEN       # 열린 채 시작 (닫힌 손가락으로 리셋하면 퍽 안에 겹쳐 생겨 튕김 → 몸체 앞이 1–2 mm 들림, p2)
        r.write_joint_position_to_sim_index(position=q, env_ids=ids)
        r.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q), env_ids=ids)
        self.q_target[ids] = q0
        self.grip_target[ids] = GRIPPER_OPEN
        for k_ in ('grasped', 'ever_grasped', 'placed'):
            getattr(self, k_)[ids] = False
        self.clean[ids] = True
        self.hold[ids] = 0
        self.reached[ids] = False
        self.z0[ids] = o[:, 2] + pos[:, 2]
        self.prev_phi_p[ids] = float('nan')
        self.prev_actions[ids] = 0
        for v in self.ep_stats.values():
            v[ids] = 0
        self.ep_stats['min_clear'][ids] = 1.0
        self._follow_robot()
        self._stale = True

    # ------------------------------------------------------------------ 상태 · 끝
    def _body(self):
        bz = matrix_from_quat(self.robot.data.root_quat_w.torch)[:, :, 2]
        self.body_tilt = torch.rad2deg(torch.acos(bz[:, 2].clamp(-1, 1)))
        wz = self.robot.data.body_pos_w.torch[:, self.wheel_ids, 2]
        self.wheel_lift = (wz.amax(1) - wz.amin(1)) * 1000

    def _target(self):
        """쥘 자리 = 퍽 윗면 13 mm 아래 (누운 퍽도 지금 자세의 윗면)."""
        upz = self.work_up[:, 2].abs()
        h = 0.03 * upz + 0.015 * (1 - upz ** 2).clamp(min=0).sqrt()
        return self.work_w + torch.stack([torch.zeros_like(h), torch.zeros_like(h), h - 0.013], -1)

    def _get_dones(self):
        self._compute()
        self._body()
        self.ev['bad'] = self._bad_state()
        o = self.scene.env_origins
        up = self.work_w[:, 2] - self.z0
        ok = self.grasped & (up > self.cfg.lift)
        self.hold = torch.where(ok, self.hold + 1, torch.zeros_like(self.hold))
        self.ev['success'] = self.hold >= self.cfg.hold_steps
        moved = ((self.work_w - o - self.src)[:, :2].norm(dim=-1) > 0.03) & ~self.ever_grasped
        fell = self.work_w[:, 2] - o[:, 2] < BOX_TOP - 0.005
        self.ev['lifted'] = self.wheel_lift > self.cfg.lift_fail_mm
        self.ev['knock'] = moved | fell
        terminated = self.ev['success'] | self.ev['severe'] | self.ev['bad'] | self.ev['lifted'] | self.ev['knock'] | self.ev['drop']
        if self.no_terminate:
            terminated = torch.zeros_like(terminated)
        return terminated, self.episode_length_buf >= self.max_episode_length - 1

    def _get_rewards(self):
        rw, ev, cf = self.cfg.reward, self.ev, self.cfg
        d = (self._target() - self.grasp_w).norm(dim=-1)
        up = (self.work_w[:, 2] - self.z0).clamp(min=0, max=cf.lift)
        phi = torch.where(self.ever_grasped, cf.raise_ * up, -cf.reach * d)
        same = ~torch.isnan(self.prev_phi_p) & (self.ever_grasped == getattr(self, '_pg', self.ever_grasped))
        shaping = torch.where(same, phi - self.prev_phi_p, torch.zeros_like(phi))
        self.prev_phi_p, self._pg = phi, self.ever_grasped.clone()
        coll = ev['collision'].float()
        self.clean &= ~ev['collision']
        self.ep_stats['collision_steps'] += coll
        self.ep_stats['min_clear'] = torch.minimum(self.ep_stats['min_clear'], self.d_min)
        a, pa = self.actions, self.prev_actions
        inh = (d < 0.012) & ~self.reached
        self.reached |= d < 0.012
        rew = (shaping + cf.in_hand * inh.float() + rw.collision * coll + rw.terminate_collision * ev['severe'].float()
               + cf.fail * (ev['lifted'] | ev['knock'] | ev['drop']).float()
               + cf.grasp * ev['grasp_new'].float() + cf.success * (ev['success'] & self.clean).float()
               + cf.tilt * (self.body_tilt - 0.45).clamp(min=0)
               + rw.action_rate * (a - pa).square().sum(1) + cf.time)
        self.prev_actions = a.clone()
        return torch.nan_to_num(rew, nan=0.0, posinf=0.0, neginf=0.0)

    def _get_observations(self):
        base = super()._get_observations()
        r, o = self.robot, self.scene.env_origins
        Rb = matrix_from_quat(r.data.root_quat_w.torch).transpose(1, 2)
        pb = r.data.root_pos_w.torch
        to_b = lambda v: torch.einsum('nij,nj->ni', Rb, v)
        box = to_b(o + self.box_c[0] - pb)
        yaw_b = torch.atan2(Rb[:, 1, 0], Rb[:, 0, 0])                          # 박스 yaw (로봇 기준) = − 로봇 yaw
        # 가장 가까운 다른 퍽 (박스 위)
        ob = torch.cat([torch.where(self.on_box[..., None], o[:, None] + self.box_pos, torch.full_like(self.box_pos, 9.0)),
                        torch.where(self.cyl_on[..., None], o[:, None] + self.cyl_pos, torch.full_like(self.cyl_pos, 9.0))], 1)
        dd = (ob - self.work_w[:, None]).norm(dim=-1)
        near = ob[torch.arange(self.num_envs, device=self.device), dd.argmin(1)]
        near_rel = torch.where((dd.amin(1) < 1.0)[:, None], to_b(near - self.grasp_w), torch.zeros_like(near))
        extra = torch.cat([box, torch.sin(4 * yaw_b)[:, None], torch.cos(4 * yaw_b)[:, None], (self.puck_half * 20)[:, None],
                           (self.body_tilt / 2)[:, None], (self.wheel_lift / 2)[:, None], near_rel], -1)
        return {'policy': torch.cat([base['policy'], torch.nan_to_num(extra).clamp(-10, 10)], -1), 'critic': base['critic']}

    def _log_and_curriculum(self, ids):
        if not self.dist:
            return
        ev = self.ev
        log = self.extras.setdefault('log', {})
        log['Pick/success'] = ev['success'][ids].float().mean()
        log['Pick/clean_success'] = (ev['success'][ids] & self.clean[ids]).float().mean()
        log['Pick/grasped'] = self.ever_grasped[ids].float().mean()
        log['Pick/lifted_fail'] = ev.get('lifted', self.clean)[ids].float().mean() if 'lifted' in ev else torch.tensor(0.0)
        log['Pick/knock'] = ev['knock'][ids].float().mean() if 'knock' in ev else torch.tensor(0.0)
        log['Pick/collision_free'] = self.clean[ids].float().mean()
        log['Pick/steps'] = self.episode_length_buf[ids].float().mean()
        log['Pick/start_mm'] = torch.tensor(self.level * 1000)
        if self.fixed is None:
            self.recent_p.extend(ev['success'][ids].float().tolist())
            if len(self.recent_p) == self.recent_p.maxlen and np.mean(self.recent_p) > self.cfg.curr_success and self.level < self.cfg.start_max - 1e-6:
                self.level = min(self.level + self.cfg.start_step, self.cfg.start_max); self.recent_p.clear()
                print(f'[env_pick] 커리큘럼: 시작 높이 최대 {self.level * 1000:.0f} mm', flush=True)
        if self.record is not None:
            for i in ids.tolist():
                self.record.append({'env': i, 'bank': int(self.bi[i]), 'success': bool(ev['success'][i]), 'clean': bool(self.clean[i]),
                                    'grasped': bool(self.ever_grasped[i]), 'lifted': bool(ev.get('lifted', self.clean)[i]) if 'lifted' in ev else False,
                                    'knock': bool(ev['knock'][i]) if 'knock' in ev else False, 'steps': int(self.episode_length_buf[i])})
