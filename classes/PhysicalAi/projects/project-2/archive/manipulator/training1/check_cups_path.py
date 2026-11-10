"""Vertical-hand insert into 12 cups + carry path from the free grasp, against body/floor."""
import re
import numpy as np
import armgeo as A
import check_body as CB

cfg = open(f"{A.REPO}/config/rack_cells.yaml").read()
CUP_FLOOR = float(re.search(r"floor_z:\s*([-\d.]+)", cfg).group(1))
CELLS = sorted([(n, float(x), float(y), float(yw)) for n, x, y, yw in
                re.findall(r"(S\d+): \{[^}]*xy: \[([-\d.]+), ([-\d.]+)\], yaw_deg: ([-\d.]+)", cfg)], key=lambda c: int(c[0][1:]))
X, Y, Z = np.eye(3)
D = 0.025
rng = np.random.default_rng(2)
SEEDS = [A.Q_TEMPLATE] + [rng.uniform(A.LO, A.HI) for _ in range(80)]
q_grasp = np.load("free_0.40_20.npy")
tip_g, _, _ = A.grip(q_grasp)
q_lift = A.solve(q_grasp, tip_g + 0.07 * Z, X, Y, 180.0)
print("lift hits", CB.hits(q_lift, CB.G.FINGER_ON))
out = {}
for n, cx, cy, yw in CELLS:
    c = np.array([np.cos(np.radians(yw)), np.sin(np.radians(yw)), 0])
    tip = np.array([cx, cy, CUP_FLOOR + 0.060 - D])
    best = None
    for s in [q_lift] + SEEDS:
        q = A.solve(np.asarray(s, float), tip, -Z, c, 90.0)
        t, a, _ = A.grip(q)
        if np.linalg.norm(t - tip) > 1e-3 or a @ -Z < np.cos(np.radians(1)):
            continue
        h = CB.hits(q, CB.G.FINGER_ON)
        q_up = A.solve(q, tip + 0.07 * Z, -Z, c, 90.0)
        hu = CB.hits(q_up, CB.G.FINGER_ON)
        # carry path lift -> above cup in joint space
        path = sum(sum(CB.hits(q_lift + (q_up - q_lift) * s_, CB.G.FINGER_ON).values()) for s_ in np.linspace(0, 1, 15))
        score = sum(h.values()) + sum(hu.values()) + path
        if best is None or score < best[0]:
            best = (score, q, q_up, h, path)
        if score == 0:
            break
    out[n] = best
    print(n, "no IK" if best is None else f"insert hits {best[3]}  carry-path hit pts {best[4]}  {'OK' if best[0]==0 else ''}")
    if best is not None:
        np.save(f"cup_{n}.npy", np.stack([best[1], best[2]]))
