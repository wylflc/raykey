# OI-288 东财预告表对池成员预告的覆盖（2026-10-15，工作流 §6.4）

- `scan_market.py`：取 2023-10-15～2026-10-15 全市场东财公告「业绩预告」（f_node=1、s_node=5）与「业绩快报」（s_node=6）栏目，按代码与公告日 ±3 天对照预告表 `RPT_PUBLIC_OP_NEWPREDICT` 与快报表 `RPT_FCI_PERFORMANCEE`；全市场结果在 `data/scratch/experiments/exp_oi288_20261015/market_previews.csv`（可重取）。
- `pool_previews.csv`：现有 182 只池成员的 593 条（`in_table` 为空即表内无对应行）。
- `analyze.py` → `summary.txt`：池内与全市场的表外条数与形态。

    python3 data/experiments/exp_oi288_20261015/scan_market.py . data/scratch/experiments/exp_oi288_20261015/market_previews.csv
    python3 data/experiments/exp_oi288_20261015/analyze.py data/scratch/experiments/exp_oi288_20261015/market_previews.csv

结论见回测日志 §12.342。乐鑫科技叠加演算（V 66.31→72.40）按 §6.7 第 4 步脚本对临时预告文件试跑，未写生产带。
