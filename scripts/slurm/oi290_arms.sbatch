#!/bin/bash
#SBATCH -J oi290_arms
#SBATCH -A tes21035
#SBATCH -p rome
#SBATCH -n 32
#SBATCH -t 03:00:00
#SBATCH --mem-per-cpu=1792M
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err
# OI-290 四臂全市场重建（data/experiments/exp_oi290_20261019/preregister.md）：两侧建带 8 进程并行 → 银行保险覆盖 → 持仓侧状态。
# 产物在 data/scratch/experiments/exp_oi290_20261019/states/，不碰生产文件。可选 EXP_ARMS=C+F3（缺省四臂）。
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
echo "=== [$(date +%H:%M:%S)] OI-290 四臂重建开始 ==="
python3 data/experiments/exp_oi290_20261019/build.py
echo "=== [$(date +%H:%M:%S)] 完成 ==="
ls -la data/scratch/experiments/exp_oi290_20261019/states/*/
