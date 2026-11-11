#!/usr/bin/env python3
"""환경 검증: 팀 실물 기록 경로 (config/arm_paths.yaml) 를 학습 환경에 그대로 재생해 충돌 · 쥠 판정이 맞게 나오는지 본다.

기본 = retrieve_S7 을 'S7 말고 11 칸이 다 찬' 적재함에서. 설계 분석 (URDF 기하) 에서 쥔 퍽이 S4 · S9 퍽에 겹쳤던 경로.
결과: logs/replay_<경로>_<시각>.gif + .json (스텝마다 거리 · 충돌 · 쥠 · 그리퍼 힘)

예) $PY replay_check.py --enable_cameras
    $PY replay_check.py --path store_S9 --stored S1,S2,S3
"""
import argparse
import json
import sys
import time
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
TEAM = Path('/home/haeminkim/바탕화면/git/Project2_Turtle_Ninja')
p = argparse.ArgumentParser()
p.add_argument('--path', default='retrieve_S7')
p.add_argument('--stored', default='recorded', help="찬 칸: 'recorded' = 실물 기록 때 찬 칸 (arm_paths.yaml 주석), 'all' = 대상 칸 말고 11 개, 'none', 또는 S1,S2,...")
p.add_argument('--steps_per_point', type=int, default=2, help='경유점 하나에 정책 스텝 몇 번 (30 Hz)')
p.add_argument('--no_gif', action='store_true')
p.add_argument('--raw', action='store_true', help='처짐 보정을 빼지 않고 명령값 그대로 (실물 명령 ≠ 실제 자세, sag.py)')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
a.enable_cameras = not a.no_gif
app = AppLauncher(a).app

sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import yaml  # noqa: E402

from cfg import CELLS, GRIPPER_CLOSE, GRIPPER_OPEN, EnvCfg  # noqa: E402
from env import Training2Env  # noqa: E402

ap = yaml.safe_load(open(TEAM / 'config' / 'arm_paths.yaml'))['control_master']['ros__parameters']['arm_paths'][a.path]
Q = np.array(ap['q']).reshape(-1, 5)
close_i = max([i for i, g in enumerate(ap['grip']) if g == 'close'] or [len(Q)])
if not a.raw:   # 명령값 → 실물 실제 자세 (팀 처짐 모델). 쥔 동안 퍽 17 g. HOME (받침이 받침) 은 그대로
    import sag
    sm = sag.SagModel()
    held = lambda i: 0.017 if (i >= close_i) == a.path.startswith('retrieve') else 0.0
    Q = np.array([Q[0]] + [sm.true_from_cmd(Q[i], held(i)) for i in range(1, len(Q))])
cell = a.path.split('_')[1]
task = 'retrieve' if a.path.startswith('retrieve') else 'store'
if a.stored == 'recorded':     # '# retrieve_S5: 실물 ... · 그때 찬 칸 S10, S11, ...' (없음 = 빈 적재함)
    import re
    line = next(l for l in open(TEAM / 'config' / 'arm_paths.yaml') if re.match(rf'\s*# {a.path}:', l))
    rec = line.split('그때 찬 칸')[1].strip()
    stored = [] if rec.startswith('없음') else [c.strip() for c in rec.split(',')]
elif a.stored == 'all':
    stored = [c for c in CELLS if c != cell]
else:
    stored = [] if a.stored == 'none' else a.stored.split(',')
print(f'[replay] {a.path} · 찬 칸 {stored}', flush=True)

cfg = EnvCfg()
cfg.scene.num_envs = 1
cfg.episode_length_s = len(Q) * a.steps_per_point * cfg.sim.dt * cfg.decimation + 5
if not a.no_gif:
    import viz
    viz.add_camera(cfg)
env = Training2Env(cfg)
env.set_scenarios([{'task': task, 'cell': cell, 'dice': 4, 'stored': stored}])
env.no_terminate = True
env.reset()
if not a.no_gif:
    # 가까이: 대상 칸을 바깥 비스듬히 위에서 · 멀리: 로봇 전체 (env 0 기준)
    cxy = env.cell_floor[CELLS.index(cell), :2].cpu().numpy()
    out_dir = cxy / (np.linalg.norm(cxy) + 1e-9)
    VIEWS = [(tuple(np.r_[cxy + 0.24 * out_dir + [0.10, 0.0], 0.36]), tuple(np.r_[cxy, 0.20])),
             ((0.42, -0.42, 0.52), (0.06, 0.0, 0.17))]


def grab():
    imgs = []
    for eye, tgt in VIEWS:
        viz.aim(env, eye=eye, target=tgt)
        env.sim.render()
        env.scene['viz_cam'].update(0.0, force_recompute=True)
        imgs.append(viz.frame(env))
    return np.concatenate(imgs, 1)

