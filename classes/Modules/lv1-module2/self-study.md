## 문제 2

과제 웹사이트:

https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C2_turtlesim_ROS2%ED%8C%A8%ED%82%A4%EC%A7%80.md


### VOCAB

#### 스택

**스택(stack)은 함수 안의 지역 변수 등이 저장되는 메모리 영역**이야.

네 코드로 보면:

```cpp
{
    Lidar stack_sensor;
}
```

`stack_sensor`는 이 블록 안에서 만들어지는 지역 객체야. **닫는 중괄호 `}`에 도달하면 자동으로 소멸해.** 직접 `delete`할 필요가 없어.

반면에:

```cpp
{
    auto heap_sensor = std::make_unique<Imu>();
}
```

여기서는 **`Imu` 객체는 힙에**, 그것을 관리하는 **`heap_sensor`라는 `unique_ptr`은 스택에** 있어. 블록이 끝나면 `unique_ptr`이 소멸하면서 힙의 `Imu`도 삭제해 줘.

즉, 지금 실험에서는 둘 다 블록 끝에서 정리되지만, **객체가 저장된 위치와 정리하는 방식이 다른 거야.**

---

여기서 `unique`는 **“하나의 포인터만 그 객체를 소유한다”**는 뜻이야. `_unique`가 별도 문법인 건 아니고, 이름의 일부야.

```cpp
auto heap_sensor = std::make_unique<Imu>();
```

이 코드는:

1. 힙에 `Imu` 객체를 만들고,
2. 그 객체를 관리하는 `std::unique_ptr<Imu>`를 반환해서,
3. `heap_sensor`에 담아.

**소유한다는 건 객체를 삭제할 책임을 갖는다는 뜻**이야. `heap_sensor`가 소멸하면 관리하던 `Imu`도 자동으로 삭제돼.

`unique_ptr`은 소유권이 중복되지 않도록 **복사는 금지하고, 소유권을 옮기는 것은 허용**해.

---

응, 맞아. **`unique_ptr`은 자신이 관리하는 객체를 자동으로 삭제하는 기능이 구현된 C++ 클래스**야. 단순한 이름이나 예약어가 아니라, 내부에 그 기능이 들어 있어.

```cpp
{
    std::unique_ptr<Imu> sensor = std::make_unique<Imu>();
} // sensor가 소멸하면서, 관리하던 Imu를 삭제
```

즉, **`make_unique`는 객체를 만들고, `unique_ptr`은 그 객체를 관리하다가 자신의 수명이 끝날 때 삭제해 줘.**

--- 

이 줄은 **“`Sensor` 객체를 관리하는 `unique_ptr`들을 담을 벡터 `sensors`를 만든다”**는 뜻이야.

```cpp
std::vector<std::unique_ptr<Sensor>> sensors;
```

안쪽부터 읽으면:

- `std::unique_ptr<Sensor>`: 센서 객체를 관리하고 자동 삭제하는 포인터
- `std::vector<...>`: 그 포인터들을 여러 개 담는 컨테이너
- `sensors`: 변수 이름

**이 줄만으로 센서 객체가 만들어지지는 않아.** 처음에는 빈 벡터야. 여기에 이렇게 추가하지:

```cpp
sensors.push_back(std::make_unique<Lidar>());
```

나중에 `sensors`가 소멸하면 → 안의 `unique_ptr`들이 소멸하고 → 각각 관리하던 센서 객체를 삭제해.

---

응, **`push_back`(푸시 백)**이라고 읽어. 벡터의 **맨 뒤에 원소를 추가하는 함수**야.

```cpp
sensors.push_back(std::make_unique<Lidar>());
```

이 줄은 **`Lidar`를 만들고, 그 객체를 관리하는 `unique_ptr`을 `sensors` 맨 뒤에 넣는다**는 뜻이야.

---

위에서부터 하나씩 볼게.

### 1. 필요한 기능 가져오기

```cpp
#include <algorithm>
```

`std::count_if` 같은 **데이터를 검색하거나 세는 함수**를 사용하기 위해 넣어.

```cpp
#include <string>
```

`std::string`, 즉 **문자열 타입**을 사용하기 위해 넣어.

```cpp
#include <unordered_map>
```

**이름과 값을 짝지어 저장하는 컨테이너**인 `std::unordered_map`을 사용하기 위해 넣어.

### 2. 센서 이름별 최근 측정값 저장

```cpp
std::unordered_map<std::string, double> latest;
```

`latest`라는 빈 저장소를 만드는 코드야.

- `std::string`: 데이터를 찾을 때 사용하는 **키**의 타입. 여기서는 센서 이름.
- `double`: 키에 연결해서 저장하는 **값**의 타입. 여기서는 측정값.
- `latest`: 변수 이름.

Python의 딕셔너리와 비슷해.

```cpp
latest["Lidar"] = 0.30;
latest["Imu"] = 0.10;
```

각 이름에 값을 저장해:

| 키 | 값 |
|---|---:|
| `"Lidar"` | 0.30 |
| `"Imu"` | 0.10 |

나중에 이렇게 쓰면:

```cpp
latest["Lidar"] = 0.25;
```

기존 `0.30`이 `0.25`로 바뀌어. **최근 값을 자동으로 찾아주는 건 아니고, 새 측정값으로 덮어써서 관리하는 거야.**

### 3. 거리 기록 여러 개 저장

