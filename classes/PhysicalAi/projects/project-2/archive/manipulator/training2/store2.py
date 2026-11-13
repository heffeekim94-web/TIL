"""스테이션 퍽 적재 경로 (팀 control_master · park_stand 방식을 파이썬으로). 좌표 = base_link (pathgen 과 같음).
퍽 자세별 집기:
  선 퍽, 수직 손 닿음   → 수직 손으로 집음 (pathgen.store_path 와 같음)
  선 퍽, 먼 자리        → 손을 기울여 집고 (pick_max_tilt, 닫힘축 ≈ 접선) J1 쪽 빈 자리에 내려놓고 수직 손으로 다시 쥠 (regrasp_nodes)
  누운 네모 퍽          → lying_grasp 로 집고 그리퍼 받침에 기울여 넣고 놓음 → 손 빼서 수직 · 닫고 받침 뒤에 꽂아 눌러 세움 (press_mode) → 수직 손으로 다시 쥠
그 뒤 공통: 적재함 높이로 들어 칸 위 → 멈춰 잼 (손 안 퍽 비킴 · 방향) → 맞춰 넣기 → 놓기."""
import numpy as np

import pathgen as pg
from pathgen import AM, CELLS, J1XY, RC, TOP, BOX_TOPB, grip, ik, lerp_path, to_cmd, to_qm, choose_close, finger_reach

DOWN = np.array([0, 0, -1.0])
Z = np.array([0, 0, 1.0])
TEMPLATE = np.array(AM['template_q']); Q5_REST = AM['q5_rest']
SIDE, LENGTH = 0.030, 0.060                 # 시뮬 퍽 (팀 설정 side 0.0348 은 실물 누운 높이)
BOX_TOP_Z = BOX_TOPB                        # 스테이션 박스 윗면 (base_link)
BOX_Z = BOX_TOPB + 0.060 + 0.047 + 0.010 + 0.012     # 박스 위 이동 높이 (쥔 퍽 바닥이 선 퍽 윗면 10 mm 위)
RACK_Z = TOP + 0.047 + 0.010 + 0.017                 # 적재함 위 이동 높이
SAFE_Z = 0.22
REGRASP_MIN_X = 0.212                       # control_master regrasp_min_x
MAX_TILT = 40.0                             # pick_max_tilt_deg
TILTED_DEPTH = 0.040                        # pick_tilted_depth_mm
VERT_DEPTH = 0.025
# 받침 (control.yaml park_*, 시뮬 기본값은 park_stand.hpp ParkCfg — 실물 값은 팔 보정 오차를 메운 것이라 시뮬은 기본값)
PARK = dict(center=np.array([0.1008, 0.00115]), floor_z=0.1365, elev=45.0, min_elev=40.0, insert_clear=0.004, end_inset=0.004,
            press_r=-0.022, press_top=0.066, press_h=0.010, press_steps=4, regrasp_depth=0.030, regrasp_r=0.004, tilt_steps=8)
import os, json
PARK.update(json.loads(os.environ.get('PARK_JSON', '{}')))
LYING = dict(grip_offset=0.025, open_inner=0.0255, open_outer=0.0437, finger_half_w=0.0164, min_margin=0.0025, min_depth=0.020 * 0.030 / 0.0348, max_roll=12.0)   # 최소 깊이는 팀 34.8 mm 퍽 기준 → 시뮬 30 mm 퍽 비율로


def hand_frame(app, close):
    return np.column_stack([close, np.cross(app, close), app])


def ik_ok(p, a, c, seed, tol_mm=1.0):
    q, e = ik(p, a, c, seed)
    tp, ta, tc = grip(q)
    good = e * 1000 < tol_mm and ta @ a > np.cos(np.radians(1.0)) and tc @ c > np.cos(np.radians(2.0))
    return q, good


def multi_ik(p, a, c, seeds):
    """여러 씨앗으로 풀어 맞는 해 중 팀 key (J5 가 쉬는 자세에 가깝고 J2–J4 가 덜 꺾임) 가 작은 것."""
    best = None
    for s in seeds:
        q, ok = ik_ok(p, a, c, s)
        if ok:
            key = (round(abs(q[4] - Q5_REST) / 0.3), np.linalg.norm(q[1:4] - TEMPLATE[1:4]))
            if best is None or key < best[0]:
                best = (key, q)
    return None if best is None else best[1]


def nearest_ik(p, a, c, q):
    """park_stand nearest_ik: 앞 자세 씨앗, 안 되면 여러 씨앗 — 맞는 해 중 앞 자세에 가장 가까운 것."""
    q1, ok = ik_ok(p, a, c, q)
    if ok:
        return q1, True
    best = None
    for s in seeds_around(q) + [TEMPLATE + np.r_[d1, 0, 0, 0, d5] for d1 in (-1.0, 1.0) for d5 in (0.0, 1.5, -1.5)]:
        qs, ok = ik_ok(p, a, c, s)
        if ok and (best is None or np.abs(qs - q).sum() < np.abs(best - q).sum()):
            best = qs
    return (best, True) if best is not None else (q1, False)


def seeds_around(q):
    return [q + np.r_[0, 0, 0, 0, d] for d in (0.0, np.pi / 2, -np.pi / 2, np.pi, -np.pi)] + \
           [TEMPLATE + np.r_[0, 0, 0, 0, d] for d in (0.0, np.pi / 2, -np.pi / 2)]


