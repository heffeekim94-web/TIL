두 코드의 차이를 draw.io 파일 1개와 PNG 이미지 3장으로 만들었습니다. 이미지를 직접 열어서 글자 잘림이나 겹침이 없는지 확인했습니다. 다만 이 PC에는 draw.io 앱이 없어서 `.drawio` 파일은 draw.io에서 직접 열어 보지는 못했습니다.

**결과물** ([report/](../report/) 폴더, 기존 `opencr_control_flow.drawio` 옆)
- [opencr_control_vs_lite.drawio](opencr_control_vs_lite.drawio): 탭 3개로 된 편집용 파일
- [pic/opencr_control_vs_lite_1.png](pic/opencr_control_vs_lite_1.png): 항목별 비교표 15개 항목 + 공통점
- [pic/opencr_control_vs_lite_2.png](pic/opencr_control_vs_lite_2.png): `loop()` 흐름도 비교
- [pic/opencr_control_vs_lite_3.png](pic/opencr_control_vs_lite_3.png): `v PAN TILT` 명령 처리 흐름 비교

**핵심 차이**
- **용도:** control은 사람이 쓰는 통합 제어 펌웨어입니다. 명령은 `v`, 상대 이동, `h`, `x`, `off`, `p`, `scan`, `auto`가 있고 EEPROM에 위치를 저장합니다. lite는 PC나 ROS가 보내는 속도 명령만 받고, 명령도 `v`, `p`, `x` 세 개뿐입니다.
- **제어 주기:** control은 100ms마다 상태를 점검하고(10Hz) 레지스터를 하나씩 따로 읽고 씁니다. lite는 10ms 고정 주기(100Hz)로 Sync Read와 Sync Write를 써서 두 축을 한 번에 처리합니다.
- **`v` 처리 방식:** control은 명령을 받는 즉시 모터에 기록합니다. lite는 요청 값만 저장해 두고 다음 10ms 주기에 반영해서, 명령이 자주 와도 버스 부하가 일정합니다.
- **안전 관련 값:** 속도 명령 타임아웃은 500ms → 200ms, 속도 상한은 약 24.5 → 1.0 rad/s, tilt 범위는 ±135° → ±120°로 바뀌었습니다. lite는 잘못된 입력이 오면 거부하는 데서 끝나지 않고 모터를 바로 멈춥니다.
- **응답 형식:** control은 사람이 읽기 위한 텍스트를 출력합니다. lite는 프로그램이 파싱하기 쉬운 `P1 …` 한 줄을 보내고, 오류가 나면 그 앞에 `F1 …` 진단 줄을 붙입니다.

PNG 생성 스크립트는 세션용 임시 폴더에 있습니다. 내용을 고치려면 `.drawio` 파일을 draw.io(app.diagrams.net 또는 VS Code의 Draw.io Integration 확장)에서 직접 편집하시면 됩니다.

---

`return`은 이번 `loop()` 실행에서 남은 단계를 건너뛰고 바로 끝낸다는 뜻입니다. 프로그램 전체가 끝나는 게 아닙니다. Arduino는 `loop()`가 끝나면 곧바로 다시 호출하기 때문에, 다음 실행은 맨 위의 타임아웃 검사부터 다시 시작합니다.

그림의 `return`은 지금 처리할 일이 없으면 시리얼 입력만 처리하고 빠져나온다는 의미입니다.

**opencr_lite.ino** ([opencr_lite.ino:312](opencr_lite.ino#L312))
```cpp
if (faulted || (uint32_t)(micros() - cycle_us) < CYCLE_US) return;
```
- **아직 10ms가 지나지 않았을 때:** 모터 읽기·쓰기를 하지 않고 나갑니다. 이 덕분에 모터 통신은 정확히 10ms(100Hz)마다 한 번만 일어납니다.
- **FAULT 상태일 때:** 모터 제어를 완전히 멈춥니다. 그래도 위쪽의 `readCommands()`는 계속 실행되므로 `p`(상태 확인)와 `x`(정지)에는 응답합니다.

**opencr_control.ino**
- **[1176번 줄](opencr_control.ino#L1176):** 마지막 점검 후 100ms가 지나지 않았으면 나갑니다. 상태 점검을 10Hz로 제한하는 역할입니다.
- **[1181번 줄](opencr_control.ino#L1181):** 이동 중(`active`)이 아니면 나갑니다. 도착 판정을 할 대상이 없기 때문입니다.

즉 두 코드 모두 `loop()`는 매우 빠르게 계속 돌고, `return`이 주기를 맞춰 무거운 작업을 정해진 간격에만 실행되게 하는 역할을 합니다.