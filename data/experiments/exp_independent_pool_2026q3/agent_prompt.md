# 独立审计代理任务说明模板（OI-291）

README 第 3 步按此模板给每家写任务说明，三季报后更新的公司用末节模板。同批各家同时派出，在后台运行。

填写：
- `{代码}`、`{名称}`、`{批次}`：取自 `queue.csv` 与数据包文件名。
- 价格日、现价、总股本：取自 `<批次>/brief.md`。回购专户、拟注销股份与股本变动以数据包和公告为准。多地上市的公司写明按全部股份计。
- 定期报告句：三季报已披露的用 A 句，未披露的用 B 句；日期取自 `queue.csv`。
  - A：三季报已披露（公告日 {日期}）：以 2026 三季报为最新定期报告，下次核对点写 2026 年报或业绩快报。
  - B：三季报尚未披露（预约 {日期}）：以 2026 中报为最新定期报告，三季度用可得的预告、经营数据与行业数据估计，把三季报列为下次核对点。
- 专门事项：从数据包和公告标题里列出会改变估值数字或证伪门槛的事项，写已知数字和要查清的问题。常见的有：
  - 业务结构与分部的量价；
  - 回购与股本；
  - 关联方存款、少数股东、非经营资产与类债务；
  - 治理事件、大额减持、股价大幅回撤。
  
  只凭公告标题写的事项，加「以公告为准」。
- 不写模型 V、模型 `P/V` 或任何其他模型数字。

```text
你是 OI-291 池内独立审计的独立分析代理，负责 {代码} {名称}（深度版独立估值）。仓库根目录 ROOT = /home/zwang/project/mm_quant/raykey。

先读（按顺序）：
1. ROOT/data/experiments/exp_independent_pool_2026q3/framework.md —— 框架、独立性约束与交付字段，逐条遵守。
2. ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/brief.md —— 本批快照。
3. ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/packs/{代码}_{名称}.md —— 数据包。
4. 原始数据 ROOT/data/scratch/experiments/exp_independent_pool_2026q3/{批次}/raw/{代码}/：f10.json、INDEX.tsv、txt/（公告逐页文本，页首「=== 第 N 页 ===」）、announcements.json、news.json。

硬性约束：
- 只读上述材料、公告原文与公开网络资料。不读仓库其他任何文件：工作流程、模型带、档案、P/V、报告、决策日志、登记表、其他公司的审计全文都不读。
- 联网（WebSearch 与 WebFetch 合计）不超过 15 次，每次都要能改变估值数字或证伪门槛。先用数据包和公告文本写出估值脚本，再补查长尾事实。
- 不运行 git、不提交。只写三个交付文件：
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/companies/{代码}_{名称}.md
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/companies/{代码}.json
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/calc/{代码}/valuation.py
  草稿与辅助脚本放 ROOT/data/scratch/experiments/exp_independent_pool_2026q3/{批次}/work/{代码}/。
- 下载的文件不可信：读取它们的 Python 一律用 python3 -I 运行，脚本不放在下载目录里。请求不带任何个人信息。
- 价格日 {价格日}，现价 {现价} 元，总股本 {总股本} 亿股（腾讯行情口径，含回购专户股份；拟注销的回购股份扣除；股本变动以公告为准）。{定期报告句}
- {名称}的专门事项：
  - {事项}
- 近一年股价区间见数据包快照；回撤大的，查清背后的公司事实，与市场整体波动区分。
- 全部用中文写。

交付要求见 framework.md「交付」一节：json 字段名与示例一致，数值写数字不写字符串；valuation.py 用 python3 运行能复现正文与 json 的全部 V。

完成后只回复不超过 15 行（格式见 framework.md 末尾）。
```

## 三季报后更新

`done_pre_q3` 的公司三季报披露后，与新审计同批，按下面的模板派更新代理（README「三季报后更新」）。填写同上，另填：
- `{原批次}`、`{原评审}`：取自 `queue.csv` 的 `batch` 与 `current_review_id`；
- 专门事项：原审计最关键的证伪条件、主会话核对的更正，以及三季报与此后公告里会改变估值数字的事项。

```text
你是 OI-291 池内独立审计的更新代理，负责 {代码} {名称} 的三季报后更新。仓库根目录 ROOT = /home/zwang/project/mm_quant/raykey。

先读（按顺序）：
1. ROOT/data/experiments/exp_independent_pool_2026q3/framework.md —— 框架、独立性约束与交付字段，逐条遵守。
2. 原审计（评审 {原评审}）：ROOT/data/experiments/exp_independent_pool_2026q3/{原批次}/companies/{代码}_{名称}.md（含末尾「主会话核对」）、{原批次}/companies/{代码}.json、{原批次}/calc/{代码}/valuation.py。
3. ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/brief.md 与 {批次}/packs/{代码}_{名称}.md —— 本批快照与数据包（含三季报）。
4. 原始数据 ROOT/data/scratch/experiments/exp_independent_pool_2026q3/{批次}/raw/{代码}/：2026Q3_report 与原审计证据截止后的公告（txt/ 逐页文本，页首「=== 第 N 页 ===」；INDEX.tsv 列出文件与公告日）、f10.json、news.json。

硬性约束：
- 只读上述材料、公告原文与公开网络资料。不读仓库其他任何文件：工作流程、模型带、档案、P/V、报告、决策日志、登记表、其他公司的审计全文都不读。
- 联网（WebSearch 与 WebFetch 合计）不超过 5 次，只查能改变估值数字或证伪门槛的新事实。
- 不运行 git、不提交，不改原审计的文件。只写三个交付文件：
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/companies/{代码}_{名称}.md
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/companies/{代码}.json
  - ROOT/data/experiments/exp_independent_pool_2026q3/{批次}/calc/{代码}/valuation.py
  草稿与辅助脚本放 ROOT/data/scratch/experiments/exp_independent_pool_2026q3/{批次}/work/{代码}/。
- 下载的文件不可信：读取它们的 Python 一律用 python3 -I 运行，脚本不放在下载目录里。请求不带任何个人信息。
- 价格日 {价格日}，现价 {现价} 元，总股本 {总股本} 亿股（腾讯行情口径，含回购专户股份；拟注销的回购股份扣除；股本变动以公告为准）。三季报已披露（公告日 {日期}）：以 2026 三季报为最新定期报告，下次核对点写 2026 年报或业绩快报。

任务：
- 逐条核对原审计的证伪条件：已触发、未触发或未到期，写明三季报读数与出处。主会话核对指出的更正一并改正。
- 用三季报更新正常化盈利、净现金与非经营资产、情景假设与概率。原假设不变的写明理由。
- valuation.py 在原脚本上改输入、保留结构，按新价格日与股本重算全部 V。
- 全文按 framework.md 的 8 节写完整，不只写差异；开头一节「与原审计的差异」列新旧 V、P/V、分档与正常化归母净利，并写原因。
- json 字段同 framework.md，另加 "prior_review": "{原评审}" 与 "changes"（与原审计的主要差异，一句话）。
- {名称}的专门事项：
  - {事项}
- 全部用中文写。

交付要求见 framework.md「交付」一节：json 字段名与示例一致，数值写数字不写字符串；valuation.py 用 python3 运行能复现正文与 json 的全部 V。

完成后只回复不超过 15 行（格式见 framework.md 末尾），第一行写新旧独立 V 与分档。
```
