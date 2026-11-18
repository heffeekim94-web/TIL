#!/usr/bin/env python3
"""학습2 받침 세우기 보정 학습 (사용자 2026-11-16 "받침 세우기부터"): 받침에 35–50° 기운 퍽을 lift 방식 기본 경로
(가운데를 긴 변과 나란히 쥠 → 축 따라 살짝 듦 → 공중에서 돌려 세움 → 수직으로 내려놓음, 2026-11-15 stand_loop --mode lift) 로 세우고,
정책은 관절 목표에 작은 보정만 더함 (env_res 와 같은 방식). 43° 넘게 기운 퍽이 세우다 넘어지는 것 (22 번 중 3 번) 을 고치려는 것.

장면 묶음 (bank) 만들기 — 두 단계:
  1) 받침에 퍽을 기울여 놓고 가라앉힌 자세 모음 (Isaac):
     $PY env_stand.py settle --lib <far_loop.npz> --out logs/stand_settle_v1.npz --num_envs 64 --rounds 8
  2) 자세마다 기본 경로 (CPU IK, Isaac 안 씀):
     $PY env_stand.py paths --lib <far_loop.npz> --settle logs/stand_settle_v1.npz --out logs/stand_bank_v1.npz
학습: $PY train.py --stand --run_name s1   (기본 경로만 시험: --stand --set scripted=...)
에피소드: 봄 자세 (받침 위, 손 벌림) 에서 시작 → 기본 경로 + 보정 → 경로 끝 + settle → 끝.
성공: 손 뺀 뒤 퍽 기울기 3° 안 · 받침 가운데 5 mm 안 · 바닥에 앉음 · 손끝이 퍽 윗면 15 mm 넘게 위.
감점: 넘어짐 (처음보다 15° 넘게 더 기욺 → 끝), 몸체 · 받침 충돌, 바퀴 뜸, 몸체 밀림, 보정 크기 · 변화.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TILT_LO, TILT_MID, TILT_HI = 35.0, 43.0, 50.0       # 시작 기울기 [°]: 절반은 43° 넘게 (넘어진 퍽은 다 43–45°)
AZ_MAX = 15.0                                        # 기운 방향: 바깥 (팔 평면) ± 이만큼 [°]


# ---------------------------------------------------------------------------- 기본 경로 (stand_loop --mode lift 그대로)
# 2026-11-16 사용자 "쥐는 동작 고치기 · 넷 다 시험": 43° 넘는 퍽이 쥘 때 · 들기 시작할 때 손 안에서 넘어감 → 쥐는 동작 변형
#   base: 지금 그대로 · A: 더 아래 쥠 (바닥에서 18 mm) · B: 처음 들 때 수직 (+Z) · C: 넓게 벌리고 더 멀리서 들어감
#   D: 축 따라 들기 빼고, 쥔 직후 바닥 쪽을 중심으로 먼저 1/3 세운 뒤 옮기며 마저 세움
#   2026-11-18 손 들어오는 길 (B 에 덧붙임, 사용자 "손 들어오는 길 고치기"):
#   W: 들어올 때 넓게 벌림 (59 mm) · O: 반대쪽에서 옆으로 넣음 · T: 옆 말고 퍽 축 따라 위에서 내려 감쌈
VARIANTS = ('base', 'A', 'B', 'C', 'D', 'BW', 'BO', 'BT', 'BTW')


def lift_path(qm, c, u, variant='base'):
    """c, u = 본 퍽 가운데 · 축 (pathgen 좌표). 반환 Path 또는 None (IK 안 됨)."""
    import pathgen as pg
    import store2 as s2
    from store2 import Z, nearest_ik, PARK, LENGTH
    P = s2.Path(qm)
    fz, sc_ = PARK['floor_z'], PARK['center']
    th0 = np.arccos(np.clip(u[2], -1, 1))
    b0 = c - (LENGTH / 2) * u
    ga = 0.018 if variant == 'A' else LENGTH / 2                     # 손끝 = 퍽 가운데 (A: 바닥에서 18 mm)
    p0 = b0 + ga * u
    rr = np.r_[(p0[:2] - s2.J1XY) / np.linalg.norm(p0[:2] - s2.J1XY), 0.0]; cl = np.r_[-rr[1], rr[0], 0.0]
    uf = lambda th: np.sin(th) * rr + np.cos(th) * Z
    nv = -np.cos(th0) * rr + np.sin(th0) * Z                         # 옆으로 넣는 방향 (퍽 축에 수직, 위쪽)
    if variant.startswith('B') and 'T' in variant:
        pre = p0 + 0.04 * u
    elif variant.startswith('B') and 'O' in variant:
        pre = p0 - 0.03 * nv
    else:
        pre = p0 + (0.045 if variant == 'C' else 0.03) * nv
    opn = pg.OPEN_WIDE if variant == 'C' or (variant.startswith('B') and 'W' in variant) else pg.OPEN_NARROW
    bt = np.r_[sc_, fz + 0.006]
    bdown = np.r_[sc_, fz + 0.001]
    got = None
    for lift in ((0.002,) if variant == 'D' else (0.008, 0.006, 0.004)):
        b1 = b0 + lift * (Z if variant[0] in 'BD' else u)
        if variant == 'D':                                             # 바닥 쪽 그대로 두고 1/3 세움 (4 걸음) → 옮기며 마저 (8 걸음)
            th1 = th0 * 2 / 3
            rot = [(b1, th0 - (th0 - th1) * j / 4) for j in range(1, 5)] + [(b1 + (bt - b1) * j / 8, th1 * (1 - j / 8)) for j in range(1, 9)]
        else:
            rot = [(b1 + (bt - b1) * j / 12, th0 * (1 - j / 12)) for j in range(1, 13)]
        pts = [(pre, -uf(th0)), (p0, -uf(th0)), (b1 + ga * u, -uf(th0))] + [(bb + ga * uf(th), -uf(th)) for bb, th in rot] + [(bdown + ga * Z, -Z), (bdown + (ga + 0.045) * Z, -Z)]
        for c0 in (cl, -cl):
            if all(nearest_ik(pt_, a_, c0, P.q[-1])[1] or nearest_ik(pt_, a_, c0, s2.TEMPLATE)[1] for pt_, a_ in pts):
                got = (c0, lift, rot, b1); break
        if got:
            break
    if got is None:
        return None
    cc, lift, rot, b1 = got
    P.hold(10, '봄')
    P.go(pre, -uf(th0), cc, '몸 쪽 위 (손 = 퍽 축과 나란히)', step=0.003, wa=1.0)
    P.hold(10, '벌림', g=f'release:{opn}')
    P.go(p0, -uf(th0), cc, '옆으로 넣어 감쌈', step=0.001)
    P.hold(10, '쥠', g='close')
    P.go(b1 + ga * u, -uf(th0), cc, '살짝 듦', step=0.0005)
    for bb, th in rot:
        P.go(bb + ga * uf(th), -uf(th), cc, '공중에서 돌려 세움', step=0.001)
    P.go(bdown + ga * Z, -Z, cc, '수직으로 내려놓음', step=0.0005)
    P.hold(10, '놓음', g=f'release:{opn}')
    P.go(bdown + (ga + 0.045) * Z, -Z, cc, '손 뺌 (위로, 퍽 윗면 15 mm 위까지)', step=0.002)
    return P


def _one_path(job):
    i, qm, c, u, g0, seed, variant = job
    from library import grip_values
    rng = np.random.default_rng(seed)
    c = c + rng.normal(0, 0.0015, 3)                                 # 가까이서 본 오차 (stand_loop seen 과 같음)
    ang = np.radians(rng.normal(0, 1.5)); ax = np.cross(u, rng.normal(size=3)); ax /= np.linalg.norm(ax)
    u = u * np.cos(ang) + np.cross(ax, u) * np.sin(ang); u /= np.linalg.norm(u)
    try:
        P = lift_path(qm, c, u, variant)
    except Exception as e:                                           # noqa: BLE001
        return i, None, f'{type(e).__name__}: {e}'
    if P is None:
        return i, None, 'IK 안 됨'
    Q, G, N = P.out(); g = grip_values(G)
    first = next((j for j, e in enumerate(G) if e != '-'), len(G)); g[:first] = g0
    kfree = next(j for j, nm in enumerate(N) if nm == '공중에서 돌려 세움')   # 쥐고 살짝 든 뒤 첫 경유점 (보정 끄기 끝)
    return i, (np.asarray(Q, np.float32), g.astype(np.float32), kfree), ''


def _base_meta(lib):
    z = np.load(lib)
    m = json.loads(str(z['meta'][0]))
    return z, m, int(m['n_prefix'])


def make_paths(lib, settle, out, workers=2, variant='base', min_tilt=0.0):
    import pathgen as pg
    from multiprocessing import Pool
    z, m, n0 = _base_meta(lib)
    q_cmd = z['Q'][0, n0 - 1].astype(float); g0 = float(z['G'][0, n0 - 1])
    qm = np.array(pg.to_qm(q_cmd), float); qm[1:] = (qm[1:] + np.pi) % (2 * np.pi) - np.pi   # stand_loop _qm_wrap
    S = np.load(settle)
    jobs = [(i, qm, S['c'][i].astype(float), S['u'][i].astype(float), g0, 1000 + i, variant)
            for i in range(len(S['c'])) if S['tilt'][i] >= min_tilt]
    with Pool(workers) as pool:
        R = sorted(pool.map(_one_path, jobs), key=lambda r: r[0])
    ok = [r for r in R if r[1] is not None]
    bad = [r for r in R if r[1] is None]
    L = max(len(r[1][0]) for r in ok)
    Qs = np.zeros((len(ok), L, 5), np.float32); Gs = np.zeros((len(ok), L), np.float32); ns = np.zeros(len(ok), np.int64); kf = np.zeros(len(ok), np.int64)
    metas = []
    for j, (i, (Q, g, kf[j]), _) in enumerate(ok):
        Qs[j, :len(Q)], Gs[j, :len(Q)] = Q, g
        Qs[j, len(Q):], Gs[j, len(Q):] = Q[-1], g[-1]
        ns[j] = len(Q)
        mm = dict(m); mm.pop('names', None); mm['n_prefix'] = 0
        mm['stand'] = dict(pos=S['pos'][i].tolist(), quat=S['quat'][i].tolist(), dst=S['dst'][i].tolist(),
                           tilt=float(S['tilt'][i]), src=int(i))
        metas.append(json.dumps(mm, ensure_ascii=False))
    np.savez_compressed(out, Q=Qs, G=Gs, n=ns, kfree=kf, meta=np.array(metas))
    t = S['tilt'][[r[0] for r in ok]]
    print(f'[paths] 경로 {len(ok)} / {len(R)} (IK 안 됨 {len(bad)}: 기울기 {np.round(S["tilt"][[r[0] for r in bad]], 0).tolist()[:20]}) · '
          f'경유점 최대 {L} · 기울기 {t.min():.0f}–{t.max():.0f}° (43° 넘음 {np.mean(t > 43):.2f}) → {out}', flush=True)


# ---------------------------------------------------------------------------- 학습 env
def _env_classes():
    import torch
    from isaaclab.utils import configclass
    from isaaclab.utils.math import matrix_from_quat
    from cfg import GRIPPER_HOLD
    from env_res import ResEnvCfg, Training2ResEnv

    @configclass
    class StandEnvCfg(ResEnvCfg):
        library: str = 'logs/stand_bank_v1.npz'
        settle_steps: int = 45                # 손 뺀 뒤 기다림 (1.5 s) — 놓은 퍽이 그 뒤에 넘어가는지 봄
        ok_tilt_deg: float = 3.0
        ok_xy: float = 0.005
        ok_z: float = 0.004
        ok_hand: float = 0.015
        fall_deg: float = 15.0                # 처음 기울기보다 이만큼 더 기울면 넘어짐 → 끝
        stand_ok: float = 10.0
        fall: float = -5.0
        end_tilt: float = -0.1                # 끝 기울기 [°] 당 (60° 까지)
        focus_lo: float = 43.0                # 2026-11-16 사용자 "43–46° 더 학습": 이 구간 장면을 focus_frac 만큼 더 뽑음
        focus_hi: float = 46.0
        focus_frac: float = 0.0               # 0 = 고르게 (s1)
        mask_grasp: bool = False              # 2026-11-17 사용자 "쥐기·들기 보정 끄기": 쥐고 살짝 들 때까지 (kfree 전) 보정 0

    class Training2StandEnv(Training2ResEnv):
        cfg: StandEnvCfg

        def __init__(self, cfg, render_mode=None, **kwargs):
            super().__init__(cfg, render_mode, **kwargs)
            N, dev = self.num_envs, self.device
            st = [m['stand'] for m in self.lib_meta]
            self.st_pos = torch.tensor([s['pos'] for s in st], device=dev, dtype=torch.float32)
            self.st_quat = torch.tensor([s['quat'] for s in st], device=dev, dtype=torch.float32)
            self.st_dst = torch.tensor([s['dst'] for s in st], device=dev, dtype=torch.float32)
            self.st_tilt = torch.tensor([s['tilt'] for s in st], device=dev, dtype=torch.float32)
            self.tilt0 = torch.zeros(N, device=dev)
            self.st_ok = torch.zeros(N, dtype=torch.bool, device=dev)
            self.st_fell = torch.zeros(N, dtype=torch.bool, device=dev)
            self.st_end = torch.zeros(N, device=dev)
            self.st_diag = torch.zeros(N, 3, device=dev)        # 끝: 받침 가운데에서 [mm] · 높이 차 [mm] · 손끝 − 퍽 윗면 [mm]
            self.kfree = None
            lib = np.load(HERE / self.cfg.library)            # 절대 경로면 HERE 무시됨
            if self.cfg.mask_grasp:
                assert 'kfree' in lib, '은행에 kfree 없음 (paths 다시 만들기)'
                self.kfree = torch.tensor(lib['kfree'], device=dev, dtype=torch.long)
                print(f'[env_stand] 쥐기·들기 보정 끔: 경유점 {int(self.kfree.min())}–{int(self.kfree.max())} 전까지', flush=True)
            # 2026-11-18 사용자 "쥘 때 기울기 재기": 쥠 (그리퍼가 처음 닫히는 경유점) · 살짝 든 뒤 (kfree) 의 퍽 기울기 기록
            Gl = lib['G']
            self.k_close = torch.tensor([int(np.argmax(Gl[i] <= Gl[i].min() + 1e-6)) for i in range(len(Gl))], device=dev)   # 처음 닫는 경유점
            self.k_free = torch.tensor(lib['kfree'], device=dev) if 'kfree' in lib else self.k_close + 14
            self.tilt_close = torch.zeros(N, device=dev); self.tilt_free = torch.zeros(N, device=dev)
            self.reset()                                        # 첫 에피소드도 받침 장면에서 (안 하면 퍽이 처음 자리라 바로 '넘어짐', 2026-11-16 smoke)
            print(f'[env_stand] 장면 {len(st)} · 기울기 {float(self.st_tilt.min()):.0f}–{float(self.st_tilt.max()):.0f}°', flush=True)

        def _reset_idx(self, env_ids):
            from collections import deque
            focus = None
            if self.fixed is None and self.cfg.focus_frac > 0 and hasattr(self, 'st_tilt'):
                n = len(env_ids) if env_ids is not None else self.num_envs
                inr = ((self.st_tilt >= self.cfg.focus_lo) & (self.st_tilt < self.cfg.focus_hi)).nonzero()[:, 0]
                pick = torch.randint(0, len(self.st_tilt), (n,), device=self.device)
                take = torch.rand(n, device=self.device) < self.cfg.focus_frac
                pick[take] = inr[torch.randint(0, len(inr), (int(take.sum()),), device=self.device)]
                focus = deque(pick.tolist()); self.fixed = focus
            try:
                super()._reset_idx(env_ids)
            finally:
                if focus is not None:
                    self.fixed = None
            if not hasattr(self, 'st_pos'):
                return
            ids = torch.as_tensor(env_ids if env_ids is not None else self.robot._ALL_INDICES, device=self.device)
            for e in ids.tolist():
                li = int(self.li[e])
                self._put(self.work_b, e, self.st_pos[li], self.st_quat[li])
            self.src_cell[ids] = 99                           # 받침 ↔ 작업 퍽 닿음은 충돌로 안 셈
            self.dst[ids] = self.st_dst[self.li[ids]]
            self.dst_cell[ids] = -1
            self.tilt0[ids] = self.st_tilt[self.li[ids]]
            self.st_ok[ids] = False; self.st_fell[ids] = False; self.st_end[ids] = 0
            if hasattr(self, 'tilt_close'):
                self.tilt_close[ids] = self.tilt0[ids]; self.tilt_free[ids] = self.tilt0[ids]
            self._follow_robot()
            self._stale = True

        def _pre_physics_step(self, actions):
            if getattr(self, 'kfree', None) is not None:
                actions = actions.clamp(-1.0, 1.0) * (self._k() >= self.kfree[self.li]).float()[:, None]
            super()._pre_physics_step(actions)

        def _stand_state(self):
            tilt = torch.rad2deg(torch.acos(self.work_up[:, 2].clamp(-1, 1)))
            dw = self.work_w - (self.scene.env_origins + self.dst)
            ok = ((tilt <= self.cfg.ok_tilt_deg) & (dw[:, :2].norm(dim=-1) <= self.cfg.ok_xy) & (dw[:, 2].abs() <= self.cfg.ok_z)
                  & (self.grasp_w[:, 2] - (self.work_w[:, 2] + 0.030) > self.cfg.ok_hand))
            self.st_diag_now = torch.stack([dw[:, :2].norm(dim=-1) * 1000, dw[:, 2] * 1000, (self.grasp_w[:, 2] - (self.work_w[:, 2] + 0.030)) * 1000], -1)
            return tilt, ok

        def _get_dones(self):
            self._compute()
            self.ev['bad'] = self._bad_state()
            o = self.scene.env_origins
            closed = self.grip_target < GRIPPER_HOLD + 0.002
            self.holding = (self.holding | self.grasped) & closed
            far = (self.work_w - self.grasp_w).norm(dim=-1) > 0.04
            self.ev['drop'] = (self.holding & far) | (self.work_w[:, 2] - o[:, 2] < 0.04)
            bz = matrix_from_quat(self.robot.data.root_quat_w.torch)[:, :, 2]
            self.body_tilt = torch.rad2deg(torch.acos(bz[:, 2].clamp(-1, 1)))
            wz = self.robot.data.body_pos_w.torch[:, self.wheel_ids, 2]
            self.wheel_lift = (wz.amax(1) - wz.amin(1)) * 1000
            self.body_angvel = self.robot.data.root_ang_vel_w.torch.square().sum(1)
            self.stable &= (self.body_tilt <= self.cfg.stab_tilt_deg) & (self.wheel_lift <= self.cfg.stab_lift_mm)
            self.ep_tilt = torch.maximum(self.ep_tilt, self.body_tilt)
            tilt, ok = self._stand_state()
            self.ev['fell'] = tilt > self.tilt0 + self.cfg.fall_deg
            self.ev['lifted'] = self.wheel_lift > self.cfg.stab_lift_mm
            done_path = self.t >= 2 * self.libN[self.li] + self.cfg.settle_steps
            self.ev['end'] = done_path
            self.ev['success'] = done_path & ok
            self.st_tilt_now = tilt
            k = self._k()
            self.tilt_close = torch.where(k <= self.k_close[self.li], tilt, self.tilt_close)   # 쥐는 경유점까지 계속 덮어씀 → 쥐는 순간 값
            self.tilt_free = torch.where(k <= self.k_free[self.li], tilt, self.tilt_free)
            terminated = self.ev['severe'] | self.ev['drop'] | self.ev['bad'] | self.ev['lifted'] | self.ev['fell']
            if self.no_terminate:
                terminated = torch.zeros_like(terminated)
            fin = terminated | done_path
            self.st_ok |= self.ev['success']; self.st_fell |= self.ev['fell']
            self.st_end = torch.where(fin, tilt, self.st_end)
            self.st_diag = torch.where(fin[:, None], self.st_diag_now, self.st_diag)
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
                '세움': self.cfg.stand_ok * (ev['success'] & self.clean).float(),
                '넘어짐': self.cfg.fall * ev['fell'].float(),
                '끝기울기': self.cfg.end_tilt * self.st_tilt_now.clamp(max=60) * ev['end'].float(),
                '기울기': self.cfg.stab_tilt * (self.body_tilt - self.cfg.stab_tilt_deg).clamp(min=0),
                '바퀴뜸': self.cfg.stab_lift * (self.wheel_lift - self.cfg.stab_lift_mm).clamp(min=0),
                '바퀴뜸실패': self.cfg.lift_fail * ev['lifted'].float(),
                '흔들림속도': self.cfg.stab_angvel * self.body_angvel,
                '보정크기': self.cfg.res_penalty * a.square().sum(1),
                '보정변화': rw.action_rate * (a - pa).square().sum(1)}
            if not hasattr(self, 'ep_parts'):
                self.ep_parts = {k: torch.zeros(self.num_envs, device=self.device) for k in parts}
            for k_, v_ in parts.items():
                self.ep_parts[k_] += torch.nan_to_num(v_)
            self.prev_actions = a.clone()
            return torch.nan_to_num(sum(parts.values()), nan=0.0, posinf=0.0, neginf=0.0)

        def _log_and_curriculum(self, ids):
            if hasattr(self, 'st_ok') and self.dist:
                log = self.extras.setdefault('log', {})
                log['Stand/success'] = self.st_ok[ids].float().mean()
                log['Stand/fell'] = self.st_fell[ids].float().mean()
                log['Stand/end_tilt_deg'] = self.st_end[ids].mean()
                big = self.tilt0[ids] > TILT_MID
                if big.any():
                    log['Stand/success_over43'] = self.st_ok[ids][big].float().mean()
            if self.record is not None and hasattr(self, 'st_ok'):
                for e in torch.as_tensor(ids).tolist():
                    if int(self.episode_length_buf[e]) == 0:     # 처음 리셋 (에피소드 아님)
                        continue
                    self.record.append(dict(env=e, li=int(self.li[e]), tilt0=float(self.tilt0[e]), ok=bool(self.st_ok[e]),
                                            fell=bool(self.st_fell[e]), end_tilt=float(self.st_end[e]), clean=bool(self.clean[e]),
                                            t_close=float(self.tilt_close[e]), t_free=float(self.tilt_free[e]),
                                            diag=[round(float(x), 1) for x in self.st_diag[e]]))
                rec, self.record = self.record, None
                try:
                    super()._log_and_curriculum(ids)
                finally:
                    self.record = rec
                return
            super()._log_and_curriculum(ids)

    return StandEnvCfg, Training2StandEnv


def __getattr__(name):                                  # from env_stand import StandEnvCfg, Training2StandEnv (Isaac 뜬 뒤에만)
    if name in ('StandEnvCfg', 'Training2StandEnv'):
        c, e = _env_classes()
        globals().update(StandEnvCfg=c, Training2StandEnv=e)
        return globals()[name]
    raise AttributeError(name)


# ---------------------------------------------------------------------------- 1) 가라앉힌 자세 모음 (Isaac)
def settle_main(argv):
    import argparse
    from isaaclab.app import AppLauncher
    p = argparse.ArgumentParser()
    p.add_argument('--lib', required=True); p.add_argument('--out', required=True)
    p.add_argument('--num_envs', type=int, default=64); p.add_argument('--rounds', type=int, default=8)
    p.add_argument('--settle', type=int, default=60); p.add_argument('--seed', type=int, default=0)
    AppLauncher.add_app_launcher_args(p)
    a = p.parse_args(argv); a.headless = True
    app = AppLauncher(a).app
    sys.path.insert(0, str(HERE))
    import torch
    from isaaclab.utils.math import matrix_from_quat, quat_from_matrix
    from env_res import ResEnvCfg, Training2ResEnv
    import store2 as s2
    rng = np.random.default_rng(a.seed)
    N = a.num_envs
    z, m, n0 = _base_meta(a.lib)
    q_cmd, g0 = z['Q'][0, n0 - 1], float(z['G'][0, n0 - 1])
    mm = dict(m); mm.pop('names', None)
    rep = str(HERE / 'logs' / '_stand_settle_lib.npz')
    np.savez_compressed(rep, Q=np.repeat(q_cmd[None, None], N, 0).repeat(30, 1), G=np.full((N, 30), g0, np.float32),
                        n=np.full(N, 30), meta=np.array([json.dumps(mm, ensure_ascii=False)] * N))
    cfg = ResEnvCfg(); cfg.library = rep; cfg.scene.num_envs = N
    env = Training2ResEnv(cfg); env.set_fixed(range(N)); env.no_terminate = True
    dev = env.device
    fz, sc = s2.PARK['floor_z'], s2.PARK['center']
    out = {k: [] for k in ('pos', 'quat', 'dst', 'c', 'u', 'tilt', 'tilt_spawn')}
    for rd in range(a.rounds):
        with torch.inference_mode():                  # 두 번째 리셋부터는 inference 텐서를 고침 (2026-11-16)
            env.set_fixed(range(N)); env.reset()
            for _ in range(5):
                env.step(torch.zeros(N, 6, device=dev))
        Rb = matrix_from_quat(env.robot.data.root_quat_w.torch)                  # 로봇 → 세계
        pb = env.robot.data.root_pos_w.torch
        o = env.scene.env_origins
        th = np.where(rng.random(N) < 0.5, rng.uniform(TILT_LO, TILT_MID, N), rng.uniform(TILT_MID, TILT_HI, N))
        az = np.radians(rng.uniform(-AZ_MAX, AZ_MAX, N))
        rr = (sc - s2.J1XY) / np.linalg.norm(sc - s2.J1XY); ang0 = np.arctan2(rr[1], rr[0])     # 바깥 = 팔 평면 방향
        for e in range(N):
            t = np.radians(th[e]); d = np.r_[np.cos(ang0 + az[e]), np.sin(ang0 + az[e]), 0]
            u = np.sin(t) * d + np.r_[0, 0, np.cos(t)]
            # 밑동 (아래 끝면 가운데): 2026-11-15 cells 로그에서 기울기 37–45° 때 x 96 → 91 mm, z 145 → 149 mm (pathgen)
            b = np.r_[sc[0] - 0.0063 - 0.0009 * (th[e] - 40) * np.cos(az[e]), sc[1] + rng.uniform(-0.002, 0.002) - 0.0009 * (th[e] - 40) * np.sin(az[e]),
                      0.1455 + 0.0007 * (th[e] - 40) + 0.002]
            cen = b + 0.030 * u
            ax = np.cross([0, 0, 1.0], u); ax /= np.linalg.norm(ax)
            yw = np.radians(rng.uniform(-5, 5))
            K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            R_tilt = np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
            R_yaw = np.array([[np.cos(ang0 + az[e] + yw), -np.sin(ang0 + az[e] + yw), 0], [np.sin(ang0 + az[e] + yw), np.cos(ang0 + az[e] + yw), 0], [0, 0, 1]])
            R_loc = torch.tensor(R_tilt @ R_yaw, device=dev, dtype=torch.float32)
            pw = pb[e] + Rb[e] @ torch.tensor(cen + np.r_[0, 0, 0.034], device=dev, dtype=torch.float32)
            qw = quat_from_matrix(Rb[e] @ R_loc)
            env._put(env.work_b, e, pw - o[e], qw)
        with torch.inference_mode():
            for _ in range(a.settle):
                env.step(torch.zeros(N, 6, device=dev))
        Rb = matrix_from_quat(env.robot.data.root_quat_w.torch); pb = env.robot.data.root_pos_w.torch
        pw, qw = env.work_b.data.root_pos_w.torch, env.work_b.data.root_quat_w.torch
        vel = env.work_b.data.root_lin_vel_w.torch.norm(dim=-1)
        Ru = matrix_from_quat(qw)[:, :, 2]
        kept = 0
        for e in range(N):
            c = (Rb[e].T @ (pw[e] - pb[e])).cpu().numpy(); c[2] -= 0.034
            u = (Rb[e].T @ Ru[e]).cpu().numpy()
            tl = float(np.degrees(np.arccos(np.clip(u[2], -1, 1))))
            if not (28 <= tl <= 56) or np.linalg.norm(c[:2] - sc) > 0.03 or float(vel[e]) > 0.01:
                continue
            dst = (pb[e] + Rb[e] @ torch.tensor(np.r_[sc, fz + 0.030 + 0.034], device=dev, dtype=torch.float32) - o[e]).cpu().numpy()
            out['pos'].append((pw[e] - o[e]).cpu().numpy()); out['quat'].append(qw[e].cpu().numpy()); out['dst'].append(dst)
            out['c'].append(c); out['u'].append(u); out['tilt'].append(tl); out['tilt_spawn'].append(th[e])
            kept += 1
        print(f'[settle {rd}] 남김 {kept} / {N} · 놓은 기울기 → 가라앉은 기울기 예: '
              + ', '.join(f'{th[e]:.0f}→{np.degrees(np.arccos(np.clip(float(Ru[e, 2]), -1, 1))):.0f}' for e in range(6)), flush=True)
    np.savez(a.out, **{k: np.array(v) for k, v in out.items()})
    t = np.array(out['tilt'])
    print(f'[settle] {len(t)} 자세 · 기울기 {t.min():.0f}–{t.max():.0f}° (43° 넘음 {np.mean(t > 43):.2f}) → {a.out}', flush=True)
    import os
    os._exit(0)                                          # app.close 에서 멈춤 (2026-11-15)


# ---------------------------------------------------------------------------- 3) 평가 · 영상 (기본 경로만 또는 정책)
def play_main(argv):
    """$PY env_stand.py play --library logs/stand_bank_v1.npz --episodes 64 [--checkpoint model.pt] [--mp4 out.mp4 --cam_envs 4]
    같은 장면 번호 (0, 1, 2, …) 를 차례로 → 기본 경로와 정책을 같은 퍽으로 비교할 수 있음."""
    import argparse
    import os
    import subprocess
    import tempfile
    from isaaclab.app import AppLauncher
    p = argparse.ArgumentParser()
    p.add_argument('--library', default='logs/stand_bank_v1.npz'); p.add_argument('--episodes', type=int, default=64)
    p.add_argument('--num_envs', type=int, default=16); p.add_argument('--checkpoint', default='')
    p.add_argument('--mp4', default=''); p.add_argument('--start', type=int, default=0)
    p.add_argument('--src', type=int, default=-1)                     # 자세 번호 (settle) 로 시작 장면 고름 — 변형 은행끼리 같은 퍽 비교
    p.add_argument('--rec', default='')                               # 장면별 결과 json (자세 번호 · 처음° · 성공 · 넘어짐)
    p.add_argument('--mask', action='store_true')                    # 쥐고 살짝 들 때까지 보정 0 (cfg.mask_grasp)
    AppLauncher.add_app_launcher_args(p)
    a = p.parse_args(argv); a.headless = True; a.enable_cameras = bool(a.mp4)
    app = AppLauncher(a).app
    sys.path.insert(0, str(HERE))
    import torch
    StandEnvCfg, Training2StandEnv = _env_classes()
    cfg = StandEnvCfg(); cfg.library = a.library; cfg.scene.num_envs = a.num_envs
    cfg.mask_grasp = a.mask
    if a.mp4:
        import viz
        viz.add_camera(cfg, height=300, width=400)
    raw = Training2StandEnv(cfg)
    nb = len(raw.lib_meta)
    if a.src >= 0:
        a.start = next(i for i, m in enumerate(raw.lib_meta) if m['stand']['src'] == a.src)
    raw.set_fixed([(a.start + i) % nb for i in range(a.episodes + a.num_envs)])
    raw.record = []
    policy = None
    if a.checkpoint:
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from rsl_rl.runners import OnPolicyRunner
        from cfg import TrainCfg
        env = RslRlVecEnvWrapper(raw)
        runner = OnPolicyRunner(env, TrainCfg().runner_dict(), None, env.device)
        runner.load(a.checkpoint)
        policy = runner.get_inference_policy(device=env.device)
        obs = env.get_observations()
    else:
        raw.reset()
    tmpd = Path(tempfile.mkdtemp(prefix='stand_play_'))
    if a.mp4:
        import viz
        viz.aim(raw, eye=(0.17, -0.24, 0.30), target=(0.14, 0.0, 0.18))
        from PIL import Image, ImageDraw, ImageFont
        F = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf', 15)
    nf, it = 0, 0
    L0 = 2 * int(raw.libN[raw.li[0]]) + cfg.settle_steps + 4                 # env 0 첫 에피소드 길이
    with torch.inference_mode():
        while len(raw.record) < a.episodes and it < 20000:
            if policy is not None:
                if os.environ.get('SB_DEBUG') and int(raw._k()[0]) in (0, 30) and it % 2 == 0:
                    print(f'[obs 0 k{int(raw._k()[0])}] ' + json.dumps(np.round(obs['policy'][0].cpu().numpy(), 3).tolist()), flush=True)
                obs, _, _, _ = env.step(policy(obs))
                if os.environ.get('SB_DEBUG') and it % 20 == 0:      # 2026-11-18: stand_loop 에 끼운 것과 보정 크기 비교용
                    print(f'[sB 0] 경유점 {int(raw._k()[0])}/{int(raw.libN[raw.li[0]])} · 걸러진 보정 [rad] {np.round((raw.a_f[0, :5] * raw.cfg.res_scale).cpu().numpy(), 3).tolist()}', flush=True)
            else:
                raw.step(torch.zeros(raw.num_envs, 6, device=raw.device))
            it += 1
            if a.mp4 and it % 2 == 0 and it <= L0:                     # env 0 첫 에피소드만
                im = Image.fromarray(viz.frame(raw)); dr = ImageDraw.Draw(im)
                dr.rectangle((0, 0, 400, 24), fill=(0, 0, 0))
                dr.text((6, 4), f'{"정책" if policy is not None else "기본 경로"} · 장면 {int(raw.li[0])} · 처음 {float(raw.tilt0[0]):.0f}° · 지금 {float(raw.st_tilt_now[0]):.0f}°', font=F, fill=(255, 255, 0))
                im.save(tmpd / f'{nf:05d}.png'); nf += 1
    rec = raw.record[:a.episodes]
    t0 = np.array([r['tilt0'] for r in rec]); ok = np.array([r['ok'] for r in rec]); fell = np.array([r['fell'] for r in rec])
    print(f'[play] {"정책 " + a.checkpoint if policy is not None else "기본 경로"} · {len(rec)} 번 · 성공 {ok.mean():.2f} · 넘어짐 {fell.mean():.2f} · 깨끗 {np.mean([r["clean"] for r in rec]):.2f}', flush=True)
    for lo, hi in ((0, 40), (40, 43), (43, 46), (46, 60)):
        m = (t0 >= lo) & (t0 < hi)
        if m.any():
            print(f'  처음 {lo}–{hi}°: {m.sum()} 번 · 성공 {ok[m].mean():.2f} · 넘어짐 {fell[m].mean():.2f}', flush=True)
    print('  실패 (장면, 처음°, 끝°, [가운데 mm, 높이 mm, 손−윗면 mm]):', [(r['li'], round(r['tilt0']), round(r['end_tilt']), r['diag']) for r in rec if not r['ok']][:30], flush=True)
    if a.rec:
        json.dump([dict(src=raw.lib_meta[r['li']]['stand']['src'], tilt0=float(r['tilt0']), ok=bool(r['ok']), fell=bool(r['fell']),
                        end=float(r['end_tilt']), t_close=r['t_close'], t_free=r['t_free']) for r in rec], open(a.rec, 'w'))
    if a.mp4 and nf:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '15', '-i', str(tmpd / '%05d.png'), '-pix_fmt', 'yuv420p', a.mp4], stdin=subprocess.DEVNULL)   # tmux 뒤에서 stdin 읽다 멈춤 (SIGTTIN, 2026-11-17)
        print(f'[play] MP4 {a.mp4} ({nf} 장)', flush=True)
    os._exit(0)


if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    if sys.argv[1] == 'play':
        play_main(sys.argv[2:])
    elif sys.argv[1] == 'settle':
        settle_main(sys.argv[2:])
    elif sys.argv[1] == 'paths':
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--lib', required=True); p.add_argument('--settle', required=True); p.add_argument('--out', required=True)
        p.add_argument('--workers', type=int, default=2)
        p.add_argument('--variant', default='base', choices=VARIANTS); p.add_argument('--min_tilt', type=float, default=0.0)
        a = p.parse_args(sys.argv[2:])
        make_paths(a.lib, a.settle, a.out, a.workers, a.variant, a.min_tilt)
