Date 2026 Sept 06, Sunday

3-4 모듈 학습

## coordinate_chain.py

### path to root

좋아요. 파일을 확인했어요. **첫 번째 TODO인 `_path_to_root`부터 하나씩** 작성해 봐요. 파일은 수정하지 않았어요.

먼저 파일 첫 줄에 공백이 하나 있어요.

```python
 from __future__ import annotations
```

맨 앞 공백을 제거해 주세요. 파일 최상위 코드가 들여쓰기되어 있으면 `IndentationError`가 발생합니다.

**1. 이 클래스가 저장하는 구조부터 이해해요.**

과제의 좌표계 연결은 다음과 같아요.

```text
base
 └─ link
     └─ camera
```

이미 작성된 `add()`는 부모 관계를 다음처럼 저장해요.

```python
self._parent = {
    "link": "base",
    "camera": "link",
}
```

즉, **자식 이름으로 부모 이름을 찾는 딕셔너리**예요.

```python
self._parent["camera"]  # "link"
self._parent["link"]    # "base"
```

**2. `_path_to_root`가 반환할 결과**

```python
_path_to_root("camera")
```

를 호출하면 부모를 따라 올라가서:

```python
["camera", "link", "base"]
```

를 반환해야 해요. 아직 행렬 계산은 하지 않고 **좌표계 이름의 경로만 만드는 단계**입니다.

**3. 출발 좌표계를 리스트에 넣어요.**

```python
path = [frame]
```

`frame = "camera"`라면:

```python
path = ["camera"]
```

입니다.

**4. 루트에 도착할 때까지 부모를 찾아요.**

```python
while frame != self.root:
```

`self.root`는 기본적으로 `"base"`예요. 현재 좌표계가 `"base"`가 될 때까지 반복합니다.

먼저 부모 정보가 있는지 확인해요.

```python
if frame not in self._parent:
    raise KeyError(f"{frame}이 루트 {self.root}에 연결되어 있지 않습니다.")
```

루트도 아닌데 부모 정보가 없으면 더 올라갈 수 없으므로, 과제 안내대로 `KeyError`를 발생시켜요.

그다음 부모로 이동합니다.

```python
frame = self._parent[frame]
```

첫 반복에서는 `"camera"`가 `"link"`로 바뀌어요.

**5. 경로에 부모를 추가해요.**

```python
path.append(frame)
```

이때 잘못된 등록으로 부모 관계가 순환하면 무한 반복할 수 있어요. 이미 방문한 이름인지 검사하면 막을 수 있습니다.

```python
if frame in path:
    raise KeyError("부모 관계가 순환하여 루트에 도달할 수 없습니다.")

path.append(frame)
```

**전체 코드는 이렇게 작성하면 돼요.**

아래 코드를 **`CoordinateChain` 클래스 안에서**, 기존 `_path_to_root` 함수 대신 작성하세요.

```python
    def _path_to_root(self, frame: str) -> list[str]:
        """frame에서 root까지의 경로 [frame, ..., root]를 만든다."""
        path = [frame]

        while frame != self.root:
            if frame not in self._parent:
                raise KeyError(
                    f"{frame}이 루트 {self.root}에 연결되어 있지 않습니다."
                )

            frame = self._parent[frame]

            if frame in path:
                raise KeyError(
                    "부모 관계가 순환하여 루트에 도달할 수 없습니다."
                )

            path.append(frame)

        return path
```

`"camera"`를 넣었을 때 변화를 따라가면:

| 단계 | `frame` | `path` |
|---|---|---|
| 시작 | `"camera"` | `["camera"]` |
| 첫 반복 후 | `"link"` | `["camera", "link"]` |
| 두 번째 반복 후 | `"base"` | `["camera", "link", "base"]` |

이제 `frame == self.root`이므로 반복을 끝내고 경로를 반환해요. 처음부터 `"base"`를 넣으면 반복 없이 `["base"]`를 반환합니다.

---

### vectors.py - gauss_eliminate

이 코드가 누락되어 진행한다

확인했어요. 현재 `vectors.py`에는 **`gauss_eliminate()`가 아직 없고**, 노트북에서는 다음 형태로 호출하도록 되어 있어요.

