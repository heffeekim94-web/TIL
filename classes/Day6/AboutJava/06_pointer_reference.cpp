// 06_pointer_reference.cpp — 8강 2절: 포인터와 참조
// 목적: 값 전달 vs 참조 전달의 차이, const 참조 관용구, 포인터 기본 문법,
//       그리고 raw 포인터가 왜 위험한지(메모리 누수)를 안전하게 재현한다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o pointer_reference src/06_pointer_reference.cpp
// 실행  : ./pointer_reference

#include <iostream>
#include <vector>

// 값 전달: 호출할 때마다 벡터 전체를 복사한다 (느림). 함수 안에서 바꿔도 원본은 그대로.
double sumByValue(std::vector<double> scan) {
    scan[0] = -999.0;   // 이 함수 안의 복사본만 바뀐다 — 원본은 영향 없음
    double total = 0.0;
    for (double v : scan) total += v;
    return total;
}

// 참조 전달: 원본의 "별명"을 넘긴다. 복사가 없다.
// const 를 붙이면 "이 함수는 원본을 절대 바꾸지 않는다"는 약속이 된다 (읽기 전용).
double sumByConstRef(const std::vector<double>& scan) {
    // scan[0] = -999.0;   // 주석을 풀면 컴파일 에러 — const라서 못 바꾼다
    double total = 0.0;
    for (double v : scan) total += v;
    return total;
}

// 참조 전달(비-const): 원본을 실제로 바꾸고 싶을 때 쓴다.
void clearFirst(std::vector<double>& scan) {
    if (!scan.empty()) scan[0] = 0.0;   // 원본이 진짜로 바뀐다
}

int main() {
    std::vector<double> scan = {0.3, 8.2, 0.5, 12.0};

    std::cout << "[1] 값 전달 vs 참조 전달\n";
    std::cout << "  sumByValue 호출 전 scan[0]    = " << scan[0] << "\n";
    double s1 = sumByValue(scan);
    std::cout << "  sumByValue 결과              = " << s1 << "\n";
    std::cout << "  sumByValue 호출 후 scan[0]    = " << scan[0]
              << "  (복사본만 바뀌었으므로 원본은 그대로)\n\n";

    double s2 = sumByConstRef(scan);
    std::cout << "  sumByConstRef 결과            = " << s2
              << "  (복사 없이 계산, 원본 보호)\n\n";

    clearFirst(scan);
    std::cout << "  clearFirst 호출 후 scan[0]     = " << scan[0]
              << "  (비-const 참조라 원본이 실제로 바뀜)\n\n";

    // ── 2. 포인터 기본 문법 ─────────────────────────────────
    std::cout << "[2] 포인터 기본 문법\n";
    int battery = 87;
    int* battery_ptr = &battery;   // & : "battery의 주소를 가져와라"

    std::cout << "  battery 값        = " << battery << "\n";
    std::cout << "  battery의 주소     = " << &battery << "\n";
    std::cout << "  battery_ptr(포인터가 담은 값) = " << battery_ptr << "\n";
    std::cout << "  *battery_ptr (역참조: 가리키는 곳의 값) = " << *battery_ptr << "\n";

    *battery_ptr = 50;   // 포인터를 통해 원본 값을 바꿀 수 있다
    std::cout << "  *battery_ptr = 50 실행 후 battery = " << battery << "\n\n";

    int* empty_ptr = nullptr;   // nullptr: "아무것도 가리키지 않는다"는 명시적 표시
    std::cout << "  empty_ptr == nullptr ? " << std::boolalpha << (empty_ptr == nullptr) << "\n";
    if (empty_ptr != nullptr) {
        std::cout << *empty_ptr << "\n";   // 이 줄은 실행되지 않음 — nullptr 역참조는 크래시로 이어진다
    } else {
        std::cout << "  nullptr인지 먼저 확인하고 나서 역참조해야 안전하다.\n\n";
    }

    // ── 3. raw 포인터의 위험 #1 — 메모리 누수 ───────────────
    std::cout << "[3] raw 포인터의 위험 — 메모리 누수 (교육 목적, 의도적 누수)\n";
    for (int i = 0; i < 3; ++i) {
        int* leaked = new int(i);   // 힙에 할당하고 delete를 하지 않는다
        std::cout << "  new int(" << i << ") 할당 — delete를 안 하면 이 메모리는 영영 안 돌아온다.\n";
        (void)leaked;               // 일부러 delete leaked; 를 쓰지 않음 — 아래 valgrind로 확인
    }
    std::cout << "  ↑ 이 프로그램을 'valgrind --leak-check=full ./pointer_reference' 로 실행하면\n";
    std::cout << "    방금 만든 3개의 int가 'definitely lost'로 잡히는 것을 볼 수 있습니다.\n";
    std::cout << "    (11_leak_demo.cpp 에서 더 큰 예제와 make_unique로 고치는 법을 다룹니다)\n\n";

    // ── 4. raw 포인터의 위험 #2 — 댕글링 포인터는 "재현하지 않는다" ──
    // 댕글링 포인터(dangling pointer) = 가리키던 객체가 이미 사라졌는데(delete된 뒤)
    // 그 사라진 자리를 여전히 가리키고 있는 포인터. "매달려(dangling) 있다"는 뜻이다.
    std::cout << "[4] 댕글링 포인터 — 이 코드는 실행하지 않고 설명만 합니다\n";
    std::cout << "  int* q = new int(1);\n";
    std::cout << "  delete q;\n";
    std::cout << "  *q = 5;   // 이미 해제된 메모리에 쓰기 → 정의되지 않은 동작(UB)\n";
    std::cout << "  실제로 이 세 줄을 실행하면 크래시가 나거나, 더 나쁘게는 '우연히' 멀쩡해 보일 수도 있습니다.\n";
    std::cout << "  정의되지 않은 동작(undefined behavior)은 결과를 예측할 수 없다는 뜻이라\n";
    std::cout << "  이 예제 파일에서는 일부러 실행하지 않습니다. 3절 스마트 포인터가 이 문제 자체를 없앱니다.\n";

    return 0;
}
