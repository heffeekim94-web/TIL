# 10/28 배운 것: nvblox · Nav2 · 예측 카메라 정책 / 오늘 실습에서 배운 것

- 강의 노트: [nvblox · Nav2 · 예측 카메라 정책](https://app.notion.com/p/nvblox-Nav2-40779696939580429389fdc0567a76fe)
- 수업 자료: [팀별 로봇 자율주행 2 — nvblox·Nav2·예측 카메라 정책](https://docs.google.com/presentation/d/10B9z7mA8zPu8sN_ghsi8B1viEOsL84xXxQIRI4-yiZE/edit)

## 수업: 팀별 로봇 자율주행 2

- **전체 흐름**: 깊이 영상 → nvblox 거리 지도 → Nav2 비용지도 → 경로 재계획 → 정책 관측 → 속도 명령
  - 검증 순서: 모델 정적 검사 → Sim 6.1 스테레오 렌더 → ROS 영상·clock·TF 연결 → cuVSLAM → nvblox·Nav2·정책
  - 정적 PASS(트리·메시·광학축 검사)는 주행 성공이 아님. 렌더 성공과 ROS 발행도 다른 단계
- **nvblox** (자율주행용 장애물 지도)
  - 주행 지도와 별도로 장애물 유무만 담는 지도를 하나 더 만듦
  - TSDF: 표면 주변의 부호 있는 거리(영상마다 가중 누적) → ESDF: 가장 가까운 장애물까지 거리 → 2D slice 를 Nav2 비용으로. Mesh 는 시각화용
  - 입력: 스테레오 영상 → VSLAM → Pose, 깊이 영상 + Pose → nvblox. 카메라 해상도·주기를 맞춰야 함
  - 시작값: voxel 0.025 m, 깊이 적분 15 Hz, ESDF 10 Hz, mesh 2 Hz, slice 높이 0.05–0.65 m, 적분 최대 5 m
- **동적 장애물**
  - 사람은 움직일 거라 기대할 수 있지만, 물건은 직접 피해 가야 함
  - 정적 지도와 동적(현재 점유) 지도를 나눔 → 사람이 지나간 자리가 벽처럼 남지 않게
  - 사람을 지도에서 지우는 것 ≠ 충돌을 무시하는 것
- **Nav2 비용지도**
  - StaticLayer(CAD 지도) + NvbloxCostmapLayer(실측 장애물) + InflationLayer(여유 거리), NavFn A*
  - allow_unknown: false — CAD 의 빈 공간은 관측 증거가 아님. 안 본 방향은 감속하고 관측 후 진행
  - 시작값: robot_radius 0.245 m, inflation 0.32 m, cost_scaling 8.0, 계획 1 Hz / 지도 5 Hz
  - nvblox 는 odom 좌표, 비용지도는 map 좌표 → 플러그인이 TF 로 연결
- **팔 카메라(예측 카메라 정책)**
  - 카메라 parent 를 팔 링크로 바꾸려면 URDF·USD 둘 다 변경
  - 관절값 q(t) 로 FK → **촬영 시각의 TF** 로 영상 처리. 그 시각 TF 가 없으면 적분 보류
  - 깊이 16UC1 이면 mm → m 변환, 영상과 CameraInfo 시각 일치
- **Nav2 경로 → PPO 관측**
  - ComputePathToPose 결과를 map 좌표·유한수 검사 → 중복점 제거 → 0.05 m 간격 재표본화
  - 관측 순서·단위·차원·정규화 통계는 학습 때와 같아야 함. M38 의 24차원을 그대로 복사하지 않기
- **안전 정지**
  - 경로 2.5 s, nvblox 지도 1.0 s 넘게 오래되면 주행 차단. 계획 실패 시 경로 해제
  - 최종 속도 명령은 한 노드만 발행. 복구는 새 입력·새 경로 확인 후
- **비교 실험·제출**: voxel 0.025/0.05, ESDF 5/10 Hz 를 같은 시작·목표·seed 로 반복. 성공 수/전체, 경로 오차, 지연, 최소 거리, ROS bag 기록

## 오늘 실습에서 배운 것 (pa06 터틀봇)

- **IP 가 매주 바뀔 때**: DHCP 로 IP 가 바뀌어도 MAC 주소는 그대로 → `arp-scan` 으로 같은 와이파이를 훑어 MAC 으로 IP 를 찾는 `ssh-pa06` 함수
- **ROS 2 통신 확인**
  - 노트북과 로봇의 `ROS_DOMAIN_ID` 를 같게(50)
  - 토픽이 안 보이면 `ros2 daemon stop` 후 다시, 멀티캐스트 시험으로 네트워크 확인
- **RViz**
  - Fixed Frame 을 센서 프레임(`base_scan`)으로 두면 TF 없이도 스캔을 볼 수 있음
  - 스캔 점 색 = intensity(반사 세기)
  - 정면에 물체를 두고 앞 방향(+x)이 맞는지 확인
- **라이다 배치**: 라이다 바로 뒤의 카메라 보드가 약 22 cm 에 찍힘(자기 가림) → `range_min` 을 0.25 m 정도로
- **Lyrical 에서 TurtleBot3 빌드**
  - apt 에 bringup·node 가 없어서 소스 빌드
  - 헤더 `.h` → `.hpp`
  - message_filters Subscriber 에 QoS 인자 필수
- **라즈베리 파이 메모리**
  - VS Code Remote-SSH 서버(약 1.3 GB) + 병렬 C++ 컴파일 + 스왑 0 → 메모리 고갈로 SSH 먹통
  - 파이에서는 일반 터미널로 접속, `MAKEFLAGS="-j1"`, `--parallel-workers 1`, 필요하면 스왑

## 오늘 YOLO 작업에서 배운 것

- **데이터 누수**: 같은 영상의 비슷한 프레임이 train·val·test 에 나뉘면 점수가 부풀려짐 → 영상 단위로 나누기
- **조명 치우침**: 어두운 영상이 한 split 에만 몰리면 학습 또는 평가가 치우침
  - 밝기를 재서 확인
  - 시간 구간으로 나누고, 경계 뒤 프레임을 버려 섞임을 막음
- **best.pt 고르는 기준**: fitness(mAP50-95 중심)라서 mAP50 이 가장 높은 epoch 과 다를 수 있음
