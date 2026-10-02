# Physical AI Lv.1 과제 학습·제출 가이드

작성일: 2026년 9월 2일  
마감 가정: 2026년 9월 3일  
우선순위: 모듈 ③ → 모듈 ① → 모듈 ② → 모듈 ④  
목표: 필수 요구사항을 모두 충족하는 4점 수준

## 1. 과제 전체 구조

Lv.1 과제는 다음 세 종류로 구성된다.

1. 강의별 미니 퀴즈
2. 모듈별 실습 산출물
3. 모듈 과제 4개

모듈 과제는 다음과 같다.

| 모듈 | 주제 | 문제 수 | 공식 예상 시간 |
|---|---|---:|---:|
| ① | 배달 로봇 온보딩 | 3 | 6~8시간 |
| ② | turtlesim 기반 C++·Python ROS2 패키지 | 10 | 20~25시간 |
| ③ | 로봇 좌표 변환 수학 라이브러리 | 6 | 12~15시간 |
| ④ | 픽앤플레이스 자세 추정과 궤적 생성 | 6 | 12~15시간 |

공통 제출 원칙:

- 문제 순서대로 진행한다. 앞 문제의 코드가 뒤 문제에서 재사용된다.
- 동작하는 코드뿐 아니라 결과가 나온 이유도 설명한다.
- 터미널 출력은 이미지가 아닌 텍스트 코드 블록으로 기록한다.
- 그래프, RViz2, turtlesim 궤적처럼 화면 자체가 결과인 경우만 이미지를 사용한다.
- 난수는 `np.random.default_rng(42)`로 고정한다.
- 부동소수점은 `==` 대신 `np.allclose` 또는 `np.isclose`로 비교한다.
- `.venv/`, `build/`, `install/`, `log/`, `__pycache__/`는 ZIP에서 제외한다.
- 노트북은 제출 전에 Restart Kernel and Run All Cells를 수행한다.

과제 원문:

- [과제 안내](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C_%EC%95%88%EB%82%B4.md)
- [모듈 ① 지시문](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C1_%EB%B0%B0%EB%8B%AC%EB%A1%9C%EB%B4%87_%EC%98%A8%EB%B3%B4%EB%94%A9.md)
- [모듈 ② 지시문](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C2_turtlesim_ROS2%ED%8C%A8%ED%82%A4%EC%A7%80.md)
- [모듈 ③ 지시문](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C3_%EC%A2%8C%ED%91%9C%EB%B3%80%ED%99%98_%EC%88%98%ED%95%99%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC.md)
- [모듈 ④ 지시문](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C4_%ED%94%BD%EC%95%A4%ED%94%8C%EB%A0%88%EC%9D%B4%EC%8A%A4_%EC%9E%90%EC%84%B8%EC%B6%94%EC%A0%95.md)

## 2. 현재 준비 상태

### 모듈 ①

준비된 내용:

- 임베디드·Edge AI·클라우드 연산 분담 개념
- 지연 예산과 카메라 데이터 전송량 계산
- localhost SSH 접속
- SSH 키 생성과 공개키 등록
- 원격 명령 실행과 `scp` 파일 전송
- loop 장치 생성과 기본 조사

부족한 내용:

- 작업 6개의 완성된 연산 분담표
- 인지·판단·제어 계층 및 갱신 주기표
- Hard/Firm/Soft 실시간 분류
- 완성된 udev 규칙 파일
- 연결 순서를 바꾼 후 고정 이름이 유지되는지 검증한 출력
- 실제 USB 센서용 udev 규칙 초안
- GitHub PR, 셀프 리뷰, 충돌 해결, merge/rebase 비교

### 모듈 ②

준비된 내용:

- C++ 기초, RAII, 스마트 포인터, 다형성 예제
- 일반적인 rclpy publisher와 rclcpp subscriber
- colcon, launch, YAML 파라미터 예제
- RViz2, Marker, rosbag, pytest 개념

