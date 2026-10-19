#!/bin/bash
#SBATCH -J oi291_kit
#SBATCH -A tes21035
#SBATCH -p rome
#SBATCH -N 1
#SBATCH -n 16
#SBATCH -t 01:00:00
#SBATCH --mem-per-cpu=1792M
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err
# OI-291 池内逐家独立审计的批次材料（data/experiments/exp_independent_pool_2026q3/README.md）：
# 东财 F10 三表与主营、腾讯行情、同业比较、公告原文（PDF 与逐页文本）、近 6 个月资讯标题，生成数据包。
# 原始数据写 data/scratch/experiments/exp_independent_pool_2026q3/$BATCH/raw/，数据包写实验目录 $BATCH/packs/。
# 代码之间用 + 分隔（--export 用逗号分隔变量）：
#   sbatch --account=tes21035 --export=ALL,BATCH=b01,PRICE_DATE=2026-10-19,CODES=600066+688041 scripts/slurm/oi291_kit.sbatch
set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
: "${BATCH:?Set BATCH, e.g. b01}"
: "${PRICE_DATE:?Set PRICE_DATE (Beijing close date)}"
: "${CODES:?Set CODES separated by +}"
echo "=== [$(date +%H:%M:%S)] OI-291 批次材料 $BATCH 价格日 $PRICE_DATE ==="
python3 -I data/experiments/exp_independent_pool_2026q3/tools/build_kit.py --batch "$BATCH" --price-date "$PRICE_DATE" \
  --codes "${CODES//+/,}" --workers 16 ${EVIDENCE_UNTIL:+--evidence-until "$EVIDENCE_UNTIL"}
echo "=== [$(date +%H:%M:%S)] 完成 ==="
