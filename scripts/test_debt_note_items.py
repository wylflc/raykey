#!/usr/bin/env python3
"""OI-261 附注类债务项目抽取（其他流动负债、其他应付款、预计负债）的单元测试（无网络；版式取自真实年报文本）。"""
from __future__ import annotations

import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_debt_note_items as dn  # noqa: E402

NOTES = "七、合并财务报表项目注释\n1、货币资金\n单位：元\n项目 期末余额 期初余额\n库存现金 1.00 1.00\n"


def task(lines: dict, year: int = 2025, **extra) -> dict:
    return dict(code="000001", name="测试", year=year, report_date=f"{year}-12-31", lines=lines, parent_equity=1e11,
                total_other_payable=extra.get("total_other_payable", lines.get("OTHER_PAYABLE", 0.0)),
                interest_payable=extra.get("interest_payable", 0.0), dividend_payable=extra.get("dividend_payable", 0.0))


def parse(text: str, line: str, t: dict) -> dict:
    full = NOTES + text
    return dn.parse_line(full, dn.cn.notes_start(full), line, t)


class OtherCurrentLiabilityTest(unittest.TestCase):
    YILI_2025 = ("44、其他流动负债\n其他流动负债情况\n√适用 □不适用\n单位：元 币种：人民币\n项目 期末余额 期初余额\n"
                 "短期应付债券 9,043,394,520.53 10,024,230,136.98\n应付退货款 30,328,690.93\n"
                 "未到期责任准备金 17,944,237.20 20,157,058.48\n担保赔偿准备金 167,343,860.35 165,343,305.51\n"
                 "待转销项税 1,186,797,761.13 1,218,928,979.35\n合计 10,445,809,070.14 11,428,659,480.32\n"
                 "短期应付债券的增减变动：\n√适用 □不适用\n单位：元 币种：人民币\n债券名称 面值 票面利率\n（%） 发行日期\n"
                 "合计 / / / / 19,000,000,000.00 10,024,230,136.98 9,000,000,000.00\n45、长期借款\n")

    def test_short_term_bonds_and_blank_cell(self):
        r = parse(self.YILI_2025, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 10_445_809_070.14}))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 9_043_394_520.53, places=2)
        self.assertIn("应付退货款:30328690.93:other", r["items"])          # 只有一个数的行按两列合计判为期末

    def test_empty_template_rows_do_not_leak_into_next_label(self):
        # 上交所模板里金额空白的「短期应付债券」「应付退货款」行不并入下一行（景津装备 2025）
        body = ("44、其他流动负债\n其他流动负债情况\n√适用 □不适用\n单位：元 币种：人民币\n项目 期末余额 期初余额\n"
                "短期应付债券\n应付退货款\n待转销项税 91,067,958.87 81,186,112.53\n"
                "已背书尚未到期的应收票据 21,465,326.80 46,485,956.79\n已背书未终止确认的供应链金融负债 10,000.00\n"
                "合 计 112,543,285.67 127,672,069.32\n45、长期借款\n")
        r = parse(body, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 112_543_285.67}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["counted"], 0.0)

    def test_thousand_yuan_page_unit_and_unlabeled_total(self):
        # 事务所版式：单位写在页眉，合计行只有数字（顺丰控股 2025，可转换债券负债部分计入其他流动负债）
        body = ("(除特别注明外，金额单位为人民币千元)\n(30) 其他流动负债\n\n2025年12月31日 2024年12月31日\n"
                "超短期融资券 – 807,787\n可转换债券 (a) 2,620,001 –\n合同负债形成的待转销项税额 120,011 92,021\n"
                "其他 9,976 18,621\n2,749,988 918,429\n(a) 可转换债券的具体信息如下：\n(31) 长期借款\n")
        r = parse(body, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 2_749_988_000.0}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["unit"], 1e3)
        self.assertAlmostEqual(r["counted"], 2_620_001_000.0)

    def test_financing_arrangements_are_review_only(self):
        body = ("44、其他流动负债\n单位：元\n项目 期末余额 期初余额\n短期融资债券 702,249,589.04\n"
                "待转销项税额 309,178,739.99 315,774,129.30\n供应链融资 68,666,739.79 83,350,442.19\n"
                "背书未到期的商业承兑汇票 4,399,659.00\n合计 1,080,095,068.82 403,524,230.49\n45、长期借款\n")
        r = parse(body, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 1_080_095_068.82}))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 702_249_589.04, places=2)
        self.assertAlmostEqual(r["review"], 68_666_739.79, places=2)

    def test_total_must_match_statement(self):
        r = parse(self.YILI_2025, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 20_000_000_000.0}))
        self.assertNotEqual(r["status"], "ok")

    def test_discounted_bills_are_financing_endorsed_are_not(self):
        # 汇川技术 2025：已贴现未到期票据（带追索权、未终止确认）是融资，列 review（2026-10-06 裁定计入）；已背书的按经营负债；表中夹页眉页码
        body = ("34、其他流动负债\n单位：元\n项目 期末余额 期初余额\n"
                "已贴现未到期票据及电子债权凭证 861,816,334.80 423,306,893.02\n待转销项税 83,649,382.59 80,960,279.86\n"
                "深圳市汇川技术股份有限公司 2025 年年度报告全文\n190\n"
                "已背书未终止确认票据及电子债权凭证 1,394,536,955.64 1,053,871,055.15\n"
                "合计 2,340,002,673.03 1,558,138,228.03\n35、长期借款\n")
        r = parse(body, "OTHER_CURRENT_LIAB", task({"OTHER_CURRENT_LIAB": 2_340_002_673.03}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["counted"], 0.0)
        self.assertAlmostEqual(r["review"], 861_816_334.80, places=2)
        self.assertIn("已背书未终止确认票据及电子债权凭证:1394536955.64:other", r["items"])


class OtherPayableTest(unittest.TestCase):
    GREE_2025 = ("38、其他应付款\n项目 期末余额 期初余额\n应付股利 5,591,546,379.65 3,889,950.33\n"
                 "其他应付款【注 1】 5,649,443,259.64 4,553,021,754.89\n合计 11,240,989,639.29 4,556,911,705.22\n"
                 "【注 1】上表中其他应付款指扣除应付利息、应付股利后的其他应付款；\n（1）应付股利\n项目 期末余额 期初余额\n"
                 "普通股股利 5,585,741,622.87 602,881.87\n其他 5,804,756.78 3,287,068.46\n合计 5,591,546,379.65 3,889,950.33\n"
                 "【注】本公司无重要的账龄超过 1年的应付股利。\n（2）其他应付款\n1)按款项性质列示其他应付款\n项目 期末余额 期初余额\n"
                 "往来款 2,698,315,049.65 1,626,920,031.91\n企业借款及利息 1,547,471,401.00 1,503,105,131.31\n"
                 "押金保证金 1,403,656,808.99 1,422,996,591.67\n合计 5,649,443,259.64 4,553,021,754.89\n"
                 "2)账龄超过 1年的重要其他应付款\n项目 期末余额 未偿还或结转的原因\n单位 1 1,072,646,600.02 未达到偿还条件\n"
                 "合计 1,072,646,600.02\n39、 一年内到期的非流动负债\n")

    def test_two_level_layout_counts_borrowings(self):
        t = task({"OTHER_PAYABLE": 11_240_989_639.29}, dividend_payable=5_591_546_379.65)
        r = parse(self.GREE_2025, "OTHER_PAYABLE", t)
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["notes_total"], 11_240_989_639.29, places=2)        # 一级表核对报表行
        self.assertAlmostEqual(r["breakdown_total"], 5_649_443_259.64, places=2)     # 性质表核对一级表的其他应付款行
        self.assertAlmostEqual(r["counted"], 1_547_471_401.00, places=2)

    def test_sse_layout_with_percentages_in_prose(self):
        body = ("41、其他应付款\n(1).项目列示\n√适用 □不适用\n单位：元 币种：人民币\n项目 期末余额 期初余额\n应付利息\n"
                "应付股利 118,839,597.50 125,409,200.12\n其他应付款 1,626,204,376.97 1,943,142,386.53\n"
                "合计 1,745,043,974.47 2,068,551,586.65\n(3).应付股利\n分类列示\n√适用 □不适用\n单位：元 币种：人民币\n"
                "项目 期末余额 期初余额\n普通股股利 118,839,597.50 125,409,200.12\n合计 118,839,597.50 125,409,200.12\n"
                "其他说明：应付股利比年初下降 5.24%。\n(4).其他应付款\n按款项性质列示其他应付款\n√适用 □不适用\n"
                "单位：元 币种：人民币\n项目 期末余额 期初余额\n押金及保证金 426,832,985.48 503,137,588.18\n"
                "往来款 223,227,071.55 247,575,789.08\n资金拆借 455,476,680.71 451,171,610.68\n"
                "限制性股票回购义务 14,158,218.06 206,615,687.49\n其他 506,509,421.17 534,642,711.10\n"
                "合计 1,626,204,376.97 1,943,142,386.53\n42、持有待售负债\n")
        r = parse(body, "OTHER_PAYABLE", task({"OTHER_PAYABLE": 1_745_043_974.47}, dividend_payable=118_839_597.50))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 455_476_680.71, places=2)

    def test_mixed_label_makes_report_ambiguous(self):
        body = ("38、其他应付款\n单位：元\n项目 期末余额 期初余额\n应付销售返点 1,029,477,027.74 929,210,630.55\n"
                "暂收暂借款 6,269,174.28 3,072,466.66\n其他 38,001,818.06 74,224,924.52\n合计 1,073,748,020.08 1,006,508,021.73\n"
                "39、一年内到期的非流动负债\n")
        r = parse(body, "OTHER_PAYABLE", task({"OTHER_PAYABLE": 1_073_748_020.08}))
        self.assertEqual(r["status"], "ambiguous")
        self.assertEqual(r["counted"], 0.0)

    def test_unlabeled_totals_hk_style_with_deposits_for_review(self):
        # 港式：百万元、合计行只有数字；财务公司吸收存款列待复核（中国神华 2019）
        body = ("人民币百万元\n24、 其他应付款\n\n按款项性质列示的其他应付款\n\n2019 年\n12 月 31 日   2018 年\n12 月 31 日\n"
                "吸收存款 (注) 32,184   30,143\n保证金 1,019   1,345\n应付股利 1,631   1,501\n其他 9,381   10,146\n"
                "  44,215   43,135\n注：吸收存款为国家能源集团及其子公司存放于神华财务公司的款项。\n25、 一年内到期的非流动负债\n")
        r = parse(body, "OTHER_PAYABLE", task({"OTHER_PAYABLE": 44_215_000_000.0}, year=2019))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["counted"], 0.0)
        self.assertAlmostEqual(r["review"], 32_184_000_000.0)

    def test_classify_rules(self):
        self.assertEqual(dn.classify("企业借款及利息", "OTHER_PAYABLE")[0], "loan")
        self.assertEqual(dn.classify("子公司少数股东借款", "OTHER_PAYABLE")[0], "loan")
        self.assertEqual(dn.classify("应付短期借款利息", "OTHER_PAYABLE")[0], "other")       # 应计利息不是借款本身
        self.assertEqual(dn.classify("借款及往来款", "OTHER_PAYABLE")[0], "mixed")
        self.assertEqual(dn.classify("往来款（股东借款）", "OTHER_PAYABLE")[0], "loan")      # 括注只写借款
        self.assertEqual(dn.classify("往来款（含借款）", "OTHER_PAYABLE")[0], "mixed")
        self.assertEqual(dn.classify("反向保理业务", "OTHER_PAYABLE")[0], "review")
        self.assertEqual(dn.classify("融资租赁保证金", "OTHER_PAYABLE")[0], "other")
        self.assertEqual(dn.classify("应付保理费", "OTHER_PAYABLE")[0], "other")          # 费用不是融资本金
        self.assertEqual(dn.classify("应付信用证", "OTHER_CURRENT_LIAB")[0], "other")     # 同应付票据
        self.assertEqual(dn.classify("已贴现尚未到期的信用证", "OTHER_CURRENT_LIAB")[0], "review")
        self.assertEqual(dn.classify("已贴现未到期的商业承兑汇票", "OTHER_CURRENT_LIAB")[0], "review")   # 贴现不受「承兑汇票」排除
        self.assertEqual(dn.classify("票据贴现款", "OTHER_PAYABLE")[0], "review")
        self.assertEqual(dn.classify("已背书或贴现未终止确认的票据", "OTHER_CURRENT_LIAB")[0], "other")   # 模板措辞，按背书
        self.assertEqual(dn.classify("已背书或\n贴现未终止确认的票据", "OTHER_CURRENT_LIAB")[0], "other")  # 连词断行
        self.assertEqual(dn.classify("票据贴现保证金", "OTHER_CURRENT_LIAB")[0], "other")
        self.assertEqual(dn.classify("应付贴现利息", "OTHER_CURRENT_LIAB")[0], "other")
        self.assertEqual(dn.classify("超短期融资券", "OTHER_CURRENT_LIAB")[0], "bond")
        self.assertEqual(dn.classify("租赁机构借款", "OTHER_CURRENT_LIAB")[0], "loan")
        self.assertEqual(dn.classify("未终止确认的商业票据支付义务", "OTHER_CURRENT_LIAB")[0], "other")
        self.assertEqual(dn.classify("矿山地质环境治理恢\n复与土地复垦基金", "PREDICT_LIAB")[0], "decom")
        self.assertEqual(dn.classify("产品质量保证", "PREDICT_LIAB")[0], "other")
        self.assertEqual(dn.classify("弃置费用及其他", "PREDICT_LIAB")[0], "mixed")
        self.assertEqual(dn.classify("减：一年内到期的预计负债", "PREDICT_LIAB")[0], "deduct")


