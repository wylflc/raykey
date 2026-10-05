# OI-255 港股研发开支补录任务说明（2026-10-05）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`。本目录只放取数材料，**不得改动** `data/processed/`、`data/reference/`、`docs/`、`scripts/` 下任何文件；不得读 `docs/xzy/`。时点：只用 2026-10-05（北京时间）以前公开的信息。不得在任何请求中填入个人邮箱或账号。

## 背景

工作流 §6.5.1 规定 ROIC 路径的研发费用按行业年限资本化（A 股 v4.216，OI-213）；海外引擎要同步（OI-255）。美股研发取 SEC 研发标签；港股东财 F10 利润表有「研发费用」行的（阿里巴巴、京东、美团、金山软件）直接取。**利润表不单列研发、但年报附注披露研发开支的港股**，需要按年报附注补录到补充表 `data/reference/overseas_statement_supplements.csv`（由主会话写入，你只出候选行）。

对象：腾讯控股 00700（重点）、泡泡玛特 09992、海底捞 06862、东方海外国际 00316。

## 任务

1. 对每家公司，从 HKEX 披露易（`https://www1.hkexnews.hk/...`）或公司 IR 下载 2017–2025 财年年报（PDF 到本目录 `raw/`，不入库），用 pypdf 抽文本（乱码时用 ghostscript 渲染页图阅读）。
2. 找到年报中**全年研发开支**的披露（腾讯通常在管理层讨论或费用性质附注中写「研究与开发开支」；注意区分「研发开支」与「研发人员薪酬」等子项，取公司口径的全年研发开支总额），逐年记录：财年、金额（原币与单位）、所在页码与附注编号、原文摘录（逐字）、年报公告日（HKEX 刊登日）。同一财年若在次年年报中重述，以首次披露为准并注明重述值。
3. 若公司年报未披露研发开支或金额不重大（例如低于营收 0.5%），写明「未披露／不重大」与依据，不出候选行。
4. 按补充表格式输出候选行 `rd_supplements.csv`，列：`market,security_code,security_name,period,period_kind,field,value,unit,original_value,original_unit,fx_to_report,evidence_date,source_url,source_ref,note`。`market` = HK，`period` = 财年末（YYYY-12-31），`period_kind` = annual，`field` = rd_expense，`unit` = 报表币（腾讯、泡泡玛特、海底捞为 CNY；东方海外按仓库现有补充行的做法折人民币，`fx_to_report` 取该年 F10 营业额 ÷ 年报营业额），`value` 为折算后的元（不是千元、百万元），`evidence_date` = 年报公告日，`source_ref` 写 PDF 页码与附注号，`note` 写原文摘录要点。参考现有补充行的写法（同一文件中 00316、06862 的 `ebit_financial_income_in_operating` 行）。
5. 另写 `rd_supplements.md`（中文，≤ 1,500 字）：各公司研发开支的口径、逐年数、与营收之比、数据缺口。

完成后回复：每家公司是否出行、逐年金额，以及任何无法核实的地方。
