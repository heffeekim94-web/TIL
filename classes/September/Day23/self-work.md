Date 2026 Sept 3, Thursday

3-5번 classwork

continue form [Day22](../Day22/self-work.md)


### to_homogeneous

정정 3차 후
```python
def to_homogeneous(P, w:float = 1.0) -> np.ndarray:
    """3D 점들을 동차좌표로 변환합니다."""
    P_homogeneous = np.asarray(P, dtype=float)
    
    if P.shape == (3,):
        return np.append(P, w)
    
    if P.ndim != 2 or P.shape[1] != 3:
        # 2차원 (행,열) 이 아니고, 열이 3개가 아니면 에러 메세지
        w_column = np.full((P.shape[0], 1), w)
        raise ValueError("P는 shape (N, 3)의 배열이어야 합니다.")
```
```python
def to_homogeneous(P, w:float = 1.0) -> np.ndarray:
    """3D 점들을 동차좌표로 변환합니다."""
    P = np.asarray(P, dtype=float)
    # array로 변환해서 받고 
    if P.shape == (3,):
        return np.append(P, w)
    # 모양이 3행 그 어떤 열이어도 끝에 1을 넣어라    
    if P.ndim == 2 or P.shape[1] == 3:
    # 차원이 2차원이든 열이 3개든 오류 메세지
        w_column = np.full((P.shape[0], 1), w)
        return np.hstack((P, w_column))
        
    raise ValueError("P는 shape (N, 3)의 배열이어야 합니다.")    
```

### transform_direction

```python
def transform_direction(T, v) -> np.ndarray:
    """4x4 변환행렬 T를 이용하여 3D 방향 벡터 v를 변환합니다."""
    T = np.asarray(T, dtype=float)
    v = np.asarray(v, dtype=float)
    # python 코드에서 numpy로 인식하게 하는 것.
    if v.shape != (3,):
        raise ValueError("v는 shape (3,)의 벡터이어야 합니다.")
    if T.shape != (4,4):
        raise ValueError("T는 4x4 변환행렬이어야 합니다.")
    R = T[:3, :3]
    new_v = R @ v
    return new_v
```

### invert_batch

'batch(배치)'는 한국말로 **'묶음'** 또는 '일괄 처리'라는 뜻입니다.

프로그래밍이나 행렬 연산(NumPy 등)에서 '배치(batch)'란 **데이터를 하나씩 처리하지 않고, 여러 개를 한꺼번에 하나의 덩어리로 묶어서 연산하는 방식**을 말합니다.

현재 풀고 계신 노트북 문제(5-4)의 맥락에 대입해 보면 다음과 같습니다.

* **단건 연산 (`inv_T`):** 변환 행렬 1개를 함수에 넣고 1개의 역행렬을 계산해서 받는 방식입니다.
* **배치 연산 (`inv_T_batch`):** 변환 행렬 2,000개를 하나의 큰 묶음(N, 4, 4)으로 겹겹이 쌓아서 함수에 딱 한 번만 전달하고, 2,000개의 역행렬을 한 번에 계산해서 받는 방식입니다.

화면의 설명에도 나와 있듯, 파이썬에서는 함수를 2,000번 반복해서 호출하는 데 걸리는 준비 시간(오버헤드)이 실제 수학 계산 시간보다 훨씬 깁니다. 따라서 이렇게 '묶음(배치)'으로 한 번에 연산하면 속도를 비약적으로 높일 수 있습니다.

#### <np.swapaxesr>

`np.swapaxesr`는 NumPy 배열에서 **특정 두 축(dimension)의 위치를 서로 맞바꾸는(swap)** 함수입니다.

함수의 기본 구조는 다음과 같습니다:

```python
np.swapaxes(arr, axis1, axis2)
```

현재 작성 중이신 `inv_T_batch` 함수 맥락(`(N, 4, 4)` 형태의 행렬 배치)에서 왜 이 함수가 힌트로 주어졌는지 살펴보면 다음과 같습니다:

