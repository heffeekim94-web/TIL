## GPIO
- General Purpose Input/Output
- 신호를 주고받는 핀
- MCU가 외부 장치와 0/1 전기 신호를 주고받는 기본 출입구.

예:
```
             MCU
       ┌─────────────┐
버튼 ──▶ GPIO Input  │
       │             │
LED  ◀── GPIO Output │
       └─────────────┘
```
```
버튼 안 누름 → GPIO = LOW  (0)
버튼 누름   → GPIO = HIGH (1)
```
- **Input(입력)**으로 설정하면 MCU가 외부 신호를 읽는다.

결과:
```
GPIO = HIGH → 전압 출력 → LED 켜짐 💡
GPIO = LOW  → 전압 낮음 → LED 꺼짐
```

---

MCU와 GPIO의 관계성:
```
거리 센서
   ↓
 GPIO (Input)
   ↓
  MCU
   ↓
판단/프로그램
   ↓
 GPIO (Output)
   ↓
모터 드라이버
   ↓
 모터
 ```

다만, 모터를 GPIO에 직접 연결하는 불가. GPIO는 큰 전류 공급은 무리, 모터 드라이버가 중계해야 함. 중간에 설치 필요.

```
CPU
 ↓
AHB
 ↓
APB
 ↓
GPIO peripheral
 ↓
GPIO 핀
 ↓
LED / 버튼 / 센서
```

