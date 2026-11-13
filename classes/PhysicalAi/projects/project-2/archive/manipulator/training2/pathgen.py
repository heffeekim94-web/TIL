"""빼기 경로 만들기 (팀 팔 모델 IK): 받침 → 일어서기 (팀 unfold 그대로) → 높이 유지하며 대상 칸 위 → 멈춰 확인 → 수직 내림 →
더 깊게 쥐기 → 수직 들기 → 높이 유지하며 박스 쪽. 손가락 닫힘 축 = 옆 칸 퍽이 없는 쪽 (grasp_select 생각), 180° 두 후보 중 J5 덜 돌리는 쪽.
돌려주는 q 는 팀 관절 값 '실제 자세' (처짐 없음) → 시뮬에 그대로."""
import numpy as np
import yaml
from scipy.optimize import least_squares

import sag

sm = sag.SagModel()
AM = yaml.safe_load(open(sag.TEAM / 'config/arm_kinematics.yaml'))['/**']['ros__parameters']['arm_model']
APP5, CLOSE5 = np.array(AM['app5']), np.array(AM['close5'])
P = yaml.safe_load(open(sag.TEAM / 'config/arm_paths.yaml'))['control_master']['ros__parameters']['arm_paths']
RC = yaml.safe_load(open(sag.TEAM / 'config/rack_cells.yaml'))['rack_cells']
CELLS = RC['cells']
ZB = 0.072 - 0.034                    # 모델 base z (바닥 위 0.072) → base_link (바닥 위 0.034)
TOP = RC['floor_z'] + 0.060           # 선 퍽 윗면 (base_link)
LO, HI = np.array([-3.14, -1.5, -1.5, -1.7, -1.5708]), np.array([3.14, 1.5, 1.4, 0.6735, 1.5708])   # 시뮬 USD 관절 범위


def grip(qm):
    F = sm.frames(qm)[4]
    return F[:3, :3] @ sm.tip5 + F[:3, 3] + [0, 0, ZB], F[:3, :3] @ APP5, F[:3, :3] @ CLOSE5


def to_qm(cmd):
    return sm.ticks_to_q(sm.cmd_to_ticks(cmd))


def to_cmd(qm):
    return sm.ticks_to_cmd(sm.q_to_ticks(qm))


def _model_bounds():
    """시뮬 관절 범위 (팀 관절 값) → 모델 관절 값. 바퀴 수 보정 없이 직선 변환, J1 은 경계 없음."""
    lin = lambda c: sm.q_ref + sm.sign * (sag.ZERO_TICK + np.asarray(c) / sag.T2R - sm.ref_tick) * sag.T2R
    a, b = lin(LO), lin(HI)
    lo, hi = np.minimum(a, b) + 1e-4, np.maximum(a, b) - 1e-4
    lo[0], hi[0] = -np.inf, np.inf
    return lo, hi


def ik(p, a, c, seed, w_c=2.0, w_lim=50.0, w_a=3.0, w_reg=0.05):
    """팀 팔 모델 IK: 손끝 p · 접근 a · 닫힘 c. 관절 범위는 경계로, 앞 자세(seed) 근처에 머물게 작은 끌림."""
    lo, hi = _model_bounds()
    s0 = np.clip(seed, lo, hi)
    def r(x):
        tp, ta, tc = grip(x)
        return np.r_[(tp - p) * 200, (ta - a) * w_a, (tc - c) * w_c, (x - s0) * w_reg]
    s = least_squares(r, s0, bounds=(lo, hi) if w_lim else (-np.inf, np.inf))
    return s.x, np.linalg.norm(grip(s.x)[0] - p)


def choose_close(cell, occupied):
    """닫힘 축 후보 = 칸 면 방향 두 개. 손가락 (닫힘축 ±46 mm, 폭 ±16 mm) 앞에 찬 이웃이 적은 쪽, 같으면 이웃까지 먼 쪽."""
    c = np.array(CELLS[cell]['xy']); yaw = np.radians(CELLS[cell]['yaw_deg'])
    best = None
    for ang in (yaw, yaw + np.pi / 2):
        ax = np.array([np.cos(ang), np.sin(ang)]); lat = np.array([-ax[1], ax[0]])
        hits, near = 0, 1.0
        for n in occupied:
            d = np.array(CELLS[n]['xy']) - c
            along, side = abs(d @ ax), abs(d @ lat)
            if side < 0.035:
                near = min(near, along)
                hits += along < 0.065
        key = (hits, -near)
        if best is None or key < best[0]:
            best = (key, ax)
    return np.r_[best[1], 0.0]


J1XY = np.array(AM['j1_xy'])


