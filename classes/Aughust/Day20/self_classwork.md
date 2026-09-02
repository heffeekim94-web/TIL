date: 2026 Aug 31, Monday

과제의 이해도가 조금 떨어지는 것 같아 처음부터 다시 하나하나 짚어서 메모함. 

'#'를 참조

### Vector

```python
def vector(x) -> np.array:
    """입력한 숫자을 벡터로 인식"""
    
    v = np.array(x, dtype=float)                    
    # 입력한 x를 float 타입의 NumPy 배열로 바꾸는 명령어

    if v.ndim != 1:
        raise ValueError("백터는 1차원이어야 합니다.")
    if v.size == 0:
        raise ValueError("빈 벡터는 사용할 수 없습니다.")
    return v 
```

---

### Angle between
```python
def angle_between(a,b, degrees=True) -> float:
    # 각도를 라디안이 아닌 도로 돌려 받겠다는 의미
    """두 벡터 사이의 각도를 라디안으로 구한다."""
    a, b = vector(a), vector(b)
    if a.shape != b.shape:
        raise ValueError(
            f"{a}와 {b}의 차원이 다릅니다: "
            f"{a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 "
            f"연산이 이루어질 수 없습니다. "
            f"{a}와 {b}가 서로 같은 차원이 되도록 수정하시오."
        )
    if norm(a) == 0 or norm(b) == 0:
        raise ValueError("영벡터는 정규호하할 수 없습니다.")
    return float(np.degrees(np.arccos(dot(a, b) / (norm(a) * norm(b)))))
    # numpy의 degree라는 함수를 사용하여 도를 반환해야 함.
```

---

### Row echelon

내 코드:
```python
def row_echelon(M) -> np.ndarray:
    a, b, c = vector(a), vector(b), vector(c)
    q = np.array([a, b, c], dtype=float)

    for i in range(2):
        if q[i,i] == 0:
            for r in range(i + 1, 3):
                if q[r,i] !=0:
                    q[[i,r]] = q[[r,i]]
                    break

        if q[i,i] == 0:
            continue
    
        for row in range(i + 1, 3):
            if q[row, i] != 0:
                k = q[row, i] / q[i,i]
                q[row] = q[row] - k * q[i]
```

정정 후 코드:
```python
def row_echelon(M) -> np.ndarray:
    q = np.array(M, dtype=float) 
    # array를 부르기때문에 

    pivots = []
    # 반환해야 하는 값: 피벗, 사다리골 만들고 맨 앞에 있는 1의 개수
    swaps = 0
    # 첫번째 란의 첫 행이 0이었으면 다른 줄하고 swap한 개수
    for i in range(2):
        if q[i,i] == 0:
            for r in range(i + 1, 3):
                if q[r,i] !=0:
                    q[[i,r]] = q[[r,i]]
                    swaps += 1
                    # 추가
                    break

        if q[i,i] == 0:
            continue
        
        pivots.append(i)
        # 추가
        
        for row in range(i + 1, 3):
            if q[row, i] != 0:
                k = q[row, i] / q[i,i]
                q[row] = q[row] - k * q[i]
    
    return q, pivots, swaps
    # 체점에 보면 불러오는 값들
```

## rotation.py

### rotation

x축 회전행렬:
```python
def rot_x(theta) -> np.ndarray:
    # 각도를 입력해야 하니까 theta를 입력값으로 설정한다
    """입력된 각도만큼 x축으로 회전하는 회전행렬을 반환한다."""
    return np.array([
        [1,0,0] # x축으로 회전하기 때문에 
        [0,np.cos(theta),-np.sin(theta)] # 그저 sin(theta) 혹은 cos(theta)하면 시스템이 알아들을 수 없기 때문에 불러온 np를 사용한다
        [0,np.sin(theta), np.cos(theta)]
    ])
```

나머지 y축과 z축:

```python
def rot_y(theta) -> np.ndarray:
    """입력된 각도만큼 y축으로 회전하는 회전행렬을 반환한다."""
    return np.array([
        [np.cos(theta), 0, np.sin(theta)]
        [0,1,0] # y축 기준의 회전이니까
        [-np.sin(theta), 0, np.cos(theta)]
    ])


def rot_z(theta) -> np.ndarray:
    """입력된 각도만큼 z축으로 회전하는 회전행렬을 반환한다."""
    return np.array([
        [np.cos(theta), -np.sin(theta), 0]
        [np.sin(theta), np.cos(theta), 0]
        [0,0,1] # z축 기준의 회전이니까
    ])
```

---

### rodrigues

