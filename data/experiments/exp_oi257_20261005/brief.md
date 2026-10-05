# OI-257 格力电器（000651）受限现金附注核对任务说明（2026-10-05）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`。本目录只放核对材料，**不得改动** `data/processed/`、`data/reference/`、`docs/`、`scripts/` 下任何文件；不得读 `docs/xzy/`。时点：只用 2026-10-05（北京时间）以前公开的信息。

## 背景

工作流 §6.5.1 第 3 条的现金口径（原文要点）：
- 超额现金 = `max(0, 现金类 − 客户资金 − 2% × 营收) + 其他金融资产`；现金类含货币资金、交易性金融资产、债权投资、其他债权投资、年报附注核定的其他流动资产／一年内到期的非流动资产／其他非流动资产中的存款、存单、理财。
- **受限现金（OI-219／OI-220）**：年报受限资产附注中受限原因写票据、承兑汇票、信用证或保函的现金类（同一行混写借款的整行计入；只写借款，或只写笼统的质押、保证金、冻结、存款准备金的不计）按经营资产计入投入资本、不计超额现金，扣除额 = min(计入额, 当期应付票据, 现金类)。
- 有息负债另计财务公司的吸收存款、同业存放、拆入资金、卖出回购、向中央银行借款等。

现状：`data/reference/restricted_cash_items.csv` 中格力 2025 年报受限的现金类 422.5 亿元全部记为 `generic`（货币资金 105.8 亿、一年内到期的非流动资产 104.7 亿、其他债权投资 79.0 亿、其他非流动资产 133.0 亿），OI-219 扣除额 0，全部按超额现金计入。当期应付票据 155.4 亿，短期借款 679.6 亿。09-30 独立估值（`docs/reports/independent_valuation_holdings_2026-09-30.zh.md`）判其中约 5.9 元／股（约 330 亿）未被质押借款抵消。生产带每股净金融资产 31.24 元（约 1,750 亿）。

## 任务

1. 下载格力 2025 年报（`http://static.cninfo.com.cn/finalpage/2026-04-29/1225250396.PDF`，仓库 `data/raw/annual_reports/000651/` 可能已有 2025 年文本）与 2026 半年报（巨潮，2026-08-27 前后公告）到本目录 `raw/`（不入库），用 pypdf 抽文本、grep 定位「所有权或使用权受到限制的资产」「受限」「质押」「保证金」「存款准备金」附注。
2. 逐项列出：报表科目、金额、附注原文的受限原因（逐字摘录）、页码。
3. 对每项判断：
   - 对应的负债是什么（短期借款中的质押借款、应付票据、财务公司吸收存款、保函／信用证等），金额是否可从附注核到（如短期借款附注的「质押借款」金额），该负债是否已计入模型的有息负债；
   - 按现行规则应归哪一类（经营资产扣除／借款抵消／笼统不扣），现行抽取是否正确；
   - 经济上是否属于股东可动用的超额现金。
4. 核对财务公司：存放中央银行法定存款准备金、吸收存款（关联方存款）是否已分别计入现金类与有息负债。
5. 汇总：现行口径下多计（或少计）的超额现金金额与每股影响（股数 56.014 亿），并说明依据。

## 输出

`000651_restricted_cash.md`（中文，≤ 2,000 字）与 `000651_restricted_cash.json`：

```json
{
  "report": "2025年报", "page_refs": [],
  "items": [{"line": "", "amount_yi": 0.0, "reason_text": "", "page": 0, "liability": "", "liability_amount_yi": null,
             "liability_in_debt": true, "current_rule_class": "notes|loan|generic", "economic_class": "operating|offset_by_debt|excess|unavailable", "note": ""}],
  "h1_2026": {"items": [], "note": ""},
  "finance_company": {"pbc_reserve_yi": null, "deposits_taken_yi": null, "in_cash_like": null, "in_debt": null, "note": ""},
  "overcount_yi": 0.0, "overcount_per_share": 0.0,
  "conclusion": "现行口径正确|需补规则", "proposed_rule": "",
  "sources": [{"title": "", "date": "", "url_or_path": ""}]
}
```