MAX_DQ = 0.04     # 팀 unfold · fold 경유점 사이 관절 최대 한 걸음 [rad] (시뮬 경유점 0.067 s → 약 0.6 rad/s, 실물 path_stand_speed 62.5°/s 보다 느림)


def dense(qs, names, max_step=MAX_DQ):
    """팀 경유점 사이를 관절 직선으로 잘게 나눔 (한 번에 크게 움직이면 몸체가 흔들려 칸 안 퍽이 튐)."""
    oq, on = [qs[0]], [names[0]]
    for q, nm in zip(qs[1:], names[1:]):
        k = max(1, int(np.ceil(np.abs(q - oq[-1]).max() / max_step)))
        p = oq[-1]
        for t in np.linspace(0, 1, k + 1)[1:]:
            oq.append(p + t * (q - p)); on.append(nm)
    return oq, on


def team_unfold():
    unfold = np.array(P['unfold']['q']).reshape(-1, 5)
    return dense([to_qm(unfold[0])] + [to_qm(sm.true_from_cmd(q)) for q in unfold[1:]], list(P['unfold']['nodes']))


def go_home(q):
    """지금 자세 → 받침 바로 위 P0 (관절 직선) → 팀 fold 경로 (P0 → 받침). 돌려줌 qs, names, grips (P0 에서 닫음)."""
    fold = np.array(P['fold']['q']).reshape(-1, 5)
    q_p0 = to_qm(sm.true_from_cmd(fold[0]))
    qs, names = dense([q, q_p0], ['돌아감', '돌아감'])
    qs, names = qs[1:], names[1:]
    grips = ['-'] * len(qs); grips[-1] = 'close'
    f, fn = dense([q_p0] + [to_qm(sm.true_from_cmd(x)) for x in fold[1:-1]] + [to_qm(fold[-1])], list(P['fold']['nodes']))
    return qs + f[1:], grips + ['-'] * (len(f) - 1), names + fn[1:]


def lerp_path(q0, targets, step, w_a=3.0, polar=False):
    """targets = [(p, a, c), ...] 를 손끝 step [m] 간격 직선으로 나눠 IK (앞 해를 씨앗으로)."""
    out, q = [], q0.copy()
    p_prev, a_prev, c_prev = grip(q)
    for p, a, c in targets:
        n = max(2, int(np.linalg.norm(p - p_prev) / step) + 1, int(np.degrees(np.arccos(np.clip(c @ c_prev, -1, 1))) / 3) + 1)
        if polar:   # 수평 이동은 J1 둘레로 돌아감 (팔 뿌리 바로 위를 지나면 J1 이 갑자기 크게 돎)
            r0, r1 = np.linalg.norm(p_prev[:2] - J1XY), np.linalg.norm(p[:2] - J1XY)
            t0 = np.arctan2(*(p_prev[:2] - J1XY)[::-1]); t1 = np.arctan2(*(p[:2] - J1XY)[::-1])
            dt = (t1 - t0 + np.pi) % (2 * np.pi) - np.pi
            n = max(n, int(abs(dt) * max(r0, r1) / step) + 1)
        for t in np.linspace(0, 1, n)[1:]:
            pp = p_prev + t * (p - p_prev)
            if polar:
                r, th = r0 + t * (r1 - r0), t0 + t * dt
                pp = np.r_[J1XY + r * np.array([np.cos(th), np.sin(th)]), pp[2]]
            aa = a_prev + t * (a - a_prev); aa /= np.linalg.norm(aa)
            cc = c_prev + t * (c - c_prev); cc -= (cc @ aa) * aa; cc /= np.linalg.norm(cc)
            q, err = ik(pp, aa, cc, q, w_a=w_a)
            out.append(q.copy())
        p_prev, a_prev, c_prev = p, a, c
    return out