부족한 내용:

- 과제 규격의 `turtle_py`, `turtle_cpp`, `turtle_interfaces` 패키지
- `/turtle_distance` 발행·구독과 정사각형 주행
- Service·Action 서버 및 클라이언트
- 커스텀 msg·srv·action
- QoS 비호환 재현과 복구
- turtlesim TF·Marker·rosbag·pytest 통합 결과

### 모듈 ③

준비된 내용:

- 벡터, 정사영, 외적, 평면 법선 개념
- `rot_x`, `rot_y`, `rot_z`, 로드리게스 공식
- Gram-Schmidt 개념
- 가우스 소거와 피벗팅 학습 자료
- `make_T`, `inv_T` 개념
- 문제별 노트북 6개

현재 치명적인 문제:

- 노트북에 저장된 통과 출력과 실제 `src` 코드가 일치하지 않는다.
- `vectors.py`의 `project()`가 `b` 대신 `a`를 다시 대입한다.
- `row_echelon()`이 일반적인 크기와 rank 결손 행렬을 안정적으로 처리하지 못한다.
- `gauss_eliminate()`와 `inverse_gauss_jordan()`이 실제 모듈에 없다.
- `rotation.py`의 `is_rotation()`이 `pass` 상태다.
- 축·각 복원과 쿼터니언 함수가 없다.
- `transform.py`는 `make_T`, `inv_T` 외 함수가 누락됐다.
- `coordinate_chain.py`가 없다.
- `test_rotation.py`에 문법 오류와 함수명 오타가 있다.
- `test_transform.py`가 비어 있다.
- 현재 `pytest`는 테스트 수집 단계에서 실패한다.

따라서 기존 노트북의 성공 출력은 제출 근거로 사용할 수 없고, 현재 코드로 처음부터 다시 실행해야 한다.

### 모듈 ④

준비된 내용:

- 쿼터니언, SLERP, 고유값·고유벡터의 기초 개념

부족한 내용:

- `PosePipeline`
- 회전행렬과 쿼터니언의 양방향 변환
- SLERP 직접 구현과 경계 처리
- 선형·스플라인·5차 다항식 궤적
- PCA와 Kabsch 자세 추정
- 이상치 제거 실험
- `demo.gif`와 `presentation.md`

## 3. 내일까지의 7시간 계획

### 0:00~0:20 — 안전한 작업본과 환경 준비

- 기존 파일은 보존하고 별도의 깨끗한 모듈 ③ 제출 디렉터리를 만든다.
- `.venv`를 생성한다.
- NumPy, SciPy, Matplotlib, pytest, JupyterLab, ipykernel을 설치한다.
- Jupyter 커널 `pose_lab`을 등록한다.
- 시스템 Python 패키지는 요구 버전보다 낮으므로 사용하지 않는다.

### 0:20~2:40 — 모듈 ③ `src` 복구

다음 순서로 구현한다.

1. `vectors.py`
2. `rotation.py`
3. `transform.py`
4. `coordinate_chain.py`

구현 직후 각 함수에 간단한 정상·경계 검사를 수행한다.

### 2:40~3:30 — 모듈 ③ 테스트 복구

- 제출 폴더 이름을 `tests/`로 통일한다.
- 회전행렬 성질 테스트 4개 이상을 작성한다.
- `inv_T`와 점·방향·점군 변환 테스트를 작성한다.
- `pytest -v tests`를 실행한다.
- 모든 테스트가 통과하기 전에는 노트북 재실행으로 넘어가지 않는다.

### 3:30~4:20 — 여섯 노트북 재실행

다음 순서를 지킨다.

1. `01_vectors.ipynb`
2. `02_rotation.ipynb`
3. `03_reorthogonalize.ipynb`
4. `04_linear_system.ipynb`
5. `05_transform.ipynb`
6. `06_chain.ipynb`

확인 사항:

