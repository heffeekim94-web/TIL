date of find: 2026 Aug 14, Friday


ERROR: **VS Code 화면이 주기적으로 깜빡이거나 순간적으로 검게 변했다 돌아오는 현상**

**GPU 하드웨어 가속/그래픽 드라이버 충돌**이에요.

특히 먼저 이것부터 확인해보는 게 좋아요.

1. VS Code에서 `Ctrl + Shift + P`
2. `Preferences: Configure Runtime Arguments` 검색
3. `argv.json`이 열리면 아래 설정이 있는지 확인해요.

```json
{
    "disable-hardware-acceleration": true
}
```

없다면 추가하고 저장한 다음 **VS Code를 완전히 종료했다가 다시 실행**해보세요.

다만 깜빡임 모양에 따라 원인이 달라질 수 있어요. 예를 들어 **VS Code 전체 창이 검게 깜빡이는지**, **코드 입력 부분만 깜빡이는지**, **터미널만 깜빡이는지**에 따라 그래픽 문제/확장 프로그램/터미널 렌더링 문제로 갈립니다.

**지금 깜빡이는 화면을 영상으로 5~10초 정도 찍어서 올려주면**, 어떤 종류의 문제인지 보고 다음 조치를 딱 맞춰서 안내할게요.


아, 찾았어. **이미 그 설정이 들어가 있어요.** 😄
사진에서 **11번째 줄**을 보면:

```json
// "disable-hardware-acceleration": true,
```

지금 앞에 `//`가 붙어서 **비활성화된 상태**예요.

### 딱 이것만 하면 돼

11번째 줄에서 앞의 `//`만 지워주세요.

현재:

```json
// "disable-hardware-acceleration": true,
```

👇 이렇게:

```json
"disable-hardware-acceleration": true,
```

그러면 파일이 대략 이렇게 됩니다.

```json
{
    "disable-hardware-acceleration": true,

    "enable-crash-reporter": true,

    "crash-reporter-id": "3f7ba303-9222-454d-9f76-bbf634ad1b5c"
}
```

그다음 **`Ctrl + S`로 저장 → VS Code 창을 전부 닫기 → 다시 VS Code 실행**하세요.

위에 주석에도 `Changing this file requires a restart of VS Code.`라고 적혀 있어서 **재시작해야 적용**됩니다.

일단 이것부터 해보고 **깜빡임이 사라지는지 보자.** 안 사라지면 다음으로 확장 프로그램 문제인지 그래픽 드라이버 문제인지 바로 좁혀볼게요.
