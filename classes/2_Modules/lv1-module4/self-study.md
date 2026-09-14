Date 2026 Sept 8일

### ffmpeg : 소프트웨어/ 도구, 프로그램 + 라이브러리
- 영상 포맷 변환, 영상 압축, 해상도 변경, 영상 자르기/합치기, 소리 추출, 프레임을 이미지로 추출, 카메라 영상 녹화/ 스트리밍
- 영상, 카메라 분야

사용 코드:
```bash
ffmpeg -i input.mp4 output.avi
```

- 영상과 소리를 터미널에서 가공하는 도구
- FF = fast forward
- MPEG = 영상,음성 앞축 표준을 만드는 그룹 이름.

사용 라이브러리:
- libavcodec
- libavformat


---

### OpenC : library
- Open Source Computer Vision Library
- 컴퓨터가 카메라나 사진을 보고 이해하도록 도와주는 라이브러리

Python:
```python
import cv2

img = cv2.imread("robot_camera.jpg")
```

Keywords:
`OpenCV`, `cv2`, `cv_bridge`, `sensor_msgs/Image`

---

### OpenCV vs FFmpeg
- FFmpeg : 영상을 저장, 변환, 압축하는 데 강함
- OpenCV : 영상 안에 무엇이 있는지 처리, 분석하는 데 강함 

---

### SLERP : 계산 방법
- Spherical Linear Interpolation
- 구면 선형 보간
- 시작 회전과 목표 회전 사이의 중간 회전 자세를 부드럽게 계산하는 방법

사용 수학:
- 쿼터니언

Keywords:
`quaternion`, `tf2`, 로봇팔 trajectory

---

### PCA : 분석
- Principal Component Analysis
- 주성분 분석
    - "이 점들이 전체적으로 어느 방향으로 퍼져 있지?" 를 찾는 방법
    - 물체가 어느 방향으로 놓여 있는지, 데이터가 어느 축으로 많이 퍼져 있는지 등 

Before:
```
y
│
│        •
│      •
│    •
│  •
│•
└──────────── x
```

After PCA use:
```
        •
      •
    •     ↗  ← PCA가 찾은 주된 방향
  •
•
```

---

### Kabsch : Calculating Algorithm
- Kabsh alorithm
- "두 점 집합을 가장 잘 겹치게 하려면 얼마나 회전시켜야 하는지"

1st measure:
```
A:

•       •
    •

•
```
- scattered points

2nd measure:
```
B:

    •
       •
  •
       •
```
- 위치와 방향이 달라짐

Kabsch does:
- A -> B 가 되는 회전행렬 R을 찾는다.
- 위치 이동까지 맞출때: 각 점 집합의 중심을 빼서 -> 회전을 구한 뒤 -> translation $t$도 계산한다.

---

### PCA vs Kabsch

|          | PCA                  | Kabsch                    |
| -------- | -------------------- | ------------------------- |
| 질문       | 점들이 **어느 방향으로 퍼졌나?** | 두 점 집합을 **어떻게 회전하면 겹치나?** |
| 입력       | 보통 하나의 점 집합          | 대응되는 두 점 집합               |
| 주로 구하는 것 | 주성분/주축               | 회전 \(R\), 그리고 보통 이동 \(t\) |
| 로봇 예시    | 물체 방향 추정             | 두 자세의 포인트 정합              |

PCA : 점들의 구조/방향 파악
Kabsh : 두 점군 사이의 자세 변환 계산

Key terms:
LiDar → Point Cloud -> SLAM

Keyword:
SVD(특이값 분해)

---

### 01_pipeline.ipynb

#### pose_pipeline.py

2-1

-내가 짠 코드:
```python
    def __init__(self, T_base_link, T_link_camera, joint_axis: str = "z"):
        # TODO: 문제 2-1
        #   - 두 변환을 np.asarray(dtype=float) 로 받아 shape 가 (4,4) 인지 확인하고 (아니면 ValueError)
        #   - self._T_base_link0 (관절 각도 0 일 때의 기준값), self._T_link_camera 로 보관
        #   - self.joint_axis, self.joint_angle = 0.0 초기화
        T_base_link = np.asarray(T_base_link, dtype=float)
        T_link_camera = np.asarray(T_link_camera, dtype=float)

        if T_base_lilnk.shape != (4,4) or T_link_camera.shape != (4,4)
            raise ValueError(f'T_base_link 와 T_link_camera는 shape이 4x4이어야 합니다.')

        self._T_base_link = T_base_link
        self._T_link_camera = T_link_camera
        self.joint_axis, self.joint_angle = 0
```

수정 후:
```python
    def __init__(self, T_base_link, T_link_camera, joint_axis: str = "z"):
        # TODO: 문제 2-1
        #   - 두 변환을 np.asarray(dtype=float) 로 받아 shape 가 (4,4) 인지 확인하고 (아니면 ValueError)
        #   - self._T_base_link0 (관절 각도 0 일 때의 기준값), self._T_link_camera 로 보관
        #   - self.joint_axis, self.joint_angle = 0.0 초기화
        T_base_link = np.asarray(T_base_link, dtype=float)
        T_link_camera = np.asarray(T_link_camera, dtype=float)

        if T_base_link.shape != (4,4) or T_link_camera.shape != (4,4):
            raise ValueError(f'T_base_link 와 T_link_camera는 shape이 4x4이어야 합니다.')

        self._T_base_link = T_base_link
        self._T_link_camera = T_link_camera
        self.joint_axis = joint_axis
        self.joint_angle = 0.0
```
<br>