class Path:
    """경유점 (모델 관절 값) · 이름 · 그리퍼 사건. 시작 자세는 출력에서 뺌."""

    def __init__(self, q):
        self.q, self.n, self.g = [np.asarray(q, float)], ['시작'], ['-']

    def go(self, p, a, c, nm, step=0.005, wa=3.0, g='-', polar=False):
        new = lerp_path(self.q[-1], [(p, a, c)], step, w_a=wa, polar=polar)
        self.q += new; self.n += [nm] * len(new); self.g += [g] + ['-'] * (len(new) - 1)

    def hold(self, k, nm, g='-'):
        self.q += [self.q[-1]] * k; self.n += [nm] * k; self.g += [g] + ['-'] * (k - 1)

    def joint(self, q, nm, g='-'):
        """관절 직선 (팀 경로 노드 사이와 같음)."""
        dq, nn = pg.dense([self.q[-1], np.asarray(q, float)], [nm, nm])
        self.q += dq[1:]; self.n += nn[1:]; self.g += ['-'] * (len(dq) - 2) + [g]

    def extend(self, qs, gs, ns):
        self.q += list(qs); self.g += list(gs); self.n += list(ns)

    def tip(self):
        return grip(self.q[-1])

    def out(self):
        Q = np.array([to_cmd(x) for x in self.q[1:]])
        Q, G, N, _ = pg.dense_all(Q, self.g[1:], self.n[1:])
        return Q, G, N


# ---------------------------------------------------------------- 선 퍽
def vertical_reach(xy, z_tip, c, seed):
    return ik_ok(np.r_[xy, z_tip], DOWN, c, seed)[1] or ik_ok(np.r_[xy, z_tip], DOWN, -c, seed)[1]


def pick_upright(path, xy, yaw, others, cyl=False):
    """선 퍽 (x, y, yaw) 집기. 수직 손이 닿으면 수직, 아니면 기울여 집고 가까운 자리에 내려놓아 수직으로 다시 쥠. 돌려줌 쥔 깊이 [m]."""
    xy = np.asarray(xy, float)
    top = BOX_TOP_Z + 0.060
    c_v, w_v = pg.choose_face_close(xy, yaw, others, cyl=cyl)
    q_now = path.q[-1]
    if vertical_reach(xy, top - VERT_DEPTH, c_v, q_now) and vertical_reach(xy, top + 0.040, c_v, q_now):
        _vertical_pick(path, xy, c_v, w_v, top, VERT_DEPTH, '')
        return VERT_DEPTH, 'vertical'
    # 기울여 집기: 팔이 5 축이라 손은 팔 평면 (J1 → 퍽) 안에서만 기울어짐 → 닫힘축 = 접선 (regrasp_nodes c_deg).
    #   네모 퍽은 면이 접선에서 35° 안이어야 (control_master tilt_able) — 손가락이 닫히며 퍽을 그만큼 돌려 맞춤
    rdir = (xy - J1XY) / np.linalg.norm(xy - J1XY); tang = np.array([-rdir[1], rdir[0]])
    if not cyl:
        off = min(np.degrees(np.arccos(np.clip(abs(np.cos(yaw + k * np.pi / 2) * tang[0] + np.sin(yaw + k * np.pi / 2) * tang[1]), -1, 1))) for k in range(2))
        if off > 35.0:
            raise RuntimeError(f'먼 퍽 ({xy[0]:.3f}, {xy[1]:.3f}): 면이 접선에서 {off:.0f}° 돌아 기울인 손으로 못 쥠 (팀 35° 까지)')
    Rp, c = np.r_[rdir, 0], np.r_[tang, 0]
    tip_g = np.r_[xy, top - TILTED_DEPTH]
    for t in np.arange(10.0, MAX_TILT + 1e-6, 5.0):
        a = np.sin(np.radians(t)) * Rp - np.cos(np.radians(t)) * Z
        seeds = seeds_around(q_now)
        qg = multi_ik(tip_g, a, c, seeds) if multi_ik(tip_g, a, c, seeds) is not None else multi_ik(tip_g, a, -c, seeds)
        if qg is not None:
            break
    else:
        raise RuntimeError(f'먼 퍽 ({xy[0]:.3f}, {xy[1]:.3f}): {MAX_TILT:.0f}° 까지 기울여도 안 닿음')
    c = grip(qg)[2]
    pre = tip_g - 0.050 * a
    path.go(np.r_[pre[:2], max(pre[2], BOX_Z)], a, c, '먼 퍽 위 (손 기울임)', wa=1.0, polar=True)
    path.go(pre, a, c, '먼 퍽 위 (손 기울임)', step=0.0025)
    path.hold(15, '확인', g=f'release:{pg.OPEN_NARROW}')
    path.go(tip_g, a, c, '기울여 들어감', step=0.002)
    path.hold(8, '쥠', g='close')
    path.go(tip_g + 0.015 * Z, a, c, '살짝 들기', step=0.002)
    # 다시 잡을 자리: J1 → 퍽 방향으로 regrasp_min_x 부터 1 cm 씩 바깥, 옆 ±4 · ±8 cm (control_master regrasp_nodes)
    r0 = np.linalg.norm(xy - J1XY)
    r_near = (REGRASP_MIN_X + 0.002 - J1XY[0]) / rdir[0] if rdir[0] > 0.1 else r0 - 0.01
    spot = None
    for r in np.arange(min(r_near, r0 - 0.01), r0 - 0.01 + 1e-9, 0.01):
        for lat in (0.0, 0.04, -0.04, 0.08, -0.08):
            s = J1XY + rdir * r + tang * lat
            if s[0] < REGRASP_MIN_X or abs(s[1]) > 0.1025 - 0.020:
                continue
            if any(np.linalg.norm(np.asarray(o[:2]) - s) < 0.030 + 0.016 + 0.021 for o in others):
                continue
            if vertical_reach(s, top - VERT_DEPTH, c, qg) and ik_ok(np.r_[s, top - TILTED_DEPTH + 0.002], a, c, qg)[1]:
                spot = s; break
        if spot is not None:
            break
    if spot is None:
        raise RuntimeError('기울여 쥔 퍽을 다시 잡을 빈 자리가 없음')
    path.go(np.r_[spot, top - TILTED_DEPTH + 0.015], a, c, '가까운 자리로', step=0.004)
    path.go(np.r_[spot, top - TILTED_DEPTH + 0.002], a, c, '내려놓기', step=0.002)
    path.hold(10, '놓음', g=f'release:{pg.OPEN_NARROW}')
    path.go(np.r_[spot, top - TILTED_DEPTH + 0.002] - 0.050 * a, a, c, '손 빼기', step=0.0025)
    c_r = pg.feasible_sign(np.r_[spot, top - VERT_DEPTH], c, path.q[-1])
    _vertical_pick(path, spot, c_r, pg.OPEN_NARROW, top, VERT_DEPTH, '다시 ')
    return VERT_DEPTH, f'tilted→regrasp ({spot[0]:.3f}, {spot[1]:.3f})'