- 실행되지 않은 코드 셀이 없어야 한다.
- 오류 출력이 없어야 한다.
- 모든 검증 셀이 True 또는 PASS를 출력해야 한다.
- 그래프와 설명이 저장되어야 한다.

### 4:20~5:00 — 모듈 ① 문제 1 작성

- 연산 분담표 6행을 완성한다.
- 카메라 원시 영상 전송량을 계산한다.
- 인지·판단·제어 계층과 주기를 작성한다.
- Hard/Firm/Soft 실시간 분류를 작성한다.
- 주기·지연·지터를 각각 한 문장으로 설명한다.

카메라 전송량:

```text
1920 × 1080 × 3 byte × 30 fps
= 186,624,000 byte/s
≈ 186.6 MB/s
≈ 1.49 Gbit/s
```

따라서 LTE로 무압축 영상을 계속 클라우드에 보내는 설계는 성립하기 어렵다.

### 5:00~5:50 — 모듈 ① 문제 2 완성

텍스트로 남길 출력:

- `systemctl status ssh`
- `ss -tlnp | grep :22`
- 비밀번호 없는 SSH 접속
- `who`
- `echo $SSH_CONNECTION`
- 원격 `uname -a`
- `scp` 결과
- `udevadm info`의 `loop/backing_file`
- `ls -l /dev/robot_*`

udev 규칙은 실제로 확인한 backing file 경로를 사용한다. 예시 loop 번호를 그대로 사용하지 않는다.

장치 해제 전에는 다음 명령으로 이번 실습에서 만든 장치인지 확인한다.

```bash
losetup -j ~/fake_sensors/lidar.img
losetup -j ~/fake_sensors/imu.img
```

확인된 정확한 장치만 `losetup -d`로 해제한다.

### 5:50~6:35 — 모듈 ① 문제 3 완성

전용 공개 저장소 이름:

```text
delivery-robot-onboarding
```

필수 브랜치:

```text
feature/compute-layout
feature/udev-rules
branch-a
branch-b
```

진행 순서:

1. `README.md`에 로봇 센서 사양을 작성해 첫 커밋을 만든다.
2. `feature/compute-layout`에 문제 1 문서를 커밋한다.
3. `feature/udev-rules`에 규칙 파일과 설명표를 커밋한다.
4. 한 브랜치로 PR을 열고 셀프 리뷰를 남긴다.
5. 리뷰를 반영한 추가 커밋 후 병합한다.
6. `branch-a`, `branch-b`에서 같은 줄을 다르게 수정해 충돌을 만든다.
7. 충돌 표식을 설명하고 해결한다.
8. 나머지 기능 브랜치는 `git rebase main` 후 병합한다.
9. merge와 rebase의 `git log --oneline --graph` 출력을 각각 저장한다.

### 6:35~7:00 — 최종 검수와 ZIP 생성

- 파일 구조와 이름을 확인한다.
- ZIP 내부에 캐시·가상환경·교사용 자료가 없는지 확인한다.
- ZIP을 임시 폴더에 풀어 다시 검사한다.

## 4. 모듈 ③ 구현 명세

### `src/vectors.py`

구현할 공개 함수:

```python
as_vector(v)
dot(a, b)
norm(v)
angle_between(a, b, degrees=True)
normalize(v, eps=1e-12)
project(a, b)
reject(a, b)
skew(a)
cross(a, b)
plane_normal(P1, P2, P3)
row_echelon(A, pivoting=True)
rank(A)
det(A)
gauss_eliminate(A, b, pivoting=True, verbose=False)
inverse_gauss_jordan(A)
```

학습 포인트:

- `dot()`과 `norm()`은 스칼라를 반환한다.
- `normalize()`, `project()`, `reject()`는 벡터를 반환한다.
- `project(a, b)`의 마지막 곱은 내적이 아니라 스칼라와 벡터의 곱이다.
- `row_echelon()`은 3×3에만 고정하지 않고 일반적인 `(m,n)` 행렬을 처리한다.
- 피벗은 현재 열에서 절댓값이 가장 큰 행을 고른다.
- 거의 0인 값은 `== 0`이 아니라 허용오차로 판단한다.

