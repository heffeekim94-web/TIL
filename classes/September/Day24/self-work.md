Date 2026 Sept 4, Friday

continue from [Day23](../Day23/self-work.md)

## rotation.py axis_angle_from_matrix()

`np.linalg.eig` 함수는 입력된 정사각행렬의 고유값(eigenvalues)과 고유벡터(eigenvectors)를 튜플 형태로 반환합니다.

반환되는 값의 구체적인 형태와 구조는 다음과 같습니다.

### 반환 형태

```python
eigenvalues, eigenvectors = np.linalg.eig(R)

```

1. **`eigenvalues` (첫 번째 반환값)**
* 형태: `(N,)` 크기의 1차원 배열 (`numpy.ndarray`)
* 행렬의 고유값들을 담고 있습니다. (입력 행렬이 $N \times N$일 때 크기는 $N$입니다.)
* 실수 행렬이라 하더라도 고유값이 복소수(`complex`)로 계산될 수 있습니다.


2. **`eigenvectors` (두 번째 반환값)**
* 형태: `(N, N)` 크기의 2차원 배열 (`numpy.ndarray`)
* 열 벡터(column vector)들이 고유벡터를 구성합니다. 즉, 반환된 행렬의 `i`번째 열인 `eigenvectors[:, i]`가 `eigenvalues[i]`에 대응하는 고유벡터가 됩니다.
* 고유값 방정식 $R v = \lambda v$를 만족하도록 정규화되어 반환됩니다.


---

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
    
    # 단위 회전축 구하기
    v = np.array([
        [R(3,2)-R(2,3)]
        [R(1,3)-R(2,1)]
        [R(2,1)-R(1,2)], dtype=float
    ])
    k = (1/2*np.sin(theta))*v

    return k, theta
```

---

이제 다시 vector로 돌아가 마무리 해보련다..


## vector.py

### 1-2
`1-2`번 노트북의 TODO: (2)는 영벡터를 정규화(`zero / norm`)했을 때 생기는 `nan`(Not a Number) 값이 **코드 내의 비교문(`==`)이나 `assert` 문을 어떻게 무력화하는지 직접 눈으로 확인하고 출력**하라는 뜻입니다.

파이썬과 넘파이(NumPy)에서 `nan`은 수학적으로 정의되지 않은 값이기 때문에 자기 자신과 비교(`nan == nan`)해도 항상 `False`가 나옵니다.

이 때문에 영벡터 처리를 안 해주고 넘어가면 코드가 에러를 뿜으며 멈추는 게 아니라, `nan`이라는 시한폭탄 같은 값이 조용히 전달되면서 `assert` 문이나 조건문 검사를 에러 없이 유유히 통과해 버리는 위험한 상황(Silent Failure)이 발생한다는 점을 체감하기 위한 단계입니다.

해당 셀의 `TODO: (2)` 부분에 아래처럼 코드를 채워 넣으시면 의도하신 대로 동작합니다.

```python
# TODO: (2) raw가 이후 비교/전파에서 어떻게 동작하는지 확인해 출력하세요.
print("raw[0] == raw[0]       :", bool(raw[0] == raw[0]))
print("np.isnan(raw[0])       :", bool(np.isnan(raw[0])))
print("assert 통과 여부 (nan):")
try:
    assert raw[0] == 1.0, "1.0이어야 하는데 nan이라서 실패함"
    print("  -> assert 통과됨!")
except AssertionError as e:
    print(f"  -> AssertionError 발생: {e}")

```

이렇게 하면 `nan == nan` 비교가 `False`를 뱉기 때문에 `assert` 문이 오작동하거나 값을 제대로 잡지 못한다는 것을 확실하게 확인하실 수 있습니다.

파이썬의 `try-except` 문은 쉽게 말해 "일단 코드를 실행해 보고, 에러(예외)가 나면 프로그램이 죽는 대신 이렇게 대처해라"라고 지시하는 방어 장치입니다.

지금 문제에서 보신 `except` 코드를 한 줄씩 뜯어보면 이렇게 이해하시면 됩니다.

```python
try:
    # 에러가 날 수 있는 위험한(?) 코드
    assert raw[0] == 1.0, "1.0이어야 하는데 nan이라서 실패함"
    print("  -> assert 통과됨!")
