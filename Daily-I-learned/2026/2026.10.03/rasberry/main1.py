import time
import serial

# 홈 기준 X +5°, Y +5°, 두 축 공통 속도 3°/s
COMMAND = "5 5 3"

with serial.Serial("/dev/ttyACM0", 115200, timeout=0.2) as board:
    time.sleep(2)
    board.write(b"\n")
    board.flush()
    time.sleep(0.2)
    board.reset_input_buffer()

    board.write((COMMAND + "\n").encode("ascii"))
    board.flush()
    print("전송:", COMMAND)

    try:
        end = time.monotonic() + 5
        while time.monotonic() < end:
            response = board.readline().decode(errors="replace").strip()
            if response:
                print(response)
    except KeyboardInterrupt:
        board.write(b"x")
        board.flush()
        print("정지 명령 전송")
