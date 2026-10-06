#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=03:00:00
#SBATCH --job-name=oi257_land
#SBATCH --output=logs/oi257_land_%j.out
#SBATCH --error=logs/oi257_land_%j.err
# OI-257 落地（v4.230）：联网补取新进清单年报并生成 NEW 受限资产表 → 两臂全量重建（§6.7 第 2、2b、3 步）→ 核对与信号日池带变化
# → 原线合格面（§12.1 对齐容差）→ BASE 14 起点（参考）。STAGE=inputs|build|run 只跑一段，缺省全跑。
# 2026-10-05 计算节点访问巨潮检索接口超时（新进清单 29 份年报定位卡住），inputs 段改在交互节点 `WORKERS=2 python3 inputs.py`，
# 本作业以 STAGE=buildrun 提交（重建、核对、合格面与 14 起点）。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi257_land_20261005
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = inputs ]; then
  (cd $EXP && /usr/bin/time -v python3 inputs.py)
fi
if [ "$STAGE" = all ] || [ "$STAGE" = build ] || [ "$STAGE" = buildrun ]; then
  (cd $EXP && /usr/bin/time -v python3 build.py && python3 check.py)
  python3 scripts/experimental/align_buy_line.py data/processed/a_share_daily_states_adopted.csv \
    $EXP/states/NEW/a_share_daily_states_adopted.csv --base-line 1.0034 --registered-share 16.916 > $EXP/align.txt 2>&1 || true
  cat $EXP/align.txt
fi
if [ "$STAGE" = all ] || [ "$STAGE" = run ] || [ "$STAGE" = buildrun ]; then
  (cd $EXP && WORKERS=30 /usr/bin/time -v python3 run.py)
fi
