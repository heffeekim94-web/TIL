"""Arm model (config/arm_kinematics.yaml, same chain as robot.urdf) + URDF collision meshes for the hand.
FK/IK mirror ros2_ws/src/manipulation/src/arm_kinematics.cpp (tip5/app5/close5 in the J5 frame)."""
import os
import re
import xml.etree.ElementTree as ET
import numpy as np

REPO = "/home/haeminkim/바탕화면/git/Project2_Turtle_Ninja"
MESH_ROOT = "/home/haeminkim/robot_lab/examples/nt_urdf_release_20261027_swerve"
URDF = f"{REPO}/sim/robot_sim/robot_description/robot.urdf"


def _yaml_arr(txt, key):
    m = re.search(rf"^\s*{key}:\s*\[([^\]]*)\]", txt, re.M)
    return np.array([float(v) for v in m.group(1).split(",")])


_t = open(f"{REPO}/config/arm_kinematics.yaml").read()
T_BASE = _yaml_arr(_t, "T_base_armbase").reshape(4, 4)
JOINT_T = _yaml_arr(_t, "joint_T").reshape(5, 4, 4)
AXIS = _yaml_arr(_t, "axis").reshape(5, 3)
TIP5, APP5, CLOSE5 = _yaml_arr(_t, "tip5"), _yaml_arr(_t, "app5"), _yaml_arr(_t, "close5")
LO, HI = _yaml_arr(_t, "lo"), _yaml_arr(_t, "hi")
Q_TEMPLATE = _yaml_arr(_t, "template_q")
BASE_Z_FLOOR = 0.072


def rot(axis, a):
    k = axis / np.linalg.norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    T = np.eye(4)
    T[:3, :3] = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
    return T


def frames(q):
    T = T_BASE.copy()
    out = []
    for j in range(5):
        T = T @ JOINT_T[j] @ rot(AXIS[j], q[j])
        out.append(T)
    return out


def grip(q):
    T5 = frames(q)[4]
    R = T5[:3, :3]
    return R @ TIP5 + T5[:3, 3], R @ APP5, R @ CLOSE5


def residual(q, p, a, c, period):
    tip, app, close = grip(q)
    r = np.zeros(7)
    r[:3] = (tip - p) * 1000
    r[3:6] = np.degrees(app - a)
    cp = close - close.dot(a) * a; cp /= np.linalg.norm(cp) + 1e-12
    ct = c - c.dot(a) * a; ct /= np.linalg.norm(ct) + 1e-12
    ang = np.arctan2(np.cross(ct, cp).dot(a), ct.dot(cp))
    k = 1.0 if period >= 179 else 4.0
    r[6] = np.degrees(np.sin(k * ang) / k)
    return r


def solve(q0, p, a, c, period=180.0, iters=300):
    x = np.clip(q0, LO + 1e-6, HI - 1e-6)
    r = residual(x, p, a, c, period); cost = r @ r; lam = 1e-3
    for _ in range(iters):
        J = np.zeros((7, 5))
        for j in range(5):
            d = np.zeros(5); d[j] = 1e-6
            J[:, j] = (residual(x + d, p, a, c, period) - residual(x - d, p, a, c, period)) / 2e-6
        JtJ, g = J.T @ J, J.T @ r
        improved = False
        while lam < 1e12:
            A = JtJ + lam * np.diag(np.diag(JtJ) + 1e-9)
            xn = np.clip(x + np.linalg.solve(A, -g), LO, HI)
            rn = residual(xn, p, a, c, period); cn = rn @ rn
            if cn < cost:
                done = cost - cn < 1e-14 * max(1, cost)
                x, r, cost = xn, rn, cn; lam = max(lam / 3, 1e-12); improved = True
                if done:
                    return x
                break
            lam *= 4
        if not improved or cost < 1e-16:
            break
    return x


def ik(p, a, c, period=180.0, seeds=None):
    """Best solution over seeds; returns (q, pos_err_mm, app_err_deg) or None."""
    seeds = seeds if seeds is not None else [Q_TEMPLATE] + [np.random.default_rng(i).uniform(LO, HI) for i in range(24)]
    best = None
    for s in seeds:
        q = solve(np.asarray(s, float), p, a, c, period)
        tip, app, close = grip(q)
        pe = np.linalg.norm(tip - p) * 1000
        ae = np.degrees(np.arccos(np.clip(app @ a, -1, 1)))
        cp = close - close.dot(a) * a; cp /= np.linalg.norm(cp) + 1e-12
        ct = c - c.dot(a) * a; ct /= np.linalg.norm(ct) + 1e-12
        re = np.degrees(np.arccos(np.clip(abs(cp @ ct), 0, 1)))
        if period < 179:
            re = min(re, 90 - re)
        score = pe + ae + re
        if best is None or score < best[3]:
            best = (q, pe, ae, score, re)
    q, pe, ae, _, re = best
    return q, pe, ae, re