내가 짠 코드:
```python
@property
    def T_base_link(self) -> np.ndarray:
        """현재 관절 각도가 반영된 T(base <- link).

        관절이 link 의 joint_axis 둘레로 joint_angle 만큼 돈 것으로 본다:
            T_base_link = T_base_link0 @ make_T(R_axis(joint_angle), [0, 0, 0])
        """
        T_base_link = T_base_link0 @ make_T(_ROT[joint_axis](joint_angle), [0, 0, 0])
        
        return T_base_link
```

수정 후:
```python
    @property
    def T_base_link(self) -> np.ndarray:
        """현재 관절 각도가 반영된 T(base <- link).

        관절이 link 의 joint_axis 둘레로 joint_angle 만큼 돈 것으로 본다:
            T_base_link = T_base_link0 @ make_T(R_axis(joint_angle), [0, 0, 0])
        """
        R = _ROT[self.joint_axis][self.joint_angle]
        T_base_link = self.T_base_link0 @ make_T(_ROT, [0, 0, 0])
        
        return T_base_link
```

<br>

내가 짠 코드:
```python
    @property
    def T_link_camera(self) -> np.ndarray:
        """T(link <- camera) — 카메라는 link 에 고정돼 있으므로 관절과 무관하다."""
        self._T_link_camera = T_link_camera

        return T_link_camera
```

수정후:
```python
    @property
    def T_link_camera(self) -> np.ndarray:
        """T(link <- camera) — 카메라는 link 에 고정돼 있으므로 관절과 무관하다."""
        return self._T_link_camera
```
<br>

내가 짠 코드:
```python
    def set_joint_angle(self, theta: float) -> "PosePipeline":
        """관절 각도 [rad] 를 바꾼다. 메서드 체이닝을 위해 self 를 돌려준다."""
        return self.theta = np.degrees(theta)
```

수정후:
```python
    def set_joint_angle(self, theta: float) -> "PosePipeline":
        """관절 각도 [rad] 를 바꾼다. 메서드 체이닝을 위해 self 를 돌려준다."""
        self.joint_angle = theta
        return self
```

---

**평균이 0인 정규분포에서 3차원 점 `N_PTS`개를 무작위로 만드는 코드**야.

```python
rng.normal(평균, 표준편차, 결과_shape)
```

각 인수는 이렇게 해석해:

- `0.0`: x, y, z 모두 평균이 0
- `[0.06, 0.03, 0.01]`: x, y, z의 표준편차가 각각 0.06, 0.03, 0.01
- `(N_PTS, 3)`: 행마다 `[x, y, z]`인 점을 `N_PTS`개 생성

즉, **원점 주변에 x 방향으로 가장 넓고, z 방향으로 가장 얇게 퍼진 점군**이 만들어져.

표준편차는 값의 범위 제한은 아니야. 예를 들어 x 값이 `±0.06`을 벗어날 수도 있어.

---

<br>

내가 짠 코드:
```python
    @property
    def T_base_camera(self) -> np.ndarray:
        """합성 변환 T(base <- camera) = T_base_link @ T_link_camera."""
        T_base_camera = self.T_base_link @ self.T_link_camera
        return T_base_camera
```

수정후:
```python
def base_to_camera(self, P_base) -> np.ndarray:
    return transform_points(self.T_camera_base, P_base)
```

<br>

내가 짠 코드:
```python
    def camera_to_base(self, P_cam) -> np.ndarray:
        """카메라 기준 점군 (N,3) 또는 점 (3,) 을 base 기준으로 바꾼다.

        반복문을 쓰지 말고 모듈 ③ 의 `transform_points` 로 한 번에 변환한다.
        """
        camera_to_base = transform_points(T_camera_base,P_cam)
        return camera_to_base
```

수정후:
```python
def camera_to_base(self, P_cam) -> np.ndarray:
    return transform_points(self.T_base_camera, P_cam)
```

<br>

내가 짠 코드:
```python
# TODO: 아래 변수를 만드세요 -> pipe, P_base, P_back, P_loop
#   pipe   = PosePipeline(T_base_link, T_link_cam)
#   P_base = pipe.camera_to_base(P_cam)                 # (N,3) 한 번에
#   P_back = pipe.base_to_camera(P_base)                # 왕복
#   P_loop = np.array([...])                            # 비교용: 점 하나씩 반복문으로 변환한 결과
   pipe   = PosePipeline(T_base_link, T_link_cam)
   P_base = pipe.camera_to_base(P_cam)                 # (N,3) 한 번에
   P_back = pipe.base_to_camera(P_base)                # 왕복

for l in P_base:
    P_loop = np.array(inv_T(P_base[l]))
    return P_loop

# TODO: P_base[:3], 왕복 최대 오차 np.max(np.abs(P_back - P_cam)) 를 출력하세요.
for e in P_base:
    result = np.max(np.abs(P_back[e] - P_cam[e]))
    print(f'왕복 최대 오차는 약: {P_base[e]}')
```

수정후:
```python
# TODO: 아래 변수를 만드세요 -> pipe, P_base, P_back, P_loop
#   pipe   = PosePipeline(T_base_link, T_link_cam)
#   P_base = pipe.camera_to_base(P_cam)                 # (N,3) 한 번에
#   P_back = pipe.base_to_camera(P_base)                # 왕복
#   P_loop = np.array([...])                            # 비교용: 점 하나씩 반복문으로 변환한 결과
pipe   = PosePipeline(T_base_link, T_link_cam)
P_base = pipe.camera_to_base(P_cam)                 # (N,3) 한 번에
P_back = pipe.base_to_camera(P_base)                # 왕복

P_loop = []

for p in P_cam:
    P_loop.append(pipe.camera_to_base(p))
P_loop = np.array(P_loop)

# TODO: P_base[:3], 왕복 최대 오차 np.max(np.abs(P_back - P_cam)) 를 출력하세요.
print("왕복 점 첫 3개: ", P_base[:3])
print("왕복 최대 오차는 약: ", np.max(np.abs(P_back - P_cam)))
    
```
### 3-1

