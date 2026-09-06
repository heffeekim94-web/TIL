Date 2026 Sept Sunday

## coordinate_chain.py

### path to root

확인했어요. `_path_to_root()`는 작성되어 있고, 다음은 **`T_from_root()`** 차례예요.

먼저 `_path_to_root()`의 오타 하나를 고쳐 주세요.

```python
while frame != self.roo:
```

여기서 **`self.roo` → `self.root`**입니다.

이제 `T_from_root()`를 작성해 봐요.

**1. 이 함수는 무엇을 구할까요?**

```python
T_from_root("camera")
```

는 **camera 좌표를 root인 base 좌표로 바꾸는 행렬**을 구해요.

연결이 다음과 같다면:

```text
base → link → camera
```

필요한 계산은:

```text
T(base ← camera)
    = T(base ← link) @ T(link ← camera)
```

입니다. 오른쪽 변환부터 적용해서 **camera → link → base**로 이동하는 거예요.

**2. 앞에서 작성한 함수로 경로를 가져와요.**

```python
path = self._path_to_root(frame)
```

`frame = "camera"`라면:

```python
path = ["camera", "link", "base"]
```

가 됩니다.

**3. 누적할 행렬을 단위행렬로 시작해요.**

```python
result = np.eye(4)
```

숫자를 계속 곱할 때 초깃값을 `1`로 두듯, 행렬은 단위행렬로 시작해요.

**4. 경로에서 자식과 부모를 한 쌍씩 가져와요.**

```python
for i in range(len(path) - 1):
    child = path[i]
    parent = path[i + 1]
```

경로가 이름 3개라면 연결은 2개예요.

| `i` | `child` | `parent` |
|---|---|---|
| 0 | camera | link |
| 1 | link | base |

**5. 각 변환을 누적 행렬의 왼쪽에 곱해요.**

```python
result = self.get(parent, child) @ result
```

이미 작성된 `get()`은 등록한 `T(parent ← child)`를 가져오는 함수예요.

반복에 따른 변화는 다음과 같아요.

```text
시작:
result = I

첫 번째:
result = T(link ← camera) @ I

두 번째:
result = T(base ← link) @ T(link ← camera)
```

원하는 순서가 되었죠. **`result @ self.get(...)`로 쓰면 곱셈 순서가 반대가 되므로 주의하세요.**

전체 함수는 다음과 같아요. 클래스 안의 기존 `T_from_root()`를 이 코드로 작성하면 됩니다.

```python
    def T_from_root(self, frame: str) -> np.ndarray:
        """frame 좌표를 root 좌표로 바꾸는 변환을 구한다."""
        path = self._path_to_root(frame)
        result = np.eye(4)

        for i in range(len(path) - 1):
            child = path[i]
            parent = path[i + 1]

            result = self.get(parent, child) @ result

        return result
```

`frame`이 처음부터 `"base"`라면 경로는 `["base"]`예요. 반복은 실행되지 않고 단위행렬을 반환합니다. **같은 좌표계 사이에서는 좌표를 바꿀 필요가 없기 때문**이에요.

---

### T

다음은 **`T()` 함수**예요. 어떤 좌표계에서 다른 좌표계로 바꾸는 변환을 구합니다.

```python
def T(self, target: str, source: str) -> np.ndarray:
```

- `source`: 현재 좌표를 표현한 기준
- `target`: 좌표를 바꿔 표현할 기준

예를 들어 `T("base", "camera")`는 **camera 좌표 → base 좌표** 변환이에요.

**1. 두 좌표계에서 root로 가는 변환을 가져와요.**

방금 작성한 `T_from_root()`를 사용합니다.

```python
T_root_target = self.T_from_root(target)
T_root_source = self.T_from_root(source)
```

각각의 방향은:

```text
T_root_target : target → root
T_root_source : source → root
```

이에요.

**2. `target → root`를 뒤집어요.**

원하는 경로는 다음과 같아요.

```text
source → root → target
```

따라서 `target → root`의 역변환이 필요해요.

```python
inv_T(T_root_target)
```

이것은 **root → target** 변환입니다. 앞서 구현한 `inv_T()`를 그대로 사용해요.

**3. 두 변환을 순서대로 연결해요.**

행렬은 오른쪽부터 적용하므로:

```python
return inv_T(T_root_target) @ T_root_source
```

가 됩니다.

```text
            root → target       source → root
                  ↑                   ↑
            왼쪽 행렬             오른쪽 행렬
```

