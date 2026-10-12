#!/bin/bash
#SBATCH -J rk_capnone
#SBATCH -p rome
#SBATCH -n 48
#SBATCH -t 01:00:00
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err

# 不设单票上限（`--position-cap 0`）对现行在册 BASE：①两臂两遍（全样本＋A）；②剔除集 U 固定单遍；③两个长跑锚点带逐日逐代码盈亏与成交流水。
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_position_cap_none_20261012
mkdir -p "$EXP/runs/eb"
BASECMD=$(python3 -c "import sys; sys.path.insert(0,'scripts'); import sweep_backtest_configs as s; print(s.BASE)")
echo "=== [$(date +%T)] 锚点逐笔（后台）==="
for START in 2011-11-01 2009-11-01; do
  for ARM in BASE CNONE; do
    EXTRA=""; [ "$ARM" = CNONE ] && EXTRA="--position-cap 0"
    TAG="${ARM}${START//-/}"
    # shellcheck disable=SC2086
    python3 "$EXP/engine.py" $BASECMD $EXTRA --artifacts --since "$START" --label-suffix "_$TAG" --out-dir "$EXP/runs" \
      --equity-bond-log-dir "$EXP/runs/eb" --trade-log "$EXP/runs/${TAG}_tradelog.csv" > "$EXP/runs/$TAG.log" 2>&1 &
  done
done
echo "=== [$(date +%T)] 两臂两遍 ==="
python3 scripts/sweep_backtest_configs.py "$EXP/config.txt" --out "$EXP/sweep.txt" --workers 40 \
  --title "不设单票上限对现行 BASE（全样本＋A）" | tee "$EXP/report.txt"
U=$(python3 - "$EXP" <<'PY'
import csv, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
import sweep_backtest_configs as sw
codes = set()
for arm in ('BASE', 'CNONE'):
    row = [r for r in csv.DictReader((Path('data/backtest') / f"summary_{sw.summary_tag(arm, sw.EX5_ANCHOR_START)}.csv").open(encoding='utf-8'))
           if r['策略'].startswith('trend_')][-1]
    codes |= {c for c in row[sw.EX5_FIELD].split('/') if c}
print(','.join(sorted(codes)))
PY
)
echo "=== [$(date +%T)] 剔除集 U=$U ==="
python3 scripts/sweep_backtest_configs.py "$EXP/config.txt" --out "$EXP/sweep_U.txt" --workers 40 --exclude-codes "$U" \
  --title "不设单票上限对现行 BASE（剔除集 U）" | tee "$EXP/report_U.txt"
wait
echo "=== [$(date +%T)] 完成 ==="
