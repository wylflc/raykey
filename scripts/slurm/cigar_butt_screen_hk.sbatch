#!/bin/bash
#SBATCH -J rk_cigar_hk
#SBATCH -A tes21035
#SBATCH -p rome
#SBATCH -n 16
#SBATCH -t 02:00:00
#SBATCH --mem-per-cpu=1792M
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err

# 工作流程 §6.10 第 7 条港股烟蒂池粗筛：全市场取数约 1,000 页，单进程顺序请求
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
: "${HK_SIGNAL_DATE:?Set HK_SIGNAL_DATE to the HK trading day}"
python3 scripts/screen_cigar_butts_hk.py --signal-date "$HK_SIGNAL_DATE" ${HK_EXTRA_ARGS:-}
