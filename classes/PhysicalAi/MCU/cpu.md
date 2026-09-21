## CPU core
- CPU 안에서 실제로 명령어를 읽고 계산하고 실행하는 핵심 부분

```
MCU
│
├── CPU Core  ← 🧠 실제 계산/명령 실행
│
├── Flash     ← 프로그램 저장
├── SRAM      ← 작업 중 데이터 저장
├── GPIO      ← 외부 핀 입출력
├── Timer
├── UART
├── ADC
└── 기타 주변장치
```

<br>

cpu가 하는 일:
```
① 명령어 가져오기 (Fetch)
        ↓
② 명령어 해석하기 (Decode)
        ↓
③ 명령 실행하기 (Execute)
        ↓
④ 다음 명령
```

cpu와 cpu core 관계:
```
CPU
┌─────────────────────────┐
│       CPU Core          │
│  ┌───────────────────┐  │
│  │ ALU : 계산        │  │
│  │ Registers : 저장  │  │
│  │ Control Unit      │  │
│  └───────────────────┘  │
│                         │
│ Cache 등                │
└─────────────────────────┘
```
- core = engine

dual core cpu:
```
CPU
├── Core 1 🧠
└── Core 2 🧠
```
- 명령을 실행할 수 있는 엔진이 두개 있다는 뜻

<br>

architechture:
```
CPU Core
   │
   │ 명령 실행
   ↓
AHB Bus ─────→ SRAM / Flash
   │
   ↓
AHB-APB Bridge
   │
   ↓
APB Bus
   │
   ├── GPIO → LED / 버튼
   ├── UART
   ├── Timer
   └── 기타 주변장치
```

key points:
- CPU Core = thinking brain
- Bus = nerves
- GPIO = 외부 장치로 신호를 내보내거나 받아들이는 신경 말단