```cpp
std::vector<double> distance_log = {0.30, 0.50, 0.20, 0.35, 0.80};
```

`double` 값 여러 개를 담는 벡터 `distance_log`를 만들고, 다섯 개의 거리 기록을 넣어.

앞의 `latest`가 센서별 값 하나를 보관한다면, 여기서는 **여러 측정 기록을 순서대로 보관**해. 지금 숫자는 설명을 위한 예시 값이야.

### 4. 조건에 맞는 기록 세기

```cpp
auto count = std::count_if(
    distance_log.begin(),
    distance_log.end(),
    [](double distance) {
        return distance <= 0.35;
    }
);
```

전체 뜻은 **“거리 기록 중 0.35 이하인 값의 개수를 세어서 `count`에 저장한다”**야.

부분별로 나누면:

```cpp
auto count =
```

`count`라는 변수를 만들고 결과를 저장해. `auto`는 **오른쪽 결과를 보고 컴파일러가 변수 타입을 정하게 하는 키워드**야.

```cpp
std::count_if(
```

**조건이 참인 원소의 개수를 세는 함수**를 호출해.

```cpp
distance_log.begin(),
distance_log.end(),
```

검사할 범위를 지정해.

- `begin()`: 첫 번째 원소를 가리키는 위치
- `end()`: 마지막 원소의 **바로 다음 위치**

`count_if`는 첫 원소부터 `end()` 직전까지 검사해.

```cpp
[](double distance) {
    return distance <= 0.35;
}
```

이 부분은 **이름 없이 그 자리에서 만드는 함수**, 즉 *람다 함수*야.

- `[]`: 바깥의 지역 변수를 가져오지 않는다는 뜻
- `(double distance)`: 검사할 값 하나를 `distance`라는 이름으로 받음
- `return distance <= 0.35;`: 값이 0.35 이하이면 `true`, 아니면 `false`를 반환

`count_if`가 각 값을 이 함수에 넣어 봐:

| distance | 조건 결과 | 개수에 포함 |
|---:|---|---|
| 0.30 | `true` | O |
| 0.50 | `false` | X |
| 0.20 | `true` | O |
| 0.35 | `true` | O |
| 0.80 | `false` | X |

그래서 `count`에는 **3**이 저장돼.

### 5. 결과 출력

```cpp
std::cout << "Lidar 최근 측정값: " << latest.at("Lidar") << '\n';
```

`latest.at("Lidar")`는 `"Lidar"`라는 키에 저장된 값을 꺼내. 해당 키가 없으면 예외가 발생해.

`std::cout`과 `<<`로 문구와 값을 출력하고, `'\n'`으로 줄을 바꿔.

```cpp
std::cout << "0.35 이내 기록: " << count << "개\n";
```

계산한 개수를 출력해. 최종 출력은:

```text
Lidar 최근 측정값: 0.3
0.35 이내 기록: 3개
```

---

그럼 **아직 안 한 `clamp`부터 하고, 다음에 메모리 누수 실험**으로 가자.

`clamp`는 값을 정해진 범위 안으로 제한하는 함수야. 예를 들어 범위가 `0~10`이면:

- `-3` → `0`
- `7` → `7`
- `15` → `10`

`main.cpp`의 **`int main()` 위에** 작성해:

```cpp
template <typename T>
T clamp(T value, T min_value, T max_value)
{
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}
```

`T`는 **나중에 사용할 자료형 자리**야. 같은 함수로 `double`과 `int`를 모두 처리할 수 있어.

`main()` 안의 **`return 0;` 위에** 다음을 추가해:

```cpp
double speed = clamp(3.5, 0.0, 2.0);
int pixel = clamp(300, 0, 255);

std::cout << "제한된 속도: " << speed << '\n';
std::cout << "제한된 픽셀값: " << pixel << '\n';
```

예상 출력은:

```text
제한된 속도: 2
제한된 픽셀값: 255
```

먼저 **함수를 정의하는 부분**이야.

```cpp
template <typename T>
```

**여러 자료형에 사용할 수 있는 함수 템플릿을 만들겠다**는 뜻이야. `T`는 자료형을 대신하는 이름이야.

- `clamp(3.5, 0.0, 2.0)`처럼 호출하면 `T`는 `double`
- `clamp(300, 0, 255)`처럼 호출하면 `T`는 `int`

```cpp
T clamp(T value, T min_value, T max_value)
```

`clamp`라는 함수를 정의해.

- 맨 앞의 `T`: **반환하는 값의 자료형**
- `T value`: 범위를 제한할 값
- `T min_value`: 허용할 최솟값
- `T max_value`: 허용할 최댓값

즉, 세 값을 같은 자료형으로 받고, 결과도 그 자료형으로 반환해.

```cpp
if (value < min_value) {
    return min_value;
}
```

입력값이 최솟값보다 작으면 **최솟값을 반환하고 함수를 끝내.**

예를 들어 `value = -3`, `min_value = 0`이면 `0`을 반환해.

```cpp
if (value > max_value) {
    return max_value;
}
```

입력값이 최댓값보다 크면 **최댓값을 반환하고 함수를 끝내.**

예를 들어 `value = 300`, `max_value = 255`이면 `255`를 반환해.

```cpp
return value;
```

앞의 두 조건에 걸리지 않았다면 이미 범위 안에 있으니까 **원래 값을 그대로 반환**해. 경곗값과 같을 때도 여기에 해당해.

