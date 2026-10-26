#!/usr/bin/env python3
"""초벌 라벨 확인·수정 도구 (real_raw처럼 사진 옆에 .txt가 있는 폴더용).

클래스: 0 qr | 1 puck_cyl (원기둥) | 2 puck_box (직육면체) | 3 signal_tower | 4 barcode
- 노란 점선 '?' = 모델이 자신 없던 박스 → 맞으면 그 번호 키, 틀리면 다른 번호, 헛것이면 r
- 모델이 놓친 것(특히 바코드)은 마우스로 드래그해서 그리고 번호 키로 확정
- 사진을 넘길 때(d/a/n) 자동 저장되고 '확인한 사진'으로 기록돼요. 중간에 꺼도 이어서 할 수 있어요.

조작법
  [드래그] 새 박스 (barcode?로 생김 → 번호 키)   [클릭] 박스 선택
  0~4  선택 박스 클래스 정하기(+확인)   Tab / ]  다음 박스   [  이전 박스   r  선택 박스 삭제
  u    다음 '?' 박스로 (다른 사진까지)
  n    아직 확인 안 한 다음 사진으로
  d/a  다음 / 이전 사진   s 저장   q 저장 후 종료

실행:
  ~/pa-course/.venv-yolo/bin/python review_labels.py
"""
import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

CLASSES = ["qr", "puck_cyl", "puck_box", "signal_tower", "barcode"]
COLORS = [(255, 160, 0), (0, 200, 0), (0, 120, 255), (200, 0, 200), (0, 230, 230)]  # BGR
WIN, ZOOM = "review", "zoom"
BAR = 54


def load_yolo(p):
    out = []
    if p.exists():
        for ln in p.read_text().splitlines():
            v = ln.split()
            if len(v) == 5:
                out.append([int(v[0])] + [float(x) for x in v[1:]])
    return out


