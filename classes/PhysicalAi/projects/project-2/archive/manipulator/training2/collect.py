"""여러 스테이션을 돌며 퍽을 모아 적재함 12 칸을 채우는 시나리오 · 경로 계획 (시뮬 없이 계획만, 실행은 demo11).
시나리오: 적재함 k 칸이 무작위로 이미 참 (사각 · 원기둥 섞임) → 나머지 12 − k 개가 스테이션 (팀 planning collect_order 순서) 에 2–3 개씩
          무작위 자리 (가장자리 · 가운데 · 먼 모서리) · 방향, 선 사각 · 원기둥 · 누운 사각.
경로: 스테이션마다 받침에서 일어섬 → 가까운 퍽부터 집어 (자세별 방법) 혁무님 순서 첫 빈 칸에 넣음 → HOME 안 들르고 다음 퍽 → 스테이션 끝나면 HOME (주행)."""
import numpy as np
import yaml

import pathgen as pg
import store2 as s2

COLLECT_ORDER = [1, 2, 4, 5, 6, 3]           # config/planning.yaml collect_order
MAP = yaml.safe_load(open(pg.sag.TEAM / 'maps/dice_map.yaml'))
HALF = 0.1025                                 # 박스 반 변


def footprint(p):
    """퍽 바닥 자국 반지름 (겹침 · 손가락 여유 근사)."""
    return 0.033 if p['kind'] == 'lying' else 0.021


def random_station(rng, n, tries=400):
    """박스 위 퍽 n 개. kind: up (선 사각) · cyl (선 원기둥) · lying (누운 사각). 좌표 base_link."""
    out = []
    kinds = list(rng.choice(['up', 'cyl', 'lying'], n, p=[0.4, 0.3, 0.3]))
    for kind in kinds:
        for _ in range(tries):
            m = HALF - (0.034 if kind == 'lying' else 0.022)
            x, y = pg.BOX_X + rng.uniform(-m, m), rng.uniform(-m, m)
            p = dict(kind=kind, xy=np.array([x, y]), yaw=rng.uniform(-np.pi / 2, np.pi / 2))
            if all(np.linalg.norm(p['xy'] - o['xy']) > footprint(p) + footprint(o) + 0.006 for o in out):
                out.append(p)
                break
        else:
            return None
    return out


def obstacle_pts(p):
    if p['kind'] == 'lying':
        a = np.array([np.cos(p['yaw']), np.sin(p['yaw'])])
        return [tuple(p['xy'] + s * 0.015 * a) for s in (-1, 0, 1)]
    return [tuple(p['xy'])]


def make_scenario(seed, k_prefill):
    rng = np.random.default_rng(seed)
    order = pg.cargo_order()
    pre = list(rng.choice(pg.cargo_order(), k_prefill, replace=False))
    pre_shape = {c: ('cyl' if rng.random() < 0.4 else 'box') for c in pre}
    n_left = 12 - k_prefill
    sizes = []
    while n_left > 0:                                  # 2–3 개씩 (마지막이 1 이 되지 않게)
        s = 3 if n_left in (3, 5) or (n_left > 3 and rng.random() < 0.5) else 2
        s = min(s, n_left)
        sizes.append(s); n_left -= s
    stations = []
    for j, n in enumerate(sizes):
        while True:
            st = random_station(rng, n)
            if st is not None:
                break
        stations.append(dict(box=f'B{COLLECT_ORDER[j]}', pucks=st))
    return dict(prefill=pre, pre_shape=pre_shape, stations=stations, seed=seed)


def plan(sc, measure=None):
    """경로 생성기: (Q, G, N, events) 조각을 차례로 내놓고, 칸 위 확인 뒤에는 measure 값을 send 로 받음.
    events: [('station', j)] · [('activate', j, i, cell)] · [('stored', cell)] · [('home',)]"""
    order = pg.cargo_order()
    occupied = list(sc['prefill'])
    q = None
    for j, st in enumerate(sc['stations']):
        uq, un = pg.team_unfold()
        Q = np.array([pg.to_cmd(x) for x in uq])
        yield Q, ['-'] * len(Q), un, [('station', j)]
        q = uq[-1]
        left = list(range(len(st['pucks'])))
        while left:
            # 가까운 퍽부터 (J1 에서)
            i = min(left, key=lambda m: np.linalg.norm(st['pucks'][m]['xy'] - pg.J1XY))
            left.remove(i)
            p = st['pucks'][i]
            cell = pg.store_cell(occupied)
            others = [pt for m in left for pt in obstacle_pts(st['pucks'][m])]
            P = s2.Path(q)
            if p['kind'] == 'lying':
                depth, how = s2.pick_lying(P, p['xy'], p['yaw'], others)
            else:
                depth, how = s2.pick_upright(P, p['xy'], p['yaw'], others, cyl=(p['kind'] == 'cyl'))
            p['how'] = how
            c_ins = s2.to_rack_check(P, cell, occupied)
            Q, G, N = P.out()
            meas = yield Q, G, N, [('activate', j, i, cell)]
            q = P.q[-1]
            off, dyaw = (meas if meas is not None else ((0.0, 0.0), 0.0))
            P = s2.Path(q)
            s2.insert(P, cell, c_ins, depth, ins_offset=off, ins_dyaw=dyaw)
            Q, G, N = P.out()
            yield Q, G, N, [('stored', cell)]
            q = P.q[-1]
            occupied.append(cell)
        hq, hg, hn = pg.go_home(q)
        Q = np.array([pg.to_cmd(x) for x in hq])
        Q, G, N, _ = pg.dense_all(Q, hg, hn)
        yield Q, G, N, [('home',)]


def check(sc):
    """시뮬 없이 끝까지 계획되는지 (보정 0)."""
    g = plan(sc)
    n, item = 0, next(g)
    try:
        while True:
            n += len(item[0])
            item = g.send(None)
    except StopIteration:
        return n


if __name__ == '__main__':
    import sys, time, collections
    why = collections.Counter()
    ok = 0
    for seed in range(int(sys.argv[1]) if len(sys.argv) > 1 else 20):
        sc = make_scenario(seed, 6)
        t = time.time()
        try:
            n = check(sc); ok += 1
            print(seed, 'OK', n, round(time.time() - t, 1), 's', [[(p['kind'], p.get('how', '')[:14]) for p in s['pucks']] for s in sc['stations']], flush=True)
        except RuntimeError as e:
            why[str(e).split(':')[-1].strip()[:40]] += 1
            print(seed, 'FAIL', e, flush=True)
    print('ok', ok, dict(why))
