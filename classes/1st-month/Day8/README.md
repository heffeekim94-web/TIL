Date: 2026 Aug 12, Wednesday

컴퓨터 성능이 좋은데 느리다고 느껴지면 타이머 콜백 현상을 살펴보면 된다.

<br>

## Review
- 발행자/ 구독자 노드가 있고 발행자는 누가 수신하는지 모른다.
- "어떤 일이 생기면 이 함수를 불러라"를 등록해 두는 이벤트 구동(event-driven) 은 콜백이라 한다
- spin 코드를 두지 않으면 콜백을 실행시킬 수 없다.

<br>

## To Do
python을 사용해서 ROS2를 만들어본다. 


<br>

## Today
10강~15강

### 10강
[Topic 통신과 노드 작성 (pub/sub,rclpy-rclccp)](https://teamsparta.notion.site/13-QoS-DDS-3ae2dc3ef51481aa9d39c0da7efb4a1c)

<br>

#### Q = 10 or More
- Q 깊이는 전달 받는 정보량에 따라 적정한 깊이를 선정해야 한다.
- 너무 얕게 잡으면 메모리 과부하로 인해 셧다운이 될 수 있다.
- 10-20% 추천
- 5 Mb 이상은 안하길 추천
- Mdot을 사용하는 것을 추천
- 품질
* dds -> Qos-> Q
[DDS 참조 웹사이트](https://fast-dds.docs.eprosima.com/en/2.6.x/index.html#)

<br>
    - Remember: 네트워크, CPU 메모리 용량때문에 고르는 것!
<br>
- 구독 Topic을 잘 못 입력해도 같은 문제가 발생할 수 있다.
- 필터링 하는 속도를 못따라 잡아도 그럴 수 있음
- Q에 들어오지도 않았는데 데이타를 요청해도 같은 문제가 발생할 수 있음
- 13강때 Q정책에 따라 깊이를 설정하는 방법을 배울거다.

### 실습 1
[발행 & 구독 node 작성](activity.md)


### 13강

#### DDS
- 우리는 fast DDS 사용 예정
- IPS만 조정할 수 있지만 
- DDS구조를 바꾸기에는 어렵다. 

#### QoS
- 앵코더 센서는 신뢰성 높게 설정하는게 좋을거임
- LiDAR의 용량이 크기 때문에 Q를 얕게 하는 것
- 줄인만큼 여러번 실행하면 된다. 

<br>

### 14강

[TF2 좌표 변환](https://teamsparta.notion.site/14-TF2-3ae2dc3ef514815aa572f520616a0abf)

<br>

#### 로봇
- 각 로봇에게도 좌표가 입력되어 있음
- ROS2 가 없었을때는 암의 위치가 좌표 기준으로 어디에 있는지 계속 알려야 했다 
- 이제는 ROS2가 그걸 알아서 한다. 
- 맵-실제로 거기 있는지 추정(odometry)-수정 좌표-base link
- ROS2를 사용하는 이유는 로봇의 움직임을 최적화하기 위해 

### 실습 2
[로봇 구현](activity2.md)
[참조 웹사이트](https://www.youtube.com/watch?v=dZ_CyyEvBE0)