이제 **함수를 사용하는 부분**을 보자.

```cpp
double speed = clamp(3.5, 0.0, 2.0);
```

속도 `3.5`를 `0.0~2.0` 범위로 제한해. 최댓값을 넘었으므로 `2.0`을 반환하고, 그 값을 `double` 변수 `speed`에 저장해.

```cpp
int pixel = clamp(300, 0, 255);
```

픽셀값 `300`을 `0~255` 범위로 제한해. 결과인 `255`를 `int` 변수 `pixel`에 저장해.

**함수 코드는 하나지만, 호출할 때 넣은 값의 자료형에 맞춰 사용할 수 있는 것이 템플릿의 역할**이야.

```cpp
std::cout << "제한된 속도: " << speed << '\n';
std::cout << "제한된 픽셀값: " << pixel << '\n';
```

계산 결과를 화면에 출력해.

- `std::cout`: 화면 출력
- `<<`: 뒤의 내용을 출력 스트림에 전달
- `'\n'`: 줄바꿈

결과는 다음과 같아:

```text
제한된 속도: 2
제한된 픽셀값: 255
```

---

좋아. 먼저 **일부러 메모리 누수를 만드는 코드**부터 실행하자.

기존 `main.cpp`와 같은 `sensors` 폴더에 **`leak_demo.cpp`**를 만들고 작성해:

```cpp
int main()
{
    for (int i = 0; i < 100; ++i) {
        int* data = new int[1000];
        data[0] = i;
        // delete[] data;를 생략해서 누수 발생
    }

    return 0;
}
```

`new int[1000]`은 힙에 정수 1,000개 공간을 할당해. 반복문이 끝날 때 포인터 변수 `data`는 사라지지만, **할당한 메모리는 자동으로 해제되지 않아.**

`sensors` 폴더의 터미널에서 다음을 실행해:

```bash
g++ -Wall -std=c++17 -g -O0 -fsanitize=address leak_demo.cpp -o leak_demo
ASAN_OPTIONS=detect_leaks=1 ./leak_demo
```

`-fsanitize=address`는 메모리 오류 검출 기능을 넣는 옵션이야. 실행 결과에서 다음과 같은 문구를 찾아봐:

```text
ERROR: LeakSanitizer: detected memory leaks
```

**이 출력이 보고서 5번의 ‘수정 전 누수 검출 결과’**야. 출력 내용을 보관한 다음 `make_unique`로 수정해서 비교하자.

---

이 줄은 **“힙에 정수 1,000개짜리 배열을 만들고, 자동으로 삭제해 줄 `unique_ptr`을 `data`에 담는다”**는 뜻이야.

```cpp
auto data = std::make_unique<int[]>(1000);
```

각 부분을 보면:

- **`int[]`**: 만들 객체가 정수 배열이라는 뜻
- **`(1000)`**: 배열에 정수 1,000개를 담을 공간을 만든다는 뜻
- **`std::make_unique`**: 배열을 만들고, 이를 소유하는 `unique_ptr`을 반환
- **`auto data`**: 반환된 타입인 `std::unique_ptr<int[]>`로 변수 `data`를 선언

그래서 다음처럼 배열 원소에 접근할 수 있어:

```cpp
data[0] = i;  // 첫 번째 원소에 i 저장
```

**반복문 한 번이 끝나면 `data`가 소멸하면서 배열 전체를 자동으로 해제해.** 직접 `delete[]`를 쓰지 않아도 되는 이유야.

---

## 문제 3

### 1. `/turtle1/pose` 필드 구성:

좋아. **문제 3은 ROS 2에서 거북이의 위치를 받아 거리를 발행하고 구독하는 노드 만들기**야. 먼저 거북이 위치 메시지부터 확인하자.

첫 번째 터미널에서:

```bash
ros2 run turtlesim turtlesim_node
```

거북이 창이 뜨면, 두 번째 터미널에서:

```bash
ros2 topic echo /turtle1/pose
```

이 명령은 `/turtle1/pose` 토픽으로 들어오는 메시지를 계속 보여줘. 출력에서 **어떤 필드가 있는지** 확인하는 게 답안 템플릿 1번이야.

출력을 보내주면 각 값의 의미부터 같이 확인하자.

찾았어. `pts/4` 터미널에서 `ros2 topic echo /turtle1/pose`가 실행 중이야. **계속 출력되는 게 정상이니, 그 터미널에서 Ctrl+C로 출력을 멈추면 돼.**

내가 같은 토픽에서 메시지 하나를 받아 확인한 값은:

```yaml
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
```

보고서 1번에는 이렇게 적으면 돼:

> `/turtle1/pose`의 필드는 `x`, `y`(위치), `theta`(방향각), `linear_velocity`(선속도), `angular_velocity`(각속도)로 구성된다.

다음부터 **한 번만 출력**하려면:

```bash
ros2 topic echo /turtle1/pose --once
```
---

### 2. `ros2 topic hz /turtle_distance 출력:

다음은 **`turtle_py` 패키지 만들기**야. 과제 폴더 안의 ROS 2 워크스페이스에서 진행하자.

터미널에서:

```bash
cd /home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws/src
```

그다음 패키지를 생성해:

```bash
ros2 pkg create turtle_py --build-type ament_python --dependencies rclpy turtlesim std_msgs geometry_msgs
```

