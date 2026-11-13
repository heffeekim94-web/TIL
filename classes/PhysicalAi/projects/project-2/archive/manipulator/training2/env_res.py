"""학습2 보정 학습 환경: 혁무님 방식 기본 경로 (library.py 로 미리 계산) 를 따라가며, 정책은 관절 목표에 작은 보정만 더함.
기본 경로만으로는 못 하는 것 = 손 안 퍽 비킴 · 방향 (칸 1 mm 여유), 먼 줄 놓기 오차, 팔 처짐 · 흔들림 → 보정이 배움.

에피소드: 라이브러리에서 작업 하나 → HOME 에서 시작해 HOME 으로 끝남 (사용자 규칙: 퍽 사이에는 HOME 안 감).
  store = 스테이션 1 곳 퍽 2–3 개를 차례로 넣음, retrieve = 주사위 눈 수만큼 차례로 꺼내 놓음.
  퍽 하나가 끝나면 (다음 퍽 경로 시작 경유점) 그 퍽을 고정 퍽 (적재 퍽 · 박스 위 퍽) 으로 바꾸고 다음 퍽을 작업 퍽으로.
  정책 한 스텝 (30 Hz) 에 기본 경로 경유점 반 개 (경유점 하나 = 2 스텝, 시연 GIF 와 같은 속도) → 경로 끝 + settle 스텝이면 끝.
행동 6: 관절 5 개 보정 (±res_scale rad) + 그리퍼 보정 (±grip_res).
보상: 충돌 · 가까움 · 떨어뜨림 · 심한 충돌 (Training2Env 와 같은 판정) + 제자리에 놓기 · 깨끗이 HOME + 보정 크기 · 변화 벌점.
"""
import json
from pathlib import Path

import numpy as np
import torch

from isaaclab.envs import DirectRLEnv
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_from_euler_xyz

from cfg import BOX_TOP, CELLS, GRIPPER_CLOSE, GRIPPER_HOLD, GRIPPER_OPEN, GRIPPER_RESET, N_CYL, EnvCfg
from env import TAGS, Training2Env

HERE = Path(__file__).resolve().parent


@configclass
class ResEnvCfg(EnvCfg):
    observation_space = 92                # Training2Env 80 + 기본 경로 12
    library: str = 'logs/library_chain_v3.npz'
    res_scale: float = 0.05               # 관절 보정 최대 [rad] (손끝 약 10 mm)
    grip_res: float = 0.0                 # 그리퍼 보정 최대 (0 = 그리퍼는 기본 경로 그대로, 2026-11-11 r1 실패 뒤)
    act_smooth: float = 0.8               # 행동 저역 필터: 보정 = 0.8 × 앞 보정 + 0.2 × 새 행동 (탐색 때 팔이 떨지 않게)
    res_penalty: float = -0.02            # 보정 크기 벌점 (행동² 합)
    settle_steps: int = 60                # 경로 끝 뒤 기다림 (2 s)
    lookahead: int = 8                    # 관측: 몇 경유점 앞 기본 자세
    # 몸체 안정 (사용자 2026-11-11: 바닥에서 덜컹거리면 감점, 안정적으로 끝내면 보상)
    own_cup_touch: float = 0.0002         # 작업 퍽 ↔ 자기 칸 컵 벽 닿음 (기록만). 사용자 2026-11-11: 자기 칸 벽 스침은 괜찮음, 다른 퍽 건드림은 금물 (충돌)
    stab_tilt_deg: float = 0.45           # 이 기울기까지는 감점 없음 (2026-11-11 사용자: 가속 5.0–1.0 측정 범위 0.31–0.41° 는 봐줌)
    stab_tilt: float = -1.0               # 넘은 각 [°] 당
    stab_lift_mm: float = 1.0             # 바퀴 높이 차 이만큼까지 감점 없음 (같은 측정 0.65–0.94 mm)
    stab_lift: float = -0.5               # 넘은 mm 당
    stab_angvel: float = -0.05            # 몸체 각속도² [rad/s]²
    stab_bonus: float = 2.0               # 미션 끝까지 기울기 · 바퀴 높이 차가 위 기준 안 · 충돌 없이 성공
    lift_fail: float = -5.0               # 바퀴 뜸이 stab_lift_mm 넘으면 에피소드 끝 + 이 벌점 (사용자 2026-11-12: 바닥에서 아예 뜨면 안 됨)


