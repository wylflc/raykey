#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=03:00:00
#SBATCH --job-name=oi269_land
#SBATCH --output=logs/oi269_land_%j.out
#SBATCH --error=logs/oi269_land_%j.err
# OI-269 银行 BV 年增速封顶 7% 落地：两臂两侧银行保险覆盖重建与持仓侧合成 → 核对与信号日实时变化 → 原线合格面 → BASE 14 起点（参考）。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi269_bank_land_20261006
(cd $EXP && /usr/bin/time -v python3 build.py && python3 check.py)
python3 scripts/experimental/align_buy_line.py data/processed/a_share_daily_states_adopted.csv \
  $EXP/states/NEW/a_share_daily_states_adopted.csv --base-line 1.0034 --registered-share 16.916 > $EXP/align.txt 2>&1 || true
cat $EXP/align.txt
(cd $EXP && WORKERS=56 /usr/bin/time -v python3 run.py)
