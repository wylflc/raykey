# OI-250 业务属性登记扩到池内全部 ROIC 路径（2026-10-01，v4.228）

- `task.md`：判定任务（口径 v2 见 `../exp_oi250_pilot_20261001/rubric.md`）；`build_inputs.py` → `inputs.csv`：尚未登记的 116 只的仓库研究记录与毛利率、营收走势。
- `attributes_part1～4.csv`：四个子代理各判 29 只。
- `register.py`：核对标签、派生规则与依据日，与已登记 57 只合并（补 `replicability_confidence`、`rejudged_from`／`rejudged_at`），写 `attributes.csv`、`register.json` 与生产登记表 `data/processed/a_share_business_attributes.csv`。

    python3 build_inputs.py && python3 register.py

合并后 173 只：稳定型 82、结构成长型 48、成本领先周期型 24、可复制成长型 14、价格周期型 5（此后阳光电源、中际联合经重点复核改判，见 `../exp_growth_reviews_20261001/`）。回测日志 §12.308。