```python
x, steps = gauss_eliminate(A, b, pivoting=True, verbose=True)
```

따라서 새 함수를 함께 작성하면 됩니다. 파일은 수정하지 않았어요.

**먼저 함수의 목적부터 볼게요.**

이전에 작성한 `inverse_gauss_jordan`은 역행렬을 구했죠. 이번에는 **연립방정식 `Ax = b`의 해 `x`**를 구해요.

```text
[A | b] 만들기
    ↓
피벗 아래를 0으로 만들기 — 전진 소거
    ↓
마지막 식부터 거꾸로 해 구하기 — 후진 대입
```

`steps`에는 과제에서 요구하는 중간 첨가행렬들을 기록할 거예요.

**첫 단계: 입력을 준비하고 `[A | b]` 만들기**

우선 아래 부분부터 작성해 보세요.

```python
def gauss_eliminate(A, b, pivoting=True, verbose=False):
    A = np.array(A, dtype=float, copy=True)
    b = np.array(b, dtype=float, copy=True)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A는 정사각행렬이어야 합니다.")

    n = A.shape[0]

    if b.shape != (n,):
        raise ValueError("b는 A의 행 개수와 같은 길이의 벡터여야 합니다.")

    augmented = np.column_stack([A, b])

    steps = [augmented.copy()]

    if verbose:
        print("초기 첨가행렬:")
        print(augmented)
```

각 부분의 의미를 살펴볼게요.

**① `A`와 `b`를 실수형 배열로 변환**

행을 나누면 소수가 나올 수 있어서 `dtype=float`를 사용해요. `copy=True`는 원본을 보존하기 위한 거예요.

**② 크기 검사**

예를 들어 미지수 3개의 연립방정식이면:

```text
A.shape = (3, 3)
b.shape = (3,)
```

이어야 합니다. 이 구현에서는 정사각행렬과 1차원 우변 벡터를 받도록 정한 거예요.

**③ `np.column_stack([A, b])`**

`b`를 **마지막 열로 붙여** 첨가행렬을 만들어요.

```python
A = [
    [2, 1],
    [1, 3],
]
b = [5, 7]
```

이라면:

```text
[2  1 | 5]
[1  3 | 7]
```

이 됩니다. 실제 배열에는 `|` 구분선은 없어요.

**④ `steps = [augmented.copy()]`**

초기 행렬을 기록하는 리스트예요. `.copy()`를 해야 이후 `augmented`를 바꾸더라도 **기록해 둔 과거 상태가 유지**됩니다.

**⑤ `if verbose:`**

`verbose=True`로 호출했을 때만 행렬을 출력해요.

여기까지는 준비 단계라 아직 해를 반환하지 않아요. 다음에는 `for col in range(n)`으로 **피벗 선택과 행 교환**을 작성하면 됩니다.

이제 **피벗을 선택하고 행을 교환하는 부분**을 작성해 봐요. 앞에서 작성한 초기 행렬 출력 코드 아래에 이어 붙이면 됩니다.

```python
    for col in range(n):
        if pivoting:
            pivot_row = col + np.argmax(
                np.abs(augmented[col:, col])
            )

            if pivot_row != col:
                augmented[[col, pivot_row]] = augmented[[pivot_row, col]]

                steps.append(augmented.copy())

                if verbose:
                    print(f"{col}번 행과 {pivot_row}번 행 교환:")
                    print(augmented)

        if augmented[col, col] == 0:
            raise ValueError(
                "현재 피벗이 0이므로 소거를 진행할 수 없습니다."
            )
```

**1. `for col in range(n)`**

열을 하나씩 처리해요. 3×3 행렬이면 `col`이 `0 → 1 → 2`로 바뀝니다.

```python
for col in range(n):
```

이번 함수에서는 각 단계의 피벗 위치가 `augmented[col, col]`이에요.

**2. `if pivoting:`**

```python
if pivoting:
```

`pivoting=True`일 때만 더 적절한 피벗을 찾아 행을 교환합니다.

과제에서 **피벗팅을 사용하는 경우와 사용하지 않는 경우의 계산 오차를 비교**하므로 이 조건이 필요해요.

**3. 절댓값이 가장 큰 피벗 선택**

```python
pivot_row = col + np.argmax(
    np.abs(augmented[col:, col])
)
```