응. 로보틱스/회전행렬 문맥에서 말하는 거라면 **Shepperd 방법**은 보통 **Shepperd’s method(셰퍼드 방법)**를 말해.

쉽게 말하면,

> **회전행렬 \(R\)을 쿼터니언 \(q\)으로 변환하는 방법**이야.

예를 들어 회전행렬

$$
R=
\begin{bmatrix}
r_{11}&r_{12}&r_{13}\\
r_{21}&r_{22}&r_{23}\\
r_{31}&r_{32}&r_{33}
\end{bmatrix}
$$

이 있을 때 우리가 원하는 건

$$
q=
\begin{bmatrix}
q_w\\q_x\\q_y\\q_z
\end{bmatrix}
$$

이 쿼터니언이야.

### 왜 그냥 변환하지 않고 Shepperd 방법을 써?

회전행렬 → 쿼터니언 공식은 여러 가지가 있는데, 특정 회전각에서는 어떤 성분이 **0에 아주 가까워져서 나눗셈이 불안정**해질 수 있어.

Shepperd 방법은 \(R\)을 보고

$$
q_w^2,\quad q_x^2,\quad q_y^2,\quad q_z^2
$$

중에서 **가장 큰 값을 갖는 성분을 먼저 선택해서 계산**해.

예를 들어 후보는 대략

$$
q_w^2=\frac{1+r_{11}+r_{22}+r_{33}}{4}
$$

$$
q_x^2=\frac{1+r_{11}-r_{22}-r_{33}}{4}
$$

$$
q_y^2=\frac{1-r_{11}+r_{22}-r_{33}}{4}
$$

$$
q_z^2=\frac{1-r_{11}-r_{22}+r_{33}}{4}
$$

이렇게 구할 수 있어.

여기서 **가장 큰 성분을 기준으로 나머지를 계산**하는 거야.

그래서 핵심은:

**회전행렬 \(R\)**
→ **쿼터니언 4개 성분의 크기를 비교**
→ **가장 큰 성분 선택**
→ **그 성분을 기준으로 나머지 계산**
→ **수치적으로 안정적인 quaternion 획득**

즉 한 문장으로 기억하면:

> **Shepperd method = 회전행렬을 쿼터니언으로 안정적으로 변환하기 위해 가장 큰 쿼터니언 성분을 선택해서 계산하는 방법.**

지금 배우고 있는 **회전행렬 → quaternion** 과정에서 꽤 중요한 방법이야. 원하면 다음으로 **실제 숫자 \(3\times3\) 회전행렬 하나를 가지고 Shepperd 방법으로 \(q\)를 직접 계산하는 과정**까지 이어서 보여줄게.

응. 제일 계산하기 쉬운 예로 **\(z\)축으로 90° 회전한 회전행렬**을 Shepperd 방법으로 쿼터니언으로 바꿔볼게.

회전행렬은

$$
R=
\begin{bmatrix}
0 & -1 & 0\\
1 & 0 & 0\\
0 & 0 & 1
\end{bmatrix}
$$

이야.

Shepperd 방법에서는 먼저 각 쿼터니언 성분의 제곱값 후보를 계산해.

$$
q_w^2=\frac{1+r_{11}+r_{22}+r_{33}}{4}
$$

여기에 값을 넣으면

$$
q_w^2
=
\frac{1+0+0+1}{4}
=
\frac{2}{4}
=
0.5
$$

따라서

$$
q_w=\sqrt{0.5}
=\frac{\sqrt2}{2}
\approx0.7071
$$

다음은 \(q_x\):

$$
q_x^2
=
\frac{1+r_{11}-r_{22}-r_{33}}{4}
$$

$$
=
\frac{1+0-0-1}{4}=0
$$

그래서

$$
q_x=0
$$

\(q_y\)도 마찬가지야.

$$
q_y^2
=
\frac{1-r_{11}+r_{22}-r_{33}}{4}
$$

$$
=
\frac{1-0+0-1}{4}=0
$$

그래서

$$
q_y=0
$$

마지막으로 \(q_z\):

$$
q_z^2
=
\frac{1-r_{11}-r_{22}+r_{33}}{4}
$$

$$
=
\frac{1-0-0+1}{4}
=
0.5
$$

따라서 크기는

$$
|q_z|=0.7071
$$

그런데 여기서 중요한 게 있어. **제곱값만 계산하면 \(+\)인지 \(-\)인지 알 수 없어.**

그래서 회전행렬의 비대칭 성분을 이용해 부호를 결정해.

$$
q_z
=
\frac{r_{21}-r_{12}}{4q_w}
$$

우리 행렬에서는

$$
r_{21}=1,\qquad r_{12}=-1
$$

이니까

$$
q_z
=
\frac{1-(-1)}
{4(0.7071)}
$$

$$
=
\frac{2}{2.8284}
\approx0.7071
$$

따라서 최종 쿼터니언은

$$
\boxed{
q=
\begin{bmatrix}
0.7071\\
0\\
0\\
0.7071
\end{bmatrix}
}
$$

즉

$$
\boxed{
q=(w,x,y,z)
=(0.7071,0,0,0.7071)
}
$$

