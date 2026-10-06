#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=04:00:00
#SBATCH --job-name=oi270_test
#SBATCH --output=logs/oi270_test_%j.out
#SBATCH --error=logs/oi270_test_%j.err
# OI-270 汇兑与研发年限估值准确性检验（预登记 exp_oi270t_20261006）：四臂全市场候选侧建带 → C 对生产逐字节核对 → 读数 1～6。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi270t_20261006
(cd $EXP && /usr/bin/time -v python3 build.py)
for f in roic_bands.csv roic_daily_raw.csv; do
  a=$(sha256sum $EXP/states/C/$f | cut -d' ' -f1); b=$(sha256sum data/processed/$f | cut -d' ' -f1)
  if [ "$a" = "$b" ]; then echo "C 复现 $f"; else echo "C 不同 $f $a $b"; fi
done | tee $EXP/reproduction.txt
(cd $EXP && /usr/bin/time -v python3 test.py)
