ㅊmodule 2-2

이번 문제는 **센서 클래스를 만들면서 상속·다형성·메모리 관리·STL을 배우는 과제**예요. 앞처럼 한 단계씩 코드의 의미와 예시를 보면서 진행하겠습니다.

먼저 **`Sensor`라는 공통 설계도와 이를 상속하는 `Lidar`, `Imu`**부터 만들게요.

현재 `cpp_basics/build`에 있다면:

```bash
cd ..
mkdir -p sensors
```

`cpp_basics/sensors` 안에 **`sensor.hpp`** 파일을 만들고 작성하세요.

```cpp
#pragma once

#include <iostream>

class Sensor
{
public:
    virtual double read() const = 0;

    virtual ~Sensor()
    {
        std::cout << "Sensor 소멸\n";
    }
};

class Lidar : public Sensor
{
public:
    double read() const override
    {
        return 0.3;
    }

    ~Lidar() override
    {
        std::cout << "Lidar 소멸\n";
    }
};

class Imu : public Sensor
{
public:
    double read() const override
    {
        return 0.1;
    }

    ~Imu() override
    {
        std::cout << "Imu 소멸\n";
    }
};
```

여기서 `0.3`, `0.1`은 실제 센서에서 읽은 값이 아니라 **연습용 가상 측정값**입니다.

**① 공통 설계도: `Sensor`**

```cpp
virtual double read() const = 0;
```

앞서 만든 함수 선언에 새로운 표현 두 개가 붙었어요.

- `virtual`: 실제 객체 종류에 맞는 함수를 호출할 수 있도록 합니다.
- `= 0`: 부모에서는 구현하지 않고, 자식 클래스가 구현하도록 하는 **순수 가상 함수**입니다.

뜻은 **“모든 센서는 값을 읽는 `read()` 기능을 제공해야 한다”**예요.

이런 순수 가상 함수를 가진 클래스를 **추상 클래스**라고 합니다. 따라서 다음처럼 `Sensor` 자체의 객체를 만들 수는 없어요.

```cpp
Sensor sensor;  // 컴파일 오류
```

**② 상속: `Lidar`, `Imu`**

```cpp
class Lidar : public Sensor
```

`Lidar`가 `Sensor`를 **상속**한다는 뜻입니다. `Lidar`를 일종의 `Sensor`로 다룰 수 있게 됩니다.

```cpp
double read() const override
{
    return 0.3;
}
```

부모가 요구한 `read()`의 실제 동작을 작성합니다.

`override`는 **“부모의 가상 함수를 재정의하는 것이 맞는지 컴파일러가 확인해 달라”**는 표시예요. 이름이나 매개변수를 잘못 쓰면 오류로 알려줍니다.

사용하면:

```cpp
Lidar lidar;
Imu imu;

std::cout << lidar.read();  // 0.3
std::cout << imu.read();    // 0.1
```

같은 이름의 `read()`지만 객체 종류에 따라 결과가 다릅니다.

**③ 소멸자: `~Sensor()`**

```cpp
virtual ~Sensor()
{
    std::cout << "Sensor 소멸\n";
}
```

클래스 이름 앞에 `~`가 붙은 함수는 **소멸자**입니다. 객체가 소멸할 때 실행되며, 보유한 자원을 정리하는 데 사용합니다. 지금은 실행 시점을 관찰하려고 출력만 넣었습니다.

예를 들어:

```cpp
{
    Lidar lidar;
}  // 여기서 lidar 소멸
```

예상 출력은:

```text
Lidar 소멸
Sensor 소멸
```

**자식 부분이 먼저, 부모 부분이 나중에 소멸**합니다.

부모 소멸자에 `virtual`을 붙이는 이유는 이후 `Sensor` 포인터로 자식 객체를 관리할 때도 **자식 소멸자부터 올바르게 실행되도록 하기 위해서**예요.

우선 여기까지 저장하세요. 다음 단계에서는 `main.cpp`에서 **부모 참조로 서로 다른 센서의 `read()`를 호출하는 다형성**을 직접 확인하겠습니다.

이제 **다형성**을 실행으로 확인해 볼게요. 다형성은 **같은 호출 코드가 실제 객체 종류에 따라 다른 동작을 하는 것**입니다.

`sensors` 폴더에 `main.cpp`를 만드세요. 이전 모터 실습의 `cpp_basics/main.cpp`와는 다른 파일입니다.

```cpp
#include <iostream>
#include "sensor.hpp"

void printReading(const Sensor& sensor)
{
    std::cout << "측정값: " << sensor.read() << '\n';
}

int main()
{
    Lidar lidar;
    Imu imu;

    printReading(lidar);
    printReading(imu);

    return 0;
}
```

**① 센서를 받아 출력하는 함수**

