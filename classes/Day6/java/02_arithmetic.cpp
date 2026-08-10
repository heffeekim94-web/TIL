// 02_arithmetic.cpp — 기본 문법 ②: 산술·비교·논리 연산과 형변환
// 목적: 사칙연산, 정수/실수 나눗셈의 차이, 증감·복합대입 연산자, 형변환,
//       그리고 <cmath> 함수까지 로봇 코드에서 실제로 쓰는 계산 패턴을 훑는다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o arithmetic src/02_arithmetic.cpp
// 실행  : ./arithmetic

#include <cmath>
#include <iostream>

int main() {
    // ── 1. 사칙연산과 나머지 ─────────────────────────────────
    int a = 7, b = 2;
    std::cout << "[1] 사칙연산 (a=7, b=2)\n";
    std::cout << "  a + b = " << (a + b) << "\n";
    std::cout << "  a - b = " << (a - b) << "\n";
    std::cout << "  a * b = " << (a * b) << "\n";
    std::cout << "  a % b = " << (a % b) << "  (나머지 연산, 정수에만 쓸 수 있다)\n\n";

    // ── 2. 정수 나눗셈 vs 실수 나눗셈 ────────────────────────
    // C++에서 가장 자주 나오는 실수 버그 중 하나: int끼리 나누면 소수점이 그냥 버려진다.
    std::cout << "[2] 나눗셈 — Python과 가장 다른 부분\n";
    std::cout << "  a / b (int / int)          = " << (a / b) << "  (3.5가 아니라 3 — 소수점 버림)\n";
    std::cout << "  (double)a / b              = " << (static_cast<double>(a) / b)
              << "  (하나라도 double로 바꿔야 실수 나눗셈)\n";
    std::cout << "  7.0 / 2                    = " << (7.0 / 2) << "  (리터럴 자체를 실수로 쓰면 간단)\n\n";

    // ── 3. 복합 대입 연산자 ─────────────────────────────────
    int score = 10;
    std::cout << "[3] 복합 대입 연산자 (score 시작값 = 10)\n";
    score += 5;  std::cout << "  score += 5  -> " << score << "\n";
    score -= 2;  std::cout << "  score -= 2  -> " << score << "\n";
    score *= 3;  std::cout << "  score *= 3  -> " << score << "\n";
    score /= 4;  std::cout << "  score /= 4  -> " << score << "\n\n";

    // ── 4. 증감 연산자: 전위(++x) vs 후위(x++) ──────────────
    // 주의: i++와 i를 같은 문장(같은 std::cout 줄) 안에 같이 쓰면 "언제 증가되는지" 순서가
    // 보장되지 않아 정의되지 않은 동작(undefined behavior, -Wsequence-point 경고)이 됩니다.
    // 그래서 아래처럼 증가와 출력을 항상 별도 문장으로 나눕니다.
    int i = 5;
    std::cout << "[4] 증감 연산자 (i 시작값 = 5)\n";

    int post_result = i++;   // 후위(postfix): "증가 전" 값을 먼저 반환하고, 그 다음 i를 1 늘린다
    std::cout << "  i++ (후위) 반환값 = " << post_result << ", 실행 후 i = " << i << "  (반환은 증가 전 값)\n";

    int pre_result = ++i;    // 전위(prefix): 먼저 i를 1 늘리고, 그 "증가된" 값을 반환한다
    std::cout << "  ++i (전위) 반환값 = " << pre_result << ", 실행 후 i = " << i << "  (반환은 증가 후 값)\n";

    std::cout << "  로봇 코드의 for(int i=0; i<n; ++i) 는 관례상 전위 ++i를 씁니다"
              << " (반환값을 쓰지 않으므로 의미 차이는 없지만 습관입니다).\n\n";

    // ── 5. 비교 연산자와 논리 연산자 ─────────────────────────
    double battery = 42.0;
    bool lidar_ok = true, imu_ok = false;
    std::cout << "[5] 비교·논리 연산자\n";
    std::cout << "  battery < 50.0            = " << std::boolalpha << (battery < 50.0) << "\n";
    std::cout << "  battery >= 20.0           = " << (battery >= 20.0) << "\n";
    std::cout << "  lidar_ok && imu_ok        = " << (lidar_ok && imu_ok) << "  (둘 다 true여야 true)\n";
    std::cout << "  lidar_ok || imu_ok        = " << (lidar_ok || imu_ok) << "  (하나만 true여도 true)\n";
    std::cout << "  !imu_ok                   = " << (!imu_ok) << "  (부정)\n\n";

    // ── 6. 형변환(casting) ──────────────────────────────────
    std::cout << "[6] 형변환\n";
    double precise = 3.99;
    int truncated = static_cast<int>(precise);   // static_cast: 의도를 명시하는 안전한 형변환
    std::cout << "  static_cast<int>(3.99) = " << truncated << "  (반올림이 아니라 소수점 버림!)\n";

    int small = 300;
    // char로 좁히면 표현 범위(대략 -128~127)를 넘어서 값이 이상해질 수 있다 — 형변환의 위험.
    char narrowed = static_cast<char>(small);
    std::cout << "  static_cast<char>(300) = " << static_cast<int>(narrowed)
              << "  (char의 표현 범위를 넘어가 값이 깨졌다 — 형변환은 항상 범위를 의식할 것)\n\n";

    // ── 7. <cmath> — 로봇 계산에 자주 쓰는 수학 함수 ─────────
    double dx = 3.0, dy = 4.0;
    double distance = std::sqrt(dx * dx + dy * dy);   // 두 점 사이 거리 (피타고라스)
    std::cout << "[7] <cmath> 함수\n";
    std::cout << "  std::sqrt(dx*dx + dy*dy) = " << distance << "  (dx=3, dy=4 → 3-4-5 직각삼각형)\n";
    std::cout << "  std::pow(2.0, 10)        = " << std::pow(2.0, 10) << "\n";
    std::cout << "  std::abs(-7)             = " << std::abs(-7) << "\n";
    std::cout << "  std::round(3.6)          = " << std::round(3.6) << "\n";

    return 0;
}