except AssertionError as e:
    # try 안에서 'AssertionError'라는 이름의 에러가 발생하면
    # 프로그램 전체를 멈추지 말고, 이 안으로 들어와서 아래를 실행해라!
    print(f"  -> AssertionError 발생: {e}")

```

### 각 단어의 의미

1. **`try:`**
* *"일단 이 안에 있는 코드를 실행해 봐."*
* `assert raw[0] == 1.0` 코드는 `raw[0]`이 `1.0`이 아니기 때문에(nan이라서) 원래라면 `AssertionError`를 내뿜고 프로그램이 강제 종료되어야 정상입니다.


2. **`except AssertionError as e:`**
* *"만약 실행하다가 **`AssertionError`** (단정문 실패 에러)가 터지면, 코드를 멈추지 말고 내가 잡아서 처리할게."*
* 뒤에 붙은 `as e`는 발생한 **에러 메시지("1.0이어야 하는데 nan이라서 실패함")를 `e`라는 변수에 담아두겠다**는 뜻입니다.


3. **`print(f"  -> AssertionError 발생: {e}")`**
* 에러가 나서 프로그램이 뻗는 대신, 우리가 지정해 둔 이 `print` 문을 실행하고 무사히 다음 단계로 넘어갑니다.



### 왜 이 코드를 썼을까요?

영벡터를 정규화하면 `nan`이 되는데, 이 `nan`이 `assert` 문을 통과하는지(`AssertionError`가 안 나고 그냥 넘어가 버리는지) 테스트해 보고 싶었던 것입니다.

만약 `except`로 잡지 않았다면 에러 화면이 붉게 뜨며 노트북 실행이 멈췄겠지만, `try-except`로 감싸 두었기 때문에 에러가 발생한 상황을 안전하게 가로채서 `-> AssertionError 발생: ...`이라는 문구로 깔끔하게 화면에 출력하고 다음 코드로 이어갈 수 있는 것입니다.

코드에서 사용된 `with np.errstate(invalid="ignore", divide="ignore"):`는 넘파이(NumPy) 연산을 할 때 수학적으로 정의되지 않는 상황(0으로 나누기, `nan` 발생 등)에서 뜨는 경고 메시지를 일시적으로 차단(무시)해 주는 문맥 관리자(Context Manager)입니다.

전체 코드 블록과 함께 뜯어보면 이렇습니다.

```python
with np.errstate(invalid="ignore", divide="ignore"):
    raw = zero / np.sqrt(zero @ zero)

```

### 각 부분의 의미

1. **`np.errstate(...)`**
* 넘파이가 연산 도중 발생하는 에러나 경고(Floating-Point Error)를 어떻게 처리할지 설정하는 도구입니다.
* **`invalid="ignore"`**: 숫자로 표현할 수 없는 결과(`nan`, Not a Number)가 나올 때 발생하는 경고를 무시합니다. (영벡터를 정규화하면 `0 / 0` 꼴이 되어 `nan`이 발생합니다.)
* **`divide="ignore"`**: 0으로 나누기(`divide by zero`)가 발생할 때 뜨는 경고를 무시합니다.


2. **`with` 문**
* 파이썬에서 `with` 블록을 사용하면, **그 블록 안에서만** 일시적으로 설정을 적용하고 블록을 빠져나오면 원래 상태로 되돌립니다. 즉, 저 아랫줄에 있는 정상적인 벡터 계산에서는 경고가 다시 정상적으로 작동하도록 안전하게 보호해 주는 역할을 합니다.


3. **왜 이 코드를 썼을까요?**
* 영벡터를 나누면 어차피 `nan`이 나올 걸 우리(개발자)가 이미 알고 테스트하는 상황입니다.
* 이때 파이썬 콘솔 창에 빨간색 `RuntimeWarning` 경고 글씨가 주렁주렁 뜨면 가독성도 나쁘고 에러가 난 것처럼 혼란스러울 수 있기 때문에, "경고는 잠시 꺼둘 테니, 내부적으로 `nan` 값이 어떻게 만들어지고 전파되는지 조용히 확인만 하겠다"는 의도로 사용된 것입니다.