각 옵션의 뜻은:

- `turtle_py`: 만들 패키지 이름
- `--build-type ament_python`: Python 기반 ROS 2 패키지로 생성
- `--dependencies ...`: 사용할 ROS 2 패키지들을 의존성으로 등록

생성되면 **`turtle_py/turtle_py/` 안에 노드 코드를 작성**하게 돼. 명령 실행 중 `already exists`가 나오면 기존 폴더를 지우지 말고 알려줘.


**에러가 아니라 라이선스를 지정하지 않았다는 경고야. 패키지는 정상 생성됐어.**

```text
[WARNING]: Unknown license 'TODO: License declaration'
```

라이선스가 기본 placeholder로 남아 있어서 `LICENSE` 파일을 만들지 않았다는 뜻이야. 지금 노드 작성은 진행할 수 있어.

그리고 화면의 `destination directory`는 다음으로 나와:

```text
/home/haeminkim/Desktop/haeminkim_backup/ros2_ws/src
```

**이 실행에서 생성된 위치는 제출 저장소 밖이 맞아.** VS Code에서 열어 둔 저장소와 터미널의 현재 폴더는 서로 다를 수 있어. 제출에 포함하려면 생성된 `turtle_py`를 과제 저장소 안으로 옮겨야 해.

좋아. 이제 **거북이 위치를 받아 원점까지의 거리를 발행하는 노드**를 만들자.

[turtle_py 코드 폴더](/home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws/src/turtle_py/turtle_py)에 **`distance_publisher.py`** 파일을 만들어.

먼저 필요한 모듈부터 작성해:

```python
import math

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from std_msgs.msg import Float32
```

- `math`: 원점까지 거리 `√(x² + y²)` 계산
- `rclpy`: Python에서 ROS 2 사용
- `Node`: 우리가 만들 노드의 부모 클래스
- `Pose`: `/turtle1/pose`로 받을 메시지 타입
- `Float32`: `/turtle_distance`로 보낼 거리 메시지 타입

이 노드는 **구독 콜백에서 최신 위치를 저장하고, 타이머 콜백에서 0.1초마다 거리를 발행**하도록 만들 거야.

이제 import 아래에 **노드 클래스와 초기화 코드**를 추가해:

```python
class DistancePublisher(Node):
    def __init__(self):
        super().__init__('distance_publisher')

        self.declare_parameter('publish_rate', 10.0)
        publish_rate = self.get_parameter('publish_rate').value

        self.latest_pose = None

        self.pose_subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.distance_publisher = self.create_publisher(
            Float32,
            '/turtle_distance',
            10
        )

        self.timer = self.create_timer(
            1.0 / publish_rate,
            self.timer_callback
        )
```

각 부분은 이런 역할이야:

- `super().__init__(...)`: 부모 `Node`를 초기화하고 노드 이름을 지정해.
- `declare_parameter(...)`: 발행 주기 설정값 `publish_rate`를 기본 **10Hz**로 선언해.
- `latest_pose = None`: 아직 위치 메시지를 받지 않았다는 뜻이야.
- `create_subscription(...)`: 위치 메시지가 오면 `pose_callback`을 호출하도록 연결해.
- `create_publisher(...)`: 거리를 발행할 통로를 만들어.
- `create_timer(...)`: **1 ÷ 10 = 0.1초마다** `timer_callback`을 호출해.

구독·발행 설정의 마지막 `10`은 **Hz가 아니라 메시지 큐 깊이**야.

아직 두 콜백을 작성하지 않았으니 실행은 다음 단계까지 작성한 뒤 하자. 실행 중 `publish_rate` 변경을 타이머에 반영하는 처리도 이후에 추가할 거야.

이제 **같은 클래스 안에**, `__init__`과 같은 들여쓰기 수준으로 두 콜백을 추가해:

```python
    def pose_callback(self, msg):
        self.latest_pose = msg

    def timer_callback(self):
        if self.latest_pose is None:
            return

        distance = math.hypot(
            self.latest_pose.x,
            self.latest_pose.y
        )

        msg = Float32()
        msg.data = distance
        self.distance_publisher.publish(msg)
```

**`pose_callback`**은 위치 메시지를 받을 때마다 `latest_pose`를 최신 값으로 바꿔.

**`timer_callback`**은 타이머가 호출할 때 다음을 수행해:

- 아직 위치를 받지 않았다면 `return`으로 끝내.
- `math.hypot(x, y)`로 원점까지 거리 **√(x² + y²)**를 계산해.
- `Float32` 메시지를 만들고, `data` 필드에 거리를 넣어.
- `publish(msg)`로 `/turtle_distance`에 발행해.

이렇게 하면 **위치를 받는 작업과 주기적으로 거리를 발행하는 작업이 분리**돼.

이제 **노드를 실행하고 종료하는 코드**를 파일 맨 아래에 추가해. 이번에는 **클래스 바깥이므로 `def main` 앞에 들여쓰기가 없어야 해.**

