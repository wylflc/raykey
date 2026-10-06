# OI-261／OI-263 附注抽取与影响量化（实验）

生成：2026-10-06 19:49:22 CST。只读输入：`data/experiments/exp_oi261_263_20261006/debt_note_items.csv`（含人工核定 `debt_note_manual.csv`）、受限资产 v1（同一缓存状态以缺省 `--parser v1` 重跑，与原脚本、生产表逐行一致）与 v2 实验表、东财三大报表、`data/raw/financials/2025-12-31.csv` 的 BPS。本页只量化、不改口径；生产表、建带与回测均未改动。

口径：其他流动负债计入短期应付债券／短融／超短融／可转换债券等债务工具（bond）与明写的借款、质押式回购借入资金（loan）；其他应付款计入「按款项性质列示」表的借款、资金拆借、企业借款及利息（loan）；预计负债计入弃置、复垦、环境恢复类（decom，已扣表内「减：一年内到期」——那部分已在一年内到期的非流动负债、本就进有息负债）。附注合计与报表行相差 ≤5%（或 100 万元）、逐行期末值之和与合计相符、计入类行不与其他性质混写才记 `ok`。股数 = (归母权益 − 其他权益工具) ÷ 2025-12-31 BPS。受限资产新增额 = v2 计入额 − v1 计入额（只限 v1 未核定、v2 核定的行），以当期应付票据封顶（`roic_inputs` 同式）。

## 1. 抽取覆盖与状态

| 范围 | 行数 | 剔除上市前年度后 | 核定（ok＋manual） | 核定占比 |
|---|---|---|---|---|
| 池成员 FY2025 | 170 | 170 | 163 | 95.88% |
| 池成员 FY2015–2025 | 1668 | 1489 | 1399 | 93.96% |
| 三表名册 FY2015–2025 | 2960 | 2697 | 2516 | 93.29% |
| 三表名册全部年份 | 4258 | 3752 | 2972 | 79.21% |

池成员 FY2015–2025 分行状态：

| 行 | 状态计数 | 核定占比 |
|---|---|---|
| OTHER_CURRENT_LIAB | ok 317，report_not_found 39，total_mismatch 4，no_total 4，manual 1，section_not_found 1，rows_mismatch 1，text_unreadable 1 | 96.07% |
| OTHER_PAYABLE | ok 957，report_not_found 107，total_mismatch 24，no_breakdown 10，no_total 9，ambiguous 7，text_unreadable 5，section_not_found 4，rows_mismatch 2，manual 1 | 93.83% |
| PREDICT_LIAB | ok 119，report_not_found 39，manual 4，total_mismatch 3，section_not_found 3，no_total 2，text_unreadable 2，rows_mismatch 1，ambiguous 1 | 89.78% |

全名册状态计数：ok 2966，report_not_found 514，not_fetched 240，total_mismatch 161，no_breakdown 97，no_total 86，section_not_found 86，rows_mismatch 32，text_unreadable 28，ambiguous 24，no_rows 17，manual 6，located 1。`report_not_found` 绝大多数是上市前年度（三表有、年报无）；`not_fetched` 是未下载的 2015 年前年报。

## 2. 审计案例核对

| 案例 | 审计数（亿） | 本次抽取 | 状态 | 说明 |
|---|---|---|---|---|
| 伊利 2025 其他流动负债 短期应付债券 | 90.43 | 90.43 | ok | 短期应付债券:9043394520.53:bond |
| 北新建材 2025 其他流动负债 短期融资券 | 10.06 | 10.06 | ok | 短期融资券:1006139726.02:bond |
| 中材国际 2025 其他流动负债 超短期融资券（附注列「短期融资债券」） | 7.02 | 7.02 | ok | 短期融资债券:702249589.04:bond |
| 中材国际 2025 其他应付款 资金拆借 | 4.34 | 4.55 | ok | 附注性质表 455,476,680.71 元（含应计利息等）；审计引用的 4.34 亿为管理层讨论「债权融资」表本金 43,366.00 万元；资金拆借:455476680.71:loan |
| 格力 2025 其他应付款 企业借款及利息 | 15.47 | 15.47 | ok | 企业借款及利息:1547471401.00:loan |
| 中国海油 2025 预计负债 弃置义务 | 1,160.39 | 1,160.39 | manual | 油气资产弃置义务（年末余额116,685减一年内到期646）:116039000000.00:decom |
| 美的 2025 受限资产 其他非流动资产质押开票（v2） | 236.90 | 236.90 | ok | 其他非流动资产:23690000000.00:notes;货币资金:16658157000.00:generic |

## 3. FY2025 池成员新增计入额（2026-10-06 裁定口径）

受影响 32 家（池内一般企业 174 家）。金额单位亿元；每股单位元。「融资类」是 §4 所列原待复核项（用户 2026-10-06 裁定计入，含同日再裁定的已贴现未到期票据；只取核定行）；「弃置专项资金」是报表现金行之外、计超额现金的专项资金（§9），从合计中减去；「税后合计」把弃置类乘 (1 − 当年税率)，其余按面值；「占 V」= 每股税后合计 ÷ 池表现行带中值，只是一阶量级（未计投入资本、ROIC、少数股东扣减的连带变化）。裁定前口径（不含融资类与专项资金）仍在 `quantification.json` 的 `total_new*` 字段。

