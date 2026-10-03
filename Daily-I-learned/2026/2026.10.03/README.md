Date: 2026 Oct 03, Saturday

## 오늘 배운 것
- [OpenCR 두 모터 동시 제어](OpenCR_두_모터_동시_제어_2026.10.03.md) - Sync Write 한 패킷으로 X·Y축 모터에 속도와 목표 위치를 함께 전달하는 방법
- 함께 출발하는 것과 같은 시각에 도착하는 것은 다르다
- [main.py 코드 설명](rasberry/main2.md) - `select`로 키보드 입력과 OpenCR 응답을 동시에 처리하는 구조
- 코드 설명 보고서: [main.py](rasberry/main_py_report.html), [opencr_control.ino](rasberry/opencr_control_report.html)



<br>

## 오늘 한 것 

- [카메라 X·Y축 제어 스케치](opencr_camera_home/opencr_camera_home.ino)에 `move X각도 Y각도 X속도 Y속도` 동시 이동 명령 추가 ([사용법](opencr_camera_home/README.md))
- 라즈베리파이 → USB 시리얼 → OpenCR 제어 코드 작성
  - [main1.py](rasberry/main1.py): 명령 한 줄을 보내고 응답 확인
  - [main2.py](rasberry/main2.py): 키보드로 이동·홈·정지·조회 명령 입력
  - [opencr_control.ino](rasberry/opencr_control.ino): 라즈베리파이 명령을 받아 두 모터를 제어하는 OpenCR 통합 스케치



<br>

## 문제점
- X축(pan)과 Y축(tilt)을 `pan 30`, `tilt -10`처럼 따로 입력해야 해서 두 축이 순서대로만 움직였다
- 이동 중에는 새 명령이 거부되어 도착을 기다리거나 `x`로 정지해야 다음 명령을 실행할 수 있었다
- Sync Write는 모터별 응답이 없어서 명령이 제대로 적용됐는지 알 수 없다




<br>

## 해결 방법

- `parseMove()`로 네 입력값을 검사하고, 잘못된 입력은 전체 거부
- `moveBoth()`에서 축별 속도·목표 위치를 계산해 Sync Write 한 패킷으로 동시에 전송
- 전송 후 각 모터의 목표 위치를 다시 읽어 적용 여부 확인
- 두 축 모두 도착해야 `DONE XY`를 출력하도록 상태 관리 추가


<br>

## 결과

- OpenCR용 컴파일, 입력 범위·잘못된 입력 거부 검사 통과
- 보드 업로드와 실제 두 모터 동시 이동은 아직 확인하지 못함



<br>

## 느낀 점

- 




<br>

## 할 일

- 보드 업로드 후 실제 두 모터 동시 이동 확인
- 두 축의 도착 시간을 맞추는 속도 자동 계산 검토
- 라즈베리파이 ↔ OpenCR 연결 테스트
