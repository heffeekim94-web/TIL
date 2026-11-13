#!/usr/bin/env python3
"""툭 건드리기 정책 체크포인트 → 팀 배포 형식 (sim/robot_sim/rl/tasks/local_planner/export.py 와 같음):
  <out>/policy.pt  (TorchScript, 관측 정규화 포함)
  <out>/policy.npz (numpy 만으로 돎 = Jetson: 정규화 mean · std · eps + 선형 층 W · b, ELU, 마지막 층 = 평균 행동)
  <out>/cfg.json   (학습 설정 + 관측 · 행동 설명)
  $PY export_nudge.py logs/<실행>/model_199.pt export/nudge_n1b
"""
import json
import shutil
import sys
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
app = AppLauncher(headless=True).app
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from cfg import TrainCfg  # noqa: E402
from env_nudge import NudgeEnvCfg, Training2NudgeEnv  # noqa: E402

ck, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
if not out.is_absolute():
    out = HERE / out
out.mkdir(parents=True, exist_ok=True)
cfg = NudgeEnvCfg(); cfg.scene.num_envs = 4
env = Training2NudgeEnv(cfg)
wenv = RslRlVecEnvWrapper(env)
runner = OnPolicyRunner(wenv, TrainCfg().runner_dict(), None, env.device)
runner.load(str(ck))
runner.export_policy_to_jit(str(out), 'policy.pt')
pol = torch.jit.load(str(out / 'policy.pt'), map_location='cpu')
obs = wenv.get_observations()
o = obs['policy'][:1].cpu()
ref = runner.get_inference_policy(env.device)(obs)[:1].cpu()
print(f'TorchScript 입력 {o.shape[1]} · 출력 차이 {float((pol(o) - ref).abs().max()):.2e}')
sd = {k: v.cpu().numpy() for k, v in pol.state_dict().items()}
layers = sorted({int(k.split('.')[1]) for k in sd if k.startswith('mlp.') and k.endswith('.weight')})
np.savez(out / 'policy.npz', mean=sd['obs_normalizer._mean'][0], std=sd['obs_normalizer._std'][0], eps=np.float32(pol.obs_normalizer.eps),
         n_layers=np.int32(len(layers)), activation=np.array('elu'),
         **{f'W{i}': sd[f'mlp.{l}.weight'] for i, l in enumerate(layers)}, **{f'b{i}': sd[f'mlp.{l}.bias'] for i, l in enumerate(layers)})
# numpy 로 같은 계산 (팀 deploy/numpy_policy.py 와 같은 식) → torch 와 비교
z = np.load(out / 'policy.npz')
def np_policy(x):
    h = (x - z['mean']) / (z['std'] + z['eps'])
    for i in range(int(z['n_layers'])):
        h = h @ z[f'W{i}'].T + z[f'b{i}']
        if i < int(z['n_layers']) - 1:
            h = np.where(h > 0, h, np.expm1(h))
    return h
x = obs['policy'][:4].cpu()
d = float(np.abs(np_policy(x.numpy()) - pol(x).detach().numpy()).max())
print(f'npz 층 {len(layers)} · torch 대비 최대 차이 {d:.2e}')
saved = json.loads((ck.parent / 'cfg.json').read_text()) if (ck.parent / 'cfg.json').exists() else {}
saved.update(checkpoint=str(ck), obs_dim=int(o.shape[1]), act_dim=int(ref.shape[1]), episode_length_s=cfg.episode_length_s,
             max_joint_speed=cfg.max_joint_speed, policy_hz=30, npz_vs_torch_max_diff=d)
(out / 'cfg.json').write_text(json.dumps(saved, indent=1, ensure_ascii=False))
print('→', out)
app.close()