이전에 배운 것과 같아요. 현재 열에서 **현재 행부터 아래쪽까지** 살펴보고, 절댓값이 가장 큰 원소의 행 번호를 구합니다.

예를 들어 첫 번째 열이:

```text
[1]
[2]
[3]
```

이면 `pivot_row = 2`예요.

**4. 필요할 때 행 교환**

```python
if pivot_row != col:
    augmented[[col, pivot_row]] = augmented[[pivot_row, col]]
```

선택한 행이 현재 행과 다르면 교환해요. **첨가행렬 전체 행을 바꾸므로 우변 `b`도 함께 이동**합니다.

```text
교환 전             교환 후
[1  2 | 5]          [3  4 | 7]
[3  4 | 7]          [1  2 | 5]
```

교환한 상태는 `steps`에 복사해 기록하고, `verbose=True`이면 출력해요.

**5. 피벗이 0인지 확인**

```python
if augmented[col, col] == 0:
    raise ValueError(...)
```

다음 단계에서 피벗으로 나눌 것이므로 0이면 멈춰야 해요.

여기서는 과제의 **아주 작은 피벗으로 인한 오차 실험**을 위해, 작은 값까지 0으로 취급하는 `np.isclose` 대신 정확히 0인지 검사합니다.

또한 `pivoting=False`에서는 역행렬이 존재하는 행렬이라도 현재 피벗이 0일 수 있어요. 그래서 오류 메시지도 “역행렬이 없다”가 아니라 **“현재 피벗으로 소거할 수 없다”**고 썼어요.

다음 단계는 이 `for col` 안에서 **피벗 아래의 원소들을 0으로 만드는 것**이에요. 이번 가우스 소거에서는 피벗 행을 나눠서 1로 만들 필요는 없습니다.

아니요. **`pivoting`과 `verbose`는 함수가 아니라, 우리가 함수 정의에서 만든 매개변수**예요.

맨 처음 작성한 줄을 보면:

```python
def gauss_eliminate(A, b, pivoting=True, verbose=False):
```

여기서 이름과 기본값을 정했어요.

| 매개변수 | 기본값 | 우리가 정한 용도 |
|---|---|---|
| `pivoting` | `True` | 피벗을 찾아 행을 교환할지 |
| `verbose` | `False` | 중간 과정을 출력할지 |

**호출할 때 값을 생략하면 기본값이 들어가요.**

```python
gauss_eliminate(A, b)
```

함수 안에서는 다음 값을 갖고 시작하는 셈이에요.

```python
pivoting = True
verbose = False
```

호출할 때 직접 바꿀 수도 있어요.

```python
gauss_eliminate(A, b, pivoting=False, verbose=True)
```

이번에는 함수 안에서 `pivoting`은 `False`, `verbose`는 `True`가 됩니다.

**이 이름에 특별한 기능이 내장된 건 아니에요. 기능은 우리가 `if` 안에 작성한 코드가 부여해요.**

```python
if pivoting:
    # 피벗을 찾고 행을 교환하는 코드
```

`if pivoting:`은 여기서는 “`pivoting`의 값이 참이면 아래 코드를 실행하라”는 뜻이에요.

마찬가지로:

```python
if verbose:
    print(augmented)
```

`verbose=True`이면 출력하고, `False`이면 건너뜁니다.

즉, **함수 정의에서 옵션을 만들고 → 호출할 때 값을 받고 → `if`로 실행 여부를 결정하는 구조**예요. 이름을 `show_steps`로 바꿔도 관련 코드를 함께 바꾸면 똑같이 작동합니다.

내 질문:
```
그럼 만약에 pivoting=false라고 해놓고 아래 함수가 if pivoting: 이면, 언제 이걸 true로 바꿀 수 있는거야
```

답:

**`if pivoting:`이 값을 `True`로 바꾸지는 않아요.** 현재 값을 확인하기만 해요.

기본값을 `False`로 정했더라도:

```python
def gauss_eliminate(A, b, pivoting=False):
    if pivoting:
        print("피벗팅 실행")
```

**호출할 때 `True`를 전달하면** 그 호출에서는 실행돼요.

```python
gauss_eliminate(A, b)                  # 기본값 False → 건너뜀
gauss_eliminate(A, b, pivoting=True)    # 전달한 값 True → 실행
```

