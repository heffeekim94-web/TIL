"""실물 학습용 사진 촬영 (Arducam 광각).

화면을 보면서 위쪽 슬라이더로 노출·화이트밸런스를 조정하고, 스페이스바로 저장해요.
  슬라이더 auto_exp : 1 = 자동 노출, 0 = 수동 (exposure 슬라이더 값 사용, 100µs 단위: 83 = 8.3ms)
  슬라이더 auto_wb  : 1 = 자동 화이트밸런스, 0 = 수동 (wb_temp 슬라이더 값 사용, 숫자 클수록 노란빛)
  SPACE: 사진 저장 | r: 영상 녹화 시작/끝 | p: 지금 설정 출력·기록 | q: 끝
사진: 레포 yolo/datasets/real_train_raw/images/train_XXXX.jpg (다시 켜도 번호 이어짐)
영상: 레포 yolo/datasets/real_train_raw/videos/clip_XX.avi (MJPG 1280x720 30fps)
설정 기록: 같은 폴더의 ../camera_settings.txt
"""
import cv2, sys, subprocess
from datetime import datetime
from pathlib import Path

DEV = sys.argv[1] if len(sys.argv) > 1 else "/dev/video2"
OUT = Path.home() / "바탕화면/git/Project2_Turtle_Ninja/yolo/datasets/real_train_raw/images"
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT.parent / "camera_settings.txt"
n = len(list(OUT.glob("*.jpg")))


def v4l2_set(**kw):
    args = []
    for k, v in kw.items():
        args += ["-c", f"{k}={v}"]
    subprocess.run(["v4l2-ctl", "-d", DEV, *args], capture_output=True)


def v4l2_get():
    r = subprocess.run(["v4l2-ctl", "-d", DEV, "--get-ctrl=auto_exposure,exposure_time_absolute,"
                        "white_balance_automatic,white_balance_temperature,gain"], capture_output=True, text=True)
    return " | ".join(l.strip() for l in r.stdout.splitlines())


cap = cv2.VideoCapture(DEV, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

WIN = "capture"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN, 960, 640)
state = {}


def apply(_=None):
    ae = cv2.getTrackbarPos("auto_exp", WIN)
    ex = max(1, cv2.getTrackbarPos("exposure", WIN))
    aw = cv2.getTrackbarPos("auto_wb", WIN)
    wb = max(2800, cv2.getTrackbarPos("wb_temp", WIN))
    new = (ae, ex, aw, wb)
    if state.get("last") == new:
        return
    state["last"] = new
    if ae:
        v4l2_set(auto_exposure=3)
    else:
        v4l2_set(auto_exposure=1, exposure_time_absolute=ex)
    if aw:
        v4l2_set(white_balance_automatic=1)
    else:
        v4l2_set(white_balance_automatic=0, white_balance_temperature=wb)


cv2.createTrackbar("auto_exp", WIN, 1, 1, apply)
cv2.createTrackbar("exposure", WIN, 83, 500, apply)
cv2.createTrackbar("auto_wb", WIN, 1, 1, apply)
cv2.createTrackbar("wb_temp", WIN, 5000, 6500, apply)
apply()


def grab(k=4):
    """설정이 반영되도록 몇 장 버리고 마지막 장."""
    f = None
    for _ in range(k):
        ok, f = cap.read()
    return f


def stats(f):
    """밝기(평균 회색값)와 색 비율(R/G, B/G)."""
    m = f.reshape(-1, 3).mean(0)          # B, G, R
    return float(f.mean()), m[2] / max(m[1], 1), m[0] / max(m[1], 1)