class ProvisionTest(unittest.TestCase):
    def test_decommissioning_net_of_current_portion(self):
        body = ("34、预计负债\n单位：元\n项目 期末余额 期初余额 形成原因\n未决诉讼  9,048,274.81\n"
                "复垦、弃置及环境清理义务（注） 1,284,992,855.69 1,261,569,210.33\n"
                "减：一年内到期的预计负债 -66,584,974.81 -65,399,774.81\n合计 1,218,407,880.88 1,205,217,710.33\n"
                "其他说明：注：根据财政部规定计提。\n35、递延收益\n")
        r = parse(body, "PREDICT_LIAB", task({"PREDICT_LIAB": 1_218_407_880.88}))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["deducted"], 66_584_974.81, places=2)      # 一年内到期部分已在有息负债
        self.assertAlmostEqual(r["counted"], 1_218_407_880.88, places=2)

    def test_reversed_columns_and_sub_rows(self):
        # 表头写「期初 期末」而列序与报表行相符的是第一列；「其中：」子行与母项同额不重复计（重庆啤酒 2025）
        body = ("50、预计负债\n√ 适用 □不适用\n单位：元  币种：人民币\n项目 期初余额 期末余额 形成原因\n对外提供担保\n"
                "包销业务相关负债 144,973,691.22\n未决诉讼 11,295,353.93 279,945,417.62\n其中：包销诉讼案 254,029,189.86\n"
                "              玻璃瓶诉讼案 10,011,494.96 24,632,368.79\n              其他 1,283,858.97 1,283,858.97\n"
                "产品质量保证\n合计 156,269,045.15 279,945,417.62 /\n51、递延收益\n")
        r = parse(body, "PREDICT_LIAB", task({"PREDICT_LIAB": 156_269_045.15}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["counted"], 0.0)

    def test_sub_row_carries_decommissioning(self):
        body = ("50、预计负债\n单位：元\n项目 期末余额 期初余额 形成原因\n其他 399,247,852.50\n其中：复垦、弃置及环境清理\n义务\n"
                "399,247,852.50\n合计 399,247,852.50 --\n51、递延收益\n")
        r = parse(body, "PREDICT_LIAB", task({"PREDICT_LIAB": 399_247_852.50}, year=2017))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 399_247_852.50, places=2)

    def test_movement_table_with_unlabeled_total(self):
        body = ("38. 预计负债\n\n2019年\n年初余额 本年增加 本年减少 年末余额\n"
                "矿山环境恢复准备金（注 1） 2,061,474,181 892,575,291 (145,269,157) 2,808,780,315\n"
                "设定受益计划 62,754,474 9,662,103 (6,010,548) 66,406,029\n诉讼准备金 41,621,501 10,960,884 (56,446) 52,525,939\n"
                "待执行亏损合同 119,810,882 - (119,810,882) -\n"
                "2,285,661,038 913,198,278 (271,146,033) 2,927,712,283\n39. 递延收益\n")
        r = parse(body, "PREDICT_LIAB", task({"PREDICT_LIAB": 2_927_712_283.0}, year=2019))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 2_808_780_315.0)

    def test_transposed_hk_table_uses_long_term_row(self):
        body = ("人民币百万元\n28、 预计负债\n\n预计负债主要是预提复垦费用。\n\n  预提复垦费用   其他   合计 \n"
                "2023 年 12 月 31 日 9,104   1,095   10,199 \n本年增加 1,032   323   1,355 \n本年减少 (290)   (798)   (1,088) \n"
                "2024 年 12 月 31 日 9,846   620   10,466 \n减：一年内到期部分 400   0   400 \n长期部分 9,446   620   10,066 \n"
                "29、 股本 \n")
        r = parse(body, "PREDICT_LIAB", task({"PREDICT_LIAB": 10_066_000_000.0}, year=2024))
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["counted"], 9_446_000_000.0)


