// 05_stack_heap.cpp — 8강 1절: 스택과 힙
// 목적: 스택 객체는 함수를 벗어나면 "자동으로", 힙 객체는 delete 해야만 정리된다는 것을
//       생성자/소멸자 출력으로 직접 눈으로 확인한다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o stack_heap src/05_stack_heap.cpp
// 실행  : ./stack_heap

#include <iostream>
#include <vector>

class Motor {
public:
    // 생성자: 객체가 "만들어지는" 순간 자동 호출
    Motor() { std::cout << "  Motor 생성\n"; }
    // 소멸자: 객체가 "사라지는" 순간 자동 호출.
    // 이 "사라질 때 자동으로 정리된다"는 성질이 RAII(Resource Acquisition Is Initialization,
    // 자원 해제를 손으로 안 챙겨도 되게 만드는 원칙)의 핵심이다 — 3절에서 자세히 다룬다.
    ~Motor() { std::cout << "  Motor 소멸\n"; }
};

void control_loop() {
    std::cout << "-- control_loop() 시작 --\n";

    double target = 0.5;          // 스택: 함수 끝나면 자동 소멸
    Motor m;                      // 스택: m도 자동 소멸 (생성자가 지금 호출됨)

    // 힙: 실행 중 크기가 정해지는 데이터. vector 객체 자체는 스택에 있지만
    // 내부의 실제 숫자 360개는 힙에 할당된다.
    std::vector<double> scan(360, 0.0);
    std::cout << "  scan.size() = " << scan.size() << " (힙에 저장된 원소 개수)\n";

    (void)target;  // 이 예제에서는 값만 보여주고 별도로 쓰지 않는다는 표시
    std::cout << "-- control_loop() 끝 (여기서 target, m, scan이 전부 자동 정리됨) --\n";
}   // 함수 범위를 벗어나는 순간: m의 소멸자 호출, scan의 내부 힙 메모리도 자동 해제

int main() {
    std::cout << "[1] 스택 vs 힙 — 생성/소멸 시점 관찰\n\n";
    control_loop();
    std::cout << "\n(control_loop 밖) Motor 소멸 로그가 함수 안에서 이미 찍힌 것을 확인하세요.\n";

    // ── 힙을 직접 다루면 어떻게 되는지 비교 (다음 예제 03에서 위험을 더 자세히 본다) ──
    std::cout << "\n[2] 힙에 직접 할당하면? (오늘의 '위험' 예고편)\n";
    Motor* p = new Motor();   // 힙에 생성 — 자동으로 안 사라진다
    std::cout << "  p를 delete하지 않으면 소멸자가 절대 호출되지 않는다.\n";
    delete p;                 // 오늘은 안전하게 직접 정리 (3절부터는 스마트 포인터가 이 delete를 대신한다)
    std::cout << "  delete p 완료 — 방금 소멸자 로그가 찍혔다.\n";

    return 0;
}
