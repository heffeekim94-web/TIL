Date 2026 Sept 05

수정했고, **`tests/test_rotation.py`의 93개 테스트가 모두 통과했어요.**

[src/rotation.py](C:/Users/haemi/git/physicalai-lv1-HaeminKim/lv1_module3_student/src/rotation.py)에서:

- `np.ndarray`를 데이터 변환용 `np.asarray`로 수정했어요.
- 행렬 크기를 `(3, 3)`으로 검사하도록 고쳤어요.
- 원소 접근을 `R[행, 열]`로 바꾸고, `v`의 인덱스·쉼표·`dtype=float` 문법을 수정했어요.
- 각도를 **라디안**으로 유지하고, 단위 회전축을 계산하도록 고쳤어요.
- 0과 π 근처의 각도에서도 안정적으로 복원하도록 처리했어요.

[tests/test_rotation.py](C:/Users/haemi/git/physicalai-lv1-HaeminKim/lv1_module3_student/tests/test_rotation.py)에서:

- Rodrigues 테스트에 각도 값을 전달하는 `parametrize`를 추가했어요.
- 왕복 테스트는 **복원한 회전행렬이 원본과 같은지** 비교하도록 수정했어요.
- 음수 각도, 0, π와 그 근처 값도 검증했어요.

---

### inverse_gauss_jordan

내 코딩
```python
def inverse_gauss_jordan(A):
    A = np.array(A, dtype=float, copy=True)
    u, pivots, swaps = row_echelon(A)
    m = A.shape[0]
    n = A.shape[1]
    row = 0
       for c in range(n):
           if A[r,c] != 0:
               row += 1
           if c == m:
               break
       if r == m:
           break
```

정정 후 
```python
def inverse_gauss_jordan(A):
    A = np.array(A, dtype=float, copy=True)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("정사각행렬이어야 합니다.")

    n = A.shape[0]

    # [A | I] 형태의 확장행렬 만들기
    augmented = np.hstack([A, np.eye(n)])

    for col in range(n):
        # 현재 행부터 아래에서 절댓값이 가장 큰 피벗 선택
        pivot_row = col + np.argmax(np.abs(augmented[col:, col]))

        if augmented[pivot_row, col] == 0:
            raise ValueError("역행렬이 없는 행렬입니다.")

        # 피벗 행을 현재 행으로 이동
        augmented[[col, pivot_row]] = augmented[[pivot_row, col]]

        # 피벗 행 전체를 나눠서 피벗을 1로 만들기
        pivot = augmented[col, col]
        augmented[col] /= pivot

        # 피벗을 제외한 같은 열의 모든 원소를 0으로 만들기
        for row in range(n):
            if row == col:
                continue

            factor = augmented[row, col]
            augmented[row] -= factor * augmented[col]

    # [I | A⁻¹]에서 오른쪽 절반 반환
    return augmented[:, n:]
```

---

### axis_angle_from_matrix

내 코딩:
```python
def axis_angle_from_matrix(R, atol: float = 1e-8):
    """고유값 분해로 회전축을, 대각합으로 회전각을 복원한다."""
    R = np.ndarray(R, dtype=float)

    if R.shape != 3:
        raise ValueError("회전행렬의 형태는 3x3이어야 합니다.")
    
    #고유값, 고유벡터
    eig, eig_v = np.linalg.eig(R)
    
    # 각도 구하기
    traceR = np.sum(R(1,1),R(2,2),R(3,3))
    theta = np.degrees(np.arccos((traceR-1) / 2))
    # rad값으로 반환해야 함. (0, π)

    # 단위 회전축 구하기
    v = np.array([
        [R(3,2)-R(2,3)]
        [R(1,3)-R(2,1)]
        [R(2,1)-R(1,2)], dtype:=float
    ])
    k = (1/2*np.sin(theta))*v

    return k, theta
```