```python
def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = DistancePublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

- `rclpy.init()`: ROS 2 통신을 초기화해.
- `DistancePublisher()`: 작성한 노드 객체를 만들어.
- `rclpy.spin(node)`: 위치 메시지와 타이머 이벤트를 처리하며 기다려.
- `except KeyboardInterrupt`: Ctrl+C로 중단했을 때 오류 traceback이 나오지 않도록 처리해.
- `finally`: 종료할 때 노드를 정리하고 ROS 2 통신을 종료해.
- 마지막 두 줄: 이 파일을 직접 실행하면 `main()`을 호출해.

다음에는 `setup.py`에 실행 명령을 등록할 거야.

이제 [setup.py](/home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws/src/turtle_py/setup.py)를 열고, 아래쪽의 `console_scripts` 목록에 한 줄을 추가해:

```python
entry_points={
    'console_scripts': [
        'distance_publisher = turtle_py.distance_publisher:main',
    ],
},
```

이 한 줄은 **`distance_publisher`라는 실행 명령을 Python 파일의 `main()` 함수와 연결**해.

저장한 뒤, 지금 있는 `ros2_ws` 터미널에서 빌드해:

```bash
colcon build --packages-select turtle_py --symlink-install
```

빌드가 성공하면 순서대로 실행해:

```bash
source install/setup.bash
ros2 run turtle_py distance_publisher
```

노드 자체에는 출력문이 없어서 **터미널에 아무것도 나오지 않고 기다리는 게 정상**이야. 거북이 창은 켜 둬. 다음에 다른 터미널에서 거리 메시지가 나오는지 확인하자.

이 목록에는 **`turtle_py`가 없어.** 지금은 패키지를 옮기기 전의 외부 워크스페이스에서 실행한 결과야.

폴더 혼동을 피하도록, 이번에는 **패키지 위치를 직접 지정해서 빌드**하자. 아래 전체를 한 번에 복사해 실행해 줘:

```bash
cd /home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws && colcon build --base-paths src/turtle_py --packages-select turtle_py --symlink-install
```

`&&`는 **폴더 이동에 성공했을 때만 빌드하라**는 뜻이야. 결과에 `Starting >>> turtle_py`가 나오는지 확인해 줘.

---

### 3. 구독잦 경고 로그

다음은 **거리가 임계값을 넘으면 경고하는 구독자 노드**야. 기본 임계값은 `2.5`야.

`distance_publisher.py`와 같은 폴더에 **`distance_subscriber.py`**를 만들고 작성해:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class DistanceSubscriber(Node):
    def __init__(self):
        super().__init__('distance_subscriber')

        self.declare_parameter('warn_distance', 2.5)

        self.subscription = self.create_subscription(
            Float32,
            '/turtle_distance',
            self.distance_callback,
            10
        )

    def distance_callback(self, msg):
        threshold = self.get_parameter('warn_distance').value

        if msg.data > threshold:
            self.get_logger().warning(
                f'거리 {msg.data:.2f}가 임계값 {threshold:.2f}를 넘었습니다.'
            )
```

- `create_subscription`: `/turtle_distance`의 거리 메시지를 받아.
- `distance_callback`: 메시지를 받을 때 실행돼.
- `get_parameter`: 매번 현재 임계값을 읽어서, 실행 중 값을 바꿔도 반영돼.
- `get_logger().warning`: 거리가 임계값보다 크면 터미널에 경고를 출력해.

아직 실행용 `main()`은 없으니, 여기까지 작성하고 이어서 붙이자.

이제 파일 맨 아래에 **클래스 바깥으로** 실행 코드를 추가해:

```python
def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = DistanceSubscriber()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

그다음 `setup.py`의 `console_scripts`에 구독자도 등록해. 기존 발행자 줄은 유지해:

```python
'console_scripts': [
    'distance_publisher = turtle_py.distance_publisher:main',
    'distance_subscriber = turtle_py.distance_subscriber:main',
],
```

저장하고 **새 터미널**에서 빌드·실행해:

```bash
cd /home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws
colcon build --packages-select turtle_py --symlink-install
source install/setup.bash
ros2 run turtle_py distance_subscriber
```

거북이와 거리 발행자는 계속 실행해 둬. 거리가 앞서 측정한 `7.84` 정도라면 다음과 같은 경고가 반복해서 나올 거야:

```text
[WARN] ... 거리 7.84가 임계값 2.50를 넘었습니다.
```

이 출력을 보고서 **3번 ‘구독자 경고 로그’**에 기록하면 돼.

맞아. 방금 추가한 **실행·종료 코드부터** 설명할게.

```python
def main(args=None):
```

프로그램의 실행을 담당하는 `main` 함수를 정의해. `args`는 ROS 2에 전달할 명령행 인자를 받는 자리야.

```python
rclpy.init(args=args)
```

**ROS 2 통신을 사용할 준비**를 해. 노드를 만들기 전에 호출해야 해.

```python
node = None
```

아직 노드를 만들지 않았다는 표시야. 노드 생성 중 오류가 나더라도, 종료 코드에서 생성 여부를 확인할 수 있어.

```python
try:
    node = DistanceSubscriber()
    rclpy.spin(node)
```

- `DistanceSubscriber()`는 네가 만든 구독자 노드 객체를 생성해. 이때 `__init__()`이 실행돼.
- `rclpy.spin(node)`는 계속 기다리면서 **메시지가 오면 구독 콜백을 실행**해.

그래서 `spin()` 실행 중에는 다음 줄로 바로 넘어가지 않아.

```python
except KeyboardInterrupt:
    pass
