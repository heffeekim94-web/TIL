#!/usr/bin/env bash
# 밤새 차례로 (tmux 세션 night): 1) 기본 경로만 실패율 (라이브러리 v4, 64 개) → 2) 보정 학습 r4 (1500 번) → 3) 툭 건드리기 빠른 설정 n2fast (200 번)
#   bash night_run.sh   ·   보기: tmux attach -t night
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMNI_KIT_ACCEPT_EULA=YES $HOME/pa-course/IsaacLab-6.2/.venv/bin/python"
LIB=logs/library_chain_v4.npz
T=$(date +%Y%m%d_%H%M%S)
if tmux has-session -t night 2>/dev/null; then echo "tmux 세션 night 이 이미 있음"; exit 1; fi
tmux new-session -d -s night -c "$HERE" "
  $PY check_res.py --n 64 --start 0 --library $LIB 2>&1 | tee logs/${T}_baseline_v4.log;
  $PY train.py --res --library $LIB --max_iterations 1500 --run_name r4 2>&1 | tee logs/${T}_r4.log;
  $PY train.py --nudge --max_iterations 200 --run_name n2fast --set episode_length_s=2.0 max_joint_speed=1.09 2>&1 | tee logs/${T}_n2fast.log;
  echo '[끝] Enter 로 닫기'; read"
echo "시작: tmux 세션 night · 로그 logs/${T}_baseline_v4.log → ${T}_r4.log → ${T}_n2fast.log"