# ---------- collision meshes (link frame = frames()[k] for arm links)
LINK_INDEX = {"arm_link1": 0, "arm_link2": 1, "arm_link3": 2, "arm_link4_wrist": 3, "arm_link5_wrist_roll": 4}


def _origin(el):
    o = el.find("origin")
    T = np.eye(4)
    if o is None:
        return T
    xyz = [float(v) for v in o.get("xyz", "0 0 0").split()]
    r, p, y = [float(v) for v in o.get("rpy", "0 0 0").split()]
    Rx = rot(np.array([1, 0, 0]), r)[:3, :3]; Ry = rot(np.array([0, 1, 0]), p)[:3, :3]; Rz = rot(np.array([0, 0, 1]), y)[:3, :3]
    T[:3, :3] = Rz @ Ry @ Rx; T[:3, 3] = xyz
    return T


def _obj_vertices(path):
    v = [list(map(float, ln.split()[1:4])) for ln in open(path) if ln.startswith("v ")]
    return np.array(v)


def _box_vertices(size, step=0.002):
    """Solid box sampled on a 2 mm grid (corners only would leave walls empty in the voxel check)."""
    s = np.array(size) / 2
    ax = [np.linspace(-h, h, max(int(2 * h / step) + 1, 2)) for h in s]
    g = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
    return g


def load_link_points(link_names):
    root = ET.parse(URDF).getroot()
    pts = {}
    for link in root.findall("link"):
        name = link.get("name")
        if name not in link_names:
            continue
        allp = []
        elems = link.findall("collision")
        if name.startswith("gripper_finger"):   # finger collision meshes are not on disk -> visual mesh
            elems = link.findall("visual")
        for col in elems:
            T = _origin(col)
            geo = col.find("geometry")
            mesh, box = geo.find("mesh"), geo.find("box")
            if mesh is not None:
                f = mesh.get("filename")
                path = os.path.join(MESH_ROOT, f) if os.path.exists(os.path.join(MESH_ROOT, f)) else os.path.join(os.path.dirname(URDF), f)
                if not os.path.exists(path):
                    continue
                v = _obj_vertices(path) * np.array([float(s) for s in mesh.get("scale", "1 1 1").split()])
            elif box is not None:
                v = _box_vertices([float(s) for s in box.get("size").split()])
            else:
                continue
            allp.append(v @ T[:3, :3].T + T[:3, 3])
        pts[name] = np.vstack(allp) if allp else np.zeros((0, 3))
    joints = {j.get("name"): j for j in root.findall("joint")}
    return pts, joints


HAND_LINKS = ["arm_link3", "arm_link4_wrist", "arm_link5_wrist_roll", "gripper_finger_a", "gripper_finger_b"]
_PTS, _JOINTS = load_link_points(HAND_LINKS)
_FINGER = {}
for nm in ("gripper_finger_a", "gripper_finger_b"):
    j = _JOINTS[f"{nm}_joint"]
    _FINGER[nm] = (_origin(j), np.array([float(v) for v in j.find("axis").get("xyz").split()]))


def hand_points(q, finger):
    """World (base_link) points of hand links. finger = prismatic value (same for both fingers)."""
    F = frames(q)
    out = {}
    for nm in HAND_LINKS:
        if nm in LINK_INDEX:
            T = F[LINK_INDEX[nm]]
        else:
            To, ax = _FINGER[nm]
            Tj = To.copy(); Tj[:3, 3] += ax / np.linalg.norm(ax) * finger
            T = F[4] @ Tj
        p = _PTS[nm]
        out[nm] = p @ T[:3, :3].T + T[:3, 3]
    return out


def finger_gap(finger):
    """Inner gap between the two fingers along close, at q = template (mm)."""
    pts = hand_points(Q_TEMPLATE, finger)
    _, app, close = grip(Q_TEMPLATE)
    a = pts["gripper_finger_a"] @ close; b = pts["gripper_finger_b"] @ close
    if a.mean() > b.mean():
        return (a.min() - b.max()) * 1000
    return (b.min() - a.max()) * 1000
