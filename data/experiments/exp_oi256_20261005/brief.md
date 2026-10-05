# OI-256 平台代收代付托管资金核对任务说明（2026-10-05）

仓库 `/gpfs/scratch1/shared/zwang/mm_quant/RayKey`。本目录只放核对材料，**不得改动** `data/processed/`、`data/reference/`、`docs/`、`scripts/` 下任何文件；不得读 `docs/xzy/`。时点：只用 2026-10-05（北京时间）以前公开的信息。访问 SEC 时 User-Agent 用 `RayKey-AShareQuant research bot (personal research use)`，**不得填入任何个人邮箱或账号**；遵守 SEC 每秒 ≤ 10 次请求。

## 背景

- 工作流 §6.5.1 第 3 条（A 股）：客户资金 = 代理买卖证券款 + 代理承销证券款，属客户所有、不是公司现金，不计超额现金。
- §6.8（海外）：SEC us-gaap 现金类含现金及等价物（含流动与非流动受限现金）＋流动证券；只有金融中介负债 ≥ 总资产 20% 的类金融公司剔除受监管隔离的客户资金。
- 拼多多（PDD）2026Q2 的现金类 = 现金 1,289.18 亿 + 受限现金 772.74 亿 + 短期投资 3,274.96 亿元（`data/processed/overseas_watchlist_valuation.csv` 的 band_derivation_text；6-K ex99-1 2026-08-25）。受限现金被计入超额现金。

## 任务

1. **拼多多**：从 2025 年 20-F（SEC EDGAR）与 2026Q2 6-K，逐字摘录受限现金的性质说明（例如「代消费者收取、待结算给商家的款项存于托管账户」），以及对应负债（应付商家款 payable to merchants、商家保证金 merchant deposits）的金额与说明；列 2021–2025 年末与 2026-06-30 的受限现金、应付商家款、商家保证金。
2. **观察清单其他公司**：`data/processed/overseas_watchlist_valuation.csv` 中 ROIC 口径的公司（腾讯、阿里巴巴、京东、美团、金山软件、泡泡玛特、海底捞、东方海外、台积电、Adobe、美光、英伟达、阿斯麦、谷歌、苹果、优步、微软、Meta、AMD、特斯拉等），按 `data/interim/overseas_roic_years.csv` 最新行与 `tags_used`（或原始缓存 `data/raw/overseas_statements/`）判断现金类中是否含受限现金或代客户持有的资金；含的，摘录年报说明（性质：代客户托管／保险或监管准备金／借款质押／其他）与金额。优步（保险准备金相关受限资产）、阿里巴巴、京东、美团请重点查。
3. **A 股池**：`data/processed/a_share_core_valuation_pool.csv` 的池成员中，有无支付机构备付金、平台代收代付托管款一类被计入现金类的项目（看三大报表 `data/raw/financials_statements/balance.csv` 的客户备付金等列与公司主营）；有则列出。
4. 提出口径建议：哪些性质的受限资金不是股东可动用的现金（与「客户资金」同理），识别所需的证据字段，A 股与海外如何同一口径实现（例如在 `data/reference/overseas_statement_supplements.csv` 增加字段、A 股走附注核定）。

## 输出

`escrow_cash.md`（中文，≤ 2,500 字）与 `escrow_cash.json`：

```json
{
  "pdd": {"periods": [{"period": "", "restricted_cash_m": 0, "payable_to_merchants_m": null, "merchant_deposits_m": null}],
          "nature_quote": "", "source": "", "liability_link": ""},
  "overseas": [{"code": "", "name": "", "restricted_in_cash_like_m": null, "currency": "", "nature": "customer_escrow|insurance_regulatory|loan_pledge|other|none", "quote": "", "source": ""}],
  "a_share": [{"code": "", "name": "", "item": "", "amount_yi": null, "note": ""}],
  "proposed_rule": "", "evidence_fields": "",
  "sources": [{"title": "", "date": "", "url_or_path": ""}]
}
```