| # | 代码 | 公司 | 短融等 | OCL借款 | 其他应付款借款 | 融资类 | 弃置类 | 弃置专项资金 | 受限资产(v2) | 合计 | 占归母权益 | 每股合计 | 每股税后 | 占 V |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 601225 | 陕西煤业 | 0.00 | 0.00 | 0.79 | 0.00 | 217.82 | 0.00 | 0.00 | 218.62 | 22.55% | 2.255 | 1.857 | 7.75% |
| 2 | 600887 | 伊利股份 | 90.43 | 0.00 | 0.00 | 9.08 | 0.00 | 0.00 | 0.00 | 99.52 | 18.21% | 1.573 | 1.573 | 8.47% |
| 3 | 600938 | 中国海油 | 0.00 | 0.00 | 0.00 | 0.00 | 1,160.39 | −85.85 | 0.00 | 1,074.54 | 13.39% | 2.261 | 1.577 | 3.93% |
| 4 | 000933 | 神火股份 | 0.00 | 0.00 | 19.82 | 0.00 | 12.18 | 0.00 | 0.00 | 32.00 | 13.03% | 1.423 | 1.259 | 4.64% |
| 5 | 000333 | 美的集团 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 236.90 | 236.90 | 10.61% | 3.118 | 3.118 | 4.29% |
| 6 | 600176 | 中国巨石 | 24.14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 24.14 | 7.76% | 0.603 | 0.603 | 7.06% |
| 7 | 002475 | 立讯精密 | 60.24 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 60.24 | 7.09% | 0.827 | 0.827 | 2.64% |
| 8 | 600970 | 中材国际 | 7.02 | 0.00 | 4.55 | 0.69 | 0.00 | 0.00 | 0.00 | 12.26 | 5.34% | 0.468 | 0.468 | 3.06% |
| 9 | 002648 | 卫星化学 | 0.00 | 0.00 | 0.00 | 17.82 | 0.00 | 0.00 | 0.00 | 17.82 | 5.31% | 0.529 | 0.529 | 2.22% |
| 10 | 601899 | 紫金矿业 | 0.00 | 0.00 | 0.00 | 3.54 | 86.39 | 0.00 | 0.00 | 89.93 | 4.85% | 0.338 | 0.270 | 1.42% |
| 11 | 000338 | 潍柴动力 | 0.31 | 42.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 42.57 | 4.57% | 0.489 | 0.489 | 2.24% |
| 12 | 002714 | 牧原股份 | 0.00 | 0.00 | 0.00 | 33.62 | 0.00 | 0.00 | 0.00 | 33.62 | 4.33% | 0.615 | 0.615 | 4.24% |
| 13 | 000786 | 北新建材 | 10.06 | 0.00 | 1.50 | 0.00 | 0.00 | 0.00 | 0.00 | 11.56 | 4.26% | 0.679 | 0.679 | 2.48% |
| 14 | 600031 | 三一重工 | 0.00 | 11.50 | 0.00 | 16.38 | 0.00 | 0.00 | 0.00 | 27.88 | 3.16% | 0.303 | 0.303 | 2.80% |
| 15 | 603505 | 金石资源 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.58 | 0.58 | 3.15% | 0.069 | 0.069 |  |
| 16 | 000426 | 兴业银锡 | 0.00 | 0.00 | 2.80 | 0.00 | 0.00 | 0.00 | 0.00 | 2.80 | 2.95% | 0.158 | 0.158 | 1.63% |
| 17 | 603993 | 洛阳钼业 | 0.00 | 0.00 | 0.00 | 0.00 | 24.24 | 0.00 | 0.00 | 24.24 | 2.94% | 0.113 | 0.077 | 0.64% |
| 18 | 002352 | 顺丰控股 | 26.20 | 0.00 | 0.00 | 1.84 | 0.00 | 0.00 | 0.00 | 28.04 | 2.82% | 0.556 | 0.556 | 3.03% |
| 19 | 300699 | 光威复材 | 0.00 | 0.00 | 1.52 | 0.00 | 0.00 | 0.00 | 0.00 | 1.52 | 2.67% | 0.183 | 0.183 | 2.17% |
| 20 | 300124 | 汇川技术 | 0.00 | 0.00 | 0.00 | 8.62 | 0.00 | 0.00 | 0.00 | 8.62 | 2.44% | 0.318 | 0.318 | 0.89% |
| 21 | 000408 | 藏格矿业 | 0.00 | 0.00 | 0.00 | 0.00 | 3.76 | 0.00 | 0.00 | 3.76 | 2.32% | 0.240 | 0.227 | 0.95% |
| 22 | 300604 | 长川科技 | 0.00 | 0.00 | 1.09 | 0.00 | 0.00 | 0.00 | 0.00 | 1.09 | 2.30% | 0.172 | 0.172 | 0.43% |
| 23 | 002594 | 比亚迪 | 50.31 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 50.31 | 2.04% | 0.552 | 0.552 | 0.55% |
| 24 | 000651 | 格力电器 | 0.00 | 0.00 | 15.47 | 0.00 | 0.00 | 0.00 | 0.00 | 15.47 | 1.06% | 0.276 | 0.276 | 0.37% |
| 25 | 002371 | 北方华创 | 0.00 | 0.24 | 0.00 | 3.46 | 0.00 | 0.00 | 0.00 | 3.70 | 0.98% | 0.510 | 0.510 | 0.30% |
| 26 | 603067 | 振华股份 | 0.00 | 0.00 | 0.23 | 0.00 | 0.00 | 0.00 | 0.00 | 0.23 | 0.63% | 0.033 | 0.033 | 0.28% |
| 27 | 600085 | 同仁堂 | 0.00 | 0.00 | 0.83 | 0.00 | 0.00 | 0.00 | 0.00 | 0.83 | 0.61% | 0.060 | 0.060 | 0.41% |
| 28 | 600285 | 羚锐制药 | 0.00 | 0.00 | 0.18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.18 | 0.53% | 0.032 | 0.032 | 0.18% |
| 29 | 601138 | 工业富联 | 0.00 | 0.00 | 0.00 | 3.66 | 0.00 | 0.00 | 0.00 | 3.66 | 0.22% | 0.018 | 0.018 | 0.08% |
| 30 | 002050 | 三花智控 | 0.00 | 0.00 | 0.64 | 0.00 | 0.00 | 0.00 | 0.00 | 0.64 | 0.20% | 0.015 | 0.015 | 0.09% |
| 31 | 600600 | 青岛啤酒 | 0.00 | 0.00 | 0.00 | 0.47 | 0.00 | 0.00 | 0.00 | 0.47 | 0.15% | 0.034 | 0.034 | 0.05% |
| 32 | 300866 | 安克创新 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.00 | 0.03 | 0.02% | 0.005 | 0.004 | 0.00% |

前 20 名（按占归母权益）：陕西煤业、伊利股份、中国海油、神火股份、美的集团、中国巨石、立讯精密、中材国际、卫星化学、紫金矿业、潍柴动力、牧原股份、北新建材、三一重工、金石资源、兴业银锡、洛阳钼业、顺丰控股、光威复材、汇川技术。

合计：短融等 268.72 亿，OCL 借款 54.00 亿，其他应付款借款 49.43 亿，融资类 99.18 亿，弃置类 1,504.82 亿（税后 1,111.69 亿），弃置专项资金抵减 85.85 亿，受限资产 v2 新增 237.48 亿。

