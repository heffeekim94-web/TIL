"""평가용 고정 시나리오 (seed 같으면 누구 컴퓨터에서나 같은 목록) — 팀원과 같은 숫자로 비교할 때 이 파일 + seed 를 맞춤.

시나리오 = {'task': 'store'|'retrieve', 'cell': 'S7', 'dice': 0..5, 'stored': ['S1', ...]}
  store    : 박스 주사위 칸 dice 의 퍽 → 빈 칸 cell. stored = 이미 찬 칸 (cell 제외)
  retrieve : 칸 cell 의 퍽 → 주사위 칸 dice. stored = 그 밖에 찬 칸
찬 칸 수는 0 ~ 11 고르게 (가장 어려운 11 개 포함).
"""
import json
import random
import sys

CELLS = [f'S{i}' for i in range(1, 13)]


def make(n, seed=0, n_dice=6):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        task = rng.choice(['store', 'retrieve'])
        k = rng.randint(0, 11)                        # 작업 퍽 말고 찬 칸 수
        cells = CELLS[:]
        rng.shuffle(cells)
        cell, stored = cells[0], sorted(cells[1:1 + k], key=lambda c: int(c[1:]))
        out.append({'task': task, 'cell': cell, 'dice': rng.randrange(n_dice), 'stored': stored})
    return out


if __name__ == '__main__':
    n, seed = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (10000, 0)
    print(json.dumps(make(n, seed)[:5], ensure_ascii=False, indent=1))