```

Ctrl+C를 누르면 발생하는 `KeyboardInterrupt`를 받아. `pass`는 별도의 작업 없이 넘어간다는 뜻이야. 이후 `finally`에서 정리해.

```python
finally:
```

정상 종료든 오류든, **이 블록에 들어오면 마지막에 수행할 정리 작업**을 적는 곳이야.

```python
    if node is not None:
        node.destroy_node()
```

노드가 만들어졌다면 `destroy_node()`로 구독 등 노드의 자원을 정리해.

```python
    if rclpy.ok():
        rclpy.shutdown()
```

ROS 2 통신이 아직 활성 상태라면 종료해. 이미 종료됐다면 다시 호출하지 않아.

```python
if __name__ == '__main__':
    main()
```

**이 파일을 직접 실행했을 때 `main()`을 호출**하는 부분이야. 다른 파일에서 `import`할 때는 이 조건이 거짓이라 자동 실행되지 않아.

그리고 `setup.py`에 추가한 이 줄은:

```python
'distance_subscriber = turtle_py.distance_subscriber:main',
```

실행 명령과 함수를 연결해.

| 부분 | 의미 |
|---|---|
| 왼쪽 `distance_subscriber` | `ros2 run`에서 사용할 실행 이름 |
| `turtle_py.distance_subscriber` | `turtle_py` 패키지 안의 `distance_subscriber.py` |
| `:main` | 그 파일에서 호출할 함수 |

따라서 다음 명령은 등록된 **`main()`을 호출**해:

```bash
ros2 run turtle_py distance_subscriber
```

터미널 명령들도 보면:

```bash
colcon build --packages-select turtle_py --symlink-install
```

`turtle_py`만 빌드하고, 개발 중 소스 변경을 반영하기 쉽도록 심볼릭 링크 설치를 사용해. 이번에는 **실행 항목을 추가했으므로 다시 빌드**하는 거야.

```bash
source install/setup.bash
```

현재 터미널이 빌드한 패키지를 찾을 수 있도록 환경을 설정해.

```bash
ros2 run turtle_py distance_subscriber
```

`turtle_py` 패키지에 등록한 구독자를 실행해. 이후에는 `spin()`이 메시지를 기다리고, 수신할 때마다 `distance_callback()`이 거리를 검사하는 흐름이야.

이제 **`SquareDriver` 클래스 안에**, `__init__`과 같은 들여쓰기 수준으로 추가해:

```python
    def timer_callback(self):
        now = self.get_clock().now()
        elapsed = (now - self.phase_start).nanoseconds / 1e9

        msg = Twist()

        if self.phase == 'forward':
            duration = self.side_length / self.linear_speed

            if elapsed < duration:
                msg.linear.x = self.linear_speed
            else:
                self.phase = 'turn'
                self.phase_start = now

        elif self.phase == 'turn':
            duration = (math.pi / 2) / self.angular_speed

            if elapsed < duration:
                msg.angular.z = self.angular_speed
            else:
                self.completed_sides += 1

                if self.completed_sides == 4:
                    self.phase = 'done'
                    self.get_logger().info('정사각형 주행 완료')
                    self.timer.cancel()
                else:
                    self.phase = 'forward'

                self.phase_start = now

        self.publisher.publish(msg)
```

코드는 **경과 시간을 보고 전진과 회전을 번갈아 수행**해.

- `elapsed`: 현재 동작을 시작한 뒤 지난 시간을 초로 계산해. `1e9`는 나노초를 초로 바꾸는 값이야.
- `msg = Twist()`: 속도가 모두 `0`인 메시지를 만들어.
- `forward` 상태: `거리 ÷ 속도`만큼의 시간 동안 `linear.x`에 전진 속도를 넣어.
- `turn` 상태: `회전각 ÷ 각속도`만큼의 시간 동안 `angular.z`에 회전 속도를 넣어. `math.pi / 2`는 90도야.
- 회전이 끝나면 `completed_sides`를 하나 늘려. 네 번 완료하면 타이머를 중지해.
- 마지막 `publish(msg)`는 계산한 속도를 발행해. **동작 전환 시점과 최종 완료 시점에는 0인 속도를 보내 정지**시켜.

다음에는 **실행 코드와 Ctrl+C로 중단할 때 정지시키는 처리**를 추가할 거야.

이제 **Ctrl+C로 중단해도 거북이를 정지시키는 코드**를 추가하자.

먼저 `SquareDriver` 클래스 안에, `timer_callback`과 같은 들여쓰기 수준으로 추가해:

```python
    def stop(self):
        self.timer.cancel()
        self.publisher.publish(Twist())
```

`Twist()`는 모든 속도가 `0`인 메시지야. 타이머를 멈추고 정지 명령을 보내는 거야.

그다음 **클래스 바깥**, 파일 맨 아래에 작성해:

```python
def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = SquareDriver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            if rclpy.ok():
                node.stop()
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

종료 시 ROS 통신이 살아 있으면 `stop()`으로 정지 명령을 보내고 노드를 정리해. 다만 Ctrl+C로 ROS 통신이 먼저 종료된 경우에는 이 방식만으로 정지 명령 전달을 보장할 수 없어.

마지막으로 `setup.py`의 `console_scripts`에 기존 두 줄을 유지하면서 추가해:

```python
'square_driver = turtle_py.square_driver:main',
```

등록까지 끝나면 빌드하고 실행할 준비가 돼.

---

## 문제 4. rclcpp 노드 작성 - C++ 발행자와 구독자