함수 안에서 직접 값을 바꿀 수도 있어요.

```python
pivoting = True

if pivoting:
    print("피벗팅 실행")
```

하지만 이렇게 무조건 바꾸면 사용자가 `False`를 전달해도 실행되므로, 지금 함수에서는 **호출할 때 선택하도록 두는 게 맞아요.**

참고로 Python에서는 소문자 `false`가 아니라 **`False`, `True`**로 써야 합니다.

이제 **피벗 아래를 0으로 만드는 전진 소거**와 **해를 구하는 후진 대입**을 붙이면 완성이에요. 파일은 직접 수정하지 않을게요.

**1. 피벗 아래 원소를 0으로 만들어요.**

앞서 작성한 `for col in range(n):` 안에서, 피벗이 0인지 검사한 다음에 넣어요.

```python
        for row in range(col + 1, n):
            factor = augmented[row, col] / augmented[col, col]
            augmented[row] -= factor * augmented[col]

            steps.append(augmented.copy())

            if verbose:
                print(f"{col}번 피벗으로 {row}번 행 소거:")
                print(augmented)
```

`range(col + 1, n)`은 **피벗 행 바로 아래부터 마지막 행까지**예요.

예를 들어 현재 열에서 피벗이 `3`, 아래 원소가 `6`이면:

```python
factor = 6 / 3  # 2
```

아래 행에서 피벗 행의 2배를 빼므로 해당 원소는:

```text
6 - 2 × 3 = 0
```

이 됩니다. 우변까지 함께 바뀌도록 **첨가행렬의 행 전체**에 연산해요.

**2. 마지막 행부터 해를 구해요.**

전진 소거가 끝나면 이런 형태가 됩니다.

```text
[2  1  3 | 13]
[0  4  2 | 14]
[0  0  5 | 15]
```

마지막 식부터 보면:

```text
5z = 15          → z = 3
4y + 2z = 14     → y = 2
2x + y + 3z = 13 → x = 1
```

이것이 **후진 대입**이에요. 아래 코드는 `for col` 바깥에 작성합니다.

```python
    x = np.zeros(n)

    for row in range(n - 1, -1, -1):
        known = augmented[row, row + 1:n] @ x[row + 1:]
        x[row] = (augmented[row, n] - known) / augmented[row, row]
```

각 부분의 의미는 다음과 같아요.

- `range(n - 1, -1, -1)`: 마지막 행부터 0번 행까지 거꾸로 진행
- `augmented[row, row + 1:n]`: 현재 미지수 오른쪽의 계수들
- `x[row + 1:]`: 이미 구한 해들
- `known`: 이미 구한 해들이 현재 식에 기여하는 값
- `augmented[row, n]`: 첨가행렬의 마지막 열, 즉 우변

예를 들어 두 번째 식에서는 `known = 2 × z = 6`이므로:

```python
y = (14 - 6) / 4  # 2
```

가 됩니다. 마지막 행에서는 오른쪽 계수와 해가 비어 있으므로 `known`은 `0`이에요.

**전체 코드는 다음과 같아요.**

```python
def gauss_eliminate(A, b, pivoting=True, verbose=False):
    A = np.array(A, dtype=float, copy=True)
    b = np.array(b, dtype=float, copy=True)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A는 정사각행렬이어야 합니다.")

    n = A.shape[0]

    if b.shape != (n,):
        raise ValueError("b는 A의 행 개수와 같은 길이의 벡터여야 합니다.")

    augmented = np.column_stack([A, b])
    steps = [augmented.copy()]

    if verbose:
        print("초기 첨가행렬:")
        print(augmented)

    # 전진 소거
    for col in range(n):
        if pivoting:
            pivot_row = col + np.argmax(
                np.abs(augmented[col:, col])
            )

            if pivot_row != col:
                augmented[[col, pivot_row]] = augmented[[pivot_row, col]]

                steps.append(augmented.copy())

                if verbose:
                    print(f"{col}번 행과 {pivot_row}번 행 교환:")
                    print(augmented)

        if augmented[col, col] == 0:
            raise ValueError(
                "현재 피벗이 0이므로 소거를 진행할 수 없습니다."
            )

        for row in range(col + 1, n):
            factor = augmented[row, col] / augmented[col, col]
            augmented[row] -= factor * augmented[col]

            steps.append(augmented.copy())

            if verbose:
                print(f"{col}번 피벗으로 {row}번 행 소거:")
                print(augmented)

    # 후진 대입
    x = np.zeros(n)

    for row in range(n - 1, -1, -1):
        known = augmented[row, row + 1:n] @ x[row + 1:]
        x[row] = (augmented[row, n] - known) / augmented[row, row]

    return x, steps
```

