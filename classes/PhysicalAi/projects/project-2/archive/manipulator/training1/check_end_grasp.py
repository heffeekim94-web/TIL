"""Horizontal end-grasp of a lying square puck on a start box, then vertical-hand insert into all 12 cups.
base_link frame: floor z = -0.072, box top z = 0.070 - 0.072. Robot footprint ±0.16 m (config/nav2.yaml)."""
import re
import numpy as np
import armgeo as A

BOX_TOP = 0.070 - A.BASE_Z_FLOOR
BOX_S = 0.205
PUCK_L, PUCK_S = 0.060, 0.0348
FINGER_OPEN, FINGER_ON_PUCK = 0.0072, -0.001       # prismatic value: gap 51 mm open, ~35 mm on the puck
ROBOT_FRONT = 0.16
CLEAR = 0.002

rng = np.random.default_rng(0)
SEEDS = [A.Q_TEMPLATE] + [rng.uniform(A.LO, A.HI) for _ in range(40)]


def solve(p, a, c, period):
    q, pe, ae, rerr = A.ik(p, a, c, period, SEEDS)
    return q, (pe < 1.0 and ae < 1.0 and rerr < 2.0), pe, ae, rerr


def box_hits(q, finger, box_x0, box_y0):
    """Lowest clearance [mm] of hand/arm points above the box top, over the box footprint (negative = inside the box)."""
    worst = np.inf
    for nm, P in A.hand_points(q, finger).items():
        over = (P[:, 0] >= box_x0) & (P[:, 0] <= box_x0 + BOX_S) & (np.abs(P[:, 1] - box_y0) <= BOX_S / 2)
        if over.any():
            worst = min(worst, (P[over, 2].min() - BOX_TOP) * 1000)
    return worst


print("=== 1. horizontal end-grasp, puck straight ahead of J1 (axis along base x), camera up")
print(" grip d = fingertip depth past the puck's near end; e = gap from box edge to the puck's near end")
print(f"{'h':>4} {'d':>4} {'e':>4} {'tip_x':>6} {'IK':>4} {'err mm/deg':>12} {'box clear mm':>13}")
ok_rows = []
for h in (0.020, 0.022, 0.025):              # fingertip axis height above the box top (puck centre = 17.4 mm)
    for d in (0.020, 0.025):
        for e in (0.0, 0.010, 0.020, 0.0325, 0.050, 0.0725):
            box_x0 = ROBOT_FRONT + 0.005
            near_end = box_x0 + e
            tip = np.array([near_end + d, 0.0, BOX_TOP + h])
            q, ok, pe, ae, rerr = solve(tip, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 180.0)
            clr = box_hits(q, FINGER_ON_PUCK, box_x0, 0.0) if ok else np.nan
            good = ok and clr >= CLEAR * 1000
            if good:
                ok_rows.append((h, d, e))
            print(f"{h*1000:4.0f} {d*1000:4.0f} {e*1000:4.1f} {tip[0]:6.3f} {'ok' if ok else 'NO':>4} {pe:5.1f}/{ae:4.1f}   {clr:10.1f}  {'<- works' if good else ''}")

print("\n=== 1b. how far forward can the horizontal hand reach at puck height? (tip x along base x)")
for x in np.arange(0.14, 0.42, 0.02):
    tip = np.array([x, 0.0, BOX_TOP + 0.022])
    q, ok, pe, ae, rerr = solve(tip, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 180.0)
    print(f"  tip x {x:.2f}: {'ok' if ok else 'NO'}  (pos {pe:.1f} mm, app {ae:.1f} deg)")

print("\n=== 2. insert: vertical hand, puck hanging below the fingertips, all 12 cups")
cfg = open(f"{A.REPO}/config/rack_cells.yaml").read()
floor_z = float(re.search(r"floor_z:\s*([-\d.]+)", cfg).group(1))
rim_z = float(re.search(r"rim_z:\s*([-\d.]+)", cfg).group(1))
cells = re.findall(r"(S\d+): \{[^}]*xy: \[([-\d.]+), ([-\d.]+)\], yaw_deg: ([-\d.]+)", cfg)
for d in (0.020, 0.025):
    tip_z = floor_z + (PUCK_L - d)
    print(f" grip d = {d*1000:.0f} mm -> fingertips {(tip_z - rim_z)*1000:.0f} mm above the rim, puck bottom on the cup floor")
    bad = []
    for name, x, y, yaw in cells:
        cyaw = np.radians(float(yaw))
        q, ok, pe, ae, rerr = solve(np.array([float(x), float(y), tip_z]), np.array([0, 0, -1.0]),
                                  np.array([np.cos(cyaw), np.sin(cyaw), 0.0]), 90.0)
        print(f"   {name:4} {'ok' if ok else 'NO':>3}  pos {pe:4.1f} mm  app {ae:4.1f}°  puck turn {rerr:4.1f}°")
        if not ok:
            bad.append(name)
    print(f"   -> {12 - len(bad)}/12 cups reachable" + (f", fails: {bad}" if bad else ""))
