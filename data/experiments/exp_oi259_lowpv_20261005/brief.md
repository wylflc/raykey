# OI-259 池内低 P/V 公司逐只审查任务说明（2026-10-05）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`。用户 2026-10-05 要求：对估值池中 `P/V` 较小（< 1）的公司重点审核，`P/V` 非常小的尤其要认真，因为它们可能触发买入。逐只回答：

1. **`P/V` 为什么低**：模型价值 V 由哪些部分构成，与市场定价的分歧在哪（盈利锚、增长、净现金、守卫、研究数等）。
2. **计算是否真实合理**：输入数据、口径与公式执行有没有错（单位、股数、现金类与受限现金、有息负债、少数股东、外生权益、一次性收益、重述、行业属性等）。
3. **独立、客观的低估程度**：不看模型，按下文方法给悲观／基准／乐观三档每股价值与对应 `P/V`。
4. **估值计算的不完善或漏洞**：指出机制层面的问题（哪条规则、哪个字段、影响多大、多少只同类公司可能受影响），作为登记新 issue 的候选。

## 纪律

- **只写本目录** `data/experiments/exp_oi259_lowpv_20261005/companies/`（逐只 `<代码>_<名称>.md` 与 `.json`）与 `raw/`（下载的原文，不入库）。不得改动 `data/processed/`、`data/reference/`、`docs/`、`scripts/` 及其他目录的任何文件；不得读 `docs/xzy/`；不得 git 提交。
- **时点**：只用 2026-10-05（北京时间）以前公开的信息；现价取 2026-09-30 收盘（`decomposition.csv` 的 `close`）。
- **财报数字以原文为准**：优先读缓存的年报文本 `data/raw/annual_reports/<代码>/<年>.txt.gz`（gzip 压缩的 UTF-8，pypdf 抽取），缺的从巨潮下载 PDF（`http://static.cninfo.com.cn/finalpage/...`，检索接口见 `scripts/fetch_cash_note_items.py` 的 `find_report`）到本目录 `raw/`，用 pypdf 抽文本后 grep。**不要用 WebFetch 读新浪等 GB18030 网页取财报数字**（曾把正负号读反）；东财 F10 接口与仓库面板可作交叉核对。网上的行业、价格、政策信息可以用 WebSearch／WebFetch，注明来源与日期。
- 本交互节点只有 1 个 CPU、内存有限：一次只解析一份 PDF，不跑全量脚本、不提交 SLURM 作业。
- 模型 `P/V` 是全池相对位置（买入线 `P/V ≤ 1.0034`，`P/V < 1` 不等于低于公允价值，OI-208）；独立 `P/V` 是绝对口径，两者只比排序与方向，不直接比水平。

## 输入

- 拆解表：本目录 `decomposition.csv`／`decomposition.md`（09-30 信号日生产候选侧带；字段说明见 `decompose.py`）。
- 生产带全字段：`data/processed/a_share_pool_model_bands_adopted.csv`（候选侧）、`a_share_pool_model_bands_hold.csv`（持仓侧）；历史带 `data/processed/roic_bands.csv`（逐报告期的 `nopat_ps`、`roic0`、`g0`、`peak_weight`、`trough_weight` 等，可看锚的来龙去脉）。
- 模型规则：`docs/000_Ashare_workflow.md` §6.5.1（唯一生产模型：ROIC/FCFF 路径、归一化比率 `ratio0` 的信任度 λ、峰／谷守卫、TTM 当期化、g0 资本腿、股本口径、超额现金与受限现金、少数股东；银行保险的股利折现）、§6.5.2.2（研究数）、§7.3（复核队列）。折现率 r = 10%、g_T = 3%、10 年 fade、ROIC 指数衰减。
- 财务数据：逐季面板 `data/raw/financials/<报告期>.csv`；三大报表 `data/raw/financials_statements/{balance,income,cashflow}.csv`（东财字段名）；附注现金类 `data/reference/cash_note_items.csv`；受限现金 `data/reference/restricted_cash_items.csv`。
- 业务属性：`data/processed/a_share_business_attributes.csv`；逐票档案 `data/companies/<代码>_<名称>/`（README 的「现价隐含了什么」等）；质量分层 `data/processed/a_share_watchlist_quality_tiers.csv`。
- 先前研究（相关的先读）：`docs/reports/independent_valuation_holdings_2026-09-30.zh.md`（格力、招行、平安、同力、中创智领、爱玛）、`byd_independent_valuation_2026-09-30.zh.md`、`external_audit_comparison_2026-10-05.zh.md`、`sinoma_gree_moat_comparison_2026-09-19.zh.md`（中材国际、格力）、`pv_valuation_logic_audit_2026-09-23.zh.md`、`innolight_2025-04_valuation_2026-10-01.zh.md`；未结问题 `docs/000_Ashare_workflow_open_issues.md`（OI-251 一次性收益与扭亏、OI-252 存量公司资本腿增长偏高、OI-257 格力受限现金等），已结案索引 `docs/Ashare_workflow_open_issues_closed.md`（按需检索，勿整读）。

