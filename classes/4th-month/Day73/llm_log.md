date: 2026.11.18

# LLM · VLM · VLA 준비 일지 (11/18)

> 작성: 김혜민 · 2026-11-18 (수)

오늘은 **노트북에 Ollama 를 준비하고 LLM → VLM → VLA 가 어떻게 이어지는지 잡은 날**이에요.

- Ollama 를 `0.40.2` → `0.40.16` 으로 올리고, GPU (RTX 5060 Laptop 8GB) 를 Ollama 가 잡는지 확인
- LLM · VLM · VLA 는 "모든 걸 토큰으로 바꾸고 다음을 예측" 하는 한 구조에서 입력 · 출력만 바꾼 것
- 8GB VRAM 에 맞는 모델을 크기별로 정리하고 `gemma4` (e4b, 6.6GB) 하나만 받음
- `ollama run gemma4 --think=false` 로 돌려 보고 `ollama ps` 로 100% GPU 확인
- VLA 는 Ollama 로 못 돌림 → LeRobot · SmolVLA 쪽으로 가야 함
- 실습 대상은 TurtleBot3 Waffle Pi + OpenManipulator-X, ROS2 는 Lyrical

<br>

## 1. API

- API = 프로그램끼리 "이렇게 요청하면 이렇게 답한다" 고 정해 둔 약속. 안은 숨기고 쓰는 법만 공개
- 웹에만 있는 게 아님: `cv2.imread()` 같은 함수 사용법, ROS 토픽 · 서비스 메시지 형식도 API
- 같이 나오는 말: 엔드포인트 (요청 주소), API 키 (누가 요청했는지 확인하는 값, GitHub 에 올리면 안 됨), REST (GET · POST · PUT · DELETE), SDK (API 를 쉽게 쓰게 묶은 도구)
- 라이브러리 = 코드 묶음 (실체), API = 그걸 쓰는 방법 (약속)

<br>

## 2. Ollama 설치 · 하드웨어 점검

- 처음엔 GPU 에서 `stand_loop.py` (stand_sB 평가 영상) 가 돌고 있어서 VRAM 4.3GB 사용 중 → 멈춘 뒤 VRAM 108MB 로 비워짐
- 일시 정지 (`Ctrl+Z`) 는 프로세스가 남아서 **VRAM 을 계속 잡고 있음**. 종료해야 풀림
- 학습 (train) 은 가중치를 바꾸고 체크포인트를 남기고, 평가 (play) 는 가중치를 고정하고 영상 · 수치만 남김

| 항목 | 값 | 판단 |
|---|---|---|
| GPU | RTX 5060 Laptop, Ollama 가 본 여유 7.3GiB | ✅ |
| 드라이버 | 595.99 (550 이상 필요) | ✅ |
| RAM | 30GB | VRAM 이 모자라면 RAM 으로 넘어감 (느려짐) |

- Isaac Lab 시뮬과 로컬 모델은 동시에 돌리지 않기 (시뮬 4GB + 모델 3–6GB > 8GB)
- 클라우드 모델 (`:cloud`) 은 내 GPU 를 안 쓰지만 `ollama signin` · 사용량 크레딧이 필요

<br>

## 3. LLM → VLM → VLA

| | 입력 | 출력 |
|---|---|---|
| LLM | 텍스트 | 텍스트 |
| VLM | 이미지 + 텍스트 | 텍스트 |
| VLA | 이미지 + 텍스트 (+ 로봇 상태) | 로봇 행동 (관절 · 그리퍼) |

- LLM: 토큰화 → 임베딩 → Transformer (attention) → 다음 토큰 확률. 학습 목표는 "다음 토큰 맞히기" 하나
- VLM: 이미지를 patch 로 잘라 비전 인코더 (ViT · CLIP 계열) 로 이미지 토큰을 만들어 텍스트 앞에 붙임. LLM 본체는 그대로
- VLA: VLM 출력을 행동으로 바꿈. 두 방식
  - 행동을 구간으로 나눠 토큰처럼 예측 (OpenVLA, RT-2)
  - VLM 뒤에 행동 헤드 (diffusion · flow matching) 를 붙임 (π0, GR00T, SmolVLA)
