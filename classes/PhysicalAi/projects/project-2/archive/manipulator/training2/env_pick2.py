"""1번 적재 모델 · 집기 정책 (사용자 2026-11-13 단계 보상): env_pick 장면 그대로 + 해낸 단계마다 보상 (퍽 하나당 한 번, 순서대로).
  ① 다가가기: 그리퍼 열린 채 손끝이 퍽 윗면보다 10 mm (퍽 높이 1/3) 넘게 내려와 퍽을 감쌈 (가로 8 mm 안) · 퍽 밀림 2 mm 이하
  ② 쥐기: ① 뒤 손가락이 퍽 폭에서 멈춰 쥠 (env.py 쥠 판정) · 그때까지 퍽 밀림 · 눌림 2 mm 이하
  ③ 들기: ② 뒤 쥔 채 20 mm 넘게 들어 10 스텝 이어짐 (= 성공)
누운 퍽은 따로 (세우기 정책) → 여기서는 선 네모 · 원기둥만 작업 퍽.
보고 집기 (사용자 2026-11-13): 정책은 퍽 정답 위치를 모름 → 손목 D435 (URDF camera_joint 보정값, 컬러 69×42°) 로 보일 때만 본 위치 (오차 포함).
  안 보이면 "안 보임" 만 (기억 없음). 30 % 에피소드는 J1 을 돌려 퍽이 안 보이게 시작 → 스테이션 쪽을 둘러봐 찾기.
  오차 = 잡음 단계 × (에피소드 고정 치우침 ±10 mm + 스텝마다 ±5 mm) × (거리/0.4 m)² (0.05–1): 멀면 최대 ±15 mm, 쥐기 직전 12 cm 면 ±1.4 mm (가까이서는 손가락 · 퍽을 같이 봄).
  둘러보기: 안 보이는 동안 시선 가운데가 스테이션 윗면 (+3 cm) 에 닿는 새 방향 (10° 칸) +0.1 (최대 1) · 스테이션 밖을 보면 스텝마다 −0.01 · 발견 (안 보이다 보임, 한 번) +0.2.
  ② 쥐기 (2026-11-13 측정: 혁무님 자세는 왼손가락이 먼저 닿아 퍽을 4–5 mm 밂) = 쥘 때 퍽이 처음 자리에서 옆 2 mm · 아래 2 mm 이하.
  ①-2 가운데 맞추기 (사용자 2026-11-13): 그리퍼 열린 채 퍽이 손가락 사이 (① 깊이) 일 때 닫는 축 어긋남 e 줄인 만큼 (100 /m, 퍼텐셜 차라 머물러도 안 쌓임)
       + 처음 |e| < 1.5 mm 되면 +1. e = 손가락 링크 기준점 좌우 차/2 − 2 mm (쥔 뒤 패드 대칭일 때 링크 차, 2026-11-13 측정).
가치망 (critic) 은 정답 위치를 봄 (학습용, 실물 정책은 안 씀).
"""
import math

import torch

from isaaclab.utils import configclass

from isaaclab.utils.math import matrix_from_quat

from cfg import BOX_TOP, GRIPPER_CLOSE, GRIPPER_OPEN
from env_pick import PickEnvCfg, Training2PickEnv


