"""GIF for sweep_pucks.py: example puck poses (robot placed on the puck axis, red = arm points inside the box),
then for each puck angle the map of puck centres that can be grabbed, then the overall map."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon, Rectangle
import sweep_pucks as S
import check_v2 as V
import render_check_geo as G

OUT = sys.argv[1]
FPS = 6
plt.rcParams["font.family"] = ["NanumGothic", "NanumSquareRound", "DejaVu Sans"]
R = np.load("sweep.npy")
HALF = S.HALF


def puck_poly(cx, cy, yaw):
    c = np.array([[s * S.PUCK_L / 2, t * S.PUCK_S / 2] for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    return c @ S.rot2(yaw).T + [cx, cy]


def grasp_points(tip_x):
    q_g, _, _ = np.load(f"v2grasp_{tip_x:.2f}_20.npy")
    return np.vstack([P for nm, P in G.world_points(q_g, V.ON).items()])


GP = {t: grasp_points(t) for t in (0.38, 0.39, 0.40)}

EXAMPLES = [(0.04, 0.0, 0), (0.06, 0.0, 0), (0.0, 0.0, 0), (0.04, 0.0, 90), (0.0, 0.06, 90), (0.05, 0.05, 45),
            (0.06, 0.0, 30), (-0.06, 0.03, 0)]
frames = []
for cx, cy, yd in EXAMPLES:
    for _ in range(int(2.0 * FPS)):
        frames.append(("ex", cx, cy, np.radians(yd)))
for yd in range(0, 180, 15):
    for _ in range(int(1.0 * FPS)):
        frames.append(("map", yd))
for _ in range(int(4 * FPS)):
    frames.append(("all",))

fig, ax = plt.subplots(figsize=(8.5, 7.2))
fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.02)


def draw_box(lim):
    ax.add_patch(Rectangle((-HALF, -HALF), 2 * HALF, 2 * HALF, fc="#efe3cf", ec="#8a6d3b", lw=1.5))
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def draw(k):
    ax.clear()
    f = frames[k]
    if f[0] == "ex":
        _, cx, cy, yaw = f
        draw_box(0.62)
        res = [S.check(cx, cy, yaw, e) for e in (1, -1)]
        pick = next((r for r in res if r[0]), res[0])
        ok, reason, (rx, ry, th), tip_x = pick
        fp = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * S.FOOT @ S.rot2(th).T + [rx, ry]
        ax.add_patch(Polygon(fp, closed=True, fc="#e3e8ef", ec="#456"))
        ax.annotate("로봇", (rx, ry), fontsize=10, ha="center", color="#456")
        W = GP[tip_x][:, :2] @ S.rot2(th).T + [rx, ry]
        ax.scatter(W[::3, 0], W[::3, 1], s=0.6, c="#555", zorder=3)
        P = S.LOW[tip_x]
        Wl = P[:, :2] @ S.rot2(th).T + [rx, ry]
        hit = (np.abs(Wl[:, 0]) <= HALF) & (np.abs(Wl[:, 1]) <= HALF)
        if hit.any():
            ax.scatter(Wl[hit, 0], Wl[hit, 1], s=5, c="red", zorder=4)
        ax.add_patch(Polygon(puck_poly(cx, cy, yaw), closed=True, fc="#d9534f", ec="k", zorder=5))
        ax.plot([rx, cx + 0.3 * np.cos(th)], [ry, cy + 0.3 * np.sin(th)], ":", c="#c33", lw=0.8)
        both = " / ".join(("됨" if r[0] else r[1]) for r in res)
        fig.suptitle(f"퍽 중심 ({cx*1000:+.0f}, {cy*1000:+.0f}) mm, 각도 {np.degrees(yaw):.0f}°: {'쥘 수 있음' if ok else '못 쥠'}",
                     fontsize=14, fontweight="bold", color="#2a7" if ok else "red")
        ax.set_title(f"양쪽 끝 결과: {both}\n로봇은 퍽 긴 축 위에 서서 팔을 {tip_x:.2f} m 뻗음 · 빨간 점 = 박스에 박히는 손/손목", fontsize=10)
    elif f[0] == "map":
        yd = f[1]
        draw_box(0.13)
        m = np.isclose(np.degrees(R[:, 2]), yd)
        sub = R[m]
        ax.scatter(sub[:, 0], sub[:, 1], s=28, marker="s", c=np.where(sub[:, 3] == 1, "#2a7", "#e88"), zorder=2)
        for cx, cy in ((0.0, 0.0), (0.06, 0.04)):
            ax.add_patch(Polygon(puck_poly(cx, cy, np.radians(yd)), closed=True, fill=False, ec="k", lw=1.2, zorder=3))
        fig.suptitle(f"퍽 각도 {yd}°: 초록 = 이 자리에 퍽 중심이 있으면 쥘 수 있음 ({sub[:, 3].mean()*100:.0f}%)", fontsize=13, fontweight="bold")
        ax.set_title("박스 위에서 본 그림 (205 × 205 mm) · 검은 테두리 = 이 각도의 퍽 모양 예시", fontsize=10)
    else:
        draw_box(0.13)
        xs = np.unique(np.round(R[:, 0], 4)); frac = {}
        for cx, cy, _, ok in R:
            frac.setdefault((round(cx, 4), round(cy, 4)), []).append(ok)
        pts = np.array([(x, y, np.mean(v)) for (x, y), v in frac.items()])
        sc = ax.scatter(pts[:, 0], pts[:, 1], s=28, marker="s", c=pts[:, 2], cmap="RdYlGn", vmin=0, vmax=1, zorder=2)
        fig.suptitle(f"전체: 퍽 자세 {len(R)}가지 중 {R[:, 3].mean()*100:.0f}%만 한 번에 쥘 수 있음", fontsize=14, fontweight="bold")
        ax.set_title("색 = 그 자리에서 쥘 수 있는 각도의 비율 (초록 100% · 빨강 0%) · 가운데는 어떤 각도로도 안 됨", fontsize=10)


anim = FuncAnimation(fig, draw, frames=len(frames), interval=1000 / FPS)
if len(sys.argv) > 2:
    for k in map(int, sys.argv[2].split(",")):
        draw(k); fig.savefig(f"s{k}.png", dpi=70)
    sys.exit()
anim.save(OUT, writer=PillowWriter(fps=FPS))
print(OUT, len(frames))