FY2025 未核定的行：美的集团（000333）OTHER_PAYABLE no_breakdown；电投能源（002128）OTHER_PAYABLE total_mismatch；宁德时代（300750）PREDICT_LIAB ambiguous；中国神华（601088）OTHER_CURRENT_LIAB total_mismatch；中国神华（601088）OTHER_PAYABLE total_mismatch；中国神华（601088）PREDICT_LIAB total_mismatch；豪威集团（603501）OTHER_PAYABLE ambiguous。

## 4. 融资类项目（原待复核，2026-10-06 裁定计入，含已贴现未到期票据），FY2025

| 代码 | 公司 | 行 | 金额（亿） | 明细 |
|---|---|---|---|---|
| 002352 | 顺丰控股 | OTHER_PAYABLE | 1.84 | 应付银行供应链金融产品/再保理款项:184430000.00 |
| 002371 | 北方华创 | OTHER_CURRENT_LIAB | 3.46 | 票据融资款项:345800917.85 |
| 002648 | 卫星化学 | OTHER_CURRENT_LIAB | 17.82 | 催化剂载体（白银）短期租借合约:1781552300.97 |
| 002714 | 牧原股份 | OTHER_PAYABLE | 33.62 | 反向保理业务:3362151137.65 |
| 300124 | 汇川技术 | OTHER_CURRENT_LIAB | 8.62 | 已贴现未到期票据及电子债权凭证:861816334.80 |
| 600031 | 三一重工 | OTHER_PAYABLE | 16.38 | 应付资产支持专项计划及保理转付款:1638411000.00 |
| 600600 | 青岛啤酒 | OTHER_PAYABLE | 0.47 | 财务公司吸收关联方存款:46639222.00 |
| 600887 | 伊利股份 | OTHER_PAYABLE | 9.08 | 财务公司吸收成员单位存款:908486765.87 |
| 600970 | 中材国际 | OTHER_CURRENT_LIAB | 0.69 | 供应链融资:68666739.79 |
| 601138 | 工业富联 | OTHER_PAYABLE | 3.66 | 应付保理款:366234000.00 |
| 601899 | 紫金矿业 | OTHER_PAYABLE | 3.54 | 吸收存款:353792837.00 |

历史上较大的待复核项：中国神华 2015–2019 年其他应付款「吸收存款」（国家能源集团及其子公司存放于神华财务公司，135～322 亿）；牧原股份 2019–2025 年「反向保理业务」（最高 75.2 亿，2023）；三一重工「应付资产支持专项计划及保理转付款」；工业富联「应付保理款」（2024 年 36.5 亿）。用户 2026-10-06 裁定：上述融资类待复核项（`review_amount`）一并计入有息负债；应付保理费等费用行、未贴现的应付信用证随之改列 other（与应付票据同属经营负债）。`review_amount` 与 `counted_amount` 逐行互斥，两者相加不重复；只在 status ∈ {ok, manual} 时取。

已贴现未到期票据（用户 2026-10-06 再裁定：带追索权贴现、未终止确认的票据与电子债权凭证计入有息负债）：标签写贴现、未写背书的行改列 `review_amount`（与上述融资类同计入；「贴现利息」「贴现保证金」不计）。全名册核定行受影响 8 行、合计 40.07 亿（汇川技术，2016、2019、2020、2021、2022、2023、2024、2025）；FY2025 池成员 1 行、8.62 亿（300124 汇川技术 OTHER_CURRENT_LIAB 8.62 亿）。标签写「背书或贴现」的（徐工机械、宇通客车、同力股份，多照抄附注模板、以背书为主）按背书不计，核定行 8 行、合计 99.44 亿；未写背书或贴现的「未终止确认的票据」核定行 47 行、合计 191.98 亿（FY2025 池成员 4.89 亿；最多的是 格力电器 62.84、徐工机械 44.94、中国巨石 38.90、兖矿能源 10.34、特变电工 7.27 亿，各年相加）也不计——贴现而未终止确认的票据通常记短期借款，记在其他流动负债的多是背书，确认需逐家读应收票据附注。

## 5. OI-263 受限资产 v2

- **缺省 v1 不变**：同一缓存状态下，原脚本与改动后脚本（缺省 `--parser v1`）各跑一遍全清单（2091／2091 行），逐行逐字段一致（`extracted_at_utc` 时间戳列除外，列顺序相同）。与生产表也逐行逐字段一致（时间戳除外）。
- **v1 核定的行在 v2 下不变**：v1 核定 1339 行，v2 下逐字段不变 1339 行（v2 先跑 v1，只对 v1 未核定的行改用 v2 版式）。
- v2 核定 1393 行；新核定 54 行，其中计入额为正 31 行，计入额合计 447.05 亿（按当期应付票据封顶后 442.82 亿）。以下 v1 基线均为同一缓存状态的 v1 重跑。
- 状态迁移（v1 → v2）：no_total->ok 20，rows_mismatch->ok 15，section_not_found->text_unreadable 12，no_total->no_rows 12，section_not_found->none_stated 12，none_stated->ok 9，section_not_found->movement_table 7，section_not_found->ok 6，rows_mismatch->movement_table 6，no_rows->ok 4，section_not_found->rows_mismatch 4，no_rows->rows_mismatch 2，rows_mismatch->no_total 1，section_not_found->no_total 1，no_total->movement_table 1，no_total->rows_mismatch 1，no_rows->movement_table 1，no_rows->none_stated 1。
- 池 FY2025：v1 none_stated 4，ok 74，rows_mismatch 5，report_not_found 1，no_total 2，section_not_found 3，no_rows 1；v2 ok 78，rows_mismatch 4，report_not_found 1，no_total 1，section_not_found 1，text_unreadable 1，none_stated 4。

新核定且计入额为正的行：

