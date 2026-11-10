"""All arm link points (downsampled URDF meshes) posed by the team arm model."""
import numpy as np
import armgeo as A

FINGER_OPEN, FINGER_ON = 0.0072, -0.001
LINKS = ["arm_link1", "arm_link2", "arm_link3", "arm_link4_wrist", "arm_link5_wrist_roll", "gripper_finger_a", "gripper_finger_b"]
PTS, _ = A.load_link_points(LINKS)
_rng = np.random.default_rng(0)
PTS = {k: v[_rng.choice(len(v), min(len(v), 1500), replace=False)] if len(v) else v for k, v in PTS.items()}


def world_points(q, finger):
    F = A.frames(q)
    out = {}
    for nm in LINKS:
        if nm in A.LINK_INDEX:
            T = F[A.LINK_INDEX[nm]]
        else:
            To, ax = A._FINGER[nm]
            Tj = To.copy(); Tj[:3, 3] += ax / np.linalg.norm(ax) * finger
            T = F[4] @ Tj
        out[nm] = PTS[nm] @ T[:3, :3].T + T[:3, 3]
    return out