이야.

이게 우리가 원래 알고 있는 쿼터니언 공식하고도 정확히 일치해.

$$
q=
\left(
\cos\frac{\theta}{2},
\;
\mathbf{u}\sin\frac{\theta}{2}
\right)
$$

여기서는 \(z\)축 회전이므로

$$
\mathbf{u}=(0,0,1)
$$

이고

$$
\theta=90^\circ
$$

이니까

$$
q=
\left(
\cos45^\circ,
0,
0,
\sin45^\circ
\right)
$$

즉

$$
(0.7071,0,0,0.7071)
$$

이 되는 거지.

**Shepperd 방법의 진짜 핵심**은 이 예제처럼 그냥 네 값을 모두 계산하는 데 있는 게 아니라,

$$
q_w^2,\;q_x^2,\;q_y^2,\;q_z^2
$$

를 비교해서 **가장 큰 성분을 골라 먼저 계산하는 것**이야. 가장 큰 값을 분모로 사용하면 아주 작은 숫자로 나누는 상황을 피할 수 있어서 수치적으로 더 안정적이거든.

예를 들어

$$
[q_w^2,q_x^2,q_y^2,q_z^2]
=
[0.5,0,0,0.5]
$$

라면 \(q_w\) 또는 \(q_z\)가 큰 성분이니까 그걸 기준으로 계산하는 식이야.

이게 **“Shepperd method가 왜 필요한가”**의 핵심이야. 특히 **180° 근처 회전행렬**을 가지고 해보면 일반 공식이 왜 불안정하고 Shepperd가 왜 유리한지가 훨씬 확실하게 보여.

**Trace(R)**는 행렬 \(R\)의 **주대각선(main diagonal) 원소를 전부 더한 값**이야.

예를 들어

$$
R=
\begin{bmatrix}
r_{11}&r_{12}&r_{13}\\
r_{21}&r_{22}&r_{23}\\
r_{31}&r_{32}&r_{33}
\end{bmatrix}
$$

이면

$$
\boxed{\operatorname{Trace}(R)=r_{11}+r_{22}+r_{33}}
$$

아까 예제의

$$
R=
\begin{bmatrix}
0&-1&0\\
1&0&0\\
0&0&1
\end{bmatrix}
$$

에서는

$$
\operatorname{Trace}(R)=0+0+1=\boxed{1}
$$

이야.

### 회전행렬에서는 더 중요한 의미가 있어

3D 회전행렬에서는 Trace로 **회전각 \(\theta\)**를 알아낼 수 있어.

$$
\boxed{\operatorname{Trace}(R)=1+2\cos\theta}
$$

따라서

$$
\boxed{
\theta=
\cos^{-1}
\left(
\frac{\operatorname{Trace}(R)-1}{2}
\right)
}
$$

위 행렬에서는

$$
\cos\theta
=
\frac{1-1}{2}=0
$$

이므로

$$
\theta=90^\circ
$$

가 나와.

즉 지금 배우는 맥락에서는 **Trace = 대각선 합**이라고 먼저 기억하고, **회전행렬에서는 회전각을 알아내는 데 사용할 수 있다**까지 기억하면 돼.

---

#### 재 설명

맞아. 이번에는 “식을 대입하면 행렬이 된다”를 건너뛰지 않고, **quaternion 곱셈 정의부터 회전행렬의 각 원소가 만들어지는 과정**, 그리고 그것을 다시 quaternion으로 푸는 과정까지 전개할게.

여기서는 다음 규약을 고정한다.

\[
q=(w,x,y,z)
\]