1. **회전 행렬의 전치(Transpose):** 동차변환의 역행렬 공식에 따르면 회전 부분 $R$은 전치 행렬($R^T$)이 되어야 합니다.
2. **배치 구조에서의 전치:** 데이터가 단건이 아니라 `(N, 3, 3)` 형태의 묶음(배치)으로 들어있을 때, 일반적인 `.T`를 쓰면 전체 순서가 뒤틀려서 망가집니다. 우리가 원하는 것은 **각 행렬의 내부(행과 열, 즉 1번 축과 2번 축)만 전치**시키는 것입니다.
3. 따라서 `np.swapaxes(Ts_R, 1, 2)`를 사용하면 **배치 번호인 0번 축은 그대로 둔 채, 각 행렬의 행(1번 축)과 열(2번 축)의 위치만 깔끔하게 맞바꿔서** $R^T$ 배치들을 한 번에 만들 수 있습니다.


#### <np.einsum>

`np.einsum`은 아인슈타인 표기법(Einstein summation)을 사용해서 **다차원 배열의 복잡한 곱셈과 축소(summation) 연산을 수식처럼 간결하고 직관적으로 처리**해 주는 함수입니다.

현재 작성하셔야 하는 `inv_T_batch`에서 힌트로 나온 `"nij,nj->ni"`를 예로 들면 이 함수가 어떻게 동작하는지 쉽게 이해할 수 있습니다.

### `np.einsum("nij,nj->ni", ...)`의 의미

1. **입력 1 (`nij`):** 첫 번째 입력 배열(예: 회전 행렬 배치 $R^T$)이 `(N, 3, 3)` 형태를 가집니다. 여기서 각 축의 이름을 임의로 `n`(배치), `i`(행), `j`(열)라고 부른 겁니다.
2. **입력 2 (`nj`):** 두 번째 입력 배열(예: 병진 벡터 $t$)이 `(N, 3)` 형태를 가집니다. 축 이름은 `n`(배치), `j`(열)입니다.
3. **출력 (`ni`):** 이 둘을 곱한 뒤, 겹치는 인덱스인 `j`를 기준으로 합산(sum)하여 최종적으로 `(N, 3)` 형태의 결과물로 만들어 달라는 뜻입니다.

### 왜 `np.dot`이나 `@` 대신 이걸 쓸까요?

배치(N개) 차원이 껴 있는 상태에서 일반적인 행렬 곱을 하려면 차원을 맞추느라 코드가 복잡해지거나 `for` 문을 돌려야 합니다.

하지만 `np.einsum`을 쓰면 "배치 축(n)은 그대로 유지하고, 행렬과 벡터의 곱셈 공식대로 알아서 계산해 줘"라고 한 줄로 깔끔하게 지시할 수 있어서, `inv_T_batch` 안에서 $-R^T t$ 부분을 계산할 때 매우 유용하게 쓰입니다.


```python
def inv_T_batch(Ts) -> np.ndarray:
    """(N, 4, 4) 동차변환 묶음을 반복문 없이 한번에 역변환한다."""
    # 1. 입력 검증 (N, 4, 4) 형태가 맞는지 검증
    Ts = np.asarray(Ts, dtype=float)
    if Ts.ndim != 3 or Ts.shape[-2:] != (4,4):
        raise ValueError("Ts는 shape (N, 4, 4)의 배열이어야 합니다.")
    
    # 2. 회전행렬 R과 병진 벡터 t 추출
    R = Ts[:, :3, :3]  # shape (N, 3, 3)
    t = Ts[:, :3, 3]   # shape (N, 3)   

    # 3. R의 배치 전치 구하기
    R_T = np.swapaxes(R, 1, 2)  # shape (N, 3, 3)

    # 4. -R^T * t 의 배치 연산 구하기
    neg_R_Tt = -np.einsum('nij,nj->ni', R_T, t)  # shape (N, 3)

    # 5. 결과를 담을 (N, 4, 4) 빈 배열 ᄄᆃ는 영행렬 생성 후 채우기
    N = Ts.shape[0]
    inv_Ts = np.zeros((N, 4, 4), dtype=Ts.dtype)

    inv_Ts[:, :3, :3] = R_T
    inv_Ts[:, :3, 3] = neg_R_Tt
    inv_Ts[:, 3, 3] = 1.0 # 마지막 행은 [0, 0, 0, 1]로

    return inv_Ts
```
- gemini 도움 받음

