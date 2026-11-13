"""1번 적재 모델 B단계 (사용자 2026-11-13): 혁무님 동작 (라이브러리 v4 적재 경로) 을 먼저 따라 하게 배우고 (bc_store.py) 강화학습으로 다듬음.
보정 학습 (env_res) 과 다른 점: 정책이 관절 속도 · 그리퍼를 직접 정함 (경로에 시간으로 묶이지 않음).
  진행 p = 지금 관절에 가장 가까운 앞쪽 경유점 (뒤로는 안 감) → 그 경유점 기준으로 다음 퍽 바꾸기 · 관측 (혁무님 계획 자세 · 앞 자세) · 성공 판정.
  팀 control_master 가 Jetson 에서 그 경로를 계산하므로 배포 때도 관측으로 줄 수 있음.
행동: a[0:5] 관절 속도 × max_joint_speed, a[5] 그리퍼 목표 (−1 닫힘 … +1 열림, 연속 = 칸 안 살짝 벌림도 됨).
보상: env_res 그대로 (충돌 · 바퀴 뜸 실패 · 기울기 · 쥠 · 놓음 · HOME · 안정) + 진행 보상 (빠를수록) − 계획에서 벗어난 만큼 (작게).
"""
import torch

from isaaclab.utils import configclass

from cfg import GRIPPER_CLOSE, GRIPPER_OPEN
from env_res import ResEnvCfg, Training2ResEnv


@configclass
class StoreEnvCfg(ResEnvCfg):
    library: str = 'logs/library_chain_v4.npz'
    store_only: bool = True               # 1번 모델 = 적재만
    max_joint_speed = 2.70                # [rad/s] 혁무님 빈 공간 150 °/s 가 들어가게 (가감속은 정책 + 감점이 정함)
    window: int = 10                      # 진행: 앞 경유점 몇 개 안에서 가장 가까운 것
    on_track: float = 0.03                # 다음 경유점에 이만큼 [rad] 붙어 있으면 시간대로 한 칸
    progress: float = 0.05                # 경유점 하나 나아갈 때 (빠를수록 보상)
    deviate: float = -0.2                 # 계획 자세에서 벗어난 관절 거리 [rad] 당 (스텝마다, 작게)
    dev_free: float = 0.15                # 이만큼은 봐줌 (다른 길로 피해 가도 되게)
    res_penalty: float = 0.0              # env_res 의 보정 크기 벌점 = 여기서는 관절 속도라 끔 (움직임 변화 벌점은 그대로)


class Training2StoreEnv(Training2ResEnv):
    cfg: StoreEnvCfg

    def __init__(self, cfg: StoreEnvCfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        self.p = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.dp = torch.zeros(self.num_envs, device=self.device)
        self.sub = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        if cfg.store_only:
            self.store_ids = [i for i, m in enumerate(self.lib_meta) if m['task'] == 'store']
            print(f'[env_store] 적재 에피소드 {len(self.store_ids)} 개', flush=True)

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ids = torch.as_tensor(env_ids, device=self.device)
        if self.cfg.store_only and (self.fixed is None or not len(self.fixed)):
            from collections import deque
            pick = torch.tensor(self.store_ids, device=self.device)[torch.randint(0, len(self.store_ids), (len(ids),), device=self.device)]
            self.fixed = deque(pick.tolist()); auto = True
        else:
            auto = False
        super()._reset_idx(ids)
        if auto:
            self.fixed = None
        self.p[ids] = 0
        self.dp[ids] = 0

    def expert_action(self):
        """혁무님 경로 따라가기: 다음 경유점을 2 스텝에 (라이브러리 시간 간격 = 2 정책 스텝)."""
        nxt = torch.minimum(self.p + 1, self.libN[self.li] - 1)
        dq = (self.libQ[self.li, nxt] - self.q_target) / (2 * self.cfg.max_joint_speed * self.step_dt)
        g = self.libG[self.li, nxt]
        ga = 2 * (g - GRIPPER_CLOSE) / (GRIPPER_OPEN - GRIPPER_CLOSE) - 1
        return torch.cat([dq.clamp(-1, 1), ga.clamp(-1, 1)[:, None]], -1)

    def _pre_physics_step(self, actions):
        self._advance_jobs()
        self._follow_robot()
        a = actions.clamp(-1.0, 1.0)
        self.actions = a
        if self.scripted is not None:
            a = self.expert_action()
        self.q_target = torch.maximum(torch.minimum(self.q_target + a[:, :5] * self.cfg.max_joint_speed * self.step_dt, self.q_hi), self.q_lo)
        self.grip_target = (GRIPPER_CLOSE + (a[:, 5] + 1) / 2 * (GRIPPER_OPEN - GRIPPER_CLOSE)).clamp(GRIPPER_CLOSE - 0.001, GRIPPER_OPEN)
        # 진행: 지금 관절 (목표) 에 가장 가까운 앞쪽 경유점
        W = self.cfg.window
        last = self.libN[self.li] - 1
        js = torch.minimum(self.p[:, None] + torch.arange(W + 1, device=self.device)[None], last[:, None])
        d = (self.libQ[self.li[:, None], js] - self.q_target[:, None]).norm(dim=-1)
        newp = js.gather(1, d.argmin(1, keepdim=True))[:, 0]
        # 멈춤 구간 (같은 자세 경유점 여럿 = 그리퍼 닫기 · 확인 기다림) 은 가장 가까운 점이 안 바뀜 → 다음 경유점에 붙어 있으면 2 스텝에 1 칸 (라이브러리 시간)
        on = (self.libQ[self.li, torch.minimum(self.p + 1, last)] - self.q_target).norm(dim=-1) < self.cfg.on_track
        self.sub = (self.sub + 1) % 2
        newp = torch.maximum(newp, torch.where(on & (self.sub == 0), torch.minimum(self.p + 1, last), self.p))
        self.dp = (newp - self.p).float()
        self.p = torch.maximum(self.p, newp)
        self.t = torch.where(self.p >= last, torch.maximum(self.t + 1, 2 * self.p), 2 * self.p)

    def _get_rewards(self):
        rew = super()._get_rewards()
        k = self.p
        dev = (self.libQ[self.li, k] - self.robot.data.joint_pos.torch[:, self.arm_ids]).norm(dim=-1)
        extra = self.cfg.progress * self.dp + self.cfg.deviate * (dev - self.cfg.dev_free).clamp(min=0)
        for name, v in (('진행', self.cfg.progress * self.dp), ('벗어남', self.cfg.deviate * (dev - self.cfg.dev_free).clamp(min=0))):
            if hasattr(self, 'ep_parts'):
                self.ep_parts.setdefault(name, torch.zeros_like(v))
                self.ep_parts[name] += torch.nan_to_num(v)
        return rew + torch.nan_to_num(extra)
