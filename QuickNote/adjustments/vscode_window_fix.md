ㅋㅋ 좋아. 나중에 그대로 복붙해서 볼 수 있게 **원인 → 테스트 → 영구 적용 → 원상복구**까지 한 번에 정리해줄게.

# 🖥️ Ubuntu에서 VS Code 최대화가 풀리며 작아지는 문제

### 증상

환경:

```text
Ubuntu 22.04
Wayland
듀얼 모니터
VS Code
```

VS Code를 최대화해놓은 상태에서 다른 모니터의 Chrome 같은 창을 클릭하면:

```text
VS Code 최대화
     ↓
다른 창 클릭
     ↓
VS Code 최대화가 풀리고 작아짐 ❌
```

Chrome 등 다른 프로그램에서는 발생하지 않고 **VS Code에서만 발생**.

---

## 1. Wayland인지 확인

터미널:

```bash
echo $XDG_SESSION_TYPE
```

결과가:

```text
wayland
```

인지 확인.

---

# 2. VS Code를 X11/XWayland로 실행해서 테스트

먼저 **열려 있는 VS Code를 전부 종료**.

Ubuntu 터미널에서:

```bash
code --ozone-platform=x11
```

이렇게 실행한다.

그다음:

```text
VS Code 최대화
     ↓
다른 모니터의 Chrome 클릭
     ↓
VS Code가 최대화 상태 유지
```

가 되면 같은 문제일 가능성이 높음.

> 이 단계는 테스트일 뿐이라 터미널에서 실행할 때만 적용된다.

---

# 3. VS Code 아이콘에도 영구 적용

시스템 파일을 직접 수정하지 않고 **사용자용 `.desktop` 파일을 만들어서 수정**한다.

### ① 사용자 applications 폴더 만들기

```bash
mkdir -p ~/.local/share/applications
```

### ② VS Code 실행 파일 설정 복사

```bash
cp /usr/share/applications/code.desktop ~/.local/share/applications/code.desktop
```

이제 시스템 원본:

```text
/usr/share/applications/code.desktop
```

은 그대로 두고,

내 계정에서 사용하는 복사본:

```text
~/.local/share/applications/code.desktop
```

만 수정하게 된다.

---

## 4. 복사본 수정

```bash
nano ~/.local/share/applications/code.desktop
```

`Exec=`로 시작하는 부분을 찾는다.

### 첫 번째

기존:

```text
Exec=/usr/share/code/code %F
```

변경:

```text
Exec=/usr/share/code/code --ozone-platform=x11 %F
```

### `new-empty-window` 부분

기존:

```text
Exec=/usr/share/code/code --new-window %F
```

변경:

```text
Exec=/usr/share/code/code --new-window --ozone-platform=x11 %F
```

즉 최종적으로 중요한 두 줄은:

```text
Exec=/usr/share/code/code --ozone-platform=x11 %F

Exec=/usr/share/code/code --new-window --ozone-platform=x11 %F
```

---

## 5. nano 저장

수정 완료 후:

```text
Ctrl + O
Enter
Ctrl + X
```

* `Ctrl + O` → 저장
* `Enter` → 파일 이름 확인
* `Ctrl + X` → nano 종료

참고로 nano에서 실수했을 때:

```text
Alt + U → Undo
Alt + E → Redo
```

---

## 6. 제대로 들어갔는지 확인

```bash
grep '^Exec=' ~/.local/share/applications/code.desktop
```

우리가 확인했던 정상 결과:

```text
Exec=/usr/share/code/code --ozone-platform=x11 %F
Exec=/usr/share/code/code --new-window --ozone-platform=x11 %F
```

이제 **VS Code를 완전히 종료한 뒤 Ubuntu의 VS Code 아이콘으로 다시 실행**한다.

그러면 터미널에서 매번

```bash
code --ozone-platform=x11
```

을 입력하지 않아도 자동으로 X11/XWayland 방식으로 실행된다.

---

# 🔄 나중에 원래대로 되돌리는 방법

이 부분도 중요해.

우리가 시스템 원본을 수정한 게 아니라

```text
~/.local/share/applications/code.desktop
```

이라는 **사용자용 복사본만 만든 것**이기 때문에 복구가 아주 간단해.

사용자용 파일을 삭제:

```bash
rm ~/.local/share/applications/code.desktop
```

끝.

그러면 VS Code가 다시 시스템 기본 파일인

```text
/usr/share/applications/code.desktop
```

을 사용하게 돼.

즉 다시 **기본 Wayland 방식**으로 돌아간다.

---

### 한 줄 요약 메모

```text
[문제]
Ubuntu Wayland + 듀얼모니터에서
VS Code 최대화 → 다른 창 클릭 → VS Code 작아짐

[테스트]
code --ozone-platform=x11

[영구 적용]
cp /usr/share/applications/code.desktop ~/.local/share/applications/code.desktop

nano ~/.local/share/applications/code.desktop

Exec=/usr/share/code/code --ozone-platform=x11 %F
Exec=/usr/share/code/code --new-window --ozone-platform=x11 %F

[원상복구]
rm ~/.local/share/applications/code.desktop
```

이 정도만 메모해두면 **나중에 VS Code 업데이트나 Ubuntu 설정 바뀌어서 다시 문제 생겨도 무슨 짓을 했는지 바로 알 수 있어.** 😎
