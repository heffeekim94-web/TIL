Date: 2026 Aug 12, Wednesday

# Class Activity

#### Node coding

<br>

1. python 파일을 어제 받아놨던 turtlebot ros2 파일에서 노드를 만들어 본다

turtlebot3_ws/src/ 위치에서 새로운 파일을 생성하여 publisher.py 파일에 내용을 하단과 같이 작성한다. 

구독 코드를 아래와 같이 작성
```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')      # 노드 이름
        # 발행자 생성: (메시지타입, 토픽명, 큐깊이)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        # 0.05초(20Hz)마다 tick 호출
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().info('발행 시작')

    def tick(self):
        msg = Twist()
        msg.linear.x = 0.3      # 0.2 m/s 전진
        msg.angular.z = 0.4     # 약간 회전 (original : 0.1)
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = VelocityPublisher()
    rclpy.spin(node)            # 콜백이 돌기 시작
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

```bash
ros2 topic list
```

```bash
/cmd_vel
/parameter_events
/rosout
```

```bash
ros2 topic echo /cmd_vel
```

- 아래와 같이 1회성으로 값을 임의로 바꿔서 조회해볼 수 있음
```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}" --rate 10
```



```bash
ros2 run rqt_graph rqt_graph
```
를 입력하면 그래프로도 발행/구독 현황을 시각화 할 수 있다. 