class SectionTest(unittest.TestCase):
    def test_continuation_heading_is_skipped(self):
        text = NOTES + ("31. 其他应付款（续）\n于 2018年 12月 31日，账龄超过一年的重要其他应付款如下：\n"
                        "31. 其他应付款\n2019年 2018年\n工程设备款 100 90\n")
        found = dn.heading_end(text, "其他应付款", dn.cn.notes_start(text))
        self.assertIn("工程设备款", text[found[0]:found[0] + 60])

    def test_auditor_style_spaced_heading(self):
        text = NOTES + "19 其他应付款\n\n2018 年 12 月 31 日  2017 年 12 月 31 日\n应付租户押金 670,894,699  645,899,595\n20 一年内到期\n"
        body = dn.section_body(text, "其他应付款", dn.cn.notes_start(text))
        self.assertIn("应付租户押金", body)

    def test_unreadable_text_layer(self):
        with tempfile.TemporaryDirectory() as folder:
            old = dn.cn.CACHE
            dn.cn.CACHE = Path(folder)
            try:
                (Path(folder) / "000001").mkdir()
                (Path(folder) / "000001" / "2025.txt.gz").write_bytes(gzip.compress("ඳս઒ ğ600938".encode()))
                rows = dn.parse_task(task({"PREDICT_LIAB": 1e9}), dict(status="ok", url="x"))
            finally:
                dn.cn.CACHE = old
        self.assertEqual(rows[0]["status"], "text_unreadable")