def _vertical_pick(path, xy, c, width, top, depth, pre):
    c = pg.feasible_sign(np.r_[xy, top - depth], c, path.q[-1])
    p0 = path.tip()[0]
    if p0[2] < BOX_Z - 0.002:
        path.go(np.r_[p0[:2], BOX_Z], path.tip()[1], path.tip()[2], '올림', step=0.003, wa=1.0)
    path.go(np.r_[xy, BOX_Z], DOWN, c, pre + '퍽 위', wa=1.0, polar=True)
    path.go(np.r_[xy, top + 0.040], DOWN, c, pre + '퍽 위', step=0.0025)
    path.hold(15, '확인', g=f'release:{width}')
    path.go(np.r_[xy, top - depth], DOWN, c, pre + '내림', step=0.0025)
    path.hold(8, pre + '쥠', g='close')
    path.go(np.r_[xy, BOX_Z], DOWN, c, pre + '들기', step=0.0025, wa=1.0)


# ---------------------------------------------------------------- 누운 네모 퍽 (park_stand.cpp lying_grasp · park_nodes press_mode)
def roll_geometry(c0, a, e1, t, tip_floor):
    half = SIDE / 2.0
    tip = c0 + LYING['grip_offset'] * e1; tip[2] = tip_floor
    for _ in range(4):
        r2 = (tip[:2] - J1XY); r2 /= np.linalg.norm(r2)
        R = np.r_[r2, 0]
        app = np.sin(t) * R - np.cos(t) * Z
        close = np.cross(app, a); close /= np.linalg.norm(close)
        if close[2] < 0:
            close = -close
        rho = np.arcsin(np.clip(close[2], -1, 1))
        h = close - close[2] * Z
        h = h / np.linalg.norm(h) if np.linalg.norm(h) > 1e-9 else close
        n = -np.sin(rho) * h + np.cos(rho) * Z
        cz = half * (np.sin(rho) + np.cos(rho) - 1.0)
        c = c0 - np.tan(rho) * cz * h + cz * Z
        margin = LYING['open_inner'] - half * (np.cos(rho) + np.sin(rho))
        b = np.cross(app, close); b /= np.linalg.norm(b)
        tip_z = tip_floor + LYING['open_outer'] * abs(close[2]) + LYING['finger_half_w'] * abs(b[2])
        xn = (tip_z - c[2]) / n[2]
        d_up = half - xn
        s_mid = xn / (app @ n)
        xa = LYING['grip_offset'] * (e1 @ a) + s_mid * (app @ a)
        tip = c + xa * a + xn * n
    return dict(tip=tip, app=app, close=close, c=c, n=n, rho=rho, margin=margin, d_up=d_up)


