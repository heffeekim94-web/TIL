haeminkim-legion-pro-5-16iax10 · 2026-10-13 점검

# Waffle SLAM 환경 점검 기록

waffle-lyrical-slam 저장소 기준으로 Isaac Sim, ROS 2 Lyrical, Gazebo, Cartographer, cuVSLAM이 제대로 설치·빌드됐는지 확인한 결과예요. 다음 세션에서 이어갈 때 이 페이지부터 보면 돼요.

## 최종 상태

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| Isaac Sim 6.1.0 | 정상 | `~/Documents/IsaacSim/6.1.0`, 빌드 `6.1.0-rc.26`. 실행은 `./isaac-sim.sh` |
| ROS 2 Lyrical | 정상 | `/opt/ros/lyrical`, 패키지 270개. Jazzy도 같이 설치돼 있음 |
| Gazebo · ros_gz | 정상 | gz sim 10.5.0, ros_gz_bridge / sim / image |
| Cartographer | 정상 | 워크스페이스에서 빌드 (`cartographer`, `cartographer_ros`, msgs, rviz) |
| Waffle 워크스페이스 | 정상 | 시뮬레이션용 빌드 완료. 실물 로봇용 6개는 의도적으로 제외 |
| Isaac ROS 5.0 cuVSLAM | 정상 | apt `ros-lyrical-isaac-ros-cuvslam` 5.0.0, 실행 파일 `isaac_ros_cuvslam`, launch 7개 |

## 환경 정보

- Ubuntu 24.04.5 (noble), RTX 5060 Laptop, 드라이버 595.99.02
- 워크스페이스: `~/workspaces/waffle-lyrical-slam` (GitHub [SeongminJaden/waffle-lyrical-slam](https://github.com/SeongminJaden/waffle-lyrical-slam)), `~/workspaces/isaac_ros-dev`
- Docker 이미지: `nvcr.io/nvidia/isaac/ros:isaac_ros_054e16b5…-amd64`, `cached_isaac_run_dev_image_local`

## 이날 실제로 바뀐 것

- Waffle 워크스페이스에 6개 추가 빌드: `turtlebot3_gazebo`, `turtlebot3_cartographer`, `turtlebot3_teleop`, `cartographer_rviz`, `pcl_ros` 외 1개 (`install/`에 들어감)
- `~/.bashrc`에 `export TURTLEBOT3_MODEL=waffle` 추가
- 그 밖에는 재설치·재빌드 없음. `isaac-ros-visual-slam` apt 설치 시도는 패키지가 없어 아무것도 설치되지 않음

## 알아둘 점

- **Isaac ROS 5.0에서 이름이 바뀜.** Jazzy의 `isaac_ros_visual_slam`이 Lyrical에서는 `isaac_ros_cuvslam`이에요. launch 파일 이름은 여전히 `isaac_ros_visual_slam*.launch.py`예요.
- **실물 로봇용 TurtleBot3 패키지는 Lyrical에서 빌드 불가.** `turtlebot3_msgs`, `dynamixel_sdk`, `hls_lfcd_lds_driver`, `nav2_bringup`, `tf_transformations`가 Lyrical용으로 없어요. 제외한 패키지: `turtlebot3`, `turtlebot3_node`, `turtlebot3_bringup`, `turtlebot3_example`, `turtlebot3_fake_node`, `turtlebot3_navigation2`, `turtlebot3_simulations`. 시뮬레이션에는 필요 없어요.
- **Isaac Sim 설치 방식이 README와 다름.** README는 `isaacsim-venv/` 방식이고 여기는 `~/Documents/IsaacSim/6.1.0` 설치예요. 연동 스크립트가 venv 경로를 가정하면 경로를 맞춰야 해요.

**확인 안 한 것 하나:** README는 Gazebo용 패키지를 `build_gazebo.sh`로 `gazebo_install/`에 빌드해요. 이날 빌드로 `install/`에도 `turtlebot3_gazebo`가 생겼어요. `gazebo_install/`이 이미 있다면 같은 패키지가 두 곳에 있는 상태예요. Gazebo에서 모델이 이상하면 이것부터 보세요.

## 다음에 이어갈 때

```
# 중복 여부 확인 (조회만)
ls -d ~/workspaces/waffle-lyrical-slam/gazebo_install

# 저장소 자체 점검
cd ~/workspaces/waffle-lyrical-slam
bash preflight.sh cartographer
bash preflight.sh cuvslam

# 환경 다시 점검 (읽기 전용 스크립트)
bash ~/check_setup.sh 2>&1 | tee ~/setup_report.txt
```

`check_setup.sh`는 Cartographer 검사를 워크스페이스 source 전에 하고, cuVSLAM을 옛 이름(`visual_slam`)으로 찾아서 두 줄이 잘못 FAIL로 나와요. 위 표가 맞는 판정이에요.