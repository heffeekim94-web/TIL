// 07_raii_smart_pointer.cpp — 8강 3절: RAII와 스마트 포인터
// 목적: unique_ptr(단독 소유) · shared_ptr(공동 소유, 참조 카운트) · std::move(이동)를
//       생성자/소멸자 로그와 use_count()로 직접 확인한다.
//
// RAII = Resource Acquisition Is Initialization (리소스 어퀴지션 이즈 이니셜라이제이션).
// 이름은 어렵지만 뜻은 "자원(메모리 등)의 수명을 객체의 수명에 묶는다"는 것뿐이다.
// 스마트 포인터(smart pointer)는 이 원칙을 포인터에 적용해, 객체가 사라질 때
// 힙 메모리도 자동으로 delete되게 만든 도구다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o raii_smart_pointer src/07_raii_smart_pointer.cpp
// 실행  : ./raii_smart_pointer

#include <iostream>
#include <memory>

class Motor {
public:
    // explicit(익스플리싯): "Motor m = "A";" 처럼 문자열이 슬쩍 Motor로 자동 변환되는
    // 것을 막아 주는 키워드. 생성자가 인자를 하나만 받을 때 실수를 막기 위해 습관적으로 붙인다.
    explicit Motor(std::string name) : name_(std::move(name)) {
        std::cout << "  [Motor " << name_ << "] 생성\n";
    }
    ~Motor() { std::cout << "  [Motor " << name_ << "] 소멸\n"; }
    void setSpeed(double v) { std::cout << "  [Motor " << name_ << "] speed=" << v << "\n"; }

private:
    std::string name_;
};

class Lidar {
public:
    Lidar() { std::cout << "  [Lidar] 생성\n"; }
    ~Lidar() { std::cout << "  [Lidar] 소멸\n"; }
};

void uniquePtrDemo() {
    std::cout << "-- unique_ptr: 단독 소유 --\n";
    auto motor = std::make_unique<Motor>("A");   // 힙에 생성, motor가 유일한 소유자
    motor->setSpeed(0.5);

    // auto motor2 = motor;         // 컴파일 에러! unique_ptr는 복사 금지
    auto motor2 = std::move(motor); // OK: 소유권이 motor -> motor2 로 이동
    std::cout << "  std::move 후 motor(원래 변수)가 비었는가? "
              << std::boolalpha << (motor == nullptr) << "\n";
    motor2->setSpeed(0.8);
    std::cout << "-- uniquePtrDemo() 끝 (motor2가 범위를 벗어나며 자동 delete) --\n";
}   // 여기서 motor2 소멸 -> Motor 소멸자 자동 호출. delete를 손으로 쓴 적이 없다.

void sharedPtrDemo() {
    std::cout << "-- shared_ptr: 공동 소유, 참조 카운트 --\n";
    auto lidar = std::make_shared<Lidar>();
    std::cout << "  생성 직후 use_count() = " << lidar.use_count() << "\n";

    {
        auto lidar2 = lidar;   // 복사 가능 — 참조 카운트가 2로 증가
        std::cout << "  lidar2 = lidar 복사 후 use_count() = " << lidar.use_count() << "\n";
    }   // 이 중괄호를 벗어나며 lidar2 소멸 -> 카운트 다시 1로 감소 (Lidar 객체 자체는 아직 안 지워짐)

    std::cout << "  안쪽 블록을 벗어난 뒤 use_count() = " << lidar.use_count() << "\n";
    std::cout << "-- sharedPtrDemo() 끝 (lidar도 사라지며 카운트 0 -> 이때 실제 delete) --\n";
}   // 여기서 lidar 소멸, 카운트 0 -> Lidar 소멸자 호출

int main() {
    std::cout << "[1] unique_ptr\n";
    uniquePtrDemo();

    std::cout << "\n[2] shared_ptr\n";
    sharedPtrDemo();

    std::cout << "\n[3] ROS2에서 흔히 쓰는 형태(감 잡기용, 실제 rclcpp 아님)\n";
    std::cout << "  auto node = std::make_shared<MyNode>();   // 10강에서 다시 만난다\n";

    return 0;
}