| 代码 | 公司 | 财年 | v1 状态 | 来源 | 计入（亿） | 应付票据（亿） | 明细 |
|---|---|---|---|---|---|---|---|
| 000333 | 美的集团（池） | 2025 | none_stated | v2:note | 236.90 | 271.22 | 其他非流动资产:23690000000.00:notes;货币资金:16658157000.00:generic |
| 000063 | 中兴通讯 | 2019 | rows_mismatch | v2:note+nototal | 33.44 | 93.73 | 货币资金:3343511000.00:notes;其他非流动资产:0.00:generic |
| 000063 | 中兴通讯 | 2017 | section_not_found | v2:note | 30.66 | 108.49 | 货币资金:3066199000.00:notes |
| 000063 | 中兴通讯 | 2018 | rows_mismatch | v2:note | 30.57 | 79.16 | 货币资金:3057459000.00:notes;其他非流动资产:0.00:generic |
| 000063 | 中兴通讯 | 2020 | no_total | v2:note+nototal | 16.84 | 113.64 | 货币资金:1683733000.00:notes;其他非流动资产:0.00:generic |
| 000975 | 山金国际（池） | 2021 | rows_mismatch | v2:note | 15.18 | 17.18 | 货币资金:707989149.66:notes;交易性金融资产:810000000.00:notes;其他非流动资产:0.00:generic |
| 000063 | 中兴通讯 | 2016 | section_not_found | v2:note | 12.39 | 116.90 | 货币资金:1238540000.00:notes |
| 000063 | 中兴通讯 | 2015 | section_not_found | v2:note | 12.26 | 98.85 | 货币资金:1225984000.00:notes |
| 000975 | 山金国际（池） | 2022 | rows_mismatch | v2:note | 10.84 | 12.94 | 货币资金:1084140704.49:notes;其他非流动资产:0.00:generic |
| 000063 | 中兴通讯 | 2022 | rows_mismatch | v2:note+nototal | 8.97 | 106.30 | 货币资金:897420000.00:notes;其他非流动资产:0.00:generic |
| 002812 | 恩捷股份 | 2024 | rows_mismatch | v2:note | 8.89 | 5.15 | 货币资金:838743097.78:notes;其他流动资产:50178767.50:notes |
| 600803 | 新奥股份（池） | 2021 | no_total | v2:note | 8.71 | 12.61 | 货币资金:1313610000.00:notes;交易性金融资产:151600000.00:generic |
| 600803 | 新奥股份（池） | 2022 | no_total | v2:note | 7.17 | 8.57 | 货币资金:1133710000.00:notes;交易性金融资产:25600000.00:generic |
| 600803 | 新奥股份（池） | 2020 | no_total | v2:note | 5.33 | 9.75 | 货币资金:997680000.00:notes;交易性金融资产:70000000.00:generic |
| 600150 | 中国船舶 | 2019 | no_total | v2:note+nototal | 3.23 | 26.41 | 货币资金:322893598.18:notes |
| 601515 | 衢州东峰 | 2017 | no_total | v2:note+nototal | 1.31 | 5.56 | 货币资金:132574059.52:generic |
| 002428 | 云南锗业 | 2024 | rows_mismatch | v2:note | 1.21 | 1.21 | 货币资金:121498567.08:notes |
| 600702 | 舍得酒业 | 2014 | no_total | v2:note+nototal | 1.03 | 0.55 | 货币资金:102940957.63:generic |
| 603505 | 金石资源（池） | 2025 | rows_mismatch | v2:note | 0.58 | 4.09 | 货币资金:57843683.87:notes;货币资金:257805.45:generic |
| 002920 | 德赛西威（池） | 2018 | no_total | v2:note+nototal | 0.37 | 2.64 | 货币资金:36714553.38:generic |
| 002138 | 顺络电子（池） | 2015 | no_total | v2:note+nototal | 0.32 | 0.65 | 货币资金:31805602.00:notes |
| 300346 | 南大光电 | 2019 | rows_mismatch | v2:note | 0.22 | 0.33 | 货币资金:21892561.14:notes |
| 000999 | 华润三九（池） | 2016 | no_total | v2:note+nototal | 0.22 | 3.29 | 货币资金:21502708.64:notes |
| 603505 | 金石资源（池） | 2022 | rows_mismatch | v2:note | 0.15 | 0.42 | 货币资金:15464887.08:notes |
| 605305 | 中际联合（池） | 2023 | rows_mismatch | v2:note | 0.12 | 1.25 | 货币资金:6926672.03:notes;货币资金:5406738.21:generic;货币资金:0.42:generic |
| 600887 | 伊利股份（池） | 2024 | no_rows | v2:note | 0.09 | 9.69 | 货币资金:780420020.51:generic;货币资金:51912792.22:loan;货币资金:645545.67:generic;货币资金:9318289.49:not |
| 603369 | 今世缘（池） | 2016 | no_total | v2:note+nototal | 0.03 | 0.39 | 货币资金:3000000.00:notes |
| 002906 | 华阳集团 | 2023 | rows_mismatch | v2:note | 0.02 | 12.60 | 货币资金:1673298.88:generic |
| 002024 | ST易购 | 2024 | no_total | v2:note | 0.00 | 40.18 | 货币资金:7194993.00:loan;货币资金:432973.00:generic;货币资金:353220.00:notes;货币资金:77405.00:generic;货币资 |
| 002024 | ST易购 | 2025 | no_total | v2:note | 0.00 | 26.12 | 货币资金:6673741.00:loan;货币资金:390649.00:generic;货币资金:53800.00:notes;货币资金:42615.00:generic;货币资金 |
| 300910 | 瑞丰新材（池） | 2024 | rows_mismatch | v2:note | 0.00 | 2.11 | 货币资金:6494.00:notes |

## 6. 未覆盖与限制

- **文本层无字符映射**（`text_unreadable`）：中国海油 2022–2025、天山铝业 2025 已按原文页面人工核定，登记 `debt_note_manual.csv`（逐行记来源、页码与依据）；
  池内其余未核定：新奥股份 2018、2019，长江电力 2022，百济神州 2021，陕西煤业 2021、2024（只抽出几页），中国神华 2009、2011–2013，
  云南白药 2007，亚钾国际 2007、2008，电投能源 2007。中国海油 2018–2021 只有招股说明书，未登记。
- **东财报表行被其后重述**（`total_mismatch`，附注合计与报表行不符即不计）：中国神华 2025（东财 2025 年报行为合并后重述数：其他流动负债 110.17 亿、
  预计负债 155.48 亿、其他应付款 268.02 亿，原版年报分别为 38.46、99.60、129.48 亿）、电投能源 2025（14.30 亿对原版 8.85 亿）；与附注现金类、
  受限资产两张表的同年行同一来源问题，需先处理报表重述再核定。