def show(msg, f=None):
    v = cv2.resize(f if f is not None else grab(1), (960, 540))
    cv2.putText(v, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.imshow(WIN, v); cv2.waitKey(1)


def auto_match():
    """자동 화면과 가장 비슷한 수동 값을 찾아 고정 (카메라가 자동 값을 알려주지 않아서 화면으로 비교)."""
    v4l2_set(auto_exposure=3, white_balance_automatic=1)
    show("auto: settling 3s ...")
    import time; t0 = time.time()
    while time.time() - t0 < 3:
        show("auto: settling ...")
    ref = [stats(grab(2)) for _ in range(5)]
    L0 = sum(r[0] for r in ref) / 5; R0 = sum(r[1] for r in ref) / 5; B0 = sum(r[2] for r in ref) / 5
    print(f"자동 화면: 밝기 {L0:.1f}, R/G {R0:.3f}, B/G {B0:.3f}")
    # 1) 색: 자동 노출 유지한 채 색온도만 수동으로 바꿔 가며 비교
    best_wb = None
    for wb in range(2800, 6501, 100):
        v4l2_set(white_balance_automatic=0, white_balance_temperature=wb)
        f = grab(); _, r, b = stats(f); show(f"matching color... wb {wb}", f)
        d = abs(r - R0) + abs(b - B0)
        if best_wb is None or d < best_wb[1]:
            best_wb = (wb, d)
    v4l2_set(white_balance_automatic=0, white_balance_temperature=best_wb[0])
    # 2) 밝기: 노출을 수동으로 바꿔 가며 비교
    best_ex = None
    for ex in list(range(10, 100, 5)) + list(range(100, 501, 10)):
        v4l2_set(auto_exposure=1, exposure_time_absolute=ex)
        f = grab(); L, _, _ = stats(f); show(f"matching brightness... exp {ex}", f)
        d = abs(L - L0)
        if best_ex is None or d < best_ex[1]:
            best_ex = (ex, d)
    v4l2_set(auto_exposure=1, exposure_time_absolute=best_ex[0])
    cv2.setTrackbarPos("auto_exp", WIN, 0); cv2.setTrackbarPos("exposure", WIN, best_ex[0])
    cv2.setTrackbarPos("auto_wb", WIN, 0); cv2.setTrackbarPos("wb_temp", WIN, best_wb[0])
    state["last"] = (0, best_ex[0], 0, best_wb[0])
    L, r, b = stats(grab())
    s = (f"{datetime.now():%F %T} | 자동 화면에 맞춰 고정: exposure {best_ex[0]}, wb {best_wb[0]} "
         f"(밝기 {L:.1f} vs 자동 {L0:.1f}, R/G {r:.3f} vs {R0:.3f}, B/G {b:.3f} vs {B0:.3f}) | {v4l2_get()}")
    print(s)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


VID = OUT.parent / "videos"
rec = {"writer": None, "path": None, "frames": 0}


def toggle_rec():
    if rec["writer"] is None:
        VID.mkdir(parents=True, exist_ok=True)
        k = len(list(VID.glob("clip_*.avi"))) + 1
        rec["path"] = VID / f"clip_{k:02d}.avi"
        # MJPG = 카메라가 보내는 형식 그대로라 화질 손실이 거의 없음 (대신 파일이 큼, 1분 약 150~200MB)
        rec["writer"] = cv2.VideoWriter(str(rec["path"]), cv2.VideoWriter_fourcc(*"MJPG"), 30, (1280, 720))
        rec["frames"] = 0
        print("● 녹화 시작:", rec["path"].name)
    else:
        rec["writer"].release()
        print(f"■ 녹화 끝: {rec['path'].name} ({rec['frames']}프레임, 약 {rec['frames'] / 30:.0f}초)")
        rec["writer"] = None


print("SPACE: 사진 저장 | r: 영상 녹화 시작/끝 | p: 설정 출력·기록 | q: 끝 | 사진:", OUT, "| 영상:", VID)

while True:
    ok, f = cap.read()
    if not ok:
        print("카메라 프레임 없음 (장치 번호 확인: v4l2-ctl --list-devices)"); break
    if rec["writer"] is not None:
        rec["writer"].write(f); rec["frames"] += 1
    view = cv2.resize(f, (960, 540))
    ae, ex, aw, wb = state["last"]
    info = f"saved {n} | exp {'AUTO' if ae else ex} | wb {'AUTO' if aw else wb}"
    cv2.putText(view, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    if rec["writer"] is not None:
        cv2.circle(view, (930, 25), 10, (0, 0, 255), -1)
        cv2.putText(view, f"REC {rec['frames'] / 30:.0f}s {rec['path'].name}", (600, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imshow(WIN, view)
    k = cv2.waitKey(1) & 0xFF
    if k == ord(" "):
        n += 1; p = OUT / f"train_{n:04d}.jpg"; cv2.imwrite(str(p), f); print("saved", p.name)
    elif k == ord("r"):
        toggle_rec()
    elif k == ord("p"):
        s = f"{datetime.now():%F %T} | next {n + 1:04d} | {v4l2_get()}"
        print(s)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(s + "\n")
    elif k == ord("q"):
        break
if rec["writer"] is not None:
    toggle_rec()
cap.release(); cv2.destroyAllWindows()
