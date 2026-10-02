Date 2026 Aug 27

숙제를 하면서 배우는데 다 외우지 못하니 하나하나 새로 배운 것을 메모해둔다:

```python
def value(a,x) --> float
```
- 출력을 float로 내보낼거라는 의미

<br>

```python
__all__ = [
    "vector",
    "dot",
]

def vector...

def dot...
```
- 이 파일에서 밖으로 공개할 함수 목록을 적어놓는 것

<br>

---

### Normalize

#### 사전 코딩:

```python
def vector(x) -> np.array:
    """입력한 숫자을 벡터로 인식"""
    if v.ndim != 1:
        raise ValueError("백터는 1차원이어야 합니다.")
    if v.size == 0:
        raise ValueError("빈 벡터는 사용할 수 없습니다.")
    return np.asarray([x,dtype=float]) 

def dot(a,b) -> float:
    """같은 차원인 두 벡터의 곱을 구한다."""
    a, b = vector(a),vector(b) 
    if a.shape != b.shape:
        raise ValueError(f"{a}와 {b}의 차원이 다릅니다: {a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 곱셈이 이루어질 수 없습니다. {a}와 {b}가 서로 같은 차원이 되도록 수정하시오.")
    return float(np.sum(a*b))
    # 스칼라를 return


def norm(v) -> float:
    """벡터의 크기(길이)를 구한다"""
    v = vector(v)
    return float(np.sqrt(dot(v,v)))


def angel_between(a,b) -> float:  # 스칼라를 return 하니까 float
    """두 벡터 사이의 각도를 라디안으로 구한다."""
    a, b = vector(a), vector(a)
    if a.shape != b.shape:
        raise ValueError(f"{a}와 {b}의 차원이 다릅니다: {a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 곱셈이 이루어질 수 없습니다. {a}와 {b}가 서로 같은 차원이 되도록 수정하시오.")
    if norm(a) == 0 or norm(b) == 0:
        raise ValueError("영벡터와의 각도는 정의할 수 없습니다.")
    return float(np.arccos(dot(a, b) / (norm(a) * norm(b))))
```
---

### Normalize (정규화)

<br>

내가 직접 짜낸 코딩:
```python
def normalize(a) -> float:
    """두 벡터의 정규화"""
    v = vector(a)
    if norm(a) == 0:
        raise ValueError("영벡터와의 각도는 정의할 수 없습니다.")
    return float(a / norm(a))
```
- 틀린 답

<br>

chat GPT:
```python
def normalize(a) -> np.ndarray:  # ndarray로 값을 돌려야 한다. not float.
    """벡터를 길이가 1인 단위벡터로 만든다"""
    v =vector(a)
    if norm(v) == 0:
        raise ValueError("영벡터와의 각도는 정의할 수 없습니다.")
    return v/norm(v) # vector()에 이미 np.array를 했기 때문에 이미 반환되는 갑은 np.array로 여겨짐.
```


<br>

---
### Project

나의 코딩:
```python
def project(a,b) -> np.array:
    """a 벡터가 b 벡터로 정사영 된 벡터값"""
    a, b = vector(a), vector(a)
    if a.shape != b.shape:
        raise ValueError(f"{a}와 {b}의 차원이 다릅니다: {a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 곱셈이 이루어질 수 없습니다. {a}와 {b}가 서로 같은 차원이 되도록 수정하시오.")
    return dot(dot(a,b)/dot(b,b),b)
```
- np.array 아님
- b 벡터가 0이 되면 안됨
- 문구 설명 정정 필요
- 결과값에 대한 구성을 잘 살펴봐야 함.

<br>

chat GPT:
```python
def project(a, b) -> np.ndarray: 
    # np.array는 만들때
    # np.ndarray는 만들고 나서의 결과값을 알림

    """벡터 a를 벡터 b 위에 정사영한다."""
    # 표현 참조
    a, b = vector(a), vector(b)

    if a.shape != b.shape:
        raise ValueError("두 벡터의 차원이 같아야 합니다.")

    if norm(b) == 0:
        raise ValueError("영벡터 위에는 정사영할 수 없습니다.")
    # 정사영 계산에 들어가는 마지막 b가 0이면 0 위에 정사영을 할 수 없어서 조건을 걸어 놓는다.
    return (dot(a, b) / dot(b, b)) * b
    # (dot(a, b) / dot(b, b))까지는 스칼라다. 그래서 여기서 dot()를 겉에 또 사용하지 않는다. dot()는 벡터끼리 * 할때의 명령을 준 것. 
```

---

### Reject

나의 코딩:
```python
def reject(a, b)-> np.ndarray:
    p = project(a, b)
    if a.shape != b.shape:
        raise ValueError(f"{a}와 {b}의 차원이 다릅니다: {a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 곱셈이 이루어질 수 없습니다. {a}와 {b}가 서로 같은 차원이 되도록 수정하시오.")
    if norm(b) == 0:
        raise ValueError("영벡터 위에는 정사영할 수 없습니다.")
    return a-p
```
- 설명문구 빠졌고
- 성분 정의가 섣뿔리 적혀졌다.
- error msg도 정돈해서 적을 수 있다.


<br>

