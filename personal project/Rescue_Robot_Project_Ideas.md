# Rescue Robot Project Ideas

## 1. 프로젝트 방향

### 핵심 주제

**재난·홍수 환경에서 구조대보다 먼저 진입해 환경을 탐색하는 오픈소스
기반 Rescue UGV**

단순히 오픈소스 로봇을 조립하는 데서 끝내지 않고, 실제 재난 상황에서
필요한 기능을 하나씩 추가하면서 발전시키는 것을 목표로 한다.

### 기본 임무

홍수, 침수, 산사태, 붕괴 지역처럼 사람이 바로 진입하기 위험한 장소에
로봇을 먼저 투입한다.

로봇은 다음 정보를 수집한다.

-   LiDAR: 주변 지형과 장애물 측정
-   Camera: 시각 정보
-   IMU: 로봇 자세 및 움직임
-   Encoder: 바퀴 이동량
-   SLAM: 주변 지도 작성
-   Path Planning: 이동 가능한 경로 탐색

최종적으로 구조대가 **어디까지 안전하게 접근할 수 있는지 판단할 수 있는
지도와 환경 정보**를 제공한다.

------------------------------------------------------------------------

## 2. 단계별 개발 계획

### Phase 1 - 기본 ROS 2 Rover

4륜 또는 트랙형 오픈소스 Rover를 기반으로 시작한다.

1.  Rover 구동
2.  ROS 2 연결
3.  LiDAR 장착
4.  SLAM 구현
5.  실내 지도 생성

처음부터 로봇 전체를 새로 설계하지 않고, 검증된 오픈소스 플랫폼을 활용해
ROS 2와 센서 시스템부터 구축한다.

### Phase 2 - 자율주행

-   Camera 추가
-   장애물 인식
-   Nav2 / Path Planning
-   목표 지점까지 자율주행
-   LiDAR + Camera 기반 환경 인식

### Phase 3 - 재난 환경 대응 기구 설계

실내 Rover에서 야외 Rescue Rover로 발전시킨다.

고려할 문제:

-   진흙
-   자갈
-   경사면
-   바퀴 슬립
-   물과 습기
-   큰 장애물
-   전복 위험

기계 설계 개선 요소:

-   큰 Wheel 또는 Track
-   높은 Ground Clearance
-   방수 Enclosure
-   센서 보호 구조
-   전복 방지 구조
-   배수 구조
-   정비가 쉬운 모듈형 구조

------------------------------------------------------------------------

## 3. Electronic Skin / Robotic Skin

### 개념

일반 PCB와 달리 로봇의 표면에 부착하여 접촉이나 압력을 감지하는 유연한
센서 시스템이다.

관련 키워드:

-   Electronic Skin (E-skin)
-   Robotic Skin
-   Flexible Electronics
-   Stretchable Electronics
-   Tactile Sensor
-   Soft Sensor

### Flexible PCB와 Stretchable Electronics의 차이

**Flexible PCB** - 휘어질 수 있음 - 하지만 크게 늘어나지는 않음

**Stretchable Electronics / E-skin** - 휘어짐 - 늘어남 - 곡면 부착
가능 - 압력 및 접촉 센서를 피부처럼 배치 가능

------------------------------------------------------------------------

## 4. 참고할 오픈소스 프로젝트

### DexSkin

로봇용 소프트 촉각 피부 프로젝트.

참고: https://github.com/sdwistreich/dexskin

살펴볼 요소:

-   촉각 센서 구조
-   센서 제작 방식
-   하드웨어 인터페이스
-   펌웨어
-   센서 데이터 처리
-   로봇 표면에 센서를 배치하는 방법

### FlexiTac

FPC와 압력 감지 재료를 이용한 얇은 촉각 센서 구조.

기본적인 아이디어:

Flexible PCB / Electrode\
↓\
Pressure-sensitive material (예: Velostat)\
↓\
Flexible PCB / Electrode

압력을 받으면 전기적 특성이 변하고 이를 마이크로컨트롤러가 읽는다.

참고: https://flexitac.github.io/

### SoftArduino

늘어날 수 있는 전자 회로를 제작하는 오픈소스 연구 프로젝트.

참고: https://github.com/swoodman11/SoftArduino

Rescue Robot의 곡면이나 변형되는 구조에 전자회로를 통합하는 방법을
연구할 때 참고할 수 있다.

