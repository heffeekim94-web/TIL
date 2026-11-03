# 11/03 실습에서 배운 것

오늘은 강의 노트가 없어서, 신호등 · Jetson 작업과 팀 회의에서 배운 것을 정리했어요.

## 1. ROBOTIS RC-100 리모컨을 OpenCR 에서 받기

- 수신기는 OpenCR 의 UART 포트에 꽂고, `RC100` 라이브러리로 읽음 (`rc.begin(1)` = `Serial2`, 57600 baud)
- `rc.available()` 이 패킷 하나를 다 받으면 true → `rc.readData()` 가 버튼 값
- 버튼 값은 비트로 합쳐진 숫자: U = 1, D = 2, L = 4, R = 8, 1 = 16, 2 = 32, 3 = 64, 4 = 128, 5 = 256, 6 = 512
- 누르고 있는 동안 같은 값이 계속 오고, 앞 버튼 비트가 남아 있을 수 있음 → **이번에 새로 켜진 비트만** 보면 됨

```cpp
uint16_t pressed = data & ~lastRcData;   // 새로 눌린 버튼만
lastRcData = data;
```

- `delay()` 로 3초씩 기다리면 그동안 명령을 못 받음 → `millis()` 로 지난 시간을 재서 바꾸면 버튼에 바로 반응

## 2. OpenCR 펌웨어를 노트북에서 빌드 · 업로드

- Arduino IDE 없이 `arduino-cli` + ROBOTIS 업로더 `opencr_ld` 로 가능 (모듈1 수업 때 `~/pa-opencr-build` 에 만든 환경)
- 스케치는 **폴더 이름 = 파일 이름** 이어야 함 (`sign_tower_rc/sign_tower_rc.ino`)
- 업로더는 실패해도 정상 종료처럼 보일 수 있음 → `CRC OK` 와 `[OK] Download` 두 줄로 판단
- OpenCR 은 USB 로 `/dev/ttyACM0` (`OpenCR Virtual ComPort`), 커널 로그는 `sudo dmesg` 로 봐야 함

## 3. ROS 2 원격 확인에서 막히는 곳

- `ROS_DOMAIN_ID` 가 다르면 같은 망이어도 토픽이 안 보임. 새로 연 SSH · 다른 터미널은 `~/.bashrc` 를 안 읽을 수 있음 → `bash -i` 로 실행하면 같은 설정
- `ros2 topic list` 는 예전 목록을 기억할 수 있음 → 실제로 오는지는 `ros2 topic hz` 로 확인
- 화면 전달은 `ssh -Y` 로 접속한 **일반 터미널**에서만 됨 (VS Code 터미널은 `DISPLAY` 가 비어 있음)
- `Connection refused` = 기기에는 닿았는데 그 포트를 받는 프로그램이 없음 → 맞는 기기인지 MAC 주소(`ip neigh`)로 확인

## 4. Jetson 엔진이 어떤 모델인지 확인하기

- 같은 ONNX 파일인지는 크기보다 `md5sum` 으로 확인 (값이 같으면 같은 파일)
- `trtexec --loadEngine=<엔진>` 으로 입력 크기와 추론 시간(평균 · p99)을 바로 볼 수 있음
- 960×960 은 1280×720 영상의 위아래 여백까지 계산 → 544×960 이 같은 결과에 1.5배 빠름 (팀원 측정)

## 5. 팀 회의에서 나온 것

- 모방학습은 저장한 관절값을 재생하는 게 아니라, 학습한 가중치로 결과가 나와야 함
- ONNX 모델은 노드가 켜질 때 메모리에 올리고 입력 → 결과를 다음 노드로 넘김. 잘못 학습하면 같은 입력에도 늘 틀린 결과 → 실물로 검증
- 적재함 칸 확인: YOLO 는 칸을 구분 못 함 → AprilTag ID 또는 손목 카메라로 칸 센터 추정 (비전 다음 과제)
