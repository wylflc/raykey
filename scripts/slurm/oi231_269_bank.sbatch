#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=02:00:00
#SBATCH --job-name=oi231_bank
#SBATCH --output=logs/oi231_bank_%j.out
#SBATCH --error=logs/oi231_bank_%j.err
# OI-269＋OI-231 银行检验（preregister.md）：月末五臂银行 V、包含检验、截面排序、买入区识别力。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd data/experiments/exp_oi231_269_20261006 && /usr/bin/time -v python3 bank_test.py)
