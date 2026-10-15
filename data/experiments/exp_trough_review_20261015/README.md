# 奥特维谷底锚研究数复核（2026-10-15，工作流 §7.3 谷底侧复核、§6.5.2.2）

- `brief.md`：任务说明；`inputs.json`：生产池带关键列、谷底侧复核行、业务属性、质量分层、模型盈利锚与 10-15 收盘。
- `annual_nopat.py`：模型口径逐年 NOPAT；`research_grid.py`：研究数代入生产带求研究口径 V（先还原除权再套用，收盘日 10-15）。
- `688516_奥特维.md`、`688516.json`：复核（锚偏高的来历、分产品三档、可证伪条件与来源）。下载件在 `data/scratch/experiments/exp_trough_review_20261015/`（可重下，不入库）。
- `apply_ruling.py`：按用户裁定写档案研究数与差距复核字段、追加决策日志（按 decision_id 去重）。

    python3 data/experiments/exp_trough_review_20261015/apply_ruling.py --conclusion 采用研究数

裁定：用户 2026-10-15 裁定采用研究数 7.90 亿，V 37.05→21.83、`P/V` 0.9566→1.62。回测日志 §12.341。
