"""학습2 환경 (Isaac Lab DirectRLEnv): 무작위로 찬 적재함에서 퍽을 넣고 · 빼서 박스 주사위 칸에 놓기, 무충돌.

한 스텝 순서 (DirectRLEnv): 행동 → 물리 4 번 → _get_dones (여기서 기하 · 충돌 · 단계를 한 번에 계산) → _get_rewards → 리셋 → 관측.
충돌 판정은 geometry.py (URDF 링크 단위 상자 · 표면 점). 적재된 퍽이 밀려도 충돌 (PhysX 가 실제로 밀어낸 결과).
"""
from collections import deque

import numpy as np
import torch

from isaaclab.envs import DirectRLEnv
from isaaclab.utils.math import matrix_from_quat, quat_from_matrix, quat_mul

from cfg import (N_CYL, ARM_JOINTS, HAND_BODIES, BOX_TOP, GRIPPER_HOLD, GRIPPER_LIMIT, GRIPPER_RESET, BOX_X, CELLS, DICE_PITCH, GRIPPER_CLOSE, GRIPPER_JOINTS, GRIPPER_OPEN, HOME,
                 PUCK_SIZE, EnvCfg)
from geometry import Urdf, base_boxes, box_surface, obb_sdf_min, sample_surface

# 충돌 판정에 쓰는 팔 몸체 (USD 이름). 무리: 0 = link2 · link3, 1 = link4, 2 = link5 · 손목(카메라 · 크랭크 포함) · 손가락
ARM_BODIES = (('link2', 0), ('link3', 0), ('link4', 1), ('link5', 2), ('wrist_link', 2), ('gripper_left_link', 2), ('gripper_right_link', 2))
HOLD = GRIPPER_HOLD                                   # 퍽 쥔 손가락 관절 값 (시뮬 측정)
# 쥐는 점 = 팀 팔 모델 손끝 tip5 (config/arm_kinematics.yaml, 혁무님 집기 계산기와 같음) 을 URDF wrist_link 좌표로 옮긴 값.
#   실물 경로 4 개 · 59 자세에서 맞춤, 흩어짐 1.2 mm (2026-11-10)
TIP_WRIST = (0.0716, -0.0304, -0.1018)
# 실물 넣기 · 빼기 경로는 손끝이 퍽 윗면 약 13 mm 아래 (S5 · S7 · S12, 처짐 보정 뒤) → 쥐는 점 목표 = 퍽 중심 + 위로 17 mm
GRIP_DEPTH = 0.017
TAGS = ('chassis', 'profile', 'stand', 'rack', 'arm_base')