- \(w\): 실수 부분
- \((x,y,z)\): 벡터 부분
- 열벡터 사용: \(\mathbf v'=R\mathbf v\)
- 오른손 좌표계
- \(q\)는 단위 quaternion:

\[
w^2+x^2+y^2+z^2=1
\]

---

# 1. Quaternion 곱셈부터 시작

Quaternion 하나를 다음처럼 쪼개서 표시하자.

\[
q=(a,\mathbf A)
\]

여기서 \(a\)는 실수이고 \(\mathbf A\)는 3차원 벡터다.

두 quaternion

\[
q_1=(a,\mathbf A),\qquad q_2=(b,\mathbf B)
\]

의 곱은 다음과 같이 정의된다.

\[
q_1q_2
=
\left(
ab-\mathbf A\cdot\mathbf B,\;
a\mathbf B+b\mathbf A+\mathbf A\times\mathbf B
\right)
\]

즉, 결과의 실수 부분은:

\[
ab-\mathbf A\cdot\mathbf B
\]

결과의 벡터 부분은:

\[
a\mathbf B+b\mathbf A+\mathbf A\times\mathbf B
\]

이다.

이 공식은 \(i^2=j^2=k^2=ijk=-1\)이라는 quaternion 곱셈 규칙을 정리한 것이다.

---

# 2. 회전시킬 벡터를 quaternion으로 바꾸기

회전시킬 벡터를:

\[
\mathbf v=(v_x,v_y,v_z)
\]

라고 하자.

이를 실수 부분이 0인 quaternion으로 표현한다.

\[
p=(0,\mathbf v)
\]

회전 quaternion은:

\[
q=(w,\mathbf u)
\]

라고 쓰자. 여기서:

\[
\mathbf u=(x,y,z)
\]

이다.

\(q\)가 단위 quaternion이면 역원은:

\[
q^{-1}=q^*=(w,-\mathbf u)
\]

이다.

벡터 회전은 다음 연산으로 정의한다.

\[
p'=qpq^{-1}
\]

이제 이 곱셈을 하나씩 직접 전개해보자.

---

# 3. 먼저 \(qp\)를 계산

\[
q=(w,\mathbf u)
\]

\[
p=(0,\mathbf v)
\]

quaternion 곱셈 공식에 넣으면:

\[
qp
=
(w,\mathbf u)(0,\mathbf v)
\]

실수 부분은:

\[
w\cdot0-\mathbf u\cdot\mathbf v
=
-\mathbf u\cdot\mathbf v
\]

벡터 부분은:

\[
w\mathbf v+0\mathbf u+\mathbf u\times\mathbf v
\]

따라서:

\[
qp=
\left(
-\mathbf u\cdot\mathbf v,\;
w\mathbf v+\mathbf u\times\mathbf v
\right)
\]

편의를 위해 다음처럼 놓자.

\[
a=-\mathbf u\cdot\mathbf v
\]

\[
\mathbf A=w\mathbf v+\mathbf u\times\mathbf v
\]

그러면:

\[
qp=(a,\mathbf A)
\]

이다.

---

# 4. 이제 \((qp)q^{-1}\)를 계산

\[
qp=(a,\mathbf A)
\]

이고:

\[
q^{-1}=(w,-\mathbf u)
\]

이므로:

\[
p'
=
(a,\mathbf A)(w,-\mathbf u)
\]

이다.

## 실수 부분

곱셈 공식에 따르면 실수 부분은:

\[
aw-\mathbf A\cdot(-\mathbf u)
\]

이다.

\(a\)와 \(\mathbf A\)를 다시 넣으면:

\[
(-\mathbf u\cdot\mathbf v)w
-
(w\mathbf v+\mathbf u\times\mathbf v)\cdot(-\mathbf u)
\]

마이너스를 정리하면:

\[
-w(\mathbf u\cdot\mathbf v)
+
(w\mathbf v+\mathbf u\times\mathbf v)\cdot\mathbf u
\]

내적을 분배하면:

\[
-w(\mathbf u\cdot\mathbf v)
+w(\mathbf v\cdot\mathbf u)
+(\mathbf u\times\mathbf v)\cdot\mathbf u
\]

내적은 순서를 바꿔도 같기 때문에:

\[
\mathbf u\cdot\mathbf v
=
\mathbf v\cdot\mathbf u
\]

앞의 두 항은 서로 소거된다.

\[
-w(\mathbf u\cdot\mathbf v)
+w(\mathbf u\cdot\mathbf v)=0
\]

또한 \(\mathbf u\times\mathbf v\)는 \(\mathbf u\)에 수직이므로:

\[
(\mathbf u\times\mathbf v)\cdot\mathbf u=0
\]

결국 실수 부분은 0이다.

\[
p'=(0,\mathbf v')
\]

즉, 회전 결과도 순수한 3차원 벡터로 남는다.

---

# 5. 회전 결과의 벡터 부분 계산

곱셈 공식에서 벡터 부분은:

\[
a(-\mathbf u)+w\mathbf A+\mathbf A\times(-\mathbf u)
\]

이다.

\(a=-\mathbf u\cdot\mathbf v\)와

\[
\mathbf A=w\mathbf v+\mathbf u\times\mathbf v
\]

를 대입하자.

\[
\begin{aligned}
\mathbf v'
={}&
(-\mathbf u\cdot\mathbf v)(-\mathbf u)\\
&+w(w\mathbf v+\mathbf u\times\mathbf v)\\
&+(w\mathbf v+\mathbf u\times\mathbf v)\times(-\mathbf u)
\end{aligned}
\]

각 항을 하나씩 계산한다.

첫 번째 항:

\[
(-\mathbf u\cdot\mathbf v)(-\mathbf u)
=
(\mathbf u\cdot\mathbf v)\mathbf u
\]

두 번째 항:

\[
w(w\mathbf v+\mathbf u\times\mathbf v)
=
w^2\mathbf v+w(\mathbf u\times\mathbf v)
\]

세 번째 항:

\[
(w\mathbf v+\mathbf u\times\mathbf v)\times(-\mathbf u)
\]

외적을 분배하면:

\[
(w\mathbf v)\times(-\mathbf u)
+
(\mathbf u\times\mathbf v)\times(-\mathbf u)
\]

첫 부분은:

\[
(w\mathbf v)\times(-\mathbf u)
=
-w(\mathbf v\times\mathbf u)
\]

외적은 순서를 바꾸면 부호가 바뀐다.

\[
\mathbf v\times\mathbf u
=
-\mathbf u\times\mathbf v
\]

따라서:

\[
-w(\mathbf v\times\mathbf u)
=
w(\mathbf u\times\mathbf v)
\]

두 번째 부분은:

\[
(\mathbf u\times\mathbf v)\times(-\mathbf u)
=
-(\mathbf u\times\mathbf v)\times\mathbf u
\]

벡터 삼중곱 공식:

\[
(\mathbf a\times\mathbf b)\times\mathbf c
=
\mathbf b(\mathbf a\cdot\mathbf c)
-
\mathbf a(\mathbf b\cdot\mathbf c)
\]

을 사용하면:

\[
(\mathbf u\times\mathbf v)\times\mathbf u
=
\mathbf v(\mathbf u\cdot\mathbf u)
-
\mathbf u(\mathbf v\cdot\mathbf u)
\]

따라서:

\[
-(\mathbf u\times\mathbf v)\times\mathbf u
=
-\|\mathbf u\|^2\mathbf v
+
(\mathbf u\cdot\mathbf v)\mathbf u
\]

