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