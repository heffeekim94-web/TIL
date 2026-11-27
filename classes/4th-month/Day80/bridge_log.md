date: 2026.11.27

# Waffle MPX 실물 · 브리지 일지 (11/27)

> 작성: 김혜민 · 2026-11-27 (금)
> 강의 자료: [14–18강. 명령 계약에서 통합 플래너 평가까지 (드라이브 PPT)](https://docs.google.com/presentation/d/13_NL2CNK8UfdWzd97lj0munzRF9M9JANiDLQ5iBY8wI/edit) · [실습 코드 (GitHub feature/open-instruction-vla)](https://github.com/SpartaPA/waffle-mpx-lyrical/tree/feature/open-instruction-vla)

오늘은 **프로젝트 3 (D팀_AUTOBOT) 을 시작하고, 튜터님의 실물 자유 지시 실행기를 와이파이에서 돌리려고 카메라 브리지를 만든 날**이에요.

- 프로젝트 3 팀 구성 · 역할 분담. 내 역할은 RAG model
- pa06 bringup: `source` 빠짐, `lidar_port` 오타 → 고쳐서 컨트롤러 5개 active
- 팀원의 RM-X52 메시를 우리 관절 한계를 지키면서 노트북에 합침
- 튜터님 새 브랜치 준비: Qwen2.5 7B 받기, 장치 없는 테스트 3개 통과
- 와이파이로 카메라 원본이 안 옴 → 압축 브리지로 4.4Hz, 지연 0.17초

<br>

## 1. 프로젝트 3 시작 (D팀_AUTOBOT)

- [팀 노션](https://app.notion.com/p/teamsparta/D-_AUTOBOT-4252dc3ef51480869660cfa94f43ff3e)
- 역할: 심규진 (통합) · 김혜민 (RAG model - 정책, Dataset 모으기, pipeline, skill) · 송정혁 (Isaac Sim, RL · IL) · 정수용 (Local LLM Fine-Tuning)
- 공통 목표: 최적화 (가볍게, 빠르게, 안정적이게)
- 노션에 매일 개인 일지 · 회의록 작성
  - 팀스파르타 노션에서 나는 게스트라 Notion MCP 연결은 안 됨. 대신 크롬으로 페이지를 열어 읽기 확인

<br>

## 2. pa06 다시 켜기

- 새 IP `10.2.150.93` (MAC 으로 찾고 호스트 키 지문으로 확인), `~/.ssh/config` 수정
- `~/waffle_mpx/install/setup.bash` 만 치면 `Permission denied` → 앞에 `source`
- 첫 bringup 은 `lidar_port:=/dev/ttyACM0` 오타
  - `ttyACM0` = OpenCR (팔 · 바퀴), `ttyUSB0` = 라이다
  - 라이다 드라이버가 OpenCR 포트를 같이 열어 `Incorrect status packet` → `Failed to 'activate' hardware`
  - 포트 기본값이 이미 맞아서 `mode:=hardware` 만 줘도 됨
- 다시 실행 → arm · gripper · diff_drive · imu · joint_state 5개 active, 카메라 사진도 정상 (어제 팔이 떨어져 부딪힌 영향 없음)
- 끄기 전엔 팔이 세워져 있으면 손으로 받친 뒤 `Ctrl+C`

<br>

## 3. `real_react` 코드 보기

| 파일 | 줄 수 | 역할 |
|---|---|---|
| `react_agent.py` | 167 | 두뇌. gemma4 가 생각 → 기술 고르기 → 결과 보기 반복 |
| `pick_puck.py` | 285 | 기술 (pick · place_on · put_down, 다가가기, MoveIt) |
| `find_puck.py` | 145 | 눈. 카메라에서 색으로 퍽 찾기 |

- 어제 무한 반복 원인
  1. `find_puck` 이 "못 찾음" 을 stderr 로 내보내는데 stdout 만 읽음 → 실패 이유 없이 계속 재시도
  2. 카메라가 왼쪽 (y = +3cm) 에 달려 있어 가까이 가면 오른쪽 퍽이 화면 밖으로 나감
- 코드 읽는 법: 이름만 훑기 (docstring, 대문자 상수, `Ctrl+Shift+O`) → 질문 하나 들고 호출 따라가기
  - `main()` → `ask_llm()` → `run_tool()` → `pick()` → `approach()` → `look_closer()` → `detect()`
  - 첫 과제: `react_agent.py` 의 `run_tool()` — LLM 은 고르기만 하고 실제 동작은 코드가 함

<br>

## 4. 팀원 RM-X52 메시 합치기

- [SpartaPA/waffle_rmx52_261127](https://github.com/SpartaPA/waffle_rmx52_261127): 팔 메시를 RM-X52 실물 CAD 로, 라이다를 LDS-03 모양으로. 관절 위치 · 한계 · ros2_control 은 그대로
- README 대로 overlay 하면 원본 (9fbf0c1) 을 복사한 거라 어제 넓힌 관절 한계와 떨림 설정이 되돌아감
- 그래서 노트북 `~/waffle_mpx/src/turtlebot3_manipulation_description/` 에 메시만 합침
  - `meshes/rm_x52/`, `meshes/lds03/` 추가
  - `open_manipulator_x.urdf.xacro` 는 팀원 버전 + 우리 한계 (joint2 하한 -0.7π, joint3 상한 0.5π)
  - `turtlebot3_waffle_pi.urdf.xacro` 는 팀원 버전 (LDS-03)
- 빌드 · URDF 검사 · 새 충돌 메시로 home 자세 충돌 검사 통과. 파이는 그대로 (메시는 RViz · MoveIt 에만 쓰임). RViz 로 모양 확인은 아직

<br>

## 5. 튜터님 실물 자유 지시 실행기

- `git pull` 결과 `4aea4b4..2bc9bbe feature/open-instruction-vla` + `Already up to date` → 새 커밋은 다른 브랜치에 있었음
- 새 브랜치 내용: `lessons/13-react/free_command.py --backend hardware` · `hardware_command.py`, `lessons/14-18/` 교안, 다시 학습한 VLA 체크포인트

| | 튜터님 `free_command.py` | 우리 `react_agent.py` |
|---|---|---|
| LLM | Qwen2.5 7B (먼저 순서 계획 → 단계별 실행) | gemma4 (한 턴씩 ReAct) |

- 준비: Qwen2.5 7B (4.7GB) 받기, VLA 워커 로드 확인, `test_hardware_command.py` 3개 통과
- 두 컴퓨터 시계 차이 약 0.1초 (코드가 0.4초 넘게 늦은 프레임은 버림)
- 이 경로는 MoveIt 충돌 검사 없이 관절 목표를 바로 보냄 → 로봇 옆에서 지켜보기

<br>

## 6. 와이파이 카메라 브리지

첫 실행 (`작업대 사진을 한장 찍고 종료해`) 에서 에러. 20초 동안 받은 메시지 수:

| 토픽 | 파이 안 | 노트북 (와이파이) |
|---|---|---|
| RGB 원본 | 251개 / 0.06초 | **0개** |
| 깊이 원본 | 274개 / 0.06초 | **0개** |
| `camera_info` | 289개 / 0.06초 | 41개 / 1.1초 지연 |

- 해결 후보: 랜선 직접 연결 / 압축 브리지 → 브리지로 감

```
[파이] D435 원본 ──pi_relay.py──▶ JPEG/PNG 압축, 초당 5장 (한 묶음 약 190KB)
                                   │ 와이파이 (도메인 63, 재전송 켬)
[노트북] laptop_bridge.py ◀────────┘ 압축 풀어 원래 토픽 이름으로 다시 내보냄
                                   │ 노트북 안 (도메인 93)
         튜터님 hardware_command.py ◀┘   팔 · 집게 · 바퀴 명령은 반대 방향
```

- 처음엔 카메라 1.1Hz → 와이파이 구간 재전송 켜고 노트북 수신 버퍼 키움 (`FASTDDS_BUILTIN_TRANSPORTS`)
- 카메라 TF 15개 중 11개만 옴 (카메라 노드가 내보내는 4개 빠짐) → 파이에서 tf_static 을 모아 2초마다 다시 보냄

| | 와이파이 직접 | 브리지 |
|---|---|---|
| RGB / 깊이 | 0개 | 4.4Hz, 지연 0.17초 |
| TF | — | 15개 모두 |
| joint_states / odom | 정상 | 정상 (0.02초) |

- 튜터님 코드는 한 줄도 안 고치고 `observe()` 로 팔 관절값 (home) · 카메라 사진 정상
- 파일: 노트북 `~/waffle_mpx/real_react/laptop_bridge.py` · `pi_relay.py`, 파이 `~/real_react/pi_relay.py`
- 끌 때는 실행기 → 브리지 → 릴레이 순서 (브리지를 끄면 팔 · 바퀴 명령도 끊김)

<br>

## 7. 역정규화 (질문)

- 학습 때 `a_norm = (a − μ)/σ` → 실행 때 `a = a_norm·σ + μ`
- μ · σ 는 학습 데이터에서 구한 값을 모델과 같이 저장해서 씀. 실행 때 다시 계산하면 행동 크기가 엉뚱해짐
- 정규화하는 이유: 관절마다 단위 · 범위가 달라 큰 값 축만 손실을 키움
- SmolVLA 예제의 `preprocess` (관측 정규화) → `select_action` (정규화된 행동) → `postprocess` (역정규화)
- 최소 / 최대 [-1, 1] 방식이면 `a = (a_norm + 1)/2 · (max − min) + min`

<br>

## 다음 할 일

- [ ] 브리지로 튜터님 실행기 실물 실행 (사진 → 팔 · 바퀴 명령 전달 확인)
- [ ] 튜터님 방식과 `react_agent.py` 결과 비교
- [ ] RViz 에서 RM-X52 메시 모양 확인
- [ ] 프로젝트 3: RAG 정책 · 데이터셋 모으기
