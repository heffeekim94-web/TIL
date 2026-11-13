#!/usr/bin/env python3
"""스테이션 집기 학습 (사용자 2026-11-12) 장면 묶음: 박스가 차체와 평행하지 않고 (±20°) 조금 떨어져 (앞면 틈 1–12 cm) 있어도 퍽을 집음.
시뮬 박스는 세계에 고정 (BOX_X, 0) → 로봇을 그 반대로 돌려 · 옮겨 세움. 박스 위 퍽 2–3 개 (선 네모 · 원기둥 · 누운 네모), 작업 퍽 = J1 에서 가장 가까운 퍽.
시작 자세 = 작업 퍽 쥘 자리 60 mm 위, 손 수직 (안 닿으면 팔 평면 안에서 15–45° 기울임, 닫힘축 = 접선 · 네모는 면이 접선에서 35° 안), 그리퍼 열림.
좌표: 로봇 = base_link (pathgen), 박스 · 퍽 = env (세계 − env 원점, 박스 중심 (BOX_X, 0)).
  $PY gen_pick_bank.py 4000 logs/pick_bank_v2.npz   (v2: 쥘 자세 q1 도 저장 → 커리큘럼 시작 높이)
"""
import sys
from multiprocessing import Pool

import numpy as np

import pathgen as pg
import store2 as s2

BOX_X, BOX_HALF, BOX_TOP = 0.2575, 0.1025, 0.070
FRONT = 0.145                       # 차체 앞 끝 (base_link x)
ZB = 0.034                          # base_link 높이 (바닥 위)
SIDE, LEN = 0.030, 0.060
YAW_MAX, GAP = np.radians(20.0), (0.01, 0.12)
DEPTH = 0.013                       # 손끝 = 퍽 윗면 13 mm 아래 (실물 넣기 · 빼기 경로와 같음, env GRIP_DEPTH)
ABOVE = 0.060
SEEDS = [pg.team_unfold()[0][-1]] + [np.array(x) for x in ([0, 0.6, 0.6, -1.0, 0], [0, 0.9, 0.3, -1.2, 0], [0, 0.3, 0.9, -1.2, 0])]


def rot(t):
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])


def solve(p, a, c):
    for sd in SEEDS:
        for cc in (c, -c):
            q, ok = s2.ik_ok(p, a, cc, sd)
            if ok:
                return q, cc
    return None, None


def one(seed):
    rng = np.random.default_rng(seed)
    for _ in range(50):
        psi = rng.uniform(-YAW_MAX, YAW_MAX)                       # 박스 yaw (로봇 기준)
        ly = rng.uniform(-0.06, 0.06)                               # 박스 중심 옆 비킴 (로봇 기준)
        reach_x = BOX_HALF * (abs(np.cos(psi)) + abs(np.sin(psi)))  # 돌린 박스 앞 끝까지 (보수적)
        cx = FRONT + rng.uniform(*GAP) + reach_x
        # 박스 위 퍽 (박스 좌표), 서로 50 mm 넘게
        n = rng.integers(2, 4)
        pk = []
        while len(pk) < n:
            xy = rng.uniform(-BOX_HALF + 0.022, BOX_HALF - 0.022, 2)
            if all(np.linalg.norm(xy - p[0]) > 0.05 for p in pk):
                shape = rng.choice(['box', 'cyl', 'lying'], p=[0.45, 0.30, 0.25])
                pk.append((xy, rng.uniform(-np.pi, np.pi), shape))
        Rb = rot(psi)
        in_rob = [np.r_[cx, ly] + Rb @ p[0] for p in pk]            # 로봇 기준 xy
        order = np.argsort([np.linalg.norm(x - pg.J1XY) for x in in_rob])
        k = int(order[0])
        xy_r, yaw_box, shape = in_rob[k], pk[k][1], pk[k][2]
        yaw_r = yaw_box + psi
        h = SIDE if shape == 'lying' else LEN
        top = BOX_TOP - ZB + h                                     # base_link
        tip = np.r_[xy_r, top - DEPTH]
        # 닫힘축 후보 (수평): 네모 = 두 면 법선, 누운 = 긴 축에 수직, 원기둥 = 아무 쪽
        u = np.r_[np.cos(yaw_r), np.sin(yaw_r), 0]; v = np.r_[-np.sin(yaw_r), np.cos(yaw_r), 0]
        cands = {'box': [u, v], 'lying': [u], 'cyl': None}[shape]   # 누운 퍽 긴 축 = −v (env: x 축 90° 뒤 yaw)
        rd = (xy_r - pg.J1XY) / np.linalg.norm(xy_r - pg.J1XY); tang = np.r_[-rd[1], rd[0], 0]
        got = None
        for tdeg in (0, 15, 30, 45):
            t = np.radians(tdeg)
            a = np.r_[np.sin(t) * rd, -np.cos(t)]
            if tdeg == 0:
                cs = cands if cands is not None else [tang]
            else:
                cs = [c for c in (cands or [tang]) if abs(c @ tang) > np.cos(np.radians(35))] if cands else [tang]
                cs = [tang * np.sign(c @ tang) for c in cs] if cands else cs
            for c in cs:
                q1, c1 = solve(tip, a, c)
                if q1 is None:
                    continue
                q0, c0 = solve(tip - ABOVE * a, a, c1)
                if q0 is not None and c0 @ c1 > 0:
                    got = (q0, q1, tdeg)
                    break
            if got:
                break
        if not got:
            continue
        # 로봇 세계 자세: 박스 (env) 중심 (BOX_X, 0), yaw 0 ↔ 로봇 기준 박스 중심 (cx, ly), yaw psi
        th = -psi
        rob_xy = np.r_[BOX_X, 0.0] - rot(th) @ np.r_[cx, ly]
        # 퍽 env 좌표
        env_pk = []
        for (xy, yw, shp) in pk:
            pe = np.r_[BOX_X, 0.0] + xy                             # 박스 좌표 = env 좌표 (박스 yaw 0)
            env_pk.append([pe[0], pe[1], yw, ['box', 'cyl', 'lying'].index(shp)])
        env_pk.insert(0, env_pk.pop(k))                            # 맨 앞 = 작업 퍽
        return dict(robot=[rob_xy[0], rob_xy[1], th], pucks=env_pk, q0=pg.to_cmd(got[0]), q1=pg.to_cmd(got[1]), tilt=got[2],
                    gap=cx - reach_x - FRONT, psi=psi)
    return None


if __name__ == '__main__':
    N, out = int(sys.argv[1]), sys.argv[2]
    with Pool(12) as P:
        R = [r for r in P.map(one, range(N)) if r is not None]
    pk = np.full((len(R), 3, 4), np.nan)
    for i, r in enumerate(R):
        pk[i, :len(r['pucks'])] = r['pucks']
    np.savez(out, robot=np.array([r['robot'] for r in R]), pucks=pk, q0=np.array([r['q0'] for r in R]), q1=np.array([r['q1'] for r in R]),
             tilt=np.array([r['tilt'] for r in R]), gap=np.array([r['gap'] for r in R]), psi=np.array([r['psi'] for r in R]))
    sh = pk[:, 0, 3]
    print(f'장면 {len(R)} / {N} · 작업 퍽 네모 {np.mean(sh == 0):.2f} 원기둥 {np.mean(sh == 1):.2f} 누운 {np.mean(sh == 2):.2f} · '
          f'손 기울임 {dict(zip(*np.unique([r["tilt"] for r in R], return_counts=True)))} → {out}')
