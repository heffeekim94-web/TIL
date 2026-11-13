#!/usr/bin/env python3
"""스테이션 집기 확인: 장면 (--checkpoint 없으면 행동 0 = 시작 자세 그대로) · 정책 동영상 · 성공 통계.
  $PY check_pick.py --n 6 --steps 30 --gif pick_scene.gif                     # 장면만
  $PY check_pick.py --checkpoint logs/<실행>/model_100.pt --n 4 --episodes 4 --mp4 pick_100.mp4
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--checkpoint', default='')
p.add_argument('--n', type=int, default=6)
p.add_argument('--steps', type=int, default=30, help='장면만 볼 때 스텝 수')
p.add_argument('--episodes', type=int, default=3)
p.add_argument('--gif', default='')
p.add_argument('--mp4', default='')
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

from env_pick import PickEnvCfg, Training2PickEnv  # noqa: E402
import viz  # noqa: E402

torch.manual_seed(a.seed)
cfg = PickEnvCfg(); cfg.scene.num_envs = a.n
viz.add_camera(cfg, height=300, width=400)
env = Training2PickEnv(cfg)
env.record = []
bank = np.load(HERE / cfg.bank)
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
    env.no_terminate = True
    env.reset()
cam = env.scene['viz_cam']
o = env.scene.env_origins.cpu().numpy()
tg = o + np.r_[0.20, 0.0, 0.08]
cam.set_world_poses_from_view(eyes=(tg + np.r_[0.12, -0.42, 0.26]).astype(np.float32), targets=tg.astype(np.float32))
F = ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf', 14)
SH = ['선 네모', '원기둥', '누운 네모']
tmp = Path(tempfile.mkdtemp()); frames = []
count = np.zeros(a.n, int); it = 0
while (count.min() < a.episodes) if policy is not None else (it < a.steps):
    with torch.inference_mode():
        if policy is not None:
            obs, _, dones, _ = wenv.step(policy(obs))
            count += dones.cpu().numpy().astype(int)
        else:
            act = torch.zeros(a.n, 6, device=env.device); act[:, 5] = 1.0
            env.step(act)
    it += 1
    rgb = cam.data.output['rgb'].torch.cpu().numpy()[..., :3].astype(np.uint8)
    W, H, cols = 400, 300, 3 if a.n > 4 else 2
    rows = (a.n + cols - 1) // cols
    canvas = Image.new('RGB', (cols * (W + 6), rows * (H + 42)), 'white'); dr = ImageDraw.Draw(canvas)
    for k in range(a.n):
        x, y = (k % cols) * (W + 6), (k // cols) * (H + 42)
        canvas.paste(Image.fromarray(rgb[k]), (x, y + 40))
        b = int(env.bi[k]); lf = float(env.wheel_lift[k]); tl = float(env.body_tilt[k])
        col = '#d93636' if lf > 1.0 or not bool(env.clean[k]) else '#2e9e4f'
        dr.text((x + 4, y + 3), f"박스 {np.degrees(bank['psi'][b]):+.0f}° · 틈 {bank['gap'][b] * 100:.0f} cm · {SH[int(bank['pucks'][b, 0, 3])]} · 손 {int(bank['tilt'][b])}°", font=F, fill='#222')
        dr.text((x + 4, y + 21), f"바퀴 뜸 {lf:.1f} mm · 기울기 {tl:.2f}° · " + ('쥠' if bool(env.grasped[k]) else '') + ('' if bool(env.clean[k]) else ' 충돌!'), font=F, fill=col)
    frames.append(canvas)
if env.record:
    R = env.record
    print(f'에피소드 {len(R)} · 성공 {np.mean([r["success"] for r in R]):.2f} · 충돌 없이 성공 {np.mean([r["success"] and r["clean"] for r in R]):.2f} · '
          f'쥠 {np.mean([r["grasped"] for r in R]):.2f} · 바퀴 뜸 실패 {np.mean([r["lifted"] for r in R]):.2f} · 밀어냄 {np.mean([r["knock"] for r in R]):.2f} · '
          f'평균 스텝 {np.mean([r["steps"] for r in R]):.0f}', flush=True)
else:
    print('장면', [int(b) for b in env.bi.tolist()], '바퀴 뜸 mm', np.round(env.wheel_lift.cpu().numpy(), 2).tolist(),
          '기울기°', np.round(env.body_tilt.cpu().numpy(), 2).tolist(), '충돌 없음', env.clean.cpu().numpy().tolist(), flush=True)
if a.mp4:
    for i, f in enumerate(frames):
        f.save(tmp / f'{i:05d}.png')
    out = HERE / 'logs' / a.mp4
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(tmp / '%05d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', str(out)], check=True)
    print('MP4', out, len(frames))
if a.gif:
    out = HERE / 'logs' / a.gif
    fr = frames[::2]
    fr[0].save(out, save_all=True, append_images=fr[1:] + [fr[-1]] * 8, duration=80, loop=0)
    print('GIF', out, len(fr))
app.close()