정정 후:
```python
def axis_angle_from_matrix(R, atol: float = 1e-8):
    """고유값 분해로 회전축을, 대각합으로 회전각을 복원한다."""
    R = np.array(R, dtype=float)
    # 다시 array로 재 생성하는 것.
    if R.shape != (3, 3):
        # 3x3 행렬이어야 하기 때문
        raise ValueError("회전행렬의 형태는 3x3이어야 합니다.")
    

    # 각도 구하기
    # 대각 합:
    traceR = R[0,0] + R[1,1] + R[2,2]
    # np.sum()은 다르게 적용 됨
    cos_theta = np.clip((traceR - 1) / 2, -1.0, 1.0)
    theta = float(np.arccos(cos_theta))
    
        if theta <= atol:
        # 회전이 없으면 축이 유일하지 않으므로 +x축으로 정한다.
            return np.array([1.0, 0.0, 0.0]), 0.0

        #고유값, 고유벡터
        eig, eig_v = np.linalg.eig(R)

        idx = np.argmin(np.abs(eig-1))

        # 단위 회전축 구하기
        k = eig_v[:, idx].real
        k = k / np.linalg.norm(k)
        
        v = np.array([
            [R[2,1]-R[1,2]],
            [R[0,2]-R[2,0]],
            [R[1,0]-R[0,1]],
        ], dtype=float)

        if np.pi - theta <= atol:
        idx = np.argmax(np.abs(k))

            if k[idx] < 0:
                k = -k

            return k, float(np.pi)
    
    if k @ v < 0:
    k = -k

    return k, theta
```

---

### quaternion_from_axis_angle

코드 설명 및 사용:
```python
def quaternion_from_axis_angle(axis, angle: float) ->np.ndarray:
    """축-각에서 단위 쿼터니언을 만든다."""
    # k 는 단위 회전축
    # theta는 라디안 각도
    # \(q=(k_x\sin(\theta/2),\;k_y\sin(\theta/2),\;k_z\sin(\theta/2),\;\cos(\theta/2))\) 해당 식을 적용할 예정

    # 입력된 축을 numpy 배열로 바꾼다.
    # 실수형
    axis = np.array(axis, dtype=float)

    #축은 x,y,z 성분을 가진 벡터이므로 (3,) 인지 확인한다.
    # [x ...]
    # [y ...]
    # [z ...] ?
    if axis.shape != (3,):
        raise ValueError("회전축은 원소가 3개인 벡터여야 합니다.")

    #축의 길이를 구하고, 단위벡터로 만든다.
    length = np.linalg.norm(axis)

    # 길이가 0이면 벡터도 0, 즉 회전축은 0일 수 없음.
    if length == 0:
        raise ValueError("회전축은 영벡터일 수 없습니다.")

    # 단위 회전축을 구하기 위해 길이로 나눈다.
    k = aixs / length

    # 쿼터니언 공식에 들어갈 theta/2를 준비한다
    half_angle = angle / 2
    s = np.sin(half_angle)
    w = np.cos(half_angle)

    xyz = k * s

    # 쿼터니언 벡터대로 입력한다.
    return np.array([xyz[0], xyz[1], xyz[2], w])
```

## test_transform.py

그럼 `test_transform.py`의 **첫 번째 TODO인 `test_inv_T_gives_identity`부터** 볼게요. 파일은 수정하지 않을게요.

현재 과제는 다음 두 식이 성립하는지 검사하는 거예요.

\[
T^{-1}T=I_4,\qquad TT^{-1}=I_4
\]

**1. 함수 인수 `T`는 위의 fixture가 만들어 줘요.**

파일에 이미 이 코드가 있어요.

```python
@pytest.fixture
def T():
    """테스트에 쓸 대표 동차변환 하나."""
    R = rot_z(0.9) @ rot_y(-0.35) @ rot_x(1.3)
    return make_T(R, [0.35, -0.15, 0.55])
```

회전과 이동을 조합한 4×4 동차변환을 만드는 코드예요. pytest는 테스트 함수의 인수 이름이 `T`이면 이 fixture를 실행해서 결과를 전달해 줍니다.

```python
def test_inv_T_gives_identity(T):
```

따라서 테스트 안에서 `T`를 다시 만들 필요가 없어요.

**2. 네가 구현한 함수로 역변환을 구해요.**

```python
T_inv = inv_T(T)
```

여기서는 **`inv_T`가 제대로 작동하는지** 검사하므로 `np.linalg.inv`로 대신 계산하면 안 돼요.

**3. 비교할 4×4 단위행렬을 만들어요.**

```python
identity = np.eye(4)
```

```text
[1  0  0  0]
[0  1  0  0]
[0  0  1  0]
[0  0  0  1]
```

**4. 두 곱셈 순서를 각각 검사해요.**

```python
assert np.allclose(T_inv @ T, identity), "inv_T(T) @ T가 단위행렬이 아닙니다."
assert np.allclose(T @ T_inv, identity), "T @ inv_T(T)가 단위행렬이 아닙니다."
```

