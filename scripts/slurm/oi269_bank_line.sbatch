#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=64
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=01:30:00
#SBATCH --job-name=oi269_line
#SBATCH --output=logs/oi269_line_%j.out
#SBATCH --error=logs/oi269_line_%j.err
# OI-269 银行 BV 年增速封顶落地：安装口径（NEW 状态 + 买入线 1.0093）对 CONTROL 的 14 起点参考回测。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
(cd data/experiments/exp_oi269_bank_land_20261006 && WORKERS=56 /usr/bin/time -v python3 run_line.py)
