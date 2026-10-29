Date: 2026 Oct 28, Wednesday

## 오늘 배운 것
- [nvblox · Nav2 · 예측 카메라 정책 / 오늘 실습에서 배운 것](class.md)
- [강의](https://app.notion.com/p/nvblox-Nav2-40779696939580429389fdc0567a76fe)
- [수업 자료](https://docs.google.com/presentation/d/10B9z7mA8zPu8sN_ghsi8B1viEOsL84xXxQIRI4-yiZE/edit)




<br>

## 오늘 한 것 

- [비전 작업 일지 (10/28)](vision_log.md)
- 팀 실제 데이터를 영상 단위로 다시 나눔 (real_v4)
- 팀장님 새 합성 데이터(아크릴 반영)로 YOLO 2단계 학습
- 결과 보기 노트북 results_1028.ipynb · results_report.py
- 어두운 조명 포함 분리 real_v5 + 실제 데이터만 학습하는 노트북 준비
- pa06 SSH 접속 해결, 라이다 /scan 확인, TurtleBot3 Lyrical 소스 빌드
- 대화를 YOLO·터틀봇 두 세션으로 나누고 공용 기록 사용



<br>

## 문제점
- 팀 실제 데이터 split 에 같은 영상의 비슷한 프레임이 train·val·test 에 섞여 있었음
- 어두운 조명 영상(new_04)이 통째로 test 에 들어가 test 점수가 떨어짐
- 합성만 학습한 모델은 같은 색 물체끼리 모양을 헷갈림 (green_box → green_cyl 31%)
- pa06 IP 가 매주 바뀌어 SSH 접속이 안 됨
- Lyrical apt 에 TurtleBot3 bringup·node 가 없음, 빌드 중 SSH 먹통
- VS Code 에서 노트북 커널(venv)이 안 잡힘




<br>

## 해결 방법

- build_real_split.py 로 영상 하나를 통째로 한 split 에 배정
- 밝기를 재서 어두운 영상을 찾고, 시간 구간 6개로 잘라 train·test·train·train·val·train 배정, 경계 뒤 90프레임 버림
- 실제 사진을 섞은 2단계 학습 (실제 약 26%)
- arp-scan 으로 MAC 주소를 찾아 접속하는 ssh-pa06 함수
- ROBOTIS 소스를 ~/ninja_ws 에서 빌드 (.h→.hpp, QoS 인자 패치), VS Code Remote 끄고 -j1 로 빌드
- 커널 문제는 results_report.py 로 PNG 를 저장해서 우회


<br>

## 결과

- real_v4: train 490 / val 112 / test 47, real_v5: train 490(어두움 45) / val 68(2) / test 52(9)
- 실제 val mAP50: 합성만 0.834 → 합성+실제 0.961 (mAP50-95 0.793)
- 클래스별 mAP50: red_cyl 0.887(가장 낮음) ~ traffic_light 0.995
- pa06 라이다 /scan 10 Hz, TurtleBot3 description·node·bringup 빌드 (3분 37초)




<br>

## 느낀 점

- 




<br>

## 할 일

- real_only_1028.ipynb 실행: 실제만 학습 → test 밝음·어두움 비교
- 공정 비교가 필요하면 mix 도 real_v5 로 다시
- pa06 bringup → /odom·TF 확인, OpenCR 펌웨어 확인, 키보드 조종
- cartographer 지도 → Nav2, 아크릴 벽이 라이다에 찍히는지 확인
- VS Code 노트북 커널 문제 정리




