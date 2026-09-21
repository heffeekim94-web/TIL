## MCU 
https://omen-circle-24920305.figma.site/


MCU types: 임베디드(embedded)
-
#### Microcontroller Unit:

전자제품이나 로봇 안에서 센서값을 읽고, 모터 같은 장치를 제어하는 작은 컴퓨터

<br>

TIME
-  μs~ms 

<br>

장비 TYPE
- STM32
- Cortex - M
- SBC
- sub 장비
    - CPU
    - RAM
    - Flash memory
    - GPIO
    - ADC
    - PWM
    - 통신 기능
        - I²C
        - SPI
        - UART
        - ...

<br>

Does:
- 모터 제어 루프
    - PWM: Pulse Width Modulation 신호 만들기
        - on/off
- 센서 읽기
- 안전 정지 (E-stop)
- RTOS / 베어메탈