모든 항을 모으면:

\[
\begin{aligned}
\mathbf v'
={}&
(\mathbf u\cdot\mathbf v)\mathbf u\\
&+w^2\mathbf v\\
&+w(\mathbf u\times\mathbf v)\\
&+w(\mathbf u\times\mathbf v)\\
&-\|\mathbf u\|^2\mathbf v\\
&+(\mathbf u\cdot\mathbf v)\mathbf u
\end{aligned}
\]

같은 항끼리 합치면:

\[
\boxed{
\mathbf v'
=
(w^2-\|\mathbf u\|^2)\mathbf v
+
2(\mathbf u\cdot\mathbf v)\mathbf u
+
2w(\mathbf u\times\mathbf v)
}
\]

이 식이 quaternion 회전을 행렬로 바꾸는 출발점이다.

---

# 6. 벡터식을 좌표별로 전개

다음과 같이 놓는다.

\[
\mathbf u=(x,y,z)
\]

\[
\mathbf v=(v_x,v_y,v_z)
\]

먼저 내적은:

\[
\mathbf u\cdot\mathbf v
=
xv_x+yv_y+zv_z
\]

외적은:

\[
\mathbf u\times\mathbf v
=
\begin{bmatrix}
yv_z-zv_y\\
zv_x-xv_z\\
xv_y-yv_x
\end{bmatrix}
\]

또한:

\[
\|\mathbf u\|^2=x^2+y^2+z^2
\]

회전식:

\[
\mathbf v'
=
(w^2-\|\mathbf u\|^2)\mathbf v
+
2(\mathbf u\cdot\mathbf v)\mathbf u
+
2w(\mathbf u\times\mathbf v)
\]

의 각 좌표를 계산해보자.

## \(v_x'\) 계산

첫 번째 항의 X 성분:

\[
(w^2-x^2-y^2-z^2)v_x
\]

두 번째 항의 X 성분:

\[
2x(xv_x+yv_y+zv_z)
\]

전개하면:

\[
2x^2v_x+2xyv_y+2xzv_z
\]

세 번째 항의 X 성분:

\[
2w(yv_z-zv_y)
\]

전개하면:

\[
2wyv_z-2wzv_y
\]

모두 더하면:

\[
\begin{aligned}
v_x'
={}&(w^2-x^2-y^2-z^2)v_x\\
&+2x^2v_x+2xyv_y+2xzv_z\\
&+2wyv_z-2wzv_y
\end{aligned}
\]

\(v_x,v_y,v_z\)별로 묶으면:

\[
\boxed{
v_x'
=
(w^2+x^2-y^2-z^2)v_x
+
2(xy-wz)v_y
+
2(xz+wy)v_z
}
\]

## \(v_y'\) 계산

같은 방식으로:

\[
\begin{aligned}
v_y'
={}&(w^2-x^2-y^2-z^2)v_y\\
&+2y(xv_x+yv_y+zv_z)\\
&+2w(zv_x-xv_z)
\end{aligned}
\]

전개하고 묶으면:

\[
\boxed{
v_y'
=
2(xy+wz)v_x
+
(w^2-x^2+y^2-z^2)v_y
+
2(yz-wx)v_z
}
\]

## \(v_z'\) 계산

\[
\begin{aligned}
v_z'
={}&(w^2-x^2-y^2-z^2)v_z\\
&+2z(xv_x+yv_y+zv_z)\\
&+2w(xv_y-yv_x)
\end{aligned}
\]

전개하고 묶으면:

\[
\boxed{
v_z'
=
2(xz-wy)v_x
+
2(yz+wx)v_y
+
(w^2-x^2-y^2+z^2)v_z
}
\]

---

# 7. 계수들을 모으면 회전행렬이 된다

지금 얻은 식은:

\[
\begin{bmatrix}
v_x'\\
v_y'\\
v_z'
\end{bmatrix}
=
R
\begin{bmatrix}
v_x\\
v_y\\
v_z
\end{bmatrix}
\]

형태다.

따라서 각 \(v_x,v_y,v_z\) 앞의 계수를 행렬에 넣으면:

\[
R=
\begin{bmatrix}
w^2+x^2-y^2-z^2
&
2(xy-wz)
&
2(xz+wy)
\\
2(xy+wz)
&
w^2-x^2+y^2-z^2
&
2(yz-wx)
\\
2(xz-wy)
&
2(yz+wx)
&
w^2-x^2-y^2+z^2
\end{bmatrix}
\]

unit quaternion이기 때문에:

\[
w^2+x^2+y^2+z^2=1
\]

예를 들어 첫 번째 대각 성분은:

\[
w^2+x^2-y^2-z^2
\]

인데:

\[
w^2+x^2=1-y^2-z^2
\]

이므로:

\[
w^2+x^2-y^2-z^2
=
1-2y^2-2z^2
\]

즉:

\[
R_{00}=1-2(y^2+z^2)
\]

다른 대각 성분도 같은 방식으로 바꾸면:

\[
\boxed{
R=
\begin{bmatrix}
1-2(y^2+z^2)
&
2(xy-wz)
&
2(xz+wy)
\\
2(xy+wz)
&
1-2(x^2+z^2)
&
2(yz-wx)
\\
2(xz-wy)
&
2(yz+wx)
&
1-2(x^2+y^2)
\end{bmatrix}
}
\]

여기까지가 `quaternion_to_matrix`의 완전한 유도다.

이제 이 식을 역으로 풀어서 `matrix_to_quaternion`을 만든다.

---

# 8. 행렬로부터 \(w^2\)를 구하기