def retrieve_path(cell, occupied, depth=0.025, safe_z=0.22, look_s=1.0, q_start=None):
    """돌려줌: q (N, 5) 실제 자세 [팀 관절 값], grip 사건 목록 ['-'|'release'|'close'], 노드 이름."""
    if q_start is None:   # HOME 에서: 팀 unfold 로 일어섬
        qs, names = team_unfold()
    else:                 # 바로 앞 놓기에서 이어서 (HOME 안 들름)
        qs, names = [q_start], ['이어서']
    grips = ['-'] * len(qs)
    down = np.array([0, 0, -1.0])
    c_star = choose_close(cell, occupied)
    xy = np.array(CELLS[cell]['xy'])
    p0, a0, c0 = grip(qs[-1])
    # 180° 두 후보 중 J5 덜 돌리는 쪽: 기록 경로의 쥐는 순간 J5 와 가까운 것
    rec = P[f'retrieve_{cell}']; Qr = np.array(rec['q']).reshape(-1, 5)
    j5_rec = sm.true_from_cmd(Qr[max(i for i, e in enumerate(rec['grip']) if e == 'close')])[4]
    above = np.r_[xy, safe_z]
    cands = []
    q_rec = to_qm(sm.true_from_cmd(Qr[max(i for i, g in enumerate(rec['grip']) if g == 'close')]))
    for cs in (c_star, -c_star):
        for d5 in (-np.pi / 2, np.pi / 2, 0.0, np.pi, -np.pi):      # 씨앗 J5 를 여러 개 (한계 없이 풀어 보고 범위 안인지)
            q_t, e = ik(above, down, cs, q_rec + np.r_[0, 0, 0, 0, d5], w_lim=0.0)
            j5 = to_cmd(q_t)[4]
            ok = e < 1e-3 and LO[4] <= j5 <= HI[4]
            cands.append((0 if ok else 1, abs(j5 - j5_rec), cs))
    order = [t[2] for t in sorted(cands, key=lambda t: (t[0], t[1]))]
    order = [order[0]] + [c for c in order[1:] if c @ order[0] < 0][:1]
    # 두 부호 다 실제로 경로를 만들어 보고, 칸 위에서 닫힘축이 맞고 (J5 가 한계에 걸려 못 돌면 안 맞음) 목표에 닿는 첫 번째를 씀
    base_q, base_n = list(qs), list(names)
    for c_try in order:
        qs, names = list(base_q), list(base_n)
        for p, a, c, nm in ((np.r_[p0[:2], safe_z], down, c0, '일어섬'), (above, down, c_try, '칸 위')):
            new = lerp_path(qs[-1], [(p, a, c)], 0.005, polar=(nm == '칸 위'))
            qs += new; names += [nm] * len(new)
        tp, ta, tc = grip(qs[-1])
        if tc @ c_try > 0.995 and np.linalg.norm(tp - above) < 2e-3:
            break
    c_star = c_try
    grips = ['-'] * len(qs)
    qs += [qs[-1]] * int(look_s * 15); names += ['확인'] * int(look_s * 15); grips += ['-'] * int(look_s * 15)   # 3. 멈춰 확인 (15 경유점 ≈ 1 s)
    grips[-1] = 'release'                                                  #    손가락 벌림
    grasp_p = np.r_[xy, TOP - depth]
    new = lerp_path(qs[-1], [(grasp_p, down, c_star)], 0.0025)             # 4. 수직으로 내림 (천천히)
    qs += new; names += ['내림'] * len(new); grips += ['-'] * len(new)
    qs += [qs[-1]] * 8; names += ['쥠'] * 8; grips += ['close'] + ['-'] * 7  # 5. 쥠
    new = lerp_path(qs[-1], [(above, down, c_star)], 0.0025)               # 6. 수직으로 들기
    qs += new; names += ['들기'] * len(new); grips += ['-'] * len(new)
    # 7. 쥔 퍽 (손끝 아래 약 47 mm 매달림) 바닥이 적재된 퍽 윗면 + 10 mm 위로 오게 더 들기. 이 높이는 손을 수직으로 못 세움 (J4 한계) → 기울기 허용
    carry_z = TOP + 0.047 + 0.010 + 0.017
    new = lerp_path(qs[-1], [(np.r_[xy, carry_z], down, c_star)], 0.0025, w_a=0.3)
    qs += new; names += ['더 들기'] * len(new); grips += ['-'] * len(new)
    box_above = np.r_[0.21, 0.03, carry_z]
    new = lerp_path(qs[-1], [(box_above, down, front_close(box_above[:2]))], 0.005, w_a=0.3, polar=True)   # 8. 몸통을 정면으로 돌리며 J5 도 원점 (그리퍼 머리 정면)
    qs += new; names += ['박스 쪽'] * len(new); grips += ['-'] * len(new)
    Q = np.array([to_cmd(q) for q in qs])
    return Q, grips, names


if __name__ == '__main__':
    import sys
    for cell, occ in (('S10', ['S11', 'S12', 'S3', 'S6', 'S7', 'S8', 'S9', 'S5']), ('S7', ['S12'])):
        Q, G, N = retrieve_path(cell, occ)
        tips = np.array([grip(to_qm(q))[0] for q in Q])
        print(cell, len(Q), 'close axis', choose_close(cell, occ)[:2].round(2), 'J5 range', Q[:, 4].min().round(2), Q[:, 4].max().round(2),
              'tip z min', tips[:, 2].min().round(3), 'TOP', round(TOP, 4))


