"""학습2 설정: 장면 · 과제 · 보상 · PPO. 숫자 출처는 줄마다 적음 (팀 저장소 config/*.yaml = 커밋 64eafaf).

과제 하나 = 퍽 하나 옮기기. HOME 에서 출발 → 원래 자리에서 쥐기 → 옮겨 놓기 → HOME 으로 돌아오기.
  store    : 박스 윗면 주사위 칸에 선 퍽 → 빈 적재함 칸 (PICK 뒤 STORE)
  retrieve : 적재함 칸의 퍽 → 박스 윗면 주사위 칸 (RETRIEVE 뒤 PLACE)
나머지 적재함 칸은 무작위로 참 (0 ~ 11 개, 처음엔 적게 → 성공률 따라 늘림).
"""
from dataclasses import dataclass
from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.sim.schemas.schemas_cfg import PhysxArticulationCfg, PhysxRigidBodyCfg

HERE = Path(__file__).resolve().parent
# USD 안 팔 몸체 경로 (robot.usda payloads/base.usda 의 중첩 그대로)
ARM_PATH = '{ENV_REGEX_NS}/Robot/Geometry/base_footprint/link2/link3/link4/link5'
HAND_BODIES = {'link5': ARM_PATH, 'wrist': ARM_PATH + '/wrist_link', 'finger_l': ARM_PATH + '/wrist_link/gripper_left_link',
               'finger_r': ARM_PATH + '/wrist_link/gripper_right_link'}
UPPER_ARM = ['{ENV_REGEX_NS}/Robot/Geometry/base_footprint/link2', '{ENV_REGEX_NS}/Robot/Geometry/base_footprint/link2/link3']
# 혁무님 xacro (2026-11-10) → convert_to_archive.py → ../robot_usd. robot_train.usda = 그 위에 wrist ↔ link2 충돌만 끔
ROBOT_USD = HERE / 'robot_train.usda'

CELLS = [f'S{i}' for i in range(1, 13)]
# config/control.yaml poses.home (그리퍼 받침 위 접은 자세)
HOME = (-0.0061, -1.4511, 0.9511, -0.1181, 0.0230)
ARM_JOINTS = ('joint1', 'joint2', 'joint3', 'joint4', 'joint5')
GRIPPER_JOINTS = ('gripper_left_joint', 'gripper_right_joint')
# config/control.yaml gripper_open 0.0164 (간격 약 50 mm) · gripper_close −0.0016 (퍽 없으면 여기까지, 있으면 전류 한계로 멈춤)
GRIPPER_OPEN_REAL, GRIPPER_CLOSE_REAL = 0.0164, -0.0016
# 시뮬 손가락 충돌 메시는 0.0007 에서 서로 닿음 (실물 −0.0016) → 시뮬 명령은 이 차이 2.3 mm 만큼 옮김.
# 30 mm 퍽을 쥐면 시뮬 손가락이 0.0041 에서 멈추고 그리퍼 힘 약 3.5 N (빈손으로 닫으면 0.05 N) — grip 시험 2026-11-10
GRIP_SIM_OFFSET = 0.0023
GRIPPER_HOLD = 0.0041
GRIPPER_OPEN, GRIPPER_CLOSE = GRIPPER_OPEN_REAL + GRIP_SIM_OFFSET, GRIPPER_CLOSE_REAL + GRIP_SIM_OFFSET
GRIPPER_LIMIT = 0.0200                  # USD 상한 0.0175 → 시뮬 열림 0.0187 이 들어가게
GRIPPER_RESET = GRIPPER_CLOSE + 0.0003  # 리셋을 닿는 값보다 안쪽에 쓰면 손가락이 겹친 채 생겨 끼임 (그리퍼가 안 열림)
# 사각 퍽 한 변 30 · 길이 60 mm (perception/wrist_pose.hpp PUCK_D · PUCK_H), 17 g (sim_core/turtleninja_maze_env.py PUCK_MASS 실측 2026-10-24)
# 컵 아래쪽 안 폭 32 mm (URDF rack_cell_*_collision_wall) → 한쪽 여유 1 mm
PUCK_SIZE, PUCK_MASS = (0.030, 0.030, 0.060), 0.017
CYL_MASS = 0.013                        # 원기둥 퍽 (지름 30 · 길이 60 mm, 같은 출처 실측)
# maps/dice_map.yaml: 박스 한 변 0.205, 윗면 0.07, 정차 거리 (박스 중심 → 로봇 중심) 0.2575, 주사위 격자 간격 60 mm
BOX_SIZE, BOX_TOP, BOX_X, DICE_PITCH = 0.205, 0.07, 0.2575, 0.060


