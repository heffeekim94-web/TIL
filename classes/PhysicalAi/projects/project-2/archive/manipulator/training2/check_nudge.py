#!/usr/bin/env python3
"""툭 건드리기 정책 확인: env 몇 개로 에피소드를 돌려 성공 · 충돌을 세고 동영상 (logs/<--mp4>).
  $PY check_nudge.py --checkpoint logs/<실행>/model_100.pt --n 4 --episodes 3 --mp4 nudge_100.mp4
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--checkpoint', required=True)
p.add_argument('--n', type=int, default=4)
p.add_argument('--episodes', type=int, default=3, help='env 마다 에피소드 수')
p.add_argument('--mp4', default='nudge.mp4')
p.add_argument('--seed', type=int, default=7)
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
a.enable_cameras = True
app = AppLauncher(a).app
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from cfg import CELLS, TrainCfg  # noqa: E402
from env_nudge import NudgeEnvCfg, Training2NudgeEnv  # noqa: E402
import viz  # noqa: E402

torch.manual_seed(a.seed)
cfg = NudgeEnvCfg(); cfg.scene.num_envs = a.n
viz.add_camera(cfg, height=300, width=400)
env = Training2NudgeEnv(cfg)
env.record = []
wenv = RslRlVecEnvWrapper(env)
runner = OnPolicyRunner(wenv, TrainCfg().runner_dict(), None, env.device)
runner.load(a.checkpoint)
policy = runner.get_inference_policy(env.device)
obs = wenv.get_observations()
cam = env.scene['viz_cam']
o = env.scene.env_origins.cpu().numpy()
F = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf', 15)
tmp = Path(tempfile.mkdtemp()); nf = 0
count = np.zeros(a.n, int)
while count.min() < a.episodes:
    # 카메라: 각 env 의 작업 칸 가까이
    cells = env.cell.cpu().numpy()
    import pathgen as pg
    tg = np.array([np.r_[pg.CELLS[CELLS[c]]['xy'], 0.20] for c in cells]) + o
    cam.set_world_poses_from_view(eyes=(tg + np.r_[0.18, -0.20, 0.16]).astype(np.float32), targets=tg.astype(np.float32))
    with torch.inference_mode():
        obs, _, dones, _ = wenv.step(policy(obs))
    count += dones.cpu().numpy().astype(int)
    rgb = cam.data.output['rgb'].torch.cpu().numpy()[..., :3].astype(np.uint8)
    W, H = 400, 300
    cols = min(a.n, 2)
    canvas = Image.new('RGB', (cols * (W + 6), ((a.n + 1) // 2) * (H + 26)), 'white'); dr = ImageDraw.Draw(canvas)
    for k in range(a.n):
        x, y = (k % 2) * (W + 6), (k // 2) * (H + 26)
        canvas.paste(Image.fromarray(rgb[k]), (x, y + 24))
        high, xy, tilt, yaw = [t_[k].item() if t_.dim() == 1 else t_[k].norm().item() for t_ in env._puck_err()]
        good = bool(env.puck_good[k]); col = '#2e9e4f' if good and bool(env.clean[k]) else ('#d93636' if not bool(env.clean[k]) else '#b07000')
        dr.text((x + 4, y + 4), f"{CELLS[cells[k]]} · 높이 {high * 1000:+.0f} mm · 기울기 {tilt:.0f}° · 면 {yaw:+.0f}° · " + ('바름' if good else '틀어짐') +
                ('' if bool(env.clean[k]) else ' · 다른 것에 닿음!'), font=F, fill=col)
    canvas.save(tmp / f'{nf:05d}.png'); nf += 1
rec = env.record
ok = [r for r in rec]
print(f'에피소드 {len(ok)} · 성공 {np.mean([r["success"] for r in ok]):.2f} · 충돌 없이 성공 {np.mean([r["success"] and r["clean"] for r in ok]):.2f} · '
      f'충돌 없음 {np.mean([r["clean"] for r in ok]):.2f} · 평균 스텝 {np.mean([r["steps"] for r in ok]):.0f}', flush=True)
out = HERE / 'logs' / a.mp4
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(tmp / '%05d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', str(out)], check=True)
print('MP4', out, nf)
app.close()
