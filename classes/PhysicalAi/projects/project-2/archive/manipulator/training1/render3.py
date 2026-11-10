"""GIF of the body-aware end-grasp check. Poses = saved IK results (free_*.npy, cup_*.npy) from check_body.py / check_cups_path.py.
Red points = arm points inside the robot body, the floor or the box."""
import re
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon, Rectangle
import armgeo as A
import check_body as CB
import render_check_geo as G

OUT = sys.argv[1]
FPS = 12
plt.rcParams["font.family"] = ["NanumGothic", "NanumSquareRound", "DejaVu Sans"]
FLOOR, BOX_TOP, BOX_S = CB.FLOOR, CB.BOX_TOP, CB.BOX_S
PUCK_L, PUCK_S, D, H = 0.060, 0.0348, 0.025, 0.025
X, Y, Z = np.eye(3)
cfg = open(f"{A.REPO}/config/rack_cells.yaml").read()
CUP_FLOOR = float(re.search(r"floor_z:\s*([-\d.]+)", cfg).group(1))
CUP_RIM = float(re.search(r"rim_z:\s*([-\d.]+)", cfg).group(1))
CELLS = sorted([(n, float(x), float(y), float(yw)) for n, x, y, yw in
                re.findall(r"(S\d+): \{[^}]*xy: \[([-\d.]+), ([-\d.]+)\], yaw_deg: ([-\d.]+)", cfg)], key=lambda c: int(c[0][1:]))
CELL = {c[0]: c for c in CELLS}
BODY_ABOVE = CB.above


def hit_mask(P, box_x0):
    chassis = (np.abs(P[:, 0]) <= 0.16) & (np.abs(P[:, 1]) <= 0.16) & (P[:, 2] <= 0.091)
    vox = np.array([tuple(v) in CB.OCC for v in np.floor(P / CB.VOX).astype(int)])
    m = chassis | vox | (P[:, 2] < FLOOR + 0.002)
    if box_x0 is not None:
        m |= (P[:, 0] >= box_x0) & (P[:, 0] <= box_x0 + BOX_S) & (np.abs(P[:, 1]) <= BOX_S / 2) & (P[:, 2] < BOX_TOP + 0.002)
    return m


def near(q, p, a, c, period):
    return A.solve(q, p, a, c, period)


def seq(keys, sec=0.9):
    out = []
    for (q0, f0, h0, _), (q1, f1, h1, lab) in zip(keys[:-1], keys[1:]):
        n = max(int(sec * FPS), 1)
        for i in range(n):
            s = 0.5 - 0.5 * np.cos(np.pi * (i + 1) / n)
            out.append(dict(q=q0 + (q1 - q0) * s, finger=f0 + (f1 - f0) * s, held=h0 and h1, label=lab))
    return out


def hold(fr, sec):
    return [dict(fr) for _ in range(int(sec * FPS))]


frames = []
import check_v2 as V
STAND = [P for n, P in __import__("body").body_points().items() if n == "gripper_park_stand_TEMP"][0]
q_g, q_pre, q_lift = np.load("v2grasp_0.40_20.npy")
tip_g, _, _ = A.grip(q_g)
box_x0 = tip_g[0] - D - 0.020
q_in, q_up = np.load("v2cup_0.40_20_S10.npy")
for f in hold(dict(q=V.Q_PARK, finger=V.PARKED_F, held=False, label="홈: 손이 받침(주황) 안에 앉아 있음"), 1.5):
    frames.append(dict(f, title="① 홈 자세에서 시작 (URDF parked)", box_x0=box_x0, e=0.020, puck="box", nocheck=True))
for f in seq([(V.Q_PARK, V.PARKED_F, False, ""), (V.Q_P0, V.OPEN, False, "받침에서 빠져 P0 (팀이 쓰는 기존 동작)")], 1.2):
    frames.append(dict(f, title="① 홈 자세에서 시작 (URDF parked)", box_x0=box_x0, e=0.020, puck="box", nocheck=True))
