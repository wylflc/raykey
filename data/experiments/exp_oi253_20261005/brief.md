# OI-253 中创智领（601717）研究正常化盈利复核任务说明（2026-10-05）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`，A 股研究。本目录只放复核材料，**不得改动** `data/processed/`、`docs/`、`scripts/` 下任何文件；不得读 `docs/xzy/`。时点：只用 2026-10-05（北京时间）以前公开的信息。

## 背景

生产估值模型（工作流 §6.5.1）给中创智领的每股 NOPAT 锚 2.1967 元 × 股数 17.854 亿 = **39.22 亿元**（候选侧带，报告期 2026-06-30，λ = 0.5 混合锚：三年中位与 TTM 之间，TTM 因子 0.7876，峰守卫 w = 0），g0 6.38%（资本腿：增量 ROIC 17.80% × 再投资率 35.83%），V 23.62，09-30 收盘 13.35，`P/V` 0.565。少数股东份额（盈利口径）0.0562。

三份独立估值认为模型偏高：
- 09-30 独立估值（`docs/reports/independent_valuation_holdings_2026-09-30.zh.md` 第四节）：正常化 NOPAT 约 27 亿元，独立基准 V 15.0；2024→25 年新增投入资本 38 亿主要是应收，增量回报约 1%；煤机下行（2012–15 年净利 −97%）；可转债摊薄最多约 15%～17%；汽零 SEG 利润薄。
- 两份网页版审计合理价 13～17 元。

这些只是参考，**不得以它们为目标反推研究数**。你要独立给出穿越周期的正常化盈利。

## 研究数规则（工作流 §6.5.2.2 要点）

- `research_nopat_yi`：研究估计的**正常化**盈利，亿元，与模型同口径：税后经营利润，剔除金融收益，含权益法损益与少数股东份额（合并口径）。
- 研究原文为归母净利时，按模型股权桥反解：`NOPAT = 归母 ÷ (1 − 生产带 minority_share 0.0562) + (最新年报 NOPAT − 合并净利)`，注明两项取值。最新年报模型口径 NOPAT 用 `../exp_growth_reviews_20261001/annual_nopat.py 601717` 计算（研发资本化后）。
- 同一产能口径：以未来产量或未建成产能为基础的盈利按现有已投产产能重述。
- 须同时给 `research_evidence_date`（所依据证据的公开可得日）、`research_falsifier`（可证伪条件，≤ 60 字，写成可量的指标与阈值）、`research_source`（出处与推算过程）。
- 「正常化」指穿越周期可持续的盈利水平，不是峰值、不是谷底。中创智领两大分部：煤机（液压支架等，需求随煤矿资本开支周期）与汽车零部件（SEG 起动机发电机、亚新科），请分部估计：煤机按穿越周期的收入与分部利润率（参考 2012–2025 年分部历史，含 2012–2017 年下行与 2018–2025 年上行），汽零按近年实际。
- 不得为希望得到的 `P/V` 反推研究数。

## 已备工具与数据

- `../exp_growth_reviews_20261001/annual_nopat.py 601717`：模型口径逐年 NOPAT、合并净利、归母、少数股东损益、投入资本、营收。
- `../exp_growth_reviews_20261001/research_grid.py 601717:<亿,亿,...>`：按 §6.5.2.2 同一引擎把研究数代入生产池带，给研究口径 V 与 09-30 收盘的 `P/V`（该带未做除权归一化，可直接用）。
- 仓库数据：逐季面板 `data/raw/financials/<报告期>.csv`；三大报表 `data/raw/financials_statements/`；券商研报 `data/raw/research_reports/reports_2026.csv`；公司档案 `data/companies/601717_中创智领/`。
- 年报、半年报原文：巨潮 cninfo（`http://static.cninfo.com.cn/finalpage/...`）或东财公告 API 下载 PDF 到本目录 `raw/`（不入库），用 pypdf 抽文本、grep 核数。09-30 报告来源节有 2026 半年报、2025 年报、可转债修订稿的链接。**不要用 WebFetch 读新浪 GB18030 页面**。财务数字以仓库面板或原文为准，引用时写来源与日期。

## 输出

写 `601717_中创智领.md`（中文，≤ 2,500 字：分部正常化过程、周期判断、与模型锚的差异来源、可转债影响）与 `601717.json`：

```json
{
  "security_code": "601717", "security_name": "中创智领",
  "research_nopat_yi": 0.0, "research_range_yi": [0.0, 0.0],
  "research_evidence_date": "YYYY-MM-DD",
  "research_falsifier": "",
  "research_source": "",
  "equity_bridge": {"parent_yi": null, "minority_share": 0.0562, "annual_nopat_yi": null, "annual_net_profit_yi": null},
  "segments": [{"segment": "", "normalized_revenue_yi": 0.0, "normalized_margin": 0.0, "normalized_profit_yi": 0.0, "basis": ""}],
  "research_v": 0.0, "research_pv": 0.0,
  "research_grid": [{"research_nopat_yi": 0.0, "v": 0.0, "pv": 0.0}],
  "convertible": {"size_yi": 0.0, "status": "", "conversion_price": null, "dilution_note": ""},
  "g0_note": "",
  "key_risks": [""],
  "sources": [{"title": "", "date": "", "url_or_path": ""}]
}
```

`research_grid` 至少给研究区间两端与中值三点。`g0_note` 说明模型 g0 6.38% 的来源是否主要是应收增长（不改 g0，只记录）。