대각 원소를 더한다.

\[
R_{00}+R_{11}+R_{22}
\]

각 항을 대입하면:

\[
\begin{aligned}
={}&(w^2+x^2-y^2-z^2)\\
&+(w^2-x^2+y^2-z^2)\\
&+(w^2-x^2-y^2+z^2)
\end{aligned}
\]

각 제곱항의 개수를 세면:

- \(w^2\): 세 번
- \(x^2\): \(+1-1-1=-1\)
- \(y^2\): \(-1+1-1=-1\)
- \(z^2\): \(-1-1+1=-1\)

따라서:

\[
R_{00}+R_{11}+R_{22}
=
3w^2-x^2-y^2-z^2
\]

unit quaternion 조건에서:

\[
x^2+y^2+z^2=1-w^2
\]

이므로:

\[
R_{00}+R_{11}+R_{22}
=
3w^2-(1-w^2)
\]

\[
=4w^2-1
\]

따라서:

\[
1+R_{00}+R_{11}+R_{22}=4w^2
\]

양변의 제곱근을 취하면:

\[
\sqrt{1+R_{00}+R_{11}+R_{22}}
=
2|w|
\]

그러므로:

\[
\boxed{
|w|
=
\frac12
\sqrt{1+R_{00}+R_{11}+R_{22}}
}
\]

정확히는 \(w\)가 아니라 \(|w|\)가 나온다. 제곱한 값 \(w^2\)에서는 원래 부호를 알 수 없기 때문이다.

구현에서는 둘 중 하나를 선택해서:

\[
w=
\frac12
\sqrt{1+R_{00}+R_{11}+R_{22}}
\]

로 둔다.

---

# 9. \(x,y,z\)의 부호와 값을 구하기

\(R_{21}\)과 \(R_{12}\)를 보자.

\[
R_{21}=2(yz+wx)
\]

\[
R_{12}=2(yz-wx)
\]

둘을 빼면:

\[
\begin{aligned}
R_{21}-R_{12}
&=2(yz+wx)-2(yz-wx)\\
&=2yz+2wx-2yz+2wx\\
&=4wx
\end{aligned}
\]

따라서 \(w\neq0\)이면:

\[
\boxed{
x=\frac{R_{21}-R_{12}}{4w}
}
\]

다음으로:

\[
R_{02}=2(xz+wy)
\]

\[
R_{20}=2(xz-wy)
\]

둘을 빼면:

\[
\begin{aligned}
R_{02}-R_{20}
&=2(xz+wy)-2(xz-wy)\\
&=2xz+2wy-2xz+2wy\\
&=4wy
\end{aligned}
\]

따라서:

\[
\boxed{
y=\frac{R_{02}-R_{20}}{4w}
}
\]

마지막으로:

\[
R_{10}=2(xy+wz)
\]

\[
R_{01}=2(xy-wz)
\]

둘을 빼면:

\[
\begin{aligned}
R_{10}-R_{01}
&=2(xy+wz)-2(xy-wz)\\
&=2xy+2wz-2xy+2wz\\
&=4wz
\end{aligned}
\]

따라서:

\[
\boxed{
z=\frac{R_{10}-R_{01}}{4w}
}
\]

그래서 \(w\)가 충분히 클 때 사용하는 공식은:

\[
\boxed{
\begin{aligned}
w&=\frac12\sqrt{1+R_{00}+R_{11}+R_{22}}\\
x&=\frac{R_{21}-R_{12}}{4w}\\
y&=\frac{R_{02}-R_{20}}{4w}\\
z&=\frac{R_{10}-R_{01}}{4w}
\end{aligned}
}
\]

이다.

---

# 10. \(180^\circ\) 회전에서는 이 공식이 깨진다

회전각이 \(180^\circ\)라면:

\[
w=\cos\frac{180^\circ}{2}
=\cos90^\circ
=0
\]

그러면:

\[
x=\frac{R_{21}-R_{12}}{4w}
\]

에서 0으로 나누게 된다.

그래서 실제 구현은 \(w\)만 계산하지 않고, \(x^2,y^2,z^2\)도 행렬의 대각 성분으로부터 계산한다.

---

# 11. \(x^2\) 공식 유도

다음 조합을 계산하자.

\[
1+R_{00}-R_{11}-R_{22}
\]

각 대각 성분을 대입한다.

\[
\begin{aligned}
={}&1+(w^2+x^2-y^2-z^2)\\
&-(w^2-x^2+y^2-z^2)\\
&-(w^2-x^2-y^2+z^2)
\end{aligned}
\]

괄호를 풀면:

\[
\begin{aligned}
={}&1+w^2+x^2-y^2-z^2\\
&-w^2+x^2-y^2+z^2\\
&-w^2+x^2+y^2-z^2
\end{aligned}
\]

정리하면:

\[
1-w^2+3x^2-y^2-z^2
\]

unit quaternion 조건에서:

\[
1-w^2=x^2+y^2+z^2
\]

이므로:

\[
\begin{aligned}
1-w^2+3x^2-y^2-z^2
&=(x^2+y^2+z^2)+3x^2-y^2-z^2\\
&=4x^2
\end{aligned}
\]

따라서:

\[
\boxed{
4x^2=1+R_{00}-R_{11}-R_{22}
}
\]

\[
\boxed{
|x|=
\frac12\sqrt{1+R_{00}-R_{11}-R_{22}}
}
\]

똑같은 방식으로:

\[
\boxed{
|y|=
\frac12\sqrt{1-R_{00}+R_{11}-R_{22}}
}
\]

