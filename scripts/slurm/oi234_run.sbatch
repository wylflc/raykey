#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=04:00:00
#SBATCH --job-name=oi234_run
#SBATCH --output=logs/oi234_run_%j.out
#SBATCH --error=logs/oi234_run_%j.err
# OI-234 回踩加仓与偏离减仓：8 臂 × 14 起点（全样本带逐周期产物与成交流水、A、U），CONTROL 复现在册 BASE（preregister.md）。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi234_20261006
(cd $EXP && WORKERS=62 /usr/bin/time -v python3 run.py)