작성 후에는 간단한 문제로 확인해 보세요.

```python
A = np.array([
    [2, 1],
    [1, 3],
], dtype=float)

b = np.array([5, 5], dtype=float)

x, steps = gauss_eliminate(A, b, pivoting=True, verbose=True)

print("해:", x)                     # [2. 1.]
print("검산:", np.allclose(A @ x, b))  # True
```

`x`에는 **구한 해**, `steps`에는 **초기 상태와 각 행 연산 후의 첨가행렬 복사본**이 들어갑니다.

---

## 4-1 가우스 소거법

내 질문:
```
04\_liner\_system에서  검증 절차에서 [FAIL]이 많이 뜨는데 뭐때문일까
```

코덱스 답:

현재 `vectors.py`와 노트북 검증 코드를 확인했어요. **여러 검증이 같은 함수에 의존해서, 몇 군데 오류가 많은 `[FAIL]`로 이어지고 있어요.** 파일은 수정하지 않았습니다.

**1. `gauss_eliminate()` — 들여쓰기 때문에 소거가 실행되지 않아요.**

현재 피벗 검사와 아래 행을 소거하는 반복문이 `for col` **바깥**에 있어요.

```python
for col in range(n):
    # 피벗 선택 ...

# 현재 이 부분이 바깥에 있음
if augmented[col, col] == 0:
    ...

for row in range(col + 1, n):
    ...
```

열 반복이 끝나면 `col = n - 1`이에요. 따라서 아래 반복문은:

```python
range(n, n)
```

이 되어 **한 번도 실행되지 않습니다.** 원래 행렬을 소거하지 않은 채 후진 대입하니 해도 잘못 나와요.

올바른 들여쓰기 구조는 다음과 같아요.

```python
for col in range(n):
    if pivoting:
        # 피벗 선택
        # 필요한 경우 행 교환

    # 피벗이 0인지 검사

    for row in range(col + 1, n):
        # 아래 행 소거
        # steps에 기록

# 모든 열의 소거가 끝난 뒤 후진 대입
```

또한 **행 교환 조건도 `if pivoting:` 안에** 있어야 해요. 지금은 바깥에 있어서 `pivoting=False`일 때 정의되지 않은 `pivot_row`를 사용하게 됩니다.

변수명 오타도 두 곳 있어요.

```python
pivt_row       # → pivot_row
augneted.copy() # → augmented.copy()
```

이 오타는 행 교환이 필요한 경우 `NameError`를 발생시켜요.

**2. `inverse_gauss_jordan()` — 피벗을 1로 만드는 코드가 빠졌어요.**

현재 주석만 있고 실제 나눗셈이 없어요.

```python
#피벗 행 전체를 나눠서 피벗을 1로 만들기
for row in range(n):
```

주석 아래, `for row` 앞에 필요한 코드는:

```python
pivot = augmented[col, col]
augmented[col] /= pivot
```

입니다. 지금은 왼쪽을 대각행렬로 만들 뿐 **단위행렬로 만들지 않아서**, 오른쪽을 그대로 반환하면 역행렬이 아니에요. 그래서 역행렬 관련 검증이 연이어 실패할 수 있습니다.

**3. `row_echelon()` — 3×3에 고정되어 있어 rank 검증에 문제가 있어요.**

현재 반복 범위가 모두:

```python
range(3)
```

으로 되어 있어요. 하지만 노트북은 **3×4 첨가행렬 `[A|b]`의 rank도 검사**합니다. 마지막 열에 새로운 피벗이 있는 모순 케이스를 현재 코드가 확인하지 못해요.