------------------------------------------------------------------------

## 5. Rescue UGV + E-Skin 아이디어

일반적인 Rescue UGV는 주로 비접촉 센서를 사용한다.

-   LiDAR: 주변 환경 측정
-   Camera: 시각 정보
-   IMU: 자세 측정

여기에 E-skin을 추가하면 로봇이 **환경을 직접 만져서 느끼는 능력**을
갖게 된다.

예:

로봇 오른쪽 측면이 잔해와 접촉\
→ E-skin 압력 증가 감지\
→ ROS 2로 접촉 위치 전달\
→ 로봇 정지\
→ 반대 방향으로 Steering\
→ 새로운 경로 계산

즉,

**LiDAR = 보기**

**Camera = 보기**

**E-skin = 만지기**

라는 서로 다른 감각을 결합할 수 있다.

------------------------------------------------------------------------

## 6. Contact-Aware Navigation

장기적으로 구현하고 싶은 핵심 기능.

센서 입력:

-   LiDAR
-   Camera
-   IMU
-   Encoder
-   E-skin / Tactile sensor

이를 ROS 2에서 통합하여 다음을 판단한다.

-   장애물 위치
-   접촉 여부
-   접촉 위치
-   접촉 압력
-   로봇 자세
-   바퀴 슬립
-   이동 가능 방향

그 결과 로봇이 단순히 장애물을 '보는' 것뿐 아니라 실제 접촉을 이용해
좁은 공간을 안전하게 이동하도록 한다.

프로젝트 제목 후보:

**Soft-Skin Equipped Rescue UGV for Contact-Aware Navigation in Flood
and Disaster Environments**

------------------------------------------------------------------------

## 7. 향후 확장 - Snake Rescue Robot

붕괴 건물이나 산사태 잔해 사이처럼 UGV가 들어가기 어려운 공간을 탐색하는
다관절 로봇.

연구 요소:

-   Servo Joint
-   Joint Angle Control
-   Forward Kinematics
-   Sinusoidal Gait
-   Snake Locomotion
-   ROS 2 Joint Control
-   Soft / Tactile Skin

특히 관절 전체에 E-skin을 적용하면 몸통이 잔해에 닿는 위치를 감지하면서
이동하는 로봇으로 확장할 수 있다.

------------------------------------------------------------------------

## 8. 장기 확장 - UAV + UGV 협업

### Drone (UAV)

넓은 재난 지역을 공중에서 빠르게 탐색한다.

### Rescue UGV

드론이 발견한 위험 지역이나 관심 지점으로 이동해 지상에서 상세 탐색한다.

구조:

Drone\
→ 넓은 지역 Mapping\
→ 침수/붕괴 지역 탐지\
→ 좌표 전달\
→ Rescue UGV 이동\
→ LiDAR + Camera + E-skin 상세 탐색\
→ 구조대에 정보 전달

장기적으로 **Multi-Robot Disaster Response System**으로 확장할 수 있다.

------------------------------------------------------------------------

## 9. 현재 가장 현실적인 시작점

처음부터 모든 것을 구현하지 않는다.

**Step 1:** ROS 2 호환 오픈소스 Rover 선정\
**Step 2:** 기본 구동\
**Step 3:** LiDAR + SLAM\
**Step 4:** Nav2 자율주행\
**Step 5:** 간단한 압력 센서 제작\
**Step 6:** Rover 범퍼 또는 측면에 Soft Sensor 부착\
**Step 7:** ROS 2에서 tactile sensor topic 생성\
**Step 8:** 접촉 시 정지/회피 동작 구현\
**Step 9:** 센서 영역을 늘려 E-skin 형태로 발전\
**Step 10:** 야외/재난 환경용 기구 구조 재설계

------------------------------------------------------------------------

## 10. 다음 조사 항목

다음 단계에서 실제 제작 후보를 정하기 위해 조사할 것:

-   ROS 2 호환 오픈소스 UGV 3\~5개 비교
-   각 플랫폼 가격
-   GitHub 활성도
-   ROS 2 지원 여부
-   LiDAR 장착 가능 여부
-   기구 수정 가능성
-   방수/야외 개조 가능성
-   국내에서 부품 조달 가능한지
-   DexSkin / FlexiTac 제작 난이도와 비용
-   E-skin을 ROS 2 센서로 연결하는 방법
