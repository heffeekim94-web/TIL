#!/usr/bin/env python3
"""학습2 PPO 학습 (rsl_rl, 팀 sim/robot_sim/rl/train.py 와 같은 형식). 결과: training2/logs/<시각>_<이름>/

예) cd archive/manipulator/training2
    PY="env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMNI_KIT_ACCEPT_EULA=YES $HOME/pa-course/IsaacLab-6.2/.venv/bin/python"
    $PY train.py --run_name t1                          # 기본 env 256, 3000 iter
    $PY train.py --num_envs 64 --max_iterations 20 --run_name smoke
    $PY train.py --resume logs/<실행>/model_1000.pt --run_name t1b
    $PY train.py --res --run_name r1                     # 보정 학습 (먼저 python3 library.py 로 logs/library.npz)
tmux 로 돌릴 때는 run_tmux.sh.
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--num_envs', type=int, default=None, help='기본 = cfg.py (256)')
p.add_argument('--max_iterations', type=int, default=None, help='기본 = cfg.py TrainCfg (3000)')
p.add_argument('--seed', type=int, default=1)
p.add_argument('--run_name', default='')
p.add_argument('--resume', default='', help='이어 학습할 model_*.pt')
p.add_argument('--res', action='store_true', help='보정 학습 (env_res: 혁무님 방식 기본 경로 + 보정, logs/library.npz 필요)')
p.add_argument('--library', default='logs/library_chain.npz')
p.add_argument('--set', nargs='*', default=[], help='설정 덮어쓰기 sec.key=값 (예: reward.near=-0.5 task.occupied_max_start=11)')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
app = AppLauncher(a).app

sys.path.insert(0, str(HERE))
import torch  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from cfg import EnvCfg, TrainCfg  # noqa: E402
from env import Training2Env  # noqa: E402

if a.res:
    from env_res import ResEnvCfg, Training2ResEnv  # noqa: E402
cfg, tc = (ResEnvCfg() if a.res else EnvCfg()), TrainCfg()
if a.res:
    cfg.library = a.library
    tc.experiment_name = 'training2_res'
if a.num_envs is not None:
    cfg.scene.num_envs = a.num_envs
cfg.seed = a.seed
for kv in a.set:                                       # 비교 실험용 (cfg.json 에 그대로 남음)
    key, val = kv.split('=', 1)
    sec, k = key.split('.', 1)
    obj = getattr(cfg, sec)
    old = getattr(obj, k)
    setattr(obj, k, (val.lower() == 'true') if isinstance(old, bool) else type(old)(val))
    print(f'[train] {key} = {getattr(obj, k)} (기본 {old})')
if a.max_iterations is not None:
    tc.max_iterations = a.max_iterations
tc.run_name = a.run_name
torch.manual_seed(a.seed)

log_dir = HERE / 'logs' / (time.strftime('%Y%m%d_%H%M%S') + (f'_{a.run_name}' if a.run_name else ''))
log_dir.mkdir(parents=True, exist_ok=True)
(log_dir / 'cfg.json').write_text(json.dumps({'num_envs': cfg.scene.num_envs, 'seed': a.seed, 'task': cfg.task.to_dict(),
                                              'reward': cfg.reward.to_dict(), 'train': asdict(tc),
                                              'max_joint_speed': cfg.max_joint_speed, 'point_spacing': cfg.point_spacing},
                                             indent=1, ensure_ascii=False))

env = RslRlVecEnvWrapper(Training2ResEnv(cfg) if a.res else Training2Env(cfg))
runner = OnPolicyRunner(env, tc.runner_dict(), str(log_dir), env.device)
if a.resume:
    runner.load(a.resume)
print(f'[train] env {cfg.scene.num_envs}, iter {tc.max_iterations} → {log_dir}', flush=True)
runner.learn(tc.max_iterations)
runner.save(str(log_dir / f'model_{tc.max_iterations}.pt'))
print(f'[train] 끝 → {log_dir}', flush=True)
app.close()
