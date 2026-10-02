// 04_functions.cpp — 기본 문법 ④: 함수
// 목적: 함수 선언/정의, 매개변수와 반환값, 기본 인자, 오버로딩, 참조로 값 바꾸기,
//       재귀 함수까지 — 8강 본문(포인터·참조·클래스)에서 바로 쓰이는 기초를 다진다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o functions src/04_functions.cpp
// 실행  : ./functions

#include <iostream>

// ── 함수 선언(프로토타입) ───────────────────────────────────
// 정의(본문)는 아래에 따로 두고, 여기서는 "이런 함수가 있다"만 컴파일러에 미리 알린다.
// 파일이 커지면 선언은 헤더(.hpp)에, 정의는 소스(.cpp)에 두는 방식(7강)으로 이어진다.
int add(int a, int b);

// ── 1. 기본 함수: 매개변수와 반환값 ─────────────────────────
int add(int a, int b) {
    return a + b;
}

// void 함수 — 반환값이 없는 함수. "계산"이 아니라 "행동"을 표현할 때 쓴다.
void printBanner(const std::string& text) {
    std::cout << "=== " << text << " ===\n";
}

// ── 2. 기본 인자(default argument) ──────────────────────────
// 호출할 때 인자를 생략하면 이 기본값이 쓰인다. 기본값은 뒤쪽 매개변수부터 채워야 한다.
double applyGain(double value, double gain = 1.0) {
    return value * gain;
}

// ── 3. 함수 오버로딩(overloading) ───────────────────────────
// 이름은 같아도 매개변수의 타입/개수가 다르면 서로 다른 함수로 인식된다.
// 컴파일러가 호출 시점의 인자를 보고 알맞은 버전을 자동으로 고른다 (Python에는 없는 개념).
std::string describe(int x) { return "int: " + std::to_string(x); }
std::string describe(double x) { return "double: " + std::to_string(x); }
std::string describe(const std::string& x) { return "string: " + x; }

// ── 4. 참조로 값을 바꾸는 함수 — swap ───────────────────────
// 값 전달로는 "함수 안에서 바뀐 값을 밖으로 돌려줄 방법"이 return 하나뿐이다.
// 여러 값을 동시에 바꾸고 싶으면 참조(&)를 매개변수로 받는다.
void swapValues(int& x, int& y) {
    int temp = x;
    x = y;
    y = temp;
}

// ── 5. 재귀 함수(recursion, 리커전) — 함수가 자기 자신을 부른다 ──────
// 종료 조건이 반드시 있어야 한다. 없으면 함수 호출이 끝없이 쌓이다가
// 스택 오버플로(stack overflow — 8강 1절에서 배운 "스택"의 저장 공간이 다 차서
// 프로그램이 강제 종료되는 현상, 8강 FAQ)로 이어진다.
unsigned long long factorial(int n) {
    if (n <= 1) {
        return 1;   // 종료 조건 (base case)
    }
    return static_cast<unsigned long long>(n) * factorial(n - 1);   // 자기 자신 호출
}

int main() {
    printBanner("함수 예제 시작");

    // ── 1. 기본 호출 ─────────────────────────────────────────
    std::cout << "[1] 기본 함수\n";
    std::cout << "  add(3, 4) = " << add(3, 4) << "\n\n";

    // ── 2. 기본 인자 ─────────────────────────────────────────
    std::cout << "[2] 기본 인자\n";
    std::cout << "  applyGain(0.5)      = " << applyGain(0.5) << "  (gain 생략 -> 기본값 1.0)\n";
    std::cout << "  applyGain(0.5, 2.0) = " << applyGain(0.5, 2.0) << "  (gain 직접 지정)\n\n";

    // ── 3. 오버로딩 ──────────────────────────────────────────
    std::cout << "[3] 오버로딩 — 같은 이름 describe, 다른 타입\n";
    std::cout << "  describe(42)        -> " << describe(42) << "\n";
    std::cout << "  describe(3.14)      -> " << describe(3.14) << "\n";
    std::cout << "  describe(\"lidar\")   -> " << describe(std::string("lidar")) << "\n\n";

    // ── 4. 참조로 값 바꾸기 ──────────────────────────────────
    int left_speed = 10, right_speed = 20;
    std::cout << "[4] 참조로 값 바꾸기 (swapValues)\n";
    std::cout << "  교체 전: left=" << left_speed << ", right=" << right_speed << "\n";
    swapValues(left_speed, right_speed);
    std::cout << "  교체 후: left=" << left_speed << ", right=" << right_speed
              << "  (함수 안에서 원본 두 개를 직접 바꿨다)\n\n";

    // ── 5. 재귀 함수 ─────────────────────────────────────────
    std::cout << "[5] 재귀 함수 — factorial(n) = n * factorial(n-1)\n";
    for (int n = 1; n <= 6; ++n) {
        std::cout << "  factorial(" << n << ") = " << factorial(n) << "\n";
    }

    return 0;
}
