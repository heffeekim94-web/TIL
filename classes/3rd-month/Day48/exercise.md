# SLAM → Nav2 실습 한 장 복습 (41~45강)

**목표:** 내가 만든 지도에서 로봇이 목적지에 도착하게 하기. **SLAM = 지도 만들기 / AMCL = 내 위치 찾기 / Nav2 = 길을 찾아 주행하기.**

> 수업 기준: Ubuntu 22.04 + ROS 2 Humble + TurtleBot3 burger·Gazebo house, 관련 패키지 설치 완료 상태. 현재 PC에는 Jazzy·Lyrical만 확인되어 아래 Humble 명령을 이 PC에서 실행 검증하지는 않았다. 수업용 Humble 환경에서 진행하고, 다른 배포판에서는 Gazebo·launch 구성을 먼저 확인한다.

## 1. 지도 만들고 저장하기 — 41강

터미널 4개를 열고 **각 터미널에서** 아래 준비 명령을 먼저 실행한다.

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
```

아래는 **각각 별도 터미널**에서 실행한다. 실행 중인 창은 유지한다.

```bash
# T1: 가상 로봇과 집
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
# T2: 지도를 만드는 SLAM
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
# T3: 지도·로봇을 보는 RViz
rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz --ros-args -p use_sim_time:=true
# T4: 키보드 조종 (화면에 표시되는 키 사용)
ros2 run turtlebot3_teleop teleop_keyboard
```

- [ ] RViz의 Fixed Frame을 `map`으로 확인한다. T4에서 **천천히 벽을 따라 한 바퀴 돌고 출발점으로 돌아온다.** 흰색=빈 곳, 검정=벽, 회색=아직 모르는 곳.
- [ ] 벽이 두 겹으로 보이지 않고 이동할 곳이 충분히 그려졌으면 로봇을 정지한다. T4의 조종을 `Ctrl+C`로 종료하고 저장한다.

```bash
mkdir -p "$HOME/maps"
ros2 run nav2_map_server map_saver_cli -f "$HOME/maps/house" --ros-args -p use_sim_time:=true
ls "$HOME/maps/house."*   # house.pgm + house.yaml 확인
```

## 2. 지도에서 내 위치 맞추기 — 42강

**T1·T3은 유지하고 T2의 SLAM만 `Ctrl+C`로 종료**한다. T2에서 아래 Nav2 전체 구성을 실행하면 지도 로드와 AMCL도 함께 시작된다. 별도 localization 실행은 필요 없다.

```bash
ros2 launch nav2_bringup bringup_launch.py map:=$HOME/maps/house.yaml use_sim_time:=true
```

- [ ] RViz **2D Pose Estimate**를 눌러 Gazebo 속 실제 로봇에 대응하는 지도 위치에서 바라보는 방향으로 드래그한다. 이것은 **출발 위치 설정**이다.
- [ ] 스캔 점들이 지도 벽에 겹치는지 확인한다. 필요하면 T4 조종을 다시 켜 조금 움직여 확인한 뒤, **정지하고 조종을 종료**한다. 파티클이 모여도 벽과 맞지 않으면 초기 위치를 다시 지정한다.

## 3. 목적지 → 여러 경유지 이동하기 — 43강

- [ ] RViz **Nav2 Goal**로 가까운 흰색 영역을 클릭·드래그한다. 이것은 **도착 위치·방향 지정**이다. 경로가 생기고 로봇이 도착해 멈추면 성공!
- [ ] Nav2 패널의 **Waypoint mode**가 있으면 켜고 `Nav2 Goal`로 A→B→C를 지정한 뒤 **Start Nav Through Poses** 또는 **Start Waypoint Following**으로 출발한다(표시는 버전에 따라 다름). 해당 기능이 없으면 A 도착 후 B, B 도착 후 C를 지정해 순서대로 복습한다. 이 대안은 자동 순찰과 구분한다.
- [ ] 먼저 가까운 지점, 다음은 다른 방, 마지막은 출발점으로 정한다. 수업 예제 좌표를 그대로 쓰지 말고 **내 지도의 빈 공간**을 선택한다.

## 4. 장애물 회피·튜닝 맛보기 — 44강

- [ ] 같은 경로를 다시 달리며 Gazebo 안에 박스를 놓아 우회를 관찰한다. 움직이는 장애물 실험은 수업의 액터 world 파일이 있을 때 별도로 한다.
- [ ] 튜닝하려면 기본 설정을 복사한다: `cp "$(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/params/nav2_params.yaml" "$HOME/maps/nav2_params.yaml"`. 복사본의 `local_costmap → local_costmap → ros__parameters → inflation_layer → inflation_radius` **한 값만** 바꾼다.
- [ ] T2를 종료하고 2번 실행 명령 끝에 `params_file:=$HOME/maps/nav2_params.yaml`을 붙여 재시작한다. 초기 위치를 다시 지정하고 같은 경로를 비교한다. `inflation_radius`는 장애물 주변 비용 영역의 크기이며, 충돌 여부는 로봇 크기·footprint도 함께 좌우한다. 우회가 줄어도 장애물에 너무 붙으면 원래 값으로 되돌린다.

## 5. 세 번 반복하고 기록하기 — 45강 축소 복습

매회 같은 출발 위치·방향과 A→B→C를 사용한다. **성공 = 전 지점 도착 + 충돌 없음 + 사람 개입 없음 + 미리 정한 제한 시간 이내.** 시간은 첫 목표 전송부터 마지막 도착까지 잰다.

| 회차 | 성공 O/X | 소요 시간(초) | 막힌 지점·원인 |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

성공률 = 성공 횟수 ÷ 3 × 100. **재계획(경로 다시 계산)**과 **리커버리(회전·후진·대기 등 복구 행동)**는 다르다. `/plan` 메시지 수에는 정상 주기 발행도 포함되므로 전부 장애물 재계획으로 세지 않는다. 3회는 복습용이며 수업의 20회 벤치마크를 대체하지 않는다.

**막히면:** 지도 없음 → `/scan`·시뮬레이션 시간 확인 / 위치 이상 → 초기 위치·방향 재설정 / 주행 안 됨 → `ros2 lifecycle get /amcl`, `ros2 lifecycle get /bt_navigator`가 `active`인지 확인. SLAM과 AMCL은 동시에 켜지 않는다.

**참고 그림:** [전체 실습 연결](pic/learning-flow.webp) · [성능 지표 정의](pic/metrics.webp). 그림은 원문 자료이며, 본문을 짧게 유지하기 위해 링크로 연결했다.

**출처·범위:** [모듈 ⑥ SLAM 및 Nav2 자율주행](https://app.notion.com/p/SLAM-Nav2-09579696939583ea967001fe919901e7)의 41~45강을 초보자용으로 축약. 그래프 직렬화·AMCL 납치 실험·Python 액션 코드·자동 벤치마크는 원문에서 이어서 진행한다. 그림 출처: 45강, TeamSparta.