- 지금까지 한 RL 정책도 "관측 → 행동" 정책. VLA 는 관측이 이미지 + 말이고, 보상 대신 시연을 따라 하며 배움
- 많이 쓰는 구성: LLM · VLM 이 "무엇을 할지" (상위 계획), VLA · RL 정책이 "어떻게 움직일지" (하위 제어)

<br>

## 4. 8GB 에 맞는 모델 고르기

- 필요한 VRAM ≈ **가중치 파일 + KV 캐시 (대화 길이에 비례) + CUDA 오버헤드 약 0.5GB**
- 약 5GB 이하는 GPU 에 다 올라감, 5–6.6GB 는 짧은 대화면 다 올라감, 7.5GB 이상은 일부가 CPU 로 넘어가 느려짐
- 빠른 실습용: `qwen3.5:4b`, `qwen3-vl:4b` (3.3GB). 기능 최대 (한계선): `gemma4` (e4b, 6.6GB)
- VLA 후보: SmolVLA (약 0.45B, 8GB 로 파인튜닝까지 가능), π0 · GR00T (약 3B, 추론 위주), OpenVLA (7B, 노트북으로는 어려움)

<br>

## 5. gemma4 받고 돌려 보기

- 비교만 하려던 `gemma4` vs `gemma4:12b` 를 묻지 않고 둘 다 받기 시작 → 바로 멈춤. `gemma4` 만 다시 받음 (`12b` 는 안 받음)
- `ollama show gemma4`

| 항목 | 값 | 뜻 |
|---|---|---|
| parameters | 7.5B | 이름의 e4b = 계산에 쓰는 크기 약 4B (Per-Layer Embedding) |
| quantization | Q4_K_M | 가중치를 약 4bit 로 압축 |
| context length | 131072 | 최대 약 128K 토큰 |
| capabilities | vision, audio, tools, thinking | |
| projector | clip, 478M | 이미지를 LLM 이 읽는 벡터로 바꾸는 비전 인코더 |

- `ollama run gemma4 --think=false` → `ollama ps`: `100% GPU`, CONTEXT 4096, VRAM 8.1GB 중 4.7GB
- `UNTIL` 은 입력이 없으면 모델을 VRAM 에서 내리는 시간 (기본 5분, `--keepalive 30m` 으로 늘림)
- `ollama ps` 의 SIZE 는 실제 VRAM 과 다르게 나와서 `nvidia-smi` 로 확인
- 대화창 명령: `/set verbose` (tok/s 표시), `/set nothink`, `/set parameter temperature 0`, `/clear`, `/bye`

<br>

## 6. 터틀봇으로 할 때 해야 할 일

- 노트북에 Lyrical 패키지 설치 완료: MoveIt, ros2_control, Dynamixel hardware interface, `open_manipulator` (apt)
- `turtlebot3` · `turtlebot3_manipulation` 은 Lyrical apt 가 없어서 jazzy 브랜치 소스 빌드
- 모델은 파이에서 못 돌림 → **로봇은 손발, 노트북은 뇌** (ROS2 로 이미지 · 관절 상태를 받고 명령을 보냄)
- 순서: 로봇 입출력 · 카메라 고정 → 동작을 함수로 만들어 LLM tool calling → VLM 상태 판정 + 평가 사진 셋 → 원격 조종으로 시연 녹화 (작업당 50 에피소드 이상) → ACT → SmolVLA
- 처음엔 로봇을 고정하고 팔만

<br>

## 다음 할 일

- [ ] OpenCR 펌웨어 확인 후 bringup 성공시키기 ([파이 연결 일지](pi_log.md))
- [ ] `/set verbose` 로 gemma4 속도 (eval rate) 재 보기
- [ ] VLM 에 사진 넣어 판정해 보기
- [ ] 리더 암이 수업 장비에 있는지 확인
