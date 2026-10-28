Date: 2026 Oct 27, Tuesday

## 오늘 배운 것
- [cuVSLAM · 미로 주행 실습 · PPO 보상 설계](class.md)
- [강의](https://app.notion.com/p/cuVSLAM-4067969693958038a92df9d7d1685209)
- [수업 자료](https://docs.google.com/presentation/d/19UfjZpjlP2RR7iLeboQTa_h0JFBVk2P_-Yz-u_tQ-eA/edit)




<br>

## 오늘 한 것 

- [비전 작업 일지 (10/27)](vision_log.md)
- 신호등 사진 포함 내보내기 → 팀 실제 데이터에 합쳐 real_v2 생성
- 팀 YOLO 2단계 학습 (sim_pre → mix_ft, mix_ft_from_final)
- 새 URDF 릴리스(스워브) 정적 검사 · MuJoCo 로딩 · 뷰어 확인
- planning과 인지 토픽 합의 (v.2 유지, frame_id는 URDF 이름, ROS 2 Lyrical)
- spare 로봇(pa06) 접속 시도, 미로주행 실습 관찰기록표 엑셀
- 팀장님과 주행 영상 1개 촬영 · 라벨링



<br>

## 문제점
- 어제 신호등 라벨이 사진 없이 내보내져 학습에 쓸 수 없었음
- 시뮬만 학습한 모델(sim_pre)은 실제 사진 val mAP50 0.822에 그침
- mix_ft를 sim_pre가 끝나기 전 초반 가중치로 시작함
- 실제 val에 빨간 물체(red_cyl, red_box)가 없어 점수가 그 클래스를 반영하지 못함
- MuJoCo 뷰어에서 Reset하면 팔이 떨어지고, 명령 없이도 조향 관절이 돌아감
- 손목 카메라 frame_id가 v.2(camera_optical_frame)와 새 URDF(d435_cad_optical_proxy_frame)에서 달랐음
- pa06.local로 SSH 접속이 안 됨




<br>

## 해결 방법

- CVAT에서 Save images를 켜고 다시 내보내 real_v2를 만듦. 영상 단위로 train/val/test를 나누고 아래 18%는 회색으로 가림
- 실제 사진을 섞은 2단계 학습으로 mAP50 0.99까지 올림. sim_pre 최종 가중치로 한 번 더 돌려 비교
- 팔이 떨어지는 건 URDF 로더가 모터를 안 만들고 중력이 켜져 있어서. 모터를 붙인 MJCF가 필요
- frame_id는 URDF 이름을 따르기로 함
- arp-scan으로 교실 와이파이를 훑어보니 파이가 없었음 → 전원이 꺼져 있었음


<br>

## 결과

- real_v2: train 252 / val 51 / test 35장
- 실제 val mAP50: sim_pre 0.822 → mix_ft 0.987 → mix_ft_from_final 0.990
- 새 URDF MuJoCo 로딩 성공 (body 16, 관절 15, 7.2초), 판정 REVIEW (조향 관절 drift)
- 인지 노드 첫 버전 방향: bbox · label · shape만, position NaN
- 작업공간: archive/ros_ws



<br>

## 느낀 점

- 




<br>

## 할 일

- 새 주행 영상 CVAT 내보내기 → real_v3 (가리기 끄기, 시간 구간으로 나누기) → 재학습
- 실제 test 평가 클래스별 정리
- spare 로봇 켜고 접속, IP 예약 요청
- archive/ros_ws 만들고 yolo_detector 첫 버전
- 신호등 HSV 문턱값 실험




