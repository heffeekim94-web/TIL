# 로봇 입력하기
.urdf에 코드를 입력하여 모형을 구현한다. 

1. rotbot.urdf 파일을 만든다
<br>

2. 설치를 하고
```bash
sudo apt install ros-humble-urdf-tutorial 
```
<br>

3. 새로운 창을 열어서 실행한다
```bash
ros2 launch urdf_tutorial display.launch.py model:=파일주소/robot.urdf
```
<br>

* model:= 이후에는 파일 주소를 입력하는건데 위치를 못찾아서 계속 오류가 난다면 
'ros2 launch urdf_tutorial display.launch.py model:=' 까지 입력을 하고 여기에 실제 파일을 드래그 드롭을 하면 위치가 작성이 된다. 
<br>

5. 위 사항이 차질 없이 진행된다면 아래 사진과 같은 그래픽 창이 뜬다.
![alt text](<스크린샷 2026-08-12 12-28-31.png>)

- 거리는 원점 대 원점 거리를 측정하여 실린더의 길이나 외형의 사이즈를 고려하여 간격을 더 줘야 겹치지 않는다. 
- 링크에서 좌표를 바꿀일은 없고 조인트에서 변경한다. 
- 3d 모형을 그리고 .stl 파일 형식으로 변형한 다음에 .urdf 파일에서 원점과 위치, 회전 방향 등을 설정한다. 

### 예시

```xml
<?xml version="1.0"?>
<robot name="my_robot">

    <link name="base_footprint"/>
  <link name="base_link">
    <visual>
      <geometry>
        <box size="1 1 0.5"/>
      </geometry>
      <origin xyz="0 0 0" rpy="0 0 0"/>
    </visual>
  </link>

  <link name="lidar">
    <visual>
      <geometry>
        <cylinder radius="0.05" length="0.1"/>
      </geometry>
      <origin xyz="0 0 0" rpy="0 0 0"/>
    </visual>
  </link>
<link name="left_wheel">
    <visual>
      <geometry>
        <cylinder radius="0.2" length="0.05"/>
      </geometry>
      <origin xyz="0 0 0" rpy="0 1.5735 0"/>
    </visual>
  </link>

  <link name="right_wheel">
    <visual>
        <geometry>
            <cylinder radius="0.2" length="0.05"/>
        </geometry>
        <origin xyz="0 0 0" rpy="1.5735 0 1.5735"/>
    </visual>
  </link>
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="-0.525 0.3 -0.2" rpy="0 0 0"/>
    <axis xyz="1 0 0"/>
    </joint>

    <joint name="right_wheel_joint" type="continuous">
        <parent link="base_link"/>
        <child link="right_wheel"/>
        <origin xyz="0.525 0.3 -0.2" rpy="0 0 0"/>
        <axis xyz="1 0 0"/>
    </joint>
    <joint name="lidar_joint" type="fixed">
        <parent link="base_link"/>
        <child link="lidar"/>
        <origin xyz="0 0 0.3" rpy="0 0 0"/>
    </joint>

    <joint name="base_footprint_joint" type="fixed">
        <parent link="base_footprint"/>
        <child link="base_link"/>
        <origin xyz="0 0 0.4" rpy="0 0 0"/>
    </joint>
</robot>
```