def _puck_cfg(name, color, kinematic=False):
    """kinematic = 적재 칸 퍽: 물리로 안 움직이는 장애물, env 가 매 스텝 로봇 몸체를 따라 옮김.
    17 g 퍽을 동적으로 두면 팔이 받침에서 떠오를 때 몸체가 튀며 컵 안 퍽이 13° 기울거나 54 mm 날아감 (팔은 8 mm 밖, 2026-11-10).
    충돌은 어차피 거리로 잼. 작업 퍽 (쥐고 옮기는 퍽) 만 동적."""
    return RigidObjectCfg(
        prim_path='{ENV_REGEX_NS}/' + name,
        spawn=sim_utils.CuboidCfg(
            size=PUCK_SIZE,
            rigid_props=[sim_utils.UsdPhysicsRigidBodyCfg(kinematic_enabled=kinematic),
                         PhysxRigidBodyCfg(max_depenetration_velocity=0.5, angular_damping=5.0,
                                           solver_position_iteration_count=16, solver_velocity_iteration_count=4)],
            mass_props=sim_utils.MassCfg(mass=PUCK_MASS),
            collision_props=sim_utils.UsdPhysicsCollisionCfg(),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=0.8, dynamic_friction=0.6),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color)),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(-1.0, 0.0, 0.03)))


def _cyl_cfg(name, color, kinematic=False):
    """원기둥 퍽. kinematic = 스테이션 (박스) 위 장애물로만 씀."""
    return RigidObjectCfg(
        prim_path='{ENV_REGEX_NS}/' + name,
        spawn=sim_utils.CylinderCfg(
            radius=PUCK_SIZE[0] / 2, height=PUCK_SIZE[2], axis='Z',
            rigid_props=[sim_utils.UsdPhysicsRigidBodyCfg(kinematic_enabled=kinematic),
                         PhysxRigidBodyCfg(max_depenetration_velocity=0.5, angular_damping=5.0,
                                           solver_position_iteration_count=16, solver_velocity_iteration_count=4)],
            mass_props=sim_utils.MassCfg(mass=CYL_MASS),
            collision_props=sim_utils.UsdPhysicsCollisionCfg(),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=0.8, dynamic_friction=0.6),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color)),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(-1.0, 0.5, 0.03)))


N_CYL = 12                              # 원기둥 장애물 퍽 (스테이션 위 · 적재함 칸 안, env_res 는 12 개까지 씀)


