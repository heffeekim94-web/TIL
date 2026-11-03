# 11/02 수업: Jetson 에지 컴퓨팅과 실시간 배포 (63강 ONNX Runtime)

교재: Jetson 에지 컴퓨팅과 실시간 배포 · 63–69강 (ONNX · TensorRT · ROS 2 통합, Jetson Orin Nano Super). 오늘은 63강 ONNX Runtime 부분.

## 왜 PC 모델을 그대로 Jetson 에 못 올리나

- Jetson 은 **ARM(aarch64)** + 8GB 공유 메모리 → 학습 PC 와 환경이 달라서 그대로 올리면 성능이 떨어질 수 있음 → **배포 환경을 따로 만들어야 함**
- PyTorch 는 학습용(동적 그래프 · 자동미분)이라 추론에는 짐 → 추론만 남기면 고정된 연산 그래프가 되고, 고정 그래프는 공격적으로 최적화할 수 있음
- 역할 나누기: PC = 시뮬레이션 · 학습, Jetson = 추론 · ROS 2, MCU = 주기 제어 · 타임아웃
- **양자화** = 모델을 우리가 가진 보드에서 잘 돌도록 축소하는 것 → 에지 컴퓨팅에서 해야 하는 일

## 이름 구분

| 이름 | 무엇인가 | 역할 |
|---|---|---|
| PyTorch | 학습 프레임워크 | 학습된 모델 · 기준 출력 |
| ONNX | 연산 그래프 + 가중치 교환 형식 ("모델이 이 구조로 되어 있다"는 표준 도면) | PC → Jetson 전달 형식 |
| ONNX Runtime | ONNX 실행기 | CPU · CUDA · TensorRT EP 로 실행, 변환 검증 기준선 |
| TensorRT | NVIDIA 추론 최적화 SDK (GPU 코어에 맞춘 실행 계획) | 대상 GPU 에서 엔진(.plan) 빌드 |

- ONNX 는 전달 형식일 뿐 속도 향상을 보장하지 않음. **변환 성공 ≠ 같은 결과** → 같은 입력으로 원본 · ORT 출력 비교 필요
- TensorRT 엔진은 그 GPU 용 계획이라 **PC 에서 만든 엔진을 Jetson 에 바로 쓸 수 없음** → ONNX 를 Jetson 으로 옮겨서 거기서 빌드
- 수업 방향: 우선 ONNX Runtime 까지 해 봄

## ONNX 파일 안에 있는 것

- ModelProto(IR 버전 · opset) → GraphProto(입력 · 출력 · 노드 · initializer) → NodeProto(Conv · MatMul 등 연산) / TensorProto(가중치) / ValueInfoProto(입출력 이름 · dtype · shape)
- 입출력 계약을 표로 고정: 입력 shape · dtype · RGB/NCHW · letterbox + 0–1 정규화 · 출력 형태 · conf/IoU/NMS → 하나라도 바뀌면 다른 시스템
- `onnx.checker.check_model` 로 구조 검사 후 opset · 입력 이름 · initializer 수 출력해서 확인

## 그래프 최적화 (정확도는 그대로, 속도만)

- **상수 접기**: 실행 전에 값이 정해지는 부분을 미리 계산해 상수로 바꿈
- **연산자 융합**: Conv → BatchNorm → ReLU 를 커널 하나로. 이득은 계산이 아니라 **메모리 왕복 감소** (중간 결과를 DRAM 에 썼다 읽는 비용). BN 은 추론 때 Conv 가중치에 흡수됨
- **레이아웃 · 중복 최적화**: NCHW ↔ NHWC, 죽은 노드 · Transpose 쌍 제거
- `SessionOptions.graph_optimization_level = ORT_ENABLE_ALL`

## 실행 공급자(EP)

- 같은 그래프에 백엔드만 갈아 끼움: `providers=["CUDAExecutionProvider", "CPUExecutionProvider"]`
- GPU 가 목록에 있어도 모든 연산이 GPU 에서 도는 건 아님 → 지원 안 되는 연산은 **CPU fallback** → 그래프 중간에 끼면 GPU ↔ CPU 복사 + 대기 발생 → 프로파일로 어느 노드가 어느 EP 인지 확인

