# turtlesim 도형 그리기 오류 해결: ROS 통신 환경 분리

## 증상과 결과

처음에는 삼각형, 오각형, 팔각형이 잘 그려졌지만 재실행하면 그림이 이상해졌다. 사용자는 당시 발행자 두 개의 충돌 문제를 안내받았고, turtlesim·액션 서버·액션 요청 터미널에 설정을 적용한 후 해결되었다고 확인했다.

## 실제 명령 기록에서 확인한 해결 설정

`/home/haeminkim/.bash_history`에서 세 역할의 실행 명령 앞에 다음 설정이 사용된 것을 확인했다.

```bash
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=37
```

- `ROS_LOCALHOST_ONLY=1`: ROS 통신을 같은 컴퓨터 안으로 제한한다.
- `ROS_DOMAIN_ID=37`: 같은 도메인 번호를 사용하는 노드끼리 통신하도록 분리한다. 37은 당시 사용한 번호다.
- 세 터미널 모두 같은 설정을 적용해야 turtlesim, 액션 서버, 액션 요청이 서로 연결된다.

이 설정은 다른 컴퓨터나 다른 도메인의 노드가 실습에 간섭하는 것을 막는다. 같은 컴퓨터의 같은 도메인에서 중복 실행한 발행자는 별도로 종료해야 한다. 환경 변수의 역할은 [ROS 2 환경 설정 문서](https://docs.ros.org/en/foxy/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html)와 [도메인 설명](https://docs.ros.org/en/lyrical/Concepts/Intermediate/About-Domain-ID.html)에 설명되어 있다.

당시 발행자 목록 출력은 확보되지 않아 두 번째 발행자가 어느 컴퓨터의 어떤 노드였는지는 확정할 수 없다. 앞선 문서에서 이전 제어 프로그램이 남은 상황을 중심으로 설명했지만, 실제 기록에서 확인된 해결책은 위 통신 환경 설정이다.

## 세 터미널에 입력할 코드

기존 turtlesim과 액션 서버를 각 실행 터미널에서 Ctrl+C로 종료한 뒤 아래 순서로 다시 실행한다. 환경 변수를 바꾸어도 이미 실행 중인 프로세스에는 소급 적용되지 않는다.

아래 환경 준비 경로는 현재 존재하는 백업 작업 공간을 사용한다. 당시 기록의 상대 경로 `lv1_module2_student/ros2_ws/`를 그대로 복원한 것은 아니다. 다른 작업 공간을 사용한다면 `source` 경로를 해당 공간의 `install/setup.bash`로 바꾼다.

### 터미널 1: 거북이 창

```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=37
ros2 run turtlesim turtlesim_node
```

### 터미널 2: 액션 서버

```bash
source /opt/ros/humble/setup.bash
source /home/haeminkim/Desktop/haeminkim_backup/ros2_ws/install/setup.bash
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=37
ros2 run turtle_examples ex06_polygon_action_server
```

### 터미널 3: 액션 요청

```bash
source /opt/ros/humble/setup.bash
source /home/haeminkim/Desktop/haeminkim_backup/ros2_ws/install/setup.bash
export ROS_LOCALHOST_ONLY=1
export ROS_DOMAIN_ID=37
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 8, side_length: 1.0}" --feedback
```

위 팔각형 요청은 명령 기록에서 확인했다. 아래 삼각형과 오각형 요청은 프로젝트의 액션 서버 소스에 있는 예시다. 한 도형의 결과가 나온 후 다음 요청을 보낸다.

```bash
# 삼각형
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 3, side_length: 2.0}" --feedback

# 오각형
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 5, side_length: 1.5}" --feedback
```

## 발행자 확인

같은 설정을 적용한 터미널 3에서 확인한다.

```bash
ros2 topic info /turtle1/cmd_vel -v
```

발행자 수와 발행 노드 이름을 확인한다. 이 실습에서 액션 서버 하나만 속도 명령을 발행한다면 `Publisher count: 1`이 기대값이다. 여전히 두 개라면 같은 컴퓨터·도메인에서 중복 실행된 서버나 다른 제어 프로그램을 확인한다.

## 추가 점검 방법: 중복 프로그램 종료와 시작 상태 초기화

통신 환경 분리 외에, 앞서 정리한 중복 프로그램 종료와 초기화 방법도 점검 절차로 남긴다. 이 방법이 당시 실제로 사용된 해결 명령이었다고 확정하는 것은 아니다.

1. 이전 액션 서버, 키보드 조종 프로그램, 반복 발행 중인 `ros2 topic pub`를 해당 터미널에서 Ctrl+C로 종료한다.
2. 같은 ROS 환경을 적용한 터미널에서 발행자를 확인한다.

```bash
ros2 node list
ros2 topic info /turtle1/cmd_vel --verbose
```

모든 속도 명령 발행자를 종료한 상태라면 발행자 수는 `0`이 기대값이다. 액션 서버를 하나 실행한 뒤에는 이 실습 구성에서 `1`이 기대값이다. 발견 정보 반영에 시간이 걸릴 수 있으므로 종료 직후에는 잠시 후 다시 확인한다.

3. 제어 프로그램을 멈춘 상태에서 필요하면 거북이의 시작 상태를 초기화한다.

```bash
ros2 service call /reset std_srvs/srv/Empty "{}"
```

초기화 응답을 확인한 후 액션 서버를 한 개만 실행하고 도형 요청을 보낸다. `/reset`은 외부 액션 서버나 발행자를 종료하지 않으므로, 중복 프로그램 정리를 먼저 해야 한다.

| 해결 방법 | 적용할 상황 |
|---|---|
| 세 터미널에 `ROS_LOCALHOST_ONLY=1`, `ROS_DOMAIN_ID=37` 설정 후 재실행 | 다른 컴퓨터나 다른 도메인의 노드와 통신을 분리할 때. 실제 명령 기록에서 확인한 방식 |
| 중복 제어 프로그램 종료 | 같은 컴퓨터의 같은 도메인에서 여러 프로그램이 속도 명령을 보낼 때 |
| 제어 프로그램 정지 후 `/reset` 호출 | 이전 그림의 마지막 위치·방향이 남아 시작 조건을 초기화해야 할 때 |

## 배운 점

ROS 2 실습에서는 코드뿐 아니라 통신 범위와 도메인 설정도 결과에 영향을 준다. 새 터미널을 열면 필요한 환경 설정을 다시 적용하고, turtlesim·액션 서버·액션 요청의 설정을 일치시킨다.

문서 작성 시 명령 기록과 프로젝트 소스를 확인했으며, 시뮬레이터를 직접 재실행하지는 않았다.