```python
def rodrigues(axis, theta):
    axis = np.array (axis, dtype=float) # 임의의 회전축
    k = axis / np.linalg.norm(axis) # 단위 벡터로 전환
                                    # linalg = linear algebra
    K = skew(k)                     # 외적을 구함
    I = np.eye(3)
    return I + np.sin(theta)*K + (1-np.cos(theta))*(K@K)
```
- 임이의 벡터 입력 -> 단위벡터로 변환 -> 단위행렬 I 준비 -> 로드리게스 공식에 입력 -> 회전행렬 R 완성

---

### Gram Shmidt

```python
def gram_shmidt(A) -> np.ndarray:
    A = np.array(A, dtype=float, copy=True)
    # (1) 입력행렬 A를 NumPy로 바꾸고 계산하면서 원본이 바뀌지 않도록 복사하는 것

    n_cols = A.shape[1]
    # 열 개수 ???

    Q = np.zeros_like(A)
    # 결과를 담을 빈 행렬을 만드는 것
    # 행령 A처럼 생겼지만 모두 0인 행렬

    for j in range(n_cols):
        v = A[:,j].copy()
        # (2)[모든행, j 열]
        # 열벡터에 대해 Gram-Schmidt 직교정규화를 수행한다

        for i in range(j):
            v -= (Q[:,i]@v)*Q[:,i]
                # 정사영 * Q = 
        nv = np.sqrt(v @ v)
        # v의 길이, v의 norm
        # norm() 쓰면 되는거 아닌가~??
        if nv <= 1e-12:
            raise ValueError(
                f"{j}번 열이 앞선 열들에 종속이라 직교화할 수 없습니다."
            )

        Q[:,j] = v/nv
        # 남은 벡터를 길이 1로 만들어서 Q의 j번째 열에 둔다.

    return Q
```
(1) 예시안:
```python
A = [a1 a2 a3]  # a1, a2, a3 각각 열벡터
```

(2) 예시안:
```
       열
       0  1  2
      ┌─────────┐
행 0  │ 1  4  7 │
행 1  │ 2  5  8 │
행 2  │ 3  6  9 │
      └─────────┘
       ↑
    Q[:, 0]

   -> [1,2,3] 위의 뜻

    즉,
   Q = [ q₁  q₂  q₃ ]
    
    Q[:, 0] → q₁
    Q[:, 1] → q₂
    Q[:, 2] → q₃
```
---

### test.py

#### test_columns_are_orthonormal
```python
def test_columns_are_orthonormal():
    R = rot_z(0.5)
    # 회전행렬 1개 생성
    result = R.T @ R
    # 열벡터들이 직교정규인지 계산
    assert np.allclose(result, np.eye(3))
    # 단위행렬과 거의 같은가?
```
- pytest는 test_로 시작하는 함수를 찾아서 자동으로 실행해준다. 
- 즉, columns_are_orthonormal인지 확인해 준다는 뜻

* `np.eye(3)`은 **3×3 단위행렬(identity matrix)을 만들어주는 NumPy 명령어**

```python
np.eye(3)
```

결과:

```python
array([
    [1., 0., 0.],
    [0., 1., 0.],
    [0., 0., 1.]
])
```

즉 수학으로는:

$$
I=
\begin{bmatrix}
1&0&0\\
0&1&0\\
0&0&1
\end{bmatrix}
$$


여기서 `3`은 **3×3 크기로 만들어라**라는 뜻

예를 들어:

```python
np.eye(2)
```

는

$$
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

이고,

```python
np.eye(4)
```

는

$$
\begin{bmatrix}
1&0&0&0\\
0&1&0&0\\
0&0&1&0\\
0&0&0&1
\end{bmatrix}
$$

이다.

그래서 지금 하려는 것은:

```python
assert np.allclose(R.T @ R, np.eye(3))
```

라고 하는 이유는 회전행렬이라면

$$
R^TR=I
$$

여야 하니까,

```text
R.T @ R        np.eye(3)
   ↓               ↓
 실제 계산값   3×3 단위행렬

        둘이 같은가?
```

를 검사하는 것.

그리고 `eye`라는 이름은 **Identity matrix의 `I`(아이)**를 영어로 읽으면 `eye`와 발음이 같아서 붙은 이름이라고 생각하면 기억하기 쉬움.

<br>

#### test_determinant_is_one
```python
def test_determinant_is_one():
    R = rot_z(0.5)
    result = det(R)
    assert np.isclose(result, 1)
```
- `isclose`는 숫자 하나와 숫자 하나가 거의 같은지 확인한다.
- vs
- `allclose`는 배열이나 행렬처럼 여러 숫자 전체가 각각 거의 같은지 확인한다. 
- 사용전 확인해 봐야 하는 사항:
```
isclose = 이 값들이 가까운가?
allclose = 전부(all) 가까운가?
```

<br>

#### test_inverse_equals_transpose
```python
def test_inverse_equals_transpose():
    R = rot_z(0.5)
    assert np.allclose(np.linalg.inv(R), R.T)
```

