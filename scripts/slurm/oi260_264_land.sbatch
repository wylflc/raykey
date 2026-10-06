#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=04:00:00
#SBATCH --job-name=oi260_264_land
#SBATCH --output=logs/oi260_264_land_%j.out
#SBATCH --error=logs/oi260_264_land_%j.err
# 第一批修正落地（OI-260／OI-264／OI-262／OI-261 估值四项与 OI-243 单票上限分母）：六臂全量重建（§6.7 第 2、2b、3 步）→ 核对与信号日池带变化
# → 原线合格面（§12.1 对齐容差）→ BASE 14 起点四臂（参考）。STAGE=build|run 只跑一段，缺省全跑。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi260_264_land_20261006
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = build ]; then
  (cd $EXP && /usr/bin/time -v python3 build.py && python3 check.py)
  python3 scripts/experimental/align_buy_line.py data/processed/a_share_daily_states_adopted.csv \
    $EXP/states/ALL/a_share_daily_states_adopted.csv --base-line 1.0034 --registered-share 16.916 > $EXP/align.txt 2>&1 || true
  cat $EXP/align.txt
fi
if [ "$STAGE" = all ] || [ "$STAGE" = run ]; then
  (cd $EXP && WORKERS=56 /usr/bin/time -v python3 run.py)
fi