- **版式未解**：其他应付款只列一行合计、构成只写文字（美的 2019–2025 等，`no_breakdown`）；少数 PDF 文字重叠或断行使逐行之和对不上（`rows_mismatch`）。
  受限资产 v2 未解的版式是窄列表格把长数字拆成上下两行、中间还夹页眉（中航光电、恩华药业、伯特利、云南白药 2025），仍为 `rows_mismatch`；
  v2 不认年初／增加／减少／年末的变动表（`movement_table`），没有合计行时须写明单位、每行不多于两期金额才按报表行值核对。
  整数（千元、百万元）表里标签自带数字的（「14 国贸 01」一类债券简称）会被当成金额，个别行因此 `rows_mismatch`。
- **混写判 `ambiguous`、整行不计**：宁德时代 2025「弃置费用及其他」1.47 亿，豪威集团 2020–2025「暂收暂借款」，中航高科 2018「往来拆借款」。
- **只取计入类、不判数额性质**：附注金额含应计利息（中材国际资金拆借 4.55 亿含利息，管理层讨论表的本金为 4.34 亿）；可转换债券只计负债成分
  （顺丰控股 2025 年 26.20 亿）。应付利息分表的「借款利息」不计（借款本身已在有息负债）。
- **受限资产 v2 沿用 v1 的原因规则**：同一行原因写了票据类就整行计入；中兴通讯 2015–2022 货币资金行的「注 1」同时写了承兑汇票保证金和存款准备金，
  准备金金额只写在散文里、未被拆出（中兴通讯不在池内）。天山铝业 2025 受限资产仍为 `text_unreadable`（附注页可按本次方法人工核定，未做）。
- **下载**：本次从巨潮补下约 430 份年报（池成员 FY2015–2025 与 FY2007–2014、三表名册其余公司 FY2015–2025 中缺的全部补下；名册其余公司
  2015 年前 240 份未下载，记 `not_fetched`）；2015 年前旧版年报多只按账龄列示其他应付款（`no_breakdown`），池成员 FY2007–2014 核定率约 54%。陕西煤业 2023
  （巨潮标题为「年报全文」、不含年份）与洛阳钼业 2022（全文不在年报分类）检索不到，仍为 `report_not_found`。

## 7. 规则与接入提案（不落地，待用户裁定）

### 7.1 §6.5.1 第 3 条（接在「有息负债另计应付短期融资款、吸收存款、同业存放、拆入资金、卖出回购、向中央银行借款、交易性与衍生金融负债」之后）

> 另计年报附注核定的类债务项目（OI-261，建带 `--note-debt notes`；`off` 只作复现）：其他流动负债中的短期应付债券、短期融资券、超短期融资券、
> 可转换债券等债务工具与明写的借款（含质押式回购借入资金），其他应付款「按款项性质列示」表中的借款、资金拆借（含企业借款及利息），按附注期末值计入；
> 预计负债中的弃置、复垦、环境恢复类义务按 `期末值 × (1 − 税率)` 计入，表内「减：一年内到期」的部分已在一年内到期的非流动负债、先扣除。
> 三项由 §6.7 第 1 步 `fetch_debt_note_items.py` 按原年报抽取到 `data/reference/debt_note_items.csv`（抽取范围为该行 ≥ 归母权益 2% 的一般企业年报；
> 附注合计与报表行相符、逐行期末值之和与合计相符、计入类行不与其他性质混写才计入；原文无法抽取的按原文人工核定，逐行记来源、页码与依据，登记
> `data/reference/debt_note_manual.csv`，报表行值其后变动超出抽取容差即失效）；供应链融资、反向保理、资产支持专项计划及保理转付款、票据融资、
> 融资租赁款、贵金属租借、记在其他应付款的财务公司吸收存款、已贴现未到期（带追索权、未终止确认）的票据与电子债权凭证（`review_amount`）
> 同样计入（应付保理费等费用、未贴现的应付信用证、已背书未终止确认的票据不计；标签写「背书或贴现」的按背书）。
> 报表现金行之外的弃置专户、矿山地质环境治理恢复基金等专项资金（`data/reference/decom_fund_items.csv`，其他流动资产、一年内到期的非流动
> 资产、其他非流动资产附注表合计与报表行相符才取）计超额现金，与弃置义务对冲；货币资金里的专项资金已按现金计。

（用户 2026-10-06 裁定：review 项计入、弃置义务税后计入、现金行之外的弃置专项资金计超额现金对冲。同一条「按规定只能用于弃置等经营
义务的专户存款按经营资产」须改为「`--note-debt notes` 时计超额现金」，以免与 `decom_fund_items.csv` 口径相冲；中国海油 2025 年 85.85 亿、
2024 年 98.70 亿在其他非流动资产。）

### 7.2 §6.7 第 1 步（取数清单由「十份」改「十一份」，在附注现金类一行之后插入；受限资产一行加 `--parser v2`）

```bash
python3 scripts/fetch_debt_note_items.py --workers 16   # 年报附注的类债务项目：短融／超短融、其他应付款借款与拆借、弃置义务（§6.5.1 第 3 条，只下载新增年报、全量重解析并入人工核定表）
python3 scripts/fetch_restricted_cash_items.py --workers 16 --parser v2   # 受限资产 v2 版式（OI-263：无「所有权」字样的标题、页眉千元、无合计行、字母脚注；v1 已核定的行不变）
```

落地时 `fetch_debt_note_items.py` 的 `OUT`／`MANUAL` 改指 `data/reference/debt_note_items.csv`／`debt_note_manual.csv`，`fetch_restricted_cash_items.py`
的 `--parser` 缺省改 `v2` 或在常设作业入口传参；第 2、2b 步建带命令加 `--note-debt notes`。计算节点连不上巨潮，新年报须先在交互节点下载（与附注现金类、受限资产两步相同）。

### 7.3 `roic_inputs` 接入（diff 草案，未应用）