또한 피벗을 항상 `q[i, i]`에서 찾으면, 중간에 피벗 없는 열이 있을 때 문제가 생깁니다. 이 함수는 **현재 피벗 행과 탐색 중인 열을 별도로 관리**하도록 수정해야 해요.

우선 **`gauss_eliminate()`의 오타와 들여쓰기부터** 고치는 게 좋아요. 수정 후에는 저장하고 **노트북 커널을 재시작한 다음 위에서부터 다시 실행**하세요. 기존에 import한 함수나 계산 결과가 남아 있으면 수정 전 결과로 검증할 수 있어요.

수정 후:

이번에는 수정 내용이 반영됐어요. 직접 실행해 보니:

- 가우스 소거 해: **`[2, -1, 3]` — 정상**
- 소거 기록: **4개이고 마지막 행렬이 상삼각 — 정상**
- 역행렬: **NumPy 결과와 일치 — 정상**

다만 **`pivoting=False`일 때는 아직 오류가 나요.**

현재 구조는:

```python
if pivoting:
    pivot_row = ...

if pivot_row != col:
    ...
```

`False`이면 `pivot_row`를 만들지 않았는데 아래에서 사용하기 때문이에요.

**행 교환 블록 전체를 `if pivoting:` 안으로 한 단계 들여쓰세요.**

```python
    for col in range(n):
        if pivoting:
            pivot_row = col + np.argmax(np.abs(augmented[col:, col]))

            if pivot_row != col:
                augmented[[col, pivot_row]] = augmented[[pivot_row, col]]

                steps.append(augmented.copy())

                if verbose:
                    print(f"{col}번 행과 {pivot_row}번 행 교환:")
                    print(augmented)

        # 이 아래는 pivoting=False여도 실행해야 하므로 현재 깊이 유지
        if augmented[col, col] == 0:
            raise ValueError(
                "현재 피벗이 0이므로 소거를 진행할 수 없습니다."
            )
```

소거 반복문과 후진 대입은 이번에 잘 고쳤어요.

그리고 **`row_echelon()`은 아직 `range(3)`으로 고정**되어 있어서, 앞서 설명한 첨가행렬의 rank 문제는 남아 있어요. 먼저 위 들여쓰기를 고치고, 다음에 그 함수를 함께 수정하면 됩니다. 파일은 제가 수정하지 않았어요.

다시 수정 후:

확인했어요. **`pivoting=True`와 `False` 모두 예제의 해 `[2, -1, 3]`을 정상적으로 구해요.**

이제 남은 **`row_echelon()`의 rank 문제**를 함께 고쳐봐요. 파일은 수정하지 않을게요.

현재 코드의 핵심 문제는 다음 부분이에요.

```python
for i in range(3):
    # q[i, i]에서 피벗 찾기
```

여기서는 행과 열을 같은 `i`로 움직여요. 하지만 **피벗이 없는 열을 건너뛸 때는 열만 이동하고 행은 그대로 있어야** 합니다.

예를 들어:

```text
[0  1  2]
[0  0  3]
[0  0  0]
```

첫 번째 열에는 피벗이 없어요. 다음 피벗은 **0번 행, 1번 열**에서 찾아야 하죠. 현재 방식은 바로 `q[1, 1]`로 이동해서 그 피벗을 놓칩니다.

그래서 두 변수를 따로 사용해야 해요.

```python
row = 0               # 다음 피벗을 놓을 행
for col in range(n):  # 살펴보는 열
```

첫 준비 부분은 이렇게 바꾸면 돼요.

```python
def row_echelon(M):
    q = np.array(M, dtype=float, copy=True)

    if q.ndim != 2:
        raise ValueError("2차원 행렬이어야 합니다.")

    m, n = q.shape
    pivots = []
    swaps = 0
    row = 0
```

- `m`: 행 개수
- `n`: 열 개수
- `row`: 다음 피벗을 배치할 행
- `pivots`: 피벗이 있는 **열 번호**를 기록할 리스트
- `swaps`: 행 교환 횟수

`m, n = q.shape`로 크기를 읽으면 **3×3 계수행렬과 3×4 첨가행렬을 모두 처리**할 수 있어요. 다음에는 이 아래에 열을 순회하면서 피벗을 찾는 코드를 붙이면 됩니다.

재 수정 후:

