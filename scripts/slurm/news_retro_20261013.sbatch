#!/bin/bash
# One-off: back-screen ~6 months of news titles for every pool member and holding
# with the §7.4 vocabulary (evidence in data/experiments/exp_news_retro_20261013/).
#SBATCH --account=tes21035
#SBATCH --partition=rome
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=1792M
#SBATCH --time=00:40:00
#SBATCH --job-name=news_retro
#SBATCH --output=logs/news_retro_%j.out
#SBATCH --error=logs/news_retro_%j.err
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
if [ "${RETRO_STAGE:-news}" = "announcements" ]; then
  # Older exchange announcements (2023-01-01 .. 2025-09-30) for the same universe.
  python3 -I data/experiments/exp_news_retro_20261013/ann_sweep_parallel.py data/processed/a_share_watchlist_quality_tiers.csv \
    data/scratch/experiments/exp_news_retro_20261013/pool_ann_20230101_20250930.jsonl 2023-01-01 2025-09-30 8
else
  python3 data/experiments/exp_news_retro_20261013/retro.py data/experiments/exp_news_retro_20261013/pool all 8
fi