class App:
    def __init__(self, root, max_w, pick_sec=0.0):
        self.root = root
        self.imgs = sorted(p for p in root.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.name != "contact.jpg")
        assert self.imgs, f"사진이 없어요: {root}"
        self.rev_path = root / "_review.json"
        self.rev = json.loads(self.rev_path.read_text()) if self.rev_path.exists() else {}
        if pick_sec > 0:   # 영상 프레임: pick_sec초 간격으로 한 장씩만 (비슷한 연속 사진 건너뜀)
            keep = set()
            for csv_path in root.rglob("frames.csv"):
                last = -1e9
                with open(csv_path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        t = float(row["time_s"])
                        if t - last >= pick_sec:
                            keep.add(csv_path.parent / row["file"]); last = t
            n0 = len(self.imgs)
            self.imgs = [p for p in self.imgs if p in keep or self.info(p).get("reviewed")
                         or not (p.parent / "frames.csv").exists()]
            print(f"{pick_sec}초 간격으로 골라서 {n0}장 중 {len(self.imgs)}장만 확인해요 (나머지는 학습에서 빠져요)")
        self.max_w = max_w
        self.idx = next((i for i, p in enumerate(self.imgs) if not self.info(p).get("reviewed")), 0)
        self.sel, self.drag = 0, None
        self.load()

    def key(self, p):
        return str(p.relative_to(self.root))

    def info(self, p):
        return self.rev.get(self.key(p), {})

    # ---------- 파일 ----------
    def load(self):
        p = self.imgs[self.idx]
        self.img = cv2.imread(str(p))
        self.H, self.W = self.img.shape[:2]
        self.scale = min(1.0, self.max_w / self.W)
        unchecked = set(self.info(p).get("unchecked", []))
        self.boxes = [dict(c=b[0], xywh=b[1:], ok=(i not in unchecked)) for i, b in enumerate(load_yolo(p.with_suffix(".txt")))]
        self.sel = 0

    def save(self, reviewed=True):
        p = self.imgs[self.idx]
        lines = [f"{b['c']} " + " ".join(f"{v:.6f}" for v in b["xywh"]) for b in self.boxes]
        p.with_suffix(".txt").write_text("\n".join(lines) + ("\n" if lines else ""))
        old = self.info(p)
        self.rev[self.key(p)] = dict(old, unchecked=[i for i, b in enumerate(self.boxes) if not b["ok"]],
                                     reviewed=old.get("reviewed", False) or reviewed)
        self.rev_path.write_text(json.dumps(self.rev, indent=1, ensure_ascii=False))

    # ---------- 좌표 ----------
    def to_px(self, xywh):
        cx, cy, w, h = xywh
        return (int((cx - w / 2) * self.W), int((cy - h / 2) * self.H),
                int((cx + w / 2) * self.W), int((cy + h / 2) * self.H))

    def hit(self, x, y):
        best = None
        for i, b in enumerate(self.boxes):
            x1, y1, x2, y2 = self.to_px(b["xywh"])
            if x1 - 4 <= x <= x2 + 4 and y1 - 4 <= y <= y2 + 4:
                a = (x2 - x1) * (y2 - y1)
                if best is None or a < best[0]:
                    best = (a, i)
        return None if best is None else best[1]

    # ---------- 그리기 ----------
    def counts(self):
        cur = self.key(self.imgs[self.idx])
        reviewed = sum(1 for p in self.imgs if self.info(p).get("reviewed") or self.key(p) == cur)
        unchecked = sum(not b["ok"] for b in self.boxes) + sum(
            len(self.info(p).get("unchecked", [])) for p in self.imgs if self.key(p) != cur)
        return reviewed, unchecked

    def draw(self):
        vis = self.img.copy()
        for i, b in enumerate(self.boxes):
            x1, y1, x2, y2 = self.to_px(b["xywh"])
            col = COLORS[b["c"]] if b["ok"] else (0, 255, 255)
            th = 3 if i == self.sel else 1
            if b["ok"]:
                cv2.rectangle(vis, (x1, y1), (x2, y2), col, th)
            else:
                for t in range(0, max(x2 - x1, 1), 8):
                    cv2.line(vis, (x1 + t, y1), (min(x1 + t + 4, x2), y1), col, th)
                    cv2.line(vis, (x1 + t, y2), (min(x1 + t + 4, x2), y2), col, th)
                for t in range(0, max(y2 - y1, 1), 8):
                    cv2.line(vis, (x1, y1 + t), (x1, min(y1 + t + 4, y2)), col, th)
                    cv2.line(vis, (x2, y1 + t), (x2, min(y1 + t + 4, y2)), col, th)
            tag = f"{i}:{CLASSES[b['c']]}" + ("" if b["ok"] else "?")
            cv2.putText(vis, tag, (x1, max(y1 - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
        if self.drag and self.drag[2] is not None:
            cv2.rectangle(vis, tuple(self.drag[:2]), self.drag[2], COLORS[4], 2)
        reviewed, unchecked = self.counts()
        p = self.imgs[self.idx]
        head = (f"[{self.idx + 1}/{len(self.imgs)}] {self.key(p)}  boxes={len(self.boxes)}  "
                f"checked photos {reviewed}/{len(self.imgs)}  '?' left {unchecked}"
                + ("  (checked)" if self.info(p).get("reviewed") else ""))
        vis = cv2.resize(vis, None, fx=self.scale, fy=self.scale) if self.scale < 1 else vis
        bar = np.zeros((BAR, vis.shape[1], 3), np.uint8)
        cv2.putText(bar, head, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(bar, "0 qr 1 cyl 2 box 3 tower 4 barcode | drag=new r=del Tab/[]=box u=next '?' n=next unchecked photo a/d=photo q=quit",
                    (8, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 180, 180), 1, cv2.LINE_AA)
        cv2.imshow(WIN, np.vstack([bar, vis]))
        self.draw_zoom()

    def draw_zoom(self):
        z = np.zeros((360, 360, 3), np.uint8)
        if self.boxes:
            b = self.boxes[self.sel]
            x1, y1, x2, y2 = self.to_px(b["xywh"])
            m = max(x2 - x1, y2 - y1)
            X1, Y1, X2, Y2 = max(0, x1 - m), max(0, y1 - m), min(self.W, x2 + m), min(self.H, y2 + m)
            crop = self.img[Y1:Y2, X1:X2].copy()
            cv2.rectangle(crop, (x1 - X1, y1 - Y1), (x2 - X1, y2 - Y1), (0, 255, 255), 1)
            if crop.size:
                s = 360 / max(crop.shape[:2])
                crop = cv2.resize(crop, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST if s > 4 else cv2.INTER_LINEAR)
                z[:crop.shape[0], :crop.shape[1]] = crop
            cv2.putText(z, f"#{self.sel} {CLASSES[b['c']]}{'' if b['ok'] else ' ?'}", (6, 352),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow(ZOOM, z)

    # ---------- 입력 ----------
    def on_mouse(self, ev, x, y, flags, _):
        y -= BAR
        x, y = int(x / self.scale), int(y / self.scale)
        x, y = max(0, min(self.W - 1, x)), max(0, min(self.H - 1, y))
        if ev == cv2.EVENT_LBUTTONDOWN:
            self.drag = [x, y, None]
        elif ev == cv2.EVENT_MOUSEMOVE and self.drag:
            self.drag[2] = (x, y); self.draw()
        elif ev == cv2.EVENT_LBUTTONUP and self.drag:
            sx, sy, e = self.drag
            self.drag = None
            if e and abs(e[0] - sx) > 4 and abs(e[1] - sy) > 4:
                x1, x2 = sorted((sx, e[0])); y1, y2 = sorted((sy, e[1]))
                self.boxes.append(dict(c=4, ok=False, xywh=[(x1 + x2) / 2 / self.W, (y1 + y2) / 2 / self.H,
                                                            (x2 - x1) / self.W, (y2 - y1) / self.H]))
                self.sel = len(self.boxes) - 1
            else:
                h = self.hit(sx, sy)
                if h is not None:
                    self.sel = h
            self.draw()

    def goto(self, i):
        self.save()
        self.idx = i % len(self.imgs)
        self.load()

    def jump_unchecked_box(self):
        for k in range(len(self.boxes)):
            j = (self.sel + 1 + k) % len(self.boxes)
            if not self.boxes[j]["ok"]:
                self.sel = j; return
        for _ in range(1, len(self.imgs)):
            self.goto(self.idx + 1)
            for j, b in enumerate(self.boxes):
                if not b["ok"]:
                    self.sel = j; return
        print("'?' 박스가 더 없어요.")

    def jump_unreviewed(self):
        cur = self.idx
        for k in range(1, len(self.imgs)):
            j = (cur + k) % len(self.imgs)
            if not self.info(self.imgs[j]).get("reviewed"):
                self.goto(j); return
        self.save()
        print("모든 사진을 확인했어요.")

    def run(self):
        cv2.namedWindow(WIN, cv2.WINDOW_AUTOSIZE)
        cv2.namedWindow(ZOOM, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WIN, self.on_mouse)
        while True:
            self.draw()
            k = cv2.waitKey(0) & 0xFF
            if k in (ord("q"), 27):
                break
            if ord("0") <= k <= ord("4") and self.boxes:
                self.boxes[self.sel].update(c=k - ord("0"), ok=True)
            elif k in (9, ord("]")) and self.boxes:
                self.sel = (self.sel + 1) % len(self.boxes)
            elif k == ord("[") and self.boxes:
                self.sel = (self.sel - 1) % len(self.boxes)
            elif k == ord("r") and self.boxes:
                self.boxes.pop(self.sel); self.sel = max(0, min(self.sel, len(self.boxes) - 1))
            elif k == ord("d"):
                self.goto(self.idx + 1)
            elif k == ord("a"):
                self.goto(self.idx - 1)
            elif k == ord("u"):
                self.jump_unchecked_box()
            elif k == ord("n"):
                self.jump_unreviewed()
            elif k == ord("s"):
                self.save(); print("saved", self.key(self.imgs[self.idx]))
        self.save()
        cv2.destroyAllWindows()
        self.report()

    def report(self):
        cnt = [0] * len(CLASSES)
        for p in self.imgs:
            for b in load_yolo(p.with_suffix(".txt")):
                cnt[b[0]] += 1
        reviewed, unchecked = self.counts()
        print(f"\n확인한 사진 {reviewed}/{len(self.imgs)}  |  남은 '?' 박스 {unchecked}")
        for i, n in enumerate(cnt):
            print(f"  {i} {CLASSES[i]:<13} {n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path.home() / "바탕화면/git/TIL/classes/PhysicalAi/projects/project-2/archive/real_raw"))
    ap.add_argument("--max-w", type=int, default=1500)
    ap.add_argument("--pick-sec", type=float, default=3.0, help="영상 프레임을 몇 초 간격으로 고를지 (0 = 전부)")
    a = ap.parse_args()
    App(Path(a.root), a.max_w, a.pick_sec).run()