def lying_grasp(xy, axis_yaw, seed, max_tilt=30.0, clear_ok=None):
    x, y = xy
    a = np.array([np.cos(axis_yaw), np.sin(axis_yaw), 0.0])
    p0, a2 = np.array(xy), a[:2]
    go_ = LYING['grip_offset']
    e_near = a if np.linalg.norm(p0 + go_ * a2 - J1XY) <= np.linalg.norm(p0 - go_ * a2 - J1XY) else -a
    radial = abs(a2 @ ((p0 - J1XY) / np.linalg.norm(p0 - J1XY))) >= np.cos(np.pi / 4)
    e_first = -e_near if radial else e_near
    top_z = BOX_TOP_Z + SIDE
    c0 = np.array([x, y, top_z - SIDE / 2])
    tip_floor = BOX_TOP_Z + 0.003                       # 수직 손 손끝이 내려가는 가장 낮은 곳 = 박스 윗면 3 mm 위
    last = '후보 없음'
    for tilt in (0.0, 10.0, 20.0, 30.0):
        if tilt > max_tilt + 1e-9:
            continue
        for e1 in (e_first, -e_first):
            geo = roll_geometry(c0, a, e1, np.radians(tilt), tip_floor)
            if np.degrees(geo['rho']) > LYING['max_roll'] + 1e-9 or geo['margin'] < LYING['min_margin'] - 1e-9 or geo['d_up'] < LYING['min_depth'] - 1e-9:
                last = f"손 {tilt:.0f}°: 굴림 {np.degrees(geo['rho']):.0f}° · 여유 {geo['margin'] * 1000:.1f} · 깊이 {geo['d_up'] * 1000:.0f}"
                continue
            grips = []
            for sg in (1.0, -1.0):
                q = multi_ik(geo['tip'], geo['app'], sg * geo['close'], seeds_around(seed))
                if q is not None:
                    grips.append((q, sg * geo['close']))
            grips.sort(key=lambda u: (round(abs(u[0][4] - Q5_REST) / 0.3), np.linalg.norm(u[0][1:4] - TEMPLATE[1:4])))
            for qg, close in grips:
                ok = True
                poses = []
                for h in (0.040, 0.010):
                    s_back = (top_z + h - geo['tip'][2]) / -geo['app'][2]
                    q, good = ik_ok(geo['tip'] - s_back * geo['app'], geo['app'], close, qg)
                    ok &= good; poses.append(geo['tip'] - s_back * geo['app'])
                if not ok:
                    last = f'손 {tilt:.0f}°: 위 · 내림 자세 IK 안 됨'
                    continue
                g = dict(q=qg, tip=geo['tip'], app=geo['app'], close=close, c=geo['c'], n=geo['n'], a_end=-e1, tilt=tilt,
                         roll=np.degrees(geo['rho']), above=poses[0], down=poses[1], depth=geo['d_up'])
                if clear_ok is not None and not clear_ok(g):
                    last = f'손 {tilt:.0f}°: 손가락이 옆 퍽에 가까움'
                    continue
                return g
    raise RuntimeError(f'누운 퍽 ({x:.3f}, {y:.3f}) 못 쥠: {last}')


def park_nodes(g, q_from):
    """park_stand.cpp park_nodes (press_mode) — 경유점 [(이름, 손끝, 기울임°, 그리퍼)] 와 IK 자세."""
    c = PARK
    sc = c['center']; rdir = (sc - J1XY) / np.linalg.norm(sc - J1XY)
    R, T = np.r_[rdir, 0], np.r_[-rdir[1], rdir[0], 0]
    Hg = hand_frame(g['app'], g['close'])
    c_h, a_h, k_h, n_h = Hg.T @ (g['c'] - g['tip']), Hg.T @ g['a_end'], Hg.T @ g['close'], Hg.T @ g['n']
    half = SIDE / 2
    app_of = lambda th: np.sin(np.radians(th)) * R - np.cos(np.radians(th)) * Z
    at = lambda r, z: np.r_[sc + r * rdir, z]
    for elev in np.arange(c['elev'], c['min_elev'] - 1e-6, -5.0):
        e = np.radians(elev)
        want = -np.cos(e) * R - np.sin(e) * Z
        cands = []
        for sg in (1.0, -1.0):
            best = (1e9, 0.0)
            for th in np.arange(-30.0, 80.0 + 1e-9, 0.25):
                a_s = hand_frame(app_of(th), sg * T) @ a_h
                err = np.degrees(np.arccos(np.clip(a_s @ want, -1, 1)))
                if err < best[0]:
                    best = (err, th)
            if best[0] < 1.0:
                cands.append((best[1], sg))
        cands.sort(key=lambda u: abs(u[0] - elev))
        for th, sg in cands:
            Hs = hand_frame(app_of(th), sg * T)
            a_s, k_s, n_s = Hs @ a_h, Hs @ k_h, Hs @ n_h
            f = at(-c['end_inset'], 0.0)
            f[2] = c['floor_z'] + c['insert_clear'] + half * (abs(k_s[2]) + abs(n_s[2]))
            p_ins = f - (LENGTH / 2) * a_s - Hs @ c_h
            p_over = at(0.04, c['floor_z'] + 0.0625)
            nodes = [('받침 위', p_over, 0.0, '-')]
            for k in range(1, c['tilt_steps'] + 1):
                fk = k / c['tilt_steps']
                nodes.append(('받침에 기울여 넣기', p_over + (p_ins - p_over) * fk, th * fk, 'release' if k == c['tilt_steps'] else '-'))
            z_top = c['floor_z'] + c['press_top']
            p_lift = p_ins.copy(); p_lift[2] = max(p_ins[2], z_top)
            nodes += [('손 빼기', p_lift, th, '-'), ('손 세우고 닫기', p_lift, 0.0, 'close'), ('받침 뒤 위', at(c['press_r'], z_top), 0.0, '-')]
            for k in range(1, c['press_steps'] + 1):
                nodes.append(('꽂아 눌러 세우기', at(c['press_r'], z_top + (c['floor_z'] + c['press_h'] - z_top) * k / c['press_steps']), 0.0, '-'))
            nodes.append(('올림', at(c['press_r'], z_top), 0.0, '-'))
            ptop = c['floor_z'] + LENGTH
            nodes += [('선 퍽 위', at(c['regrasp_r'], ptop + 0.0075), 0.0, 'release'), ('다시 내림', at(c['regrasp_r'], ptop - c['regrasp_depth']), 0.0, 'close'),
                      ('받침에서 들기', at(c['regrasp_r'], ptop + 0.0075), 0.0, '-')]
            q, out, ok = q_from, [], True
            for nm, p, tdeg, gr in nodes:
                q_n, good = nearest_ik(p, app_of(tdeg), sg * T, q)
                if not good:
                    ok = False; break
                q = q_n; out.append((nm, q, gr))
            if ok:
                return out, elev, sg * T
    raise RuntimeError('받침에 넣는 자세 IK 안 됨')


