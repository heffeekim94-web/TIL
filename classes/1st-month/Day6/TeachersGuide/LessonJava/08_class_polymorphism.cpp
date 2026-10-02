// 08_class_polymorphism.cpp — 8강 4절: 클래스와 다형성 (virtual)
// 목적: virtual + override + 가상 소멸자로 다형성이 동작하는 모습과,
//       virtual을 빠뜨리면 어떻게 "조용히" 틀어지는지를 같은 파일에서 대조한다.
//
// 다형성(polymorphism, 폴리모피즘) = "여러(poly) 모습(morph)"이라는 뜻 그대로,
// 같은 코드(s->read())가 실제 객체 타입(Lidar냐 Imu냐)에 따라 다르게 동작하는 성질.
// virtual(버추얼) 키워드가 있어야 이 성질이 켜진다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o class_polymorphism src/08_class_polymorphism.cpp
// 실행  : ./class_polymorphism

#include <iostream>
#include <memory>
#include <vector>

// ── 1. 올바른 다형성: virtual + override + 가상 소멸자 ────────────
class Sensor {
public:
    // 가상 소멸자(virtual destructor): 부모 포인터로 자식 객체를 delete할 때
    // 자식의 소멸자까지 제대로 불리게 하려면 부모 소멸자도 virtual이어야 한다 (상속 시 필수!).
    virtual ~Sensor() = default;
    // 순수 가상 함수(pure virtual function): 끝에 "= 0"이 붙으면 본체가 없다는 뜻으로,
    // "자식 클래스가 반드시 이 함수를 직접 구현해야 한다"는 규칙이 된다.
    // 이렇게 순수 가상 함수를 하나라도 가진 클래스를 추상 클래스(abstract class)라고 부르며,
    // Sensor 자체로는 객체를 만들 수 없고 반드시 Lidar처럼 구현을 채운 자식을 통해서만 쓴다.
    virtual std::vector<double> read() = 0;
    bool isConnected() const { return connected_; }

// protected(프로텍티드): private처럼 클래스 밖에서는 못 건드리지만, 상속받은
// 자식 클래스 안에서는 접근할 수 있는 접근 지정자. "가족(자식)에게만 공개"라고 생각하면 된다.
protected:
    bool connected_ = true;
};

class Lidar : public Sensor {
public:
    std::vector<double> read() override {     // override: 재정의임을 컴파일러가 검증해 준다
        return {0.8, 0.82, 0.85};
    }
};

class Imu : public Sensor {
public:
    std::vector<double> read() override {
        return {0.01, -0.02, 9.81};   // roll, pitch, accel_z 라고 가정
    }
};

void printReadings(const std::vector<std::unique_ptr<Sensor>>& sensors) {
    for (const auto& s : sensors) {
        auto data = s->read();   // 다형성: 실제 객체(Lidar/Imu)의 read()가 호출된다
        std::cout << "  read() -> [";
        for (std::size_t i = 0; i < data.size(); ++i) {
            std::cout << data[i] << (i + 1 < data.size() ? ", " : "");
        }
        std::cout << "]\n";
    }
}

// ── 2. 대조군: virtual을 빠뜨리면 무슨 일이 생기는가 ───────────────
// (미니 퀴즈 5번과 연결되는 예제. 실무 코드로 이렇게 짜면 안 되지만,
//  "왜 안 되는지"를 눈으로 보기 위한 교육용 예제입니다.)
struct BadBase {
    std::string label() { return "BadBase"; }   // virtual이 없다!
};

struct BadDerived : BadBase {
    std::string label() { return "BadDerived"; }   // "재정의"가 아니라 이름을 새로 가리는 것뿐
};

int main() {
    std::cout << "[1] 올바른 다형성 (virtual + override)\n";
    std::vector<std::unique_ptr<Sensor>> sensors;
    sensors.push_back(std::make_unique<Lidar>());
    sensors.push_back(std::make_unique<Imu>());
    printReadings(sensors);
    std::cout << "  -> Lidar, Imu 각각 자기 read()가 호출됐다. 내일 Ultrasonic을 추가해도\n";
    std::cout << "     printReadings() 함수는 한 줄도 안 바뀐다.\n\n";

    std::cout << "[2] virtual이 없으면? (BadBase / BadDerived)\n";
    BadDerived bd;
    BadBase& ref = bd;   // 부모 타입 "참조"로 자식 객체를 가리킴 (다형성을 기대하는 상황)
    std::cout << "  bd.label()  (자식 타입으로 직접 호출)      = " << bd.label() << "\n";
    std::cout << "  ref.label() (부모 참조로 호출, virtual 없음) = " << ref.label() << "\n";
    std::cout << "  -> virtual이 없으면 '부모 참조로 부를 때' 자식 버전이 아니라\n";
    std::cout << "     부모 버전이 실행된다. 컴파일 에러가 아니라서 더 위험하다 (4절 FAQ 참고).\n";

    return 0;
}
