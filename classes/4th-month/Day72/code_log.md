date: 2026.11.17

# Turtle Ninja 코드 읽기 일지 (11/17)

> 작성: 김혜민 · 2026-11-17 (화)

오늘은 **로봇이 실제로 도는 코드를 첫 단추부터 순서대로 읽기 시작한 날**이에요.

- 로봇을 켜는 첫 파일 `run_robot.sh` → `robot.launch.py` → 설정 4개 (hardware_map · urdf · controllers · control) → 노드 7개 흐름을 따라감
- 실제 로봇 (젯슨) 에서 도는 건 `main` 이 아니라 `~/p2_integ` → 설명 기준을 `feat/integ-1110` 으로 바꿈
- 11/16 16:30 판 rosbag 에 실제로 찍힌 토픽으로 "만들어진 순서" 13단계 정리
- 1단계 펌웨어 4개 파일 (`firmware/opencr/`) 을 읽음: 패킷 · 루프 · 모터 버스
- 광각 밝기 브랜치는 따로 안 만들기로 함 (혁무님 PR #19 에 이미 들어 있음)

<br>

## 1. 셸 기초

- `.sh` 는 명령을 차례로 적어 둔 목록. 첫 줄 `#!/usr/bin/env bash` 는 주석이 아니라 "bash 로 실행해라" 는 표시 (shebang)
- `bin` 은 실행 파일 서랍, `PATH` 가 어느 서랍을 찾을지 정함. bash 도 결국 `/usr/bin/bash` 라는 파일
- 어떤 코드가 도는지는 **어느 폴더에서 실행하고 어떤 `install/setup.bash` 를 source 했나** 로 정해짐 (`ROOT=$(cd "$(dirname "$0")/../.." && pwd)`). 그래서 clone 한 저장소를 고쳐도 젯슨 로봇에는 안 바뀜

<br>

## 2. 저장소가 생긴 순서 (git 이력)

| 날짜 | 한 일 |
|---|---|
| 10/19 | 정조은님 README · 폴더 뼈대, 혁무님 본체 코드 89개 파일 |
| 10/21 | `nt_` 이름 정리 |
| 11/02 | `run_robot.sh` 생김 |

<br>

## 3. 코드 읽는 순서 (11/16 rosbag 토픽 기준)

남이 쓰는 걸 먼저 → 아래 (하드웨어) 부터 위 (미션) 로:

펌웨어 → hardware → urdf → swerve → launch → interfaces → 팔 → 라이다 · SLAM → nav2 / cmd_vel_hold → perception → planning → mission → mission_system.launch

- 토픽 9개 (`/startup/lifecycle_status` 등) 는 `feat/integ-1110` 에서 만드는 파일을 못 찾음 → 11/11 이후에 따로 들어온 것으로 보임

<br>

## 4. 펌웨어 4개 파일 (`feat/integ-1110` `firmware/opencr/`)

| 파일 | 줄 | 하는 일 |
|---|---|---|
| `opencr_packet.h` | 534 | 젯슨 ↔ 보드 편지 규칙 (패킷 모양) |
| `opencr.ino` | 254 | 지휘자: 10 ms 루프, 300 ms 경비견 (명령 끊기면 멈춤) |
| `motor_bus.h` | 92 | 모터 목록표 |
| `motor_bus.cpp` | 557 | 다이나믹셀 Sync Read / Write, 컨트롤 테이블 칸 116 · 132, 3번 실패하면 잠금 |

- **패킷 (상자)**: `AA 55 | 종류 | 길이 | 데이터 | 체크섬`. 예: CONFIG_ACK `AA 55 04 03 04 0F 00 1A`. CMD · STATE 가 100 Hz 로 오감
- `class Parser` 는 한 바이트씩 받아 상자 시작 (`AA 55`) 을 찾는 상태 기계, 체크섬 틀리면 버림
- **보드와 젯슨이 같은 헤더를 씀** → `opencr_packet.h` 를 바꾸면 젯슨 빌드와 보드 업로드 둘 다 다시. 이 파일은 실행할 때가 아니라 빌드할 때만 필요
- 루프 (10 ms): 받기 → IMU → 경비견 → Sync Write / Read → STATE 보내기. 안전장치는 3겹 (swerve · 펌웨어 · Bus Watchdog)

### `opencr_packet.h` 에서 본 C++ 방식

- `#pragma once`, `stdint.h` · `string.h` 만 씀, 고정 크기 정수 (`uint8_t` …)
- `namespace pkt` = 이름에 붙이는 "성" (`pkt::State`, `std::`, `rclcpp::` 와 같은 것)
- 동적 할당 없이 고정 배열 + 개수 `n`, 실패는 예외 대신 0 / false 로 알림, 길이 검사
- `put` / `get` 포인터 + `memcpy`, 리틀 엔디언
- DIAG v1 / v2 하위 호환 (53 → 63 바이트)
- `= 0x..` 상수가 다 "종류" 는 아님: `TYPE_` 만 패킷 종류. `ST_` · `FLAG_` · `MODE_` · `TF_` 는 다른 칸에 쓰는 값 (`TYPE_STATE` 와 `ST_HOST_TIMEOUT` 은 둘 다 0x02)
- 1씩 커지는 값은 번호, 2배씩 커지는 값 (0x01, 0x02, 0x04 …) 은 동시에 켤 수 있는 스위치 (비트 깃발)

<br>

## 5. 광각 밝기

- 팀장님이 PR 을 다 처리한 뒤 `main` (`235b6e7`, PR #21 병합) 기준으로 `feat/wide-cam-brightness` 를 준비하려 했음
- 그런데 `main` 에는 아직 `bringup.launch.py` 가 없고, 밝기 코드 (`brightness: -1`, 3초 뒤 `v4l2-ctl`, `wide_brightness` 기본 −20) 는 혁무님 PR #19 (`feat/arm-drive-demo-version`) 에 이미 들어 있음
- → 브랜치 따로 안 만들고, 팀장님께 #19 그대로 merge 부탁하기로 함

<br>

## 다음 할 일

- [ ] 팀장님께 PR #19 merge 부탁 → 병합 뒤 `main` pull, `bringup.launch.py` 에 `wide_brightness` 있는지 확인
- [ ] 펌웨어 다음 단계 (hardware) 읽기