class Training2Env(DirectRLEnv):
    cfg: EnvCfg

    def __init__(self, cfg: EnvCfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        N, dev = self.num_envs, self.device
        self.robot = self.scene['robot']
        self.work_b, self.work_c = self.scene['work_puck'], self.scene['work_cyl']   # 사각 · 원기둥 작업 퍽 (에피소드마다 하나)
        self.pucks = [self.scene[f'puck_{c}'] for c in CELLS]
        self.cyls = [self.scene[f'cyl_{i}'] for i in range(N_CYL)]
        f = lambda ids: torch.tensor(ids, dtype=torch.long, device=dev)
        self.arm_ids = f(self.robot.find_joints(list(ARM_JOINTS), preserve_order=True)[0])
        self.grip_ids = f(self.robot.find_joints(list(GRIPPER_JOINTS), preserve_order=True)[0])
        self.home = torch.tensor(HOME, device=dev)
        lim = self.robot.data.soft_joint_pos_limits.torch[0, self.arm_ids]
        self.q_lo, self.q_hi = lim[:, 0], lim[:, 1]
        self._build_geometry()

        rw = cfg.reward
        self.q_target = self.home.repeat(N, 1)
        self.grip_target = torch.full((N,), GRIPPER_CLOSE, device=dev)
        self.prev_actions = torch.zeros(N, 6, device=dev)
        self.task_store = torch.zeros(N, dtype=torch.bool, device=dev)        # True = store, False = retrieve
        self.stored = torch.zeros(N, 12, dtype=torch.bool, device=dev)        # 이미 적재된 퍽 (작업 퍽 제외)
        self.on_box = torch.zeros(N, 12, dtype=torch.bool, device=dev)        # 박스 위에 이미 놓인 퍽 (빈 칸 퍽을 씀, 주사위 눈)
        self.box_pos = torch.zeros(N, 12, 3, device=dev)                      # 그 퍽 중심 (env 기준)
        self.box_quat = torch.tensor([0, 0, 0, 1.0], device=dev).repeat(N, 12, 1)
        self.cyl_on = torch.zeros(N, N_CYL, dtype=torch.bool, device=dev)     # 스테이션 위 원기둥 퍽
        self.cyl_pos = torch.zeros(N, N_CYL, 3, device=dev)
        self.work_is_cyl = torch.zeros(N, dtype=torch.bool, device=dev)
        self.src = torch.zeros(N, 3, device=dev)                              # 작업 퍽 처음 자리 (env 기준)
        self.dst = torch.zeros(N, 3, device=dev)                              # 놓을 자리 (퍽 중심, env 기준)
        self.src_cell = torch.full((N,), -1, dtype=torch.long, device=dev)    # −1 = 박스
        self.dst_cell = torch.full((N,), -1, dtype=torch.long, device=dev)
        self.stored_p0 = torch.zeros(N, 12, 3, device=dev)
        self.stored_up0 = torch.zeros(N, 12, 3, device=dev)
        self.grasped = torch.zeros(N, dtype=torch.bool, device=dev)
        self.ever_grasped = torch.zeros(N, dtype=torch.bool, device=dev)
        self.placed = torch.zeros(N, dtype=torch.bool, device=dev)
        self.clean = torch.ones(N, dtype=torch.bool, device=dev)              # 이 에피소드 충돌 0 이었나
        self.phase = torch.zeros(N, dtype=torch.long, device=dev)            # 0 쥐러 감 · 1 옮김 · 2 돌아옴
        self.prev_phi = torch.zeros(N, device=dev)
        self.ev = {k: torch.zeros(N, dtype=torch.bool, device=dev) for k in ('success', 'collision', 'severe', 'drop', 'grasp_new', 'place_new')}
        self.dist = {}
        self.occ_max = cfg.task.occupied_max_start
        self.recent = deque(maxlen=cfg.task.curriculum_window)
        self.scenarios = None              # 평가 · 재생용 고정 시나리오 (set_scenarios)
        self.scripted = None               # 재생용: (q_target (N, 5), grip_target (N,)) 를 정책 대신
        self.record = None                 # 평가용: 끝난 에피소드 결과를 여기에 쌓음 (list)
        self.no_terminate = False          # 재생 검증용: 충돌 · 떨어뜨림에도 에피소드를 끝내지 않음
        self.ep_stats = {k: torch.zeros(N, device=dev) for k in ('collision_steps', 'min_clear')}
        self._stale = True

    # ------------------------------------------------------------------ 기하
    def _build_geometry(self):
        dev, cs = self.device, self.cfg.point_spacing
        u = Urdf()
        pts, owner, group = [], [], []
        self.arm_body_ids = []
        for k, (b, g) in enumerate(ARM_BODIES):
            self.arm_body_ids.append(self.robot.find_bodies(b)[0][0])
            tris = np.concatenate([u.tris(n) @ T[:3, :3].T + T[:3, 3] for n, T in u.links_in_body(b) if len(u.tris(n))])
            p = sample_surface(tris, cs, seed=k)
            pts.append(p); owner += [k] * len(p); group += [g] * len(p)
        t = lambda a: torch.tensor(np.asarray(a), dtype=torch.float32, device=dev)
        self.p_local = t(np.concatenate(pts))
        self.p_owner = torch.tensor(owner, device=dev)
        self.p_group = torch.tensor(group, device=dev)
        self.arm_body_ids = torch.tensor(self.arm_body_ids, device=dev)
        # 몸체(base_footprint) 부품 상자
        bb = base_boxes(u)
        self.base_c = t([b.T[:3, 3] for b in bb]); self.base_R = t([b.T[:3, :3] for b in bb]); self.base_h = t([b.half for b in bb])
        self.base_tag = torch.tensor([TAGS.index(b.tag) if b.tag in TAGS else 0 for b in bb], device=dev)
        cell_of_box = [CELLS.index(b.name[10:-5]) if b.name.startswith('rack_cell_') else -1 for b in bb]
        self.base_cell = torch.tensor(cell_of_box, device=dev)             # 컵 벽이면 그 칸 번호
        # 칸 바닥 중심 (base_footprint 기준) · 방향
        Tc = [u.body_of(f'rack_cell_{c}_link')[1] for c in CELLS]
        self.cell_floor = t([T[:3, 3] for T in Tc])
        self.cell_quat = quat_from_matrix(t([T[:3, :3] for T in Tc]))
        self.stored_local = self.cell_floor + torch.tensor([0, 0, PUCK_SIZE[2] / 2 + 5e-4], device=dev)    # 칸 퍽 중심 (로봇 기준)
        self.park = t([(-0.55, -0.33 + 0.06 * i, PUCK_SIZE[2] / 2) for i in range(12)])                   # 빈 칸 퍽은 로봇 뒤 바닥
        self.park_q = torch.tensor([0, 0, 0, 1.0], device=dev)
        # 주사위 칸 (박스 윗면, 퍽 중심 높이)
        rows = self.cfg.task.dice_rows
        self.dice = t([(BOX_X + r * DICE_PITCH, c * DICE_PITCH, BOX_TOP + PUCK_SIZE[2] / 2) for r in rows for c in (-1, 0, 1)])
        self.box_c = t([[BOX_X, 0.0, BOX_TOP / 2]]); self.box_h = t([[0.205 / 2, 0.205 / 2, BOX_TOP / 2]])
        self.grasp_local = t(TIP_WRIST)
        # 그리퍼 상한을 시뮬 열림 값이 들어가게 넓힘 (cfg.GRIP_SIM_OFFSET)
        lim = self.robot.data.joint_pos_limits.torch[:, self.grip_ids].clone()
        lim[..., 1] = GRIPPER_LIMIT
        self.robot.write_joint_position_limit_to_sim_index(limits=lim, joint_ids=self.grip_ids)
        self.wrist_id = self.robot.find_bodies('wrist_link')[0][0]
        self.puck_h = t(PUCK_SIZE) / 2
        self.puck_pts = t(box_surface(np.array(PUCK_SIZE) / 2, cs))
        print(f'[env] 팔 표면 점 {len(self.p_local)} · 몸체 상자 {len(bb)} · 주사위 칸 {len(self.dice)}', flush=True)

    # ------------------------------------------------------------------ 시나리오
    def set_scenarios(self, scenarios):
        """평가 · 재생: [{'task': 'store'|'retrieve', 'cell': 'S7', 'dice': 4, 'stored': ['S1', ...]}, ...] 를 차례로 씀."""
        self.scenarios = deque(scenarios)

    def _sample(self, ids):
        n, dev, tc = len(ids), self.device, self.cfg.task
        self._box_req, self._work_req, self._shape_req = {}, {}, {}
        store = torch.rand(n, device=dev) < (0.5 if len(tc.tasks) == 2 else float(tc.tasks[0] == 'store'))
        # 찬 칸 수 k (작업 퍽 칸 포함): store = 적재된 퍽 occupied_min ~ occ_max, retrieve = 그 + 작업 퍽 1
        lo = tc.occupied_min + (~store).long()
        hi = min(self.occ_max, 11) + (~store).long()
        k = lo + (torch.rand(n, device=dev) * (hi - lo + 1).float()).long().clamp(max=hi - lo)
        perm = torch.rand(n, 12, device=dev).argsort(1)                # 칸 무작위 순서, 앞에서 k 개가 참
        filled = perm.argsort(1) < k[:, None]
        cell = torch.where(store, perm.gather(1, k.clamp(max=11)[:, None])[:, 0], perm[:, 0])   # store = 첫 빈 칸, retrieve = 찬 칸
        stored = filled & ~(torch.arange(12, device=dev)[None] == cell[:, None])
        dice = torch.randint(0, len(self.dice), (n,), device=dev)
        if self.scenarios:
            for j in range(n):
                if not self.scenarios:
                    break
                s = self.scenarios.popleft()
                store[j] = s['task'] == 'store'
                cell[j] = CELLS.index(s['cell'])
                dice[j] = s['dice']
                stored[j] = torch.tensor([c in s['stored'] for c in CELLS], device=dev)
                self._box_req[int(ids[j])] = s.get('on_box', [])
                if 'work' in s:                       # 작업 퍽 자리 직접 (store: 박스 위 x, y, yaw)
                    self._work_req[int(ids[j])] = s['work']
                self._shape_req[int(ids[j])] = s.get('work_shape', 'box')
        return store, cell, dice, stored

    # ------------------------------------------------------------------ 리셋
    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ids = torch.as_tensor(env_ids, device=self.device)
        self._log_and_curriculum(ids)
        super()._reset_idx(ids)
        n, o = len(ids), self.scene.env_origins[ids]
        store, cell, dice, stored = self._sample(ids)
        self.task_store[ids], self.stored[ids] = store, stored
        # 박스 위 퍽 (주사위 눈): 빈 칸 퍽에 차례로 맡김. 무작위 학습에서는 아직 없음 (시나리오 'on_box' 로만)
        self.on_box[ids] = False
        self.cyl_on[ids] = False
        self.work_is_cyl[ids] = False
        for i_env, shp in getattr(self, '_shape_req', {}).items():
            self.work_is_cyl[i_env] = shp == 'cyl'
        for i_env, xys in getattr(self, '_box_req', {}).items():
            free = [k for k in range(12) if not bool(stored[int((ids == i_env).nonzero()[0, 0]), k])]
            cyl_xy = [x for x in xys if len(x) > 3 and x[3] == 'cyl']
            xys = [x for x in xys if not (len(x) > 3 and x[3] == 'cyl')]
            for k, xy in enumerate(cyl_xy[:N_CYL]):
                self.cyl_on[i_env, k] = True
                self.cyl_pos[i_env, k] = torch.tensor([xy[0], xy[1], BOX_TOP + PUCK_SIZE[2] / 2 + 5e-4], device=self.device)
            for k, xy in zip(free, xys):
                self.on_box[i_env, k] = True
                self.box_pos[i_env, k] = torch.tensor([xy[0], xy[1], BOX_TOP + PUCK_SIZE[2] / 2 + 5e-4], device=self.device)
                yaw = xy[2] if len(xy) > 2 else 0.0
                self.box_quat[i_env, k] = torch.tensor([0, 0, np.sin(yaw / 2), np.cos(yaw / 2)], device=self.device)
        cell_c = self.cell_floor[cell] + torch.tensor([0, 0, PUCK_SIZE[2] / 2 + 5e-4], device=self.device)
        box_c = self.dice[dice] + torch.tensor([0, 0, 5e-4], device=self.device)
        self.src[ids] = torch.where(store[:, None], box_c, cell_c)
        self.dst[ids] = torch.where(store[:, None], cell_c, box_c)
        self.src_cell[ids] = torch.where(store, torch.full_like(cell, -1), cell)
        self.dst_cell[ids] = torch.where(store, cell, torch.full_like(cell, -1))
        # 로봇: HOME, 그리퍼 닫힘, 바퀴 0
        r = self.robot
        root = torch.cat([o, torch.tensor([0, 0, 0, 1.0], device=self.device).repeat(n, 1)], -1)
        r.write_root_pose_to_sim_index(root_pose=root, env_ids=ids)
        r.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=self.device), env_ids=ids)
        q = r.data.default_joint_pos.torch[ids].clone()
        q[:, self.arm_ids] = self.home
        q[:, self.grip_ids] = GRIPPER_RESET
        r.write_joint_position_to_sim_index(position=q, env_ids=ids)
        r.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q), env_ids=ids)
        self.q_target[ids] = self.home
        self.grip_target[ids] = GRIPPER_CLOSE
        # 퍽: 적재된 칸 · 작업 퍽 · 나머지는 로봇 뒤 바닥
        up = torch.tensor([0, 0, 1.0], device=self.device)
        for i, p in enumerate(self.pucks):
            park = torch.tensor([-0.55, -0.33 + 0.06 * i, PUCK_SIZE[2] / 2], device=self.device)
            pos = torch.where(stored[:, i:i + 1], self.cell_floor[i] + up * (PUCK_SIZE[2] / 2 + 5e-4), park)
            quat = torch.where(stored[:, i:i + 1], self.cell_quat[i].expand(n, 4), torch.tensor([0, 0, 0, 1.0], device=self.device))
            p.write_root_pose_to_sim_index(root_pose=torch.cat([o + pos, quat], -1), env_ids=ids)
            p.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=self.device), env_ids=ids)
            self.stored_p0[ids, i] = pos                    # 로봇 기준 (로봇은 env 원점 · 회전 0 으로 리셋)
            self.stored_up0[ids, i] = up
        wq = torch.where(store[:, None], torch.tensor([0, 0, 0, 1.0], device=self.device).expand(n, 4), self.cell_quat[cell])
        for i_env, (wx, wy, wyaw) in getattr(self, '_work_req', {}).items():
            j = int((ids == i_env).nonzero()[0, 0])
            self.src[i_env] = torch.tensor([wx, wy, BOX_TOP + PUCK_SIZE[2] / 2 + 5e-4], device=self.device)
            wq[j] = torch.tensor([0, 0, np.sin(wyaw / 2), np.cos(wyaw / 2)], device=self.device)
        cyl = self.work_is_cyl[ids][:, None]
        for obj, mine, park in ((self.work_b, ~cyl, [-0.55, 0.42, PUCK_SIZE[2] / 2]), (self.work_c, cyl, [-0.55, 0.48, PUCK_SIZE[2] / 2])):
            pos = torch.where(mine, o + self.src[ids], o + torch.tensor(park, device=self.device))
            obj.write_root_pose_to_sim_index(root_pose=torch.cat([pos, wq], -1), env_ids=ids)
            obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=self.device), env_ids=ids)
        for k in ('grasped', 'ever_grasped', 'placed'):
            getattr(self, k)[ids] = False
        self.clean[ids] = True
        self.phase[ids] = 0
        self.prev_actions[ids] = 0
        self.prev_phi[ids] = float('nan')                         # 첫 스텝은 퍼텐셜 차 0
        for v in self.ep_stats.values():
            v[ids] = 0
        self.ep_stats['min_clear'][ids] = 1.0
        self._stale = True

    def _log_and_curriculum(self, ids):
        if not self.dist:            # 첫 리셋 (아직 계산 전)
            return
        ev = self.ev
        done = ids
        log = self.extras.setdefault('log', {})
        succ = ev['success'][done].float()
        for s in succ.tolist():
            self.recent.append(s)
        log['Episode/success'] = succ.mean()
        log['Episode/collision_free'] = self.clean[done].float().mean()
        log['Episode/collision_steps'] = self.ep_stats['collision_steps'][done].mean()
        log['Episode/min_clearance_mm'] = self.ep_stats['min_clear'][done].mean() * 1000
        log['Episode/drop'] = ev['drop'][done].float().mean()
        log['Episode/physics_reset'] = ev['bad'][done].float().mean() if 'bad' in ev else torch.tensor(0.0)
        log['Episode/grasped'] = self.ever_grasped[done].float().mean()
        log['Episode/placed'] = self.placed[done].float().mean()
        log['Curriculum/occupied_max'] = torch.tensor(float(self.occ_max))
        if self.record is not None:
            for i in ids.tolist():
                self.record.append({'env': i, 'task': 'store' if self.task_store[i] else 'retrieve',
                                    'cell': CELLS[int(self.dst_cell[i] if self.task_store[i] else self.src_cell[i])],
                                    'stored': [c for c, s in zip(CELLS, self.stored[i].tolist()) if s],
                                    'success': bool(ev['success'][i]), 'collision_free': bool(self.clean[i]),
                                    'collision_steps': int(self.ep_stats['collision_steps'][i]), 'drop': bool(ev['drop'][i]),
                                    'grasped': bool(self.ever_grasped[i]), 'placed': bool(self.placed[i]),
                                    'min_clearance_mm': round(float(self.ep_stats['min_clear'][i]) * 1000, 2),
                                    'steps': int(self.episode_length_buf[i])})
        tc = self.cfg.task
        if self.scenarios is None and len(self.recent) == self.recent.maxlen and np.mean(self.recent) > tc.curriculum_success \
                and self.occ_max < tc.occupied_max_end:
            self.occ_max += 1
            self.recent.clear()
            print(f'[env] 커리큘럼: 찬 칸 최대 {self.occ_max}', flush=True)

    # ------------------------------------------------------------------ 행동
    def _pre_physics_step(self, actions):
        self._follow_robot()
        a = actions.clamp(-1.0, 1.0)
        self.actions = a
        if self.scripted is not None:
            self.q_target[:], self.grip_target[:] = self.scripted
        else:
            self.q_target = torch.maximum(torch.minimum(self.q_target + a[:, :5] * self.cfg.max_joint_speed * self.step_dt, self.q_hi), self.q_lo)
            self.grip_target = torch.where(a[:, 5] > 0, GRIPPER_OPEN, GRIPPER_CLOSE)

    def _follow_robot(self):
        """적재 칸 퍽 (kinematic) 을 로봇 몸체 자세에 붙여 옮김 (로봇이 바퀴 위에서 1–2 mm 움직이면 적재함도 같이 움직임)."""
        r = self.robot
        R = matrix_from_quat(r.data.root_quat_w.torch)
        p = r.data.root_pos_w.torch
        o = self.scene.env_origins
        rq = r.data.root_quat_w.torch
        for i, pk in enumerate(self.pucks):
            on = self.stored[:, i]
            pos = torch.where(on[:, None], p + torch.einsum('nij,j->ni', R, self.stored_local[i]),
                              torch.where(self.on_box[:, i:i + 1], o + self.box_pos[:, i], o + self.park[i]))
            quat = torch.where(on[:, None], quat_mul(rq, self.cell_quat[i].expand_as(rq)),
                               torch.where(self.on_box[:, i:i + 1], self.box_quat[:, i], self.park_q.expand_as(rq)))
            pk.write_root_pose_to_sim_index(root_pose=torch.cat([pos, quat], -1))
        for i, cy in enumerate(self.cyls):
            pos = torch.where(self.cyl_on[:, i:i + 1], o + self.cyl_pos[:, i], o + torch.tensor([-0.70, -0.33 + 0.06 * i, PUCK_SIZE[2] / 2], device=self.device))
            cy.write_root_pose_to_sim_index(root_pose=torch.cat([pos, self.park_q.expand_as(rq)], -1))

    def _work_state(self):
        """작업 퍽 (사각 또는 원기둥) 위치 · 자세 · 속도."""
        c = self.work_is_cyl[:, None]
        pick = lambda a, b: torch.where(c, b, a)
        return (pick(self.work_b.data.root_pos_w.torch, self.work_c.data.root_pos_w.torch),
                pick(self.work_b.data.root_quat_w.torch, self.work_c.data.root_quat_w.torch),
                pick(self.work_b.data.root_lin_vel_w.torch, self.work_c.data.root_lin_vel_w.torch))

    def _apply_action(self):
        self.robot.set_joint_position_target_index(target=self.q_target, joint_ids=self.arm_ids)
        self.robot.set_joint_position_target_index(target=self.grip_target[:, None].expand(-1, 2), joint_ids=self.grip_ids)

    # ------------------------------------------------------------------ 계산 (한 스텝 한 번)
    def _compute(self):
        rw, dev, N = self.cfg.reward, self.device, self.num_envs
        r = self.robot
        o = self.scene.env_origins
        root_p, root_R = r.data.root_pos_w.torch, matrix_from_quat(r.data.root_quat_w.torch)
        bp = r.data.body_pos_w.torch[:, self.arm_body_ids]
        bR = matrix_from_quat(r.data.body_quat_w.torch[:, self.arm_body_ids])
        P = torch.einsum('nmij,mj->nmi', bR[:, self.p_owner], self.p_local) + bp[:, self.p_owner]      # (N, M, 3) 팔 표면 점
        wR = matrix_from_quat(r.data.body_quat_w.torch[:, self.wrist_id])
        self.grasp_w = r.data.body_pos_w.torch[:, self.wrist_id] + wR @ self.grasp_local
        self.wrist_R = wR
        # 퍽
        # 장애물 퍽 = 칸 퍽 12 + 스테이션 원기둥 N_CYL (원기둥은 30 × 30 × 60 상자로 근사, 보수적)
        sp = torch.stack([p.data.root_pos_w.torch for p in self.pucks + self.cyls], 1)
        sR = matrix_from_quat(torch.stack([p.data.root_quat_w.torch for p in self.pucks + self.cyls], 1))
        wpos, wquat, _ = self._work_state()
        wp, wR_p = wpos, matrix_from_quat(wquat)
        self.work_w, self.work_up = wp, wR_p[:, :, 2]
        H12 = self.puck_h.expand(1, 12 + N_CYL, 3)
        inf = torch.tensor(1.0, device=dev)
        groups = [P[:, self.p_group == g] for g in range(3)]
        # 1) 팔 ↔ 적재된 퍽
        d_stored = torch.stack([obb_sdf_min(G, sp, sR, H12) for G in groups], 0).amin(0)
        obst = torch.cat([self.stored | self.on_box, self.cyl_on], 1)              # 장애물 퍽 = 적재된 퍽 + 박스 위 퍽 (사각 · 원기둥)
        d_stored = torch.where(obst, d_stored, inf).amin(1)
        # 2) 팔 ↔ 몸체 부품 (받침은 HOME 근처면 허용, link1 은 link2 · link3 무리 제외)
        bc = torch.einsum('nij,kj->nki', root_R, self.base_c) + root_p[:, None]
        bR_ = torch.einsum('nij,kjl->nkil', root_R, self.base_R)
        Hb = self.base_h[None]
        d_base_g = [obb_sdf_min(G, bc, bR_, Hb) for G in groups]                # 각 (N, K)
        at_home = (r.data.joint_pos.torch[:, self.arm_ids] - self.home).abs().amax(1) < 0.2
        stand = (self.base_tag == TAGS.index('stand'))[None]
        armb = (self.base_tag == TAGS.index('arm_base'))[None]
        d_base = torch.stack([torch.where(stand | armb, inf, d_base_g[0]).amin(1),
                              torch.where(stand, inf, d_base_g[1]).amin(1),
                              torch.where(stand, inf, d_base_g[2]).amin(1)], 1).amin(1)
        # 그리퍼 받침: 앉는 자리 → HOME 근처는 빼고, 그 밖에서도 stand_depth 넘게 파고들 때만 충돌
        d_stand = torch.where(stand, torch.stack(d_base_g, 0).amin(0), inf).amin(1)
        self.d_stand = torch.where(at_home, inf, d_stand)
        # 3) 팔 ↔ 박스
        boxc = (o + self.box_c)[:, None]
        boxR = torch.eye(3, device=dev).expand(N, 1, 3, 3)
        d_box = obb_sdf_min(P, boxc, boxR, self.box_h[None]).amin(1)
        # 4) 손 쪽 ↔ 팔 앞쪽 (자기 충돌): PhysX 필터 접촉 힘 [N], 열 = [link2, link3].
        #    wrist ↔ link2 는 충돌 메시가 HOME 에서 원래 겹침 (팀 moveit_config ninja_turtle.srdf 도 reason="Default" 로 끔) → HOME 근처만 뺌
        fm = {k: self.scene[f'self_{k}'].data.force_matrix_w.torch.norm(dim=-1).amax(1) for k in HAND_BODIES}
        fm['wrist'][:, 0] = torch.where(at_home, 0.0, fm['wrist'][:, 0])
        self.self_force = torch.stack([v.amax(1) for v in fm.values()], 1).amax(1)
        # 5) 작업 퍽 ↔ 적재된 퍽 · 몸체 부품 (넣을 · 뺄 칸 컵 벽 · 적재함 바닥판 제외)
        WP = torch.einsum('nij,mj->nmi', wR_p, self.puck_pts) + wp[:, None]
        d_wp_st = torch.where(obst, obb_sdf_min(WP, sp, sR, H12), inf).amin(1)
        d_wp_b = obb_sdf_min(WP, bc, bR_, Hb)
        own = (self.base_cell[None] == self.src_cell[:, None]) | (self.base_cell[None] == self.dst_cell[:, None])
        own &= self.base_cell[None] >= 0
        plate = ((self.base_tag == TAGS.index('rack')) & (self.base_cell < 0))[None]
        # 몸체 윗판 (base_link 상자) 은 적재함 칸 바로 밑이라 칸 안 퍽과 3 mm → 퍽이 제 칸 25 mm 안이면 뺌
        in_own = torch.minimum((wp - o - self.src).norm(dim=-1), (wp - o - self.dst).norm(dim=-1)) < 0.025
        top = (self.base_tag == TAGS.index('chassis'))[None] & in_own[:, None]
        d_wp_base = torch.where(own | plate | top, inf, d_wp_b).amin(1)
        self.d_own_cup = torch.where(own, d_wp_b, inf).amin(1)
        # 6) 적재된 퍽이 밀림 · 기욺
        #    로봇 기준으로 잼 (로봇이 조금 움직이면 적재함 · 퍽도 같이 움직임)
        RbT = root_R.transpose(1, 2)
        sp_b = torch.einsum('nij,nkj->nki', RbT, sp[:, :12] - root_p[:, None])
        up_b = torch.einsum('nij,nkj->nki', RbT, sR[:, :12, :, 2])
        moved = (sp_b - self.stored_p0).norm(dim=-1)
        tilt = torch.rad2deg(torch.acos((up_b * self.stored_up0).sum(-1).clamp(-1, 1)))
        self.stored_moved = torch.where(self.stored, moved, torch.zeros_like(moved)).amax(1)
        stored_bad = (self.stored & ((moved > rw.stored_move) | (tilt > rw.stored_tilt_deg))).any(1)
        self.dist = {'stored': d_stored, 'base': d_base, 'box': d_box, 'work_stored': d_wp_st, 'work_base': d_wp_base}
        dmin = torch.stack(list(self.dist.values()), 1).amin(1)
        self.d_min = dmin
        self.ev['collision'] = (dmin < rw.contact_eps) | stored_bad | (self.self_force > rw.self_force) | (self.d_stand < -rw.stand_depth)
        self.ev['severe'] = (torch.minimum(dmin, self.d_stand) < -rw.severe_depth) | stored_bad
        # 쥠: 닫으라 했고, 손가락이 퍽 폭에서 멈췄고 (속도 ≈ 0, 전류 한계 = 힘), 손 안에 퍽.
        #   멈춤 조건이 없으면 닫히며 지나가는 순간을 쥠으로 봄 (replay_check 2026-11-10). 손 안 = 손끝에서 3 cm (퍽 중심은 손끝 약 17 mm 아래)
        gq = r.data.joint_pos.torch[:, self.grip_ids[0]]
        self.grip_q = gq
        self.grip_eff = r.data.applied_torque.torch[:, self.grip_ids[0]].abs()
        # 멈춤 = 한 정책 스텝 (33 ms) 동안 0.3 mm 안 (PhysX 관절 속도는 접촉 중 0.03–0.04 m/s 로 떨려 못 씀)
        still = (gq - getattr(self, '_prev_gq', gq)).abs() < 3e-4
        self._prev_gq = gq.clone()
        in_hand = (wp - self.grasp_w).norm(dim=-1) < 0.03
        grasp = (self.grip_target < 0.5 * (GRIPPER_OPEN + GRIPPER_CLOSE)) & ((gq - HOLD).abs() < 0.003) & still & (self.grip_eff > 2.0) & in_hand
        self.ev['grasp_new'] = grasp & ~self.ever_grasped
        self.grasped = grasp
        self.ever_grasped |= grasp
        # 놓음: 목표 자리 · 바로 섬 · 손 뗌
        rel = wp - (o + self.dst)
        xy_tol = torch.where(self.task_store, rw.place_xy_cell, rw.place_xy_box)
        upright = self.work_up[:, 2] > np.cos(np.deg2rad(rw.place_tilt_deg))
        at_dst = (rel[:, :2].norm(dim=-1) < xy_tol) & (rel[:, 2].abs() < 0.004) & upright
        place = at_dst & ~grasp & self.ever_grasped & (gq > HOLD + 0.002)
        self.ev['place_new'] = place & ~self.placed
        self.placed |= place
        # 떨어뜨림: 쥔 적 있고, 놓기 전, 손에서 4 cm 넘게 멀어졌거나 바닥에 떨어짐
        self.ev['drop'] = self.ever_grasped & ~self.placed & ~at_dst & (((wp - self.grasp_w).norm(dim=-1) > 0.04) | (wp[:, 2] - o[:, 2] < 0.04))
        home_err = (r.data.joint_pos.torch[:, self.arm_ids] - self.home).abs()
        self.ev['success'] = self.placed & (home_err.amax(1) < rw.home_tol)
        self.phase = torch.where(self.placed, 2, torch.where(self.ever_grasped, 1, 0))
        self.home_err = home_err.sum(1)

    def _bad_state(self):
        """물리가 터진 env (NaN · inf · 퍽이 2 m 넘게 날아감). 2026-11-11 t1 이 1210 iter 에서 관측 NaN 으로 멈춤 → 그 env 만 리셋."""
        r, o = self.robot, self.scene.env_origins
        wp, _, wv = self._work_state()
        parts = {'joint_pos': r.data.joint_pos.torch, 'joint_vel': r.data.joint_vel.torch, 'root': r.data.root_pos_w.torch, 'work_pos': wp, 'work_vel': wv}
        bad = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        for k, v in parts.items():
            nb = ~torch.isfinite(v).all(-1)
            if nb.any():
                print(f'[env] 물리 값 이상 ({k}) env {nb.nonzero()[:, 0].tolist()[:8]} → 리셋', flush=True)
            bad |= nb
        return bad | ((wp - o).norm(dim=-1) > 2.0)

    def _get_dones(self):
        self._compute()
        self.ev['bad'] = self._bad_state()
        terminated = self.ev['success'] | self.ev['severe'] | self.ev['drop'] | self.ev['bad']
        if self.no_terminate:
            terminated = torch.zeros_like(terminated)
        return terminated, self.episode_length_buf >= self.max_episode_length - 1

    # ------------------------------------------------------------------ 보상
    def _phi(self):
        rw, o = self.cfg.reward, self.scene.env_origins
        d_reach = (self.work_w + GRIP_DEPTH * self.work_up - self.grasp_w).norm(dim=-1)
        rel = (o + self.dst) - self.work_w
        dxy = rel[:, :2].norm(dim=-1)
        lift = 0.06 * (dxy / 0.02).clamp(max=1.0)               # 옆으로 멀면 6 cm 위를 거쳐 가게, 맞춰지면 내려감
        d_carry = dxy + (rel[:, 2] + lift).abs()
        return torch.where(self.phase == 0, -rw.reach * d_reach,
                           torch.where(self.phase == 1, -rw.carry * d_carry, -rw.home_shaping * self.home_err))

    def _get_rewards(self):
        rw, ev = self.cfg.reward, self.ev
        phi = self._phi()
        same = ~torch.isnan(self.prev_phi) & (self.phase == getattr(self, '_prev_phase', self.phase))
        shaping = torch.where(same, phi - self.prev_phi, torch.zeros_like(phi))
        self.prev_phi, self._prev_phase = phi, self.phase.clone()
        coll = ev['collision'].float()
        near = ((rw.near_dist - self.d_min) / (rw.near_dist - rw.contact_eps)).clamp(0, 1) * (~ev['collision']).float()
        self.clean &= ~ev['collision']
        self.ep_stats['collision_steps'] += coll
        self.ep_stats['min_clear'] = torch.minimum(self.ep_stats['min_clear'], self.d_min)
        a, pa = self.actions, self.prev_actions
        rew = (shaping
               + rw.collision * coll + rw.near * near
               + rw.terminate_collision * ev['severe'].float()
               + rw.drop * ev['drop'].float()
               + rw.own_cup_scrape * (self.d_own_cup < rw.contact_eps).float()
               + rw.grasp * ev['grasp_new'].float()
               + rw.place * (ev['place_new'] & self.clean).float()
               + rw.home * (ev['success'] & self.clean).float()
               + rw.action_rate * (a - pa).square().sum(1)
               + rw.joint_vel * self.robot.data.joint_vel.torch[:, self.arm_ids].square().sum(1)
               + rw.time)
        self.prev_actions = a.clone()
        return torch.nan_to_num(rew, nan=0.0, posinf=0.0, neginf=0.0)

    # ------------------------------------------------------------------ 관측
    def _get_observations(self):
        if self._stale:          # 리셋 직후 (리셋한 env 의 거리 · 쥠 값을 새 자세로 다시)
            self._compute()
            self._stale = False
        r, o = self.robot, self.scene.env_origins
        Rb = matrix_from_quat(r.data.root_quat_w.torch).transpose(1, 2)          # 세계 → 로봇
        pb = r.data.root_pos_w.torch
        to_b = lambda v: torch.einsum('nij,nj->ni', Rb, v)
        q = r.data.joint_pos.torch[:, self.arm_ids]
        qd = r.data.joint_vel.torch[:, self.arm_ids]
        dst_w = o + self.dst
        dst_onehot = torch.zeros(self.num_envs, 12, device=self.device)
        dst_onehot[self.dst_cell >= 0, self.dst_cell[self.dst_cell >= 0]] = 1
        src_onehot = torch.zeros_like(dst_onehot)
        src_onehot[self.src_cell >= 0, self.src_cell[self.src_cell >= 0]] = 1
        t_left = 1 - self.episode_length_buf.float() / self.max_episode_length
        policy = torch.cat([
            q - self.home, 0.1 * qd,                                               # 5 + 5
            ((self.grip_q - GRIPPER_CLOSE) / (GRIPPER_OPEN - GRIPPER_CLOSE))[:, None],
            (self.grip_eff / 20.0)[:, None],                                        # 그리퍼 힘 (실물 = 전류)
            to_b(self.grasp_w - pb),                                                # 손 위치 3
            to_b(self.wrist_R[:, :, 2]), to_b(self.wrist_R[:, :, 1]),               # 손 방향 6
            to_b(self.work_w - self.grasp_w), to_b(self.work_up),                   # 퍽 3 + 3
            to_b(dst_w - self.work_w), to_b(dst_w - self.grasp_w),                  # 목표 3 + 3
            self.task_store[:, None].float(), (~self.task_store)[:, None].float(),  # 2
            self.stored.float(), dst_onehot, src_onehot,                            # 12 · 12 · 12
            self.grasped[:, None].float(), self.placed[:, None].float(),            # 2
            self.prev_actions, t_left[:, None]], -1)                                # 6 + 1
        d = torch.stack(list(self.dist.values()), 1).clamp(-0.05, 0.1) * 10
        critic = torch.cat([d, (self.self_force / 10).clamp(max=1)[:, None], (self.stored_moved * 100)[:, None], self.clean[:, None].float(),
                            self._work_state()[2]], -1)
        fix = lambda x: torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0).clamp(-100, 100)   # 물리가 터진 env 는 _get_dones 가 리셋
        return {'policy': fix(policy), 'critic': fix(critic)}
