# Install C++ language



1. update
```bash
haeminkim@pa:~/Desktop$ sudo apt update
```

2. enter passcode
```bash
[sudo] haeminkim 암호: 
```
3. running program looks like:
```bash
기존:1 http://kr.archive.ubuntu.com/ubuntu jammy InRelease
기존:2 http://kr.archive.ubuntu.com/ubuntu jammy-updates InRelease                                       
기존:3 http://kr.archive.ubuntu.com/ubuntu jammy-backports InRelease                                     
기존:4 https://dl.google.com/linux/chrome-stable/deb stable InRelease                                    
기존:5 http://packages.ros.org/ros2/ubuntu jammy InRelease                                               
기존:6 http://security.ubuntu.com/ubuntu jammy-security InRelease                                        
기존:7 https://packagecloud.io/slacktechnologies/slack/debian jessie InRelease
기존:8 https://linux.teamviewer.com/deb stable InRelease                      
패키지 목록을 읽는 중입니다... 완료                   
의존성 트리를 만드는 중입니다... 완료
상태 정보를 읽는 중입니다... 완료        
188 패키지를 업그레이드할 수 있습니다. 확인하려면 'apt list --upgradable'를 실행하십시오.
```

4. c++ language installation 
```bash
haeminkim@pa:~/Desktop$ sudo apt install -y build-essential cmake gdb valgrind git
```

5. running program looks like:
```bash
패키지 목록을 읽는 중입니다... 완료
의존성 트리를 만드는 중입니다... 완료
상태 정보를 읽는 중입니다... 완료        
패키지 build-essential는 이미 최신 버전입니다 (12.9ubuntu3).
build-essential 패키지는 수동설치로 지정합니다.
패키지 cmake는 이미 최신 버전입니다 (3.22.1-1ubuntu1.22.04.2).
cmake 패키지는 수동설치로 지정합니다.
패키지 gdb는 이미 최신 버전입니다 (12.1-0ubuntu1~22.04.2).
gdb 패키지는 수동설치로 지정합니다.
패키지 git는 이미 최신 버전입니다 (1:2.34.1-1ubuntu1.17).
git 패키지는 수동설치로 지정합니다.
다음 패키지가 자동으로 설치되었지만 더 이상 필요하지 않습니다:
  libfwupd2 libfwupdplugin5 libgcab-1.0-0 libsmbios-c2
'sudo apt autoremove'를 이용하여 제거하십시오.
다음의 추가 패키지가 설치될 것입니다 :
  libc6-i386
제안하는 패키지:
  valgrind-dbg valgrind-mpi kcachegrind alleyoop valkyrie
다음 새 패키지를 설치할 것입니다:
  libc6-i386 valgrind
0개 업그레이드, 2개 새로 설치, 0개 제거 및 188개 업그레이드 안 함.
16.9 M바이트 아카이브를 받아야 합니다.
이 작업 후 91.8 M바이트의 디스크 공간을 더 사용하게 됩니다.
받기:1 http://kr.archive.ubuntu.com/ubuntu jammy-updates/main amd64 libc6-i386 amd64 2.35-0ubuntu3.14 [2,838 kB]
받기:2 http://kr.archive.ubuntu.com/ubuntu jammy/main amd64 valgrind amd64 1:3.18.1-1ubuntu2 [14.1 MB]
40% [2 valgrind 3,543 kB/14.1 MB 25%]^C
```

6. check version
```bash
haeminkim@pa:~/Desktop$ g++ --version
```

7. shows version
```bash
g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
Copyright (C) 2021 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

8. check cmake version
```bash
haeminkim@pa:~/Desktop$ cmake --version
```

9. shows cmake version
```bash
cmake version 3.22.1
CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

10. check gdb version
```bash
haeminkim@pa:~/Desktop$ gdb --version
```

11. shows gdb version
```bash
GNU gdb (Ubuntu 12.1-0ubuntu1~22.04.2) 12.1
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
```

12. chceck valgrind version
```bash
haeminkim@pa:~/Desktop$ valgrind --version
```

13. shows vlgrind version
```bash
명령어 'valgrind' 을(를) 찾을 수 없습니다. 그러나 다음을 통해 설치할 수 있습니다:
sudo snap install valgrind  # version 3.26.0, or
sudo apt  install valgrind  # version 1:3.18.1-1ubuntu2
'snap info valgrind'에서 추가적인 버전을 확인하십시오.
```
