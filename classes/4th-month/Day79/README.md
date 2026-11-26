Date: 2026 Nov 26, Thursday

## 오늘 배운 것
- (강의) ReAct 실행기는 생각 → 도구 호출 → 관측을 반복하고, 끝날 때 종료 이유 (photo_saved · outside_threshold · budget_exhausted · unknown_tool · timeout) 를 남긴다
- (강의) 호출 예산 = 도구를 부를 수 있는 최대 횟수. timeout 은 거리를 "모르는" 것이라 0m 같은 가짜 값을 넣으면 안 된다
- 다이나믹셀은 한 바퀴를 4096 눈금으로 읽고 2048 이 정면 (0 rad). 위치 모드 (OpMode 3) 의 Homing Offset 은 ±1024 (±90°) 까지만 돼서 180° 어긋난 건 혼을 다시 끼워야 한다
- 펌웨어를 올려도 모터 설정 (ID · Homing · OpMode) 은 각 모터 EEPROM 에 그대로 남는다
- 업로더는 파일로 고른다: `.opencr` → `opencr_ld_shell`, `.bin` → `opencr_ld`
- 작은 LLM (1.5B) 은 프롬프트 예시 숫자를 베끼기도 한다. 위험한 조건은 코드로 검사해야 한다
- 학교 와이파이에서는 ROS2 자동 탐색이 안 될 수 있다 → `ROS_STATIC_PEERS=<파이 IP>`
- RViz MoveIt 드롭다운이 안 먹던 건 Qt6 에서 생긴 MoveIt 버그. ROS 패키지는 일부만 올리면 버전이 섞여 깨진다



<br>

## 오늘 한 것 

- 강의 자료: [13강. ReAct와 Tool Use (드라이브 PPT)](https://docs.google.com/presentation/d/16Anjh3qNQQir5wTxjD1Pa__6dpp8TdKWQFrltp_H12A/edit) · [실습 코드 (GitHub lessons/13-react)](https://github.com/SpartaPA/waffle-mpx-lyrical/tree/main/lessons/13-react)
- [ReAct · Waffle MPX 일지 (11/26)](react_log.md)
- 13강 ReAct와 Tool Use 수업 (호출 예산, timeout 질문)
- pa06 팔 joint1 혼 180° 재조립, OpMode 4 → 3, manipulation 펌웨어 복구, 관절 한계 · home 자세 수정
- 13강 실습 (Qwen2.5 1.5B · SmolVLM2 · VLA) 을 Isaac Sim 6.1 에서 실행: 촬영 · 촬영 생략 · 전진 · 빨강 / 파랑 블록 집기
- MoveIt2 mock → 실물 실행, 팔 떨림 줄이기
- 실물 자연어 명령 · 퍽 인식 · gemma4 ReAct 에이전트 (`~/waffle_mpx/real_react/`) 만들기



<br>

## 문제점
- joint1 이 정면인데 ±3.1 rad 로 읽혀 arm_controller 가 안 켜짐
- 브리지 펌웨어 업로드 `[NG] not opencr fw`
- MoveIt RViz 에서 home · gripper open/close 가 안 고름
- MoveIt 패키지만 올렸더니 `undefined symbol` 에러
- 실물 팔이 움직일 때 떨림 (제어 루프 7Hz)
- 노트북 스크립트가 파이의 `/odom` · `/scan` 을 못 받음
- 팀 YOLO 모델이 파란 퍽을 못 찾음



<br>

## 해결 방법

- 팔은 그대로 두고 joint1 혼만 180° 돌려 다시 조립 → 눈금 2034 (-0.021 rad)
- `.bin` 은 `opencr_ld` 로 올림
- ROS 패키지 전체 업그레이드 후 waffle_mpx 다시 빌드
- 모터 프로파일 0/0 으로 바꿔 움직일 때 떨림 줄임
- `ROS_STATIC_PEERS=10.2.150.176`
- 색 (HSV) + 깊이로 퍽 찾기



<br>

## 결과

- 컨트롤러 5개 모두 active, 텔레옵 · MoveIt 실물로 팔 움직임
- 13강 실습 5개 모두 동작. 빨강 / 파랑 블록 집기 `success: true` (놓은 위치 오차 약 6mm)
- 에이전트는 계획 모드 (로봇 안 움직임) 에서만 확인. 실물은 아직



<br>

## 느낀 점

- 드디어 나의 자연어를 듣고 이해하고 수행한다! 이런 귀여운 로봇이 다 있나.. ㅋㅋ 근데 아직 손볼게 많다. 여러 부분에서 잘 수행이 안되고 보정해줄게 많다. 될때까지 해보면 되니까!!!



<br>

## 할 일

- 실물에서 `react_agent.py` 로 퍽 집기 · 쌓기 해 보기
- 팔 떨림: 프로파일 속도 30 / 가속 0 시험, 근본적으로는 제어 루프 속도 올리기
- 13강 `waffle_react.py` 비교 실험 (호출 예산 · 도구 오류 · timeout)
