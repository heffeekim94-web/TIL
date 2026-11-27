Date: 2026 Nov 27, Friday

## 오늘 배운 것
- 셸에서 `source` 없이 `setup.bash` 경로만 치면 프로그램처럼 실행하려다 `Permission denied` 가 난다
- bringup 포트를 잘못 주면 (`lidar_port:=/dev/ttyACM0`) 라이다 드라이버가 OpenCR 포트를 같이 열어 `Incorrect status packet` → 하드웨어 활성화 실패
- `git pull` 은 다른 브랜치 업데이트도 받아 오지만, 그 브랜치로 바꿔야 파일에 보인다 (`feature/open-instruction-vla`)
- 와이파이로는 압축 안 된 카메라 원본 영상이 노트북까지 오지 못한다 → 파이에서 압축해 보내고 노트북에서 풀어 주는 브리지
- 역정규화: 학습 때 `a_norm = (a − μ)/σ` 였으면 실행 때 `a = a_norm·σ + μ`. μ · σ 는 학습 데이터 값을 그대로 쓴다
- 코드는 위에서부터 읽지 말고 질문 하나 ("파란 퍽 집어" 하면 무슨 일이?) 를 들고 함수 호출을 따라간다 (VS Code `F12`, `Alt+←`)
- 팀스파르타 노션에 게스트로 들어가 있으면 Notion MCP 연결이 안 된다 (편집 권한과 별개)



<br>

## 오늘 한 것 

- 강의 자료: [14–18강. 명령 계약에서 통합 플래너 평가까지 (드라이브 PPT)](https://docs.google.com/presentation/d/13_NL2CNK8UfdWzd97lj0munzRF9M9JANiDLQ5iBY8wI/edit) · [역정규화 질문 강의 원문 (노션)](https://app.notion.com/p/LLM-VLM-VLA-Robotics-1a079696939583a5853b01679b97a0a4)
- [Waffle MPX 실물 · 브리지 일지 (11/27)](bridge_log.md)
- 프로젝트 3 시작: D팀_AUTOBOT ([팀 노션](https://app.notion.com/p/teamsparta/D-_AUTOBOT-4252dc3ef51480869660cfa94f43ff3e)), 내 역할은 RAG model (정책, Dataset 모으기, pipeline, skill)
- pa06 새 IP (`10.2.150.93`) 찾고 bringup 다시 실행
- `real_react` 코드 구조 보기, 어제 무한 반복 원인 확인
- 팀원의 RM-X52 팔 · LDS-03 메시를 노트북 `~/waffle_mpx/src` 에 합침 (관절 한계는 우리 값 유지)
- 튜터님 새 브랜치 (`feature/open-instruction-vla`) 로 바꾸고 실물 자유 지시 실행기 준비
- 와이파이 카메라 브리지 (`pi_relay.py` · `laptop_bridge.py`) 만듦



<br>

## 문제점
- bringup 후 컨트롤러가 모두 `inactive`
- `git pull` 했는데 "Already up to date"
- 튜터님 `free_command.py --backend hardware` 가 카메라 영상을 못 받음 (노트북에서 RGB · 깊이 0개)
- 브리지 처음엔 카메라 1.1Hz, 카메라 TF 15개 중 11개만 들어옴



<br>

## 해결 방법

- `lidar_port` 오타 고쳐 다시 실행 → 컨트롤러 5개 active
- 튜터님 커밋이 `main` 이 아니라 `feature/open-instruction-vla` 에 있어서 그 브랜치로 전환
- 파이에서 JPEG/PNG 로 압축해 초당 5장, 노트북에서 풀어 원래 토픽 이름으로 다시 내보냄
- 와이파이 구간 재전송 켜기, 노트북 수신 버퍼 키우기, 파이에서 tf_static 을 모아 2초마다 다시 보냄



<br>

## 결과

- 브리지로 RGB · 깊이 4.4Hz, 지연 0.17초 (0.4초 기준 안), TF 15개 모두 들어옴
- 튜터님 코드 한 줄도 안 고치고 `observe()` 로 팔 관절값 · 카메라 사진 정상
- 팔 · 바퀴 명령이 브리지로 전달되는지는 아직 확인 안 함



<br>

## 느낀 점

- 오늘 팀이 재구성 되어서 프로젝트3 발제내용을 듣고 미션 디자인 해보고 또 역할 분담도 했다. 전에 있던 팀에서는 뭔가 벙쪄 있었다면 이번 미션에서는 좀더 집중할 수 있어서 맘이 놓인다. 앞으로 적극적인 수기가 되어서 팀의 프로그레스 유지가 되도록 노력해보고싶다. 뭔가 맨날 누군가 해주길 바라는 마음만 있으면 아무도 내 마음을 몰라주니 내가 직접 그 행동을 꺼내서 행해야지 할 수 있지 않을까? 기대된다. 



<br>

## 할 일

- 브리지로 튜터님 자유 지시 실행기 실물 실행 (사진 → 팔 · 바퀴 명령)
- 튜터님 방식 (Qwen2.5 7B + VLA) 과 우리 `react_agent.py` (gemma4) 결과 비교
- 프로젝트 3: RAG 정책 · 데이터셋 모으기 시작
