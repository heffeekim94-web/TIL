Date: 2026 Sept 04, Friday

module 4는 module 1,2,3 다 사용

LMS 기한은 언젠지 몰라서 
우선은 제출할 링크부터 복사 붙여놓는 방식을 추천

과제 마감일은 9월 7일 11:59PM

수료 과정에 필수 사항은 아니지만, 피드백을 받고싶다면 제출

KANT 제출 방법 설명 NOTION
링크: https://app.notion.com/p/teamsparta/KANT-3d02dc3ef51480c599c2c80fb53be7aa

제출 LMS 링크: https://bootcamp-lms.spartaclub.kr/kant/assignment-project/6a994aef9fe9342373c5a009?type=assignment&version=v2


template이 제공된 대로 제출

https://github.com/SpartaPA/physicalai-lv1-assignments/tree/main

lv1_module2_student
lv1_module3_student
lv1_module4_student

위 폴더 안에 구성 되어 있는 대로 하는게 좋음

---

### pose_lab 환경 구성 for jupyter

과제 안내 내용에 
https://github.com/SpartaPA/physicalai-lv1-assignments/blob/main/%EA%B3%BC%EC%A0%9C_%EC%95%88%EB%82%B4.md

☑ 커널이 Python (pose_lab) 으로 선택되어 있다

의 의미는 

우리가 .venv환경에서 jupyter를 실행하듯이 
pose_lab이라는 환경에서 jupyter를 실행해야 한다는 뜻이다. 

그러려면

```bash
$ python3 -m .venv venv
```
가 아닌 

```bash
$ python3 -m .venv pose_lab
```
이어야 한다. 

그런 다음 파일 위치를 확인하고 
```bash
$ python -c "import sys; print(sys.executable)"
```
- 파일 주소가 나온다

pose_lab 환경으로 활성화 한다
```bash
$ source pose_lab/bin/activate
```

그리고 다시 jupyter 설치
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

.ipybn파일을 jupyter에서 열람해 보면 kernel옵션창에서 Change Kernel...을 했을 때 

- Python3 pose_lab이라는 옵션이 있어야 된다는 것이고 
- 실행 탭의 오른쪽에도 Python3 (pose_lab)이라고 떠있어야 한다. 

아직 ipykernel 이라고 쓰여 있다면 

bash 창에 아래를 입력해 볼 것
```bash
$ python -m ipykernel install --user --name=pose_lab --display-name="Python (pose_lab)"
```
- vs code 환경에서의 코드

그러면 pose_lab에서의 환경에서 작성하고 있음을 보일 수 있다. 

왜 이런 환경을 만들어서 하는지는.. 다시 리뷰를 해야 할 것 같다..