class DecomFundTest(unittest.TestCase):
    """用户 2026-10-06 裁定：报表现金行之外的弃置专项资金计超额现金对冲；货币资金里的只列出备查。"""

    def test_fund_row_in_reconciled_asset_note(self):
        text = NOTES + ("18、其他非流动资产\n单位：元\n项目 期末余额 期初余额\n一年以上定期存款 100.00 50.00\n"
                        "弃置费专户存款 200.00 150.00\n预付工程款 25.00 10.00\n合计 325.00 210.00\n19、短期借款\n")
        r = dn._fund_rows_from_note(text, dn.cn.notes_start(text), "OTHER_NONCURRENT_ASSET", 325.0)
        self.assertEqual(r["note_status"], "ok")
        self.assertEqual(r["funds"], [("弃置费专户", 200.0)])
        bad = dn._fund_rows_from_note(text, dn.cn.notes_start(text), "OTHER_NONCURRENT_ASSET", 9_000_000_000.0)
        self.assertEqual(bad["funds"], [])                                  # 附注合计与报表行不符不取

    def test_cash_prose_amount_before_name_and_mixed_label(self):
        text = NOTES.replace("1、货币资金\n单位：元\n项目 期末余额 期初余额\n库存现金 1.00 1.00\n", "") + (
            "1、货币资金\n单位：元\n项目 期末余额 期初余额\n库存现金 1,000.00 2,000.00\n其他货币资金（注 1） 9,000.00 8,000.00\n"
            "合计 10,000.00 10,000.00\n注 1：本集团其他货币资金主要包含：人民币 4,000.00 元(2024 年 12 月 31 日：人民币 3,000.00 元)"
            "为闭矿生态复原准备金，按规定存入银行专户；地质环境治理恢复基金、借款保证金等 3,500.00 元使用受限。\n2、交易性金融资产\n")
        r = dn._fund_rows_in_cash(text, 10_000.0)
        self.assertEqual(r["funds"], [("闭矿生态复原准备金", 4_000.0)])          # 混写借款保证金的合计数不取

    def test_manual_basis_text(self):
        hits = list(dn.FUND_AMOUNT.finditer("附注(六)18：一年以上到期的定期存款17,259百万元计入；弃置费专户存款8,585百万元，弃置费专户存款按规定只能用于油气设施弃置"))
        self.assertEqual([(h["amount"], h["unit"]) for h in hits], [("8,585", "百万元")])


