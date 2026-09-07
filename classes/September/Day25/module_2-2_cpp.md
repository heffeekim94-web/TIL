module 2-2

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