- `@`: 행렬 곱셈
- `np.allclose`: 대응하는 모든 원소가 오차 범위 안에서 같은지 검사
- `assert`: 결과가 `False`이면 테스트를 실패시키고 메시지를 표시

실수 계산에서는 0이어야 할 값이 `0.0000000000000001`처럼 나올 수 있으므로 `==` 대신 `np.allclose`를 사용해요.

첫 번째 TODO를 대체할 코드는 다음과 같습니다.

```python
def test_inv_T_gives_identity(T):
    T_inv = inv_T(T)
    identity = np.eye(4)

    assert np.allclose(T_inv @ T, identity), \
        "inv_T(T) @ T가 단위행렬이 아닙니다."

    assert np.allclose(T @ T_inv, identity), \
        "T @ inv_T(T)가 단위행렬이 아닙니다."
```

이 테스트는 **변환과 역변환을 연달아 적용하면 원래 상태로 돌아오는지** 확인하는 거예요.

---

다음은 **`test_inv_T_matches_generic_inverse`**예요.

앞의 테스트는 곱셈 결과가 단위행렬인지 확인했죠. 이번에는 **직접 구현한 `inv_T(T)`의 결과를 NumPy가 계산한 역행렬과 비교**해요.

**1. 직접 구현한 함수의 결과를 구해요.**

```python
T_inv = inv_T(T)
```

`T`는 앞에서와 같이 pytest가 fixture에서 전달해 줍니다.

**2. NumPy로 비교할 정답을 구해요.**

```python
expected = np.linalg.inv(T)  # 검산용
```

`np.linalg.inv`는 일반적인 정사각행렬의 역행렬을 계산해요. 과제에서 허용한 **검산 용도**로 사용하는 거예요.

**3. 두 행렬을 비교해요.**

```python
assert np.allclose(T_inv, expected), \
    "inv_T 결과가 NumPy 역행렬과 일치하지 않습니다."
```

두 행렬의 대응하는 원소들이 오차 범위 안에서 모두 같으면 통과합니다.

따라서 두 번째 TODO는 이렇게 작성하면 돼요.

```python
def test_inv_T_matches_generic_inverse(T):
    T_inv = inv_T(T)
    expected = np.linalg.inv(T)  # 검산용

    assert np.allclose(T_inv, expected), \
        "inv_T 결과가 NumPy 역행렬과 일치하지 않습니다."
```

여기서는 `T_inv @ expected`처럼 곱하지 않아요. **두 함수가 같은 역행렬을 반환했는지** 확인하는 것이므로 결과를 직접 비교합니다.

---

다음은 **`test_point_and_direction_differ`**예요. 같은 벡터를 **점으로 변환할 때와 방향으로 변환할 때의 차이**를 검사합니다.

동차변환이 회전 `R`과 이동 `t`로 구성되어 있다면:

\[
\text{점}: Rp+t,\qquad \text{방향}: Rv
\]

점은 위치를 가지므로 이동의 영향을 받아요. 방향은 이동의 영향을 받지 않고 회전만 합니다.

**1. 두 변환에 사용할 같은 벡터를 만들어요.**

```python
v = np.array([1.0, 2.0, 3.0])
```

**2. 점과 방향으로 각각 변환해요.**

```python
point_result = transform_point(T, v)
direction_result = transform_direction(T, v)
```

**3. 두 결과가 다른지 확인해요.**

```python
assert not np.allclose(point_result, direction_result), \
    "이동이 있는 변환에서 점과 방향의 결과가 같습니다."
```

파일의 `T` fixture에는 0이 아닌 이동이 포함되어 있으므로 두 결과가 달라야 해요.

**4. 두 결과의 차이가 이동 벡터인지 확인해요.**

같은 벡터를 사용했으므로 회전 부분이 서로 상쇄됩니다.

\[
(Rv+t)-Rv=t
\]

동차변환의 이동 벡터는 **마지막 열의 위쪽 세 원소**예요.

```python
translation = T[:3, 3]
```

`[:3, 3]`은 **0~2번 행, 3번 열**을 가져옵니다.

```python
assert np.allclose(point_result - direction_result, translation), \
    "점과 방향의 변환 결과 차이가 이동 벡터와 다릅니다."
```

**5. 방향 벡터의 길이가 유지되는지 확인해요.**

회전은 방향을 바꾸지만 길이는 보존해요.