class ManualTest(unittest.TestCase):
    def _write(self, folder: Path) -> Path:
        path = folder / "manual.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=dn.MANUAL_FIELDS)
            writer.writeheader()
            writer.writerow(dict(security_code="600938", security_name="中国海油", fiscal_year="2025", report_date="2025-12-31",
                                 line="PREDICT_LIAB", line_label="预计负债", statement_amount="116039000000.00",
                                 notes_total="116039000000.00", counted_amount="116039000000.00", counted_kind="decom",
                                 counted_items="弃置义务:116039000000.00:decom", review_amount="0.00", review_items="",
                                 unit="1000000.0", source_date="2026-03-27", source_title="年报", source_url="url",
                                 source_page="PDF 第187页", basis="变动表只有弃置义务", registered_at="2026-10-06"))
        return path

    def test_manual_row_replaces_and_goes_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._write(Path(folder))
            merged = {("600938", 2025): [dict(security_code="600938", fiscal_year="2025", line="PREDICT_LIAB",
                                              statement_amount="116039000000.00", counted_amount="0.00", status="text_unreadable")]}
            self.assertEqual(dn.apply_manual(merged, path), 1)
            row = merged[("600938", 2025)][0]
            self.assertEqual((row["status"], row["counted_amount"]), ("manual", "116039000000.00"))
            merged = {("600938", 2025): [dict(security_code="600938", fiscal_year="2025", line="PREDICT_LIAB",
                                              statement_amount="150000000000.00", counted_amount="0.00", status="text_unreadable")]}
            dn.apply_manual(merged, path)
            row = merged[("600938", 2025)][0]
            self.assertEqual((row["status"], row["counted_amount"]), ("manual_stale", "0.00"))
        self.assertIn("manual", dn.VERIFIED)


if __name__ == "__main__":
    unittest.main()