def pick_lying(path, xy, axis_yaw, others, until='all'):
    """누운 네모 퍽: 집기 → 받침 세우기 → 다시 쥠. 돌려줌 쥔 깊이 (선 퍽 윗면 아래) [m]."""
    def clear_ok(g):
        # 열린 손가락 (닫힘축 ±reach, 폭 ±16 mm) 이 옆 퍽 (반 대각 21 mm) 과 3 mm 넘게 떨어짐
        cax = g['close'][:2] / max(np.linalg.norm(g['close'][:2]), 1e-9); lat = np.array([-cax[1], cax[0]])
        for o in others:
            d = np.asarray(o[:2]) - g['tip'][:2]
            if abs(d @ lat) < 0.016 + 0.021 and abs(d @ cax) - 0.021 - finger_reach(pg.OPEN_WIDE) < 0.003:
                return False
        try:                                  # 팀 accept: 받침에 넣을 수 있는 쥐기만 (park_nodes 가 되는지)
            g['park'] = park_nodes(g, g['q'])
        except RuntimeError:
            return False
        return True
    g = lying_grasp(xy, axis_yaw, path.q[-1], clear_ok=clear_ok)
    p0 = path.tip()[0]
    if p0[2] < BOX_Z - 0.002:
        path.go(np.r_[p0[:2], BOX_Z], path.tip()[1], path.tip()[2], '올림', step=0.003, wa=1.0)
    path.go(np.r_[g['above'][:2], BOX_Z], g['app'], g['close'], '누운 퍽 위', wa=1.0, polar=True)
    path.go(g['above'], g['app'], g['close'], '누운 퍽 위', step=0.003)
    path.hold(15, '확인', g=f'release:{pg.OPEN_WIDE}')
    path.go(g['down'], g['app'], g['close'], '내림', step=0.0025)
    path.go(g['tip'], g['app'], g['close'], '내림', step=0.002)
    path.hold(8, '쥠 (누운 퍽 끝)', g='close')
    path.go(np.r_[g['tip'][:2], BOX_Z + 0.02], g['app'], g['close'], '들기', step=0.0025, wa=1.0)
    nodes, elev, c_park = g['park']
    path.park_close = c_park
    for nm, q, gr in nodes:
        if until == 'insert' and nm == '손 세우고 닫기':     # 받침에 넣고 손 뺀 데까지 (뒤는 확인하며 park_press · park_regrasp)
            break
        path.joint(q, nm)
        gg = {'release': f'release:{pg.OPEN_NARROW}', 'close': 'close'}.get(gr, '-')
        if gg != '-':
            path.hold(8, nm, g=gg)
    return PARK['regrasp_depth'], f'lying tilt {g["tilt"]:.0f}° roll {g["roll"]:.0f}° · 받침 넣는 각 {elev:.0f}°'


# ---------------------------------------------------------------- 적재함 칸에 넣기
def to_rack_check(path, cell, occupied):
    """쥔 퍽 (수직) 을 적재함 높이로 들어 칸 위로 가서 멈춤 (여기서 손 안 퍽을 잼)."""
    cxy = np.array(CELLS[cell]['xy'])
    c_ins = choose_close(cell, occupied)
    rec = pg.P[f'retrieve_{cell}']
    q_rec = to_qm(pg.sm.true_from_cmd(np.array(rec['q']).reshape(-1, 5)[max(i for i, e in enumerate(rec['grip']) if e == 'close')]))
    c_ins = pg.feasible_sign(np.r_[cxy, RACK_Z], c_ins, q_rec)
    p0, a0, c0 = path.tip()
    path.go(np.r_[p0[:2], RACK_Z], DOWN, c0, '적재함 높이로', step=0.0025, wa=0.3)
    path.go(np.r_[cxy, RACK_Z], DOWN, c_ins, '칸 위로', wa=0.3, polar=True)
    path.hold(15, '칸 위 확인')
    return c_ins


def insert(path, cell, c_ins, depth, ins_offset=(0.0, 0.0), ins_dyaw=0.0, insert_gap=0.008, hold_only=False):
    """hold_only: 칸 안 놓는 점까지 내려가 쥔 채 멈춤 (걸림 확인 뒤 release_and_lift 또는 recover_lift_out). 돌려줌 (txy, c_fix)."""
    cxy = np.array(CELLS[cell]['xy'])
    txy = cxy - np.asarray(ins_offset)
    cr, sr = np.cos(-ins_dyaw), np.sin(-ins_dyaw)
    c_fix = np.r_[cr * c_ins[0] - sr * c_ins[1], sr * c_ins[0] + cr * c_ins[1], 0.0]
    path.go(np.r_[txy, RACK_Z], DOWN, c_fix, '맞춤', step=0.0015, wa=0.3)
    ins_tip = RC['floor_z'] + insert_gap + 0.060 - depth
    path.go(np.r_[txy, SAFE_Z], DOWN, c_fix, '넣기', step=0.0025, wa=3.0)
    path.go(np.r_[txy, ins_tip], DOWN, c_fix, '넣기', step=0.0015, wa=3.0)
    if hold_only:
        path.hold(6, '걸림 확인')
        return txy, c_fix
    release_and_lift(path, txy, c_fix)
    return txy, c_fix


