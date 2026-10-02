// 09_template.cpp — 8강 5절: 템플릿
// 목적: 하나의 함수 템플릿이 여러 타입에 대해 "런타임 비용 없이" 동작하는 것을 확인한다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o template_demo src/09_template.cpp
// 실행  : ./template_demo

#include <algorithm>
#include <iostream>
#include <string>

// template <typename T> : "이 함수는 T라는 이름의 아무 타입에 대해서나 동작한다"는 선언.
// 컴파일러가 실제로 사용된 타입(double, int, ...)마다 전용 코드를 따로 만들어 주는데,
// 이 과정을 템플릿 인스턴스화(template instantiation, "T 자리에 실제 타입을 채워
// 진짜 함수를 찍어낸다"는 뜻)라고 부른다. 실행 중이 아니라 컴파일할 때 끝나는 작업이라
// 런타임 비용이 없다.
template <typename T>
T clamp(T value, T lo, T hi) {
    return std::max(lo, std::min(value, hi));
}

// 템플릿은 함수뿐 아니라 아래처럼 "값을 출력하는" 일반적인 헬퍼에도 자주 쓰인다.
template <typename T>
void printLabeled(const std::string& label, const T& value) {
    std::cout << "  " << label << " = " << value << "\n";
}

int main() {
    std::cout << "[1] clamp<T> — 같은 코드, 다른 타입\n";

    double speed = clamp(1.8, 0.0, 1.0);      // T = double 로 자동 추론 -> 1.0 (속도 상한)
    printLabeled("clamp(1.8, 0.0, 1.0)  [double]", speed);

    int pixel = clamp(150, 0, 255);           // T = int 로 자동 추론 -> 150 (픽셀값)
    printLabeled("clamp(150, 0, 255)   [int]", pixel);

    int low = clamp(-40, 0, 255);
    printLabeled("clamp(-40, 0, 255)   [int, 하한에 걸림]", low);

    // T를 명시적으로 지정할 수도 있다 (보통은 인자로부터 자동 추론되므로 생략 가능).
    double explicit_t = clamp<double>(0.9, 0.0, 1.0);
    printLabeled("clamp<double>(0.9, 0.0, 1.0)", explicit_t);

    std::cout << "\n[2] 템플릿이 요구하는 조건 — 비교(<, >)가 가능한 타입이어야 한다\n";
    std::cout << "  clamp는 내부에서 std::min/std::max(<, > 비교)를 쓰기 때문에,\n";
    std::cout << "  비교 연산자가 없는 타입(예: 직접 정의한 벡터 구조체에 operator< 가 없는 경우)을\n";
    std::cout << "  넣으면 컴파일 에러가 납니다 — 실행 전에 잡힌다는 뜻이라 오히려 안전합니다.\n";

    return 0;
}