---

coordiante_chain.py를 작성하려면 rotation.py의 axis_angle_from_matrix()를 작성이 완료가 되어야 한다. 

#### 코딩 가이드:

- 회전축은 고유값 1 에 대응하는 실수 고유벡터다 (R k = k).
      -> 여기서는 `np.linalg.eig` 를 써도 된다 (검산이 아니라 축 복원이 목적).
- 회전각은 **$\text{trace}(R) = 1 + 2 \cos\theta$**  에서 구한다.
- arccos 의 치역이 [0, pi] 라 '어느 쪽으로 도는지'는 알 수 없고,
  고유벡터도 부호가 정해지지 않는다. 반대칭 성분
  R - R^T = 2 sin(theta) [k]_x 를 이용해 부호를 맞춘다.
- theta = 0 (회전 없음) 과 theta = pi (sin = 0) 는 따로 처리해야 한다.
      두 경우에 어떤 규약을 쓸지 정하고 주석으로 남긴다.


## np.linalg.eig
`np.linalg.eig`는 NumPy에서 제공하는 함수로, 정사각 행렬의 고유값(eigenvalue)과 고유벡터(eigenvector)를 구해주는 함수입니다.

선형대수학에서 고유값과 고유벡터는 행렬이 공간을 어떻게 변환하는지 그 성질(특징)을 뜯어볼 때 핵심적으로 사용됩니다.

### 사용법과 반환값

```python
eigenvalues, eigenvectors = np.linalg.eig(A)

```

* **`eigenvalues` (고유값):** 행렬이 늘어나거나 줄어드는 크기(비율)를 나타내는 값들입니다.
* **`eigenvectors` (고유벡터):** 행렬을 곱해도 방향이 변하지 않고 크기만 변하는 특정한 방향(축)들을 나타냅니다.

### 현재 보고 계신 코드(`rotation.py`)에서의 의미

지금 보고 계신 `axis_angle_from_matrix` 함수 주석을 보면, 회전 행렬 $R$에서 회전축을 복원할 때 "회전축은 고유값이 1인 실수 고유벡터($Rk = k$)다"라는 성질을 이용하라고 되어 있습니다.

어떤 물체를 3차원 공간에서 특정 축을 중심으로 회전시켰을 때, **그 회전축 위에 있는 점들은 회전해도 자리가 바뀌지 않고 그대로 제자리에 남아있게 됩니다.** 즉, 회전축 방향의 벡터는 변환 후에도 크기와 방향이 그대로 유지(고유값이 1)되기 때문에, `np.linalg.eig`로 고유값이 1이 나오는 고유벡터를 찾으면 그게 바로 우리가 찾던 **회전축**이 되는 것입니다!


## atol

여기서 `atol`은 Absolute Tolerance(절대 오차 허용치)의 약자입니다.

컴퓨터가 부동소수점(실수)을 계산할 때는 미세한 오차가 발생하기 때문에, 어떤 값이 정확히 `0`인지 판정할 때 `== 0`이라고 쓰면 오차 때문에 거짓이 나오는 경우가 많습니다.

따라서 `atol=1e-8`은 "10의 마이너스 8제곱(0.00000001)보다 작은 차이는 그냥 0(또는 같은 값)으로 쳐주겠다"라는 뜻의 기준값입니다.

지금 보고 계신 함수 설명에 나와 있는 것처럼, 회전각이 0도(`theta = 0`)이거나 180도(`theta = pi`)일 때 `sin(theta)` 값이 0에 아주 가까워지는데, 컴퓨터 계산 오차 때문에 정확히 0이 안 되고 아주 작은 소수점으로 떨어질 수 있습니다. 이때 `atol`을 활용해 "이 정도 오차는 0으로 간주하고 예외 처리를 하자"라고 판정하기 위해 사용하는 안전장치입니다.
