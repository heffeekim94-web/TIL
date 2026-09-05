Date: 2026 Sept 05, Saturday

확인 결과, **`pose_lab`은 현재 정상 등록되어 있고 `02_rotation.ipynb`에도 해당 커널이 저장돼 있어요.** 다만 `git pull`은 실패했습니다.

진행 과정과 해결 방법은 다음과 같아요.

1. **처음 보였던 `Python (QuickTip)`은 다른 환경이었어요.**
   - `QuickTip` → `C:\Users\haemi\git\.venv\Scripts\python.exe`
   - `pose_lab` → 프로젝트 내부 `pose_lab\Scripts\python.exe`
   
   가상환경을 만드는 것과 Jupyter에 커널로 등록하는 것은 별도 단계예요. 당시 등록 상태는 기록이 없어 확정할 수 없지만, 화면에는 다른 환경이 선택되어 있었습니다.

2. **`command not found`는 터미널 문법 차이 때문에 발생했어요.**
   
   사용 중인 터미널은 **Git Bash**인데 제가 PowerShell용 `.\pose_lab\Scripts\python.exe`를 안내했습니다. Bash에서는 `\`가 이스케이프 문자로 처리되어 경로가 깨진 거예요. 제 안내 오류였습니다.

3. **Git Bash용 경로로 설치·등록하는 것이 해결 방법이었어요.**
   ```bash
   ./pose_lab/Scripts/python.exe -m pip install ipykernel
   ./pose_lab/Scripts/python.exe -m ipykernel install --user --name pose_lab --display-name "Python (pose_lab)"
   ```
   이후 노트북에서 `Python (pose_lab)`을 선택하는 흐름입니다. 현재 실제 Python 실행과 `ipykernel` 가져오기가 성공했고, 노트북에도 선택 결과가 저장돼 있어요.

**Git 이력은 확인하지 못했어요.** 현재 `C:\Users\haemi\git\physicalai-lv1-HaeminKim`에는 `.git`이 없어서 `git pull --ff-only`와 커밋 이력 조회 모두 다음 오류가 났습니다.

```text
fatal: not a git repository (or any of the parent directories): .git
```

따라서 위 요약은 **대화의 명령어 기록과 현재 환경·노트북 파일을 확인한 결과**예요. 원격 저장소 주소를 알려주시면 실제 Git 저장소를 연결하는 다음 작업을 진행할 수 있어요.