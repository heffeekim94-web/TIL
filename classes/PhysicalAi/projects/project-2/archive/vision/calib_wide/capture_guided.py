#!/usr/bin/env python3
"""Arducam 캘리브레이션 사진을 안내에 따라 모으는 스크립트 (레포 밖에서 사용, 커밋 안 함).

실행:
    python3 ~/calib_wide/capture_guided.py --dev /dev/video8 --out ~/calib_wide2

화면 보는 법:
    - 3x3 칸: 빨강 = 아직 없음, 노랑 = 조금 있음, 초록 = 충분함. 빨강/노랑 칸에 보드를 가져가세요
    - 오른쪽 위 TILT 목록: 보드를 그 방향으로 기울인 사진. [ ] 인 것을 채우세요
    - 보드가 전부 보이고(초록 점), 잠깐 멈춰 있고, 이전 사진과 충분히 다르면 자동 저장
    - 아래쪽 NEXT 줄이 다음에 찍을 곳을 알려줌
키:
    q / ESC  종료      s  지금 프레임 강제 저장
"""

import argparse
import os
import time

import cv2
import numpy as np

CB = (9, 6)            # 내부 코너
GRID = 3               # 화면을 3x3 칸으로 나눔
ZONE_OK = 60           # 칸에 코너가 이만큼 쌓이면 초록
STABLE_PX = 1.5        # 프레임 사이 코너 평균 이동이 이보다 작으면 "멈춤"
STABLE_N = 4           # 연속으로 멈춘 프레임 수
NOVEL_TH = 0.12        # 저장된 사진들과의 최소 차이
COOLDOWN = 0.8         # 저장 간격 (초)
TILT_RATIO = 1.25      # 마주 보는 변 길이 비율이 이보다 크면 기울인 것으로 봄
TARGET = 25            # 최소 저장 장수

ZONE_NAMES = [["top-left", "top", "top-right"],
              ["left", "center", "right"],
              ["bottom-left", "bottom", "bottom-right"]]
TILTS = ["tilt-left", "tilt-right", "tilt-up", "tilt-down"]


def detect(gray):
    """반 크기에서 빠르게 찾고, 원본에서 서브픽셀로 다듬음. 못 찾으면 None."""
    small = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
    ok, c = cv2.findChessboardCorners(small, CB, flags)
    if not ok:
        return None
    c = c * 2.0
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-3)
    c = cv2.cornerSubPix(gray, c.astype(np.float32), (5, 5), (-1, -1), crit)
    return c.reshape(-1, 2)


def outer_quad(c):
    """보드 바깥 네 코너: 왼위, 오위, 오아래, 왼아래 (검출 순서 기준)."""
    g = c.reshape(CB[1], CB[0], 2)
    return g[0, 0], g[0, -1], g[-1, -1], g[-1, 0]


def tilt_of(c):
    tl, tr, br, bl = outer_quad(c)
    left, right = np.linalg.norm(bl - tl), np.linalg.norm(br - tr)
    top, bottom = np.linalg.norm(tr - tl), np.linalg.norm(br - bl)
    found = set()
    if left / right > TILT_RATIO:
        found.add("tilt-right")   # 왼쪽이 더 크게 보임 = 오른쪽이 멀어짐
    if right / left > TILT_RATIO:
        found.add("tilt-left")
    if top / bottom > TILT_RATIO:
        found.add("tilt-down")
    if bottom / top > TILT_RATIO:
        found.add("tilt-up")
    return found, left / right, top / bottom


def descriptor(c, w, h):
    """사진끼리 얼마나 다른지 비교용: 중심 위치, 크기, 기울기."""
    hull = cv2.convexHull(c.astype(np.float32))
    area = cv2.contourArea(hull) / (w * h)
    cx, cy = c.mean(0) / [w, h]
    _, lr, tb = tilt_of(c)
    return np.array([cx, cy, np.sqrt(area), np.log(lr), np.log(tb)])


def zone_counts(c, w, h):
    cnt = np.zeros((GRID, GRID), int)
    for x, y in c:
        cnt[min(int(y / h * GRID), GRID - 1), min(int(x / w * GRID), GRID - 1)] += 1
    return cnt


