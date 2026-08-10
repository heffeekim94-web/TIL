// 11_leak_demo.cpp — 8강 실습 5번(심화): valgrind로 메모리 누수 검출하기
// 목적: new만 반복하고 delete를 안 하면 실제로 누수가 잡힌다는 것을 valgrind로 확인하고,
//       make_unique로 바꾸면 누수가 사라지는 것도 같은 파일에서 스위치 하나로 비교한다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -g -o leak_demo src/11_leak_demo.cpp
// 실행(누수 확인)  : valgrind --leak-check=full ./leak_demo
//
// USE_SMART_POINTER를 0 -> 1로 바꾸고 다시 컴파일한 뒤 valgrind를 다시 돌려서
// "definitely lost"(데피니틀리 로스트, "확실히 잃어버린 메모리" — 프로그램이 끝날 때까지
// 아무도 delete하지 않은, valgrind가 확신하는 순수 누수) 항목이 사라지는지 비교해 보세요.
#define USE_SMART_POINTER 0

#include <iostream>
#include <memory>

class Motor {
public:
    explicit Motor(int id) : id_(id) {}
    void setSpeed(double v) { speed_ = v; }

private:
    int id_;
    double speed_ = 0.0;
};

int main() {
#if USE_SMART_POINTER
    std::cout << "[모드] make_unique 사용 — 누수 없음\n";
    for (int i = 0; i < 1000; ++i) {
        auto m = std::make_unique<Motor>(i);   // 범위(루프 한 바퀴)를 벗어나며 자동 delete
        m->setSpeed(0.5);
    }
#else
    std::cout << "[모드] raw new, delete 없음 — 의도적 메모리 누수\n";
    for (int i = 0; i < 1000; ++i) {
        Motor* m = new Motor(i);   // delete m; 이 없다 — 1000개의 Motor가 계속 쌓인다
        m->setSpeed(0.5);
        // delete m;   // 이 줄을 살리면 누수가 사라진다 (또는 위 make_unique 버전 사용)
    }
#endif

    std::cout << "프로그램 종료. valgrind --leak-check=full 로 실행해 결과를 확인하세요.\n";
    return 0;
}