### 1. `colcon build` 성공 출력

좋아. 앞서 안내한 `turtle_cpp` 패키지 생성까지 했다면, 이제 **C++ 거리 발행자**를 작성하자. 직접 작성할 수 있게 조금씩 설명할게.

`ros2_ws/src/turtle_cpp/src/` 안에 **`distance_publisher.cpp`**를 만들고, 먼저 다음을 작성해:

```cpp
#include <chrono>
#include <cmath>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "turtlesim/msg/pose.hpp"
#include "std_msgs/msg/float32.hpp"

using namespace std::chrono_literals;
```

각 줄의 역할은:

- `<chrono>`: 타이머에 사용할 시간 표현
- `<cmath>`: 원점까지 거리를 계산하는 `std::hypot`
- `<memory>`: `std::shared_ptr`, `std::make_shared` 같은 스마트 포인터
- `"rclcpp/rclcpp.hpp"`: C++에서 ROS 2 노드를 만드는 기능
- `"turtlesim/msg/pose.hpp"`: 거북이 위치·방향 메시지
- `"std_msgs/msg/float32.hpp"`: 거리 값을 발행할 메시지

```cpp
using namespace std::chrono_literals;
```

이 줄을 넣으면 **`100ms`처럼 시간을 표현**할 수 있어. 이후 타이머를 `100ms`, 즉 0.1초마다 실행해서 **10Hz**로 거리를 발행할 거야.

이제 아래에 **노드 클래스의 기본 구조**를 추가해:

```cpp
class DistancePublisher : public rclcpp::Node
{
public:
    DistancePublisher() : Node("distance_publisher_cpp")
    {
        publisher_ = this->create_publisher<std_msgs::msg::Float32>(
            "/turtle_distance", 10
        );

        subscription_ = this->create_subscription<turtlesim::msg::Pose>(
            "/turtle1/pose",
            10,
            [this](turtlesim::msg::Pose::SharedPtr msg) {
                latest_pose_ = *msg;
                has_pose_ = true;
            }
        );

        timer_ = this->create_wall_timer(
            100ms,
            [this]() {
                this->publish_distance();
            }
        );
    }

private:
    turtlesim::msg::Pose latest_pose_;
    bool has_pose_ = false;

    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr publisher_;
    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr subscription_;
    rclcpp::TimerBase::SharedPtr timer_;

    void publish_distance()
    {
        // 다음 단계에서 거리 계산과 발행 코드를 작성
    }
};
```

Python에서 작성했던 구조와 같아. 하나씩 보면:

```cpp
class DistancePublisher : public rclcpp::Node
```

`rclcpp::Node`를 **상속받는 클래스**를 만들어. Python의 `class DistancePublisher(Node):`에 해당해.

```cpp
DistancePublisher() : Node("distance_publisher_cpp")
```

생성자야. 부모 `Node`를 초기화하면서 ROS 노드 이름을 지정해.

```cpp
this->create_publisher<std_msgs::msg::Float32>(
    "/turtle_distance", 10
);
```

`Float32` 메시지를 발행할 통로를 만들어. `this->`는 현재 객체의 멤버에 접근하는 표현이고, `10`은 메시지 큐 깊이야.

구독 콜백은 다음 부분이야:

```cpp
[this](turtlesim::msg::Pose::SharedPtr msg) {
    latest_pose_ = *msg;
    has_pose_ = true;
}
```

- `[this]`: 람다 안에서 현재 객체의 멤버를 사용할 수 있게 해.
- `msg`: 받은 메시지를 가리키는 스마트 포인터야.
- `*msg`: 포인터가 가리키는 실제 메시지를 꺼내.
- `latest_pose_ = *msg`: 최신 자세를 복사해서 저장해.
- `has_pose_ = true`: 위치 메시지를 받았다고 표시해.

타이머는 **100ms마다 `publish_distance()`를 호출**해.

`private:` 아래 변수들은 노드 내부에서 사용할 데이터야. 이름 끝의 `_`는 **멤버 변수라는 것을 알아보기 위한 관례**이고 특별한 문법은 아니야.

마지막으로 C++ 클래스 정의는 **`};`로 끝난다**는 것도 확인해 줘.

이제 비워 둔 **`publish_distance()` 함수 안**을 채워줘:

```cpp
    void publish_distance()
    {
        if (!has_pose_) {
            return;
        }

        double distance = std::hypot(
            latest_pose_.x,
            latest_pose_.y
        );

        std_msgs::msg::Float32 msg;
        msg.data = static_cast<float>(distance);

        publisher_->publish(msg);
    }
```

각 부분은 이런 뜻이야.

```cpp
if (!has_pose_) {
    return;
}
```

`!`는 **부정**이야. 아직 위치 메시지를 받지 않았다면 함수를 끝내고 기다려.

```cpp
double distance = std::hypot(
    latest_pose_.x,
    latest_pose_.y
);
```

최신 위치의 `x`, `y`로 **원점까지 거리 √(x² + y²)**를 계산해.

```cpp
std_msgs::msg::Float32 msg;
```

발행할 `Float32` 메시지 객체를 만들어.

```cpp
msg.data = static_cast<float>(distance);
```

계산 결과는 `double`이고, 메시지의 `data`는 `float`라서 **자료형을 명시적으로 변환**해서 넣어.

