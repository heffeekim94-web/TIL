"""팀 팔 처짐 모델 (ros2_ws/src/manipulation/src/arm_kinematics.cpp sag_torques · encoder_goal_q 를 그대로 옮김).

실물: 명령 = 실제 − sag_c · τ(실제) (J2 · J3 · J4, τ = 중력 토크). config/arm_paths.yaml 은 이 '명령' 값이다.
시뮬 팔은 거의 안 처지므로 명령을 그대로 주면 손이 실물보다 높이 · 앞에 멈춘다 → 실제 자세로 되돌려서 준다:
  실제 = 명령 + sag_c · τ(실제)   (고정점 반복)
관절 값 변환: 팀 명령 [rad] ↔ 틱 (zero_tick, 4096 틱/바퀴) ↔ 모델 관절 (ref_tick · q_deg_at_ref · sign) — arm_state.cpp · arm_kinematics.cpp 와 같음.
"""
from pathlib import Path

import numpy as np
import yaml

TEAM = Path('/home/haeminkim/바탕화면/git/Project2_Turtle_Ninja')
G = 9.81
T2R = 2 * np.pi / 4096
# hardware_map.yaml zero_tick (joint1 은 4104 를 한 바퀴 뺀 8 로 적음 → 틱 범위 안으로 바퀴 수를 맞춰 씀)
ZERO_TICK = np.array([8, 2048, 2048, 2048, 2048], dtype=float)


class SagModel:
    def __init__(self):
        m = yaml.safe_load(open(TEAM / 'config' / 'arm_kinematics.yaml'))['/**']['ros__parameters']['arm_model']
        self.Tb = np.array(m['T_base_armbase']).reshape(4, 4)
        self.JT = np.array(m['joint_T']).reshape(5, 4, 4)
        self.axis = np.array(m['axis']).reshape(5, 3)
        self.tip5 = np.array(m['tip5'])
        self.sag_c = m['sag_c']
        self.ref_tick, self.q_ref = np.array(m['ref_tick']), np.radians(m['q_deg_at_ref'])
        self.sign = np.array(m['sign'])
        self.tick_lo, self.tick_hi = np.array(m['tick_lo']), np.array(m['tick_hi'])

    # --- 관절 값 변환
    def cmd_to_ticks(self, cmd):
        t = ZERO_TICK + np.asarray(cmd) / T2R
        t = np.where(t < self.tick_lo, t + 4096, t)       # 여러 바퀴 관절 (joint1) 은 범위 안 바퀴로
        return np.where(t > self.tick_hi, t - 4096, t)

    def ticks_to_cmd(self, t):
        t = np.asarray(t)
        return (t - ZERO_TICK - np.where(t - ZERO_TICK > 2048, 4096, 0)) * T2R

    def ticks_to_q(self, t):
        return self.q_ref + self.sign * (np.asarray(t) - self.ref_tick) * T2R

    def q_to_ticks(self, q):
        return self.ref_tick + (np.asarray(q) - self.q_ref) / (self.sign * T2R)

    # --- 모델 기구학 · 처짐
    def frames(self, q):
        out, T = [], self.Tb.copy()
        for j in range(5):
            a = self.axis[j] / np.linalg.norm(self.axis[j])
            K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
            R = np.eye(4)
            R[:3, :3] = np.eye(3) + np.sin(q[j]) * K + (1 - np.cos(q[j])) * K @ K
            T = T @ self.JT[j] @ R
            out.append(T)
        return out

    def sag_torques(self, q, held_kg):
        F = self.frames(q)
        o2, o3, o4, p5 = F[1][:3, 3], F[2][:3, 3], F[3][:3, 3], F[4][:3, 3]
        tip = F[4][:3, :3] @ self.tip5 + p5
        masses = [((o2 + o3) / 2, 0.12, 2), ((o3 + o4) / 2, 0.12, 3), ((o4 + p5) / 2, 0.10, 4),
                  (p5 + (tip - p5) / 3, 0.40, 4), (tip, held_kg, 4)]
        o = {2: o2, 3: o3, 4: o4}
        tau = []
        for j in (2, 3, 4):
            ax = F[j - 1][:3, :3] @ self.axis[j - 1]
            tau.append(sum(np.cross(p - o[j], [0, 0, -kg * G]) @ ax for p, kg, frm in masses if kg > 0 and j <= frm))
        return np.array(tau)

    def true_from_cmd(self, cmd, held_kg=0.0, iters=20):
        """팀 명령 [rad] (arm_paths.yaml) → 실물 실제 자세 [rad, 팀 관절 값]."""
        qc = self.ticks_to_q(self.cmd_to_ticks(cmd))
        q = qc.copy()
        for _ in range(iters):
            q = qc.copy()
            q[1:4] += self.sag_c * self.sag_torques(q_last, held_kg) if _ else 0.0
            q_last = q
        return self.ticks_to_cmd(self.q_to_ticks(q))

    def cmd_from_true(self, q_true_cmd, held_kg=0.0):
        """검산용 = 팀 encoder_goal_q: 실제 자세 → 명령."""
        q = self.ticks_to_q(self.cmd_to_ticks(q_true_cmd))
        q[1:4] -= self.sag_c * self.sag_torques(q, held_kg)
        return self.ticks_to_cmd(self.q_to_ticks(q))