### `src/rotation.py`

구현할 공개 함수:

```python
rot_x(theta)
rot_y(theta)
rot_z(theta)
rodrigues(axis, theta)
gram_schmidt(A)
orthogonality_error(R)
is_rotation(R, atol=1e-8)
axis_angle_from_matrix(R, atol=1e-8)
quaternion_from_axis_angle(axis, angle)
```

회전행렬의 핵심 검증식:

```math
R^T R = I
```

```math
\det(R) = 1
```

- 직교행렬이더라도 행렬식이 -1이면 반사이므로 회전행렬이 아니다.
- 로드리게스 공식의 회전축은 함수 안에서 정규화한다.
- 축·각 복원은 회전 없음과 180도 회전을 별도 경계 상황으로 처리한다.

### `src/transform.py`

구현할 공개 함수:

```python
make_T(R, t)
inv_T(T)
inv_T_batch(Ts)
to_homogeneous(P, w=1.0)
transform_point(T, p)
transform_direction(T, v)
transform_points(T, P, w=1.0)
least_squares_normal_equation(A, b)
rmse(residual)
```

핵심 공식:

```math
T = \begin{bmatrix} R & t \\ 0 & 1 \end{bmatrix}
```

```math
T^{-1} = \begin{bmatrix} R^T & -R^Tt \\ 0 & 1 \end{bmatrix}
```

- `make_T`는 `R`, `t`를 배열로 변환하고 shape를 검사한 다음 `T`에 대입한다.
- `inv_T`는 `T.shape`를 먼저 검사한 다음 회전과 병진을 분리한다.
- 점은 `w=1`이므로 회전과 병진이 적용된다.
- 방향은 `w=0`이므로 병진이 적용되지 않는다.
- 점군 변환은 반복문 없이 행렬 연산으로 처리한다.

### `src/coordinate_chain.py`

구현할 공개 인터페이스:

```python
CoordinateChain
default_chain()
camera_point_to_base(p_cam, chain=None)
base_point_to_camera(p_base, chain=None)
```

핵심 순서:

```math
T_{base\leftarrow camera}
= T_{base\leftarrow link}
  T_{link\leftarrow camera}
```

역방향 변환에서는 곱셈 순서가 뒤집힌다.

## 5. 테스트 계획

### 회전 테스트

- 회전행렬의 열벡터가 단위벡터인지 확인한다.
- 서로 다른 열의 내적이 0인지 확인한다.
- 행렬식이 1인지 확인한다.
- 역행렬이 전치행렬과 같은지 확인한다.
- Gram-Schmidt 후 직교성이 복구되는지 확인한다.
- 반사행렬은 회전행렬로 판정되지 않아야 한다.

### 동차변환 테스트

- `T @ inv_T(T)`와 `inv_T(T) @ T`가 모두 단위행렬이어야 한다.
- `inv_T(T)`가 검산용 `np.linalg.inv(T)`와 일치해야 한다.
- 점과 방향의 변환 결과 차이가 병진 벡터여야 한다.
- 점군 벡터화 결과가 반복문 결과와 같아야 한다.
- base → camera → base 왕복 후 원래 좌표가 복원되어야 한다.
- 정규방정식 결과가 검산용 `np.linalg.lstsq`와 일치해야 한다.

## 6. 제출 구조

### 모듈 ③

```text
lv1_module3_제출자이름.zip
├── notebooks/
│   ├── 01_vectors.ipynb
│   ├── 02_rotation.ipynb
│   ├── 03_reorthogonalize.ipynb
│   ├── 04_linear_system.ipynb
│   ├── 05_transform.ipynb
│   └── 06_chain.ipynb
├── src/
│   ├── __init__.py
│   ├── vectors.py
│   ├── rotation.py
│   ├── transform.py
│   └── coordinate_chain.py
├── tests/
│   ├── test_rotation.py
│   └── test_transform.py
└── requirements.txt
```