def release_and_lift(path, txy, c_fix):
    path.hold(10, '놓음', g='release:0.0085')
    path.go(np.r_[txy, SAFE_Z], DOWN, c_fix, '칸에서 들기', step=0.0025)


def recover_lift_out(path, txy, c_fix, spot, others):
    """혁무님 store_recover: 걸리면 칸 안에서 놓지 않고 쥔 채 곧게 들어 → 박스 자리 spot 에 세워 내려놓음 (그 뒤 다시 보고 다시 쥠)."""
    path.go(np.r_[txy, SAFE_Z], DOWN, c_fix, '걸림 → 쥔 채 곧게 들기', step=0.0025)
    path.go(np.r_[txy, RACK_Z], DOWN, c_fix, '걸림 → 쥔 채 곧게 들기', step=0.0025, wa=0.3)
    path.go(np.r_[spot, RACK_Z], DOWN, pg.front_close(spot), '적재함 높이로 박스 위까지', wa=0.3, polar=True)   # 적재함 위에서 내려가지 않게
    place_dice(path, spot, others)


def seat_correct(path, cell, kind, yaw_err=0.0, occupied=()):
    """칸 안 퍽 정정 (사용자 2026-11-11, 옆 퍽 안 건드리게 칸 바로 위에서만 작게):
    kind 'press' = 손가락 닫고 윗면 가운데를 수직으로 살짝 눌러 내림 (턱에 걸침 · 기욺),
    kind 'twist' = 칸 위로 나온 부분만 좁게 쥐고 5 mm 들어 손목으로 yaw_err 만큼 되돌려 내려놓음 (면 돌아감)."""
    cxy = np.array(CELLS[cell]['xy'])
    c = pg.feasible_sign(np.r_[cxy, SAFE_Z], choose_close(cell, [o for o in occupied if o != cell]), path.q[-1])
    p0 = path.tip()[0]
    path.go(np.r_[p0[:2], max(p0[2], SAFE_Z)], DOWN, path.tip()[2], '올림', step=0.003, wa=1.0)
    path.go(np.r_[cxy, SAFE_Z], DOWN, c, '칸 위 (정정)', wa=1.0, polar=True)
    if kind == 'press':
        path.hold(8, '손가락 닫음', g='close')
        path.go(np.r_[cxy, TOP + 0.010], DOWN, c, '윗면 위', step=0.0025)
        path.go(np.r_[cxy, TOP - 0.002], DOWN, c, '살짝 눌러 내림', step=0.001)
        path.go(np.r_[cxy, SAFE_Z], DOWN, c, '올림', step=0.0025)
    else:
        grip_tip = TOP - 0.015                                  # 칸 턱 (rim) 위로 나온 부분만 (손끝 턱 위 약 17 mm)
        path.hold(10, '좁게 벌림', g=f'release:{pg.OPEN_NARROW}')
        path.go(np.r_[cxy, grip_tip], DOWN, c, '윗부분 쥐러', step=0.002)
        path.hold(8, '쥠', g='close')
        path.go(np.r_[cxy, grip_tip + 0.005], DOWN, c, '5 mm 들기', step=0.001)
        cr, sr = np.cos(-yaw_err), np.sin(-yaw_err)
        c2 = np.r_[cr * c[0] - sr * c[1], sr * c[0] + cr * c[1], 0.0]
        path.go(np.r_[cxy, grip_tip + 0.005], DOWN, c2, '손목으로 돌려 맞춤', step=0.001)
        path.go(np.r_[cxy, grip_tip + 0.001], DOWN, c2, '내려놓기', step=0.001)
        path.hold(10, '놓음', g='release:0.0085')
        path.go(np.r_[cxy, SAFE_Z], DOWN, c2, '올림', step=0.0025)


