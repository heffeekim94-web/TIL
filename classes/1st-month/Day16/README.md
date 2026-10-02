Date: 2026 Aug 25, Tuesday

# 과제 설명

과제 바꾼다

과제 3번
jupiter->py로 변경하는 것만. 

## 과제 1

```
sudo apt install systemd-udevd
```
```
$ ss -tlnp | grep :22
```

- listen
- 0.0.0.0 : 모든 ip에서 들어오는 것도 듣겠다.  
- 22번 부터


http : 80

https : 443 (암호화 ㅎ한것)

```
$ ssh pa@localhost
```
- 비밀번호
- 'Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-138-generic x86_64)' 내용이 뜨면 된 것.

```
$ systemctl status ssh
```
![alt text](<스크린샷 2026-08-25 09-39-38.png>)

- 상태 표시가 가능

과제 1이 끝난 것 

로봇 제어는 이렇게 하면 안됨

ip를 열어두면 누구든 들어올 수 있다는 뜻

ssh파일에 키파일이 있어야 접속이 가능하게 한다. 
아마존, 네이버 등에도 이런 서버 키가 있어야 들어갈 수 있게 되어 있다. 

aws
인스턴스 - 가상의 컴퓨터 
우분투 선택
키 페어 - 자물쇠의 비밀번호가 담긴 파일
키 페어 없이 진행하면 안됨
키 페어 - test를 우선 해볼 수 있음
키 페어 파일이 만들어짐
메모장으로 열어볼 수 있음
이 비밀번호가 없으면 컴터에 접속을 할 수 없음
인바운드 규칙에 0.0.0.0이 아니라 내 컴퓨터만 또는 내가 원하는 컴터만 지정 할 수 있고, 포트들만 지정할 수 있다. 

ssh-keygen -t ed25519
- 3번 엔터

cat .ssh/id_ed25519로 하면 

who
- 누가 내 우분투에 들어와있는지 볼 수 있다

echo \SSH_CONNECTION

echo $SSH_CONNECTION

ipconfig
- 자신의 ip를 볼 수 있다. 

pa@LAPTOP-0KC3V059 10.2.16.242
- 선생님 laptop

---
### 헤드리스 운용

$ ssh pa@localhost 'uname -a'

$ scp 파일 이름 pa@localhost(원격컴퓨터):/폴더위치/
- 어떤 작업을 하고 암호화한 파일을 넣어야 할때 scp를 사용한다. 


(없앰)

---

### 시리얼 장치

ls -l /dev/tty*
- /dev/tty : dev
- /dev/tty : dev 파일 안에 tty라는 파일이 있다라는 뜻
- usb 포트들을 의미함

```
$ mkdir -p ~/fake_sensors && cd ~/fake_sensors
```
- fake_sensor 파일을 만든다

<br>

```
$ truncate -s 10M lidar.img imu.img
```
- 10 메가 파일을 만드는 것

- 가상의 라이다 장치를 만든것 

<br>

```
$ sudo losetup -f --show lidar.img
$ sudo losetup -f --show imu.img
```
- loop가 순서대로 추가 된 대로 입력이 된다. 


<br>

```
$ udevadm info --attribute-walk /dev/loopN
```
- loop 번호를 끝에 수정해서 조회해 본다. 
- UDEV 규칙

<br>

두개의 값이 다른 값을 찾아서 loop/backing_file에 답안 기록
- 강의 3번에 설명이 자세히 있음. 

<br>

```
$ sudo nano /etc/udev/rules.d/99-robot-sensor.rules
```
- 룰을 만든다
- SUBSYTEM=="block"가는 룰

```
$ sudo udevadm control --reload-rules
```
- 룰이 적용 됐는지 확인

```
$ ls -l /dev/robot_*
```
- 룰을 적용한 대로 로봇이 있는가 보는 것
- CP2102 반도체가 USB포트에서 라이다로 연결해주는 장치.
- PID가 그 제품의 식별 번호

sudo losetup /dev/loo#
- 기존 설정을 해제하는 것

ls -d /dev/loop*
- 해제를 하는 것 

9/7일까지 과제 1 - 원격
privite으로 내 github에 저장

---

## 과제 2

[우선] turtlesim 깔기

과제 파일과 채점 조건을 잘 주시하기

정리되어 있는 대로만 문제를 풀어야 한다.

```
$ sudo apt install ros-humbel-turtlesim
```
- 프로그램이 깔려 있는지 없는지 알려준다 

```
sudo apt update
sudo apt install ros-humbel-turtlesim
```
- 업데이트 진행을 한다. 

최종 결과물 제출을을 zip파일이 아니라 ros_ws로 올리는 것으로 변경

1. 번과제

```
// stop_distance.cpp — 로봇의 제동(정지) 거리 계산
//
// 물리: 바퀴와 바닥 사이 마찰이 유일한 제동력이라고 보면
//   감속도 a = mu * g   (mu: 마찰계수, g: 중력가속도)
//   운동에너지 (1/2)m v^2 이 마찰일 (mu m g d) 로 모두 소모되어 정지하므로
//   d = v^2 / (2 * mu * g)
//
// 빌드: g++ -Wall -std=c++17 stop_distance.cpp -o stop_distance
// 실행: ./stop_distance <속도[m/s]> <마찰계수>
//   인자를 안 주면 값을 직접 입력받는다.

```

2. 번 과제..




할당이 제대로 됐는지 안됐는지를 볼 예정

5-9번 과제는 옵션 제출이지만 해보는 것을 추천 (사실상 필수)

10번 과제 
- 브로드캐스트 파일은 py c++ 상관 없음













