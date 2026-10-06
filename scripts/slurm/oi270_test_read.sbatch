#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=02:00:00
#SBATCH --job-name=oi270_read
#SBATCH --output=logs/oi270_read_%j.out
#SBATCH --error=logs/oi270_read_%j.err
# OI-270 汇兑与研发年限估值准确性检验读数段（建带已完成，exp_oi270t_20261006）。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd data/experiments/exp_oi270t_20261006 && /usr/bin/time -v python3 test.py)
