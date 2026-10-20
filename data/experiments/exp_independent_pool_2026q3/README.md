# 池内逐家独立审计（OI-291，2026 年三季报轮）

用户 2026-10-19 裁定：池内逐家做一轮独立审计，全部用深度版；研究数同时进 §6.9 登记表与档案；池文档并列独立 `P/V`（v4.254 已落地）。用户 2026-10-20 要求现在就开始：先用已披露的最新定期报告形成深度审计结果，三季报后再更新。缘由见[增长率假设评估](../../../docs/reports/growth_assumption_review_2026-10-19.zh.md)与[海康威视评审](../../../docs/reports/independent_hikvision_2026-10-19.zh.md)。待办登记 [OI-291](../../../docs/000_Ashare_workflow_open_issues.md)，汇总见[池内独立审计报告](../../../docs/reports/independent_pool_2026q3.zh.md)。

## 范围与顺序

- 范围：10-16 扫描的池成员 182 家，见 `queue.csv`。`status`：
  - `pending`：未审计；
  - `done`：已用三季报完成深度审计；
  - `done_pre_q3`：已用中报完成深度审计，三季报后更新；
  - `recheck_after_q3`：已有现行评审、但早于三季报的公司（初始 30 家），各自三季报后复核。
- 每批约 8 家，按以下顺序取：
  1. 三季报已披露、尚未审计的公司；
  2. 三季报预约日在 10-27 及以后的公司，按最近一次扫描的模型 `P/V` 升序（主会话排序用，代理不读）；预约日更早的等披露后归入第 1 条；
  3. 银行与保险单独成批（股利折现框架）。
- 量级：海康单家约 1 小时 40 分、193 轮、读入约 4,600 万 token（多为缓存读取）。

## 目录

| 位置 | 内容 |
| --- | --- |
| `framework.md` | 统一任务框架、独立性约束与交付字段 |
| `queue.csv` | 全池队列（三季报日期、状态、批次） |
| `tools/` | 主会话工具：`build_kit.py`（批次材料）、`pdf_text.py`、`write_brief.py`、`check_delivery.py`、`register_batch.py`、`register_research.py`、`apply_rulings.py` |
| `<批次>/brief.md`、`packs/`、`companies/`、`calc/<代码>/` | 批次快照、数据包、审计全文与 `.json`、估值脚本（入库） |
| `research/<代码>.json` | 档案研究数登记输入 |
| `data/scratch/experiments/exp_independent_pool_2026q3/<批次>/raw/`、`work/` | 原始数据、公告 PDF 与文本、代理草稿（不入库，14 天未改动即被清理） |

## 每批步骤

1. 材料：`sbatch --account=tes21035 --export=ALL,BATCH=<批次>,PRICE_DATE=<收盘日>,CODES=<代码+代码> scripts/slurm/oi291_kit.sbatch`（8 家约 10～20 分钟）。
2. 快照：`python3 tools/write_brief.py <批次> --price-date <收盘日>` 写 `<批次>/brief.md`。
3. 派代理：每家一个，任务说明引用 `framework.md` 与 `brief.md`，写明不读仓库模型、联网不超过 15 次、不提交、只写本公司三个交付文件。
4. 核对：`python3 tools/check_delivery.py <批次>` 校验字段、分档、加权、脚本复现与报表数；主会话再抽查 `spot_checks` 与 `web_facts` 的一手来源，更正写回全文并注明。
5. 登记：`python3 tools/register_batch.py <批次>`：
   - §6.9 登记表追加 `current` 行（旧行改 `superseded`），重出阅读版；
   - 写 `research/<代码>.json` 并登记档案研究数（§6.5.2.2 折算）；档案已「采用研究数」的不覆盖，汇总报告列出新旧两数，提请用户裁定；
   - 档案在发布凭据的输入摘要内：研究数在当日执行清单发布之前登记；已发布的，留到下一次扫描之前登记，不在发布后改档案。
   - 框架口径修订后重算的公司用 `--revision r1 --no-research` 重登：新评审编号带后缀，旧行改 `superseded`，研究数不变。
6. 重出池文档（`build_a_share_core_valuation_pool.py --md-only`）与档案 README。下一次扫描按 §7.3 计算差距：超过 30% 的入队，研究数低于模型锚的冻结新增买入。
7. 汇总报告追加本批：模型与独立 `P/V` 对照、差距超过 30% 与已采用研究数的个案，按批次提请用户裁定「采用研究数／维持模型」。裁定写成 `<批次>/rulings.json`，`python3 tools/apply_rulings.py <批次>/rulings.json --day <裁定日> --review-batch <批次>` 写档案差距复核字段与决策日志（发布时段规则同第 5 步）。
8. 更新 `queue.csv` 的 `status`／`batch`，提交。

## 三季报后更新

`done_pre_q3` 的公司在三季报披露后更新：每家派一个更新代理，只读原审计全文、`.json`、估值脚本、三季报与此后公告，联网不超过 5 次。更新正常化盈利、净现金与情景假设，逐条核对证伪条件，重跑估值脚本，写 `companies/<代码>_<名称>_q3.md` 与新 `.json`。结论或独立 V 改变的追加 `current` 行、旧行改 `superseded`；不变的也追加一行，写明新的证据截止（§6.9 第 3 条）。研究数按第 5 步登记。

## 完成条件

池内全部成员有三季报后的现行独立评审。全轮汇总对照模型与独立 `P/V`（分布、秩相关、差距大的个案），据此再议研究增长规则（资本腿失效行的机械替代值已于 OI-290 检验、不采纳）。

## 已登记

| 代码 | 名称 | 评审 | 研究数（亿元） | 模型锚（亿元） | 差距 |
| --- | --- | --- | ---: | ---: | ---: |
| 002415 | 海康威视 | `iv20261019_hik:002415` | 184.47（163.94～204.66） | 186.01 | 0.8% |

OI-291 各批的登记结果与待裁定个案见[汇总报告](../../../docs/reports/independent_pool_2026q3.zh.md)。

海康的独立 V 比模型 V 高 64%，但盈利锚几乎一致。差距来自增长率（模型 g0 = 0）、折现率（10% 对 9%）、回报衰减与非经营资产，不在研究数口径内。