```cpp
void printReading(const Sensor& sensor)
```

- `void`: 반환값이 없습니다.
- `Sensor&`: 센서 객체를 복사하지 않고 **참조해서 사용**합니다.
- `const`: 이 참조를 통해 객체를 변경하지 않겠다는 뜻입니다.

`Lidar`와 `Imu`는 모두 `Sensor`를 상속했으므로 이 함수에 전달할 수 있어요.

추상 클래스는 직접 객체를 만들 수 없지만, 이렇게 **자식 객체를 가리키는 참조나 포인터의 타입**으로는 사용할 수 있습니다.

**② 같은 코드로 다른 함수 호출**

```cpp
sensor.read()
```

`read()`가 `virtual`이므로 실제 전달된 객체에 따라 호출할 함수가 결정됩니다.

```cpp
printReading(lidar);  // Lidar::read() → 0.3
printReading(imu);    // Imu::read()   → 0.1
```

`printReading` 안에서 센서 종류를 구분하는 `if`문을 쓰지 않아도 됩니다. 이것이 다형성이에요.

**③ 컴파일하고 실행**

터미널을 `cpp_basics/sensors`로 이동한 뒤 실행하세요.

```bash
g++ -Wall -std=c++17 main.cpp -o sensor_demo
./sensor_demo
```

예상 출력:

```text
측정값: 0.3
측정값: 0.1
Imu 소멸
Sensor 소멸
Lidar 소멸
Sensor 소멸
```

지역 객체는 **생성 순서의 역순**으로 소멸합니다. `lidar` 다음에 `imu`를 만들었으므로 `imu`가 먼저 소멸하고, 각각 자식 → 부모 순서로 소멸자가 실행돼요.

이 결과를 확인한 다음, 과제에서 요구하는 **`vector`와 `unique_ptr`에 센서들을 담아 반복문으로 읽기**로 넘어가겠습니다.

맞아요. **지금 스크린샷의 코드는 올바릅니다.** 제가 같은 수정만 반복해서 안내했네요.

이전 오류에 나온 코드와 지금 편집기 내용이 다르니, **저장된 파일과 컴파일하는 파일이 같은지** 확인해야 해요.

먼저 **Ctrl+S**를 누르고, 컴파일했던 터미널에서 다음을 실행해 주세요.

```bash
pwd
cat -n sensor.hpp
g++ -Wall -std=c++17 main.cpp -o sensor_demo && ./sensor_demo
```

- `pwd`: 컴파일하는 폴더 확인
- `cat -n sensor.hpp`: 컴파일러가 실제로 읽을 파일 내용 확인
- 마지막 명령: 새로 컴파일하고 성공하면 실행

**이 명령의 새 출력**을 보내주세요. 편집기 코드는 더 고치지 않아도 됩니다.

---

지금 코드가 잘못돼서 바꾸는 건 아니에요. **현재 코드는 포인터 배열로 다형성을 확인하는 올바른 코드**예요.

기록에 다음 단계가 `vector`와 `unique_ptr`라고 적혀 있어서 제가 먼저 넘어갔어요. 지금 코드를 충분히 이해했는지 확인하지 않고 교체부터 안내했네요.

그대로 두고 이어가요. 지금 코드의 핵심은 이 부분이에요.

```cpp
Sensor* sensors[] = {&lidar, &imu};
```

`lidar`와 `imu`의 **주소를 부모 타입인 `Sensor*` 배열에 담는 것**이에요. 이후 `sensor->read()`를 호출하면 실제 객체에 따라 `Lidar::read()` 또는 `Imu::read()`가 실행돼요.

마지막에 이 코드 실행까지 성공했었나요, 아니면 오류를 해결하던 중이었나요?

---

좋아, 작업 파일 찾았어요. 지금은 **`Sensor*` 배열에 `Lidar`, `Imu`를 넣고 반복문으로 읽는 단계**까지 작성돼 있어요. 다음은 **`vector`와 `unique_ptr`로 센서를 관리하기**예요.

[main.cpp](/C:/Users/haemi/git/classwork/physicalai-lv1-HaeminKim/lv1_module2_student/cpp_basics/sensors/main.cpp)를 다음처럼 바꿔볼게요. `sensor.hpp`는 그대로 사용해요.

```cpp
#include <iostream>
#include <memory>
#include <vector>
#include "sensor.hpp"

int main()
{
    std::vector<std::unique_ptr<Sensor>> sensors;

    sensors.push_back(std::make_unique<Lidar>());
    sensors.push_back(std::make_unique<Imu>());

    for (const auto& sensor : sensors)
    {
        std::cout << "측정값: " << sensor->read() << '\n';
    }

    return 0;
}
```

각 부분을 풀어보면:

