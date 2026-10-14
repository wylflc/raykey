# 成长股预做重点复核与差距复核（2026-10-14，工作流 §9.3.6 第 3、6 条、§7.3）

- `brief.md`：德业股份预做重点复核的任务说明；`inputs.json`：登记行、结构性增长复核行、生产带关键列（含预告叠加）、模型盈利锚与 10-14 收盘。
- `annual_nopat.py`：模型口径逐年 NOPAT；`research_grid.py`：研究数代入生产带求研究口径 V（先还原除权再套用，收盘日 10-14）。
- `605117_德业股份.md`、`605117.json`：德业股份复核（研究数 46.2 亿、可复制性、需求、下跌原因、证伪条件核对与来源）。下载件在 `data/scratch/experiments/exp_growth_prereview_20261014/`（可重下，不入库）。
- `apply_rulings.py`：按用户 2026-10-14 裁定改档案与登记表、追加决策日志（按 decision_id 去重）。两只的第 6 条核对先由 `growth_stocks.py --check` 登记。

    python3 data/experiments/exp_growth_prereview_20261014/apply_rulings.py --deye 通过

裁定：德业股份重点复核通过，研究数登记不采用，登记行证伪条件改为分产品口径；沪电股份维持采用研究数 48.80 亿；核对与复核日记证据日 10-15（v4.252，结 OI-287）。回测日志 §12.340。
