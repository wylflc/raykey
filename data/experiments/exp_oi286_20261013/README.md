# OI-286 存量负面事件的质量复核（2026-10-13，工作流 §7.4、§5.7）

- `brief.md`：取证任务说明；`<代码>.json`：18 家的取证产物（事件事实、现状、公司安排、经营读数、未核项、来源）。
- `build_reviews.py`：逐家复核结论（治理分、旗标、证据说明、复核触发）→ `reviews.json`；`apply_event_reviews.py`：写分层表、档案、估值证据、决策日志并在负面事件登记表登记处置。
- `ann_probe.py`、`ann_fetch_text.py`、`news_probe.py`、`html_text.py`：取证用的公告与新闻读取脚本。全年公告清单与下载的原文在 `data/scratch/experiments/exp_oi286_20261013/`（可重取）。

    python3 data/experiments/exp_oi286_20261013/build_reviews.py
    python3 data/experiments/exp_oi286_20261013/apply_event_reviews.py

结论见回测日志 §12.337；结论为模型推导，用户可覆盖。
