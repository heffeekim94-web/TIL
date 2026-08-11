// 01_variables.cpp — 기본 문법 ①: 변수 선언과 기본 타입
// 목적: C++은 Python(5강)과 달리 변수를 쓰기 전에 "이 변수는 어떤 타입인가"를
//       반드시 선언해야 한다는 것을 정수·실수·문자·문자열·배열·상수 각각으로 확인한다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o variables src/01_variables.cpp
// 실행  : ./variables

#include <iostream>
#include <string>

int main() {
    // ── 1. 정수 계열 ────────────────────────────────────────
    // 크기가 다른 정수 타입들. 로봇 코드에서는 "이 값이 음수가 될 수 있는가"로
    // int(부호 있음) / unsigned int(부호 없음)를 고른다.
    short small_count = 12;                    // 짧은 정수 (보통 2바이트)
    int battery_percent = 87;                   // 가장 흔히 쓰는 기본 정수 (보통 4바이트)
    long total_ticks = 1234567890L;              // 더 큰 정수가 필요할 때
    unsigned int sensor_id = 3;                  // 음수가 없는 값(ID, 개수 등)에 사용

    std::cout << "[1] 정수 계열\n";
    std::cout << "  short small_count       = " << small_count << "\n";
    std::cout << "  int battery_percent     = " << battery_percent << "\n";
    std::cout << "  long total_ticks        = " << total_ticks << "\n";
    std::cout << "  unsigned int sensor_id  = " << sensor_id << "\n";
    std::cout << "  sizeof(int)  = " << sizeof(int) << " 바이트, "
              << "sizeof(long) = " << sizeof(long) << " 바이트\n\n";

    // ── 2. 실수 계열 ────────────────────────────────────────
    // float(단정밀도, 4바이트)은 정밀도가 낮고 빠름, double(배정밀도, 8바이트)은 정밀도가 높음.
    // 로봇 좌표·속도 계산에는 특별한 이유가 없으면 double을 기본으로 씁니다.
    // 리터럴(literal, 코드에 직접 적어 넣은 값 그 자체. 3.14f, 87, "abc" 같은 것들)
    float rough_distance = 3.14f;   // 리터럴 끝의 f는 "이건 float다"라는 표시
    double target_speed = 0.35;     // 기본 선택

    std::cout << "[2] 실수 계열\n";
    std::cout << "  float  rough_distance = " << rough_distance << " (정밀도 낮음)\n";
    std::cout << "  double target_speed   = " << target_speed << " (기본 선택)\n\n";

    // ── 3. bool / char / string ─────────────────────────────
    bool is_connected = true;              // 참/거짓 두 값만 가짐
    char sensor_code = 'L';                // 문자 하나 (작은따옴표)
    std::string robot_name = "kant-01";    // 문자열 (std::string, 큰따옴표) — C 스타일 char* 대신 이걸 쓴다

    std::cout << "[3] bool / char / string\n";
    std::cout << "  bool is_connected  = " << std::boolalpha << is_connected << "\n";
    std::cout << "  char sensor_code   = " << sensor_code << "\n";
    std::cout << "  string robot_name  = " << robot_name << "\n";
    std::cout << "  robot_name + \"-v2\" = " << (robot_name + "-v2") << "  (문자열 이어붙이기)\n\n";

    // ── 4. 배열 — 같은 타입 값을 고정 개수로 묶기 ────────────
    int readings[5] = {12, 8, 15, 3, 9};   // 크기 5, 컴파일 때 크기가 정해진다 (8강 1절 '스택' 조건)
    std::cout << "[4] 배열\n";
    std::cout << "  readings[0] = " << readings[0] << ", readings[4] = " << readings[4] << "\n";
    std::cout << "  배열 전체 크기(바이트) = " << sizeof(readings)
              << ", 원소 1개 크기 = " << sizeof(readings[0])
              << " -> 원소 개수 = " << sizeof(readings) / sizeof(readings[0]) << "\n\n";

    // ── 5. 상수 — const / constexpr ─────────────────────────
    const double max_speed = 1.0;          // 한 번 초기화하면 다시 바꿀 수 없다 (실행 중 결정 가능)
    // constexpr(constant expression, 컨스턴트 익스프레션의 줄임): const는 "실행 중 한 번만" 정해지면
    // 되지만, constexpr은 "컴파일하는 순간에 이미" 값이 확정되어야 한다는 더 강한 조건이다.
    constexpr int max_retries = 3;
    // max_speed = 2.0;   // 주석을 풀면 컴파일 에러 — 언어가 실수를 막아 준다

    std::cout << "[5] 상수\n";
    std::cout << "  const double max_speed   = " << max_speed << "\n";
    std::cout << "  constexpr int max_retries = " << max_retries << "\n\n";

    // ── 6. auto — 타입 추론 ─────────────────────────────────
    // auto는 "타입이 없어지는 것"이 아니라, 오른쪽 값을 보고 컴파일러가 타입을 대신 적어 주는 것이다.
    auto lidar_range = 12.0;      // double 로 추론
    auto loop_count = 100;        // int 로 추론
    std::cout << "[6] auto (타입 추론)\n";
    std::cout << "  auto lidar_range = 12.0  -> double 로 추론, 값 = " << lidar_range << "\n";
    std::cout << "  auto loop_count  = 100   -> int 로 추론, 값 = " << loop_count << "\n\n";

    // ── 7. 변수의 범위(scope) ───────────────────────────────
    int x = 1;
    std::cout << "[7] 변수 범위(scope)\n";
    std::cout << "  블록 밖 x = " << x << "\n";
    {
        int x = 2;   // 바깥 x와는 별개의 변수 (블록 안에서만 존재)
        std::cout << "  블록 안 x = " << x << " (바깥 x를 잠시 가림)\n";
    }
    std::cout << "  블록을 나온 뒤 x = " << x << " (바깥 x는 그대로였다)\n\n";

    std::cout << "[참고] 초기화하지 않은 변수를 그냥 읽으면 어떤 값이 나올지 예측할 수 없습니다\n";
    std::cout << "  (정의되지 않은 동작, undefined behavior). 그래서 변수는 선언과 동시에\n";
    std::cout << "  항상 초기값을 주는 습관을 들이세요 — 이 파일의 모든 변수가 그렇게 되어 있습니다.\n";

    return 0;
}
