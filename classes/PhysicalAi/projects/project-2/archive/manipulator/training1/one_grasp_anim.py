"""Schematic animation: grab a lying puck once, flip it upright in hand, drop it into a rack cup.
Left = top view (base lines J1 up with the puck's long axis). Right = side view in the arm plane.
Not a physics sim: sizes are roughly to scale (puck 34.8 x 60 mm, cup 28 mm deep), arm lengths made up."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon, Rectangle, FancyArrow

OUT = sys.argv[1]
FPS = 20
PUCK_L, PUCK_S = 0.060, 0.0348
S = np.array([0.0, 0.20])          # shoulder (J2)
L1, L2, LH = 0.13, 0.12, 0.10      # upper arm, forearm, J4 -> grip point
CUP_X, CUP_RIM, CUP_FLOOR = 0.08, 0.17, 0.142
PUCK_C0 = np.array([0.27, PUCK_S / 2])
FINGER_HALF_LEN, FINGER_HALF_W = 0.016, 0.0164


def rot(v, deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def unit(deg):
    r = np.radians(deg)
    return np.array([np.cos(r), np.sin(r)])


def rect(center, axis, length, width):
    u = axis / np.linalg.norm(axis)
    n = np.array([-u[1], u[0]])
    h, w = length / 2, width / 2
    return np.array([center + u * h + n * w, center + u * h - n * w, center - u * h - n * w, center - u * h + n * w])


def ik(w):
    d = w - S
    r = np.clip(np.linalg.norm(d), 1e-6, L1 + L2 - 1e-6)
    a = np.arctan2(d[1], d[0])
    b = np.arccos(np.clip((L1**2 + r**2 - L2**2) / (2 * L1 * r), -1, 1))
    elbow = S + L1 * np.array([np.cos(a + b), np.sin(a + b)])   # elbow up
    return elbow


# ---- key poses (grip point g, hand approach angle deg, finger closed 0..1, puck held?)
# g = finger pad centre. Pad sits 16 mm in from the J1-side end and a bit above mid-height,
# so the lowest finger corner clears the floor at a 45° hand.
A_GRASP, A_CUP = -45.0, -135.0
g_grasp = np.array([PUCK_C0[0] - PUCK_L / 2 + 0.016, 0.024])
D_GRASP = PUCK_C0 - g_grasp        # puck centre from pad centre, fixed in the hand
d_cup = rot(D_GRASP, A_CUP - A_GRASP)
# at the cup: lowest finger corner 3 mm above the rim, puck centred on the cup, puck drops the rest
low_cup = FINGER_HALF_LEN * abs(unit(A_CUP)[1]) + FINGER_HALF_W * abs(unit(A_CUP + 90)[1])
g_cup = np.array([CUP_X - d_cup[0], CUP_RIM + 0.003 + low_cup])
DROP = (g_cup[1] + d_cup[1] - PUCK_L / 2) - CUP_FLOOR
g_above = g_grasp + np.array([-0.03, 0.08])
g_lift = g_grasp + np.array([0.0, 0.07])
g_cup_above = g_cup + np.array([0.0, 0.07])
g_home = np.array([0.12, 0.30])

# (seconds, title, g_from, g_to, ang_from, ang_to, close_from, close_to, held)
PHASES = [
    (2.0, "1. Base slides so J1 sits on the puck's long axis", g_home, g_home, -90, -90, 0, 0, False),
    (1.2, "2. Hand tilted 45°, reach the J1-side end of the puck", g_home, g_above, -90, A_GRASP, 0, 0, False),
    (0.8, "2. Hand tilted 45°, reach the J1-side end of the puck", g_above, g_grasp, A_GRASP, A_GRASP, 0, 0, False),
    (0.6, "3. Close fingers across the square end (one grasp)", g_grasp, g_grasp, A_GRASP, A_GRASP, 0, 1, False),
    (0.7, "4. Lift", g_grasp, g_lift, A_GRASP, A_GRASP, 1, 1, True),
    (2.0, "5. Carry back and pitch the hand 90°: puck turns upright", g_lift, g_cup_above, A_GRASP, A_CUP, 1, 1, True),
    (0.9, "6. Lower until the fingers are just above the rim", g_cup_above, g_cup, A_CUP, A_CUP, 1, 1, True),
    (0.6, f"7. Open: puck drops {DROP * 1000:.0f} mm into the cup, upright", g_cup, g_cup, A_CUP, A_CUP, 1, 0, False),
    (0.9, "7. Open and leave: puck stands in the cup", g_cup, g_cup_above, A_CUP, A_CUP, 0, 0, False),
    (1.2, "Done: no stand, no second grasp", g_cup_above, g_cup_above, A_CUP, A_CUP, 0, 0, False),
]
frames = []
for dur, title, g0, g1, a0, a1, c0, c1, held in PHASES:
    n = int(dur * FPS)
    for i in range(n):
        t = i / max(n - 1, 1)
        s = 0.5 - 0.5 * np.cos(np.pi * t)
        frames.append(dict(title=title, g=g0 + (g1 - g0) * s, ang=a0 + (a1 - a0) * s, close=c0 + (c1 - c0) * s,
                           held=held, phase=PHASES.index((dur, title, g0, g1, a0, a1, c0, c1, held)), t=s))

fig, (ax_top, ax) = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw=dict(width_ratios=[1, 1.5]))
fig.subplots_adjust(left=0.03, right=0.99, top=0.84, bottom=0.04, wspace=0.08)

state = {"puck_c": PUCK_C0.copy(), "puck_axis": 0.0}


def draw(k):
    f = frames[k]
    ax.clear(); ax_top.clear()
    fig.suptitle(f["title"], fontsize=14, fontweight="bold")

    # ---------- top view
    ax_top.set_title("Top view", fontsize=10)
    ax_top.set_xlim(-0.25, 0.45); ax_top.set_ylim(-0.30, 0.30); ax_top.set_aspect("equal"); ax_top.axis("off")
    puck_top_c = np.array([0.30, 0.0]); puck_yaw = 0.0
    j1_start, j1_end = np.array([0.0, -0.12]), np.array([0.0, 0.0])
    if f["phase"] == 0:
        j1 = j1_start + (j1_end - j1_start) * f["t"]
    else:
        j1 = j1_end
    body = rect(j1, unit(0), 0.24, 0.20)
    ax_top.add_patch(Polygon(body, closed=True, fc="#dfe6ee", ec="#456", lw=1.5))
    ax_top.plot(*j1, "o", color="#c33", ms=8); ax_top.annotate("J1", j1 + [-0.05, 0.03], fontsize=9, color="#c33")
    ax_top.plot([-0.25, 0.45], [0, 0], "--", color="#c33", lw=0.8)
    ax_top.annotate("puck long axis", (0.20, 0.015), fontsize=8, color="#c33")
    if f["phase"] >= 1:
        reach = (f["g"][0] - 0.0)
        ax_top.plot([j1[0], j1[0] + max(reach, 0.05)], [j1[1], j1[1]], color="#555", lw=5, solid_capstyle="round", alpha=0.6)
    if f["phase"] <= 4 or (f["phase"] == 5 and f["t"] < 0.05):
        ax_top.add_patch(Polygon(rect(puck_top_c, unit(puck_yaw), PUCK_L, PUCK_S), closed=True, fc="#d9534f", ec="k"))
    box = Rectangle((0.20, -0.09), 0.16, 0.18, fill=False, ec="#8a6d3b", lw=1.5)
    ax_top.add_patch(box); ax_top.annotate("start box", (0.21, -0.13), fontsize=8, color="#8a6d3b")
    for cx, cy in [(0.08, -0.04), (0.08, 0.04), (0.02, -0.04), (0.02, 0.04)]:
        ax_top.add_patch(Rectangle((cx - 0.018, cy - 0.018), 0.036, 0.036, fill=False, ec="#456", lw=1))
    ax_top.annotate("rack cups", (-0.03, -0.085), fontsize=8, color="#456")
    if f["phase"] >= 7:
        ax_top.add_patch(Rectangle((CUP_X - PUCK_S / 2, -0.04 - PUCK_S / 2), PUCK_S, PUCK_S, fc="#d9534f", ec="k"))

    # ---------- side view
    ax.set_title("Side view (arm plane)", fontsize=10)
    ax.set_xlim(-0.16, 0.42); ax.set_ylim(-0.03, 0.40); ax.set_aspect("equal"); ax.axis("off")
    ax.plot([-0.16, 0.42], [0, 0], color="k", lw=1.5)
    ax.add_patch(Rectangle((-0.12, 0.04), 0.26, 0.09, fc="#dfe6ee", ec="#456"))
    for wx in (-0.09, 0.11):
        ax.add_patch(plt.Circle((wx, 0.035), 0.033, fc="#333"))
    ax.add_patch(Rectangle((-0.015, 0.13), 0.03, 0.07, fc="#999", ec="#555"))
    ax.add_patch(Rectangle((CUP_X - 0.022, 0.13), 0.044, CUP_RIM - 0.13, fill=False, ec="#456", lw=2))
    ax.plot([CUP_X - 0.018, CUP_X + 0.018], [CUP_FLOOR, CUP_FLOOR], color="#456", lw=1)
    ax.annotate("cup", (CUP_X + 0.025, CUP_RIM - 0.015), fontsize=8, color="#456")
    ax.plot([0.20, 0.20], [0, 0.04], color="#8a6d3b", lw=3); ax.plot([0.36, 0.36], [0, 0.04], color="#8a6d3b", lw=3)
    ax.annotate("start box", (0.24, -0.022), fontsize=8, color="#8a6d3b")

    a = unit(f["ang"]); g = f["g"]
    w = g - LH * a
    e = ik(w)
    ax.plot([S[0], e[0], w[0]], [S[1], e[1], w[1]], color="#555", lw=7, solid_capstyle="round", alpha=0.85)
    for p in (S, e, w):
        ax.plot(*p, "o", color="#222", ms=6)
    ax.plot([w[0], g[0] - 0.02 * a[0]], [w[1], g[1] - 0.02 * a[1]], color="#555", lw=5)

    # puck
    if f["held"]:
        turn = f["ang"] - A_GRASP
        state["puck_c"] = g + rot(D_GRASP, turn); state["puck_axis"] = turn
    elif f["phase"] < 4:
        state["puck_c"] = PUCK_C0.copy(); state["puck_axis"] = 0.0
    elif f["phase"] == 7:   # released: fall to the cup floor
        top = np.array([CUP_X, CUP_FLOOR + DROP + PUCK_L / 2])
        state["puck_c"] = top - np.array([0.0, DROP * min(f["t"] * 2.5, 1.0)])
    ax.add_patch(Polygon(rect(state["puck_c"], unit(state["puck_axis"]), PUCK_L, PUCK_S), closed=True, fc="#d9534f", ec="k", zorder=3))

    # gripper: palm + near finger (other finger is behind the puck, out of the page)
    palm_c = g - 0.045 * a
    ax.add_patch(Polygon(rect(palm_c, a, 0.04, 0.05), closed=True, fc="#333", ec="k", zorder=4))
    finger_c = g
    col = "#2a7" if f["close"] > 0.5 else "#7a7a7a"
    ax.add_patch(Polygon(rect(finger_c, a, 0.032, 0.0328), closed=True, fc=col, ec="k", alpha=0.55, zorder=5))
    ax.annotate("fingers " + ("closed" if f["close"] > 0.5 else "open"), g + np.array([0.03, 0.02]), fontsize=8, color=col, zorder=6)
    ax.annotate(f"hand {abs(f['ang'] + 90):.0f}° from vertical", (-0.15, 0.37), fontsize=9)


anim = FuncAnimation(fig, draw, frames=len(frames), interval=1000 / FPS)
anim.save(OUT, writer=PillowWriter(fps=FPS))
print(OUT, len(frames), "frames")
