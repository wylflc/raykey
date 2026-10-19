#!/bin/bash
#SBATCH -J oi290_read
#SBATCH -A tes21035
#SBATCH -p rome
#SBATCH -n 16
#SBATCH -t 02:00:00
#SBATCH --mem-per-cpu=1792M
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err
# OI-290 读数（preregister.md 读数 1～7）：月末观测采集 → 读数 → 买入线对齐与第 13 款，并写回测扫描配置。依赖 oi290_arms 作业。
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
E=data/experiments/exp_oi290_20261019
echo "=== [$(date +%H:%M:%S)] 采集月末观测 ==="
python3 $E/collect.py
echo "=== [$(date +%H:%M:%S)] 读数 1～5、7 ==="
python3 $E/readings.py > $E/readings.txt
echo "=== [$(date +%H:%M:%S)] 买入线对齐、第 13 款、扫描配置 ==="
python3 $E/post.py > $E/post.txt
echo "=== [$(date +%H:%M:%S)] 完成 ==="