**방금 추가한 준비 부분은 맞아요.** `m, n = q.shape`와 `row = 0`까지 잘 작성했어요.

다만 아래에 **기존 반복문이 그대로 남아 있어서 함수 전체는 아직 수정 중**인 상태예요.

```python
pivots = []  # 위에서 이미 만들었으므로 중복
swaps = 0   # 이것도 중복
for i in range(3):
    ...
```

이 두 번째 `pivots = []`부터 기존 반복문 끝까지를 지우고, 그 자리에 새 반복문을 작성하면 됩니다. 맨 아래의 `return q, pivots, swaps`는 유지하세요.

다음 단계인 **피벗 선택 부분**은 이렇게 시작해요.

```python
    for col in range(n):
        if row >= m:
            break

        pivot_row = row + np.argmax(np.abs(q[row:, col]))

        if abs(q[pivot_row, col]) <= 1e-12:
            continue
```

각 줄을 설명하면:

- `for col in range(n)`: 마지막 열까지 모두 확인해요. 첨가행렬의 우변 열도 포함됩니다.
- `if row >= m`: 모든 행에 피벗을 배치했다면 끝내요.
- `q[row:, col]`: 현재 피벗 행부터 아래에서 후보를 찾습니다.
- `<= 1e-12`: 후보 중 가장 큰 값도 거의 0이면, 이 열에는 피벗이 없다고 판단해요.
- `continue`: **`row`는 그대로 두고 다음 열로 이동**해요.

여기서 `1e-12`는 계산 오차로 남은 아주 작은 값을 0으로 취급하기 위한 기준이에요.

이 부분 다음에 **행 교환 → 아래 행 소거 → `row += 1`**을 붙이면 완성됩니다. 파일은 제가 수정하지 않았어요.

재수정 후:

확인했어요. **아직 기존 코드가 섞여 있고, 오타 두 곳이 남아 있어요.** 실제 실행에서도 행 교환 시 `NameError`, 영행렬에서는 0으로 나누는 문제가 나왔습니다. 파일은 수정하지 않았어요.

**1. `<-`를 `<=`로 바꿔야 해요.**

현재:
```python
if abs(q[pivot_row, col]) <- 1e-8:
```

이건 Python에서 **“절댓값이 음수 `-1e-8`보다 작은가?”**로 해석돼 항상 거짓이에요.

```python
if abs(q[pivot_row, col]) <= 1e-8:
    continue
```

**2. 행 교환 코드에 변수명 오타가 있어요.**

현재:
```python
q[[row, pivot_row]] = q[[pivot, row]]
```

`pivot`이 아니라 `pivot_row`예요.

```python
q[[row, pivot_row]] = q[[pivot_row, row]]
```

**3. 기존 반복문 두 개는 제거해야 해요.**

현재 남아 있는:

```python
for i in range(3):
    ...
```

와 마지막의:

```python
for row in range(i + 1, 3):
    ...
```

는 이전 구현이에요. 새 반복문과 함께 실행하면 행 연산이 중복되고, `row` 값도 덮어써집니다.

헷갈리지 않게 **함수 전체의 올바른 들여쓰기**를 보여줄게요. 현재 `row_echelon`을 아래와 비교해서 정리하세요.

```python
def row_echelon(M):
    q = np.array(M, dtype=float, copy=True)

    if q.ndim != 2:
        raise ValueError("2차원 행렬이어야 합니다.")

    m, n = q.shape
    pivots = []
    swaps = 0
    row = 0

    for col in range(n):
        if row >= m:
            break

        pivot_row = row + np.argmax(np.abs(q[row:, col]))

        if abs(q[pivot_row, col]) <= 1e-8:
            continue

        # 행 교환
        if pivot_row != row:
            q[[row, pivot_row]] = q[[pivot_row, row]]
            swaps += 1

        pivots.append(col)

        # 피벗 아래 소거
        for r in range(row + 1, m):
            factor = q[r, col] / q[row, col]
            q[r] -= factor * q[row]
            q[r, col] = 0.0

        row += 1

    return q, pivots, swaps
```

**`row += 1`은 `for r` 바깥이면서 `for col` 안쪽**, **`return`은 두 반복문 바깥**인 점을 확인하세요.


수정 후:

