#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=01:30:00
#SBATCH --job-name=oi234_land
#SBATCH --output=logs/oi234_land_%j.out
#SBATCH --error=logs/oi234_land_%j.err
# OI-234 偏离减仓落地：v4.235 正式状态上 CONTROL（现行 BASE）与 NEW（BASE ＋ --dev-trim 1.35）14 起点参考回测。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd data/experiments/exp_oi234_land_20261006 && WORKERS=56 /usr/bin/time -v python3 run.py)
