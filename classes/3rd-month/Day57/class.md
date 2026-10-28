# 10/27 배운 것: cuVSLAM · 미로 주행 실습 · PPO 보상 설계

- 강의 노트: [cuVSLAM](https://app.notion.com/p/cuVSLAM-4067969693958038a92df9d7d1685209)
- 수업 자료: [팀별 로봇 미로 주행 — 보상 설계·cuVSLAM·Nav2 실습](https://docs.google.com/presentation/d/19UfjZpjlP2RR7iLeboQTa_h0JFBVk2P_-Yz-u_tQ-eA/edit)

- **팀별 로봇 미로 주행 실습** (Isaac Sim 6.1 · Isaac Lab · ROS 2 Lyrical)
  - 완료 기준: 목표 오차 < 0.10 m, 차체 최고 속도 ≤ 0.951 m/s, 바퀴 아닌 부분 접촉 ≤ 0.5 N, 센서 누락 시 정지·복구
  - Sim · Lab · ROS는 Python 환경을 섞지 않고 따로 둠 (`~/isaacsim6_venv`, `~/IsaacLab/.venv`, `/opt/ros/lyrical`)
  - 예시 로봇(M38)의 값을 그대로 쓰지 말고 우리 로봇의 관절명·축·영점·물성·센서 TF로 바꿔야 함
  - 검증 순서: 기구학 → 센서 → 정책 → 폐루프
- **PPO 주행 학습**
  - 관측 24개(경로 preview, 속도, 팔 yaw 오차, IMU 기울기·각속도, 시야), 행동 2개(가감속, 팔 yaw 속도)
  - 보상은 표를 만들어 목표 값을 정하고 항목별로 설계 (진행 +, 시간 −, 행동 −, 도착 보너스, 실패 −)
  - 보상 악용 사례: 목표 보너스를 매 step 받기, 넘어져서 빨리 끝내기, 멈춰서 시간 비용 피하기 → 한 항씩 바꾸고 같은 seed로 비교
  - PPO 시작값: lr 3e-4, clip 0.2, gamma 0.99, GAE lambda 0.95, entropy 0.005. 학습 보상과 완주율은 따로 봐야 함
  - 팔을 과하게 움직이면 차체가 기울 수 있으니 실제 상황을 관찰하고, 바퀴 일부가 안 쓰이는지 확인
- **cuVSLAM**
  - 영상(+ 깊이·IMU 선택)으로 카메라의 6자유도 움직임을 추정. 라이다용이 아님, cartographer와 비슷한 구조(프런트엔드 특징 추적 → 백엔드 지도 보정)
  - 핵심은 영상이 끊기지 않고 들어오는 것. 강사님은 640×640 사용
  - 팔 카메라가 움직이므로 영상과 **같은 시각의 팔 FK**를 써야 함. 최신 관절각을 쓰면 팔 회전이 차체 이동으로 보임
  - 설정 예: tracking_mode 2(RGBD), depth 16UC1 mm, IMU fusion은 시간·외부보정 맞춘 뒤 켬
- **위치 추정과 Nav2**
  - EKF(robot_localization): 바퀴 odom은 vx·vy, IMU는 yaw rate, VO는 위치 차분 → 속도로 융합 (같은 값을 중복 융합하지 않기)
  - AMCL은 스워브라 OmniMotionModel, MPPI도 motion_model Omni. Nav2와 PPO가 동시에 명령하지 않게 함
- **센서·하드웨어 주의**
  - OpenCR을 두 개 이상 쓰면 장치 매핑(udev)을 잘 확인해야 함
  - 엔코더는 각도 래핑을 푼 뒤 차분, 바퀴각 / 4 = 모터축 각도
- 강사님 시연: 한 목표까지 60초 → 20초가 목표 (코너에서 멈추는 문제가 남음). 주행 실험은 팀당 1.5시간, 우리 팀은 3:30부터