\[
\boxed{
|z|=
\frac12\sqrt{1-R_{00}-R_{11}+R_{22}}
}
\]

를 얻는다.

결과적으로 행렬은 다음 네 값을 알려준다.

\[
\begin{aligned}
4w^2 &= 1+R_{00}+R_{11}+R_{22}\\
4x^2 &= 1+R_{00}-R_{11}-R_{22}\\
4y^2 &= 1-R_{00}+R_{11}-R_{22}\\
4z^2 &= 1-R_{00}-R_{11}+R_{22}
\end{aligned}
\]

---

# 12. 왜 가장 큰 성분을 선택하는가

예를 들어 \(w\)가 아주 작다고 해보자.

\[
w=0.000001
\]

그러면:

\[
x=\frac{R_{21}-R_{12}}{4w}
\]

에서 매우 작은 수로 나누게 된다. 행렬에 작은 오차가 있으면 그 오차가 크게 증폭된다.

반면 \(x\)가 크다면 \(x\)를 먼저 계산한 뒤 다른 성분을 \(x\)로 나누는 편이 안정적이다.

\(x\)를 먼저 구했다고 하자.

행렬 원소를 더하면:

\[
R_{21}-R_{12}=4wx
\]

\[
R_{01}+R_{10}=4xy
\]

\[
R_{02}+R_{20}=4xz
\]

따라서:

\[
\boxed{
\begin{aligned}
w&=\frac{R_{21}-R_{12}}{4x}\\
y&=\frac{R_{01}+R_{10}}{4x}\\
z&=\frac{R_{02}+R_{20}}{4x}
\end{aligned}
}
\]

이런 이유로 구현은 \(w,x,y,z\) 중 절댓값이 가장 큰 성분을 선택한다.

---

# 13. 코드의 `s`가 의미하는 것

예를 들어 `trace > 0`인 분기를 보자.

```python
s = 2 * sqrt(1 + trace)
w = 0.25 * s
x = (R[2][1] - R[1][2]) / s
y = (R[0][2] - R[2][0]) / s
z = (R[1][0] - R[0][1]) / s
```

앞에서:

\[
w=\frac12\sqrt{1+\operatorname{trace}(R)}
\]

였으므로:

\[
4w=2\sqrt{1+\operatorname{trace}(R)}
\]

이다.

코드의:

```python
s = 2 * sqrt(1 + trace)
```

는 바로:

\[
s=4w
\]

를 계산하는 것이다.

따라서:

```python
w = 0.25 * s
```

는:

\[
w=\frac{s}{4}
\]

이고:

```python
x = (R[2][1] - R[1][2]) / s
```

는:

\[
x=\frac{R_{21}-R_{12}}{4w}
\]

와 동일하다.

---

# 14. \(q\)와 \(-q\)가 생기는 이유도 행렬식에서 바로 보인다

회전행렬의 모든 원소를 다시 보자.

\[
R_{00}=w^2+x^2-y^2-z^2
\]

\[
R_{01}=2(xy-wz)
\]

\[
R_{02}=2(xz+wy)
\]

여기에:

\[
(w,x,y,z)\rightarrow(-w,-x,-y,-z)
\]

를 대입한다.

예를 들어:

\[
R_{01}'=2((-x)(-y)-(-w)(-z))
\]

마이너스끼리 곱하면 플러스가 되므로:

\[
R_{01}'=2(xy-wz)=R_{01}
\]

다른 모든 원소도 마찬가지다.

- \(w^2\rightarrow(-w)^2=w^2\)
- \(xy\rightarrow(-x)(-y)=xy\)
- \(wz\rightarrow(-w)(-z)=wz\)

행렬에는 quaternion 성분이 항상 **두 개씩 곱해진 형태**로만 나타난다. 그래서 전체 부호를 뒤집어도 행렬은 변하지 않는다.

즉, 행렬에서 quaternion을 역으로 구할 때:

\[
w^2
\]

는 알 수 있지만 \(w\)가 양수였는지 음수였는지는 알아낼 수 없다.

\[
w=\pm\sqrt{w^2}
\]

한쪽 부호를 선택하면 나머지 성분의 부호가 결정되고, 최종적으로 두 가능성이 남는다.

\[
q=(w,x,y,z)
\]

\[
-q=(-w,-x,-y,-z)
\]

둘은 정확히 같은 행렬을 만든다.

---

# 전체 유도의 핵심 연결

\[
p'=qpq^{-1}
\]

를 quaternion 곱셈 규칙으로 전개하면:

\[
\mathbf v'
=
(w^2-\|\mathbf u\|^2)\mathbf v
+
2(\mathbf u\cdot\mathbf v)\mathbf u
+
2w(\mathbf u\times\mathbf v)
\]

가 나온다.

이것을 \(v_x,v_y,v_z\)별로 전개하면:

\[
\mathbf v'=R\mathbf v
\]

형태의 회전행렬이 나온다.

그 행렬의:

- 대각 성분을 더하고 빼면 \(w^2,x^2,y^2,z^2\)
- 비대각 성분을 더하고 빼면 \(wx,wy,wz,xy,xz,yz\)

가 나온다.

그래서 행렬로부터 quaternion을 복원할 수 있다. 실제 구현의 여러 분기는 \(180^\circ\) 부근에서 0에 가까운 값으로 나누는 문제를 피하려는 것이다.

<br>

내가 짠 코드:
```python

```

수정후:
```python

```

<br>

내가 짠 코드:
```python

```

수정후:
```python

```

<br>

내가 짠 코드:
```python

```

수정후:
```python

```