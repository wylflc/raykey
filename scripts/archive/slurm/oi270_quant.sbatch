#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=01:00:00
#SBATCH --job-name=oi270_quant
#SBATCH --output=logs/oi270_quant_%j.out
#SBATCH --error=logs/oi270_quant_%j.err
# OI-270 全池量化：池成员候选侧带五臂（CONTROL／FX／M0／ML／RD5，研究开关缺省关）→ 信号日 2026-09-30 池带与叠加 → 读数。
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXP=data/experiments/exp_oi270_20261006
(cd $EXP && /usr/bin/time -v python3 build.py && python3 compare.py)
