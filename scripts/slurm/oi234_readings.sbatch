#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=01:00:00
#SBATCH --job-name=oi234_read
#SBATCH --output=logs/oi234_read_%j.out
#SBATCH --error=logs/oi234_read_%j.err
# OI-234 读数（preregister.md 第 1～8 条）：参考读数、剂量、加仓账与减仓账、第 13／11 款。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd data/experiments/exp_oi234_20261006 && /usr/bin/time -v python3 readings.py)
