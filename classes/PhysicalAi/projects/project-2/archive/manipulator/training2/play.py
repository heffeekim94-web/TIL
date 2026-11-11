#!/usr/bin/env python3
"""학습2 평가: 고정 시나리오 (scenarios.py, seed 같으면 팀원과 같은 목록) 로 정책을 돌려 합격 기준을 잰다.

합격 기준 (사용자와 정함 2026-11-10): 충돌 0 번 · 떨어뜨림 0 번 · 여유 거리 (최소 거리) — 찬 칸 11 개 포함.
결과: <체크포인트 폴더>/eval_<시각>.json (+ --gif 면 env 0 영상)

예) $PY play.py --checkpoint logs/<실행>/model_3000.pt --episodes 1000
    $PY play.py --checkpoint logs/<실행>/model_3000.pt --episodes 8 --num_envs 1 --gif
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--checkpoint', required=True)
p.add_argument('--episodes', type=int, default=1000)
p.add_argument('--num_envs', type=int, default=64)
p.add_argument('--seed', type=int, default=0, help='시나리오 목록 seed (팀원과 같게)')
p.add_argument('--gif', action='store_true')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
a.enable_cameras = a.gif
app = AppLauncher(a).app

sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

import scenarios  # noqa: E402
from cfg import EnvCfg, TrainCfg  # noqa: E402
from env import Training2Env  # noqa: E402

cfg = EnvCfg()
cfg.scene.num_envs = a.num_envs
if a.gif:
    import viz
    viz.add_camera(cfg)
raw = Training2Env(cfg)
sc = scenarios.make(a.episodes + a.num_envs, a.seed, n_dice=len(raw.dice))   # 처음 리셋이 env 수만큼 먼저 씀
raw.set_scenarios(sc)
raw.record = []
env = RslRlVecEnvWrapper(raw)
runner = OnPolicyRunner(env, TrainCfg().runner_dict(), None, env.device)
runner.load(a.checkpoint)
policy = runner.get_inference_policy(device=env.device)
if a.gif:
    viz.aim(raw)

obs = env.get_observations()
frames, t0 = [], time.time()
with torch.inference_mode():
    while len(raw.record) < a.episodes:
        obs, _, _, _ = env.step(policy(obs))
        if a.gif and len(frames) < 1800 and raw.common_step_counter % 2 == 0:
            frames.append(viz.frame(raw))
rec = raw.record[:a.episodes]
n = len(rec)
summary = {
    'checkpoint': a.checkpoint, 'episodes': n, 'scenario_seed': a.seed,
    'success': sum(r['success'] for r in rec) / n,
    'collision_free': sum(r['collision_free'] for r in rec) / n,
    'collision_episodes': sum(not r['collision_free'] for r in rec),
    'drops': sum(r['drop'] for r in rec),
    'min_clearance_mm_p01': float(np.percentile([r['min_clearance_mm'] for r in rec], 1)),
    'by_occupied': {k: {'n': v, 'success': sum(r['success'] for r in rec if len(r['stored']) == k) / v}
                    for k, v in sorted(Counter(len(r['stored']) for r in rec).items())},
    'pass': all(r['collision_free'] for r in rec) and not any(r['drop'] for r in rec),
}
out = Path(a.checkpoint).resolve().parent / f'eval_{time.strftime("%Y%m%d_%H%M%S")}'
out.with_suffix('.json').write_text(json.dumps({'summary': summary, 'episodes': rec}, ensure_ascii=False, indent=1))
print(json.dumps(summary, ensure_ascii=False, indent=1))
print(f'[play] {n} 에피소드 {time.time() - t0:.0f} s → {out}.json', flush=True)
if a.gif and frames:
    from PIL import Image
    ims = [Image.fromarray(f) for f in frames]
    ims[0].save(str(out.with_suffix('.gif')), save_all=True, append_images=ims[1:], duration=66, loop=0)
    print(f'[play] {out}.gif', flush=True)
app.close()