@configclass
class SceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(prim_path='/World/ground', spawn=sim_utils.GroundPlaneCfg())
    light = AssetBaseCfg(prim_path='/World/light', spawn=sim_utils.DomeLightCfg(intensity=2500.0))
    robot: ArticulationCfg = ArticulationCfg(
        prim_path='{ENV_REGEX_NS}/Robot',
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(ROBOT_USD),
            activate_contact_sensors=True,
            rigid_props=PhysxRigidBodyCfg(max_depenetration_velocity=1.0),
            # 팀 sim (sim_core/turtleninja_maze_env.py) 은 self-collision 끔 → 학습2 는 팔 ↔ 몸체 ↔ 적재함이 실제로 부딪혀야 해서 켬.
            # 솔버 32 / 4 = 팀 값 (8 / 1 이면 손목 · 손가락 관절 발산, 2026-10-21 팀 시험)
            articulation_props=[PhysxArticulationCfg(enabled_self_collisions=True, solver_position_iteration_count=32,
                                                     solver_velocity_iteration_count=4)]),
        # 몸체는 바닥에 고정하지 않음 (실물처럼 바퀴로 섬). fix_root_link 는 이 USD 의 payload 때문에 Isaac Lab 이 실패함
        init_state=ArticulationCfg.InitialStateCfg(joint_pos=dict(zip(ARM_JOINTS, HOME)) | {'gripper_.*': GRIPPER_RESET}),
        actuators={
            # 팔 XM430-W350 위치 모드: 이득 500 / 10 = 팀 sim 값, 힘 한계 4.1 N·m = USD (XM430 정지 토크), armature = 팀 sim 추정값
            'arm': ImplicitActuatorCfg(joint_names_expr=['joint[1-5]'], stiffness=500.0, damping=10.0, armature=0.01,
                                       joint_effort_limit=4.1),
            # 그리퍼: 실물은 전류 제한 위치 모드 (퍽 있으면 전류 한계로 멈춤 = 쥠). 1000 / 2 · 20 N · 0.15 m/s = 팀 sim 값.
            #   3000 으로 세게 쥐면 오히려 퍽이 빠짐: 시뮬은 손끝이 퍽 윗면 약 9 mm 아래만 쥐어 (실물 약 13 mm) 쐐기처럼 밀려 나감 (2026-11-10)
            'gripper': ImplicitActuatorCfg(joint_names_expr=['gripper_.*_joint'], stiffness=1000.0, damping=2.0,
                                           joint_effort_limit=20.0, joint_velocity_limit=0.15),
            # 바퀴 · 조향은 그 자리 유지 (팔 쓸 때 control_master 가 바퀴를 세움). 바퀴 = 속도 모드 목표 0:
            #   팀 sim damping 1 이면 팔 반동에 로봇이 15 mm 굴러감 (replay_check 2026-11-10) → 20 (속도 0.3 rad/s 에 6 N·m, XM430 한계 넘음 = 사실상 정지)
            'steer': ImplicitActuatorCfg(joint_names_expr=['steer_.*_joint'], stiffness=20.0, damping=0.3, armature=0.012),
            'drive': ImplicitActuatorCfg(joint_names_expr=['drive_.*_joint'], stiffness=0.0, damping=20.0, armature=0.005),
        })
    dice_box = AssetBaseCfg(
        prim_path='{ENV_REGEX_NS}/DiceBox',
        spawn=sim_utils.CuboidCfg(size=(BOX_SIZE, BOX_SIZE, BOX_TOP), collision_props=sim_utils.UsdPhysicsCollisionCfg(),
                                  visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.75, 0.55))),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(BOX_X, 0.0, BOX_TOP / 2)))
    work_puck: RigidObjectCfg = _puck_cfg('WorkPuck', (0.93, 0.63, 0.0))
    work_cyl: RigidObjectCfg = _cyl_cfg('WorkPuckCyl', (0.93, 0.63, 0.0))      # 원기둥 작업 퍽 (에피소드마다 사각 · 원기둥 중 하나만 씀)

    def __post_init__(self):
        # 팔끼리 충돌: 손 쪽 몸체 ↔ link2 · link3 접촉 힘 (PhysX 필터 접촉은 센서 하나가 몸체 하나만)
        for k, path in HAND_BODIES.items():
            setattr(self, f'self_{k}', ContactSensorCfg(prim_path=path, filter_prim_paths_expr=UPPER_ARM))
        for i in range(N_CYL):
            setattr(self, f'cyl_{i}', _cyl_cfg(f'Cyl_{i}', (0.36, 0.42, 0.48), kinematic=True))
        for c in CELLS:   # 적재함 칸마다 퍽 하나 (빈 칸 퍽은 로봇 뒤 바닥에 세워 둠)
            setattr(self, f'puck_{c}', _puck_cfg(f'Puck_{c}', (0.36, 0.42, 0.48), kinematic=True))


@configclass
class TaskCfg:
    tasks: tuple = ('store', 'retrieve')
    # 주사위 칸 (박스 중심 기준 앞뒤 −1 · 0 · +1, 좌우 −1 · 0 · +1). 먼 줄 (+1) 은 실물도 30° 다시 쥐기가 필요 (dice_map.yaml) → 처음엔 뺌
    dice_rows: tuple = (-1, 0)
    occupied_min: int = 0
    occupied_max_start: int = 3          # 커리큘럼: 처음 찬 칸 최대 개수
    occupied_max_end: int = 11
    curriculum_success: float = 0.6      # 최근 성공률이 이 값을 넘으면 찬 칸 최대 +1
    curriculum_window: int = 400         # 최근 몇 에피소드로 성공률을 보나


