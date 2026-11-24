Date: 2026 Nov 23, Monday

## 오늘 배운 것
- (강의) Attention = softmax(QKᵀ / √d_k) V. Q 로 각 K 와의 유사도를 재고, 그 비율만큼 V 를 섞어 가져온다
- (강의) Q · K · V 는 같은 입력 X 에 서로 다른 학습 행렬 Wq · Wk · Wv 를 곱해 만든다. '나를 나타내는 일' 과 '단서를 찾는 일' 이 다르기 때문
- (강의) √d_k 로 나누는 건 차원이 커질수록 내적이 커져 softmax 가 쏠리는 걸 막기 위해서다
- (강의) 위치 정보는 순서를, causal mask 는 참고 범위 (현재 + 과거) 를 정한다. 마스크 자리는 -∞ → 가중치 0
- (강의) 헤드는 Attention 한 번, 블록은 Multi-head + FFN + 잔차 + LayerNorm. KV cache 는 과거 K · V 를 재사용하지만 메모리가 계속 는다
- (강의) RT-1 은 언어로 영상 특징을 조절 (FiLM) 하고 Transformer 로 행동 토큰을 낸다
- 파이썬에서 `k` 와 `K` 는 다른 변수다. 함수 안에 없으면 전역에서 찾아 쓴다. VS Code 에서 흐린 변수는 안 쓰인다는 신호
- `shape[-1]` 은 마지막 축 = 벡터 차원 (d_k). 입력 모양이 바뀌어도 항상 맞다



<br>

## 오늘 한 것 

- [Transformer · Attention 일지 (11/23)](attention_log.md)
- 11강 Transformer 와 Attention (23장) 수업
- 실습 ① 을 [KQV.py](KQV.py) 로 짜서 세 조건 (q 바꾸기 · 둘째 Key 가리기) 실행
- 에러 · 실수 고치기, 코드 한 줄씩 이해



<br>

## 문제점
- `e_x.sum(e_x)` 에서 `TypeError`
- print 에 `f` 가 빠져 `{ }` 가 set 이 됨
- 반환 순서와 받는 순서가 반대
- 매개변수 `k` 를 안 쓰고 전역 `K` 를 씀



<br>

## 해결 방법

- `e_x.sum()` 으로 수정
- f-string, 반환 순서 맞춤
- `k` 는 13번 줄을 `q @ k.T` 로 바꿔야 함 (아직 안 바꿈)



<br>

## 결과

- q = [1, 0] → weights [0.670, 0.330], q = [0, 1] → [0.330, 0.670], 둘째 Key 가림 → [1, 0] · output [2, 0]
- 세 조건 모두 가중치 합 1.0



<br>

## 느낀 점

- 이해는가는데 무슨 계산법들이 조금은 헷갈린다.. 어떤식으로 AI가 돌아가는지를 배우는데.. 얼추 알긴 하지만 다시 설명하려니 어렵다.. 다시 설명하기 위한 공부가 진짜 공부겠지?



<br>

## 할 일

- `KQV.py` 13번 줄 고치기
- 실습 ② 세 토큰 causal Attention 손계산 + 코드
- 미니 퀴즈 풀기, Attention Is All You Need · RT-1 그림 읽기