```diff
--- a/scripts/roic_inputs.py
+++ b/scripts/roic_inputs.py
@@
 RESTRICTED_CASH_FILE = ROOT / "data/reference/restricted_cash_items.csv"
+# OI-261：年报附注核定的类债务项目（fetch_debt_note_items.py）；off 只作复现
+NOTE_DEBT_FILE = ROOT / "data/reference/debt_note_items.csv"
+NOTE_DEBT_MODES = ("off", "notes")
+DECOM_FUND_FILE = ROOT / "data/reference/decom_fund_items.csv"   # 报表现金行之外的弃置专项资金（2026-10-06 裁定计超额现金）
@@ class RoicYear:
     statutory_reserve: float = 0.0
+    note_debt: float = 0.0            # OI-261：附注核定的短融／超短融／借款／拆借及融资类待复核项（面值）
+    decom_liability: float = 0.0      # OI-261：弃置、复垦类义务 × (1 − 税率)
+    decom_fund: float = 0.0           # OI-261：报表现金行之外的弃置专项资金（计超额现金）
@@
-def _year_from_parts(code, period, parts, notice_cap, ic_floor=0.0, caliber="nonop", note_cash=0.0,
-                     restricted=0.0, pledged_wc=False, reserve=0.0) -> RoicYear | None:
+def _year_from_parts(code, period, parts, notice_cap, ic_floor=0.0, caliber="nonop", note_cash=0.0,
+                     restricted=0.0, pledged_wc=False, reserve=0.0,
+                     note_debt: tuple[float, float] = (0.0, 0.0), decom_fund: float = 0.0) -> RoicYear | None:
@@
     year.interest_debt = _sum(bal, DEBT_FIELDS) + (_sum(bal, FIN_LIAB_FIELDS) if caliber == "nonop" else 0.0)
+    if caliber == "nonop":
+        year.note_debt = note_debt[0]
+        year.interest_debt += year.note_debt
@@
         year.nopat = year.ebit * (1 - year.tax_rate)
+    if caliber == "nonop" and note_debt[1] > 0:
+        # 弃置义务支出时可抵税，按税后计入；其折现回转在财务费用里、本就不进 EBIT，两边同口径
+        year.decom_liability = note_debt[1] * (1 - (year.tax_rate if year.tax_rate is not None else DEFAULT_TAX_RATE))
+        year.interest_debt += year.decom_liability
+@@
         year.excess_cash = max(0.0, cash - operating_cash) + max(0.0, _sum(bal, OTHER_FIN_ASSET_FIELDS))
+        year.decom_fund = decom_fund
+        year.excess_cash += year.decom_fund   # 专款只能用于弃置，不受经营现金扣减，与税后弃置义务对冲
@@
+def load_debt_note_items(codes: set[str] | None = None, path: Path | None = None) -> dict[tuple[str, str], tuple[float, float]]:
+    """`debt_note_items.csv` → `{(代码, 年报期): (短融／超短融／借款／拆借及融资类待复核项合计, 弃置类义务合计)}`（元），只取 `status ∈ VERIFIED`。"""
+    from fetch_debt_note_items import VERIFIED
+    path = path or NOTE_DEBT_FILE
+    out: dict[tuple[str, str], tuple[float, float]] = {}
+    if not path.exists():
+        return out
+    with path.open(newline="", encoding="utf-8") as handle:
+        for row in csv.DictReader(handle):
+            code = (row.get("security_code") or "").zfill(6)
+            if row.get("status") not in VERIFIED or (codes is not None and code not in codes):
+                continue
+            key = (code, (row.get("report_date") or "")[:10])
+            debt, decom = out.get(key, (0.0, 0.0))
+            value = _num(row.get("counted_amount")) or 0.0
+            if row.get("line") != "PREDICT_LIAB":
+                value += _num(row.get("review_amount")) or 0.0      # 用户 2026-10-06 裁定：融资类待复核项一并计入
+            out[key] = (debt, decom + value) if row.get("line") == "PREDICT_LIAB" else (debt + value, decom)
+    return out
+
+def load_decom_fund_items(codes: set[str] | None = None, path: Path | None = None) -> dict[tuple[str, str], float]:
+    """`decom_fund_items.csv` → `{(代码, 年报期): 报表现金行之外的弃置专项资金（元）}`，只取 `status ∈ VERIFIED` 且
+    `counts_as_excess_cash = 1`（货币资金里的专项资金已按现金计；附注现金类抽取排除了弃置专户，不重复）。"""
+    from fetch_debt_note_items import VERIFIED
+    path = path or DECOM_FUND_FILE
+    out: dict[tuple[str, str], float] = {}
+    if not path.exists():
+        return out
+    with path.open(newline="", encoding="utf-8") as handle:
+        for row in csv.DictReader(handle):
+            code = (row.get("security_code") or "").zfill(6)
+            if (row.get("status") not in VERIFIED or row.get("counts_as_excess_cash") != "1"
+                    or (codes is not None and code not in codes)):
+                continue
+            key = (code, (row.get("report_date") or "")[:10])
+            out[key] = out.get(key, 0.0) + (_num(row.get("fund_amount")) or 0.0)
+    return out
@@ def load_statements(codes=None, stmt_dir=STMT_DIR, ic_floor=0.0, notice_cap=True, caliber="nonop",
-                    restricted_cash="off", tax_anomaly="off"):
+                    restricted_cash="off", tax_anomaly="off", note_debt="off"):
@@
+    if note_debt not in NOTE_DEBT_MODES:
+        raise ValueError(f"note_debt {note_debt!r} 不在 {NOTE_DEBT_MODES}")
+    debts = load_debt_note_items(codes) if caliber == "nonop" and note_debt == "notes" else {}
+    funds = load_decom_fund_items(codes) if caliber == "nonop" and note_debt == "notes" else {}
@@
             year = _year_from_parts(code, period, parts, notice_cap, ic_floor, caliber, note_cash.get((code, period), 0.0),
                                     restricted.get((code, period), 0.0), restricted_cash == "notes_wc",
-                                    reserves.get((code, period), 0.0))
+                                    reserves.get((code, period), 0.0), debts.get((code, period), (0.0, 0.0)),
+                                    funds.get((code, period), 0.0))
```

`attach_superseded_versions` 同样把 `debts`、`funds` 传给重述前版本；`build_historical_valuation_bands.py` 加
`parser.add_argument("--note-debt", choices=roic_inputs.NOTE_DEBT_MODES, default="off")` 并传入 `load_statements`。作用面：`interest_debt`
同时进投入资本（ROIC、增量 ROIC）与 `fin_nd`（每股净金融负债）；生产 WACC 取 `unlevered`，债务权重不受影响。季报行沿用最新年报的附注值。
弃置义务税率用当年 `tax_rate`（OI-264 的异常税率修正在其后执行，接入时可改用修正后税率）。OI-263 不需改 `roic_inputs`：生产取数改跑 `--parser v2` 即可。