# ---------------------------------------------------------------- 놓기 (주사위 칸)
BOX_X, PITCH = 0.2575, 0.060                    # maps/dice_map.yaml 정차 거리 · 눈 간격
BOX_TOPB = 0.070 - 0.034                         # 박스 윗면 (base_link)
# 팀 mission/src/dice.cpp dice_pip_offsets: (열 x −1 왼쪽 · +1 오른쪽, 행 y +1 = 로봇에서 먼 쪽)
PIPS = {1: [(0, 0)], 2: [(-1, 1), (1, -1)], 3: [(-1, 1), (0, 0), (1, -1)], 4: [(-1, 1), (1, 1), (-1, -1), (1, -1)],
        5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)], 6: [(-1, 1), (-1, 0), (-1, -1), (1, 1), (1, 0), (1, -1)]}


def pip_xy(px, py):
    """보는 사람 (로봇, +x 를 봄) 기준 그림 → base_link: 오른쪽 = −y, 먼 쪽 = +x (dice.cpp pips_view_to_map)."""
    return np.array([BOX_X + py * PITCH, -px * PITCH])


def pip_order(pips):
    """놓는 순서 (사용자 2026-11-11): 먼 줄 → 가까운 줄, 같은 줄은 왼쪽 → 오른쪽 (팀 dice.cpp order_far_first 를 바꿈).
    J5 원점 (정면) 으로 놓으면 손가락이 좌우로 닫힘 → 이 순서면 이미 놓인 퍽은 늘 왼쪽 · 먼 쪽."""
    return sorted(PIPS[pips], key=lambda c: (-c[1], c[0]))


FRONT_DEG = 86.0       # J5 원점 (HOME J5 0.023) 수직 손의 닫힘축 = J1 → 손끝 반지름 방향에서 86° (IK 로 잼, 2026-11-11)


def front_close(xy):
    """그리퍼 머리 정면 (J5 원점) 일 때 닫힘축 (손가락 좌우)."""
    r = np.asarray(xy, float) - J1XY
    a = np.arctan2(r[1], r[0]) + np.radians(FRONT_DEG)
    return np.array([np.cos(a), np.sin(a), 0.0])


def choose_close_xy(xy, others):
    best = None
    for ax in (np.array([1.0, 0.0]), np.array([0.0, 1.0])):
        lat = np.array([-ax[1], ax[0]])
        hits, near = 0, 1.0
        for o in others:
            d = np.asarray(o) - xy
            if abs(d @ lat) < 0.035:
                near = min(near, abs(d @ ax)); hits += abs(d @ ax) < 0.065
        if best is None or (hits, -near) < best[0]:
            best = ((hits, -near), ax)
    return np.r_[best[1], 0.0]


def place_and_home(q_start, target_xy, placed_xy, depth=0.025, home=True):
    """쥔 퍽을 박스 주사위 칸에 놓고 HOME 으로. 이미 놓인 퍽 (placed_xy) 을 피해 손가락 방향 고름."""
    down = np.array([0, 0, -1.0])
    c = front_close(target_xy)                                        # 그리퍼 머리 정면 그대로 (손가락 좌우)
    carry_z = BOX_TOPB + 0.060 + 0.047 + 0.010 + 0.012              # 쥔 퍽 바닥이 놓인 퍽 윗면 10 mm 위 (팔이 닿는 높이)
    place_z = BOX_TOPB + 0.060 - depth + 0.002                         # 퍽 바닥이 박스 윗면 2 mm 위에서 놓음
    qs, names, grips = [], [], []
    q = q_start
    for p, nm, step, wa in ((np.r_[grip(q)[0][:2], carry_z], '박스 위로 내림', 0.005, 1.0),   # 박스 쪽 자리에서 놓기 높이로 내림
                            (np.r_[target_xy, carry_z], '놓을 칸 위', 0.005, 1.0)):            # 그 높이로 칸 위까지 수평
        new = lerp_path(q, [(p, down, c)], step, w_a=wa); q = new[-1]
        qs += new; names += [nm] * len(new); grips += ['-'] * len(new)
    qs += [q] * 15; names += ['자리 확인'] * 15; grips += ['-'] * 15
    new = lerp_path(q, [(np.r_[target_xy, place_z], down, c)], 0.0025, w_a=3.0); q = new[-1]
    qs += new; names += ['내려놓기'] * len(new); grips += ['-'] * len(new)
    qs += [q] * 10; names += ['놓음'] * 10; grips += ['release:0.0100'] + ['-'] * 9   # 좁게 벌림 (옆 퍽 60 mm, 여유 약 11 mm)
    new = lerp_path(q, [(np.r_[target_xy, carry_z], down, c)], 0.0025, w_a=1.0); q = new[-1]
    qs += new; names += ['들기'] * len(new); grips += ['-'] * len(new)
    if not home:          # 바로 다음 칸으로 (HOME 안 들름)
        return np.array([to_cmd(x) for x in qs]), grips, names
    hq, hg, hn = go_home(q)
    qs += hq; grips += hg; names += hn
    return np.array([to_cmd(x) for x in qs]), grips, names


