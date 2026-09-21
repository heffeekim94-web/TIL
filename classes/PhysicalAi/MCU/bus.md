## AHB/APB
- MCU 내부에서 CPU, 메모리, 주변장치들을 서로 연결해 주는 통신 통로(Bus)
```
             MCU 내부

       ┌──────────────┐
       │   CPU Core   │
       └──────┬───────┘
              │
           AHB Bus
      ════════╪══════════
              │
       ┌──────┴───────┐
       │   SRAM/Flash │
       └──────────────┘
              │
        AHB → APB Bridge
              │
           APB Bus
      ────────┼──────────
        │     │      │
       GPIO  UART   I2C
              │
             SPI
```

### AHB
- AHB = Advanced High-performance Bus

### APB
- APB = Advanced Peripheral Bus


| 구분     | AHB             | APB                 |
| ------ | --------------- | ------------------- |
| 목적     | 빠른 데이터 전송       | 주변장치 제어             |
| 속도/대역폭 | 높음              | 상대적으로 낮음            |
| 구조     | 복잡              | 단순                  |
| 주로 연결  | CPU, RAM, DMA 등 | GPIO, UART, Timer 등 |
| 비유     | 고속도로            | 동네 도로               |