@configclass
class RewardCfg:
    # --- 안전 (사용자 요구: 충돌 · 떨어뜨림은 빼고, 안전하게 끝내면 줌) ---
    contact_eps: float = 0.001           # 이 거리 [m] 아래면 닿음
    collision: float = -1.0              # 닿음 한 스텝마다 (적재된 퍽 · 몸체 부품 · 박스 · 팔끼리 · 쥔 퍽 ↔ 다른 퍽)
    near_dist: float = 0.005             # 이 안으로 다가가면 0 → near 까지 점점
    near: float = -0.2
    severe_depth: float = 0.003          # 겹침 3 mm 넘거나 적재된 퍽이 밀리면 에피소드 끝
    # 적재된 퍽이 컵 밖으로 밀려남 (로봇 기준 10 mm · 20°) → 충돌 · 끝. 컵 안 흔들림 (몸체 진동, 퍽 17 g) 은 치지 않음:
    #   팔 · 퍽 접촉은 거리로 봄 (PhysX 충돌 껍질 ↔ 시각 메시 차이 1 mm 안 확인, 2026-11-10)
    stored_move: float = 0.010
    stored_tilt_deg: float = 20.0
    stand_depth: float = 0.001           # 그리퍼 받침은 앉는 자리라 닿아도 됨, 1 mm 넘게 파고들 때만 충돌
    self_force: float = 0.5              # 손 쪽 ↔ link2 · link3 접촉 힘 [N] 이 넘으면 팔끼리 닿음
    terminate_collision: float = -5.0
    drop: float = -5.0                   # 쥔 퍽을 놓침 (목표 자리 밖)
    own_cup_scrape: float = -0.05        # 넣을 · 뺄 칸 컵 벽 스침 (충돌로 치지 않고 작게) — 사용자와 정할 값
    # --- 진행 ---
    reach: float = 2.0                   # 손 → 퍽 거리 줄인 만큼 (퍼텐셜 차)
    grasp: float = 1.0                   # 그리퍼 간격 ≈ 퍽 폭 + 그리퍼 힘 + 손 안에 퍽 (한 번)
    carry: float = 3.0                   # 쥔 퍽 → 목표 거리 줄인 만큼
    place: float = 10.0                  # 목표 자리에 바르게 놓고 손 뗌 (그때까지 충돌 0 일 때만)
    place_xy_cell: float = 0.004         # 칸: 중심 4 mm 안 (컵 아래 여유 한쪽 1 mm 라 사실상 들어가면 됨)
    place_xy_box: float = 0.010          # 박스 주사위 칸: 10 mm 안
    place_tilt_deg: float = 5.0
    home: float = 2.0                    # 놓은 뒤 HOME 으로 돌아옴 (관절 오차 < home_tol)
    home_tol: float = 0.05
    home_shaping: float = 0.5
    # --- 부드러움 ---
    action_rate: float = -0.01
    joint_vel: float = -0.001
    time: float = -0.005


@dataclass
class TrainCfg:
    num_steps_per_env: int = 32
    max_iterations: int = 3000
    save_interval: int = 100
    experiment_name: str = 'training2'
    run_name: str = ''

    def runner_dict(self) -> dict:      # 팀 rl/tasks/local_planner/cfg.py 와 같은 rsl_rl 5 형식
        return {
            'num_steps_per_env': self.num_steps_per_env,
            'save_interval': self.save_interval,
            'experiment_name': self.experiment_name,
            'run_name': self.run_name,
            'logger': 'tensorboard',
            'obs_groups': {'actor': ['policy'], 'critic': ['policy', 'critic']},
            'algorithm': {
                'class_name': 'PPO', 'num_learning_epochs': 5, 'num_mini_batches': 4, 'clip_param': 0.2,
                'gamma': 0.99, 'lam': 0.95, 'value_loss_coef': 1.0, 'entropy_coef': 0.005,
                'learning_rate': 3e-4, 'max_grad_norm': 1.0, 'schedule': 'adaptive', 'desired_kl': 0.01,
            },
            'actor': {'class_name': 'MLPModel', 'hidden_dims': [256, 256, 128], 'activation': 'elu', 'obs_normalization': True,
                      'distribution_cfg': {'class_name': 'GaussianDistribution', 'init_std': 0.5}},
            'critic': {'class_name': 'MLPModel', 'hidden_dims': [512, 256, 128], 'activation': 'elu', 'obs_normalization': True},
        }


@configclass
class EnvCfg(DirectRLEnvCfg):
    # 물리 120 Hz, 정책 30 Hz
    decimation = 4
    episode_length_s = 25.0               # 실물 넣기 · 빼기 경로 약 10–20 s (arm_paths.yaml 경유점 · 속도) + 돌아오기
    sim: SimulationCfg = SimulationCfg(dt=1 / 120, render_interval=4, physics=PhysxCfg())
    scene: SceneCfg = SceneCfg(num_envs=256, env_spacing=1.5, replicate_physics=True)
    action_space = 6                      # 관절 5 개 목표 변화 + 그리퍼 (> 0 열기, ≤ 0 닫기)
    observation_space = 80                # env.py _get_observations policy (critic 은 따로 11)
    state_space = 0
    # 관절 최고 속도: 실물 빈 공간 40 °/s, 칸 근처 15 °/s (arm_paths.yaml 머리말). 정책이 칸 근처에서 줄이도록 상한만 둠
    max_joint_speed = 0.70                # [rad/s] ≈ 40 °/s
    point_spacing = 0.005                 # 팔 표면 점 간격 [m] (충돌 판정)
    task: TaskCfg = TaskCfg()
    reward: RewardCfg = RewardCfg()
