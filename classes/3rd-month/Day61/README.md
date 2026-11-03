Date: 2026 Nov 2, Monday

## 오늘 배운 것
- [신호등 밝기 판정 · 릴레이 · SSH 화면 속도 (오늘 실습에서 배운 것)](class.md)




<br>

## 오늘 한 것 

- [비전 작업 일지 (11/02)](vision_log.md)
- Jetson 에서 perception 광각 탐지 실행, 노트북 SSH(-Y) 뷰어로 영상 + 탐지 상자 확인
- 뷰어 화면을 640×360 으로 줄여 속도 개선
- 신호등 실물 시험 (Visible YES 인데 OFF) → 원인 후보 정리
- 신호등 OpenCR 코드(sign_tower.ino) 확인, 시리얼 명령으로 색을 고정하는 판 받음



<br>

## 문제점
- SSH X 포워딩으로 본 탐지 화면이 10 Hz 이하로 느림
- 신호등 상자는 찾는데 색 판정이 계속 OFF
- 신호등이 3초마다 빨강 → 노랑 → 초록 → 소등을 반복해서 한 색을 고정해 시험할 수 없음
- 라즈베리파이가 없어 신호등 OpenCR 에 SSH 로 코드를 올릴 수 없음




<br>

## 해결 방법

- 탐지 입력은 그대로 두고 보여 주는 화면만 cv2.resize(frame, (640, 360)) 으로 줄임
- 신호등 판정 규칙(칸별 HSV 밝기 90분위, v_margin 40, 5장 중 3장)을 config 와 코드로 확인 → 기준값을 바로 낮추지 않고 한 색을 켜 둔 상태에서 다시 보기로 함
- sign_tower.ino 를 시리얼 명령 r/y/g/o/a(115200 baud)로 색을 고정하는 판으로 수정
- 노트북과 신호등 OpenCR 을 USB 로 직접 연결해 Arduino IDE 로 업로드하기로 함


<br>

## 결과

- Jetson 광각 탐지 뷰어: 10 Hz 이하 → 약 15 Hz
- 신호등 OFF 원인 후보 3가지: 켜진 칸과 꺼진 칸의 밝기 차 부족(자동 노출) / 탐지 상자와 램프 칸 위치 불일치 / 점멸 중 촬영
- 신호등 색 고정 펌웨어 준비 (업로드 · 실물 확인 전)




<br>

## 느낀 점





<br>

## 할 일

- sign_tower.ino 색 고정 판 업로드 → r / y / g 각각 고정해서 신호등 판정 확인
- 그래도 OFF 면 상자 위에 칸 경계 · 칸별 점수를 그려서 칸 비율 · v_margin 실측
- 리모컨(RC-100) 수신기 확인 → 리모컨으로 색 선택
- 레포 통합본(perception TensorRT, firmware, tools/jetson) 빌드 · 실행
- TIL Day60 README · class.md 반영