```python
assert np.isclose(
    np.linalg.norm(direction_result),
    np.linalg.norm(v),
), "방향 변환 후 벡터의 길이가 달라졌습니다."
```

벡터끼리 비교할 때는 `np.allclose`, 길이처럼 숫자 하나끼리 비교할 때는 `np.isclose`를 사용했어요.

전체 코드는 다음과 같습니다.

```python
def test_point_and_direction_differ(T):
    v = np.array([1.0, 2.0, 3.0])

    point_result = transform_point(T, v)
    direction_result = transform_direction(T, v)

    assert not np.allclose(point_result, direction_result), \
        "이동이 있는 변환에서 점과 방향의 결과가 같습니다."

    translation = T[:3, 3]

    assert np.allclose(point_result - direction_result, translation), \
        "점과 방향의 변환 결과 차이가 이동 벡터와 다릅니다."

    # np.linalg.norm은 길이 보존을 검산하는 용도
    assert np.isclose(
        np.linalg.norm(direction_result),
        np.linalg.norm(v),
    ), "방향 변환 후 벡터의 길이가 달라졌습니다."
```

이 테스트는 **결과가 다름 → 차이는 이동 벡터 → 방향의 길이는 보존됨**이라는 세 조건을 확인해요.

---

다음은 **`test_transform_points_is_vectorized`**예요.

여러 점을 `transform_points`로 **한 번에 변환한 결과**가, `transform_point`로 **하나씩 변환한 결과**와 같은지 검사합니다.

**1. 테스트할 점들을 만들어요.**

```python
points = np.array([
    [0.0, 0.0, 0.0],
    [1.0, 2.0, 3.0],
    [-2.0, 0.5, 1.0],
    [0.3, -1.0, 2.0],
])
```

각 행이 하나의 점이에요. 점 4개에 좌표가 각각 3개이므로 `points.shape`은 `(4, 3)`입니다.

**2. 모든 점을 한 번에 변환해요.**

```python
actual = transform_points(T, points)
```

이번에 검사하려는 함수의 결과예요.

**3. 같은 점들을 하나씩 변환해서 비교 기준을 만들어요.**

```python
expected = np.array([
    transform_point(T, point)
    for point in points
])
```

이 문법은 다음 반복문을 짧게 쓴 거예요.

```python
results = []

for point in points:
    results.append(transform_point(T, point))

expected = np.array(results)
```

`point`에는 `points`의 각 행이 순서대로 들어갑니다.

**4. 결과의 크기와 값을 확인해요.**

```python
assert actual.shape == points.shape, \
    "변환 결과의 형태가 (N, 3)이 아닙니다."

assert np.allclose(actual, expected), \
    "일괄 변환 결과가 개별 변환 결과와 다릅니다."
```

크기를 먼저 확인하면, NumPy가 서로 다른 크기의 배열을 자동으로 맞춰 비교하는 **브로드캐스팅** 때문에 잘못 통과하는 것을 막을 수 있어요.

전체 코드는 다음과 같습니다.

```python
def test_transform_points_is_vectorized(T):
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 2.0, 3.0],
        [-2.0, 0.5, 1.0],
        [0.3, -1.0, 2.0],
    ])

    actual = transform_points(T, points)

    expected = np.array([
        transform_point(T, point)
        for point in points
    ])

    assert actual.shape == points.shape, \
        "변환 결과의 형태가 (N, 3)이 아닙니다."

    assert np.allclose(actual, expected), \
        "일괄 변환 결과가 개별 변환 결과와 다릅니다."
```

이 테스트는 **여러 점을 입력받아 올바른 결과를 반환하는지** 확인해요. 함수 내부에서 실제로 반복문 없이 계산하는지나 실행 속도까지 검사하지는 않습니다.

---

다음은 **`test_roundtrip_through_inverse`**예요.

점들을 `T`로 변환한 뒤 **역변환 `inv_T(T)`로 되돌리면 원래 좌표가 나오는지** 확인합니다.

\[
p' = Tp,\qquad T^{-1}p' = p
\]

위 식은 동차좌표로 표현한 원리이고, 코드에서는 `(N, 3)` 점 배열을 함수에 전달하면 돼요.

**1. 원본 점들을 준비해요.**

```python
points = np.array([
    [0.0, 0.0, 0.0],
    [1.0, 2.0, 3.0],
    [-2.0, 0.5, 1.0],
    [0.3, -1.0, 2.0],
])
```