keys = [(V.Q_P0, G.FINGER_OPEN, False, "P0"), (q_pre, G.FINGER_OPEN, False, "손을 수평으로, 퍽 끝 위"),
        (q_g, G.FINGER_OPEN, False, "위에서 내려와 퍽 끝 25 mm를 감쌈"), (q_g, G.FINGER_ON, True, "쥠 (한 번만)"),
        (q_lift, G.FINGER_ON, True, "들어 올림"), (q_up, G.FINGER_ON, True, "손을 세우며 S10 위로 (J5로 칸 방향)"),
        (q_in, G.FINGER_ON, True, "S10에 내림"), (q_in, G.FINGER_OPEN, False, "놓음"), (q_up, G.FINGER_OPEN, False, "빠짐"),
        (V.Q_P0, G.FINGER_OPEN, False, "P0로 돌아옴 (받침 위)")]
f2 = seq(keys, 1.0)
for f in f2 + hold(f2[-1], 1.0):
    frames.append(dict(f, title=f"② P0에서 쥐고 S10에 넣고 P0로 복귀: 받침 포함 충돌 없음 (로봇은 박스에서 {(box_x0 - 0.16)*100:.0f} cm)",
                       box_x0=box_x0, e=0.020, puck="box", cell="S10"))

# ③ same robot spot, puck end 35 mm from the edge -> wrist hits the box
q_g35 = A.solve(q_g, tip_g, X, Y, 180.0)
box35 = tip_g[0] - D - 0.035
f3 = seq([(A.Q_TEMPLATE, G.FINGER_OPEN, False, "준비"), (q_g35, G.FINGER_OPEN, False, "퍽 끝이 가장자리에서 35 mm")], 1.2)
for f in f3 + hold(f3[-1], 2.0):
    frames.append(dict(f, title="③ 같은 자리, 퍽 끝이 박스 가장자리에서 35 mm: 손목이 박스에 닿음 (빨간 점)", box_x0=box35, e=0.035, puck="box"))

# ④ all 12 cups
for n, *_ in CELLS:
    qi, qu = np.load(f"v2cup_0.40_20_{n}.npy")
    for f in seq([(qu, G.FINGER_ON, True, f"{n} 위"), (qi, G.FINGER_ON, True, f"{n}: 넣음 · 충돌 없음")], 0.5) + hold({}, 0):
        frames.append(dict(f, title="④ 12칸 모두: 손을 수직으로 세우고 J5로 칸 방향을 맞춰 넣음", box_x0=None, e=None, puck=None, cell=n))


def puck_corners(c, u, v):
    w = np.cross(u, v)
    return np.array([c + a * PUCK_L / 2 * u + b * PUCK_S / 2 * v + d * PUCK_S / 2 * w
                     for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)])


def hull(pts):
    pts = sorted(map(tuple, pts))
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


fig, (ax_s, ax_t) = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw=dict(width_ratios=[1.35, 1]))
fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.02, wspace=0.04)
COL = {"arm_link1": "#888", "arm_link2": "#888", "arm_link3": "#777", "arm_link4_wrist": "#555",
       "arm_link5_wrist_roll": "#333", "gripper_finger_a": "#2a7", "gripper_finger_b": "#2a7"}
released = {"S10": False}


