date: 2026.11.18

# 터틀봇 파이 연결 일지 (11/18)

> 작성: 김혜민 · 2026-11-18 (수)

오늘은 **와이파이가 막힌 터틀봇 (pa06) 에 랜선으로 들어가 Wi-Fi 와 ROS2 통신을 다시 살린 날**이에요.

- KANT Sparta 비밀번호가 바뀌어 파이가 Wi-Fi 에 못 붙음 → 노트북과 랜선 직결 (`pi-share`) 로 접속
- netplan 비밀번호가 해시 (PSK) 라서 SSID 만 바꾸면 연결이 안 됨 → 실제 비밀번호로 바꿔 KANT_15F 연결
- 노트북 · 파이 `ROS_DOMAIN_ID=63` 으로 맞추고 노트북에서 파이 토픽 확인
- `turtlebot3_node` 가 OpenCR 과 연결 실패 (`Failed connection with Devices`) → 펌웨어 문제로 좁힘

<br>

## 1. 랜선으로 파이 들어가기

- 노트북 유선 포트 `enp129s0` 에 `pi-share` 프로필 (`ipv4.method shared`, 자동 연결 끔) → 노트북 `10.42.0.1`, 파이 `10.42.0.60`
- USB-C 선은 파이에 **전원만** 줌 (노트북이 USB 장치로 인식 못 함). OpenCR 전원과 동시에 꽂지 않기
- 계정은 `ubuntu` 도 `turtle` (젯슨용) 도 아니고 `pa06`
- 지연: 랜선 0.15ms, Wi-Fi 7–104ms → 팔 실습 · 데이터 수집은 랜선, 주행은 Wi-Fi

<br>

## 2. Wi-Fi 바꾸기 (netplan)

- 파일은 `/etc/netplan/50-cloud-init.yaml` 하나
- 64자리 `password` 는 비밀번호가 아니라 **PSK = PBKDF2(비밀번호, SSID)**. SSID 가 계산에 들어가서 SSID 만 바꾸면 키가 안 맞음
- 바꾼 것: SSID `KANT_15F`, 실제 비밀번호, `regulatory-domain: KR` (5GHz 채널)
- `sudo netplan try` 로 적용 (확정 안 하면 120초 뒤 되돌아감) → `wlan0` 에 `10.2.150.x` 주소 받음
- 해시값도 비밀번호와 같은 효력이라 붙여 넣을 때 가리기

<br>

## 3. `ssh-pa06`

- `~/.bashrc` 의 함수: `arp-scan` 으로 Wi-Fi 망을 훑어 **파이 Wi-Fi 카드 MAC** 을 찾고 그 IP 로 접속 → IP 가 바뀌어도 됨
- 파이의 유선 (`eth0`) 과 무선 (`wlan0`) MAC 은 끝자리가 다름. 함수는 무선 쪽을 찾아서 파이가 Wi-Fi 에 없으면 못 찾음
- 조건: 같은 Wi-Fi, 노트북도 Wi-Fi, sudo 필요
- `exit` 는 SSH 만 끊음. 그 SSH 에서 띄운 프로그램 (bringup) 은 같이 꺼짐 → `tmux` 안에서 실행

<br>

## 4. ROS_DOMAIN_ID · Lyrical

- ROS_DOMAIN_ID = 같은 번호끼리만 서로 보이는 채널. 층 전체 Wi-Fi 라 다른 조와 겹치면 남의 토픽이 섞임 (0 · 30 같은 흔한 번호 피하기)
- 노트북 · 파이 둘 다 `63`. 파이 `.bashrc` 에 예전 `50` 줄이 남아 있었지만 마지막 줄이 이김
- 노트북에서 `ros2: command not found` → `.bashrc` 에 jazzy 줄은 꺼 두고 lyrical source 줄이 없었음. `source /opt/ros/lyrical/setup.bash` (Isaac Lab `PYTHONPATH` 충돌 때문에 alias 추천)
- `.bashrc` 를 바꾸면 이미 열린 터미널엔 `source ~/.bashrc` 해야 적용
- 앱 입력창의 `!` 명령은 항상 **노트북**에서 실행됨. 프롬프트가 `pa06@pa06` 인지 보고 칠 것

<br>

## 5. bringup · OpenCR

- 노트북에서 보인 토픽: `/scan`, `/tf`, `/robot_description` 등. `/odom` `/cmd_vel` `/imu` `/battery_state` 가 없음 → `turtlebot3_node` 가 없음
- 1차 원인: OpenCR 전원 스위치가 꺼져 있었음 (USB 전원만으로 `/dev/ttyACM0` 은 보임)
- 전원을 배터리로 바꾸는 순간 파이가 재부팅 → bringup 과 SSH 가 같이 꺼짐
- 다시 켜도 같은 에러. 로그 순서:

```
Succeeded to open the port(/dev/ttyACM0)!
Succeeded to change the baudrate!
Failed connection with Devices          ← 34ms 만에 실패
```

- `exit code -6` = SIGABRT (처리 못 한 예외로 스스로 종료)
- 노드 로그는 `~/.ros/log/latest/` 가 아니라 `~/.ros/log/turtlebot3_ros_<PID>_*.log`
- `udevadm` 결과 `ROBOTIS OpenCR` 으로 인식 → USB · 보드는 정상
- `turtlebot3_node` 는 OpenCR 자체 (ID 200) 에 ping. TurtleBot3 ROS2 펌웨어면 모터 전원과 상관없이 답함 → **펌웨어가 TurtleBot3 ROS2 용이 아닐 가능성**
- `Detected lidar stuck` (LDS-03) 은 WARN 이라 원인 아님

<br>

## 다음 할 일

- [ ] OpenCR 켤 때 멜로디가 나는지 확인
- [ ] 조교 · 강사님께 OpenCR 펌웨어가 무엇인지, TurtleBot3 ROS2 펌웨어로 다시 올려도 되는지 묻기
- [ ] 파이 · 노트북 `.bashrc` 의 중복 `ROS_DOMAIN_ID` 줄 정리, 조원과 번호 맞추기
- [ ] bringup 을 `tmux` 안에서 실행