chat GPT:
```python
def reject(a, b) -> np.ndarray:
    """벡터 a에서 b 방향의 정사영 성분을 제거한다."""

    a, b = vector(a), vector(b)
    # 여기서 이미 project(a, b)로 해 버리면 a.shape과 b.shape을 검사할 수 없어서 위와 같이 a, b를 다시 정의 줘야 한다. 
    # 만약에 p = project(a,b)를 넣고싶다면 (아래에..retun 바로 직전)
    
    if a.shape != b.shape:
        raise ValueError("두 벡터의 차원이 같아야 합니다.")

    if norm(b) == 0:
        raise ValueError("영벡터에 대해서는 rejection을 구할 수 없습니다.")
    # 여기에 p를 넣어야 한다
    
    return a - project(a, b)
```

---

### Skew

내 코딩:
```python
def skew(a,b) -> np.array
    """벡터 a의 반대칭핼려의 곱으로 외적을 구한다."""
    a,b = vector(a), vector(b)
    if a.shape != b.shape:
        raise ValueError(
            f"{a}와 {b}의 차원이 다릅니다: "
            f"{a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 "
            f"연산이 이루어질 수 없습니다. "
            f"{a}와 {b}가 서로 같은 차원이 되도록 수정하시오."
    return np.array([
        [0,-a[2],a[1]],
        [a[2],0,-a[0]],
        [-a[1],a[0],0]
    ])
```
- np.array 아니고 np.ndarray
- 벡터 1개만 받으면 됨.
- 조건문은 이거 두개 말고 새롭게 벡터가 3 성분으로 되어야 함을 강조
- 내부 인덱스를 성분으로 정의
- array에 정의된 성분으로 설계
- 

<br>

chat GPT:
```python
def skew(v) -> np.ndarray:

    v = vector(v)
    # 숙제에는 a로 벡터가 정의 되어 있으니까 v를 a로 표기하면 됨.
    if v.size != 3:
        raise ValueError("skew는 3차원 벡터에 대해서만 정의됩니다.")
    # 벡터는 3개의 숫자로 구성되도록

    x, y, z = v
    # 각 인덱스에 성분을 새김

    return np.array([
        [0, -z,  y],
        [z,  0, -x],
        [-y, x,  0]
    ], dtype=float)
    # 보통 array를 만들면 정수로 만들어지는데 이 명령어는 실수로 만들어달라는 의미
```

---

### Cross

내 코딩:
```python
def cross(a,b) -> np.ndarray:
    """벡터 a와 b의 외적을 구한다"""
    a,b = vector(a), vector(b)
    if a.shape != b.shape:
        raise ValueError(
            f"{a}와 {b}의 차원이 다릅니다: "
            f"{a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 "
            f"연산이 이루어질 수 없습니다. " 
            f"{a}와 {b}가 서로 같은 차원이 되도록 수정하시오."
    ax, ay, az = a
    bx, by, bz = b 
    return np.array([
        ax*bz - az*by,
        az*bx - ax*bz,
        ax*by - ay*bx
    ], dtype=float)
```

<br>

chat GPT (나와 비슷한 코딩을 했을 때):
```python
def cross(a, b) -> np.ndarray:
    """벡터 a와 b의 외적을 구한다."""

    a, b = vector(a), vector(b)

    if a.shape != b.shape:
        raise ValueError(
            f"{a}와 {b}의 차원이 다릅니다: "
            f"{a}는 {a.shape}이고, {b}는 {b.shape}이므로 "
            f"연산이 이루어질 수 없습니다."
        )

    if a.size != 3 or b. != 3:
        raise ValueError("외적은 3차원 벡터에서만 정의됩니다.")
    # 벡터들의 사이즈가 정확해야 함을 명시
    ax, ay, az = a
    bx, by, bz = b

    return np.array([
        ay*bz - az*by,
        #ax 가 아니고 aybz
        az*bx - ax*bz,
        ax*by - ay*bx
    ], dtype=float)
```

<br>

chat GPT (간단한 버전):
```python
def cross(a, b) -> np.ndarray:

    a, b = vector(a), vector(b)

    if a.size != 3 or b.size != 3:
        raise ValueError("외적은 3차원 벡터에서만 정의됩니다.")

    return skew(a) @ b
    # numpy에서는 @가 행렬 곱셈이다.
```
- 위에 array를 만든 식이 똑같이 적용되는 명령이다.
- 설명문만 추가하면 된다. 

---

### Plane normal

내 코딩:
```python
def plane_normal(P1,P2,P3) -> np.ndarray:
    u = vector(P2 - P1)
    v = vector(P3 - P1)
    if u.shape != v.shape:
        raise ValueError(
            f"{a}와 {b}의 차원이 다릅니다: "
            f"{a}는 {a.shape}차원이고, {b}는 {b.shape}차원이므로 "
            f"연산이 이루어질 수 없습니다. " 
            f"{a}와 {b}가 서로 같은 차원이 되도록 수정하시오."
        )
    return np.array(cross(u,v))
```

<br>

chat GPT:
```python
def plane_normal(a, b, c) -> np.ndarray:
    """두 벡터가 만드는 평면의 단위 법선벡터를 구한다."""
    P1 = vector(a)
    P2 = vector(b)
    P3 = vector(c)
    # 아래에 공식에 맞게 적용이 되려면 각 입력 포인트는 list에서 array로 인식 되고 공식이 적용될 수 있다. 해서 이미 array로 전환하게끔 공식화 되어 있는 vector()를 사용한다.
    u = P2 - P1
    v = P3 - P1
    # 각 벡터의 정의를 주고

    n = cross(u,v)
    # 기존 외적 공식을 사용해서 외적을 구한다

    if norm(n) == 0:
        raise ValueError("두 벡터가 평행하므로 평면의 법선벡터를 정할 수 없습니다.")

    return normalize(n)
    # plane_normal 값을 반환한다.
```
