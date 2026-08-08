# TIL 작성 방법

## *제목 작성 방법*
'#'의 개수마다 제목의 사이즈가 달라진다.
*TIP: 1개와 2개일때는 수평선이 가로질러진다.

예)
# 제일 큰 제목 - # 1개 
## 두 번째 큰 제목 - ## 2개
### 세 번째 큰 제목 - ### 3개
#### 더 작은 제목 - #### 4개

**굵게**
*이탤릭*
~~취소선~~


### Bulletin 작성 방법
- bulletin으로 인식하는 방법 : - 작성내용
    - 하위 bulletin으로 인식하는 방법 : 들여쓰기하고 - 작성내용


### 글씨에 링크 다는 방법
[괄호 안에 제목을 넣고](둥근 괄호 안에 현재 폴더보다 아래면 바로 아래의 폴더부터 선택하여 위치를 정한다. 그리고 마지막으로 README.md를 쓴다.)
예)
####[제목](하위폴더/README.md)


## java 언어일때의 코드 작성 방법
#### '''java          <-- java 코드가 작성 전 작성하고 
#### 코드 내용         <-- 코드 내용을 담고
#### '''              <-- 닫는다

```java
#작성내용
public class JobBuilderFactory {

    private JobRepository jobRepository;

    public JobBuilderFactory(JobRepository jobRepository) {
        this.jobRepository = jobRepository;
    }
}
```


## python 언어일때의 코드 작성 방법
#### '''python        <-- phython 코드가 작성 전 작성하고 
#### 코드 내용         <-- 코드 내용을 담고
#### '''              <-- 닫는다

```python
#작성내용
import numpy as np

a = np.array([1, 2, 3])

print(a)
```


## Bath 언어일때의 코드 작성 방법
#### '''bash          <-- bash 코드가 작성 전 작성하고 
#### 코드 내용         <-- 코드 내용을 담고
#### '''              <-- 닫는다

```bash
#작성내용
cd TIL
mkdir Git-manual
```