```cpp
publisher_->publish(msg);
```

`publisher_`는 스마트 포인터이므로 `->`로 멤버 함수에 접근해. 준비한 메시지를 `/turtle_distance`로 보내는 줄이야.

이제 **위치 수신 → 최신 값 저장 → 0.1초마다 거리 계산·발행**까지 작성된 상태야. 다음에는 클래스 바깥에 실행용 `main()`을 붙이면 돼.

이제 **클래스가 끝나는 `};` 아래에** 실행용 `main()`을 추가해:

```cpp
int main(int argc, char* argv[])
{
    rclcpp::init(argc, argv);

    auto node = std::make_shared<DistancePublisher>();
    rclcpp::spin(node);

    rclcpp::shutdown();
    return 0;
}
```

각 줄은 이런 뜻이야:

- **`argc`, `argv`**: 프로그램 실행 시 전달한 명령행 인자의 개수와 내용이야.
- **`rclcpp::init(argc, argv)`**: ROS 2 통신을 초기화해.
- **`std::make_shared<DistancePublisher>()`**: 노드 객체를 만들고, 수명을 관리할 스마트 포인터를 반환해. `shared_ptr`은 앞서 배운 `unique_ptr`과 달리 소유권을 공유할 수 있어.
- **`rclcpp::spin(node)`**: 메시지와 타이머 이벤트를 기다리면서 콜백을 실행해.
- **`rclcpp::shutdown()`**: ROS 2 통신을 종료해.
- **`return 0`**: 프로그램이 정상 종료됐음을 나타내.

Python에서 작성했던 **`init → 노드 생성 → spin → shutdown`**과 같은 흐름이야.

다음에는 `CMakeLists.txt`에 이 파일의 빌드·설치 설정을 추가해야 `ros2 run`으로 실행할 수 있어.

확인해 보니 **`turtle_cpp` 폴더는 아직 없어.** 내가 패키지가 생성됐는지 확인하지 않고 다음 단계로 넘어갔네. 미안해.

작성한 `distance_publisher.cpp`는 `ros2_ws/src/`에 잘 있어. 아래 명령으로 패키지를 만들자:

```bash
cd /home/haeminkim/Desktop/haeminkim_backup/git/physicalai-lv1-HaeminKim/lv1_module2_student/ros2_ws/src

ros2 pkg create turtle_cpp --build-type ament_cmake --dependencies rclcpp turtlesim std_msgs
```

그다음 작성한 파일을 패키지 안으로 옮겨:

```bash
mv distance_publisher.cpp turtle_cpp/src/
```

그러면 구조가 이렇게 돼:

```text
src/
└── turtle_cpp/
    ├── CMakeLists.txt
    ├── package.xml
    └── src/
        └── distance_publisher.cpp
```

이제 **`turtle_cpp/CMakeLists.txt`**를 열면 돼.

좋아. **기존 내용은 지우지 말고**, 맨 아래의 `ament_package()` **바로 위에** 다음을 추가해:

```cmake
add_executable(distance_publisher src/distance_publisher.cpp)

ament_target_dependencies(distance_publisher
  rclcpp
  turtlesim
  std_msgs
)

install(TARGETS
  distance_publisher
  DESTINATION lib/${PROJECT_NAME}
)
```

각 설정의 역할은:

- `add_executable`: 작성한 C++ 파일로 실행 파일을 만들어.
- `ament_target_dependencies`: 실행 파일에 필요한 ROS 2 라이브러리를 연결해.
- `install`: `ros2 run`이 찾을 위치에 실행 파일을 설치해.

그리고 위쪽에 아래 세 줄이 있는지 확인해. **이미 있으면 추가하지 않아도 돼.**

```cmake
find_package(rclcpp REQUIRED)
find_package(turtlesim REQUIRED)
find_package(std_msgs REQUIRED)
```

저장하면 빌드할 준비가 된 거야.

다음은 **C++ 구독자를 만들어 Python 발행자의 거리 메시지를 받는 단계**야.

`turtle_cpp/src/`에 **`distance_subscriber.cpp`**를 만들고 작성해:

```cpp
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

class DistanceSubscriber : public rclcpp::Node
{
public:
    DistanceSubscriber() : Node("distance_subscriber_cpp")
    {
        subscription_ = this->create_subscription<std_msgs::msg::Float32>(
            "/turtle_distance",
            10,
            [this](std_msgs::msg::Float32::SharedPtr msg) {
                RCLCPP_INFO(
                    this->get_logger(),
                    "받은 거리: %.2f",
                    msg->data
                );
            }
        );
    }

private:
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr subscription_;
};
```

앞서 작성한 발행자와 구조가 비슷해.

- **`create_subscription<...>`**: `/turtle_distance`에서 `Float32` 메시지를 받도록 등록해.
- **`10`**: 메시지 큐 깊이야.
- **`[this](...) { ... }`**: 메시지가 올 때 실행할 람다 콜백이야.
- **`msg->data`**: 받은 메시지의 거리 값을 꺼내.
- **`RCLCPP_INFO`**: 터미널에 정보 로그를 출력해.
- **`"받은 거리: %.2f"`**: 거리 값을 소수점 둘째 자리까지 표시해.

이번 구독자는 **메시지가 올 때 바로 출력하므로 타이머가 필요 없어.** 여기까지 작성하면 다음에 `main()`과 빌드 설정을 추가하자.