def draw(k):
    f = frames[k]
    ax_s.clear(); ax_t.clear()
    fig.suptitle(f["title"], fontsize=13, fontweight="bold")
    ax_s.set_title(f"옆에서 · {f['label']}", fontsize=11); ax_t.set_title("위에서", fontsize=11)
    for ax in (ax_s, ax_t):
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax_s.set_xlim(-0.20, 0.60); ax_s.set_ylim(FLOOR - 0.01, 0.40)
    ax_t.set_xlim(-0.20, 0.60); ax_t.set_ylim(-0.24, 0.24)
    ax_s.plot([-0.2, 0.6], [FLOOR, FLOOR], "k", lw=1)
    ax_s.add_patch(Rectangle((-0.16, FLOOR + 0.005), 0.32, 0.091 - FLOOR - 0.005, fc="#e3e8ef", ec="#456"))
    ax_t.add_patch(Rectangle((-0.16, -0.16), 0.32, 0.32, fc="#e3e8ef", ec="#456"))
    ax_s.scatter(BODY_ABOVE[::20, 0], BODY_ABOVE[::20, 2], s=0.5, c="#9ab")
    ax_s.scatter(STAND[::4, 0], STAND[::4, 2], s=1.5, c="#f0a030", zorder=2)
    ax_t.scatter(STAND[::4, 0], STAND[::4, 1], s=1.5, c="#f0a030", zorder=2)
    for n, cx, cy, yw in CELLS:
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * 0.018
        r = np.radians(yw); R = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
        on = f.get("cell") == n
        ax_t.add_patch(Polygon(sq @ R.T + [cx, cy], closed=True, fill=on, fc="#fde2a7", ec="#456", lw=1.4 if on else 0.7))
        ax_t.annotate(n, (cx - 0.013, cy - 0.006), fontsize=6, color="#456")
    if f["box_x0"] is not None:
        bx = f["box_x0"]
        ax_s.add_patch(Rectangle((bx, FLOOR), BOX_S, 0.070, fc="#d8c3a5", ec="#8a6d3b"))
        ax_t.add_patch(Rectangle((bx, -BOX_S / 2), BOX_S, BOX_S, fc="#efe3cf", ec="#8a6d3b"))
        ax_s.annotate(f"퍽 끝 ↔ 가장자리 {f['e']*1000:.0f} mm", (bx, BOX_TOP + 0.05), fontsize=9, color="#8a6d3b")
        if bx > 0.17:
            ax_s.annotate("", (0.16, FLOOR + 0.02), (bx, FLOOR + 0.02), arrowprops=dict(arrowstyle="<->", color="#456"))
            ax_s.annotate(f"{(bx - 0.16)*100:.0f} cm", ((0.16 + bx) / 2 - 0.02, FLOOR + 0.025), fontsize=9, color="#456")

    # puck
    tip, app, close = A.grip(f["q"])
    c = None
    if f["held"]:
        c, u, v = tip + (PUCK_L / 2 - D) * app, app, close
    elif f["puck"] == "box":
        after_release = f.get("cell") and f["label"] in ("놓음", "빠짐")
        if after_release:
            n, cx, cy, yw = CELL[f["cell"]]
            c, u, v = np.array([cx, cy, CUP_FLOOR + PUCK_L / 2]), -Z, np.array([np.cos(np.radians(yw)), np.sin(np.radians(yw)), 0])
        else:
            c, u, v = np.array([f["box_x0"] + f["e"] + PUCK_L / 2, 0, BOX_TOP + PUCK_S / 2]), X, Y
    if c is not None:
        P = puck_corners(c, u, v)
        ax_s.add_patch(Polygon(hull(P[:, [0, 2]]), closed=True, fc="#d9534f", ec="k", zorder=2))
        ax_t.add_patch(Polygon(hull(P[:, [0, 1]]), closed=True, fc="#d9534f", ec="k", zorder=2))

    nhit = 0
    for nm, P in G.world_points(f["q"], f["finger"]).items():
        ax_s.scatter(P[:, 0], P[:, 2], s=0.8, c=COL[nm], zorder=3)
        ax_t.scatter(P[:, 0], P[:, 1], s=0.8, c=COL[nm], zorder=3)
        if nm == "arm_link1" or f.get("nocheck"):
            continue
        m = hit_mask(P, f["box_x0"])
        if m.any():
            nhit += m.sum()
            ax_s.scatter(P[m, 0], P[m, 2], s=7, c="red", zorder=4)
            ax_t.scatter(P[m, 0], P[m, 1], s=7, c="red", zorder=4)
    ax_s.annotate("(홈: 받침에 앉은 상태, 검사 안 함)" if f.get("nocheck") else "충돌 없음" if nhit == 0 else f"충돌 점 {nhit}개", (-0.19, 0.37), fontsize=12, fontweight="bold",
                  color="#2a7" if nhit == 0 else "red")
    ax_s.annotate("점 = URDF 팔·그리퍼 메시 · 자세 = 팀 팔 모델 IK · 회색 박스 = 로봇 차체 · 주황 = 그리퍼 받침", (-0.19, FLOOR + 0.004), fontsize=7, color="#666")


if len(sys.argv) > 2:
    for k in map(int, sys.argv[2].split(",")):
        draw(k); fig.savefig(f"k{k}.png", dpi=70)
    sys.exit()
anim = FuncAnimation(fig, draw, frames=len(frames), interval=1000 / FPS)
anim.save(OUT, writer=PillowWriter(fps=FPS))
print(OUT, len(frames))