def full_path(cell, occupied, target_xy, placed_xy):
    Q1, G1, N1 = retrieve_path(cell, occupied)
    Q2, G2, N2 = place_and_home(to_qm(Q1[-1]), target_xy, placed_xy)
    return np.vstack([Q1, Q2]), G1 + G2, N1 + N2


# ---------------------------------------------------------------- 넣기 (박스 위 퍽 → 적재함 칸)
def cargo_order():
    """config/planning.yaml cargo_slots (혁무님 실물 시험 순서)."""
    import re
    for line in open(sag.TEAM / 'config/planning.yaml'):
        m_ = re.match(r'\s*cargo_slots:\s*\[(.*)\]', line)
        if m_:
            return [c.strip().strip('"').strip("'") for c in m_.group(1).split(',')]


def _plan_list(key):
    """config/planning.yaml 의 ["A:B", ...] 목록 → [(A, B)] (A 를 넣기 · 빼기 전에 B 가 비어야 함)."""
    import re
    for line in open(sag.TEAM / 'config/planning.yaml'):
        m_ = re.match(r'\s*' + key + r':\s*\[(.*?)\]', line)
        if m_:
            return [tuple(x.strip().strip('"').strip("'").split(':')) for x in m_.group(1).split(',') if ':' in x]
    return []


def store_cell(occupied):
    """넣을 칸: 혁무님 순서 (cargo_slots) 첫 빈 칸, 넣기 제약 (rack_store_needs_empty) 을 어기면 다음 빈 칸."""
    need = _plan_list('rack_store_needs_empty')
    empty = [c for c in cargo_order() if c not in occupied]
    for c in empty:
        if all(b not in occupied for a, b in need if a == c):
            return c
    return empty[0]


def retrieve_cells(filled, n):
    """뺄 칸 n 개 차례: 마지막에 넣은 칸부터 (cargo_slots 거꾸로), 빼기 제약 (rack_retrieve_needs_empty) 을 지키는 칸 먼저."""
    need = _plan_list('rack_retrieve_needs_empty')
    left, out = list(filled), []
    order = cargo_order()
    for _ in range(n):
        cands = sorted(left, key=order.index, reverse=True)
        ok = [c for c in cands if all(b not in left for a, b in need if a == c)]
        c = (ok or cands)[0]
        out.append(c); left.remove(c)
    return out


def random_box_layout(n, seed, pitch=0.05, jitter=0.004, max_yaw=np.radians(30)):
    """박스 윗면 퍽 n 개 무작위: 3 × 4 자리 (간격 50 mm) 중 n 개 + 위치 ±4 mm · 방향 ±30°. [(x, y, yaw)] base_link."""
    rng = np.random.default_rng(seed)
    grid = [(BOX_X + (i - 1) * pitch, (j - 1.5) * pitch) for i in range(3) for j in range(4)]   # 3 줄 × 4 (차체에서 5 cm 이상)
    pick = rng.choice(len(grid), n, replace=False)
    return [(grid[k][0] + rng.uniform(-jitter, jitter), grid[k][1] + rng.uniform(-jitter, jitter), rng.uniform(-max_yaw, max_yaw)) for k in pick]


def feasible_sign(p, c, seed):
    """닫힘 축 c 와 −c 중 (손끝 p, 손 수직) J5 가 시뮬 범위 안이고 지금 J5 에서 덜 돌리는 쪽."""
    down = np.array([0, 0, -1.0])
    best = None
    for cs in (c, -c):
        for d5 in (0.0, np.pi / 2, -np.pi / 2, np.pi, -np.pi):
            q_t, e = ik(p, down, cs, seed + np.r_[0, 0, 0, 0, d5], w_lim=0.0)
            res = grip(q_t)
            j5 = to_cmd(q_t)[4]
            ok = e < 1e-3 and LO[4] <= j5 <= HI[4] and res[2] @ cs > 0.995
            key = (0 if ok else 1, abs(j5 - to_cmd(seed)[4]))
            if best is None or key < best[0]:
                best = (key, cs)
    return best[1]


OPEN_WIDE, OPEN_NARROW = 0.0187, 0.0100      # 시뮬 손가락 값: 넓게 (간격 약 59 mm) · 좁게 (약 42 mm, 한쪽 6 mm 여유)


