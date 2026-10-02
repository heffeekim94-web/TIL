우분투(Ubuntu)에서 사용자를 dialout 그룹에 추가하려면 터미널에 sudo usermod -aG dialout 사용자이름 명령어를 입력하면 됩니다. [1] 
시리얼 포트(COM 포트, 아두이노 등) 접근 권한을 위해 dialout 그룹에 계정을 추가하는 방법과 확인 절차는 다음과 같습니다.
## 그룹 추가 방법

   1. 터미널을 엽니다.
   2. 아래 명령어를 입력하여 사용자를 dialout 그룹에 추가합니다 (username 부분을 실제 사용자 이름으로 바꿉니다).
   
   sudo usermod -aG dialout username
   
   * -aG 옵션은 기존 그룹에서 탈퇴시키지 않고 새로운 그룹에 추가(Append)할 때 사용합니다. [1, 2, 3] 
   
## 적용 및 확인 방법

   1. 그룹 변경 사항을 완전히 적용하려면 시스템에서 로그아웃한 후 다시 로그인하거나 터미널을 재시작해야 합니다.
   2. 현재 로그인한 계정의 그룹 소속을 확인하려면 아래 명령어를 입력합니다.
   
   id
   
   3. 출력 결과에 dialout이 포함되어 있는지 확인합니다. [1] 

만약 특정 디바이스 파일 권한(예: /dev/ttyACM0) 이나 아두이노 연결 관련해서 다른 문제가 있다면 말씀해 주세요. 해결 방법을 안내해 드릴게요.

[1] [https://alphalok.tistory.com](https://alphalok.tistory.com/21)
[2] [https://scribblinganything.tistory.com](https://scribblinganything.tistory.com/801)
[3] [https://jjeongil.tistory.com](https://jjeongil.tistory.com/1680)