- **`vector`**: 센서를 여러 개 담는, 크기를 늘릴 수 있는 컨테이너예요.
- **`unique_ptr<Sensor>`**: 센서 객체를 소유하고, 수명이 끝나면 자동으로 삭제하는 스마트 포인터예요.
- **`make_unique<Lidar>()`**: `Lidar` 객체를 만들고 이를 소유하는 스마트 포인터를 반환해요.
- **`const auto&`**: 스마트 포인터를 복사하지 않고 참조해서 읽어요. `unique_ptr`는 소유권이 하나라 복사가 금지돼 있어요.

기존의 `&lidar`는 별도로 만든 객체의 주소만 담았어요. 이번에는 **컨테이너 안의 스마트 포인터가 객체의 수명까지 관리**해요. `main()`이 끝나면 센서도 자동으로 정리됩니다.

`sensors` 폴더의 터미널에서 저장 후 실행해 주세요.

```bash
g++ -Wall -std=c++17 main.cpp -o sensor_demo
./sensor_demo
```

측정값 `0.3`, `0.1`과 소멸 메시지가 나오면 됩니다. 현재 제가 사용하는 PowerShell에서는 `g++`가 잡히지 않아 실행 검증은 아직 못 했어요.

모듈 2-2 센서 과제로 돌아가요. 마지막에는 `vector`와 `unique_ptr`를 사용한 코드가 실행돼서 **측정값 `0.3`, `0.1`과 소멸 메시지**까지 나왔어요.

이번 코드에서 확인할 핵심은 이거예요.

```cpp
sensors.push_back(std::make_unique<Lidar>());
```

1. `make_unique<Lidar>()`가 `Lidar` 객체를 만들어요.
2. 만들어진 객체를 소유하는 `unique_ptr`를 `sensors`에 넣어요.
3. `main()`이 끝나면 `sensors`가 소멸하면서 각 `unique_ptr`가 센서 객체를 자동으로 삭제해요.

그래서 우리가 **`delete`를 직접 쓰지 않았는데도 소멸 메시지가 나온 것**이에요. `Sensor`의 소멸자가 `virtual`이라서 `Lidar 소멸` → `Sensor 소멸`처럼 자식과 부모의 소멸자가 모두 실행됩니다.

이제 반복문을 살펴볼게요.

```cpp
for (const auto& sensor : sensors)
{
    std::cout << "측정값: " << sensor->read() << '\n';
}
```

**`sensors`에 담긴 스마트 포인터를 하나씩 참조해서 센서 값을 읽는 코드**예요.

- `auto`: 원소의 타입인 `std::unique_ptr<Sensor>`를 컴파일러가 추론해요.
- `&`: 원소를 복사하지 않고 참조해요. `unique_ptr`는 복사할 수 없어서 중요해요.
- `const`: 이 참조로 스마트 포인터를 변경하지 않아요.
- `->read()`: 포인터가 가리키는 센서의 `read()`를 호출해요.

이때 **`Sensor` 포인터로 호출해도 실제 객체에 맞는 함수가 실행**돼요.

```text
Lidar 객체 → Lidar::read() → 0.3
Imu 객체   → Imu::read()   → 0.1
```

이것이 앞에서 배운 **다형성**이에요. 센서를 담는 방식은 바뀌었지만, 실제 센서 종류에 따라 `read()`가 실행되는 원리는 같아요.

여기서 `const`를 하나만 더 짚고 갈게요.

```cpp
for (const auto& sensor : sensors)
```

이 `const`는 **스마트 포인터 자체를 변경하지 못하게 하는 것**이에요. 가리키는 센서까지 무조건 변경 불가능하게 만드는 건 아니에요.

반면 `sensor.hpp`의:

```cpp
virtual double read() const = 0;
```

여기서 함수 뒤의 `const`는 **`read()`가 센서의 일반 멤버 변수를 변경하지 않겠다는 뜻**이에요. `const`가 붙는 위치에 따라 대상이 달라져요.

지금 코드에서는 세 가지가 함께 작동하고 있어요.

| 기능 | 담당 |
|---|---|
| 센서 여러 개를 담기 | `vector` |
| 센서 객체를 자동으로 삭제하기 | `unique_ptr` |
| 실제 센서 종류에 맞는 `read()` 호출하기 | `virtual`을 통한 다형성 |

직접 확인해 보려면 `Imu`를 추가한 줄 아래에 다음 한 줄을 더 넣어보세요.

```cpp
sensors.push_back(std::make_unique<Lidar>());
```

반복문을 수정하지 않아도 측정값이 **`0.3` → `0.1` → `0.3`**으로 세 번 나와요. 센서가 늘어나도 같은 반복문으로 처리할 수 있는 거예요.