## 측정 기본기

- 워밍업 제외 (첫 실행은 커널 준비 · 메모리 할당으로 훨씬 느림)
- 평균 말고 분포로: P50 / P95 / P99
- 조건을 같이 적기: 배치 · shape · EP · 전원 모드
- 정합 체크: 구조(checker) → 수치(같은 입력 abs/rel 오차) → 과제(같은 test mAP) → 실행(EP 프로파일) → 제출(ONNX · 해시 · 환경 · 로그)

## 우리 프로젝트와 연결

- 10/30 경량화 비교가 이 순서였음: 같은 test 52장 · 같은 후처리로 PyTorch / ONNX FP32 · FP16 · INT8 비교, 워밍업 20회 후 평균 · p99 → ONNX FP16 채택
- INT8 은 Detect 층까지 int8 로 하면 mAP 0 → 민감한 층은 높은 정밀도 유지 (교재 64강 "혼합 정밀도 · 민감 층" 과 같은 얘기)
- 다음: Jetson 에서 ONNX → TensorRT FP16 엔진 빌드 (11/03 수업 양자화)

---

# 11/02 실습에서 배운 것

## 1. 신호등 색은 "색"이 아니라 "칸별 밝기"로 판정한다

- 신호등 렌즈는 꺼져 있어도 빨강 · 노랑 · 초록 색이 보임 → HSV 의 색(H)으로 판정하면 꺼진 불도 켜진 걸로 착각
- 그래서 YOLO 가 찾은 신호등 상자를 위에서 아래로 칸을 나누고(red 10–40%, yellow 40–70%, green 70–100%, 가로는 가운데 25–75%만), 칸마다 **밝기(V)의 90 분위수**를 점수로 씀
  - 평균 대신 90 분위수: 켜진 램프는 칸의 일부만 밝아서 평균은 묻힘, 최댓값은 반사 한 점에 흔들림
- 가장 밝은 칸이 두 번째보다 `v_margin`(40) 이상 밝아야 그 색, 아니면 **OFF**
- 한 장으로 확정하지 않고 최근 5장 중 3장이 같아야 확정(다수결) → 깜빡임 · 한 장 오검출에 강함
- **Visible YES 인데 OFF** = 상자는 찾았는데 밝기 차가 기준을 못 넘은 것. 원인을 나누는 순서:
  1. 한 색을 계속 켜 둔다 (점멸 영향 제거)
  2. 그래도 OFF 면 상자 위에 칸 경계와 칸별 점수를 그려 본다 (칸 위치 · 자동 노출 확인)
  3. 그다음에야 칸 비율이나 v_margin 을 바꾼다 (기준부터 낮추면 꺼진 불도 켜졌다고 나옴)

## 2. 릴레이는 LOW 가 켜짐일 수 있다

- 신호등 OpenCR 코드(sign_tower.ino)는 릴레이 핀 5 · 6 · 7 에 `digitalWrite(pin, LOW)` 로 켜고 `HIGH` 로 끔 (active-low 릴레이 모듈)
- 코드를 고칠 때 "켜기 = HIGH" 로 생각하면 반대로 동작하니 원래 코드부터 확인
- 시리얼 명령으로 상태를 바꾸면(r/y/g/o/a) `loop()` 안에서 `delay(3000)` 로 도는 대신 명령이 올 때까지 상태를 유지할 수 있음

## 3. SSH X 포워딩 화면이 느린 이유

- `ssh -Y` 로 띄운 OpenCV 창은 프레임 픽셀을 통째로 네트워크로 보냄 → 원본 크기면 탐지가 빨라도 화면은 10 Hz 이하
- 보여 주는 화면만 `cv2.resize(frame, (640, 360))` 으로 줄이면 약 15 Hz. 탐지 입력은 그대로라 결과에는 영향 없음
- 영상과 탐지 결과는 `message_filters.TimeSynchronizer` 로 같은 시각(header.stamp)끼리 묶어야 상자가 다른 프레임 위에 그려지지 않음
