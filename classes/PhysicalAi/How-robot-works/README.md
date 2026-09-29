
```
          [ 로봇 시스템 아키텍처 ]

LiDAR ──┐
Camera ─┼──→ Raspberry Pi / SoC
IMU ────┘          │
                   ↓
             SLAM / Nav2
                   │
                   ↓
                  MCU
                   │
              PID → PWM
                   │
                   ↓
                 Motor
```

<br>

알고리즘 테두리
```
센서 데이터 받기
      ↓
로봇 위치 추정
      ↓
주변 장애물 계산
      ↓
지도 업데이트
      ↓
다시 위치 추정
```