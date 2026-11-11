"""기본 경로 라이브러리: 학습 에피소드마다 쓸 '퍽 하나' 작업과 그 기본 경로 (pathgen · store2, 혁무님 방식) 를 미리 계산해 저장.
학습 중에는 IK 를 안 풂 (경로 하나 1–3 s) → env_res 가 이 파일에서 골라 씀. 강화학습은 이 경로에 보정만 더함.

  python library.py --n 3000 --out logs/library_chain.npz      (CPU 여러 개로 나눠 계산, 약 5–10 분)

작업 (에피소드 = HOME 에서 시작해 HOME 으로 끝남):
  store    : 적재함 무작위로 k 칸 참 (사각 · 원기둥) · 스테이션 1 곳 퍽 2–3 개 (선 사각 · 원기둥 · 누운 사각) 를 가까운 것부터
             혁무님 순서 빈 칸에 차례로 넣음. 퍽 사이 HOME 안 감 (사용자 규칙), 마지막에만 HOME
  retrieve : 주사위 눈 n 개만큼 마지막에 넣은 칸부터 꺼내 먼 눈부터 놓음. 놓고 바로 다음 칸, 마지막에만 HOME
  jobs     : 퍽마다 [시작 경유점 · 칸 · (store) 스테이션 퍽 번호 · (retrieve) 놓을 자리] — env_res 가 그 경유점에서 작업 퍽을 바꿈
좌표: 퍽 · 칸 xy = base_link (시뮬 env 원점 기준 xy 와 같음)."""
import argparse
import multiprocessing as mp
import time

import numpy as np

import collect
import pathgen as pg
import store2 as s2

GRIP_OPEN, GRIP_CLOSE = 0.0187, 0.0007          # cfg.GRIPPER_OPEN · CLOSE (시뮬 값)


def grip_values(G):
    out, g = [], GRIP_CLOSE
    for ev in G:
        if ev.startswith('release'):
            g = float(ev.split(':')[1]) if ':' in ev else GRIP_OPEN
        elif ev == 'close':
            g = GRIP_CLOSE
        out.append(g)
    return np.array(out, np.float32)


def gen_store(rng):
    """스테이션 1 곳: 퍽 2–3 개를 가까운 것부터 차례로 혁무님 순서 빈 칸에 넣음. 퍽 사이 HOME 안 감, 마지막에만 HOME."""
    order = pg.cargo_order()
    n_st = int(rng.integers(2, 4))
    st = None
    while st is None:
        st = collect.random_station(rng, n_st)
    k = int(rng.integers(0, 12 - n_st + 1))
    pre = [str(c) for c in rng.choice(order, k, replace=False)]
    pre_shape = ['cyl' if rng.random() < 0.4 else 'box' for _ in pre]
    uq, un = pg.team_unfold()
    Q, G, N = [pg.to_cmd(x) for x in uq], ['-'] * len(uq), list(un)
    q = uq[-1]
    occupied = list(pre)
    left = list(range(n_st))
    jobs = []
    while left:
        i = min(left, key=lambda m: np.linalg.norm(st[m]['xy'] - pg.J1XY))
        left.remove(i)
        p = st[i]
        cell = next(c for c in order if c not in occupied)
        others = [pt for m in left for pt in collect.obstacle_pts(st[m])]
        P = s2.Path(q)
        if p['kind'] == 'lying':
            depth, how = s2.pick_lying(P, p['xy'], p['yaw'], others)
        else:
            depth, how = s2.pick_upright(P, p['xy'], p['yaw'], others, cyl=(p['kind'] == 'cyl'))
        c_ins = s2.to_rack_check(P, cell, occupied)
        s2.insert(P, cell, c_ins, depth)
        q = P.q[-1]
        Qp, Gp, Np = P.out()
        jobs.append(dict(start=len(Q), puck=i, cell=str(cell), how=how))
        Q += list(Qp); G += Gp; N += Np
        occupied.append(cell)
    hq, hg, hn = pg.go_home(q)
    Qh, Gh, Nh, _ = pg.dense_all(np.array([pg.to_cmd(x) for x in hq]), hg, hn)
    Q += list(Qh); G += Gh; N += Nh
    pucks = [(m_['kind'], float(m_['xy'][0]), float(m_['xy'][1]), float(m_['yaw'])) for m_ in st]
    return dict(task='store', prefill=pre, pre_shape=pre_shape, station=pucks, jobs=jobs), np.array(Q), G, N


def gen_retrieve(rng):
    """주사위 눈 n 개: 마지막에 넣은 칸부터 (혁무님 순서 역순) 꺼내 먼 눈부터 놓음. 놓은 뒤 바로 다음 칸, 마지막에만 HOME."""
    order = pg.cargo_order()
    pips = int(rng.integers(1, 7))
    n = int(rng.integers(pips, 13))
    filled = [str(c) for c in rng.choice(order, n, replace=False)]
    cells = sorted(filled, key=order.index, reverse=True)[:pips]
    Q, G, N, segs = pg.dice_sequence(cells, filled, pips)
    pre_shape = ['cyl' if rng.random() < 0.4 else 'box' for _ in filled]
    jobs = [dict(start=int(st_), cell=str(c), target=[float(xy[0]), float(xy[1])]) for st_, c, xy in segs]
    return dict(task='retrieve', prefill=filled, pre_shape=pre_shape, pips=pips, jobs=jobs), Q, G, N


def one(seed):
    rng = np.random.default_rng(seed)
    task = 'store' if rng.random() < 0.5 else 'retrieve'
    try:
        meta, Q, G, N = (gen_store if task == 'store' else gen_retrieve)(rng)
    except RuntimeError as e:
        return seed, None, str(e)
    meta['seed'] = seed
    return seed, (meta, Q.astype(np.float32), grip_values(G), N), None


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=3000)
    ap.add_argument('--seed0', type=int, default=0)
    ap.add_argument('--procs', type=int, default=max(1, mp.cpu_count() - 4))
    ap.add_argument('--out', default='logs/library_chain.npz')
    a = ap.parse_args()
    t0 = time.time()
    ok, fails = [], {}
    with mp.Pool(a.procs) as pool:
        for k, (seed, res, why) in enumerate(pool.imap_unordered(one, range(a.seed0, a.seed0 + a.n), chunksize=4)):
            if res is None:
                key = why.split(':')[-1].strip()[:30]; fails[key] = fails.get(key, 0) + 1
            else:
                ok.append(res)
            if (k + 1) % 200 == 0:
                print(f'{k + 1}/{a.n} 성공 {len(ok)} · {time.time() - t0:.0f} s', flush=True)
    L = max(len(r[1]) for r in ok)
    Q = np.zeros((len(ok), L, 5), np.float32); G = np.zeros((len(ok), L), np.float32); n = np.zeros(len(ok), np.int32)
    for i, (meta, q, g, _) in enumerate(ok):
        n[i] = len(q); Q[i, :len(q)] = q; Q[i, len(q):] = q[-1]; G[i, :len(g)] = g; G[i, len(g):] = g[-1]
    import json
    np.savez_compressed(a.out, Q=Q, G=G, n=n, meta=np.array([json.dumps(r[0], ensure_ascii=False) for r in ok]))
    tasks = [r[0]['task'] for r in ok]
    print(f'저장 {a.out}: {len(ok)} 개 (store {tasks.count("store")} · retrieve {tasks.count("retrieve")}) · 최대 경유점 {L} · '
          f'평균 {n.mean():.0f} · 실패 {sum(fails.values())} {fails} · {time.time() - t0:.0f} s')
