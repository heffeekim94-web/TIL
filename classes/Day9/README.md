


build에 parameters를 넣어 놔야 한다. 

아래와 같이 폴더를 생성한다. 

home
    ros2_ws
        src
            demo_cpp
                demo_cpp
            demo_python
                demo_python
                    __init__.py
                    talker.py
                resource
                    demo.py
                    package.xml
                    setup.cfg
                    setup.py
                    

cmd창에 아래의 순서대로 명령어를 입력한다. 

1. 코드 작성

2. 작업공간을 빌드하는 도구
```bash
colcon build
```
3. bash를 install 하고
```bash
source install/setup.bash
```

4. launch를 한다
```bash
ros2_ws/src$ ros2 launch demo_bringup demo.launch.py
```

* ros2_ws 폴더를 새로 홈에 만들고 src폴더 안에 해당 폴더들을 만드는게 좋다

