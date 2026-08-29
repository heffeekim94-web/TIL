date 2026 aug 26, Wednesday

과제 설명 웹사이트: https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C3_%EC%A2%8C%ED%91%9C%EB%B3%80%ED%99%98_%EC%88%98%ED%95%99%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC.md

건산용 코드 

별도 첨부파일 없음

부동소수점??

노트북 문양마다.. 제공 예정

손으로 계산하는 값..
사진으로 올려도 됨

한번에 설치할 수 있는 파일 slack 참조

```
$ nano requirements.txt
```

안의 내용은:

```
# Lv.1 모듈 ③ — 로봇 좌표 변환 수학 라이브러리
#
# 설치 (Windows PowerShell)
#   python -m venv .venv
#   .\.venv\Scripts\Activate.ps1
#   python -m pip install --upgrade pip
#   pip install -r requirements.txt
#
# 설치 (macOS / Linux)
#   python3 -m venv .venv
#   source .venv/bin/activate
#   python -m pip install --upgrade pip
#   pip install -r requirements.txt

numpy>=1.24
matplotlib>=3.7
scipy>=1.10
pytest>=7.0
jupyterlab>=4.0

# ---------------------------------------------------------------------------
# 이 정답본을 실제로 실행·검증한 버전 (2026-08 기준)
#   Python 3.12.x / numpy 2.4.6 / scipy 1.15.3 / matplotlib 3.11.1
#   pytest 9.1.1 / jupyterlab 4.6.3 / pyzmq 26.2.0
#
# 노트북 재생성용(제출에는 불필요): jupytext, nbformat, nbconvert
#   pip install jupytext nbformat nbconvert
# ---------------------------------------------------------------------------
```
$ pip install -r requirements.txt

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
generate-parameter-library-py 0.7.5 requires typeguard, which is not installed.
```
- 종속성이 없이 설치 됨
- upgrade pip를 해야 하는데 
- 크게 문제되진 않을 예정

```
$ jupyter lab
```

3-1

numpy를 사용하지 않고 우선 해보고
numpy..

주석..처럼??

직접 구현..???

만드는걸로..

vectors

src/...py 파일안에 파이선 파일로 제출

## 문제 1

1-2번  문제 
- failtest를 해야 함.
- 거의 0도 0이라 여겨야 함

IEEE 754

---
### vectors.py

코드를 작성한다는 것은 우선 구분을 해야 한다

어떤 기능이 어디에 있는지를 한눈에 알아볼 수 있어야 한다

구조 설계를 잘해야 하는 것이 첫번째 목표

계산을 먼저 해봐야 어떤 코드를 기입해야 하는지 안다

```python
from __future__ import annotation   # 타이핑을 편하게 하기 위한것
import numpy as np  # np로 줄여서 쓸 수 있다는 것


__all__ = [         # 목록들을 만드는 것..
    "as_vector",    # 함수들
    "dot",
    "norm",

    .
    .

]

pivot_cols : list[int] = []

```

함수를 만드는 방법

```python

def dot(a,b) -> float:
    return a + b    # 들여쓰기 필수. 이 def 안의 내용을 저장하는 것. 
    # return 은 결과값을 출력으로 주문하는 것.
    # or 
    # c = a + b
    # return c 로도 할 수 있다.

```
- python 문법

```cpp
def dot(a,b) -> float{

}
```
- c++ 언어 문법

```python
np.ndim # 차원을 의미

a = as_vector(a)
b = as_vector(b)
# 를 
a, b= as_vector(a), as_vector(b)
# 로 쉽게 표현 할 수 있다

if a.shape != b.shape:
    raise ValueError(f"차원이 다릅니다: {a.shape} vs {b.shape}")
return float(np.sum(a*b))
```

대부분 `float`으로 전환한다.

나눗셈이 많아서..

가우스 소거법을 직접 계산해주는 numpy가 있는데 그런 간단한 것을 사용하지 말라는 것.

os 로 불러오기 가능 import를 위해서

system - 파일 - pass???

## 벡터


```python
def as_vector(v) -> np.ndarray:
    arr = np.array(v, dtype=float)
```


## norm

```python
float으로 전환

def dot에서 이미 곱하기를 했으니

def sqrt

# 정답은 아니니 참조
```


degrees: bool = True