## 8. 复现

```bash
python3 scripts/fetch_debt_note_items.py --pool --years 2015-2025 --workers 6      # 定位、补下缺失年报（巨潮，交互节点）、解析写实验表
python3 scripts/fetch_debt_note_items.py --parse-only                               # 全名册重解析（并入 debt_note_manual.csv）
python3 scripts/fetch_restricted_cash_items.py --parse-only --parser v2 \
  --out data/experiments/exp_oi261_263_20261006/restricted_cash_items_v2.csv
python3 scripts/test_debt_note_items.py && python3 scripts/test_restricted_cash_items.py
```

## 9. 弃置专项资金（用户 2026-10-06 裁定：弃置义务税后计入股权桥，报表现金行之外的专项资金计超额现金对冲）

`decom_fund_items.csv`（`fetch_debt_note_items.py --funds`）：对弃置类计入额 > 0 的 (代码, 财年) 逐行查专项资金，共 351 行，not_found 292，ok 55，manual 4。其他流动资产、一年内到期的非流动资产、其他非流动资产取自合计与报表行相符的附注表（`counts_as_excess_cash = 1`，计超额现金）；货币资金取货币资金附注、「现金和现金等价物」附注的表格行与写明单位的散文（`0`，模型已按现金计，只列出备查）；中国海油（文本层不可读）取 `cash_note_manual.csv` 依据栏，已对照 2025 年报第 181 页原文。合计：报表现金行之外 391.34 亿，货币资金内 498.01 亿（各年相加）。`not_found` 表示该行附注核上了但没有专项资金行，或附注核不上（`note_status`）。

