date: 2026.11.25

# 자연어 → 하위 작업 일지 (11/25)

> 작성: 김혜민 · 2026-11-25 (수)
> 강의 자료: [12강. 자연어를 하위 작업으로 바꾸기 (드라이브 PPT)](https://drive.google.com/file/d/15fO_W-0gOEQ38Fwutf2qw3gdSjBX7xFd/view) · [강의 원문 (노션)](https://app.notion.com/p/teamsparta/12-4122dc3ef514815a9647fc93e0fae081)

오늘은 **12강 자연어를 하위 작업으로 바꾸기를 배우고, 수업 끝에 pa06 (라즈베리파이) 에 waffle-mpx-lyrical 을 빌드한 날**이에요.

- "A 에서 상자를 가져와 B 에 놓고 충전해" 한 문장을 대상 · 목적지 · 완료 조건 · 순서로 나눠 봄
- 하위 작업을 `id` · `op` · `after` 로 적고, 선행 관계를 그래프 (DAG) 로 그려 위상 정렬로 순서를 정함
- 명령을 보낸 것과 성공한 것은 다름 → 관측으로 확인하고, 실패하면 바뀐 지점부터 다시 시작
- pa06 IP 가 바뀌어 접속이 안 됨 → MAC 주소로 새 IP 찾아 VS Code 로 접속
- 디스크 91% → 옛 VS Code 서버 · 로그 등을 지워 남은 공간 1.3G → 4.9G, 빌드 6개 패키지 3분 21초 성공

<br>

## 1. 지시를 검사할 수 있는 조건으로

- "B 에 놓아" → 선택한 상자가 B 에 있고 손이 비어 있음 (놓은 직후 확인)
- "충전해" → 충전기 D 에 연결되고 충전 중 신호가 켜짐 (도킹 후 확인)
- "놓고 충전해" → 놓은 **뒤에** 충전 시작. 마지막 상태만 보면 순서가 바뀐 기록도 통과하므로 두 사건의 시각을 비교
- 상자가 두 개 (둘 다 빨강) 면 색만으로 못 고름 → "입구 쪽과 창가 쪽 중 어느 것?" 처럼 눈으로 구별되는 위치로 되묻기
  - 후보가 둘 = `clarification_required`, 지도에 없는 위치 = `unknown_target`. 다른 오류에 같은 질문을 하면 안 됨

<br>

## 2. 작업 명세와 실행 확인

```json
{ "id": "t2", "op": "pick", "object_id": "box_02", "after": ["t1"] }
```

- 실행 전 검사: id 는 한 번만, `op` 는 허용 목록에, 물체는 관측 목록에, `after` 는 실제로 있는 작업
- JSON 을 읽을 수 있는 것과 실행할 수 있는 것은 별개. 허용 목록에 없는 `op` 는 추측하지 않고 돌려보냄
- `pick` 명령을 보냄 ≠ 집기 성공. 그리퍼가 닫혀도 상자가 탁자에 남아 있으면 B 로 출발하면 안 됨
- 관측 값은 세 가지: `free(B) = true / false / unknown`. 카메라가 가려졌을 때 `false` 로 넣으면 "가려졌다" 는 정보가 사라짐

<br>

## 3. 작업 그래프와 위상 정렬

| 작업 | 뜻 | 선행 |
|---|---|---|
| A / check | A 로 이동 / B 공간 조회 | 없음 |
| pick / B | 상자 집기 / B 로 이동 | A / pick |
| place | 상자 놓기 | B 와 check 모두 |
| D / charge | 충전기로 / 충전 시작 | place / D |

- 위상 정렬 = 선행 작업 수가 0 인 것부터 처리하고, 끝날 때마다 뒤 작업의 수를 1 씩 줄임. 가능한 순서는 하나가 아님 (A 와 check 중 아무거나 먼저)
- check 가 끝난 것과 B 가 비어 있다는 값은 다름. check 가 끝나도 값이 `false` 면 place 못 함
- `place → A` 같은 간선을 잘못 넣으면 고리 (A → pick → B → place → A) 가 생겨 영원히 대기. 고칠 땐 잘못 넣은 간선만 지움
- 선후 관계와 별개로 **장비** 도 봐야 함: 고정 카메라 조회는 차체 이동과 동시에 되지만, A 이동과 B 이동은 차체 하나라 동시에 못 함

```python
from graphlib import TopologicalSorter, CycleError
plan = {'A': (), 'check': (), 'pick': ('A',), 'B': ('pick',), 'place': ('B', 'check')}
print(tuple(TopologicalSorter(plan).static_order()))   # ('A', 'check', 'pick', 'B', 'place')
broken = dict(plan, A=('place',))                         # 고리 만들기 → CycleError
```

- `TopologicalSorter` 는 선행 목록에만 있는 오타 ID (`t9`) 도 노드로 받아들임 → `missing = {x for deps in plan.values() for x in deps} - set(plan)` 로 따로 검사

<br>

## 4. 상태 공간 탐색 · 실패 후 재계획

- 행동 하나가 상태 (로봇 위치 / 상자 위치 / 손) 의 어느 칸을 바꾸는지 따라감. B 에 도착한 것과 내려놓은 것은 다른 사건
- 손에 다른 상자가 있으면: 상태 공간 탐색은 가능한 행동부터 찾고, 작업 분해는 "집기" 의 사전조건이 막혀 "기존 상자 보관" 하위 작업을 넣음. 둘 다 내려놓을 자리가 없으면 사용자에게 물어야 함
- 집기 실패: A 도착은 여전히 유효 → 상자 자세를 다시 추정하고 집기부터 다시. 계속 실패하면 멈추고 사람에게 알림
- B 가 막혔는데 C 가 비었으면: 다시 보고, 대기하거나 "C 에 놓아도 될까요?" 물음. 목표를 바꾸는 판단과 경로를 바꾸는 판단은 다름
- 논문
  - **SayCan** (Ahn 외, 2022): 지시와의 관련성 (언어 점수) × 지금 실행 가능성 (affordance) 으로 다음 행동 선택
  - **Inner Monologue** (Huang 외, 2022): 실패 피드백 (`success: no`) 을 다시 언어 모델에 넣어 행동을 다시 고름

<br>

## 5. pa06 에 waffle-mpx-lyrical 빌드

### 접속
- 어제 IP `10.2.150.168` 은 다른 기기가 쓰고 있어서 `Connection refused`. DHCP 가 IP 를 새로 줬음
- 네트워크를 훑어 pa06 의 MAC 으로 찾음 → `10.2.150.201`. 호스트 키 지문이 어제와 같은 걸로 같은 파이인지 확인
- ssh 는 지문을 **IP 별로** 기억해서, IP 가 바뀌면 같은 파이여도 다시 확인을 받음
- VS Code Remote-SSH 는 `~/.ssh/config` 를 같이 씀 → `Host pa06` 의 `HostName` 한 줄만 새 IP 로 고치면 됨

### 디스크 정리 (SD 15G 중 91% 사용, 남은 1.3G)
| 지운 것 | 크기 | 이유 |
|---|---|---|
| `~/.vscode-server/cli/servers` 옛 버전 4개 | 약 2.5G | VS Code 업데이트마다 새 서버를 깔고 옛것을 안 지움 |
| `/var/log/journal` | 513M → 48M | 시스템 로그 (`journalctl --vacuum-size=50M`) |
| `librealsense` | 330M | 소스 빌드 흔적. 실제로는 apt 의 `ros-lyrical-librealsense2` 사용 |
| `ninja_ws` · `pa06_ws` · `opencr_fw` · `opencr_ld` 등 | 약 200M | 이전 구성 |

- 폴더별 크기 보기: `du -sh ~/* ~/.[!.]* | sort -rh`, 전체는 `df -h /`
- `/usr/lib/firmware` (740M) 는 와이파이 등 드라이버라 건드리면 안 됨
- 결과: 남은 공간 **4.9G** (64%)

### 빌드
- 저장소가 곧 `src` 인 구조 → `~/waffle_mpx/src` 로 옮김
- `tmux` 안에서 실행 (접속이 끊겨도 계속 돎. `Ctrl+B`, `D` 로 빠져나옴)
- 파이에는 MoveIt · Cartographer 같은 제어 PC 용은 빼고 ros2_control 관련만 apt 로 설치
  - `[0%]` 에서 멈춘 것처럼 보였는데 `libboost` 헤더 수만 개를 SD 카드에 쓰는 중이었음 (프로세스 상태 `D`)
- RAM 3.7G · swap 없음 → `--parallel-workers 1`, `MAKEFLAGS=-j2`, `--packages-up-to turtlebot3_manipulation_bringup`
- 결과: `Summary: 6 packages finished [3min 21s]`, failed 없음
- colcon 결과 읽기: `finished` 성공, `failed` 실패, `stderr output` 은 성공했지만 경고, `aborted` 는 다른 패키지 때문에 중단

<br>

## 다음 할 일

- [ ] 실습 1 ~ 4 (종이 그래프, `graphlib` 정상 · 순환, 되묻는 질문) 직접 해 보기
- [ ] pa06 `~/.bashrc` 의 `ninja_ws` 줄 정리 (`COLCON_PREFIX_PATH` 경고)
- [ ] `source ~/waffle_mpx/src/tools/lyrical_env.bash` → `ros2 launch turtlebot3_manipulation_bringup robot.launch.py mode:=mock`
- [ ] OpenCR 에 manipulation 펌웨어 올리기
- [ ] 시간 날 때 `sudo apt upgrade` + 재부팅 (IP 바뀌면 `~/.ssh/config` 수정)