전체 코드는 짧아요. 클래스 안의 기존 `T()`를 다음처럼 작성하세요.

```python
    def T(self, target: str, source: str) -> np.ndarray:
        """source 좌표를 target 좌표로 바꾸는 변환을 구한다."""
        T_root_target = self.T_from_root(target)
        T_root_source = self.T_from_root(source)

        return inv_T(T_root_target) @ T_root_source
```

예를 들어:

```python
chain.T("link", "camera")
```

이면 **camera → base → link**로 연결해서, 최종적으로 camera 좌표를 link 기준으로 표현하는 변환을 얻어요. 파일은 수정하지 않았어요.

---

### transform

다음은 **`transform()`**이에요. 방금 만든 `T()`로 변환행렬을 구한 다음, **실제 점이나 방향에 적용하는 함수**입니다.

과제 조건은 다음과 같아요.

- 점 하나 `(3,)`와 여러 점 `(N, 3)` 모두 지원
- `w=1`이면 점, `w=0`이면 방향
- 반복문 사용 금지

현재 네 `transform_points()`는 `(N, 3)` 배열을 받도록 작성되어 있어요. 그래서 **점 하나가 들어오면 잠시 `(1, 3)`으로 바꿔서 재사용**하면 됩니다.

**1. 입력을 배열로 만들고 크기를 검사해요.**

```python
P = np.asarray(P, dtype=float)

if P.ndim == 1:
    if P.shape != (3,):
        raise ValueError("점 하나는 shape (3,)이어야 합니다.")
elif P.ndim == 2:
    if P.shape[1] != 3:
        raise ValueError("여러 점은 shape (N, 3)이어야 합니다.")
else:
    raise ValueError("입력은 shape (3,) 또는 (N, 3)이어야 합니다.")
```

`ndim`이 1이면 점 하나, 2이면 여러 점인지 확인하는 거예요.

**2. 점 하나였는지 기억해요.**

```python
single_point = P.ndim == 1
```

나중에 출력 모양을 원래대로 돌려놓기 위해 저장합니다.

**3. 항상 2차원 배열로 만들어 변환해요.**

```python
points = np.atleast_2d(P)
```

이 함수는:

```text
[1, 2, 3] → [[1, 2, 3]]
  (3,)         (1, 3)
```

처럼 바꿔요. 이미 `(N, 3)`이면 그대로 유지합니다.

```python
T_matrix = self.T(target, source)
result = transform_points(T_matrix, points, w=w)
```

`w`도 전달하므로 기존 함수가 **점에는 이동을 적용하고, 방향에는 회전만 적용**하게 됩니다.

**4. 원래 점 하나였다면 첫 행을 꺼내요.**

```python
if single_point:
    return result[0]

return result
```

`result[0]`은 `(1, 3)` 배열의 첫 행을 꺼내 `(3,)`으로 돌려줘요.

전체 코드는 다음과 같습니다.

```python
    def transform(self, target: str, source: str, P,
                  w: float = 1.0) -> np.ndarray:
        """source의 점 또는 방향을 target 좌표계로 변환한다."""
        P = np.asarray(P, dtype=float)

        if P.ndim == 1:
            if P.shape != (3,):
                raise ValueError("점 하나는 shape (3,)이어야 합니다.")
        elif P.ndim == 2:
            if P.shape[1] != 3:
                raise ValueError("여러 점은 shape (N, 3)이어야 합니다.")
        else:
            raise ValueError(
                "입력은 shape (3,) 또는 (N, 3)이어야 합니다."
            )

        single_point = P.ndim == 1
        points = np.atleast_2d(P)

        T_matrix = self.T(target, source)
        result = transform_points(T_matrix, points, w=w)

        if single_point:
            return result[0]

        return result
```

**변환 계산은 기존 `transform_points()`에 맡기고, 이 함수에서는 좌표계 선택과 입력·출력 모양을 처리**하는 구조예요.

---

### axis_angle

다음은 **`axis_angle()`**이에요. 두 좌표계 사이의 변환에서 **회전 부분만 꺼내서 회전축과 각도로 바꾸는 함수**입니다.

이미 작성한 함수들을 활용하면 세 줄로 만들 수 있어요.

**1. 두 좌표계 사이의 변환행렬을 구해요.**

```python
T_matrix = self.T(target, source)
```

이 행렬은 `source` 좌표를 `target` 좌표로 바꾸는 4×4 동차변환이에요.