def finger_reach(q):
    """손가락 바깥 끝까지 닫힘축 거리 [m] ≈ 간격/2 + 손가락 두께 12 mm (30 mm 퍽을 쥔 값 0.0041 에서 간격 30 mm)."""
    return (0.030 + 2 * (q - 0.0041)) / 2 + 0.012


def choose_face_close(xy, yaw, others, body_x=0.150, cyl=False):
    """네모 퍽: 닫힘 축 (면 법선 yaw · yaw + 90°) × 벌림 폭 (넓게 · 좁게) 중 손가락이 옆 퍽 · 차체에 안 닿는 것.
    넓은 쪽부터, 같으면 옆 퍽까지 여유 큰 쪽 (팀 grasp_select 순서)."""
    cands = []
    angs = np.radians(np.arange(0, 180, 15)) if cyl else (yaw, yaw + np.pi / 2)   # 원기둥: 15° 간격 12 방향 (grasp_select 와 같음)
    for width in (OPEN_WIDE, OPEN_NARROW):
        reach = finger_reach(width)
        for ang in angs:
            ax = np.array([np.cos(ang), np.sin(ang)]); lat = np.array([-ax[1], ax[0]])
            clear = 1.0
            for o in others:
                d = np.asarray(o[:2]) - xy
                if abs(d @ lat) < 0.016 + 0.021:                  # 손가락 폭 ±16 mm + 퍽 반 대각 21 mm
                    clear = min(clear, abs(d @ ax) - 0.021 - reach)
            clear = min(clear, min(xy[0] + reach * ax[0], xy[0] - reach * ax[0]) - body_x)
            cands.append((clear >= 0.003, width, clear, ax))
    ok = [c for c in cands if c[0]]
    best = max(ok, key=lambda c: (c[1], c[2])) if ok else max(cands, key=lambda c: c[2])
    return np.r_[best[3], 0.0], best[1]


def store_path(work, others, cell, occupied, depth=0.025, safe_z=0.22, insert_gap=0.008, ins_offset=(0.0, 0.0), ins_dyaw=0.0, cyl=False):
    """박스 위 퍽 work (x, y, yaw) 를 집어 칸 cell 에 넣고 HOME. others = 박스 위 다른 퍽, occupied = 이미 찬 칸."""
    down = np.array([0, 0, -1.0])
    qs, names = team_unfold(); grips = ['-'] * len(qs)
    wxy = np.array(work[:2])
    c_pick, w_pick = choose_face_close(wxy, work[2], others, cyl=cyl)
    p0, a0, c0 = grip(qs[-1])
    c_pick = feasible_sign(np.r_[wxy, BOX_TOPB + 0.060 + 0.047 + 0.010 + 0.012], c_pick, qs[-1])
    pick_top = BOX_TOPB + 0.060
    box_z = BOX_TOPB + 0.060 + 0.047 + 0.010 + 0.012          # 박스 위 이동 (쥔 퍽 바닥이 다른 퍽 윗면 10 mm 위)
    rack_z = TOP + 0.047 + 0.010 + 0.017                      # 적재함 위 이동 (쥔 퍽 바닥이 적재 퍽 윗면 10 mm 위)

    def go(p, a, c, nm, step=0.005, wa=3.0, g='-', polar=False):
        nonlocal qs, names, grips
        new = lerp_path(qs[-1], [(p, a, c)], step, w_a=wa, polar=polar)
        qs += new; names += [nm] * len(new); grips += [g] + ['-'] * (len(new) - 1)

    def hold(n, nm, g='-'):
        nonlocal qs, names, grips
        qs += [qs[-1]] * n; names += [nm] * n; grips += [g] + ['-'] * (n - 1)

    go(np.r_[p0[:2], safe_z], down, c0, '일어섬')
    go(np.r_[p0[:2] + (wxy - p0[:2]) * 0.5, safe_z], down, c_pick, '박스 쪽', wa=1.0)
    go(np.r_[wxy, box_z], down, c_pick, '퍽 위', wa=1.0)
    hold(15, '확인', g=f'release:{w_pick}')
    go(np.r_[wxy, pick_top - depth], down, c_pick, '내림', step=0.0025)
    hold(8, '쥠', g='close')
    go(np.r_[wxy, box_z], down, c_pick, '들기', step=0.0025, wa=1.0)
    # 적재함 칸으로: 퍽 면을 칸 면에 맞춤 (손목 돌림), 닫힘 축 = 옆 칸 퍽이 없는 쪽
    cxy = np.array(CELLS[cell]['xy'])
    c_ins = choose_close(cell, occupied)
    c_ins = feasible_sign(np.r_[cxy, TOP + 0.047 + 0.010 + 0.017], c_ins, to_qm(sm.true_from_cmd(np.array(P[f'retrieve_{cell}']['q']).reshape(-1, 5)[
        max(i for i, g in enumerate(P[f'retrieve_{cell}']['grip']) if g == 'close')])))
    go(np.r_[wxy, rack_z], down, c_pick, '더 들기', step=0.0025, wa=0.3)
    go(np.r_[cxy, rack_z], down, c_ins, '칸 위로', wa=0.3, polar=True)
    hold(15, '확인')
    # 칸 위 확인 때 잰 손 안 퍽 비킴 (ins_offset, 세계 xy) · 방향 어긋남 (ins_dyaw) 만큼 손끝 · 손목 보정 (실물 = 손목 카메라 · /held_puck/tag)
    txy = cxy - np.asarray(ins_offset)
    cr, sr = np.cos(-ins_dyaw), np.sin(-ins_dyaw)
    c_fix = np.r_[cr * c_ins[0] - sr * c_ins[1], sr * c_ins[0] + cr * c_ins[1], 0.0]
    go(np.r_[txy, rack_z], down, c_fix, '맞춤', step=0.0015, wa=0.3)
    ins_tip = RC['floor_z'] + insert_gap + 0.060 - depth
    go(np.r_[txy, safe_z], down, c_fix, '넣기', step=0.0025, wa=3.0)
    go(np.r_[txy, ins_tip], down, c_fix, '넣기', step=0.0015, wa=3.0)
    hold(10, '놓음', g='release:0.0085')                          # 컵 안: 살짝만 벌림 (옆 칸 퍽 · 컵 벽)
    go(np.r_[txy, safe_z], down, c_fix, '들기', step=0.0025)
    hq, hg, hn = go_home(qs[-1])
    qs += hq; grips += hg; names += hn
    return np.array([to_cmd(x) for x in qs]), grips, names



