Date: 2026 Nov 20, Friday

## 오늘 배운 것
- 우분투 시스템 파이썬엔 `pip install` 이 막혀 있다. 가상환경 (`venv`) 을 만들고 `(.venv)` 가 붙은 상태에서 설치한다
- 가이드의 `bash` 블록은 터미널에, `python` 블록은 파이썬 안에서 친다
- SmolVLA 는 SmolVLM2 (VLM) 앞쪽 16층 + 행동 헤드다. 받은 모델 두 개가 VLA = VLM + 행동 출력 구조를 그대로 보여 준다
- `mps` 는 Mac 전용 GPU. 리눅스에선 `cuda`
- Traceback 은 맨 아래 줄부터 읽는다. `$( )` 안쪽이 실패하면 바깥 명령엔 빈칸이 들어간다
- 로봇 없이 VLA 동작을 보려면 시뮬레이터 (LIBERO) 로 평가하고 영상을 본다
- (자료) RT-2 는 행동을 텍스트 토큰으로 바꿔 VLM 과 같이 학습하고, OpenVLA 는 Open X-Embodiment 97만 에피소드로 학습한 7B 공개 VLA, SmolVLA 는 작은 VLM + flow matching 행동 전문가 (action expert) 로 한 GPU 에서 학습 가능한 VLA



<br>

## 오늘 한 것 

- [SmolVLA 설치 · 실행 일지 (11/20)](smolvla_log.md)
- 튜터님 가이드 (velog SmolVLA) 따라 `~/vla` 에 LeRobot 클론 · 가상환경 · `[smolvla]` 설치
- 2-A 공식 예제 실행 → SmolVLM2 · `smolvla_base` 모델 받음
- 4-A LIBERO 평가 시도
- 드라이브에 RT-2 · OpenVLA · SmolVLA 논문 PDF 추가



<br>

## 문제점
- 시스템 파이썬에서 `pip install` → `externally-managed-environment`
- python 코드를 터미널에 붙여 `Command 'import' not found`
- 2-A 예제가 `Requested device 'mps' but MPS is not available` 로 멈춤
- 4-A 후 `outputs/` 폴더와 mp4 가 없음



<br>

## 해결 방법

- `python3 -m venv .venv` → `source .venv/bin/activate`
- `bash` 와 `python` 블록 구분
- 2-A 는 SO-100 로봇이 있어야 끝까지 돌아서 로봇 없이 볼 수 있는 4-A 로 넘어감
- 4-A 는 `libero` 가 환경에 없는 것까지 확인 (설치부터 다시 해야 함)



<br>

## 결과

- LeRobot 0.7.1 · torch 설치, SmolVLM2 (2.03GB) · `smolvla_base` (907MB) 다운로드 완료
- LIBERO 미설치로 시뮬레이션 영상은 아직 없음



<br>

## 느낀 점

- 



<br>

## 할 일

- `pip install -e ".[libero]"` 다시 → `lerobot-eval` → 영상 보기
- SO-100 로봇팔 받는지 확인
- RT-2 · OpenVLA · SmolVLA 논문 읽기
