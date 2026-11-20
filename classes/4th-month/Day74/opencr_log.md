date: 2026.11.19

# 터틀봇 OpenCR 펌웨어 확인 일지 (11/19)

> 작성: 김혜민 · 2026-11-19 (목)

오늘은 **어제 막힌 `Failed connection with Devices` 의 원인을 OpenCR 펌웨어로 좁히고, 다시 올릴 펌웨어가 파이에 이미 있다는 걸 찾은 날**이에요.

- OpenCR 전원을 켰는데 멜로디가 안 남 → TurtleBot3 펌웨어가 아닐 가능성이 큼
- 파이에 보이는 OpenCR 은 `ttyACM0` 하나. `ttyUSB0` 는 LiDAR
- 파이의 `ninja_ws` bringup 은 정상 실행됨. 대답을 못 한 건 OpenCR 쪽
- 파이 `~/opencr_fw/` 에 waffle 펌웨어 5개 + 업로드 도구가 이미 있음 → 다운로드 필요 없음
- 아직 OpenCR 에는 아무것도 올리지 않음

<br>

## 1. 소리가 안 났다

- TurtleBot3 펌웨어가 든 OpenCR 은 전원을 켜면 멜로디가 남. 안 남
- 지난주 신호등 (sign tower) OpenCR 에 펌웨어를 올리는 작업이 있었음. 가능성 두 가지

| | 상황 | 확인 |
|---|---|---|
| A | `ttyACM0` 이 신호등 OpenCR, 터틀봇 OpenCR 은 USB 가 안 꽂힘 | USB 선을 따라가 봄 |
| B | 신호등 펌웨어가 터틀봇 OpenCR 에 올라감 | 터틀봇 OpenCR 만 꽂아도 소리 없음 |

- 둘 다 `turtlebot3_node` 에겐 "TurtleBot3 가 아닌 OpenCR" 이라 같은 에러가 남

<br>

## 2. 포트 확인

```
ls -l /dev/serial/by-id/
usb-ROBOTIS_OpenCR_Virtual_ComPort...      -> ttyACM0   ← OpenCR (하나뿐)
usb-Silicon_Labs_CP2102_USB_to_UART...     -> ttyUSB0   ← LiDAR (LDS-03) 변환 칩
```

- `by-id` 는 장치 이름으로 포트를 보여 줘서 `ttyACM0` 이 무슨 보드인지 알 수 있음

<br>

## 3. 파이의 turtlebot3 파일 ≠ OpenCR 펌웨어

- TurtleBot3 는 두 컴퓨터가 USB 로 대화하는 구조

| | 파이의 turtlebot3 (`ninja_ws`) | OpenCR 펌웨어 |
|---|---|---|
| 실행 위치 | 라즈베리파이 (Linux) | OpenCR 마이크로컨트롤러 (STM32) |
| 형태 | ROS2 패키지 | `.bin` 파일 하나 |
| 역할 | ROS 토픽 ↔ USB 메시지 변환 | 모터 · IMU · 배터리 |
| 상태 | ✅ 실행됨 (포트 열기까지 성공) | ❌ TurtleBot3 가 아닌 것으로 추정 |

- bringup 은 OpenCR 에 프로그램을 넣어 주지 않음. 펌웨어가 있다고 가정하고 연결만 시도
- **재플래시** = 보드 안 프로그램을 다시 써넣는 것. OpenCR 에는 한 번에 프로그램 하나만 들어감

<br>

## 4. 파이에 이미 있는 펌웨어

- 파이 Wi-Fi IP 가 바뀌어 있어서 새 주소로 SSH 접속해 확인
- `~/opencr_fw/`

| 파일 | 날짜 | 추정 |
|---|---|---|
| `waffle_V230127R1.bin` | 11/04 | ROBOTIS 공식판 |
| `waffle_rc_timeout_1106.bin` | 11/06 | 팀판 (리모컨 타임아웃) |
| `waffle_sonar.bin` | 11/12 | 팀판 (초음파) |
| `waffle_guard.bin` | 11/12 | 팀판 (가장 최신) |
| `sonar_test.bin` | 11/12 | 초음파 테스트용 |
| `opencr_ld` | | 업로드 도구 |

- 파이 명령 기록에 예전에 `./opencr_ld /dev/ttyACM0 115200 waffle_rc_timeout_1106.bin 1` 로 올린 기록이 있음
- 같이 발견: 파이의 `~/sign_tower_rc.ino.bin` 은 11/13판. 11/16판은 이 경로로 안 올라갔을 수 있음

<br>

## 5. 재플래시 순서 (아직 안 함)

1. **파이에 꽂힌 OpenCR 이 터틀봇 본체 것인지 선을 따라 확인** (신호등이면 신호등 펌웨어를 덮어씀)
2. bringup 끄기 (포트를 쓰고 있으면 실패)
3. `cd ~/opencr_fw`
4. `./opencr_ld /dev/ttyACM0 115200 <펌웨어>.bin 1` → `[OK] Download` 확인 (포트 · 속도 · 파일 · 올린 뒤 실행)
5. 전원 껐다 켜서 멜로디 → bringup → 노트북에서 `/odom` `/cmd_vel` 확인

- 공식판은 확실하지만 팀 기능이 빠짐. `waffle_guard.bin` 은 팀이 마지막에 쓰던 판일 가능성 → 팀원에게 확인

<br>

## 다음 할 일

- [ ] OpenCR USB 가 터틀봇 보드인지 신호등 보드인지 확인
- [ ] 팀원에게 어떤 펌웨어 (공식 · `waffle_guard`) 를 올릴지 묻기
- [ ] 재플래시 후 멜로디 · bringup · `/odom` 확인
- [ ] 신호등 11/16판이 올라갔는지 확인
- [ ] 노트북 · 파이 `.bashrc` 중복 `ROS_DOMAIN_ID` 줄 정리
