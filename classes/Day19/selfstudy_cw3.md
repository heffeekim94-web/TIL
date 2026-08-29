Date 2026 Aug 28, Friday

vectors.py 코딩을 이어나간다. 

continue from [classwork](../Day17/classwork.md)

### row_echelon

내 코딩:
```python
def row_echelon(a,b,c) -> np.ndarray:
    a = vector(a)                           
    b = vector(b)
    c = vector(c)

    q = np.array([
        a,
        b,
        c
    ])

    row = 1
    i = 0
    
    while row <= 2 and i< 2:
        if q[i,i] == 0:
            for r in range(i+1,3):
                if q[r,i] != 0:
                    q[[i,r]] = q[[r,i]]
                    break

        while q[row,i] != 0:
            k = q[row,i] / q[i,i]
            q[row] = q[row] - k * q[i]
        
        if row < 2:
            row += 1

        elif row == 2 and i < 2:
            i += 1   
    return q
```
- 처음에는 아예 구조도 못짰다.. 이것도 chat gpt의 도움을 받아 적은거긴 한데 내가 시작한데서부터 차근차근 코드가 작동할 수 있는 원리로 이끌어줬다.

<br>

```python
def row_echelon(a, b, c) -> np.ndarray:
    a = vector(a)
    b = vector(b)
    c = vector(c)

    q = np.array([
        a,
        b,
        c
    ], dtype=float)
    # float으로 반환.

    # pivot 위치: 0 → 1
    for i in range(2):

        # pivot이 0이면 아래 행에서 0이 아닌 값을 찾아 교환
        if q[i, i] == 0:
            for r in range(i + 1, 3):
                if q[r, i] != 0:
                    q[[i, r]] = q[[r, i]]
                    break

        # 교환했는데도 pivot이 0이면 이 열에서는 제거 불가능
        if q[i, i] == 0:
            continue

        # pivot 아래의 행들을 하나씩 처리
        for row in range(i + 1, 3):
            if q[row, i] != 0:
                k = q[row, i] / q[i, i]
                q[row] = q[row] - k * q[i]

    return q
```