| 公司 | 财年 | 行 | 金额（亿） | 计超额现金 | 状态 | 明细 |
|---|---|---|---|---|---|---|
| 000408 藏格矿业 | 2025 | MONETARYFUNDS | 0.05 | 否（已在货币资金） | ok | 环境恢复治理基金:5118767.82 |
| 000792 盐湖股份 | 2020 | MONETARYFUNDS | 0.08 | 否（已在货币资金） | ok | 环境治理恢复保证金:8096570.64 |
| 000933 神火股份 | 2017 | MONETARYFUNDS | 1.32 | 否（已在货币资金） | ok | 环境治理保证金:132397450.29 |
| 000933 神火股份 | 2018 | MONETARYFUNDS | 0.96 | 否（已在货币资金） | ok | 环境治理保证金:95958972.89 |
| 000933 神火股份 | 2019 | MONETARYFUNDS | 2.50 | 否（已在货币资金） | ok | 环境治理保证金:249565660.68 |
| 000933 神火股份 | 2020 | MONETARYFUNDS | 3.21 | 否（已在货币资金） | ok | 环境治理保证金:321073356.58 |
| 000933 神火股份 | 2021 | MONETARYFUNDS | 0.88 | 否（已在货币资金） | ok | 矿山环境治理恢复基金:87805123.80 |
| 000933 神火股份 | 2022 | MONETARYFUNDS | 0.33 | 否（已在货币资金） | ok | 矿山环境治理恢复基金:32610403.22 |
| 000933 神火股份 | 2023 | MONETARYFUNDS | 0.71 | 否（已在货币资金） | ok | 矿山环境治理恢复基金:70916327.28 |
| 000933 神火股份 | 2024 | MONETARYFUNDS | 0.78 | 否（已在货币资金） | ok | 矿山环境治理恢复基金:78296822.02 |
| 000933 神火股份 | 2025 | MONETARYFUNDS | 5.41 | 否（已在货币资金） | ok | 矿山环境治理恢复基金:540982186.45 |
| 600188 兖矿能源 | 2015 | MONETARYFUNDS | 1.08 | 否（已在货币资金） | ok | 环境治理保证金:107700000.00 |
| 600188 兖矿能源 | 2015 | OTHER_CURRENT_ASSET | 10.95 | 是 | ok | 环境治理保证金:1095493000.00 |
| 600188 兖矿能源 | 2017 | OTHER_CURRENT_ASSET | 1.74 | 是 | ok | 环境治理保证金:173899000.00 |
| 600188 兖矿能源 | 2018 | MONETARYFUNDS | 9.13 | 否（已在货币资金） | ok | 环境治理保证金:912763000.00 |
| 600188 兖矿能源 | 2018 | OTHER_CURRENT_ASSET | 1.74 | 是 | ok | 环境治理保证金:173899000.00 |
| 600188 兖矿能源 | 2020 | MONETARYFUNDS | 5.89 | 否（已在货币资金） | ok | 环境恢复治理基金:589247000.00 |
| 600188 兖矿能源 | 2020 | OTHER_CURRENT_ASSET | 0.64 | 是 | ok | 环境治理保证金:63899000.00 |
| 600188 兖矿能源 | 2021 | MONETARYFUNDS | 12.66 | 否（已在货币资金） | ok | 环境恢复治理基金:1266382000.00 |
| 600188 兖矿能源 | 2021 | OTHER_CURRENT_ASSET | 0.62 | 是 | ok | 环境治理保证金:62186000.00 |
| 600188 兖矿能源 | 2023 | MONETARYFUNDS | 27.36 | 否（已在货币资金） | ok | 环境恢复治理基金:2736368000.00 |
| 600188 兖矿能源 | 2023 | OTHER_CURRENT_ASSET | 0.62 | 是 | ok | 环境治理保证金:62186000.00 |
| 600188 兖矿能源 | 2024 | MONETARYFUNDS | 37.04 | 否（已在货币资金） | ok | 环境恢复治理基金:3704404000.00 |
| 600188 兖矿能源 | 2024 | OTHER_CURRENT_ASSET | 0.64 | 是 | ok | 环境治理保证金:63665000.00 |
| 600188 兖矿能源 | 2025 | MONETARYFUNDS | 54.96 | 否（已在货币资金） | ok | 环境恢复治理基金:5495680000.00 |
| 600188 兖矿能源 | 2025 | OTHER_CURRENT_ASSET | 0.64 | 是 | ok | 环境治理保证金:63557000.00 |
| 600938 中国海油 | 2022 | OTHER_NONCURRENT_ASSET | 83.60 | 是 | manual | 弃置费专户:8360000000.00；PDF 第210页 |
| 600938 中国海油 | 2023 | OTHER_NONCURRENT_ASSET | 90.39 | 是 | manual | 弃置费专户:9039000000.00；PDF 第211页 |
| 600938 中国海油 | 2024 | OTHER_NONCURRENT_ASSET | 98.70 | 是 | manual | 弃置费专户:9870000000.00；PDF 第187页 |
| 600938 中国海油 | 2025 | OTHER_NONCURRENT_ASSET | 85.85 | 是 | manual | 弃置费专户:8585000000.00；PDF 第181页 |
| 600988 赤峰黄金 | 2018 | OTHER_NONCURRENT_ASSET | 0.77 | 是 | ok | 复垦保证金:76539191.41 |
| 600988 赤峰黄金 | 2019 | MONETARYFUNDS | 0.06 | 否（已在货币资金） | ok | 地质环境治理恢复基金:6107612.79 |
| 600988 赤峰黄金 | 2019 | OTHER_NONCURRENT_ASSET | 0.80 | 是 | ok | 复垦保证金:80329003.48 |
| 600988 赤峰黄金 | 2020 | MONETARYFUNDS | 0.03 | 否（已在货币资金） | ok | 地质环境治理恢复基金:2598603.38 |
| 600988 赤峰黄金 | 2020 | OTHER_NONCURRENT_ASSET | 0.78 | 是 | ok | 复垦保证金:78441687.74 |
| 600988 赤峰黄金 | 2021 | MONETARYFUNDS | 0.03 | 否（已在货币资金） | ok | 地质环境治理恢复基金:2615139.39 |
| 600988 赤峰黄金 | 2021 | OTHER_NONCURRENT_ASSET | 0.87 | 是 | ok | 复垦保证金:87370427.34 |
| 600988 赤峰黄金 | 2023 | MONETARYFUNDS | 0.04 | 否（已在货币资金） | ok | 地质环境治理恢复基金:3190565.52;地质环境恢复治理基金:326549.48 |
| 600988 赤峰黄金 | 2023 | OTHER_NONCURRENT_ASSET | 1.03 | 是 | ok | 地质环境治理恢复基金:102974284.03 |
| 601088 中国神华 | 2022 | MONETARYFUNDS | 63.57 | 否（已在货币资金） | ok | 地质环境保护基金:6357000000.00 |
| 601088 中国神华 | 2023 | MONETARYFUNDS | 72.98 | 否（已在货币资金） | ok | 地质环境保护基金:7298000000.00 |
| 601225 陕西煤业 | 2019 | MONETARYFUNDS | 9.86 | 否（已在货币资金） | ok | 地质环境治理恢复与土地复垦基金:986252144.95 |
| 601225 陕西煤业 | 2020 | MONETARYFUNDS | 16.48 | 否（已在货币资金） | ok | 地质环境治理恢复与土地复垦基金:1648108982.86 |
| 601225 陕西煤业 | 2022 | MONETARYFUNDS | 55.96 | 否（已在货币资金） | ok | 地质环境治理恢复与土地复垦基金:5595597386.33 |
| 601225 陕西煤业 | 2025 | MONETARYFUNDS | 96.99 | 否（已在货币资金） | ok | 地质环境治理恢复与土地复垦基金:9699434526.39 |
| 601899 紫金矿业 | 2015 | MONETARYFUNDS | 0.66 | 否（已在货币资金） | ok | 闭矿生态复原准备金:66308378.00 |
| 601899 紫金矿业 | 2016 | MONETARYFUNDS | 0.67 | 否（已在货币资金） | ok | 闭矿生态复原准备金:66882941.00 |
| 601899 紫金矿业 | 2017 | MONETARYFUNDS | 0.68 | 否（已在货币资金） | ok | 闭矿生态复原准备金:67516073.00 |
| 601899 紫金矿业 | 2018 | MONETARYFUNDS | 1.01 | 否（已在货币资金） | ok | 闭矿生态复原准备金:101359612.00 |
| 601899 紫金矿业 | 2019 | MONETARYFUNDS | 1.21 | 否（已在货币资金） | ok | 闭矿生态复原准备金:120857247.00 |
| 601899 紫金矿业 | 2020 | MONETARYFUNDS | 0.24 | 否（已在货币资金） | ok | 闭矿生态复原准备金:23644758.00 |
| 601899 紫金矿业 | 2021 | MONETARYFUNDS | 0.81 | 否（已在货币资金） | ok | 闭矿生态复原准备金:80935443.00 |
| 601899 紫金矿业 | 2022 | MONETARYFUNDS | 1.42 | 否（已在货币资金） | ok | 闭矿生态复原准备金:142488327.00 |
| 601899 紫金矿业 | 2023 | MONETARYFUNDS | 2.65 | 否（已在货币资金） | ok | 闭矿生态复原准备金:265105034.00 |
| 601899 紫金矿业 | 2024 | MONETARYFUNDS | 3.46 | 否（已在货币资金） | ok | 闭矿生态复原准备金:345899833.00 |
| 601899 紫金矿业 | 2025 | MONETARYFUNDS | 4.40 | 否（已在货币资金） | ok | 闭矿生态复原准备金:440477664.00 |
| 603993 洛阳钼业 | 2016 | MONETARYFUNDS | 0.20 | 否（已在货币资金） | ok | 矿山环境恢复治理专项保证金:20016029.71 |
| 603993 洛阳钼业 | 2017 | MONETARYFUNDS | 0.24 | 否（已在货币资金） | ok | 矿山环境恢复治理专项保证金:24420803.62 |

弃置类计入额 > 0 而各行均未找到专项资金的（FY2015–2025）：洛阳钼业 2019–2021、2025（2016、2017 年货币资金内有「矿山环境恢复治理专项保证金」0.20、0.24 亿）；藏格矿业 2024；陕西煤业 2015、2016、2018（2018 年货币资金受限明细里「矿山地质治理恢复与土地复垦基金」2.80 亿在两列表里只剩一个数，期末期初判不出，未取）；兖矿能源 2019（货币资金受限明细里环境治理保证金只有期初数）；中国神华 2024（受限说明把地质环境治理恢复基金与借款保证金等合写为 141.89 亿，未拆）；苏能股份 2023–2025（基金与票据保证金合写）；中国石油、金钼股份、天齐锂业、德赛西威、宁德时代、安克创新、扬农化工、城发环境各年。
