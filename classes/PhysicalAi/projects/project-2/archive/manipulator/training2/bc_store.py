#!/usr/bin/env python3
"""1번 적재 모델 B단계 ①: 혁무님 동작 따라 하기 (모방). 전문가 = env_store.expert_action (라이브러리 경로 따라가기).
  1) 전문가 행동 + 작은 잡음으로 돌리며 (관측, 전문가 행동) 모음 — 잡음이 있어야 벗어났을 때 돌아오는 법도 배움
  2) 정책 (rsl_rl actor, 평균 출력) 을 지도 학습 → logs/<시각>_<이름>/model_0.pt (train.py --store --resume 으로 이어서 강화학습)
  3) 전문가 그대로 · 모방 정책 성공률 비교
  $PY bc_store.py --run_name s1bc --rollouts 2 --epochs 30
"""
import argparse
import json
import sys
import time
from pathlib import Path

from isaaclab.app import AppLauncher

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--run_name', default='s1bc')
p.add_argument('--num_envs', type=int, default=128)
p.add_argument('--rollouts', type=int, default=2, help='모을 에피소드 묶음 수 (env 수 × 이만큼)')
p.add_argument('--noise', type=float, default=0.15)
p.add_argument('--epochs', type=int, default=30)
p.add_argument('--every', type=int, default=2, help='몇 스텝마다 저장')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
app = AppLauncher(a).app
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import torch  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from cfg import TrainCfg  # noqa: E402
from env_store import StoreEnvCfg, Training2StoreEnv  # noqa: E402

cfg = StoreEnvCfg(); cfg.scene.num_envs = a.num_envs
env = Training2StoreEnv(cfg)
env.record = []
wenv = RslRlVecEnvWrapper(env)
log_dir = HERE / 'logs' / (time.strftime('%Y%m%d_%H%M%S') + f'_{a.run_name}')
log_dir.mkdir(parents=True, exist_ok=True)
tc = TrainCfg(); tc.experiment_name = 'training2_store'; tc.run_name = a.run_name
R = tc.runner_dict(); R['actor']['distribution_cfg']['init_std'] = 0.1
runner = OnPolicyRunner(wenv, R, str(log_dir), env.device)
actor = runner.alg.actor
N, dev = a.num_envs, env.device


def stats(rec):
    if not rec:
        return '기록 없음'
    return (f"에피소드 {len(rec)} · 퍽 끝냄 {np.mean([r.get('done_frac', 0) for r in rec]):.2f} · 충돌 없음 {np.mean([r['collision_free'] for r in rec]):.2f} · "
            f"성공 {np.mean([r['success'] for r in rec]):.2f} · 떨어뜨림 {np.mean([r['drop'] for r in rec]):.2f}")


def rollout(policy_fn, n_ep, collect=False):
    """env 마다 n_ep 에피소드 (끝난 env 는 계속 돌지만 기록은 처음 n_ep 개만)."""
    env.record = []
    obs = wenv.get_observations()
    O, A = [], []
    count = torch.zeros(N, dtype=torch.long, device=dev); it = 0
    while int(count.min()) < n_ep:
        with torch.no_grad():
            ae = env.expert_action()
            act = policy_fn(obs, ae)
        if collect and it % a.every == 0:
            O.append(obs['policy'].clone()); A.append(ae.clone())
        obs, _, dones, _ = wenv.step(act)
        count += dones.long(); it += 1
    return O, A


t0 = time.time()
print('[bc] 1) 전문가 + 잡음으로 모으기', flush=True)
def noisy(o, ae):
    nz = a.noise * torch.randn_like(ae); nz[:, 5] = 0          # 그리퍼는 잡음 없이 (s1bc: 그리퍼 잡음 → 떨어뜨림 26 %)
    return (ae + nz).clamp(-1, 1)
O, A = rollout(noisy, a.rollouts, collect=True)
print(f'[bc]   전문가(+잡음) {stats(env.record)} · 표본 {sum(len(x) for x in O) * 1} · {time.time() - t0:.0f} s', flush=True)
Ob = torch.cat(O); Ab = torch.cat(A)
print('[bc] 2) 지도 학습', Ob.shape, flush=True)
from tensordict import TensorDict  # noqa: E402
actor.train()
actor.update_normalization(TensorDict({'policy': Ob, 'critic': torch.zeros(len(Ob), 1, device=dev)}, batch_size=[len(Ob)]))
opt = torch.optim.Adam(actor.parameters(), lr=1e-3)
B = 4096
for ep in range(a.epochs):
    perm = torch.randperm(len(Ob), device=dev); tot = 0.0
    for i in range(0, len(Ob), B):
        j = perm[i:i + B]
        td = TensorDict({'policy': Ob[j]}, batch_size=[len(j)])
        out = actor(td)
        loss = (out - Ab[j]).square().mean()
        opt.zero_grad(); loss.backward(); opt.step(); tot += float(loss) * len(j)
    if ep % 5 == 0 or ep == a.epochs - 1:
        print(f'[bc]   epoch {ep} loss {tot / len(Ob):.4f}', flush=True)
actor.eval()
runner.save(str(log_dir / 'model_0.pt'))
print('[bc] 3) 모방 정책 평가', flush=True)
_ = rollout(lambda o, ae: actor(o).clamp(-1, 1), 1)
print(f'[bc]   모방 정책 {stats(env.record)}', flush=True)
(log_dir / 'cfg.json').write_text(json.dumps(vars(a) | {'library': cfg.library}, indent=1, ensure_ascii=False, default=str))
print(f'[bc] 끝 → {log_dir} · {time.time() - t0:.0f} s', flush=True)
app.close()