# ---------------------------------------------------------------- 놓은 퍽 다시 세우기 · 끌어오기 (사용자 2026-11-11: 놓고 확인 → 넘어졌으면 다시)
def drag_in(path, xy, axis_yaw, r_end=0.235):
    """손이 못 집는 먼 자리의 누운 퍽: 손가락 닫고 퍽 바깥쪽 뒤로 내려가 J1 쪽으로 끌어옴 (퍽 중심이 J1 에서 r_end 까지).
    손은 팔 평면 안에서만 기울어짐 (5 축) → 바깥으로 기울여 멀리 닿음, 닫힘축 = 접선 (손가락 판이 미는 면)."""
    xy = np.asarray(xy, float)
    rdir = (xy - J1XY) / np.linalg.norm(xy - J1XY); tang = np.array([-rdir[1], rdir[0]])
    a_ax = np.array([np.cos(axis_yaw), np.sin(axis_yaw)])
    ext = 0.030 * abs(a_ax @ rdir) + 0.015 * abs(a_ax @ tang)        # 누운 퍽 반지름 방향 반 길이
    start_xy = xy + rdir * (ext + 0.012)                              # 퍽 바깥 면 12 mm 뒤 (손가락 반 두께 6 + 여유)
    end_xy = J1XY + rdir * (r_end + ext + 0.006)
    z_push = BOX_TOP_Z + 0.012                                        # 손끝이 박스 윗면 12 mm 위 (누운 퍽 높이 30 의 아래쪽)
    R, c = np.r_[rdir, 0], np.r_[tang, 0]
    for t in np.arange(0.0, 45.1, 5.0):
        a = np.sin(np.radians(t)) * R - np.cos(np.radians(t)) * Z
        seeds = seeds_around(path.q[-1])
        if multi_ik(np.r_[start_xy, z_push], a, c, seeds) is not None and multi_ik(np.r_[end_xy, z_push], a, c, seeds) is not None:
            break
    else:
        raise RuntimeError(f'끌어오기: 퍽 ({xy[0]:.3f}, {xy[1]:.3f}) 뒤로 손이 안 닿음')
    p0 = path.tip()[0]
    path.go(np.r_[p0[:2], max(p0[2], BOX_Z)], path.tip()[1], path.tip()[2], '올림', step=0.003, wa=1.0)
    path.go(np.r_[start_xy, BOX_Z], a, c, '퍽 뒤 위로', wa=1.0, polar=True)
    path.hold(8, '손가락 닫음', g='close')
    path.go(np.r_[start_xy, z_push], a, c, '퍽 뒤로 내림', step=0.002)
    path.go(np.r_[end_xy, z_push], a, c, '끌어옴', step=0.002)
    path.go(np.r_[end_xy, BOX_Z], a, c, '올림', step=0.003, wa=1.0)
    return f'끌어옴 손 {t:.0f}° ({xy[0]:.3f} → {J1XY[0] + rdir[0] * r_end:.3f})'


def place_dice(path, target, placed, depth=VERT_DEPTH):
    """쥔 퍽 (수직 손) 을 주사위 자리에 놓기. 수직 손이 닿으면 그대로 (pathgen.place_and_home),
    안 닿으면 팀 control_master place_far_regrasp: 같은 방향 (J1 → 목표) 가까운 빈 자리에 세워 내려놓고 →
    손을 기울여 (닫힘축 = 접선) 다시 쥠 (퍽은 선 채) → 그 기울임 그대로 먼 자리에 놓음. 기울인 손으로 수직 퍽을 놓으면 넘어짐 (2026-11-11 시뮬)."""
    target = np.asarray(target, float)
    top = BOX_TOP_Z + 0.060
    c_f = pg.front_close(target)
    q_now = path.q[-1]
    if vertical_reach(target, top - depth + 0.002, c_f, q_now) and vertical_reach(target, top + 0.040, c_f, q_now):
        Q, G, N = pg.place_and_home(q_now, target, placed, depth=depth, home=False)
        path.extend([to_qm(x) for x in Q], G, N)
        return 'vertical'
    rdir = (target - J1XY) / np.linalg.norm(target - J1XY); tang = np.array([-rdir[1], rdir[0]])
    R, c = np.r_[rdir, 0], np.r_[tang, 0]
    # 기울임: 목표에 놓는 자세가 되는 가장 작은 손 기울임
    for t in np.arange(10.0, MAX_TILT + 1e-6, 5.0):
        a = np.sin(np.radians(t)) * R - np.cos(np.radians(t)) * Z
        if multi_ik(np.r_[target, top - TILTED_DEPTH + 0.002], a, c, seeds_around(q_now)) is not None:
            break
    else:
        raise RuntimeError(f'주사위 자리 ({target[0]:.3f}, {target[1]:.3f}): {MAX_TILT:.0f}° 기울여도 안 닿음')
    # 내려놓을 가까운 자리: J1 → 목표 선 위, regrasp_min_x 부터 바깥으로 1 cm 씩, 옆 0 · ±4 cm. 놓인 퍽 · 목표에서 떨어지고 수직 손 · 기울인 손 다 닿는 곳
    r0 = np.linalg.norm(target - J1XY)
    spot = None
    for r in np.arange((REGRASP_MIN_X + 0.002 - J1XY[0]) / max(rdir[0], 0.1), r0 - 0.03 + 1e-9, 0.01):
        for lat in (0.0, 0.04, -0.04):
            s = J1XY + rdir * r + tang * lat
            if s[0] < REGRASP_MIN_X or abs(s[1]) > 0.1025 - 0.020:
                continue
            if any(np.linalg.norm(np.asarray(p) - s) < 0.067 for p in placed):          # 목표 자리는 비어 있으니 가까워도 됨
                continue
            if vertical_reach(s, top - depth + 0.002, pg.front_close(s), q_now) and ik_ok(np.r_[s, top - TILTED_DEPTH], a, c, q_now)[1]:
                spot = s; break
        if spot is not None:
            break
    if spot is None:
        raise RuntimeError('먼 주사위 자리: 내려놓고 다시 쥘 빈 자리가 없음')
    Q, G, N = pg.place_and_home(q_now, spot, placed, depth=depth, home=False)
    path.extend([to_qm(x) for x in Q], G, N)
    tip_s = np.r_[spot, top - TILTED_DEPTH]
    path.go(np.r_[(tip_s - 0.050 * a)[:2], BOX_Z], a, c, '기울여 다시 쥐러', wa=1.0)
    path.go(tip_s - 0.050 * a, a, c, '기울여 다시 쥐러', step=0.0025)
    path.hold(10, '확인', g=f'release:{pg.OPEN_NARROW}')
    path.go(tip_s, a, c, '기울여 들어감', step=0.002)
    path.hold(8, '다시 쥠 (손 기울임, 퍽은 선 채)', g='close')
    path.go(tip_s + 0.020 * Z, a, c, '들기', step=0.002)
    tip_t = np.r_[target, top - TILTED_DEPTH + 0.002]
    path.go(tip_t + 0.020 * Z, a, c, '먼 자리 위로', step=0.003)
    path.hold(15, '자리 확인')
    path.go(tip_t, a, c, '내려놓기', step=0.002)
    path.hold(10, '놓음', g=f'release:{pg.OPEN_NARROW}')
    path.go(tip_t - 0.050 * a, a, c, '손 빼기', step=0.0025)
    path.go(np.r_[(tip_t - 0.050 * a)[:2], BOX_Z], a, c, '들기', step=0.003, wa=1.0)
    return f'far: 손 {t:.0f}° · 다시 쥔 자리 ({spot[0]:.3f}, {spot[1]:.3f})'


