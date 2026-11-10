"""Lying puck anywhere on the start box top, any angle.
The swerve base parks so J1 is on the puck's long axis and the fingertip lands 25 mm into one end
(fingertip 0.38 / 0.39 / 0.40 m from J1 = the only body-clear reach found in check_v2.py).
Checked per puck pose and per end: robot footprint vs box, and every arm point along
P0 -> above puck -> grasp -> lift -> above S10 against the box (other collisions were cleared in check_v2.py)."""
import numpy as np
import armgeo as A
import check_body as CB
import check_v2 as V
import render_check_geo as G

BOX_S, BOX_TOP = CB.BOX_S, CB.BOX_TOP
PUCK_L, PUCK_S, D = 0.060, 0.0348, 0.025
HALF = BOX_S / 2
FOOT = 0.16
MARGIN = 0.010


def path_points(tip_x):
    q_g, q_pre, q_lift = np.load(f"v2grasp_{tip_x:.2f}_20.npy")
    _, q_up = np.load(f"v2cup_{tip_x:.2f}_20_S10.npy")
    segs = [(V.Q_P0, q_pre, V.OPEN, V.OPEN), (q_pre, q_g, V.OPEN, V.OPEN), (q_g, q_g, V.OPEN, V.ON),
            (q_g, q_lift, V.ON, V.ON), (q_lift, q_up, V.ON, V.ON)]
    pts = []
    for q0, q1, f0, f1 in segs:
        for s in np.linspace(0, 1, 10):
            for nm, P in G.world_points(q0 + (q1 - q0) * s, f0 + (f1 - f0) * s).items():
                if nm != "arm_link1":
                    pts.append(P)
    P = np.vstack(pts)
    return P[P[:, 2] < BOX_TOP + 0.002]          # only points low enough to touch the box top matter


def rot2(a):
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def squares_overlap(c1, a1, h1, c2, a2, h2):
    """Separating-axis test for two squares (centre, angle, half size)."""
    def corners(c, a, h):
        return (np.array([[-h, -h], [h, -h], [h, h], [-h, h]]) @ rot2(a).T) + c
    P1, P2 = corners(c1, a1, h1), corners(c2, a2, h2)
    for a in (a1, a1 + np.pi / 2, a2, a2 + np.pi / 2):
        n = np.array([np.cos(a), np.sin(a)])
        if (P1 @ n).max() < (P2 @ n).min() or (P2 @ n).max() < (P1 @ n).min():
            return False
    return True


LOW = {t: path_points(t) for t in (0.38, 0.39, 0.40)}


def check(cx, cy, yaw, end):
    """Return (ok, reason, robot pose (x, y, heading), tip_x) for grabbing the given end (+1 / -1)."""
    u = end * np.array([np.cos(yaw), np.sin(yaw)])        # robot +x points along u (from the robot into the puck)
    th = np.arctan2(u[1], u[0])
    best = None
    for tip_x in (0.40, 0.39, 0.38):
        robot_xy = np.array([cx, cy]) - rot2(th) @ np.array([tip_x - D + PUCK_L / 2, 0.0])
        if squares_overlap(robot_xy, th, FOOT + MARGIN, np.zeros(2), 0.0, HALF):
            reason = "로봇 몸체가 박스와 겹침"
            best = best or (False, reason, (*robot_xy, th), tip_x)
            continue
        P = LOW[tip_x]
        W = P[:, :2] @ rot2(th).T + robot_xy
        inside = (np.abs(W[:, 0]) <= HALF) & (np.abs(W[:, 1]) <= HALF)
        if inside.any():
            best = (False, "손/손목이 박스에 닿음", (*robot_xy, th), tip_x) if best is None or best[1] != "손/손목이 박스에 닿음" else best
            continue
        return True, "됨", (*robot_xy, th), tip_x
    return best


if __name__ == "__main__":
    xs = np.arange(-0.075, 0.0751, 0.005)
    yaws = np.radians(np.arange(0, 180, 15))
    rows = []
    for cx in xs:
        for cy in xs:
            for yaw in yaws:
                # puck must lie fully on the box top
                cor = np.array([[s * PUCK_L / 2, t * PUCK_S / 2] for s in (-1, 1) for t in (-1, 1)]) @ rot2(yaw).T + [cx, cy]
                if np.abs(cor).max() > HALF:
                    continue
                res = [check(cx, cy, yaw, e) for e in (1, -1)]
                ok = any(r[0] for r in res)
                rows.append((cx, cy, yaw, ok, res[0][1], res[1][1]))
    R = np.array([(r[0], r[1], r[2], r[3]) for r in rows])
    np.save("sweep.npy", R)
    print(f"퍽 자세 {len(R)}개 (위치 5 mm, 각도 15° 간격) 중 쥘 수 있음 {int(R[:, 3].sum())}개 = {R[:, 3].mean()*100:.1f}%")
    reasons = {}
    for r in rows:
        if not r[3]:
            for k in (r[4], r[5]):
                reasons[k] = reasons.get(k, 0) + 1
    print("실패 이유 (양 끝 각각):", reasons)
    # distance from the nearest edge for ok poses
    okp = R[R[:, 3] == 1]
    if len(okp):
        print("쥘 수 있는 퍽 중심의 가장자리까지 최소 거리 범위:",
              np.round((HALF - np.abs(okp[:, :2]).max(1)).min() * 1000), "~", np.round((HALF - np.abs(okp[:, :2]).max(1)).max() * 1000), "mm")