@configclass
class Pick2EnvCfg(PickEnvCfg):
    bank: str = 'logs/pick_bank_v3.npz'   # 2026-11-14: 혁무님 정차 (면 0.5–3.5 cm · ±3°). 멀거나 삐뚤면 집지 않고 다시 붙음 (dock3)
    lift: float = 0.020
    success: float = 2.0                  # ③
    grasp: float = 0.0                    # 쥠 보상은 ② 로
    in_hand: float = 0.0                  # ① 로
    stage1: float = 1.0
    stage2: float = 2.0
    fail: float = -10.0                   # 바퀴 뜸 · 밀어냄 (k5 바퀴 뜸 4 % → 2026-11-14 −5 에서 올림)
    lift_warn_mm: float = 0.5             # 바퀴 높이 차가 이 위면 스텝마다 감점 (뜨기 전에 조심하게)
    lift_warn: float = -2.0               # [/mm]
    center: float = 100.0                 # ①-2 어긋남 줄인 만큼 [/m]
    center_bonus: float = 1.0
    center_tol: float = 0.0015
    finger_asym: float = 0.002
    depth: float = 0.010                  # ① 손끝이 윗면 아래로 이만큼
    side: float = 0.008                   # ① 가로 어긋남 한도
    push: float = 0.002                   # ①② 퍽 옆 밀림 · 아래 눌림 한도
    episode_length_s = 6.0                # 둘러보기 시간
    observation_space = 92                # env_pick 91 + 보임 1
    # 보기 (손목 D435)
    cam_xyz: tuple = (0.085672, 0.001345, 0.004098)          # 팀 URDF camera_joint (wrist_link → wrist_cam_color_optical_frame)
    cam_rpy: tuple = (-2.969292, -0.048951, -1.995706)
    fov_h: float = 69.0
    fov_v: float = 42.0
    near: float = 0.10
    far: float = 1.0
    noise: float = 1.0                    # 잡음 단계 (사용자 t: 최대에서 시작, 성공률 오르면 낮춤)
    noise_step: float = 0.1
    noise_success: float = 0.8            # 최근 성공률이 이보다 높으면 잡음 단계 낮춤
    bias_max: float = 0.010
    jitter_max: float = 0.005
    yaw_bias_max: float = 20.0            # [°] 본 퍽 방향 오차 (치우침 + 스텝마다), 위치처럼 거리로 줄어듦 → 멀면 최대 ±30°
    yaw_jitter_max: float = 10.0
    look_away: float = 0.3                # 안 보이게 시작하는 비율
    look_away_deg: tuple = (25.0, 45.0)
    # 둘러보기 보상
    search: float = 0.1
    search_max: float = 1.0
    off_station: float = -0.01
    found: float = 0.2