```text
[r00  r01  r02 | tx]
[r10  r11  r12 | ty]
[r20  r21  r22 | tz]
[ 0    0    0  |  1]
```

**2. 왼쪽 위 3×3 회전행렬을 꺼내요.**

```python
R = T_matrix[:3, :3]
```

`[:3, :3]`은 **0~2번 행과 0~2번 열**을 선택한다는 뜻이에요. 이동 벡터는 제외됩니다.

**3. 앞서 구현한 축·각 복원 함수에 전달해요.**

```python
return axis_angle_from_matrix(R)
```

이 함수가 반환하는 `(axis, angle)` 두 값을 그대로 반환해요.

클래스 안의 기존 `axis_angle()`을 다음처럼 작성하면 됩니다.

```python
    def axis_angle(self, target: str, source: str):
        """두 좌표계 사이 회전의 축과 각도를 구한다."""
        T_matrix = self.T(target, source)
        R = T_matrix[:3, :3]

        return axis_angle_from_matrix(R)
```

사용할 때는:

```python
axis, angle = chain.axis_angle("base", "camera")
```

처럼 받아요. `axis`는 길이 1인 회전축, `angle`은 **라디안 각도**입니다.

---

다음은 **`default_chain()`**이에요. 과제에서 사용할 **base → link → camera 연결을 실제로 만드는 함수**입니다.

이번 함수는 **클래스 바깥**에 작성하므로 `def` 앞에 들여쓰기를 하지 않아요.

**1. base 기준 link의 자세를 만들어요.**

과제에서 지정한 값은:

- z축 회전: 30°
- 이동: `[0.30, 0.00, 0.40]`

회전 함수는 라디안을 받으므로 먼저 변환해요.

```python
R_base_link = rot_z(np.deg2rad(30))
T_base_link = make_T(R_base_link, [0.30, 0.00, 0.40])
```

`make_T()`는 회전행렬과 이동 벡터를 합쳐 4×4 동차변환을 만듭니다.

**2. link 기준 camera의 자세를 만들어요.**

과제에서 지정한 회전행렬의 곱은 다음과 같아요.

```python
R_link_camera = (
    rot_y(np.deg2rad(-20)) @ rot_x(np.deg2rad(90))
)
```

**열벡터에 적용할 때는 오른쪽의 x축 회전이 먼저 적용**돼요. 과제에 지정된 행렬 곱 순서 `rot_y(...) @ rot_x(...)`를 그대로 사용하면 됩니다.

이동도 합칩니다.

```python
T_link_camera = make_T(R_link_camera, [0.10, 0.05, 0.15])
```

**3. 좌표계 연결을 등록해요.**

```python
chain = CoordinateChain("base")
```

루트를 `"base"`로 하는 객체를 만들고:

```python
chain.add("base", "link", T_base_link)
chain.add("link", "camera", T_link_camera)
```

두 연결을 등록해요.

여기서 `add(parent, child, T)`에 넣는 행렬은 **child 좌표를 parent 좌표로 바꾸는 변환**입니다.

**4. 완성된 객체를 반환해요.**

```python
return chain
```

전체 코드는 다음과 같아요.

```python
def default_chain() -> CoordinateChain:
    """과제의 기본 좌표계 연결 base → link → camera를 만든다."""
    R_base_link = rot_z(np.deg2rad(30))
    T_base_link = make_T(
        R_base_link,
        [0.30, 0.00, 0.40],
    )

    R_link_camera = (
        rot_y(np.deg2rad(-20)) @ rot_x(np.deg2rad(90))
    )
    T_link_camera = make_T(
        R_link_camera,
        [0.10, 0.05, 0.15],
    )

    chain = CoordinateChain("base")
    chain.add("base", "link", T_base_link)
    chain.add("link", "camera", T_link_camera)

    return chain
```

이제 다음처럼 호출하면:

```python
chain = default_chain()
```

앞서 만든 `chain.T()`, `chain.transform()`, `chain.axis_angle()`을 사용할 준비가 된 거예요.

---

### camera point to base

좋아요. 다음부터는 **각 줄이 실행되면서 변수에 무엇이 들어가고, 어떤 함수로 넘어가는지** 함께 설명할게요.

이번 함수는 **`camera_point_to_base()`**예요. 카메라 기준으로 측정한 점을 base 기준 좌표로 바꿔 줍니다.

먼저 전체 코드는 짧아요. 이 함수도 **클래스 바깥**에 작성해요.

