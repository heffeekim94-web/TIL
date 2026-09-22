2026 Sept 22, Tuesday

---

프라임모터

지방경기기능대회

2인 1조 

같은 지역인 사람만 나갈 수 있음

[마이스터net](https://meister.hrdkorea.or.kr/sub/3/2/1/20160512110924569100_view.do)

출전??

나이제한 없음

상위권에 들어가면 국가대표

올림픽에 들어갈 수 있는데 그때는 나이제한

---

ncs

국가 능력 평가

[월드디카](www.studica.co)

---

lv2 모듈 1

로봇팔 안하기로 

---

오늘 할 것 

lv2 모듈 1 과제 1번

- rasberry pi랑 openCR을 연결해서 자동으로 작동하게 
- ssh - 아두이노 아이디를 사용 할 수 없음
- 아두이노 cni로 설치
- ssh 접속, 아두이노로 작동
    - ros2 로봇 다룰때는 이렇게 접속을 비추
    - 라즈베리 파이가 많이 뜨거워짐.
- openCR과 라즈베리파이 연결
    - 매뉴얼대로 연결 방법 적용
- opneCR을 어댑터로만 power 공급
- [어제](../Day35/class.md) 라즈베리 파이 ssh 연결해 둔 대로 진행 
    - ip address
---

vs code로 연결 방법
- 맨왼쪽 하단에 `><`아이콘을 누르고 
- ssh 접속
- `+` 새로운 호스트
- `ssh pa06@pa06.local` or `ssh pa06@10.2.12.156` or `ssh 호스트@ip주소`
    - ip 주소를 모르면 터미널창을 열어서 `ping 호스트이름.local -4`로 검색해서 나오는 ip 주소를 확인하기
    - 비번 입력하는 것 잊지 말기. 라즈베리 파이 구울때 설정한 비밀버ᇿ호.
- `/home/pa06`폴더에서 작업. `root`에서 파일을 관리하면 관리 잘 안됨. 

---

[실행 방법](https://github.com/SpartaPA/physicalai-lv2-assignments/blob/main/%EB%AA%A8%EB%93%881_%EC%9E%84%EB%B2%A0%EB%94%94%EB%93%9C%EC%A0%9C%EC%96%B4%EA%B8%B0%EC%B4%88/OpenCR_%EB%B9%8C%EB%93%9C_%EC%97%85%EB%A1%9C%EB%93%9C_%EA%B0%80%EC%9D%B4%EB%93%9C.md)

```bash
export BASE="$HOME/pa-opencr-build"                             //모델을 보내는 방법
set -o pipefail
mkdir -p "$BASE"/{bin,downloads,data,user,sketches,output}
sudo apt update
sudo apt install -y build-essential curl git python3-serial \
  gcc-arm-none-eabi libnewlib-arm-none-eabi \
  libstdc++-arm-none-eabi-newlib usbutils file
arm-none-eabi-g++ --version
sudo usermod -aG dialout "$USER"                                //등록을 하는 과정
```

<br>

```bash
cd "$BASE/downloads"
VER=1.5.1
ASSET="arduino-cli_${VER}_Linux_ARM64.tar.gz"                  //원하면 직접 빌드해서 작성 해도 ok
RELEASE="https://github.com/arduino/arduino-cli/releases/download"
curl -fL -o "$ASSET" "$RELEASE/v$VER/$ASSET"
curl -fL -o checksums.txt \
  "$RELEASE/v$VER/${VER}-checksums.txt"
grep "  $ASSET\$" checksums.txt | sha256sum -c -
```

<br>

```bash
git clone https://github.com/SpartaPA/physicalai-lv2-assignments.git \
  "$BASE/repo"
SOURCE=$(find "$BASE/repo" -type d -name opencr_position_p -print -quit)
test -n "$SOURCE" && test -f "$SOURCE/opencr_position_p.ino"
```
- pid id 바꾸기
- 속도는 고정이다
---

7.번 upload 전에 6.의 build를 한번더 하고 하기

---

ceggle?

json 나노???
- 팀당 1개

avac?

24시간 학습???