**2. `T`로 변환해요.**

```python
transformed = transform_points(T, points)
```

`transformed`에는 회전과 이동이 적용된 좌표가 들어가요.

**3. 역변환을 구하고, 변환된 점들을 되돌려요.**

```python
T_inv = inv_T(T)
restored = transform_points(T_inv, transformed)
```

여기서 두 번째 인수는 원본 `points`가 아니라 **이미 변환한 `transformed`**여야 해요.

**4. 원본과 비교해요.**

```python
assert restored.shape == points.shape, \
    "복원된 점군의 형태가 원본과 다릅니다."

assert np.allclose(restored, points), \
    "변환 후 역변환한 점들이 원본과 다릅니다."
```

전체 코드는 다음과 같아요.

```python
def test_roundtrip_through_inverse(T):
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 2.0, 3.0],
        [-2.0, 0.5, 1.0],
        [0.3, -1.0, 2.0],
    ])

    transformed = transform_points(T, points)

    T_inv = inv_T(T)
    restored = transform_points(T_inv, transformed)

    assert restored.shape == points.shape, \
        "복원된 점군의 형태가 원본과 다릅니다."

    assert np.allclose(restored, points), \
        "변환 후 역변환한 점들이 원본과 다릅니다."
```

앞의 단위행렬 테스트가 **변환행렬끼리 곱해서** 확인했다면, 이번에는 **실제 점들에 적용해서 원래 위치로 돌아오는지** 확인하는 거예요.

---

마지막은 **`test_least_squares_matches_lstsq`**예요. 두 가지를 검사합니다.

1. 직접 구현한 최소자승 해가 NumPy의 결과와 같은가?
2. 잔차가 `A`의 모든 열벡터와 수직인가?

**1. 재현 가능한 난수를 준비해요.**

```python
rng = np.random.default_rng(42)
```

시드를 고정하면 실행할 때마다 같은 데이터를 사용해서 오류를 재현하기 쉬워요.

**2. 미지수보다 방정식이 많은 문제를 만들어요.**

```python
A = rng.normal(size=(8, 3))
x_true = np.array([1.0, -2.0, 0.5])
```

`A`는 8행 3열이므로 **방정식 8개, 미지수 3개**인 과결정 문제예요.

```python
noise = rng.normal(scale=0.01, size=8)
b = A @ x_true + noise
```

잡음이 없으면 `x_true`가 정확한 해예요. 잡음을 더하면 보통 모든 식을 동시에 만족시킬 수 없어서, **오차의 제곱합을 최소화하는 해**를 찾아야 합니다.

**3. 직접 구현한 함수로 해를 구해요.**

```python
actual = least_squares_normal_equation(A, b)
```

이 함수가 정규방정식

\[
A^T A x = A^T b
\]

을 이용해 구한 결과를 검사할 거예요.

**4. NumPy 결과와 비교해요.**

```python
expected, _, _, _ = np.linalg.lstsq(A, b, rcond=None)  # 검산용
```

`np.linalg.lstsq`는 결과 네 개를 반환해요. 첫 번째가 해이고, 이번에 사용하지 않는 나머지는 `_`로 받아요.

```python
assert np.allclose(actual, expected), \
    "최소자승 해가 NumPy 결과와 다릅니다."
```

여기서는 잡음이 있으므로 `x_true`와 정확히 같은지 검사하지 않아요. **같은 잡음 데이터를 풀어 얻은 NumPy 해**와 비교해야 합니다.

**5. 잔차가 A의 열벡터들과 수직인지 확인해요.**

잔차를 다음처럼 정의할게요.

```python
residual = b - A @ actual
```

최소자승 해에서는 다음 조건이 성립해요.

\[
A^T r = 0
\]

`A.T @ residual`의 각 원소는 **A의 각 열벡터와 잔차의 내적**이에요. 모두 0에 가까우면 수직이라는 뜻입니다.

```python
assert np.allclose(A.T @ residual, np.zeros(3), atol=1e-8), \
    "잔차가 A의 열공간에 수직이 아닙니다."
```

전체 코드는 다음과 같아요.

