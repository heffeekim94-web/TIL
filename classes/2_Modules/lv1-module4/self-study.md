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