제외할 파일:

- `assignment/`
- `tests_teacher/`
- `01_vectors_prob.ipynb`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`

### 모듈 ①

```text
lv1_module1_제출자이름.zip
├── report.md
├── rules/
│   └── 99-robot-sensor.rules
└── images/
```

`report.md`는 다음 절을 반드시 포함한다.

```markdown
## 문제 1
## 문제 2
## 문제 3
```

문제 3에는 공개 저장소 URL과 PR URL을 넣는다.

## 7. 시간이 부족할 때의 우선순위

1. 모듈 ③ `src`와 테스트를 정상화한다.
2. 여섯 노트북을 현재 코드로 다시 실행한다.
3. 모듈 ③ ZIP을 검수한다.
4. 모듈 ①의 실제 SSH·udev 증빙을 완성한다.
5. 모듈 ① GitHub PR과 충돌 실습을 완성한다.
6. 설명 문장을 다듬는다.

검증하지 않은 성공 출력이나 수행하지 않은 명령 결과를 작성하지 않는다. 6시간보다 적게 남으면 두 과제를 모두 4점 수준으로 완성하기 어렵다는 점을 인정하고, 실제로 완료한 항목을 정확히 제출한다.

## 8. 마감 이후 학습 순서

### 모듈 ②

다음 순서를 지킨다.

1. C++ 수동 빌드와 CMake
2. C++ 센서 클래스·RAII·STL
3. `turtle_py` rclpy 노드
4. `turtle_cpp` rclcpp 노드
5. Service와 Action
6. `turtle_interfaces` 커스텀 인터페이스
7. QoS 비호환 재현과 복구
8. colcon 의존성
9. launch·YAML·namespace
10. TF·RViz2·rosbag·pytest

문서에 선택과제 표현이 있더라도 최종적으로는 10문제를 모두 수행하는 것을 목표로 한다.

### 모듈 ④

모듈 ③이 완전히 검증된 뒤 시작한다.

1. `PosePipeline`
2. 회전행렬 ↔ 쿼터니언
3. SLERP와 경계 처리
4. 선형·스플라인·5차 다항식 궤적
5. PCA·Kabsch 자세 추정
6. 이상치 제거와 오차 분석
7. `demo.gif`
8. `presentation.md`

## 9. 최종 체크리스트

### 모듈 ③

- [ ] 올바른 가상환경 커널을 사용했다.
- [ ] `pytest -v tests`가 전수 통과한다.
- [ ] 여섯 노트북을 Restart & Run All 했다.
- [ ] 오류 출력과 실행되지 않은 코드 셀이 없다.
- [ ] 모든 난수 시드가 42다.
- [ ] `np.linalg`는 직접 구현 대체가 아닌 검산·비교에만 사용했다.
- [ ] 그래프와 설명이 저장되어 있다.
- [ ] ZIP에서 가상환경·캐시·교사용 자료를 제외했다.

### 모듈 ①

- [ ] 연산 분담표가 6행 모두 채워졌다.
- [ ] 카메라 전송량 계산이 들어 있다.
- [ ] 인지·판단·제어와 Hard/Firm/Soft 표가 있다.
- [ ] SSH 관련 출력이 텍스트로 기록됐다.
- [ ] udev 규칙 파일이 제출 폴더에 있다.
- [ ] 연결 순서를 바꾼 뒤 고정 이름을 검증했다.
- [ ] 실제 USB 센서용 규칙 초안이 있다.
- [ ] 공개 저장소 URL과 PR URL이 있다.
- [ ] 셀프 리뷰와 반영 커밋이 있다.
- [ ] 충돌 해결 과정이 기록됐다.
- [ ] merge와 rebase 이력 그래프가 모두 있다.

