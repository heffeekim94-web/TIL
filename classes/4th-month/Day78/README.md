Date: 2026 Nov 25, Wednesday

## 오늘 배운 것
- (강의) 자연어 지시는 대상 · 목적지 · 완료 조건 · 순서로 나눠야 검사할 수 있다. 같은 설명에 후보가 둘이면 눈으로 구별되는 말로 되묻는다
- (강의) 하위 작업을 `id` · `op` · `after` 로 적고 선행 관계를 그래프로 그리면 위상 정렬로 순서를 정할 수 있다. 잘못된 간선 하나로 고리가 생기면 영원히 기다린다
- (강의) 명령을 보낸 것과 성공한 것은 다르다. 관측으로 확인하고, 실패하면 바뀐 지점부터 다시 계획한다 (SayCan, Inner Monologue)
- (강의) 관측 값은 true / false 말고 unknown 도 있어야 한다
- ssh 는 호스트 키를 IP 별로 기억한다. IP 가 바뀌면 `~/.ssh/config` 의 `HostName` 만 고치면 VS Code 도 같이 된다
- VS Code 는 업데이트할 때마다 원격 서버를 새로 깔고 옛것을 안 지운다 (파이에서 2.5G)
- colcon 의 `stderr output` 은 실패가 아니라 경고다



<br>

## 오늘 한 것 

- 강의 자료: [12강. 자연어를 하위 작업으로 바꾸기 (드라이브 PPT)](https://drive.google.com/file/d/15fO_W-0gOEQ38Fwutf2qw3gdSjBX7xFd/view) · [강의 원문 (노션)](https://app.notion.com/p/teamsparta/12-4122dc3ef514815a9647fc93e0fae081)
- [자연어 → 하위 작업 일지 (11/25)](task_planning_log.md)
- 12강 자연어를 하위 작업으로 바꾸기 (25장) 수업
- pa06 새 IP 찾아 VS Code 로 접속
- pa06 디스크 정리, waffle-mpx-lyrical 의존성 설치 · 빌드



<br>

## 문제점
- pa06 접속 안 됨 (`Connection refused`)
- pa06 디스크 91% (남은 1.3G)
- apt 설치가 `[0%]` 에서 멈춘 것처럼 보임



<br>

## 해결 방법

- MAC 주소로 새 IP (`10.2.150.201`) 찾고 `~/.ssh/config` 수정
- 옛 VS Code 서버 4개 · 시스템 로그 · 안 쓰는 폴더 삭제
- 끊지 않고 기다림 (Boost 헤더를 SD 카드에 쓰는 중이었음)



<br>

## 결과

- 남은 공간 1.3G → 4.9G
- `Summary: 6 packages finished [3min 21s]`, failed 없음



<br>

## 느낀 점

- 생각보다 간단한 강의 내용이여서 집중할만 했다. 매일 이정도의 강의면 집중 가능할 것 같다. 



<br>

## 할 일

- 12강 실습 1 ~ 4 해 보기
- pa06 `.bashrc` 의 `ninja_ws` 줄 정리, mock 모드로 bringup 실행
- OpenCR 에 manipulation 펌웨어 올리기
