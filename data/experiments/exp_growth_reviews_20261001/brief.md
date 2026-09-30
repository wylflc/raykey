# 成长股复核任务说明（2026-10-01）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`，A 股研究。本目录只放复核材料，**不得改动** `data/processed/`、`docs/`、`scripts/` 下任何文件；不得读 `docs/xzy/`。

## 背景

生产估值模型（工作流 §6.5.1）的峰守卫把「当期回报 ÷ 十年中位」偏高的公司当作周期高点，每股 NOPAT 改取五年中位，结构性成长公司的 V 因此被大幅压低。§7.3 结构性增长复核要求登记「研究正常化盈利」。个人投资体系第 5.12 节的业务属性登记已把以下公司判为 `结构成长型`：差异化定价、需求结构扩张、难复制（同业两年内难以扩产压价）。

研究数规则（工作流 §6.5.2.2，原文要点）：
- `research_nopat_yi`：研究估计的**正常化**盈利，亿元，与模型同口径：税后经营利润，剔除金融收益，含权益法损益与少数股东份额。
- 研究原文为归母净利时，按模型股权桥反解：`NOPAT = 归母 ÷ (1 − 生产带 minority_share) + (最新年报 NOPAT − 合并净利)`，注明两项取值。最新年报 NOPAT 用本目录 `annual_nopat.py` 算的模型口径（研发资本化后）数。
- **同一产能口径**：以未来产量或未建成产能为基础的盈利，按现有已投产产能重述；扩产由模型增速腿计价，不进研究数。
- 须同时给 `research_evidence_date`（所依据证据的公开可得日）、`research_falsifier`（可证伪条件，≤ 60 字，写成可量的指标与阈值）、`research_source`（出处与推算过程）。
- 「正常化」指穿越周期可持续的盈利水平，不是峰值、不是谷底。需判断当前毛利率与出货中有多少是短期稀缺溢价（同业扩产后会被压回），有多少是技术、认证、规模带来的持久部分。
- 不得为希望得到的 `P/V` 反推研究数。

参考写法：`data/processed/a_share_valuation_dossiers.csv` 中五粮液、亚钾国际、牧原股份、爱玛科技的 `research_*` 与 `divergence_*` 列。

## 已备输入

- `inputs.json`：各公司的业务属性登记行、可复制性 v2 重判行、结构性增长复核行、生产池带关键列与模型盈利锚（`model_anchor_yi` = 每股 NOPAT × shares_est，亿元）。
- `annual_nopat.py <代码,...>`：模型口径（研发资本化后）逐年 NOPAT、合并净利、归母、少数股东损益、投入资本、营收。
- `research_grid.py <代码>:<亿,亿,...>`：按 §6.5.2.2 同一引擎，把研究数代入生产池带，给研究口径 V 与 09-30 收盘的 `P/V`。
- 仓库数据：逐季面板 `data/raw/financials/<报告期>.csv`（归母、营收、毛利率、公告日）；三大报表 `data/raw/financials_statements/`；年报原文 `data/raw/annual_reports/<代码>/2025.pdf|.txt.gz`；券商研报元数据与预测 EPS `data/raw/research_reports/reports_2026.csv`（列 `publish_date`、`predict_this_year_eps` 等；抓取脚本 `scripts/fetch_a_share_research_reports.py`，API `reportapi.eastmoney.com/report/list`）；公司档案 `data/companies/<代码>_<名称>/`。
- 2026 半年报等原文：巨潮 cninfo 或东财公告 API 下载 PDF 后用 pypdf 抽文本、grep 核数；**不要用 WebFetch 读新浪 GB18030 页面**（会乱码、翻转正负号）。财务数字以仓库面板或原文为准，引用时写来源与日期。

时点：只用 2026-10-01（北京时间）以前公开的信息。

## 输出

每家公司写 `<代码>_<名称>.md`（中文，≤ 2,500 字）与 `<代码>.json`，JSON 字段：

```json
{
  "security_code": "", "security_name": "",
  "research_nopat_yi": 0.0, "research_range_yi": [0.0, 0.0],
  "research_evidence_date": "YYYY-MM-DD",
  "research_falsifier": "",
  "research_source": "",
  "equity_bridge": {"parent_yi": null, "minority_share": null, "annual_nopat_yi": null, "annual_net_profit_yi": null},
  "research_v": 0.0, "research_pv": 0.0,
  "price_for_pv_1": 0.0,
  "replicability": {"judgment": "难复制|易复制", "confidence": "高|中|低", "evidence": ""},
  "demand_runway": {"judgment": "结构扩张|存量", "driver": "", "falsifier": ""},
  "price_decline_reason": "",
  "conclusion": "可买|不可买|不适用", "conclusion_reason": "",
  "key_risks": [""],
  "sources": [{"title": "", "date": "", "url_or_path": ""}]
}
```

`price_for_pv_1` = 研究口径 V × 1.0034（现行买入线，§9.3.1）。`conclusion` 只在研究口径 `P/V` ≤ 1.0034 时给「可买／不可买」，否则填「不适用」。
