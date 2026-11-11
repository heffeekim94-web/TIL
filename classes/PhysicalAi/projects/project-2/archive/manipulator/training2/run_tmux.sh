#!/usr/bin/env bash
# 학습2 를 tmux 세션에서 돌림 (터미널을 닫거나 SSH 가 끊겨도 계속). 결과 = training2/logs/<시각>_<이름>/ + 같은 이름 .log
#   bash run_tmux.sh t1                       # 기본 env 256 · 3000 iter (약 9 시간, RTX 5060 8 GB)
#   bash run_tmux.sh t1 --max_iterations 500  # train.py 인자 그대로 뒤에
# 보기: tmux attach -t train2   ·  빠져나오기: Ctrl-b 다음 d   ·  TensorBoard: tensorboard --logdir logs
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="${1:?실행 이름을 주세요 (예: t1)}"; shift
PY="$HOME/pa-course/IsaacLab-6.2/.venv/bin/python"
SESSION=train2
mkdir -p "$HERE/logs"
LOG="$HERE/logs/$(date +%Y%m%d_%H%M%S)_${NAME}.log"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux 세션 '$SESSION' 이 이미 있음 → tmux attach -t $SESSION 로 확인하거나 끝난 뒤 다시"; exit 1
fi
tmux new-session -d -s "$SESSION" -c "$HERE" \
  "env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMNI_KIT_ACCEPT_EULA=YES $PY train.py --run_name $NAME $* 2>&1 | tee $LOG; echo '[끝] Enter 로 닫기'; read"
echo "시작: tmux 세션 '$SESSION' · 로그 $LOG"
echo "보기: tmux attach -t $SESSION   (빠져나오기 Ctrl-b 다음 d)"
