#!/bin/bash
#SBATCH -J rk_magic_formula
#SBATCH -p rome
#SBATCH -n 16
#SBATCH -t 02:00:00
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err

# 神奇公式在沪深 300 历年成分上的季度回测（实验，只描述；预登记
# data/experiments/exp_magic_formula_csi300_20261012/preregister.md）。
# 计算节点可访问外网：第 1 步取全部报告期的利润表、资产负债表与行业到 data/scratch（可断点续跑），第 2 步回测。
#
# 用法：
#   sbatch --account=tes21035 --export=ALL,STEP=fetch    scripts/slurm/magic_formula_csi300.sbatch
#   sbatch --account=tes21035 --export=ALL,STEP=backtest scripts/slurm/magic_formula_csi300.sbatch
#   sbatch --account=tes21035 --export=ALL,STEP=all      scripts/slurm/magic_formula_csi300.sbatch

set -euo pipefail
cd /home/zwang/project/mm_quant/raykey
STEP="${STEP:-all}"
EXP=exp_magic_formula_csi300_20261012
SCRATCH="data/scratch/experiments/$EXP"

if [ "$STEP" = fetch ] || [ "$STEP" = all ]; then
  echo "=== [$(date +%H:%M:%S)] 第 1 步：报表与行业 ==="
  python3 scripts/experimental/magic_formula_fetch_inputs.py --out-dir "$SCRATCH"
  # 网络失败的代码不进 done_codes.txt，补跑一遍
  python3 scripts/experimental/magic_formula_fetch_inputs.py --out-dir "$SCRATCH"
fi

if [ "$STEP" = backtest ] || [ "$STEP" = all ]; then
  echo "=== [$(date +%H:%M:%S)] 第 2 步：回测 ==="
  python3 scripts/experimental/magic_formula_backtest.py --inputs "$SCRATCH" --out-dir "data/experiments/$EXP"
fi
echo "=== [$(date +%H:%M:%S)] 完成 ==="