def dice_sequence(cells, occupied, pips):
    """주사위 눈 pips 개를 먼 칸부터, 칸 cells 차례로 꺼내 놓음. 놓은 뒤 HOME 안 들르고 바로 다음 칸, 마지막만 HOME.
    돌려줌: Q, grips, names, 구간 [(시작 경유점, 칸, 놓을 xy)]."""
    order = [pip_xy(*c) for c in pip_order(pips)]
    Q, G, N, segs = [], [], [], []
    occ = list(occupied)
    q = None
    for k, (cell, xy) in enumerate(zip(cells, order)):
        segs.append((len(Q), cell, xy))
        Q1, G1, N1 = retrieve_path(cell, [c for c in occ if c != cell], q_start=q)
        import store2                                   # 먼 자리는 기울여 다시 쥐어 놓기 (store2.place_dice)
        P = store2.Path(to_qm(Q1[-1]))
        store2.place_dice(P, xy, order[:k])
        if k == len(order) - 1:
            hq, hg, hn = go_home(P.q[-1]); P.extend(hq, hg, hn)
        Q2 = np.array([to_cmd(x) for x in P.q[1:]]); G2, N2 = P.g[1:], P.n[1:]
        Q += list(Q1) + list(Q2); G += G1 + G2; N += N1 + N2
        occ.remove(cell)
        q = to_qm(Q2[-1])
    Q, G, N, st = dense_all(np.array(Q), G, N, [s_[0] for s_ in segs])
    return Q, G, N, [(a_, c_, x_) for a_, (_, c_, x_) in zip(st, segs)]


def unwrap_limits(Q):
    """관절 값 (팀 명령) 이 한 바퀴 (2π) 건너뛰면 실제 관절 범위 (LO–HI) 안의 같은 각도로. 틱 변환 (cmd_to_ticks) 이 범위 끝에서
    2π 바꿔 놓아 J4 가 한 바퀴 도는 명령이 됐음 (2026-11-11, 시뮬에서 그리퍼가 하늘로 꺾임)."""
    Q = np.array(Q, float)
    for i in range(len(Q)):
        for j in range(5):
            cands = Q[i, j] + 2 * np.pi * np.arange(-2, 3)
            inside = cands[(cands >= LO[j] - 0.05) & (cands <= HI[j] + 0.05)]
            pool = inside if len(inside) else cands
            ref = Q[i - 1, j] if i else Q[i, j]
            Q[i, j] = pool[np.argmin(np.abs(pool - ref))]
    return Q


