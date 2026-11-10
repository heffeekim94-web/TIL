"""Re-check the horizontal end-grasp with the robot's own body and the floor.
Body = solid chassis (footprint ±0.16 m, floor .. top plate z 0.091) + parts above the plate (URDF meshes, 4 mm voxels).
For each tip distance from J1, try many IK seeds and keep any solution with no hit on body, floor or box."""
import numpy as np
import armgeo as A
import body
import render_check_geo as G

VOX = 0.004
above = np.vstack([P[P[:, 2] > 0.0915] for n, P in body.body_points().items()])
OCC = set(map(tuple, np.floor(above / VOX).astype(int)))
OCC = {(i + di, j + dj, k + dk) for (i, j, k) in OCC for di in (-1, 0, 1) for dj in (-1, 0, 1) for dk in (-1, 0, 1)}
FLOOR = -A.BASE_Z_FLOOR
BOX_TOP = 0.070 - A.BASE_Z_FLOOR
BOX_S = 0.205


def hits(q, finger, box_x0=None):
    worst = {"body": 0, "floor": 0, "box": 0}
    for nm, P in G.world_points(q, finger).items():
        if nm == "arm_link1":
            continue   # J1 housing sits on the plate by design
        chassis = (np.abs(P[:, 0]) <= 0.16) & (np.abs(P[:, 1]) <= 0.16) & (P[:, 2] <= 0.091)
        vox = np.array([tuple(v) in OCC for v in np.floor(P / VOX).astype(int)])
        worst["body"] += int((chassis | vox).sum())
        worst["floor"] += int((P[:, 2] < FLOOR + 0.002).sum())
        if box_x0 is not None:
            worst["box"] += int(((P[:, 0] >= box_x0) & (P[:, 0] <= box_x0 + BOX_S) & (np.abs(P[:, 1]) <= BOX_S / 2)
                                 & (P[:, 2] < BOX_TOP + 0.002)).sum())
    return worst


X, Y, Z = np.eye(3)

if __name__ == "__main__":
    X, Y = np.eye(3)[0], np.eye(3)[1]
    rng = np.random.default_rng(1)
    SEEDS = [A.Q_TEMPLATE] + [rng.uniform(A.LO, A.HI) for _ in range(150)]
    D, H = 0.025, 0.025
    print("tip_x  e(mm)  solutions  best (body/floor/box hit points)")
    for tip_x in np.arange(0.18, 0.46, 0.02):
        tip = np.array([tip_x, 0.0, BOX_TOP + H])
        sols = []
        for s in SEEDS:
            q = A.solve(np.asarray(s, float), tip, X, Y, 180.0)
            t, a, _ = A.grip(q)
            if np.linalg.norm(t - tip) < 1e-3 and a @ X > np.cos(np.radians(1)):
                if not any(np.abs(q - p).max() < 0.05 for p in sols):
                    sols.append(q)
        for e in (0.0, 0.020, 0.035):
            box_x0 = tip_x - D - e
            if box_x0 < 0.165:
                continue
            res = [hits(q, G.FINGER_ON, box_x0) for q in sols]
            best = min(res, key=lambda r: sum(r.values())) if res else None
            free = [q for q, r in zip(sols, res) if sum(r.values()) == 0]
            print(f"{tip_x:.2f}  {e*1000:4.0f}  {len(sols):3d} IK, {len(free)} free   {best}")
            if free:
                np.save(f"free_{tip_x:.2f}_{e*1000:.0f}.npy", free[0])
    