def sharpness(gray, c):
    x0, y0 = c.min(0).astype(int)
    x1, y1 = c.max(0).astype(int)
    roi = gray[max(y0, 0):y1, max(x0, 0):x1]
    return cv2.Laplacian(roi, cv2.CV_64F).var() if roi.size else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="/dev/video8")
    ap.add_argument("--out", default=os.path.expanduser("~/calib_wide2"))
    ap.add_argument("--min-sharp", type=float, default=80.0, help="이보다 흐리면 저장 안 함")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.dev, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        raise SystemExit(f"카메라를 열 수 없어요: {args.dev} (다른 프로그램이 쓰는 중인지 확인)")

    zones = np.zeros((GRID, GRID), int)
    tilts_done = set()
    descs = []
    saved = 0
    prev, still, last_save = None, 0, 0.0
    flash = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("프레임을 못 받았어요")
            break
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        c = detect(gray)
        view = frame.copy()

        status = "board: NOT FOUND (whole board must be visible)"
        color = (0, 0, 255)
        save_now = False
        if c is not None:
            move = np.abs(c - prev).mean() if prev is not None and prev.shape == c.shape else 99
            still = still + 1 if move < STABLE_PX else 0
            prev = c
            d = descriptor(c, w, h)
            novel = min((np.linalg.norm(d - e) for e in descs), default=9) > NOVEL_TH
            sharp = sharpness(gray, c)
            tl, _, _ = tilt_of(c)
            new_tilt = bool(tl - tilts_done)
            if still < STABLE_N:
                status, color = "board OK - hold still...", (0, 200, 255)
            elif sharp < args.min_sharp:
                status, color = f"blurry ({sharp:.0f}) - hold still", (0, 200, 255)
            elif not (novel or new_tilt):
                status, color = "same as before - move to a new place", (0, 200, 255)
            else:
                status, color = "saving", (0, 255, 0)
                save_now = time.time() - last_save > COOLDOWN
            cv2.drawChessboardCorners(view, CB, c.reshape(-1, 1, 2), True)
        else:
            prev, still = None, 0

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("s") and c is not None:
            save_now = True

        if save_now and c is not None:
            saved += 1
            cv2.imwrite(os.path.join(args.out, f"frame_{saved:03d}.png"), frame)
            descs.append(descriptor(c, w, h))
            zones += zone_counts(c, w, h)
            tilts_done |= tilt_of(c)[0]
            last_save, still, flash = time.time(), 0, 6
            print(f"saved {saved}  tilts={sorted(tilts_done)}")

        # --- 안내 표시 ---
        ov = view.copy()
        for r in range(GRID):
            for q in range(GRID):
                x0, y0 = q * w // GRID, r * h // GRID
                x1, y1 = (q + 1) * w // GRID, (r + 1) * h // GRID
                n = zones[r, q]
                col = (0, 0, 255) if n == 0 else (0, 220, 255) if n < ZONE_OK else (0, 200, 0)
                cv2.rectangle(ov, (x0, y0), (x1, y1), col, -1)
        view = cv2.addWeighted(ov, 0.18, view, 0.82, 0)
        for r in range(GRID):
            for q in range(GRID):
                x0, y0 = q * w // GRID, r * h // GRID
                cv2.rectangle(view, (x0, y0), ((q + 1) * w // GRID, (r + 1) * h // GRID), (255, 255, 255), 1)
                cv2.putText(view, f"{ZONE_NAMES[r][q]} {zones[r, q]}", (x0 + 8, y0 + 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        for k, t in enumerate(TILTS):
            mark = "[x]" if t in tilts_done else "[ ]"
            cv2.putText(view, f"{mark} {t}", (w - 190, 60 + 26 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 200, 0) if t in tilts_done else (0, 0, 255), 2)

        todo = [ZONE_NAMES[r][q] for r, q in sorted(np.ndindex(GRID, GRID), key=lambda rq: zones[rq])
                if zones[r, q] < ZONE_OK]
        todo += [t for t in TILTS if t not in tilts_done]
        nxt = "NEXT: " + (", ".join(todo[:3]) if todo else "all done!")
        if not todo and saved >= TARGET:
            nxt = "DONE - press q"
        cv2.rectangle(view, (0, h - 70), (w, h), (0, 0, 0), -1)
        cv2.putText(view, f"saved {saved}/{TARGET}   {status}", (10, h - 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(view, nxt, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if flash:
            cv2.rectangle(view, (0, 0), (w - 1, h - 1), (0, 255, 0), 12)
            flash -= 1

        cv2.imshow("calib capture", view)

    cap.release()
    cv2.destroyAllWindows()
    print(f"끝: {saved}장 저장 → {args.out}")


if __name__ == "__main__":
    main()