# 속도 (사용자 2026-11-11: 빈 공간은 빠르게 · 퍽 근처는 안정적으로, 최고 속도까지 올렸다가 다시 줄임) — 팀 config/control.yaml 값
FAST = {'칸 위', '박스 쪽', '놓을 칸 위', '칸 위로', '적재함 높이로', '먼 자리 위로', '먼 퍽 위 (손 기울임)', '누운 퍽 위', '박스 빈 자리로',
        '퍽 뒤 위로', '가까운 자리로', '기울여 다시 쥐러', '돌아감', '박스 위로 내림', '일어섬', '퍽 위', '다시 퍽 위', '더 들기'}
SLOW_PUSH = ('눌러 세우기', '꽂아 눌러')
V_FAST, V_NEAR, V_PUSH = np.radians(150.0), np.radians(62.5), np.radians(20.0)   # path_speed_dps · near_puck_speed_dps · park_push_speed_dps
ACC = 3.7                  # 가감속 [rad/s²] (2026-11-11 사용자: 5.0–1.0 비교 뒤 3.7, 몸체 0.32°)
WP_DT = 2 / 30             # 경유점 하나 = 정책 2 스텝


def _speed(name):
    if name in FAST:
        return V_FAST
    if any(k in name for k in SLOW_PUSH):
        return V_PUSH
    return V_NEAR


def dense_all(Q, G, N, marks=(), max_step=None):
    """경로 (팀 관절 값) 를 시간으로 다시 나눔 (경유점 간격 WP_DT). 멈춤 (같은 자세 반복 = 확인 · 쥠 · 놓음) 사이는 한 번에 이어서:
    출발 때 가속 ACC 로 올리고, 멈출 곳 앞에서만 줄임. 구간마다 최고 속도 (빈 공간 · 퍽 근처) 가 달라도 서지 않고 속도만 바꿈
    (앞 · 뒤 두 번 훑어 가속 한계 안에서 가장 빠른 속도, 사용자 2026-11-11: 뚝뚝 끊기지 않게)."""
    Q = unwrap_limits(Q)
    G, N = list(G), list(N)
    oq, og, on, idx = [Q[0]], [G[0]], [N[0]], [0]
    i = 1
    while i < len(Q):
        if np.abs(Q[i] - Q[i - 1]).max() < 1e-6:                  # 멈춤
            oq.append(Q[i]); og.append(G[i]); on.append(N[i]); idx.append(len(oq) - 1); i += 1
            continue
        j = i
        while j < len(Q) and np.abs(Q[j] - Q[j - 1]).max() >= 1e-6:
            j += 1
        pts = np.vstack([oq[-1:], Q[i:j]])
        seg = np.abs(np.diff(pts, axis=0)).max(1)
        cum = np.r_[0, np.cumsum(seg)]
        vlim = np.array([_speed(N[m]) for m in range(i, j)])      # 각 작은 구간 (pts[k] → pts[k+1]) 최고 속도
        v = np.r_[0.0, vlim.copy()]                                 # 각 점 속도 (끝점 0)
        v[-1] = 0.0
        for k in range(1, len(v)):                                  # 앞으로: 가속 한계
            v[k] = min(v[k], np.sqrt(v[k - 1] ** 2 + 2 * ACC * seg[k - 1]), vlim[k - 1] if k - 1 < len(vlim) else v[k])
        for k in range(len(v) - 2, -1, -1):                         # 뒤로: 감속 한계
            v[k] = min(v[k], np.sqrt(v[k + 1] ** 2 + 2 * ACC * seg[k]))
        dt = 2 * seg / np.maximum(v[:-1] + v[1:], 1e-9)             # 작은 구간마다 걸리는 시간 (등가속)
        tcum = np.r_[0, np.cumsum(dt)]
        T = tcum[-1]
        n = max(1, int(np.ceil(T / WP_DT)))
        base = len(oq)
        for t in np.linspace(0, T, n + 1)[1:]:
            k = min(np.searchsorted(tcum, t, side='right') - 1, len(seg) - 1)
            tau = t - tcum[k]; a_k = (v[k + 1] - v[k]) / max(dt[k], 1e-9)
            d = min(v[k] * tau + 0.5 * a_k * tau * tau, seg[k])
            oq.append(pts[k] + d / max(seg[k], 1e-12) * (pts[k + 1] - pts[k])); on.append(N[min(i + k, j - 1)]); og.append('-')
        for m_, tc in zip(range(i, j), tcum[1:]):                   # 원래 경유점 → 그 시각에 처음 닿는 새 경유점
            nk = base + int(min(np.ceil(tc / WP_DT - 1e-9) - 1, n - 1))
            nk = max(nk, base)
            if G[m_] != '-':
                og[nk] = G[m_]
            idx.append(nk)
        i = j
    return np.array(oq), og, on, [idx[m] for m in marks]