# 그리퍼: 경로의 release / close 사건 그대로. store 는 처음부터 쥔 채 시작해야 하지만 환경은 HOME 출발이라
# store 경로는 박스 위 기준점부터라 처음 퍽 위치가 다름 → store 재생은 충돌 판정만 의미 있음
grip = GRIPPER_CLOSE
rows, frames = [], []
dev = env.device
for i in range(len(Q)):
    g = ap['grip'][i]
    if g == 'release':
        grip = GRIPPER_OPEN
    elif g == 'close':
        grip = GRIPPER_CLOSE
    env.scripted = (torch.tensor(Q[i], dtype=torch.float32, device=dev)[None], torch.tensor([grip], device=dev))
    for _ in range(a.steps_per_point):
        env.step(torch.zeros(1, 6, device=dev))
    d = {k: round(float(v[0]) * 1000, 2) for k, v in env.dist.items()}
    rows.append({'i': i, 'node': ap['nodes'][i], 'grip_cmd': 'open' if grip > 0.5 * (GRIPPER_OPEN + GRIPPER_CLOSE) else 'close', **{f'd_{k}_mm': v for k, v in d.items()},
                 'self_N': round(float(env.self_force[0]), 2), 'stored_moved_mm': round(float(env.stored_moved[0]) * 1000, 2),
                 'collision': bool(env.ev['collision'][0]), 'severe': bool(env.ev['severe'][0]), 'grasped': bool(env.grasped[0]),
                 'grip_q': round(float(env.grip_q[0]), 4), 'grip_N': round(float(env.grip_eff[0]), 2),
                 'd_stand_mm': round(min(float(env.d_stand[0]), 1.0) * 1000, 2),
                 'hand_puck_mm': round(float((env.work_w[0] - env.grasp_w[0]).norm()) * 1000, 1),
                 'root_mm': [round(float(x) * 1000, 2) for x in env.robot.data.root_pos_w.torch[0] - env.scene.env_origins[0]]})
    if not a.no_gif and i % 3 == 0:
        frames.append((i, grab()))

stamp = time.strftime('%Y%m%d_%H%M%S')
out = HERE / 'logs' / f'replay_{a.path}_{stamp}'
out.parent.mkdir(exist_ok=True)
(out.with_suffix('.json')).write_text(json.dumps({'path': a.path, 'stored': stored, 'rows': rows}, ensure_ascii=False, indent=0))
coll = [r for r in rows if r['collision']]
print(f'[replay] 경유점 {len(rows)} · 충돌 스텝 {len(coll)} · 쥠 {any(r["grasped"] for r in rows)}', flush=True)
for r in coll[:8]:
    print('  ', r, flush=True)

if not a.no_gif:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans']
    t = np.array([r['i'] for r in rows])
    fig = plt.figure(figsize=(15, 5.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.1, 1])
    axi, axd, axg = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1])
    fig.subplots_adjust(left=0.01, right=0.98, top=0.9, bottom=0.1, hspace=0.5)
    fig.suptitle(f'혁무님 실물 경로 {a.path} 를 학습 환경(Isaac 물리)에서 재생 · ' + ('처짐 보정 뺌' if not a.raw else '명령값 그대로') + f' · 찬 칸 {len(stored)} 개', fontsize=12)
    for k, c, lab in (('stored', '#2a78d6', '팔 ↔ 적재 퍽'), ('work_stored', '#eda100', '작업 퍽 ↔ 적재 퍽'), ('base', '#888', '팔 ↔ 몸체 부품')):
        axd.plot(t, [min(r[f'd_{k}_mm'], 80) for r in rows], color=c, lw=1.5, label=lab)
    axd.plot(t, [r['stored_moved_mm'] for r in rows], color='#e34948', lw=1.5, label='적재 퍽 밀린 거리')
    axd.axhline(0, color='#e34948', lw=0.8); axd.set_ylim(-10, 80); axd.set_ylabel('mm'); axd.legend(fontsize=8, frameon=False, loc='upper right')
    axd.set_title('거리 (음수 = 겹침) · 밀림', fontsize=10)
    axg.plot(t, [r['grip_N'] for r in rows], color='#444', lw=1.5, label='그리퍼 힘 [N]')
    axg.fill_between(t, 0, [12 if r['grasped'] else 0 for r in rows], color='#4caf50', alpha=0.25, label='쥠 판정')
    axg.fill_between(t, 0, [12 if r['collision'] else 0 for r in rows], color='#e34948', alpha=0.25, label='충돌 판정')
    axg.set_ylim(0, 12); axg.legend(fontsize=8, frameon=False, loc='upper left'); axg.set_xlabel('경유점 번호')
    cur = [axd.axvline(0, color='#999'), axg.axvline(0, color='#999')]
    im = axi.imshow(frames[0][1]); axi.axis('off')
    txt = axi.text(0.02, 0.97, '', transform=axi.transAxes, va='top', fontsize=11, color='white',
                   bbox=dict(facecolor='black', alpha=0.5, lw=0))

    def draw(k):
        i, img = frames[k]
        im.set_data(img)
        r = rows[i]
        txt.set_text(f"경유점 {i} · {r['node']}\n" + ('충돌!' if r['collision'] else '충돌 없음') + (' · 쥠' if r['grasped'] else ''))
        txt.set_color('#ff6b6b' if r['collision'] else 'white')
        for c in cur:
            c.set_xdata([i, i])

    FuncAnimation(fig, draw, frames=len(frames)).save(str(out.with_suffix('.gif')), writer=PillowWriter(fps=8), dpi=72)
    print(f'[replay] {out}.gif', flush=True)
app.close()
