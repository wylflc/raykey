#!/bin/bash
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=00:40:00
#SBATCH --job-name=base_longrun_at
#SBATCH --output=logs/base_longrun_attrib_%j.out
#SBATCH --error=logs/base_longrun_attrib_%j.err
# 现行 BASE 14 起点单跑（描述性）：逐日净值、逐日逐代码盈亏与滚动窗口，summary 须与在册 BASE 逐字段一致
set -euo pipefail
cd /gpfs/scratch1/shared/zwang/mm_quant/RayKey/data/experiments/exp_base_longrun_attrib_20261007
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKERS="${WORKERS:-8}" /usr/bin/time -v python3 run.py
