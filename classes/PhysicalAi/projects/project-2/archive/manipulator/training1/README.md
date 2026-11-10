# 학습1: 누운 퍽을 한 번에 쥐어 적재함 12칸에 넣기 (보류, 2026-11-09)

누운 네모 퍽(34.8 × 34.8 × 60 mm)을 그리퍼 받침에 세워 다시 쥐지 않고, 한 번 쥐어서 적재함 S1–S12 모두에 세워 넣을 수 있는지 계산한 기록이에요. 일지: `Daily-I-learned/2026/2026.11.09/manipulator_log.md`

- 기준: 팀 저장소 `feat/moveit-config` cb78917 의 `config/arm_kinematics.yaml` (팔 모델), `config/rack_cells.yaml` (칸 위치), `sim/robot_sim/robot_description/robot.urdf` (메시 · 그리퍼 받침)
- 메시 파일: `~/robot_lab/examples/nt_urdf_release_20261027_swerve/meshes` (손가락 충돌 메시는 없어서 겉모양 메시 사용)
- 팀 저장소는 읽기만 함

## 결과

| 방식 | 결과 |
|---|---|
| 기울여 쥐고 손 안에서 뒤집기 | 12칸 중 S12 만. 팔 관절 5개라 칸 안 퍽 방향을 못 맞춤 (8칸 25–41° 틀어짐) |
| 수평으로 끝 쥐고 손을 세워 J5 로 맞추기 | 12칸 모두, P0 부터 차체 · 그리퍼 받침 충돌 없음. 단 손끝이 J1 에서 0.38–0.40 m 일 때만 |
| 박스 위 누운 퍽 9,736 자세 | 22% 만 쥘 수 있음 (퍽 끝이 박스 가장자리에서 약 20–30 mm 안), 박스 가운데 0% |

## 파일

| 파일 | 내용 |
|---|---|
| `armgeo.py` | 팔 모델 FK · IK (팀 `arm_kinematics.cpp` 와 같은 계산), URDF 메시 읽기 |
| `body.py` | 차체에 붙은 부품 (상판 · 그리퍼 받침 · 홀더) 메시 |
| `render_check_geo.py` | 팔 링크 점을 자세에 맞춰 놓기 |
| `check_end_grasp.py` | 처음 계산 (손 · 박스만 봄 → 틀림, 기록용) |
| `check_body.py` | 차체까지 넣은 쥐기 계산 |
| `check_v2.py` | 그리퍼 받침까지 넣은 전체 동작 (P0 → 쥐기 → 12칸 → P0) |
| `check_cups_path.py` | 12칸 넣기 · 옮기는 경로 |
| `sweep_pucks.py` | 누운 퍽 위치 · 각도 9,736 가지 |
| `one_grasp_anim.py`, `render2.py`, `render3.py`, `render_sweep.py` | GIF 만들기 |
| `poses/` | 계산한 관절 자세 (`v2grasp_*`, `v2cup_*`), 9,736 결과 (`sweep.npy`) |

## 다시 돌리기

자세 파일을 현재 폴더에서 읽으므로 `poses/` 에서 실행해요. 파이썬은 학습할 때 쓴 venv (numpy · matplotlib).

```bash
cd poses
~/pa-course/.venv-yolo/bin/python ../check_v2.py
~/pa-course/.venv-yolo/bin/python ../sweep_pucks.py
~/pa-course/.venv-yolo/bin/python ../render_sweep.py lying_puck_sweep.gif
```

## 아직 안 본 것

- 같은 박스의 다른 퍽, 칸에 이미 든 퍽, 경기장 벽
- 바퀴 · 조향 모듈의 실제 모양 (차체는 상자로 단순화)
- 비스듬히 다가가는 경우, 로봇이 서는 위치 오차 (가능 범위가 2 cm 뿐)
