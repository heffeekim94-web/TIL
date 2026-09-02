date: 2026 Sept 2, Wednesday

## 3-5 모듈

<br>

### make_T

내 코딩:
```python
def make_T(R,t) -> np.ndarray:
    """회전행렬과 병진으로 이루어진 4x4 변환행렬을 생성합니다."""
    T = np.array([
        [R,t]
        [0,1]
        # 에러가 나옴.
        # R은 3x3 덩어리고 t는 3개짜리 벡터라서 둘을 한행처럼 np.array에 넣을 수 없다.
    ])

    if R.shape != (3,3):
        raise ValueError("R은 3x3 회전행렬이어야 합니다.")
    if t.shape != (3,):
        raise ValueError("t은 shape (3,)의 벡터여야 합니다.")

    return T
```

<br>

정정 후:
```python
def make_T(R,t) -> np.ndarray:
    """회전행렬과 병진으로 이루어진 4x4 변환행렬을 생성합니다."""
    T = np.eye(4)   
    # I를 우선 만들어 준다 
    # 예)
    # [1,0,0,0]
    # [0,1,0,0]
    # [0,0,1,0]
    # [0,0,0,1]
    T[:3, :3] = R
    # 그리고 R의 자리를 새겨줌으로서 덮어씌운다
    T[:3, 3] = t
    # t도 마찬가지

    if R.shape != (3,3):
        raise ValueError("R은 3x3 회전행렬이어야 합니다.")
    if t.shape != (3,):
        raise ValueError("t은 shape (3,)의 벡터여야 합니다.")

    return T
    # 결과는 이렇게 된다
    # T =   [R11,R12,R13,tx]
    #       [R21,R22,R23,ty]
    #       [R31,R32,R33,tz]
    #       [  0,  0,  0, 1]
```
---

### inv_T


```math
T = \begin{bmatrix} R^{T} & -R^{T}t \\ 0 & 1 \end{bmatrix}
```
를 구현 하려면 아래와 같은 코드 형식으로 가야 한다.

```python
def inv_T(T) -> np.ndarray:
    """4x4 변환행렬의 역행렬을 계산합니다."""
    R = T[:3, :3]
    t = T[:3, 3]
    # 그 어떤 행을 입력 해도 위와 같이 구분하게끔 다시 정의한다.
    T_inv = np.eye(4)
    # 우선 I 모댱을 만들고 
    T_inv[:3, :3] = R.T
    # 해당 위치에 놓일 수들을 = 행렬을 변환한다
    T_inv[:3, 3] = -R.T @ t
    # 해당 위치에 놓일 수들을 = (-)값에 변환행렬 하고 t를 곱해준다.

    if T.shape != (4,4):
        raise ValueError("T는 4x4 변환행렬이어야 합니다.")

    return T_inv
```
- python파일이라 자동으로 작성 됨.


---

### transport_point

내 코딩
```python
def transform_point(T,v) -> np.ndarray:
    """4x4 변환행렬 T를 이용하여 3D 점 v를 변환합니다."""
    Rp = make_T(T,v)
    # make_T를 불러올 필요가 없음. 이미 회전행렬을 한 변환행렬이라고 봐야 함.
    P = Rp @ np.append(v, 1)
        
    
    if v.shape != (3,):
        raise ValueError("v는 shape (3,)의 벡터여야 합니다.")
    if T.shape != (4,4):
        raise ValueError("T는 4x4 변환행렬이어야 합니다.")
    
    return P[:3]
```

정정 1차 후 
```python
def transform_point(T,v) -> np.ndarray:
    """4x4 변환행렬 T를 이용하여 3D 점 v를 변환합니다."""
    p = np.eye(4)
    p[4,:] = v
    # -->   [1,0,0,0]
    #       [0,1,0,0]
    #       [0,0,1,0]
    #       [1,0,0,1]  <-- v added
    # returns 4x4 array but need 1x3...

    new_p = T @ p
        
    
    if v.shape != (3,):
        raise ValueError("v는 shape (3,)의 벡터여야 합니다.")
    if T.shape != (4,4):
        raise ValueError("T는 4x4 변환행렬이어야 합니다.")
    
    return new_p[:3]
```

정정 2차 후 
```python
def transform_point(T,v) -> np.ndarray:
    """4x4 변환행렬 T를 이용하여 3D 점 v를 변환합니다."""
    p_homogeneous = np.append(v,1)
    new_p = T @ p
        
    
    if v.shape != (3,):
        raise ValueError("v는 shape (3,)의 벡터여야 합니다.")
    if T.shape != (4,4):
        raise ValueError("T는 4x4 변환행렬이어야 합니다.")
    
    return new_p[:3]
```