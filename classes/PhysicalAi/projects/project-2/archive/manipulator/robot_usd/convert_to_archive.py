"""혁무님 xacro → URDF → USD 를 이 폴더(robot_usd/)에 만든다. 팀 저장소의 tools/convert_team_robot.py 를 그대로 쓰고, 팀 저장소는 읽기만 한다.

  1) URDF (시스템 python + ROS xacro):
       source /opt/ros/lyrical/setup.bash
       python3 convert_to_archive.py urdf ~/Downloads/robot.urdf.xacro
  2) USD (Isaac Lab python):
       env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMNI_KIT_ACCEPT_EULA=YES \
         ~/pa-course/IsaacLab-6.2/.venv/bin/python convert_to_archive.py usd

xacro 는 $(find description), $(find bringup) 를 찾으므로 임시 폴더에 가짜 패키지 두 개를 만들어 AMENT_PREFIX_PATH 로 알려 준다:
  description = 받은 xacro + 팀 ros2_control.xacro + 팀 meshes,  bringup = 팀 config/hardware_map.yaml
만들어진 URDF 의 메시 경로는 팀 저장소 ros2_ws/src/description/meshes 를 가리킨다.
--out 으로 다른 폴더에 만들 수 있다 (기본: 이 파일이 있는 폴더)."""
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path('/home/haeminkim/바탕화면/git/Project2_Turtle_Ninja')
REPO_DESC = REPO / 'ros2_ws' / 'src' / 'description'

args = sys.argv[1:]
out = Path(__file__).resolve().parent
if '--out' in args:
    i = args.index('--out')
    out = Path(args[i + 1]).expanduser().resolve()
    del args[i:i + 2]
stage = args[0] if args else ''
if stage not in ('urdf', 'usd') or (stage == 'urdf' and len(args) < 2):
    sys.exit(__doc__)
sys.argv = sys.argv[:1]  # convert_team_robot.main() 이 자기 인자를 읽으므로 비움

sys.dont_write_bytecode = True  # 팀 저장소에 __pycache__ 를 남기지 않음
sys.path.insert(0, str(REPO / 'sim' / 'robot_sim' / 'tools'))
import convert_team_robot as C

C.TEAM_DIR = out / 'urdf'
C.TEAM_URDF = out / 'urdf' / 'robot.urdf'
C.TEAM_SWERVE = out / 'urdf' / 'config' / 'swerve.yaml'
C.TEAM_USD = out / 'usd' / 'robot' / 'robot.usda'

if stage == 'urdf':
    xacro = Path(args[1]).expanduser().resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        desc, bringup, index = tmp / 'description', tmp / 'bringup', tmp / 'share' / 'ament_index' / 'resource_index' / 'packages'
        (desc / 'urdf').mkdir(parents=True)
        (bringup / 'config').mkdir(parents=True)
        index.mkdir(parents=True)
        (desc / 'urdf' / 'robot.urdf.xacro').symlink_to(xacro)
        (desc / 'urdf' / 'ros2_control.xacro').symlink_to(REPO_DESC / 'urdf' / 'ros2_control.xacro')
        (desc / 'meshes').symlink_to(REPO_DESC / 'meshes')
        (bringup / 'config' / 'hardware_map.yaml').symlink_to(REPO / 'config' / 'hardware_map.yaml')
        for pkg in (desc, bringup):
            (index / pkg.name).touch()
            (tmp / 'share' / pkg.name).symlink_to(pkg)
        os.environ['AMENT_PREFIX_PATH'] = f"{tmp}:{os.environ.get('AMENT_PREFIX_PATH', '')}"
        C.DESC = desc
        C.TEAM_DIR.mkdir(parents=True, exist_ok=True)
        root = C.make_urdf()
        # 메시 경로: 임시 폴더 대신 팀 저장소를 직접 가리키게 (이 스크립트가 끝나도 URDF 가 유효하도록)
        C.TEAM_URDF.write_text(C.TEAM_URDF.read_text().replace(str(desc) + '/', str(REPO_DESC) + '/'))
        C.make_swerve(root)
    print('URDF:', C.TEAM_URDF, '· swerve:', C.TEAM_SWERVE)
else:
    C.make_urdf = lambda: ET.parse(C.TEAM_URDF).getroot()
    C.make_swerve = lambda root: None
    C.main()
