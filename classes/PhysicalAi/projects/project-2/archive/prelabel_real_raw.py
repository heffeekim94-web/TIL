#!/usr/bin/env python3
"""real_raw 사진에 자동 초벌 라벨 달기 (지금 모델이 박스를 먼저 쳐 줌).

- 사진 옆에 같은 이름의 .txt (YOLO 형식, 5클래스 번호: 0 qr | 1 puck_cyl | 2 puck_box | 3 signal_tower | 4 barcode)
- 모델은 4클래스(0~3)라 바코드는 못 잡음 → review_labels.py에서 직접 그리기
- 신뢰도가 --sure 미만인 박스는 '확인 필요(?)'로 표시 → review_labels.py에서 u로 하나씩 확인
- 이미 .txt가 있는 사진은 건너뜀 (사람이 고친 라벨 보호). 다시 하려면 --overwrite

실행:
  ~/pa-course/.venv-yolo/bin/python prelabel_real_raw.py
"""
import argparse
import json
from pathlib import Path

from ultralytics import YOLO

HOME = Path.home()
ARCH = HOME / "바탕화면/git/TIL/classes/PhysicalAi/projects/project-2/archive"
REPO = HOME / "바탕화면/git/Project2_Turtle_Ninja"
DEFAULT_MODEL = REPO / "yolo/train/results/experiment_2_linear_20261023_164149/b12/weights/best_map50.pt"

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=str(ARCH / "real_raw"))
ap.add_argument("--model", default=str(DEFAULT_MODEL), help="실물 퍽 점수가 가장 높았던 experiment_2 b12")
ap.add_argument("--conf", type=float, default=0.25, help="이 값 이상만 박스로 씀 (초벌이라 조금 낮게)")
ap.add_argument("--sure", type=float, default=0.6, help="이 값 미만은 '확인 필요'로 표시")
ap.add_argument("--overwrite", action="store_true")
a = ap.parse_args()

root = Path(a.root)
imgs = sorted(p for p in root.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.name != "contact.jpg")
review_path = root / "_review.json"
review = json.loads(review_path.read_text()) if review_path.exists() else {}
todo = [p for p in imgs if a.overwrite or not p.with_suffix(".txt").exists()]
print(f"사진 {len(imgs)}장 | 새로 라벨 달 사진 {len(todo)}장 | 모델 {Path(a.model).name} ({Path(a.model).parent.parent.name})")

model = YOLO(a.model)
names = model.names
cnt, n_unsure, n_empty = {}, 0, 0
for i in range(0, len(todo), 16):
    chunk = todo[i:i + 16]
    for p, r in zip(chunk, model.predict([str(x) for x in chunk], conf=a.conf, imgsz=1280, verbose=False)):
        lines, unchecked = [], []
        for k, b in enumerate(r.boxes):
            c = int(b.cls); cx, cy, w, h = b.xywhn[0].tolist()
            lines.append(f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            cnt[names[c]] = cnt.get(names[c], 0) + 1
            if float(b.conf) < a.sure:
                unchecked.append(k)
        p.with_suffix(".txt").write_text("\n".join(lines) + ("\n" if lines else ""))
        review[str(p.relative_to(root))] = dict(unchecked=unchecked, reviewed=False, auto=True)
        n_unsure += len(unchecked); n_empty += not lines
    print(f"  {min(i + 16, len(todo))}/{len(todo)}")
review_path.write_text(json.dumps(review, indent=1, ensure_ascii=False))
print(f"\n끝: 박스 {sum(cnt.values())}개 {cnt} | 확인 필요(?) {n_unsure}개 | 박스 없는 사진 {n_empty}장")
print(f"다음: ~/pa-course/.venv-yolo/bin/python review_labels.py   (진행 기록: {review_path})")