맞아요. **1번·2번은 해 둔 거고, 다음은 3번 ‘가상 소멸자를 뺐을 때의 차이’**예요. 제가 자꾸 앞 단계로 돌아갔네요.

먼저 현재 `sensors` 폴더 터미널에서 실험용 파일을 복사해요.

```bash
mkdir -p no_virtual
cp sensor.hpp main.cpp no_virtual/
```

그다음 **`no_virtual/sensor.hpp`에서 소멸자 선언 세 줄만** 바꾸세요.

```cpp
virtual ~Sensor()   →   ~Sensor()
~Lidar() override   →   ~Lidar()
~Imu() override     →   ~Imu()
```

`read()`는 그대로 두고 저장한 다음 실행해요.

```bash
g++ -Wall -Wextra -std=c++17 no_virtual/main.cpp -o no_virtual/sensor_demo.exe && ./no_virtual/sensor_demo.exe
```

**이번에는 어떤 소멸 메시지가 나오는지** 확인해서 정상 버전과 비교할 거예요. 가상 소멸자 없이 부모 포인터로 자식 객체를 삭제하면 *정의되지 않은 동작*이므로, 출력 결과가 항상 같다고 보장되지는 않아요.

---

그럼 다음은 **4번: 센서별 최근 값 저장 + 측정 로그에서 `0.35` 이내인 기록 세기**예요.

원본 **`sensors/main.cpp`**에서 진행해요.

① 위쪽에 헤더 두 개를 추가하세요.

```cpp
#include <string>
#include <unordered_map>
#include <algorithm>
```

② 센서 두 개를 `push_back`한 다음, 기존 반복문을 아래 코드로 바꾸세요.

```cpp
std::vector<std::string> names = {"Lidar", "Imu"};
std::unordered_map<std::string, double> latest;
std::vector<double> logs;

for (std::size_t i = 0; i < sensors.size(); ++i)
{
    double value = sensors[i]->read();

    latest[names[i]] = value;
    logs.push_back(value);

    std::cout << names[i] << " 측정값: " << value << '\n';
}

auto count = std::count_if(
    logs.begin(),
    logs.end(),
    [](double distance)
    {
        return distance <= 0.35;
    }
);

std::cout << "Lidar 최근 값: " << latest.at("Lidar") << '\n';
std::cout << "Imu 최근 값: " << latest.at("Imu") << '\n';
std::cout << "0.35 이내 기록: " << count << "개\n";
```

- `latest`: 센서 **이름으로 최근 측정값을 조회**해요.
- `logs`: 읽은 측정값을 순서대로 쌓아요.
- `count_if`: 조건을 만족하는 기록의 개수를 세요. 여기서는 과제의 가상 측정값을 거리로 취급해요.

③ 저장하고 원본 폴더에서 실행하세요.

```bash
g++ -Wall -std=c++17 main.cpp -o sensor_demo.exe && ./sensor_demo.exe
```

현재 값은 `0.3`, `0.1`이므로 **`0.35 이내 기록: 2개`**가 나와야 해요.그럼 다음은 **4번: 센서별 최근 값 저장 + 측정 로그에서 `0.35` 이내인 기록 세기**예요.

원본 **`sensors/main.cpp`**에서 진행해요.

① 위쪽에 헤더 두 개를 추가하세요.

```cpp
#include <string>
#include <unordered_map>
#include <algorithm>
```

② 센서 두 개를 `push_back`한 다음, 기존 반복문을 아래 코드로 바꾸세요.

```cpp
std::vector<std::string> names = {"Lidar", "Imu"};
std::unordered_map<std::string, double> latest;
std::vector<double> logs;

for (std::size_t i = 0; i < sensors.size(); ++i)
{
    double value = sensors[i]->read();

    latest[names[i]] = value;
    logs.push_back(value);

    std::cout << names[i] << " 측정값: " << value << '\n';
}

auto count = std::count_if(
    logs.begin(),
    logs.end(),
    [](double distance)
    {
        return distance <= 0.35;
    }
);

std::cout << "Lidar 최근 값: " << latest.at("Lidar") << '\n';
std::cout << "Imu 최근 값: " << latest.at("Imu") << '\n';
std::cout << "0.35 이내 기록: " << count << "개\n";
```

- `latest`: 센서 **이름으로 최근 측정값을 조회**해요.
- `logs`: 읽은 측정값을 순서대로 쌓아요.
- `count_if`: 조건을 만족하는 기록의 개수를 세요. 여기서는 과제의 가상 측정값을 거리로 취급해요.

③ 저장하고 원본 폴더에서 실행하세요.

```bash
g++ -Wall -std=c++17 main.cpp -o sensor_demo.exe && ./sensor_demo.exe
```

현재 값은 `0.3`, `0.1`이므로 **`0.35 이내 기록: 2개`**가 나와야 해요.