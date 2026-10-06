#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=05:00:00
#SBATCH --job-name=oi252_268_tests
#SBATCH --output=logs/oi252_268_tests_%j.out
#SBATCH --error=logs/oi252_268_tests_%j.err
# 两组估值准确性检验（预登记 exp_oi252_267_20261006、exp_oi266_268_20261006）：各臂全市场候选侧建带（v4.232 生产口径 + 研究开关）
# → 读数 1～7（scripts/experimental/caliber_fairness.py）。STAGE=build|test 只跑一段，缺省全跑。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = build ]; then
  (cd data/experiments/exp_oi252_267_20261006 && /usr/bin/time -v python3 build.py) &
  (cd data/experiments/exp_oi266_268_20261006 && /usr/bin/time -v python3 build.py) &
  wait
fi
if [ "$STAGE" = all ] || [ "$STAGE" = test ]; then
  (cd data/experiments/exp_oi252_267_20261006 && /usr/bin/time -v python3 test.py) &
  (cd data/experiments/exp_oi266_268_20261006 && /usr/bin/time -v python3 test.py) &
  wait
fi