```python
def camera_point_to_base(
    p_cam,
    chain: CoordinateChain | None = None,
) -> np.ndarray:
    """카메라 기준 좌표를 base 기준 좌표로 변환한다."""
    if chain is None:
        chain = default_chain()

    return chain.transform("base", "camera", p_cam)
```

**1. 함수의 입력부터 볼게요.**

```python
p_cam
```

변환하려는 카메라 좌표예요. 점 하나 또는 여러 점을 전달할 수 있어요.

```python
# 점 하나: shape (3,)
p_cam = [0.0, 0.0, 0.0]

# 여러 점: shape (2, 3)
p_cam = [
    [0.0, 0.0, 0.0],
    [0.1, 0.0, 0.0],
]
```

카메라 기준 `[0, 0, 0]`은 **카메라 좌표계의 원점**이에요. base 기준 원점과 같다는 뜻은 아닙니다.

다음 매개변수는:

```python
chain: CoordinateChain | None = None
```

이렇게 읽으면 돼요.

- `chain`: 사용할 좌표계 연결 객체
- `CoordinateChain | None`: 객체 또는 `None`을 받는다는 타입 안내
- `= None`: 생략하면 기본값이 `None`

`None`은 여기서 **“사용할 좌표계 연결을 따로 전달하지 않았다”**는 의미로 사용해요.

**2. 연결 객체를 생략했는지 확인해요.**

```python
if chain is None:
    chain = default_chain()
```

예를 들어 이렇게 호출하면:

```python
result = camera_point_to_base([0.0, 0.0, 0.0])
```

함수에 들어왔을 때의 값은:

```text
p_cam = [0.0, 0.0, 0.0]
chain = None
```

따라서 `if` 안으로 들어가서 방금 작성한 `default_chain()`을 실행합니다.

그 결과 `chain`에는 다음 연결을 가진 객체가 들어가요.

```text
base → link → camera
```

반대로 직접 객체를 전달했다면:

```python
my_chain = default_chain()
result = camera_point_to_base([0.0, 0.0, 0.0], my_chain)
```

`chain`은 이미 객체이므로 `if`를 건너뛰고 **전달받은 객체를 사용**해요.

**3. 실제 좌표 변환을 요청해요.**

```python
return chain.transform("base", "camera", p_cam)
```

앞서 작성한 메서드의 인수 순서를 떠올려 보세요.

```python
transform(target, source, P, w=1.0)
```

이번 호출에서는:

| 매개변수 | 전달되는 값 | 의미 |
|---|---|---|
| `target` | `"base"` | 결과를 표현할 좌표계 |
| `source` | `"camera"` | 입력을 표현한 좌표계 |
| `P` | `p_cam` | 변환할 점 |
| `w` | 기본값 `1.0` | 방향이 아닌 점으로 처리 |

따라서 **회전과 이동을 모두 적용**해요.

**4. 실제 숫자로 따라가 볼게요.**

카메라 원점을 넣었다고 해볼게요.

```python
camera_point_to_base([0.0, 0.0, 0.0])
```

내부 계산은 다음 경로를 따릅니다.

```text
카메라 좌표 → link 좌표 → base 좌표
```

우선 카메라 원점을 link 기준으로 바꾸면:

```text
p_link = R_link_camera @ [0, 0, 0] + [0.10, 0.05, 0.15]
       = [0.10, 0.05, 0.15]
```

영벡터는 회전해도 영벡터이므로 이동 벡터만 남아요.

이어서 base 기준으로 바꾸면:

```text
p_base = rot_z(30°) @ [0.10, 0.05, 0.15]
         + [0.30, 0.00, 0.40]
```

각 성분을 계산하면:

```text
x = 0.10 × cos(3mk0°) - 0.05 × sin(30°) + 0.30
  ≈ 0.361603

y = 0.10 × sin(30°) + 0.05 × cos(30°)
  ≈ 0.093301

z = 0.15 + 0.40
  = 0.55
```

따라서 반환값은 대략:

```python
array([0.361603, 0.093301, 0.55])
```

예요. 이는 **카메라 원점이 base 기준으로 어디에 있는지** 나타냅니다.

이 함수 안에 행렬 계산 코드를 다시 쓰지 않아도 되는 이유는, **`chain.transform()`이 이미 그 계산을 담당하기 때문**이에요. 이번 함수는 사용할 체인을 준비하고, 변환 방향을 `"camera" → "base"`로 지정해 주는 역할입니다.

## notebooks 06

### 6-1 error

