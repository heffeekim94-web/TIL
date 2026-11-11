#!/usr/bin/env python3
"""보정 학습 환경 확인: 라이브러리 작업을 보정 0 (기본 경로 그대로) 또는 학습한 정책으로 돌려 작업마다 결과.
  $PY check_res.py --n 32                                   # 기본 경로만
  $PY check_res.py --n 32 --checkpoint logs/<실행>/model_500.pt
  $PY check_res.py --n 4 --gif                              # env 4 개 GIF (logs/check_res.gif)
"""
import argparse
import json
import sys
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--n', type=int, default=32)
p.add_argument('--start', type=int, default=0, help='라이브러리 몇 번부터')
p.add_argument('--ids', default='', help='라이브러리 번호 목록 (쉼표), 주면 --n · --start 대신')
p.add_argument('--library', default='logs/library_chain.npz')
p.add_argument('--checkpoint', default='')
p.add_argument('--gif', action='store_true')
p.add_argument('--max_steps', type=int, default=0, help='> 0: 이 스텝까지만 (짧게 찍기)')
p.add_argument('--every', type=int, default=12, help='GIF · 동영상 몇 스텝마다 한 장')
p.add_argument('--mp4', default='', help='동영상 파일 (logs/ 안), 주면 GIF 대신')
p.add_argument('--gui', action='store_true', help='Isaac Sim 창으로 보기 (GIF 대신)')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = not a.gui
a.gif = a.gif or bool(a.mp4)
a.enable_cameras = a.gif
IDS = [int(x) for x in a.ids.split(',')] if a.ids else None
if IDS:
    a.n = len(IDS)
app = AppLauncher(a).app
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402

from env_res import ResEnvCfg, Training2ResEnv  # noqa: E402
import viz  # noqa: E402

cfg = ResEnvCfg(); cfg.library = a.library; cfg.scene.num_envs = a.n
if a.gif:
    viz.add_camera(cfg, height=300, width=400)
env = Training2ResEnv(cfg)
env.set_fixed(IDS or range(a.start, a.start + a.n))
env.record = []
policy = None
if a.checkpoint:
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
    from rsl_rl.runners import OnPolicyRunner
    from cfg import TrainCfg
    wenv = RslRlVecEnvWrapper(env)
    runner = OnPolicyRunner(wenv, TrainCfg().runner_dict(), None, env.device)
    runner.load(a.checkpoint)
    policy = runner.get_inference_policy(env.device)
    obs = wenv.get_observations()
else:
    env.reset()
dev = env.device
done_once = torch.zeros(a.n, dtype=torch.bool, device=dev)
frames = []
if a.gif:
    cam = env.scene['viz_cam']; o = env.scene.env_origins.cpu().numpy()
    cam.set_world_poses_from_view(eyes=(o + np.r_[0.10, -0.50, 0.50]).astype(np.float32), targets=(o + np.r_[0.12, 0.0, 0.12]).astype(np.float32))
    from PIL import Image, ImageDraw, ImageFont
    F = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf', 15)
it = 0
while not done_once.all() and not (a.max_steps and it >= a.max_steps):
    with torch.inference_mode():
        if policy is not None:
            act = policy(obs)
            obs, _, dones, _ = wenv.step(act)
        else:
            _, _, term, trunc, _ = env.step(torch.zeros(a.n, 6, device=dev))
            dones = term | trunc
    done_once |= dones.bool()
    if a.gif and it % a.every == 0 and not done_once.all():
        rgb = cam.data.output['rgb'].torch.cpu().numpy()[..., :3].astype(np.uint8)
        k_ = min(a.n, 4)
        canvas = Image.new('RGB', (2 * 410, 2 * 330), 'white'); dr = ImageDraw.Draw(canvas)
        for k in range(k_):
            x, y = (k % 2) * 410, (k // 2) * 330
            canvas.paste(Image.fromarray(rgb[k]), (x, y + 28))
            m = env.lib_meta[int(env.li[k])]
            col = '#2e9e4f' if bool(env.clean[k]) else '#d93636'
            cells = ' → '.join(jb['cell'] for jb in m['jobs'])
            done_k = int(env.n_done[k]) + int(bool(env.placed[k]))
            what = ('스테이션 퍽 ' if m['task'] == 'store' else f"주사위 {m['pips']} 눈 · ") + f"{len(m['jobs'])} 개: {cells}"
            dr.text((x + 4, y + 4), f"{what} · 끝낸 퍽 {done_k} · " + ('충돌 없음' if bool(env.clean[k]) else '충돌!'), font=F, fill=col)
        frames.append(canvas)
    it += 1
rec = env.record[:a.n] if len(env.record) >= a.n else env.record
by = {}
for r in env.record:
    by.setdefault(r['env'], r)
rows = [by[k] for k in sorted(by)]
for r in rows:
    m = env.lib_meta[(IDS[r['env']] if IDS else a.start + r['env'])]
    print(r['env'], m['task'], [jb['cell'] for jb in m['jobs']], [jb.get('how', '')[:14] for jb in m['jobs']], '· 끝낸 퍽', r.get('done'), '/', len(m['jobs']), '· 충돌 없음', r['collision_free'], '· 성공', r['success'],
          '· 떨어뜨림', r['drop'], '· 가장 가까움', r['min_clearance_mm'], 'mm', flush=True)
for task in ('store', 'retrieve'):
    rr = [r for r in rows if env.lib_meta[(IDS[r['env']] if IDS else a.start + r['env'])]['task'] == task]
    if rr:
        print(f'{task}: {len(rr)} 개 · 퍽 끝냄 {np.mean([r["done_frac"] for r in rr]):.2f} · 충돌 없음 {np.mean([r["collision_free"] for r in rr]):.2f} · 성공 {np.mean([r["success"] for r in rr]):.2f}')
if a.mp4 and frames:
    import subprocess, tempfile
    tmp = Path(tempfile.mkdtemp())
    for i, f in enumerate(frames):
        f.save(tmp / f'{i:05d}.png')
    out = HERE / 'logs' / a.mp4
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(round(30 / a.every * 2)), '-i', str(tmp / '%05d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', str(out)], check=True)
    print('MP4', out, len(frames))
elif a.gif and frames:
    out = HERE / 'logs' / 'check_res.gif'
    frames[0].save(out, save_all=True, append_images=frames[1:] + [frames[-1]] * 10, duration=110, loop=0)
    print('GIF', out, len(frames))
app.close()