**들여쓰기와 반복문 구조는 이제 맞아요!** 다만 행 교환 줄에 오타 하나가 아직 남아 있어요.

현재:
```python
q[[row, pivot_row]] = q[[pivot, row]]
```

수정:
```python
q[[row, pivot_row]] = q[[pivot_row, row]]
```

오른쪽의 **`pivot` → `pivot_row`**만 바꾸면 됩니다. 지금은 행 교환이 필요한 경우 `NameError`가 나요.

실행해서 확인한 나머지 결과는 정상이었어요.

- 피벗 없는 열을 건너뛰는 rank 계산: 통과
- 영행렬의 rank가 0: 통과
- 모순이 있는 3×4 첨가행렬의 rank가 3: 통과
- 과제 행렬의 행렬식: `42`
- 역행렬: NumPy 결과와 일치
- 가우스 소거: 피벗팅 여부 모두 `[2, -1, 3]`

그 한 줄을 고쳐 저장한 뒤, **노트북 커널을 재시작하고 위에서부터 다시 실행**해 보세요. 파일은 제가 수정하지 않았어요.

---

### [FAIL] 메세지 수정

원인을 찾았어요. **이번에는 `rank()`가 아니라, 노트북의 `b_bad`와 `b_ok` 값이 반대로 되어 있어요.**

현재 계수행렬은:

```python
A_dep = np.array([
    [1.0, 2.0, 3.0],
    [3.0, 6.0, 9.0],  # 첫 번째 행의 3배
    [1.0, 1.0, 1.0],
])
```

두 번째 식의 왼쪽이 첫 번째 식의 **3배**이므로, 모순이 없으려면 **우변도 3배**여야 해요.

그런데 현재 작성한 값은:

```python
b_bad = np.array([1.0, 3.0, 1.0])  # 실제로는 모순 없음
b_ok = np.array([1.0, 2.0, 1.0])   # 실제로는 모순 있음
```

따라서 다음처럼 바꾸세요.

```python
b_bad = np.array([1.0, 2.0, 1.0])  # 2 != 3 × 1 → 모순
b_ok = np.array([1.0, 3.0, 1.0])   # 3 == 3 × 1 → 모순 없음
```

왜 그런지 식으로 보면, `b_bad`는:

```text
 x + 2y + 3z = 1
3x + 6y + 9z = 2
```

첫 번째 식의 3배를 두 번째 식에서 빼면 **`0 = -1`**이 되므로 해가 없어요.

수정 후 예상 결과는:

| 입력 | rank(A_dep) | rank([A_dep｜b]) | 판정 |
|---|---:|---:|---|
| `b_bad` | 2 | 3 | 해 없음 |
| `b_ok` | 2 | 2 | 해 무한 |

현재 주석의 **“2행은 2여야 하는데”도 “2행의 우변은 3이어야 하는데”**로 고치면 됩니다. 이 입력 셀을 실행한 뒤 4-2 검증 셀을 다시 실행하세요. 파일은 수정하지 않았어요.

---

### 4-3 행렬식과 역행렬 - 그리고 det ~ 0의 위험

아래 내용을 각 빈칸에 넣으면 돼요.

**여인수 공식 관점**
> 역행렬 공식에는 det(A)로 나누는 항이 있어 주의가 필요하다. 다만 분자인 여인수도 함께 변하므로, det가 작다는 이유만으로 계산이 불안정하다고 단정할 수 없다.

**소거 관점**
> 작은 피벗으로 나누면 중간 계산값이 커질 수 있고, 이후 뺄셈에서 유효숫자가 손실되어 오차가 커질 수 있다.

**스케일 실험에서 관찰한 것**
> A와 b에 같은 스케일을 곱하자 행렬식은 크게 작아졌지만, 조건수는 약 4.215로 유지되었고 해의 상대오차도 약 10⁻¹⁶ 수준으로 유지되었다. 따라서 작은 행렬식이 반드시 부정확한 해를 의미하지는 않는다.

**실무 판정 기준과 그 의미**
> 행렬식의 절댓값만 보지 않고 조건수를 확인한다. 조건수가 클수록 작은 입력 오차가 해의 큰 변화로 이어질 수 있으므로, 입력 오차와 필요한 정확도를 함께 고려해야 한다.


