"""GIF 용 카메라 (env 0 하나만) 와 그림 합치기. play.py · replay_check.py 가 씀 (스크립트가 enable_cameras 를 켬)."""
import numpy as np

import isaaclab.sim as sim_utils
from isaaclab.sensors import CameraCfg

# 로봇 오른쪽 앞 위에서 적재함 · 박스를 같이 보는 자리 (env 0 원점 기준)
EYE, TARGET = (0.42, -0.42, 0.52), (0.06, 0.0, 0.17)
# 적재함 오른쪽 (S4 · S7 · S9 · S12) 가까이


def add_camera(cfg, height=480, width=640):
    cfg.scene.viz_cam = CameraCfg(prim_path='{ENV_REGEX_NS}/VizCam', height=height, width=width, data_types=['rgb'],
                                  spawn=sim_utils.PinholeCameraCfg(focal_length=14.0, clipping_range=(0.01, 10.0)))


def aim(env, eye=EYE, target=TARGET):
    cam = env.scene['viz_cam']
    o = env.scene.env_origins.cpu().numpy()
    cam.set_world_poses_from_view(eyes=(o + np.array(eye)).astype(np.float32), targets=(o + np.array(target)).astype(np.float32))


def frame(env):
    return env.scene['viz_cam'].data.output['rgb'][0].cpu().numpy()[..., :3].astype(np.uint8)
