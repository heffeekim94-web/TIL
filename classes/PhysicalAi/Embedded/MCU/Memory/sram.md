## SRAM
- Static Random Access Memory
- MCU가 프로그램을 실행하는 동안 필요한 데이터를 잠깐 저장해두는 작업 공간

실행 구조:
```
Flash 💾
┌────────────────────────┐
│ 프로그램 코드           │
│ target - current       │
└───────────┬────────────┘
            │ 명령어 읽기
            ▼
        CPU Core 🧠
            │
            │ 계산하면서
            ▼
SRAM 📝
┌────────────────────────┐
│ target_speed  = 100    │
│ current_speed = 80     │
│ error         = 20     │
└────────────────────────┘
```

ALU using SRAM:
```
SRAM
100 ──┐
      ├──→ CPU의 ALU → 100 - 80 → 20
80 ───┘                        │
                              ▼
                         SRAM에 저장
                         error = 20
```

FLASH VS SRAM:
```
          MCU

Flash 💾                    SRAM 📝
프로그램 장기 보관           작업 중 데이터
전원 꺼도 유지              전원 끄면 사라짐
     │                          ↕
     └──────→ CPU Core ←────────┘
                 │
                ALU
              실제 계산
```

전원이 꺼지면 SRAM에서 사라지는 값:
- `target_speed`, `current_speed`, `error`

What remains at Flash:
- 로봇 제어 프로그램

