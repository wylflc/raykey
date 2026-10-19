#!/bin/bash
#SBATCH -J oi290_sweep
#SBATCH -A tes21035
#SBATCH -p rome
#SBATCH -n 64
#SBATCH -t 03:00:00
#SBATCH --mem-per-cpu=1792M
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err
# OI-290 读数 8：标准起点集回测参考读数（全样本与去赢家 A），按 §12.1（v4.254）只报不用。依赖 oi290_read 作业写出的 sweep_arms.txt。
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
E=data/experiments/exp_oi290_20261019
python3 scripts/sweep_backtest_configs.py $E/sweep_arms.txt --out $E/sweep.txt --workers 58 --title "OI-290 g0 = 0 下限四臂"
python3 scripts/sweep_backtest_configs.py --report --out $E/sweep.txt > $E/sweep_report.txt
