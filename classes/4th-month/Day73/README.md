Date: 2026 Nov 18, Wednesday

## 오늘 배운 것
- API 는 프로그램끼리 "이렇게 요청하면 이렇게 답한다" 는 약속이다. 웹 주소뿐 아니라 함수 사용법, ROS 메시지 형식도 API 다
- LLM · VLM · VLA 는 한 구조다. 이미지를 토큰으로 바꿔 붙이면 VLM, 출력을 로봇 행동으로 바꾸면 VLA
- 모델에 필요한 VRAM 은 파일 크기 + KV 캐시 + 오버헤드다. 8GB 노트북에선 약 6.6GB 모델이 한계선
- Wi-Fi 해시 비밀번호 (PSK) 는 SSID 와 섞어 만든 값이라 SSID 만 바꾸면 연결이 안 된다
- ROS2 는 같은 Wi-Fi + 같은 `ROS_DOMAIN_ID` 여야 서로 보이고, 터미널마다 `setup.bash` 를 source 해야 `ros2` 가 생긴다
- 포트 · 보레이트가 다 되는데 `Failed connection with Devices` 면 OpenCR 펌웨어를 의심한다



<br>

## 오늘 한 것 

- [LLM · VLM · VLA 준비 일지 (11/18)](llm_log.md)
- [터틀봇 파이 연결 일지 (11/18)](pi_log.md)
- Ollama `0.40.2` → `0.40.16` 업그레이드, GPU 점검
- 8GB 에 맞는 LLM · VLM 모델 정리, `gemma4` (e4b) 받아서 실행
- 노트북에 Lyrical MoveIt · ros2_control · open_manipulator 설치
- 터틀봇 pa06: 랜선 직결 → netplan 으로 KANT_15F 연결 → `ROS_DOMAIN_ID=63` → bringup



<br>

## 문제점
- KANT Sparta 비밀번호가 바뀌어 파이가 Wi-Fi 에 못 붙음
- SSID 만 바꿔서는 Wi-Fi 연결이 안 됨
- 노트북에서 `ros2: command not found`
- `turtlebot3_node` 가 바로 죽어서 `/odom` `/cmd_vel` 이 없음
- 비교만 하려던 모델 두 개를 묻지 않고 받기 시작함



<br>

## 해결 방법

- 노트북과 랜선 직결 (`pi-share`, `10.42.0.60`) 로 들어가 netplan 수정
- 해시 대신 실제 비밀번호 + `regulatory-domain: KR`, `sudo netplan try`
- `source /opt/ros/lyrical/setup.bash`
- OpenCR 전원 켜기 → 노드 로그 · `udevadm` 으로 포트 · 보드는 정상, 펌웨어로 좁힘
- 다운로드 멈추고 `gemma4` 만 받음



<br>

## 결과

- 파이 Wi-Fi 연결, 노트북 ↔ 파이 ping · SSH · ROS2 토픽 확인
- 지연: 랜선 0.15ms, Wi-Fi 7–104ms
- `gemma4` 100% GPU, VRAM 8.1GB 중 4.7GB
- OpenCR 연결은 아직 안 됨 (펌웨어 확인 필요)



<br>

## 느낀 점

- 이제야 Physical ai의 본질인 LLM, VLM, VLA를 배운다. 드디어 본격적인 것을 배운다니 기대된다. 과연 난 잘 흡수할 수 있을가? 프로젝트 2를 끝냈는데도 아직 확신이 되는 학습 내용은 없다. 아직 어떻게 코드가 흘러가는지도 모르겠고.. 누가 어떻게 그렇게 만들었냐고 물으면 답할 자신이 없다. 뭐부터 다시 짚어야할까...



<br>

## 할 일

- 조교 · 강사님께 OpenCR 펌웨어 확인, bringup 성공시키기
- gemma4 속도 재기, VLM 에 사진 넣어 보기
- `.bashrc` 중복 줄 정리, bringup 은 `tmux` 에서
