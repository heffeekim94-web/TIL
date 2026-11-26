date: 2026.11.20

# SmolVLA 설치 · 실행 일지 (11/20)

> 작성: 김혜민 · 2026-11-20 (금)
> 참고 자료: [튜터님 가이드 (velog SmolVLA)](https://velog.io/@roboticsmaster/SmolVLA) · [논문 PDF (드라이브 Research papers)](https://drive.google.com/drive/folders/12683e-ywY8Bg8cwTTH4qqdTiIgTcC7m0)

오늘은 **튜터님 가이드 (velog SmolVLA) 를 따라 LeRobot · SmolVLA 를 처음 설치하고, 로봇 없이 어디까지 돌릴 수 있는지 확인한 날**이에요.

- 시스템 파이썬에 `pip install` → `externally-managed-environment` → 가상환경 (`~/vla/.venv`) 을 만들어 해결
- `~/vla/lerobot` 클론, `pip install -e ".[smolvla]"` 로 LeRobot 0.7.1 설치
- 2-A 공식 예제 실행 → 모델 2개 (SmolVLM2 2.03GB, `smolvla_base` 907MB) 받고 `mps` 오류로 멈춤
- 2-A 는 SO-100 실물 로봇이 있어야 끝까지 돎. 로봇 없이 VLA 를 눈으로 보는 단계는 4-A (LIBERO)
- 4-A 는 `libero` 가 환경에 설치되지 않아 아직 영상이 안 나옴

<br>

## 1. 가상환경

- 우분투 24.04 의 시스템 파이썬은 `pip install` 을 막음 (`externally-managed-environment`). apt 패키지와 꼬이지 않게 하려는 것
- 해결: `python3 -m venv .venv` → `source .venv/bin/activate` → 프롬프트에 `(.venv)` 가 붙은 상태에서 설치
- `(.venv)` 가 없는 터미널에서 실행하면 다시 시스템 파이썬으로 감
- 지금 환경은 `~/vla/.venv`, `--system-site-packages` 없이 만듦 → LIBERO 는 괜찮지만 나중에 ROS 2 (`rclpy`) 단계에서는 다시 만들어야 함

<br>

## 2. bash 와 python 은 다른 곳에 친다

- 가이드의 ```` ```python ```` 코드를 터미널 (`$`) 에 붙여서 `Command 'import' not found`
- `bash` 블록 = 터미널 명령, `python` 블록 = `python` 을 켜고 `>>>` 에서 입력 (또는 `.py` 파일로 저장해 실행)
- 가이드 2번의 두 부분

| | 2-A 공식 예제 | 2-B 코드 조각 |
|---|---|---|
| 블록 | bash | python |
| 성격 | 실행하는 명령 | "이렇게 부르면 된다" 는 참고 |
| 그대로 실행하면 | SO-100 로봇 연결에서 멈춤 | `observation` 이 없어서 오류 |

<br>

## 3. 2-A 예제 실행 (`using_smolvla_example.py`)

- 받은 모델
  - `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` (2.03GB): VLM 바탕
  - `lerobot/smolvla_base` (907MB): VLM 에 행동 헤드를 붙인 VLA. 나중에 파인튜닝할 때 씀
  - 로그의 `Reducing the number of VLM layers to 16` = SmolVLA 는 VLM 앞쪽 16층만 써서 가볍게 만듦
- → **VLA = VLM + 행동 출력** 이 실제 파일 두 개로 보임
- 멈춘 이유: `Requested device 'mps' but MPS is not available`. `mps` 는 Mac GPU 전용. 리눅스는 `cuda`
- `cuda` 로 고쳐도 다음 줄 `robot.connect()` 에서 멈춤 (`follower_port = ...` 빈칸, 로봇 없음)
- 예제 흐름: 관측 받기 → `preprocess` → `select_action` → `postprocess` → `send_action` 반복
- 받은 모델은 `~/.cache/huggingface/` 에 남아서 다음엔 다시 안 받음
- `HF_TOKEN` 경고는 로그인 없이 받아서 속도 제한이 있다는 뜻 (오류 아님, 약 2MB/s)

<br>

## 4. Traceback 읽는 법

- **맨 아래 줄이 진짜 원인**, 위쪽은 어떤 함수를 거쳐 왔는지 경로
- `$( ... )` 는 안쪽 명령의 결과를 그 자리에 끼워 넣는 bash 문법. 안쪽 `find` 가 실패하면 바깥 `xdg-open` 에 빈칸이 들어가 사용법만 출력됨

<br>

## 5. 4-A LIBERO (로봇 없이 VLA 보기)

```
pip install -e ".[libero]"     → LIBERO 시뮬레이터 설치
export MUJOCO_GL=egl
lerobot-eval --policy.path=HuggingFaceVLA/smolvla_libero --env.type=libero \
  --env.task=libero_object --eval.batch_size=1 --eval.n_episodes=2 \
  --policy.device=cuda --output_dir=outputs/eval/smolvla_libero_test
xdg-open $(find outputs/eval/smolvla_libero_test -name "*.mp4" | head -n 1)
```

- 앞 단계가 성공해야 다음 단계가 됨 (설치 → 평가 + mp4 생성 → 영상 열기)
- 확인 결과: `~/vla/.venv` 에 `libero` · `mujoco` · `robosuite` 가 없음, `outputs/` 없음, `smolvla_libero` 도 안 받아짐
- `pip install --dry-run` 으로는 막히는 것 없이 설치된다고 나옴 → 설치가 이 환경에 반영 안 된 상태. 다른 터미널 (`(.venv)` 없음) 이나 중간에 끊겼을 가능성
- 설치 확인: `python -c "import libero, mujoco; print('LIBERO OK', mujoco.__version__)"`

<br>

## 6. 가이드 새로 고침 후 바뀐 점

- 4-A: `--output_dir` 이 `outputs/eval/smolvla_libero_test` 로 바뀌고, 영상 여는 3단계가 추가됨
- 뒷부분: 4-B Isaac Sim 6.1 + ROS 2 연동 (SmolVLA 노드와 Isaac Sim 을 다른 환경에서 띄우고 ROS 2 토픽으로 주고받음), 5 SO-100 leader · follower 로 데이터 수집, 6 명령어 요약
- 4-B 용 `~/vla/isaac_smolvla/` 파일은 아직 이 컴퓨터에 없음
- 가이드 오타로 보이는 것: `lerobot/smolvlabase` → `smolvla_base`, `so100follower` → `so100_follower`, `<아이디>/<데이터셋이름>` 의 `<` 빠짐

<br>

## 다음 할 일

- [ ] `(.venv)` · `~/vla/lerobot` 확인하고 `pip install -e ".[libero]"` 다시 → `Successfully installed` 확인
- [ ] `lerobot-eval` 돌려서 mp4 영상 보기
- [ ] 수업에서 SO-100 로봇팔을 받는지 확인 (받으면 2-A · 5 · 3)
- [ ] 4-B 용 파일 받으면 `--system-site-packages` 환경 새로 만들기
