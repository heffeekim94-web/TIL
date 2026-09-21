## ALU
- ALU = Arithmetic Logic Unit
- CPU Core 안에서 실제 계산을 담당하는 부분
- 산술 논리 장치

position:
```
CPU Core 🧠
│
├── Control Unit → "무슨 일을 할지 지시"
├── Register     → "잠깐 데이터를 보관"
└── ALU          → "실제로 계산" 🧮
```

<br>

ALU가 하는 일:
```
| 종류  | 예시        | ALU가 하는 일 |
| --- | --------- | --------- |
| 덧셈  | `3 + 5`   | → `8`     |
| 뺄셈  | `10 - 4`  | → `6`     |
| 비교  | `5 > 3`   | → 참       |
| AND | `1 AND 0` | → `0`     |
| OR  | `1 OR 0`  | → `1`     |
| XOR | `1 XOR 1` | → `0`     |
```

<br>

계산 흐름:
```C
int a = 3;
int b = 5;
int c = a + b;
```
- codels

```
Register
a = 3
b = 5
   │
   ▼
┌──────────┐
│   ALU    │
│  3 + 5   │
└────┬─────┘
     │
     ▼
Register
c = 8
```
- cpu simplifies

<br>

flow:
```
MCU
 └─ CPU Core
      ├─ ALU       ← 계산 🧮
      ├─ Register  ← 임시 데이터
      └─ Control Unit
           │
           ↓
         Bus
           ↓
         GPIO
           ↓
      센서 / LED / 모터드라이버
```

