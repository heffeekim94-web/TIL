DATE 2026 Sept 18, Friday

프로젝트 
- 노션 사용
    - 매일 권장
- 피그마로 아이디어 구성 추천
- 실습시간 2~5
- 오전 교습시간
- 5~6 설계 시간

---

오늘 내용
- MCU
- 메모리
- 타이머 
- PWM

외우기

---

cluster
- 지연 예방
- 라즈베리 파이

---

PID 제어 

센서 입력
- GPIO,ADC

계산 시점 

출력


---

MCU 구조
- pin
    - ADC, UART - 통신 프로토컬
- 프로토컬 알아보기

cortex-M : MCU type

정의된 핀대로 입력

라즈베리 4

핀맵 사용

shematic 잘 봐야 함.

중국산은 설명은 본인들끼리, 표기 오차 등이 있다

되도록이면 정품 사용 권장

arduino는 ATmega
mega - 칩이 크고 핀이 많다
칩 자체에 대한 schematic도 봐야 한다

아두이노는 핀맵 형태로 쉽게 나온 제품

---

sbc
- single board computer
- 라즈베리 파이 
- 통합 되어 있다.
- 운영체제 설치 가능
- ros 설치
- 카메라 기능 설치
- 메가 - 옛날 / 기가 - 요즘
    - dram
- OS
- 부팅 키는데 몇초
    - 성능이 높고 메모리가 높아서 체크할 사항이 많아서 
- software 담당
- 엣지에 gpu가 들어서 오는 개념

VS

mcu 
- 운영체제 설치 불가능
- 모터를 제어
- 제어 영역
- 센서 노이즈 필터링
- 속도 차이: kb - mb 수준
    - dram 말고 sm - 기가바이트 영역의 저장
    - 변수 지정, step 저장
- flash 메모리
    - 업로드라는 코드 저장 공간
    - 용량이 차면 업로드가 안됨
    - 코드 다이어트 하는 계열의 직업도, 연구 분야도 있음
    - 코드 개발자가 별로 없다.
    - mcu만 다루는 인재 찾기가 이잡기 수준
    - 연봉 높다
    - 어셈블리 언어
- rtos - os 체계
- 부팅 속도가 높음. 가겹기 때문
- 지연: nano second 
- hardware 담당

<br>

sbc-mcu
- usb 선으로 연결
- 신호 주고 받는 실시간성을 볼 수 있음
- 일반 통신 말고 유선 or lan통신 - 규격 정해져 있음

lan 통신 규격
- lan port 가닥
- 인터넷 빠르려면 8가닥을 사용하는 것 
- 라즈베리는 6가닥 까지
- 3D 라이다는 CAT.6e 사용 충분

클럽 차이 
- 단위속도 
- 수백 메가 사이즈 
-

---

메모리
- 이진수, 16진수 사용
- 이진수
    - 01010001
- 16진수
    - 25, 26, 2C ....
- 아두이노는 on/off 함수가 정해져있음
- 윈도우 7까지만 메모리 지정 지원
- 우리는 이미 되어 있는 메모리 지정에 ai를 사용하여 사용하는 것

---

레지스터와 HAL

ST- LINK 안함

---

GPIO
- 핀 이용할 수 있음
- 거리감지 센서
- 입력/출력/통신(다른 제어기와)/타이머(리얼타임 RTC 모듈)/아날로그 제어
    - 아날로그 
        - BLDC 모터나 자세한 제어를 할때 
        - 입력/ 출력도 이렇게 받을 수 있음
        - 가변저항 / 저항
            - 가변저항
                - 돌려가면서 옴을 올리고 낮추고 가능
            - 저항
        - 언어가 정해져있음
            ... (analog, INPUT) or (analog, OUTPUT)
            


엔코더 
- 광학적
    - 디지털
        - CD에 01010011 주소가 새겨져 있음
        - 디스크에 저장하여 읽는 것
        - 모아서 계산해서 얼마나 회전했는지 보는 것 
        - ![광학 센서]()
- 물리적
    - 아날로그
    
---

버튼 입력과 풀업
- PLC
    - 물리적인 방법을 사용
    - LD라는 언어를 사용
    - 도면이 따로 있음
    - RELAY는 뺏다 꼈다 할 수 있다.
        - 반도체화 하는 것이  TRANSISTOR
            - 5v 12v가 일반적
            - 220v는 없는 것 
            - 이렇게 transistor가 많은 집합이 반도체
            - 게이트들을 많이 만드는 것 
- 버튼이 너무 오래 되면 안눌릴때도 있지만 

<br>

폴링의 응답 시간
- 메인 루프가 주기적으로 입력 
- 눌리는 시간을 늘리면..

---

전기가 흐르는 경우를 HIGH
안흐르는 경우 LOW

논리를 흐르고 안흐르고로 조절

---

인터럽트 처리 흐름
- code 
```
while (1){
    모터회전 (30) 
    if (도착){
        종료
    }
}
```
장애물이 나타나거나 비상 정지를 해야 할때는 이런 코드를 사용할 수 없다
인터럽트 
    계속 동작을 하고 있다가 
    다른 조건이 나타나면 동작을 멈추는 것

[인터럽트에 대한 상세 설명](https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=proscw&logNo=220650635893)


- [ISR](https://www.google.com/search?sca_esv=6710bc477f81f8b5&sxsrf=APpeQnvd6esExJ1ILPd4cuLqvq52GKq3Nw:1789701633599&udm=2&fbs=ABfTbFUgt-aXEFkBhPo84x72c1XoLHFs6TcISYM3FayWAWWA70DBExgkDFCpIGAUraPZqPpSs1EXRrKCiKydXz2VHg4BL0rDRmIxVf27UpgdHNcHqrOe3fTEsBhT7klfW0nLunAvu7Gpe18QTEKqkAn-7WVBvS8BZZudnhqIpC1RLvO5QCda61mR51upT9TVB8RUBBp3Hgt_kTHwdr2wjqSSggDXWClIrg&q=ISR+%EC%9D%B8%ED%84%B0%EB%9F%BD%ED%8A%B8&sa=X&ved=2ahUKEwink_-QlveWAxWtklYBHRXjAV0QtKgLegQIGhAB&biw=1534&bih=951&dpr=1#sv=CAMSURoyKhBlLWRVc183aURBLVdHU0JNMg5kVXNfN2lEQS1XR1NCTToObnBGek5HUW1jRjM0M00gBCoXCgFzEhBlLWRVc183aURBLVdHU0JNGAEwARgHIJum2PsNSggQARgBIAEoAQ)
    - 프로그램이 흘러가다가 이 장치에서 진행 되다가 메인으로 돌아가 작업을 재개 하는 것 
    - ms정도 걸림
    - 메모리 자채를 멈춰야 할 때 수행 
- 순간 인터럽트로 인해 진행되는 다는 행동은 nanosecond가 걸리는 속도 정도여야 한다. 

---

우선 순위..?

---


추 후 

타이머 
- 월요일날 

---

PWM
- 시간 개념
- 몇초 흘러가는지에 따라 각도를 제어할 수 있음
- 천천히 돌리려면 시간 제어로 천천히 돌리는 것 
- pulse의 폭을 변조를 해서 제어하는 방식임
- 대부분의 모터에서 사용
- 나누어서 제어 가능 
    - 1이되는 시간 0이 되는 시간

---

-end

윈도우 위젯 사용



