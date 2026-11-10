"""Full motion check from the real home pose (URDF parked, gripper in the stand), with the stand modelled solid.
parked -> C1_P0 -> above the puck end -> grasp -> lift -> above cup -> insert -> release -> above cup -> C1_P0 -> parked.
Every interpolated step (joint space) is checked against chassis, parts on the plate (incl. the stand), floor and box."""
import json
import re
import numpy as np
import armgeo as A
import check_body as CB

POSE = json.load(open(f"{A.REPO}/sim/robot_sim/robot_description/config/initial_pose.json"))
Q_PARK = np.array([POSE["positions"][f"arm_joint{i}"] for i in range(1, 6)])
Q_P0 = np.array([POSE["poses"]["C1_P0"]["q_rad"][f"arm_joint{i}"] for i in range(1, 6)])
cfg = open(f"{A.REPO}/config/rack_cells.yaml").read()
CUP_FLOOR = float(re.search(r"floor_z:\s*([-\d.]+)", cfg).group(1))
CELLS = sorted([(n, float(x), float(y), float(yw)) for n, x, y, yw in
                re.findall(r"(S\d+): \{[^}]*xy: \[([-\d.]+), ([-\d.]+)\], yaw_deg: ([-\d.]+)", cfg)], key=lambda c: int(c[0][1:]))
X, Y, Z = np.eye(3)
D, H = 0.025, 0.025
OPEN, ON, PARKED_F = 0.0072, -0.001, -0.0212
rng = np.random.default_rng(3)
SEEDS = [A.Q_TEMPLATE, Q_P0] + [rng.uniform(A.LO, A.HI) for _ in range(150)]


def nhit(q, f, box_x0):
    return sum(CB.hits(q, f, box_x0).values())


def seg_hits(q0, q1, f0, f1, box_x0, n=12):
    return max(nhit(q0 + (q1 - q0) * s, f0 + (f1 - f0) * s, box_x0) for s in np.linspace(0, 1, n))


def ik_all(p, a, c, period, seeds):
    sols = []
    for s in seeds:
        q = A.solve(np.asarray(s, float), p, a, c, period)
        t, ap, _ = A.grip(q)
        if np.linalg.norm(t - p) < 1e-3 and ap @ a > np.cos(np.radians(1)) and not any(np.abs(q - o).max() < 0.05 for o in sols):
            sols.append(q)
    return sols


if __name__ == "__main__":
    print("home pose itself (gripper resting in the stand):", CB.hits(Q_PARK, PARKED_F), " P0:", CB.hits(Q_P0, OPEN))
    print("parked -> P0 path worst:", seg_hits(Q_PARK, Q_P0, PARKED_F, OPEN, None))
    results = []
    for tip_x in np.arange(0.34, 0.45, 0.01):
        for e in (0.0, 0.010, 0.020):
            box_x0 = tip_x - D - e
            tip = np.array([tip_x, 0, CB.BOX_TOP + H])
            for q_g in ik_all(tip, X, Y, 180.0, SEEDS):
                q_pre = A.solve(q_g, tip + 0.06 * Z, X, Y, 180.0)
                q_lift = A.solve(q_g, tip + 0.07 * Z, X, Y, 180.0)
                steps = {"grasp pose": nhit(q_g, ON, box_x0),
                         "P0->above puck": seg_hits(Q_P0, q_pre, OPEN, OPEN, box_x0),
                         "down to grasp": seg_hits(q_pre, q_g, OPEN, OPEN, box_x0),
                         "lift": seg_hits(q_g, q_lift, ON, ON, box_x0)}
                if sum(steps.values()):
                    continue
                cup_ok = []
                for n, cx, cy, yw in CELLS:
                    c = np.array([np.cos(np.radians(yw)), np.sin(np.radians(yw)), 0])
                    tin = np.array([cx, cy, CUP_FLOOR + 0.060 - D])
                    best = None
                    for q_in in ik_all(tin, -Z, c, 90.0, [q_lift, Q_P0] + SEEDS[:40]):
                        q_up = A.solve(q_in, tin + 0.07 * Z, -Z, c, 90.0)
                        w = (seg_hits(q_lift, q_up, ON, ON, box_x0) + seg_hits(q_up, q_in, ON, ON, box_x0, 6)
                             + seg_hits(q_in, q_up, OPEN, OPEN, box_x0, 6) + seg_hits(q_up, Q_P0, OPEN, OPEN, box_x0))
                        if best is None or w < best[0]:
                            best = (w, q_in, q_up)
                        if w == 0:
                            break
                    if best and best[0] == 0:
                        cup_ok.append(n)
                        np.save(f"v2cup_{tip_x:.2f}_{e*1000:.0f}_{n}.npy", np.stack([best[1], best[2]]))
                results.append((tip_x, e, len(cup_ok), cup_ok))
                np.save(f"v2grasp_{tip_x:.2f}_{e*1000:.0f}.npy", np.stack([q_g, q_pre, q_lift]))
                print(f"tip {tip_x:.2f} m  e {e*1000:2.0f} mm  grasp path clear, cups clear {len(cup_ok)}/12 {[c for c in [x[0] for x in CELLS] if c not in cup_ok]}", flush=True)
                break
    if not results:
        print("no grasp pose with a clear path")