# ---------------------------------------------------------------- 받침에서 확인하며 세우기 (사용자 2026-11-11: 누르고 확인 → 2 번 안 되면 다시 집어 박스에서 다시)
def _park_at(r, z):
    sc = PARK['center']; rdir = (sc - J1XY) / np.linalg.norm(sc - J1XY)
    return np.r_[sc + r * rdir, z]


def _park_T():
    sc = PARK['center']; rdir = (sc - J1XY) / np.linalg.norm(sc - J1XY)
    return np.r_[-rdir[1], rdir[0], 0.0]


def park_press(path, side):
    """받침에 기댄 퍽 누르기: side = -1 뒤 (J1 쪽, 퍽 윗부분이 바깥으로 기울었을 때), +1 앞 (로봇 쪽으로 기울었을 때).
    손 수직 · 닫고 그 쪽 위 → 바닥 + press_h 까지 곧게 내려 누름 → 올림."""
    c = getattr(path, 'park_close', _park_T())
    z_top = PARK['floor_z'] + PARK['press_top']
    r = side * abs(PARK['press_r'])
    p0 = path.tip()[0]
    q, ok = nearest_ik(np.r_[p0[:2], max(p0[2], z_top)], DOWN, c, path.q[-1])
    path.joint(q, '손 세우고 닫기'); path.hold(8, '손 세우고 닫기', g='close')
    q, ok = nearest_ik(_park_at(r, z_top), DOWN, c, path.q[-1])
    if not ok:
        raise RuntimeError(f'받침 {"앞" if side > 0 else "뒤"} 누르기 자세 IK 안 됨')
    path.joint(q, f'받침 {"앞" if side > 0 else "뒤"} 위')
    for k in range(1, PARK['press_steps'] + 1):
        q, ok = nearest_ik(_park_at(r, z_top + (PARK['floor_z'] + PARK['press_h'] - z_top) * k / PARK['press_steps']), DOWN, c, path.q[-1])
        path.joint(q, f'{"앞" if side > 0 else "뒤"}에서 눌러 세우기')
    q, ok = nearest_ik(_park_at(r, z_top), DOWN, c, path.q[-1])
    path.joint(q, '올림')


def park_regrasp(path, xy):
    """받침에 선 퍽 (잰 자리 xy) 을 수직 손으로 다시 쥠 · 들기. 돌려줌 쥔 깊이."""
    c = getattr(path, 'park_close', _park_T())
    ptop = PARK['floor_z'] + LENGTH
    for p, nm, g in ((np.r_[xy, ptop + 0.0075], '선 퍽 위', f'release:{pg.OPEN_NARROW}'), (np.r_[xy, ptop - PARK['regrasp_depth']], '다시 내림', 'close'),
                     (np.r_[xy, ptop + 0.0075], '받침에서 들기', '-')):
        q, ok = nearest_ik(p, DOWN, c, path.q[-1])
        if not ok:
            raise RuntimeError(f'받침 다시 쥐기 IK 안 됨 ({nm})')
        path.joint(q, nm)
        if g != '-':
            path.hold(8, nm, g=g)
    return PARK['regrasp_depth']


def park_extract(path, top_xyz, spot):
    """2 번 눌러도 안 선 퍽: 받침에서 집어 (윗끝을 수직 손으로) 박스 빈 자리 spot 에 놓음 (누운 채) → 거기서 다시 제대로 잡기."""
    c = getattr(path, 'park_close', _park_T())
    top = np.asarray(top_xyz, float)
    for p, nm, g in ((np.r_[top[:2], top[2] + 0.015], '받침 퍽 윗끝 위', f'release:{pg.OPEN_WIDE}'), (np.r_[top[:2], top[2] - 0.018], '윗끝 쥐러 내림', 'close'),
                     (np.r_[top[:2], top[2] + 0.030], '받침에서 꺼냄', '-')):
        q, ok = nearest_ik(p, DOWN, c, path.q[-1])
        if not ok:
            raise RuntimeError(f'받침에서 꺼내기 IK 안 됨 ({nm})')
        path.joint(q, nm)
        if g != '-':
            path.hold(8, nm, g=g)
    path.go(np.r_[spot, BOX_Z], DOWN, pg.front_close(spot), '박스 빈 자리로', wa=1.0, polar=True)
    path.go(np.r_[spot, BOX_TOP_Z + 0.045], DOWN, pg.front_close(spot), '내려놓기', step=0.0025)
    path.hold(10, '놓음', g=f'release:{pg.OPEN_WIDE}')
    path.go(np.r_[spot, BOX_Z], DOWN, pg.front_close(spot), '들기', step=0.003)