```python
def test_least_squares_matches_lstsq():
    rng = np.random.default_rng(42)

    # 방정식 8개, 미지수 3개인 과결정 문제
    A = rng.normal(size=(8, 3))
    x_true = np.array([1.0, -2.0, 0.5])

    # 정확한 관측값에 작은 잡음 추가
    noise = rng.normal(scale=0.01, size=8)
    b = A @ x_true + noise

    actual = least_squares_normal_equation(A, b)

    # np.linalg는 검산용
    expected, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

    assert actual.shape == expected.shape, \
        "최소자승 해의 형태가 올바르지 않습니다."

    assert np.allclose(actual, expected), \
        "최소자승 해가 NumPy 결과와 다릅니다."

    residual = b - A @ actual

    assert np.allclose(
        A.T @ residual,
        np.zeros(A.shape[1]),
        atol=1e-8,
    ), "잔차가 A의 열공간에 수직이 아닙니다."
```

**잔차 자체가 0일 필요는 없어요.** 잡음 때문에 오차가 남더라도, 최소자승 해에서는 그 잔차가 `A`의 열공간에 수직이어야 합니다.

---

error msg:
```ipynb
0m? **\<frozen importlib.\_bootstrap>**:935: in \_load\_unlocked     ??? **..\pose\_lab\Lib\site-packages\\\_pytest\assertion\rewrite.py**:179: in exec\_module     source\_stat, co = \_rewrite\_test(fn, self.config)                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ **..\pose\_lab\Lib\site-packages\\\_pytest\assertion\rewrite.py**:348: in \_rewrite\_test     tree = ast.parse(source, filename=strfn)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ **..\\..\\..\AppData\Local\Programs\Python\Python312\Lib\ast.py**:52: in parse     return compile(source, filename, mode, flags, **E     File "C:\Users\haemi\git\physicalai-lv1-HaeminKim\lv1\_module3\_student\tests\test\_transform.py", line 58** **E       assert np.isclose(np.linalg.norm(direction\_result)), np.linalg.norm(v), "방향 변환 후 벡터의 길이가 달라졌습니다."** **E                                                                             ^** **E   SyntaxError: invalid syntax** **=========================== short test summary info ===========================** ERROR tests/test\_transform.py !!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!! **1 error** in 0.68s  복구 후 종료 코드 : 2

이런 오류코드가 .ipynb에서 떴는데 뭐때문인거야
```

**`test_transform.py` 58번째 줄에서 괄호가 너무 일찍 닫혀서 발생한 문법 오류**예요. 노트북이나 커널 문제는 아닙니다.

현재 코드:
```python
assert np.isclose(np.linalg.norm(direction_result)), np.linalg.norm(v), "방향 변환 후 벡터의 길이가 달라졌습니다."
```

`np.isclose` 안에 **비교할 두 값**이 모두 들어가야 하는데, 첫 번째 값 뒤에서 닫혔어요.

이렇게 고치면 됩니다.

```python
assert np.isclose(
    np.linalg.norm(direction_result),
    np.linalg.norm(v),
), "방향 변환 후 벡터의 길이가 달라졌습니다."
```

구조는 다음과 같아요.

```python
assert np.isclose(변환_후_길이, 원래_길이), "실패 메시지"
```

pytest가 테스트 파일을 읽다가 문법 오류를 만나서 **테스트 실행 전에 중단된 상태**예요. 해당 줄을 수정하고 **저장한 뒤 노트북의 테스트 셀을 다시 실행**하세요.

---

error msg:
```
d_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\pose_lab\Lib\site-packages\_pytest\assertion\rewrite.py:179: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\pose_lab\Lib\site-packages\_pytest\assertion\rewrite.py:348: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\ast.py:52: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\haemi\git\physicalai-lv1-HaeminKim\lv1_module3_student\tests\test_transform.py", line 97
E       assert restored.shape == points, shape, "복원된 점군의 형태가 원본과 다릅니다."
E                                             ^
E   SyntaxError: invalid syntax
=========================== short test summary info ===========================
ERROR tests/test_transform.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.43s

복구 후 종료 코드 : 2

```

이번에는 **`points.shape`에 점(`.`) 대신 쉼표(`,`)가 들어간 오타**예요.

현재 97번째 줄:
```python
assert restored.shape == points, shape, "복원된 점군의 형태가 원본과 다릅니다."
```

이렇게 수정하세요.
```python
assert restored.shape == points.shape, \
    "복원된 점군의 형태가 원본과 다릅니다."
```

`points.shape`은 원본 점 배열의 크기인 `(N, 3)`을 뜻해요. 복원된 배열도 같은 크기인지 비교하는 코드입니다.

저장한 뒤 테스트 셀을 다시 실행하면 돼요.

---

