# 成长股结构性增长复核第二批（2026-10-13，工作流 §7.3、§6.5.2.2、§9.3.6 第 2 条）

- `brief.md`：复核任务说明；`inputs.json`：五只的登记行、结构性增长复核行、生产带关键列与模型盈利锚。
- `annual_nopat.py`：模型口径逐年 NOPAT；`research_grid.py`：研究数代入生产带求研究口径 V（除权归一化过的带先还原再套用）。
- `<代码>_<名称>.md`、`<代码>.json`：百济神州、沪电股份、中微公司、鼎龙股份、天孚通信的复核；`300054_broker_forecasts.csv`、`002463_norm.py` 为附带的研报预测与算式。
- `apply_reviews.py`：按用户 2026-10-13 裁定改档案、登记表与临时冻结名单，追加决策日志；`rulings.json` 为摘要。

    python3 data/experiments/exp_growth_reviews_20261013/apply_reviews.py

裁定：百济神州、沪电股份、鼎龙股份采用研究数；中微公司、天孚通信维持模型；登记表修订三处。回测日志 §12.338。