class Training2ResEnv(Training2Env):
    cfg: ResEnvCfg

    def __init__(self, cfg: ResEnvCfg, render_mode=None, **kwargs):
        lib = np.load(HERE / cfg.library if not Path(cfg.library).is_absolute() else cfg.library)
        self._libQ, self._libG, self._libN = lib['Q'], lib['G'], lib['n']
        self.lib_meta = [json.loads(m) for m in lib['meta']]
        cfg.episode_length_s = (2 * int(self._libN.max()) + cfg.settle_steps + 10) * cfg.decimation * cfg.sim.dt
        super().__init__(cfg, render_mode, **kwargs)
        dev = self.device
        self.libQ = torch.tensor(self._libQ, device=dev)
        self.libG = torch.tensor(self._libG, device=dev)
        self.libN = torch.tensor(self._libN, device=dev, dtype=torch.long)
        N = self.num_envs
        self.li = torch.zeros(N, dtype=torch.long, device=dev)
        self.t = torch.zeros(N, dtype=torch.long, device=dev)
        self._sp = torch.zeros(N, dtype=torch.bool, device=dev)   # 이 에피소드 성공 보상 줬나
        self.holding = torch.zeros(N, dtype=torch.bool, device=dev)
        self.a_f = torch.zeros(N, 6, device=dev)                         # 걸러진 보정 행동
        self.wheel_ids = [i for i, nm in enumerate(self.robot.body_names) if 'wheel' in nm.lower()]
        self.stable = torch.ones(N, dtype=torch.bool, device=dev)     # 이 에피소드 내내 몸체 안정
        self.ep_tilt = torch.zeros(N, device=dev)                      # 에피소드 최대 기울기 [°]
        self.js = [None] * N               # env 마다 이 에피소드 퍽 차례 (라이브러리 jobs)
        self.n_jobs = torch.ones(N, dtype=torch.long, device=dev)
        self.n_done = torch.zeros(N, dtype=torch.long, device=dev)   # 제자리에 놓고 끝난 퍽 수 (지금 퍽 빼고)
        self.next_start = torch.full((N,), 10 ** 9, dtype=torch.long, device=dev)
        self.fixed = None                 # 평가: 라이브러리 번호 목록을 차례로 (set_fixed)
        # 받침 상자: 누운 퍽을 받침에서 세우는 동안 작업 퍽 ↔ 받침은 충돌로 안 셈 (src_cell = 99 일 때)
        self.base_cell = torch.where(self.base_tag == TAGS.index('stand'), torch.full_like(self.base_cell, 99), self.base_cell)
        print(f'[env_res] 라이브러리 {len(self.lib_meta)} 개 (최대 경유점 {int(self._libN.max())}) · 에피소드 최대 {self.max_episode_length} 스텝', flush=True)

    def set_fixed(self, idx):
        from collections import deque
        self.fixed = deque(int(i) for i in idx)

    # ------------------------------------------------------------------ 리셋
    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ids = torch.as_tensor(env_ids, device=self.device)
        self._log_and_curriculum(ids)
        DirectRLEnv._reset_idx(self, ids)
        dev, n, o = self.device, len(ids), self.scene.env_origins
        unit = torch.tensor([0, 0, 0, 1.0], device=dev)
        if self.fixed is not None and len(self.fixed):
            pick = torch.tensor([self.fixed.popleft() if self.fixed else 0 for _ in range(n)], device=dev)
        else:
            pick = torch.randint(0, len(self.lib_meta), (n,), device=dev)
        self.li[ids], self.t[ids] = pick, 0
        for f in ('stored', 'on_box', 'cyl_on', 'work_is_cyl'):
            getattr(self, f)[ids] = False
        self.n_done[ids] = 0
        up = torch.tensor([0, 0, 1.0], device=dev)
        for e in ids.tolist():
            m = self.lib_meta[int(self.li[e])]
            js = dict(m=m, j=0, obj={}, cyl_free=list(range(N_CYL)))
            self.js[e] = js
            for c, sh in zip(m['prefill'], m['pre_shape']):      # 적재함에 이미 있는 퍽
                i = CELLS.index(c)
                if sh == 'cyl':
                    k = js['cyl_free'].pop(0); self.cyl_on[e, k] = True; self.cyl_pos[e, k] = self.stored_local[i]; js['obj'][c] = ('cyl', k)
                else:
                    self.stored[e, i] = True; self.stored_p0[e, i] = self.stored_local[i]; self.stored_up0[e, i] = up; js['obj'][c] = ('box', i)
            if m['task'] == 'store':                              # 스테이션 퍽: 사각은 들어갈 칸 번호의 puck_S, 원기둥은 cyl_k
                for job in m['jobs']:
                    kind, x, y, yaw = m['station'][job['puck']]
                    pos, q = self._station_pose(kind, x, y, yaw)
                    if kind == 'cyl':
                        k = js['cyl_free'].pop(0); self.cyl_on[e, k] = True; self.cyl_pos[e, k] = pos; js['obj'][('st', job['puck'])] = ('cyl', k)
                    else:
                        i = CELLS.index(job['cell'])
                        self.on_box[e, i] = True; self.box_pos[e, i] = pos; self.box_quat[e, i] = q; js['obj'][('st', job['puck'])] = ('box', i)
            self.task_store[e] = m['task'] == 'store'
            self.n_jobs[e] = len(m['jobs'])
            self._activate(e, 0, reset=True)
        self.next_start[ids] = torch.tensor([self._next_start(e) for e in ids.tolist()], device=dev)
        # 로봇: HOME, 그리퍼 닫힘
        r = self.robot
        root = torch.cat([o[ids], unit.repeat(n, 1)], -1)
        r.write_root_pose_to_sim_index(root_pose=root, env_ids=ids)
        r.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev), env_ids=ids)
        q = r.data.default_joint_pos.torch[ids].clone()
        q[:, self.arm_ids] = self.libQ[pick, 0]
        q[:, self.grip_ids] = GRIPPER_RESET
        r.write_joint_position_to_sim_index(position=q, env_ids=ids)
        r.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q), env_ids=ids)
        self.q_target[ids] = self.libQ[pick, 0]
        self.grip_target[ids] = GRIPPER_CLOSE
        for k in ('grasped', 'ever_grasped', 'placed', 'holding'):
            getattr(self, k)[ids] = False
        self.clean[ids] = True
        self.stable[ids] = True
        self.ep_tilt[ids] = 0
        if hasattr(self, 'a_f'):
            self.a_f[ids] = 0
        self.phase[ids] = 0
        self.prev_actions[ids] = 0
        self.prev_phi[ids] = float('nan')
        for v in self.ep_stats.values():
            v[ids] = 0
        self.ep_stats['min_clear'][ids] = 1.0
        self._follow_robot()
        self._stale = True

    # ------------------------------------------------------------------ 퍽 차례 (한 에피소드에 퍽 여러 개)
    def _station_pose(self, kind, x, y, yaw):
        dev = self.device
        lying = kind == 'lying'
        q = quat_from_euler_xyz(torch.tensor([0.0], device=dev), torch.tensor([np.pi / 2 if lying else 0.0], device=dev), torch.tensor([yaw], device=dev))[0]
        return torch.tensor([x, y, BOX_TOP + (0.015 if lying else 0.030) + 5e-4], device=dev), q

    def _next_start(self, e):
        js = self.js[e]
        return js['m']['jobs'][js['j'] + 1]['start'] if js['j'] + 1 < len(js['m']['jobs']) else 10 ** 9

    def _put(self, obj, e, pos, quat):
        ids = torch.tensor([e], device=self.device)
        obj.write_root_pose_to_sim_index(root_pose=torch.cat([self.scene.env_origins[e] + pos, quat])[None], env_ids=ids)
        obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(1, 6, device=self.device), env_ids=ids)

    def _activate(self, e, j, reset=False):
        """j 번째 퍽을 작업 퍽 (움직이는 물체) 으로: 그 자리의 고정 퍽을 치우고 같은 자세로 작업 퍽을 놓음."""
        dev, js = self.device, self.js[e]
        m, job = js['m'], js['m']['jobs'][j]
        js['j'] = j
        unit = torch.tensor([0, 0, 0, 1.0], device=dev)
        if m['task'] == 'store':
            kind, x, y, yaw = m['station'][job['puck']]
            pos, q = self._station_pose(kind, x, y, yaw)
            o_kind, idx = js['obj'][('st', job['puck'])]
            ci = CELLS.index(job['cell'])
            self.src_cell[e] = 99 if kind == 'lying' else -1
            self.dst[e] = self.stored_local[ci]; self.dst_cell[e] = ci
        else:
            ci = CELLS.index(job['cell'])
            o_kind, idx = js['obj'][job['cell']]
            pos, q = self.stored_local[ci], self.cell_quat[ci]
            self.src_cell[e] = ci; self.dst_cell[e] = -1
            self.dst[e] = torch.tensor([job['target'][0], job['target'][1], BOX_TOP + 0.030 + 5e-4], device=dev)
        if o_kind == 'cyl':
            self.cyl_on[e, idx] = False
        else:
            self.on_box[e, idx] = False; self.stored[e, idx] = False
        cyl = o_kind == 'cyl'
        self.work_is_cyl[e] = cyl
        js['work'] = (o_kind, idx)
        self.src[e] = pos
        self._put(self.work_c if cyl else self.work_b, e, pos, q)
        self._put(self.work_b if cyl else self.work_c, e, torch.tensor([-0.55, 0.42 if cyl else 0.48, 0.03], device=dev), unit)
        for k in ('grasped', 'ever_grasped', 'placed', 'holding'):
            getattr(self, k)[e] = False

    def _freeze(self, e):
        """방금 끝난 작업 퍽을 고정 퍽으로: store = 그 칸 적재 퍽, retrieve = 박스 위 놓인 자리 그대로."""
        js = self.js[e]
        m, job = js['m'], js['m']['jobs'][js['j']]
        o_kind, idx = js['work']
        wp, wq, _ = self._work_state()
        pos, quat = wp[e] - self.scene.env_origins[e], wq[e]
        self.n_done[e] += int(bool(self.placed[e]))
        if m['task'] == 'store':
            ci = CELLS.index(job['cell'])
            if o_kind == 'cyl':
                self.cyl_on[e, idx] = True; self.cyl_pos[e, idx] = self.stored_local[ci]
            else:
                self.stored[e, ci] = True; self.stored_p0[e, ci] = self.stored_local[ci]; self.stored_up0[e, ci] = torch.tensor([0, 0, 1.0], device=self.device)
        else:
            if o_kind == 'cyl':
                self.cyl_on[e, idx] = True; self.cyl_pos[e, idx] = pos
            else:
                self.on_box[e, idx] = True; self.box_pos[e, idx] = pos; self.box_quat[e, idx] = quat

    def _advance_jobs(self):
        k = self._k()
        due = (k >= self.next_start).nonzero()[:, 0].tolist()
        for e in due:
            self._freeze(e)
            self._activate(e, self.js[e]['j'] + 1)
            self.next_start[e] = self._next_start(e)
        if due:
            self._follow_robot()

    # ------------------------------------------------------------------ 행동
    def _k(self, ahead=0):
        return torch.minimum(self.t // 2 + ahead, self.libN[self.li] - 1)

    def _pre_physics_step(self, actions):
        self._advance_jobs()
        self._follow_robot()
        a = actions.clamp(-1.0, 1.0)
        self.actions = a
        k = self._k()
        qb = self.libQ[self.li, k]
        if self.scripted is not None:                      # 기본 경로만 (보정 0) 시험
            a = torch.zeros_like(a)
        self.a_f = self.cfg.act_smooth * self.a_f + (1 - self.cfg.act_smooth) * a
        self.q_target = torch.maximum(torch.minimum(qb + self.a_f[:, :5] * self.cfg.res_scale, self.q_hi), self.q_lo)
        self.grip_target = (self.libG[self.li, k] + self.a_f[:, 5] * self.cfg.grip_res).clamp(GRIPPER_CLOSE - 0.001, GRIPPER_OPEN)
        self.t += 1

    # ------------------------------------------------------------------ 끝 · 보상
    def _get_dones(self):
        self._compute()
        self.ev['bad'] = self._bad_state()
        # 떨어뜨림 = 쥐고 있어야 할 때 (쥠 확인 뒤 그리퍼 닫힘 명령 중) 손에서 4 cm 넘게 빠짐, 또는 바닥에 떨어짐.
        #   일부러 놓기 (기울여 쥔 퍽 내려놓기 · 받침에 넣기 · 칸 · 주사위 칸) 는 그리퍼를 여니까 떨어뜨림이 아님
        o = self.scene.env_origins
        closed = self.grip_target < GRIPPER_HOLD + 0.002              # 쥔 값 근처 (칸 안 살짝 벌림 0.0085 도 놓기)
        self.holding = (self.holding | self.grasped) & closed
        far = (self.work_w - self.grasp_w).norm(dim=-1) > 0.04
        self.ev['drop'] = (self.holding & far) | ((self.work_w[:, 2] - o[:, 2] < 0.04) & ~self.placed)
        # 몸체 기울기 (몸체 z 축 ↔ 세계 z) · 바퀴 뜸 (네 바퀴 높이 차) · 각속도
        from isaaclab.utils.math import matrix_from_quat
        bz = matrix_from_quat(self.robot.data.root_quat_w.torch)[:, :, 2]
        self.body_tilt = torch.rad2deg(torch.acos(bz[:, 2].clamp(-1, 1)))
        wz = self.robot.data.body_pos_w.torch[:, self.wheel_ids, 2]
        self.wheel_lift = (wz.amax(1) - wz.amin(1)) * 1000
        self.body_angvel = self.robot.data.root_ang_vel_w.torch.square().sum(1)
        self.stable &= (self.body_tilt <= self.cfg.stab_tilt_deg) & (self.wheel_lift <= self.cfg.stab_lift_mm)
        self.ep_tilt = torch.maximum(self.ep_tilt, self.body_tilt)
        home_ok = (self.robot.data.joint_pos.torch[:, self.arm_ids] - self.home).abs().amax(1) < self.cfg.reward.home_tol
        last = self.next_start >= 10 ** 9
        self.ev['success'] = last & ((self.n_done + self.placed.long()) >= self.n_jobs) & home_ok & (self.t >= 2 * self.libN[self.li])
        self.cup_touch = self.d_own_cup < self.cfg.own_cup_touch       # 칸 벽 닿음 (기록만)
        self.ev['lifted'] = self.wheel_lift > self.cfg.stab_lift_mm
        terminated = self.ev['severe'] | self.ev['drop'] | self.ev['bad'] | self.ev['lifted']
        if self.no_terminate:
            terminated = torch.zeros_like(terminated)
        done_path = self.t >= 2 * self.libN[self.li] + self.cfg.settle_steps
        return terminated, done_path | (self.episode_length_buf >= self.max_episode_length - 1)

    def _get_rewards(self):
        rw, ev = self.cfg.reward, self.ev
        coll = ev['collision'].float()
        near = ((rw.near_dist - self.d_min) / (rw.near_dist - rw.contact_eps)).clamp(0, 1) * (~ev['collision']).float()
        self.clean &= ~ev['collision']
        self.ep_stats['collision_steps'] += coll
        self.ep_stats['min_clear'] = torch.minimum(self.ep_stats['min_clear'], self.d_min)
        a, pa = self.actions, self.prev_actions
        parts = {
            '충돌': rw.collision * coll, '가까움': rw.near * near,
            '심한충돌': rw.terminate_collision * ev['severe'].float(), '떨어뜨림': rw.drop * ev['drop'].float(),
            '컵닿음': self.cup_touch.float(),                           # 기록만 (닿은 스텝 수, 보상에 안 들어감)
            '쥠': rw.grasp * ev['grasp_new'].float(), '놓음': rw.place * (ev['place_new'] & self.clean).float(),
            'HOME': rw.home * (ev['success'] & ~self._sp & self.clean).float(),
            '기울기': self.cfg.stab_tilt * (self.body_tilt - self.cfg.stab_tilt_deg).clamp(min=0),
            '바퀴뜸': self.cfg.stab_lift * (self.wheel_lift - self.cfg.stab_lift_mm).clamp(min=0),
            '바퀴뜸실패': self.cfg.lift_fail * ev['lifted'].float(),
            '흔들림속도': self.cfg.stab_angvel * self.body_angvel,
            '안정보상': self.cfg.stab_bonus * (ev['success'] & ~self._sp & self.clean & self.stable).float(),
            '보정크기': self.cfg.res_penalty * a.square().sum(1),
            '보정변화': rw.action_rate * (a - pa).square().sum(1)}
        if not hasattr(self, 'ep_parts'):
            self.ep_parts = {k: torch.zeros(self.num_envs, device=self.device) for k in parts}
        for k_, v_ in parts.items():
            self.ep_parts[k_] += torch.nan_to_num(v_)
        rew = sum(v for k_, v in parts.items() if k_ != '컵닿음')
        self._sp |= ev['success']
        self.prev_actions = a.clone()
        return torch.nan_to_num(rew, nan=0.0, posinf=0.0, neginf=0.0)

    # ------------------------------------------------------------------ 관측
    def _get_observations(self):
        saved = self.src_cell.clone()
        self.src_cell[saved == 99] = -1                    # 칸 원핫은 0–11 만
        try:
            base = super()._get_observations()
        finally:
            self.src_cell.copy_(saved)
        q = self.robot.data.joint_pos.torch[:, self.arm_ids]
        k = self._k()
        qb, qa = self.libQ[self.li, k], self.libQ[self.li, self._k(self.cfg.lookahead)]
        prog = (k.float() / self.libN[self.li].float())[:, None]
        gb = ((self.libG[self.li, k] - GRIPPER_CLOSE) / (GRIPPER_OPEN - GRIPPER_CLOSE))[:, None]
        extra = torch.nan_to_num(torch.cat([qb - q, qa - qb, prog, gb], -1)).clamp(-10, 10)
        return {'policy': torch.cat([base['policy'], extra], -1), 'critic': base['critic']}

    def _log_and_curriculum(self, ids):
        n0 = len(self.record) if self.record is not None else 0
        super()._log_and_curriculum(ids)
        if self.record is not None and hasattr(self, 'n_done'):
            for r in self.record[n0:]:
                e = r['env']; d = int(self.n_done[e]) + int(bool(self.placed[e]))
                r['done'], r['done_frac'] = d, d / max(int(self.n_jobs[e]), 1)
                if hasattr(self, 'ep_parts'):
                    r['parts'] = {k: round(float(v[e]), 2) for k, v in self.ep_parts.items()}
        if hasattr(self, 'ep_parts'):
            log = self.extras.setdefault('log', {})
            for k, v in self.ep_parts.items():
                log[f'Reward_part/{k}'] = v[ids].mean()
                v[ids] = 0
        if hasattr(self, '_sp'):
            self._sp[ids] = False
        if self.dist and hasattr(self, 'li'):
            log = self.extras.setdefault('log', {})
            st = self.task_store[ids]
            for nm, msk in (('store', st), ('retrieve', ~st)):
                if msk.any():
                    log[f'Task/{nm}_pucks_done'] = ((self.n_done[ids] + self.placed[ids].long()).float() / self.n_jobs[ids].float())[msk].mean()
                    log[f'Task/{nm}_clean'] = self.clean[ids][msk].float().mean()
            log['Episode/body_stable'] = self.stable[ids].float().mean()
            log['Episode/body_tilt_max_deg'] = self.ep_tilt[ids].mean()