class Training2Pick2Env(Training2PickEnv):
    cfg: Pick2EnvCfg

    def __init__(self, cfg: Pick2EnvCfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        keep = (self.b_pucks[:, 0, 3] != 2).nonzero()[:, 0]      # 작업 퍽 = 선 것만
        self.b_robot, self.b_pucks, self.b_q0, self.b_q1 = self.b_robot[keep], self.b_pucks[keep], self.b_q0[keep], self.b_q1[keep]
        self.n_bank = len(keep)
        self.bank_keep = keep                                     # 걸러낸 번호 → 원래 묶음 번호 (영상 글자용)
        self.s1 = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.s2 = torch.zeros_like(self.s1)
        self.sc = torch.zeros_like(self.s1)
        self.s2_done = torch.zeros_like(self.s1)
        self.prev_e = torch.full((self.num_envs,), float('nan'), device=self.device)
        N, dev = self.num_envs, self.device
        r, p, y = cfg.cam_rpy
        Rx = torch.tensor([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
        Ry = torch.tensor([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
        Rz = torch.tensor([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
        self.cam_R = (Rz @ Ry @ Rx).float().to(dev); self.cam_t = torch.tensor(cfg.cam_xyz, device=dev)
        fl = [i for i, n in enumerate(self.robot.body_names) if n == 'gripper_left_link']
        fr = [i for i, n in enumerate(self.robot.body_names) if n == 'gripper_right_link']
        self.finger_ids = fl + fr
        self.bias = torch.zeros(N, 3, device=dev)
        self.yaw_bias = torch.zeros(N, device=dev)
        self.perc_yaw = torch.zeros(N, device=dev)
        self.vis = torch.zeros(N, dtype=torch.bool, device=dev)
        self.perc = torch.zeros(N, 3, device=dev)
        self.ever_lost = torch.zeros_like(self.s1); self.found_given = torch.zeros_like(self.s1)
        self.bins = torch.zeros(N, 36 * 18, dtype=torch.bool, device=dev)
        self.search_sum = torch.zeros(N, device=dev)
        self.away = torch.zeros_like(self.s1)
        self.noise_level = cfg.noise
        print(f'[env_pick2] 선 퍽 장면 {self.n_bank} 개', flush=True)

    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)
        ids = self.robot._ALL_INDICES if env_ids is None else env_ids
        self.s1[ids] = False
        self.s2[ids] = False
        self.sc[ids] = False
        self.s2_done[ids] = False
        self.prev_e[ids] = float('nan')
        ids = torch.as_tensor(ids, device=self.device)
        n = len(ids)
        b = torch.rand(n, 3, device=self.device) * 2 - 1; b[:, 2] *= 0.5
        self.bias[ids] = b * self.cfg.bias_max
        self.yaw_bias[ids] = (torch.rand(n, device=self.device) * 2 - 1) * self.cfg.yaw_bias_max
        self.ever_lost[ids] = False; self.found_given[ids] = False
        self.bins[ids] = False; self.search_sum[ids] = 0
        # 안 보이게 시작: J1 을 ±25–45° 돌림 (손은 스테이션 위 높이 그대로)
        away = torch.rand(n, device=self.device) < self.cfg.look_away
        self.away[ids] = away
        if away.any():
            lo, hi = self.cfg.look_away_deg
            ang = torch.deg2rad(lo + torch.rand(n, device=self.device) * (hi - lo)) * torch.where(torch.rand(n, device=self.device) < 0.5, -1.0, 1.0)
            ang = torch.where(away, ang, torch.zeros_like(ang))
            # 손은 쥘 자리 60 mm 위 (q0, 다른 퍽 위로 비킴) 에서 J1 만 돌림
            qa = torch.where(away[:, None], self.b_q0[self.bi[ids]], self.q_target[ids])
            qa[:, 0] += ang
            q = self.robot.data.default_joint_pos.torch[ids].clone()
            q[:, self.arm_ids] = qa
            q[:, self.grip_ids] = GRIPPER_OPEN
            self.robot.write_joint_position_to_sim_index(position=q, env_ids=ids)
            self.robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q), env_ids=ids)
            self.q_target[ids] = qa
        self.vis[ids] = False                                # 첫 스텝에 봄 (리셋 직후 자세는 다음 물리 뒤 반영)

    def _cam(self):
        bp = self.robot.data.body_pos_w.torch; bq = self.robot.data.body_quat_w.torch
        wR = matrix_from_quat(bq[:, self.wrist_id])
        return bp[:, self.wrist_id] + torch.einsum('nij,j->ni', wR, self.cam_t), wR @ self.cam_R

    def _visible(self, pt, cp, cR, bp):
        v = torch.einsum('nji,nj->ni', cR, pt - cp)
        z = v[:, 2]
        hx = torch.rad2deg(torch.atan2(v[:, 0], z)).abs(); hy = torch.rad2deg(torch.atan2(v[:, 1], z)).abs()
        vis = (z > self.cfg.near) & (z < self.cfg.far) & (hx < self.cfg.fov_h / 2) & (hy < self.cfg.fov_v / 2)
        dp = (pt - cp).norm(dim=-1).clamp(min=1e-4); u = (pt - cp) / dp[:, None]
        occ = torch.zeros_like(vis)
        blockers = [(bp[:, i], 0.008) for i in self.finger_ids]
        o = self.scene.env_origins
        for k in range(self.box_pos.shape[1]):
            blockers.append((torch.where(self.on_box[:, k, None], o + self.box_pos[:, k], torch.full_like(pt, 99.0)), 0.015))
        for k in range(self.cyl_pos.shape[1]):
            blockers.append((torch.where(self.cyl_on[:, k, None], o + self.cyl_pos[:, k], torch.full_like(pt, 99.0)), 0.015))
        for bpt, rad in blockers:
            f = bpt - cp; df = f.norm(dim=-1).clamp(min=1e-4)
            ang = torch.acos(((f / df[:, None]) * u).sum(-1).clamp(-1, 1))
            occ |= (df < dp - 0.02) & (ang < 0.012 / dp + rad / df)
        return vis & ~occ, z

    def _see(self, ids=None):
        cp, cR = self._cam()
        bp = self.robot.data.body_pos_w.torch
        vis, z = self._visible(self.work_w, cp, cR, bp)
        f = ((z.abs() / 0.4) ** 2).clamp(0.05, 1.0)
        jit = (torch.rand_like(self.bias) * 2 - 1) * self.cfg.jitter_max
        perc = self.work_w + self.noise_level * f[:, None] * (self.bias + jit)
        # 본 퍽 방향 (로봇 기준 yaw, 사각 퍽 = 90° 대칭이라 4×각 으로 씀)
        q = torch.where(self.work_is_cyl[:, None], self.work_c.data.root_quat_w.torch, self.work_b.data.root_quat_w.torch)
        Rm = matrix_from_quat(q); Rr = matrix_from_quat(self.robot.data.root_quat_w.torch)
        yaw = torch.atan2(Rm[:, 1, 0], Rm[:, 0, 0]) - torch.atan2(Rr[:, 1, 0], Rr[:, 0, 0])
        yj = (torch.rand_like(yaw) * 2 - 1) * self.cfg.yaw_jitter_max
        pyaw = yaw + torch.deg2rad(self.noise_level * f * (self.yaw_bias + yj))
        if ids is None:
            self.vis, self.perc, self.perc_yaw = vis, perc, pyaw
        else:
            self.vis[ids], self.perc[ids], self.perc_yaw[ids] = vis[ids], perc[ids], pyaw[ids]
        return cp, cR

    def _get_rewards(self):
        rew = super()._get_rewards()
        cf, o = self.cfg, self.scene.env_origins
        was = self.vis.clone()
        cp, cR = self._see()
        # 둘러보기: 안 보이는 동안 시선 가운데 (광축) 가 스테이션 윗면 (+3 cm) 에 닿는 새 방향
        g = cR[:, :, 2]
        tz = o[:, 2] + BOX_TOP
        tt = (tz - cp[:, 2]) / g[:, 2].clamp(max=-1e-3)
        hit = cp + tt[:, None] * g
        bc = o + self.box_c[0]
        on_st = (g[:, 2] < -1e-3) & ((hit[:, :2] - bc[:, :2]).abs() < self.box_h[0, :2] + 0.03).all(-1)
        Rb = matrix_from_quat(self.robot.data.root_quat_w.torch)
        gb = torch.einsum('nji,nj->ni', Rb, g)
        yb = ((torch.rad2deg(torch.atan2(gb[:, 1], gb[:, 0])) + 180) / 10).long().clamp(0, 35)
        pb = ((torch.rad2deg(torch.asin(gb[:, 2].clamp(-1, 1))) + 90) / 10).long().clamp(0, 17)
        k = yb * 18 + pb
        ar = torch.arange(self.num_envs, device=self.device)
        lost = ~self.vis
        new_bin = lost & on_st & ~self.bins[ar, k] & (self.search_sum < cf.search_max - 1e-6)
        self.bins[ar, k] |= lost & on_st
        self.search_sum += cf.search * new_bin.float()
        self.ever_lost |= lost
        found = self.vis & ~was & self.ever_lost & ~self.found_given
        self.found_given |= found
        look = cf.search * new_bin.float() + cf.off_station * (lost & ~on_st).float() + cf.found * found.float()
        d = self.work_w - o - self.src
        pushed = (d[:, :2].norm(dim=-1) > cf.push) | (-d[:, 2] > cf.push)
        top = self.work_w[:, 2] + self.puck_half
        rel = self.grasp_w - self.work_w
        opened = self.grip_target > 0.5 * (GRIPPER_OPEN + GRIPPER_CLOSE)
        in_jaw = opened & (self.grasp_w[:, 2] < top - cf.depth) & (rel[:, :2].norm(dim=-1) < cf.side) & ~pushed
        new1 = ~self.s1 & in_jaw
        self.s1 |= new1
        # ①-2 가운데 맞추기
        bp = self.robot.data.body_pos_w.torch
        L, R = bp[:, self.finger_ids[0]], bp[:, self.finger_ids[1]]
        ax = (R - L) / (R - L).norm(dim=-1, keepdim=True).clamp(min=1e-6)
        dl = ((self.work_w - L) * ax).sum(-1); dr = ((R - self.work_w) * ax).sum(-1)
        e = ((dr - dl) / 2 - cf.finger_asym).abs()
        e = torch.where(in_jaw, e, torch.full_like(e, float('nan')))
        sh = torch.where(~torch.isnan(e) & ~torch.isnan(self.prev_e), cf.center * (self.prev_e - e), torch.zeros_like(e))
        self.prev_e = e
        newc = ~self.sc & in_jaw & (e < cf.center_tol)
        self.sc |= newc
        # 쥠 판정 순간 대신 '처음 쥔 것으로 보인 뒤 첫 보상 스텝' 에 한 번 판정 (2026-11-14 버그: 다른 env 가 리셋되면
        #   _get_observations 가 _compute 를 한 번 더 불러 쥠이 거기서 켜짐 → grasp_new 가 보상에 안 보여 ② 가 거의 안 켜짐)
        chk = self.ever_grasped & ~self.s2_done
        self.s2_done |= chk
        new2 = chk & self.s1 & ~pushed
        self.s2 |= new2
        warn = cf.lift_warn * (self.wheel_lift - cf.lift_warn_mm).clamp(min=0)
        return rew + warn + cf.stage1 * new1.float() + cf.stage2 * new2.float() + look + torch.nan_to_num(sh) + cf.center_bonus * newc.float()

    def _get_observations(self):
        obs = super()._get_observations()
        pol = obs['policy']
        r = self.robot
        Rb = matrix_from_quat(r.data.root_quat_w.torch).transpose(1, 2)
        to_b = lambda v: torch.einsum('nij,nj->ni', Rb, v)
        v = self.vis[:, None].float()
        true = torch.cat([pol[:, 21:33], pol[:, 88:91]], -1)                  # 정답 (가치망만)
        lift = torch.tensor([0, 0, self.cfg.lift], device=self.device)
        pol = pol.clone()
        pol[:, 21:24] = v * to_b(self.perc - self.grasp_w)                     # 본 퍽 (손 기준)
        box = v * (~self.work_is_cyl[:, None]).float()                         # 본 퍽 방향 (2026-11-14, 사각만 · 보일 때만) + 원기둥 표시 (인식 종류)
        pol[:, 24:26] = box * torch.stack([torch.sin(4 * self.perc_yaw), torch.cos(4 * self.perc_yaw)], -1)
        pol[:, 26:27] = v * self.work_is_cyl[:, None].float()
        pol[:, 27:30] = to_b(lift.expand(self.num_envs, 3))
        pol[:, 30:33] = v * to_b(self.perc + lift - self.grasp_w)
        pol[:, 88:91] = 0                                                      # 다른 퍽 정답 위치 빼기
        pol = torch.cat([pol, v], -1)
        return {'policy': torch.nan_to_num(pol).clamp(-10, 10), 'critic': torch.cat([obs['critic'], torch.nan_to_num(true).clamp(-10, 10)], -1)}

    def _get_dones(self):
        terminated, timeout = super()._get_dones()
        self.ev['success'] &= self.s2                        # ③ 은 ② 뒤에만 (밀거나 눌러 쥐면 들어도 보상 없음)
        return terminated, timeout

    def _log_and_curriculum(self, ids):
        if self.dist:
            log = self.extras.setdefault('log', {})
            log['Pick/s1_approach'] = self.s1[ids].float().mean()
            log['Pick/s2_grasp'] = self.s2[ids].float().mean()
            log['Pick/s1b_center'] = self.sc[ids].float().mean()
            log['Pick/start_away'] = self.away[ids].float().mean()
            a = self.away[ids]
            log['Pick/found_when_away'] = (self.found_given[ids] | ~self.ever_lost[ids])[a].float().mean() if a.any() else torch.tensor(0.0)
            log['Pick/search_sum'] = self.search_sum[ids].mean()
            log['Pick/noise_level'] = torch.tensor(self.noise_level)
            if self.fixed is None and len(self.recent_p) >= self.cfg.curr_window // 2 and self.level >= self.cfg.start_max - 1e-6:
                import numpy as np
                if np.mean(self.recent_p) > self.cfg.noise_success and self.noise_level > 0.1 + 1e-6:
                    self.noise_level = round(self.noise_level - self.cfg.noise_step, 2); self.recent_p.clear()
                    print(f'[env_pick2] 잡음 단계 {self.noise_level:.1f}', flush=True)
        super()._log_and_curriculum(ids)