## 独立估值方法（与 09-30 报告同口径，便于横向比较）

- **非金融**：每股价值 = 正常化税后经营利润 ÷ 10%（零增长盈利能力价值 EPV）＋ 保守净自由现金 ＋（只在有据时）增长溢价。
  - 正常化利润给悲观／基准／乐观三档，说明依据（周期位置、行业供需、价格、份额、政策、一次性项目）；商品价格接受者按概率加权的长期价格，不取现价。
  - 净自由现金：现金类 − 有息负债，扣除受限、质押（未被质押借款抵消的部分）、经营备付（约 2% 营收）、客户资金与已宣派未付股息；经营浮存（应付、合同负债、预提返利）回吐风险在悲观档体现。
  - 增长只在「近年增量投入回报明显高于 10% 且行业需求有增量」时单列，写明 g、持续年数与 ROIC 假设。
  - 周期股另报 12% 折现的结果。
- **银行**：`P/B = (长期 ROE − g) ÷ (资本成本 − g)`，g = 3%，ROE 与资本成本给区间取中；注明不良、拨备、息差与资本约束。**保险**：P/EV、`P/B = (ROE − 3%) ÷ (COE − 3%)` 与股利折现，按 40／40／20 加权。
- **交叉核对**：现价隐含的永续利润、市盈率（TTM 与正常化）、股息率、与可比公司和自身历史估值区间的对照。

## 逐只输出（`companies/<代码>_<名称>.md`，中文 ≤ 1,800 字；同名 `.json`）

Markdown 依次写：一句话结论；一、模型 V 的构成与 `P/V` 低的原因；二、计算核对（逐项写查了什么、结果，发现的错误给原文页码与金额）；三、独立估值（三档表与依据）；四、低估程度判断（独立 `P/V`、主要风险、什么情况下是价值陷阱）；五、模型不完善或漏洞（每条：机制、证据、影响 V 的估计、同类公司、建议修正方向）；来源。

JSON：

```json
{"code": "", "name": "", "close": 0.0,
 "model": {"V": 0.0, "pv": 0.0, "path": "", "nopat_anchor_yi": 0.0, "g0": 0.0, "net_cash_ps": 0.0, "drivers": ""},
 "why_low": [""],
 "computation_check": [{"item": "", "result": "ok|issue", "detail": "", "v_impact_pct": null}],
 "independent": {"normalized_profit_yi": {"bear": 0, "base": 0, "bull": 0}, "net_cash_ps": {"bear": 0, "base": 0, "bull": 0},
                 "growth_premium_ps": 0, "V": {"bear": 0, "base": 0, "bull": 0}, "pv": {"bear": 0, "base": 0, "bull": 0},
                 "V_12pct_base": null, "method_note": ""},
 "model_vs_independent_pct": 0.0,
 "undervaluation_view": "明显低估|小幅低估|大致合理|高估|无法判断",
 "trap_risk": "",
 "model_flaws": [{"title": "", "mechanism": "", "evidence": "", "affected_field": "", "v_impact_pct": null,
                  "likely_affected_peers": [""], "proposed_fix": ""}],
 "sources": [{"title": "", "date": "", "url_or_path": ""}]}
```

## 组内汇总

每组最后写 `companies/_group_<组名>.md`（≤ 1,000 字）：组内独立 `P/V` 排序、模型偏乐观／偏保守的方向与共同原因、组内发现的模型漏洞（合并同类项）。
