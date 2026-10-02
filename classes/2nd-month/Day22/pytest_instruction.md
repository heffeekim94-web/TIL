## pytest 실행 방법
date: 2026 Sept. 2, Wednesday 

**pytest**를 사용하는 기본적인 흐름은 약속된 규칙에 맞춰 파일과 함수 이름을 짓고, `assert` 문으로 조건을 확인한 뒤, 터미널에서 명령어로 한 번에 실행하는 방식입니다.

[과제 문서](https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C3_%EC%A2%8C%ED%91%9C%EB%B3%80%ED%99%98_%EC%88%98%ED%95%99%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC.md)의 환경을 기준으로 작성하고 실행하는 3단계를 보여드릴게요.

**1. 파일 및 함수 이름 규칙 (Naming)**
pytest가 테스트 코드를 자동으로 찾아내게 하려면 반드시 이름 규칙을 지켜야 합니다.

* **파일 이름:** `test_`로 시작해야 합니다. (예: `tests/test_rotation.py`)
* **함수 이름:** 파일 내부의 함수 이름도 `test_`로 시작해야 합니다. (예: `def test_determinant_is_one():`)

**2. assert 문으로 검증하기 (Assertion)**
테스트 함수 안에서는 파이썬의 `assert` 키워드를 사용해 "이 수식이나 결과가 무조건 참(True)이어야 한다"고 선언합니다. 코드가 실행될 때 이 조건이 참이면 조용히 통과(PASS)하고, 거짓이면 테스트가 실패(FAIL)하며 어디서 틀렸는지 상세한 에러를 보여줍니다.

```python
# tests/test_rotation.py 파일 내부 예시

import numpy as np
# 내가 만든 회전 함수를 불러옵니다
from src.rotation import rot_z 

def test_determinant_is_one():
    # 1. 검증할 상황을 만듭니다 (z축으로 90도 회전하는 행렬)
    matrix = rot_z(np.pi / 2)
    
    # 2. 실제 결괏값을 계산합니다 (행렬식 계산)
    det = np.linalg.det(matrix)
    
    # 3. assert로 행렬식이 1과 같은지 확인합니다 
    # (수치 해석 과제이므로 부동소수점 오차를 고려해 np.isclose 사용)
    assert np.isclose(det, 1.0)

```

**3. 터미널에서 실행하기 (Execution)**
코드를 저장한 뒤, 터미널(또는 명령 프롬프트)을 열고 폴더 최상단에서 아래 명령어를 입력합니다.

```bash
pytest -v

```

* `pytest`: 폴더 내의 모든 `test_` 파일을 뒤져 테스트 함수를 전부 알아서 실행합니다.
* `-v` (verbose): 어떤 테스트 함수가 통과(PASSED)했는지, 실패(FAILED)했는지 한 줄씩 상세하게 결과를 출력해 줍니다. 과제 문서에서도 테스트가 실패하는 것을 잡아내는지 확인하기 위해 이 `-v` 옵션을 켠 전수 통과 화면을 요구하고 있습니다.

즉, 과제에서 요구하는 pytest 작성이란 "내가 직접 짠 수학 함수(회전 행렬 등)에 값을 넣었을 때, 이론적인 수학 성질(행렬식이 1인지, 직교하는지 등)을 정확히 만족하는지 `assert`로 깐깐하게 확인하는 자동 검사기를 만드는 것"입니다.
