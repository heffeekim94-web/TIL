glossary
**Lifecycle Node** - 활성되기 전 대기 상태로 각 행동 노드를 준비시키는 것 - 명시적 상태.
**트레이드오프** - 큰 데이터가 교환되는 성능은 composition하고, 안전*독립성이 중요한 노드는 격리 시키는 것. 
**Uncondfiguired** - node 초기 상태
**configure()** - node 자원 준비 명령
**Inactive** - node 노드 설정 완료, 사용 대기
**active()** - node 동작 명령
**Active** - node 실제 동작 상태
**deactivate()** - node 대기 명령
**shutdown()** - node 종료 명령

<br>

## Lifecycle Node
활성되기 전 대기 상태로 각 행동 노드를 준비시키는 것 - 명시적 상태.

<br>

### 관리 순서:
1. Uncondfiguired(초기)
2. configure()
3. Inactive(설정완료, 대기)
4. activate()
5. Active(실제 동작) 

<br>

### shut down 순서:
deactivate() 대기 --> shutdown() 으로 종료

<br>

### *문제* 해결
- 시작 순서
    - 활성시킬 노드를 준비/configure() 시킨 뒤,
    - 준비 된 것을 확인 후
    - 순서대로 activate()
    - **핵심: 준비되지 않았는데 제어가 도는 것을 방지**

<br>

### in *Robotics* 
- Nav2가 Lifecycle Node로 구성됨.
- 전체 주행 스택을 관리되는 상태로 일괄 기동 또는 정지함.

<br>

## Composition
Composition - 여러 노드를 하나의 프로세스로 함케 실행.

<br>

### *문제*
독립 프로세스의 격리는 *견고*하지만 but 비용이 *high cost*
켰을때 모든 노드를 작동 시키고 데이타를 복사/직렬하면 메모리 차지 및 *낭비가 큼*.

<br>

### 해결
Composition
같은 프로세스 안의 메모리를 **직접 공유(intra-process communication)**, 복사 없이 데이터 give-n-take

<br>

### 구분

|         |   독립 프로세스 (기본)  |    Composition (합성)       |
|---------|---------------------|----------------------------|
|   견고성  | 높음(하나 죽어도 격리) |        낮음(같이 죽음)         |
| 통신 비용 |      복사*직렬화      |      메모리 공유(복사 x)       |
|   적합   |      대부분의 노드    | 대요양 데이터를 주고받는 노드 묶음 | 

즉, **트레이드오프** - 큰 데이터가 교환되는 성능은 composition하고, 안전*독립성이 중요한 노드는 격리 시키는 것. 

<br>

### Tip
'shared_ptr'이 여기서 빛을 발함

<br>

## Colcon 
workspace - 여러 패키지(노드/인터페이스)를 한데 모은 곳

colcon - workspace(ws)를 만드는 는 것. CMake와 setup.py를 의존성 순서대로 호출해 주는 상위 도구.

*참조 - 강의 7: CMake, 강의 5: setup.py*

<br>

#### 명령어
```bash
colcon build
```


<br>
<br>
<br>
<br>















build에 parameters를 넣어 놔야 한다. 

아래와 같이 폴더를 생성한다. 

home
    ros2_ws
        src
            demo_cpp
                demo_cpp
            demo_python
                demo_python
                    __init__.py
                    talker.py
                resource
                    demo.py
                    package.xml
                    setup.cfg
                    setup.py
                    

cmd창에 아래의 순서대로 명령어를 입력한다. 

1. 코드 작성
- lunch파일들을 대부분 작성하게 된다
- 이번 demo에서는 lunch파일을 만들면 


2. 작업공간을 빌드하는 도구
```bash
colcon build
```
3. bash를 install 하고
```bash
source install/setup.bash
```

4. launch를 한다
```bash
ros2_ws/src$ ros2 launch demo_bringup demo.launch.py
```

* ros2_ws 폴더를 새로 홈에 만들고 src폴더 안에 해당 폴더들을 만드는게 좋다

<br>

험난한 개발자 세상에서 살아남기

1. 지금까지 만들어왔던 것


- 볼링 에이아이

왜 <br>
단순한 관심 - Ai랑 볼링치면 어떨까

가장 막혔던 지점
학습시킬 데이타 세트 찾기가 어려웠음.
10만장 이상이 필요했음
비용이 어마해서 포기

어떻게 넘었나


- 화재진압드론

왜: 
기존의 한계점 넘어보고싶음

막혔던 지점
ros2가 없었던 지점

해결
ros1을 독학

결과
자율주행경진대회 3위
ros에서 비행제어를 위한 알고리즘 설계 방법 학습


- 반려 로봇강아지

왜
vr로 강아지랑 소통 시도

막혔던 지점
중국 제품 , 지원 어려움
동물의 움직임 파악이 우선..

어떻게 넘었나
ros2 직접 독학 모든 패키지를 직접 개발

결과와 남는 것
vr 업체에 판매
ros2 심화 사용법, 전반적인 로봇 시스템에 대한 이해도 상승


- 경찰과 도둑 관리 어플 

왜
추억의 경도 하는 10~20대.. 관리를 앱으로 시도

막혔던
앱개발 처음. 앱스토어 출시 목표 아무것도 모름

넘었던
시니어 개발자에게 알려달라

남은 것 
어플 출시


- 사주로 결혼상대 매칭

왜
나는 솔로 보고 잘 팔리겠다

알고리즘 어려웠음

사주/명리학 공부

결혼정보 회사에 판매


- 캐리터 대화

왜
아이돌도 소통하는데 애니미는

ai모델 어려움 저작궈ㅓㄴ??

본격적인 ai 공부
저작권 ai로 돈 받음



프로젝트 고르는 기준

공부하고 만드는게 아니고 
만들면서 공부하는 것

순서

재밌는가

공부할 값어치가 있는가

주어진 시간과 예산 안에서 되는가

이력서에 쓸 수 있는가
- 설명이 가능해야 함



거르는 것

남들이 하는거 - 막히면 이유 없어짐

남 눈에 좋아 보이는 것 - 흥미 없음, 2주 못감

설계부터 완벽 - 미루게 됨

자료가 거의 없는 최신 기술 - 첫 판매 시간만 녹음

6개월 - 3주째에 조용히 사라짐..


고르는 것

내가 실제로 불편했던 것 - 쓸 사람은 최소 한명 확실

완성이 상상이 되는 것

2주 안에 뭐라도 돌아가는 크기 - 첫 성공이 빨라야 안저븝니다. 

검색하면 답이 나오는 기술 - 막혔을 때 빠져나올 구멍

만들다 보면 

ros 코드 커뮤니티

Stack overflow


Velog



