#!/usr/bin/env python3
"""OI-219 受限资产附注解析与质押开票现金类扣减的单元测试（无网络）。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_restricted_cash_items as rc  # noqa: E402
import roic_inputs  # noqa: E402


class ParseSectionTest(unittest.TestCase):
    def test_one_period_table_with_reasons(self):
        body = ("\n单位：元 币种：人民币\n项目 期末账面价值 受限原因\n"
                "货币资金 1,096,591,549.00 质押开具银行承兑汇票 注1\n其他非流动资产 3,230,000,000.00 质押开具银行承兑汇票 注2\n"
                "固定资产 200,000,000.00 抵押借款\n合计 4,526,591,549.00 /\n其他说明：\n注1：银行承兑票据保证金。\n")
        r = rc.parse_section(body)
        self.assertEqual(r["status"], "ok")
        self.assertEqual([x["label"] for x in r["rows"]], ["货币资金", "其他非流动资产", "固定资产"])
        self.assertIn("承兑汇票", r["rows"][0]["reason"])

    def test_two_period_table_footnote_and_opening_only_row(self):
        # 新版式：每期「账面余额 账面价值 类型 情况」，原因只写「质押 注 N」；固定资产行只有期初数
        body = ("\n单位：元 币种：人民币\n项目\n期末 期初\n账面余额 账面价值 受限\n类型\n受限\n情况 账面余额 账面价值 受限\n类型\n受限\n情况\n"
                "货币资\n金\n473,334,44\n8.37\n473,334,\n448.37 质押 注 1 1,099,964\n,455.37\n1,099,964,\n455.37 质押 注 1\n"
                "其他非\n流动资\n产\n4,100,000,\n000.00\n4,100,00\n0,000.00 质押 注 2 4,101,970\n,833.33\n4,101,970,\n833.33 质押 注 2\n"
                "固定资\n产\n56,944,50\n2.69\n56,944,502\n.69 抵押 注 3\n"
                "合计 4,573,334,\n448.37\n4,573,33\n4,448.37 / / 5,258,879\n,791.39\n5,258,879,\n791.39 / /\n其他说明：\n"
                "注 1：以银行承兑票据保证金为质押开具银行承兑汇票。\n注 2：以三年期定期存单为质押开具银行承兑汇票。\n注 3：借款抵押。\n")
        r = rc.parse_section(body)
        self.assertEqual(r["status"], "ok")
        self.assertEqual([x["label"] for x in r["rows"]], ["货币资金", "其他非流动资产"])
        self.assertAlmostEqual(r["rows"][1]["value"], 4_100_000_000.00, places=2)
        self.assertIn("承兑汇票", r["rows"][1]["reason"])

    def test_cash_note_breakdown_table(self):
        body = "\n项  目 期末余额 年初余额\n银行承兑汇票保证金 27,314,056.04 9,317,741.07\n定期存款 2,040,865.04\n合 计 29,354,921.08 9,317,741.07\n"
        r = rc.parse_section(body, cash_note=True)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(len(r["rows"]), 2)
        self.assertIn("承兑汇票", r["rows"][0]["reason"])


class ClassifyTest(unittest.TestCase):
    def setUp(self):
        self.task = dict(code="000001", year=2025, balance={"MONETARYFUNDS": 1_000.0})

    def test_categories_and_caps(self):
        rows = [dict(label="货币资金", value=800.0, reason="银行承兑汇票保证金、借款质押"),
                dict(label="其他非流动资产", value=500.0, reason="质押开具银行承兑汇票"),
                dict(label="一年内到期的非流动资产", value=300.0, reason="质押"),
                dict(label="交易性金融资产", value=100.0, reason="借款质押"),
                dict(label="固定资产", value=900.0, reason="开具保函抵押")]
        note_cash = {("000001", 2025, "OTHER_NONCURRENT_ASSET"): 400.0,
                     ("000001", 2025, "NONCURRENT_ASSET_1YEAR"): 300.0}
        c = rc.classify(rows, self.task, note_cash)
        self.assertAlmostEqual(c["counted"], 800.0 + 400.0)      # 混写借款整行计入；附注行以核定现金为限
        self.assertAlmostEqual(c["generic"], 300.0)
        self.assertAlmostEqual(c["loan"], 100.0)                 # 交易性金融资产无报表行值时不设限


class CashNoteBreakdownTest(unittest.TestCase):
    """OI-257：货币资金类行原因笼统时读受限分项；法定存款准备金。"""
    GREE_2025 = ("1、 货币资金\n项目 期末余额 期初余额\n库存现金 317,120.96 493,036.20\n"
                 "其他货币资金【注 1】 9,253,823,481.13 35,080,968,670.38\n存放中央银行款项【注 2】 1,911,851,424.72 1,876,552,187.02\n"
                 "合计 11,165,992,026.81 36,957,013,893.60\n"
                 "【注 1】其他货币资金期末余额主要为银行承兑汇票保证金、保函保证金、信用证保证金存款\n等，其中受限制资金为 8,675,252,384.99元；\n"
                 "【注 2】公司存放中央银行款项中法定存款准备金为 1,902,339,726.09元，其使用受到限制；\n2、 交易性金融资产\n")
    TASK = dict(code="000651", year=2025, balance={"MONETARYFUNDS": 11_165_992_026.81})

    def test_prose_breakdown_with_reserve_and_manual_loan(self):
        detail = [dict(label="货币资金", value=10_577_592_111.08, cat="generic", reason="法定存款准备金及保证金等"),
                  dict(label="其他债权投资", value=7_900_000_000.0, cat="generic", reason="质押")]
        out = rc.cash_note_breakdown(self.GREE_2025, self.TASK, detail, 18_477_592_111.08, 640_006.60)
        self.assertAlmostEqual(out["fallback"], 8_675_252_384.99 - 640_006.60, places=2)   # 票据类保证金先减借款质押余额
        self.assertAlmostEqual(out["reserve"], 1_902_339_726.09, places=2)
        self.assertAlmostEqual(out["generic"], 7_900_000_000.0 + 640_006.60, places=2)     # 质押存单维持笼统
        self.assertEqual(out["breakdown_source"], "cash_note:generic")

    def test_reserve_without_restricted_table(self):
        out = rc.cash_note_breakdown(self.GREE_2025, self.TASK, [], 0.0, 0.0)
        self.assertEqual(out["fallback"], 0.0)
        self.assertAlmostEqual(out["reserve"], 1_902_339_726.09, places=2)

    def test_reason_column_and_opening_only_rows(self):
        # 「理由」列重复行名（兖矿 2023）；只有期初数的行（中材国际 2019）按期末 0 计
        rows = rc.labeled_rows("项目 本期金额 上期金额 理由\n票据及信用证保证金 2,875,788 2,857,243 票据及信用证保证金\n"
                               "环境恢复治理基金 2,736,368 2,165,121 环境恢复治理基金\n法定存款保证金 1,524,257 2,524,619 法定存款保证金\n"
                               "贷款保证金  27 贷款保证金\n合计 7,136,413 7,547,010 /\n", "integer")
        found = rc.find_breakdown(rows, 7_136_413_000.0, 1e3)
        self.assertIsNotNone(found)
        cats = {i["label"]: i["cat"] for i in found["items"]}
        self.assertEqual(cats, {"票据及信用证保证金": "notes", "环境恢复治理基金": "generic", "法定存款保证金": "reserve"})

    def test_notes_row_carves_out_reserve(self):
        # 受限资产表同一行写票据类原因而整行计入、又写明法定存款准备金（伊利 2021）：先拆出准备金
        text = ("1、货币资金\n单位：元\n项目 期末余额 期初余额\n银行存款 1,000,000,000.00 900,000,000.00\n"
                "其他货币资金 481,558,991.11 300,000,000.00\n合计 1,481,558,991.11 1,200,000,000.00\n"
                "受限制的货币资金明细如下：\n项目 期末余额 期初余额\n存放中央银行法定存款准备金 391,966,366.16 149,569,894.32\n"
                "担保保证金 61,907,515.05 25,256,300.27\n信用证保证金 27,685,109.90\n合计 481,558,991.11 174,826,194.59\n2、交易性金融资产\n")
        task = dict(code="600887", year=2021, balance={"MONETARYFUNDS": 1_481_558_991.11})
        detail = [dict(label="货币资金", value=481_558_991.11, cat="notes", reason="存放中央银行法定存款准备金、担保保证金、信用证保证金")]
        out = rc.cash_note_breakdown(text, task, detail, 0.0, 0.0)
        self.assertAlmostEqual(out["reserve"], 391_966_366.16, places=2)
        self.assertAlmostEqual(out["carve"], 391_966_366.16, places=2)
        self.assertEqual(out["fallback"], 0.0)

    def test_sum_mismatch_falls_back_to_generic(self):
        detail = [dict(label="货币资金", value=12_000_000_000.0, cat="generic", reason="保证金")]
        out = rc.cash_note_breakdown(self.GREE_2025, self.TASK, detail, 12_000_000_000.0, 0.0)
        self.assertEqual(out["fallback"], 0.0)                          # 分项之和与受限额不符不补计
        self.assertAlmostEqual(out["reserve"], 1_902_339_726.09, places=2)


class ParserV2Test(unittest.TestCase):
    """OI-263：v2 版式（「使用权受到限制的资产」、页眉千元、无合计行、字母脚注）；v1 已核定的行在 v2 下不变。"""
    MIDEA_2025 = ("美的集团股份有限公司\n2025 年度财务报表附注\n(除特别注明外，金额单位为人民币千元)\n210\n四 合并财务报表项目附注(续)\n"
                  "(26) 使用权受到限制的资产\n\n于 2025 年 12 月 31 日及 2024 年 12 月 31 日，使用权受到限制的资产情况\n如下：\n\n"
                  "  2025 年 12 月 31 日  2024 年 12 月 31 日\n\n 其他非流动资产(a) 23,690,000  22,592,792\n"
                  " 货币资金(b) 16,658,157  84,222,595\n 其他资产(c) 6,236,358  7,267,056\n  46,584,515  114,082,443\n\n"
                  "(a) 其他非流动资产主要为取得时期限在一年以上到期的固定收益类产品，用于\n质押开立银行承兑汇票。\n\n"
                  "(b) 货币资金主要包括三个月以上一年内到期的定期存款及存放同业款项、其他\n货币资金及存放中央银行法定准备金。\n\n"
                  "(c) 其他资产主要包括应收账款、应收票据、固定资产等，用于抵押或质押取得银行借款及开立银行承兑汇票。\n\n"
                  "(27) 短期借款\n\n  2025 年 12 月 31 日  2024 年 12 月 31 日\n 信用借款 19,672,362  6,396,560\n")
    TASK = dict(code="000333", name="美的集团", year=2025, report_date="2025-12-31", notes_payable=27_121_881_000.0,
                balance={"MONETARYFUNDS": 132_000_000_000.0})

    def test_lettered_footnotes_page_unit_and_unlabeled_total(self):
        self.assertIsNone(rc.find_section(self.MIDEA_2025))                  # v1 认不出没有「所有权」的标题
        body, source, unit = rc.find_section_v2(self.MIDEA_2025)
        self.assertEqual((source, unit), ("note", 1e3))
        self.assertNotIn("信用借款", body)                                   # 段止于「(27)」
        r = rc.parse_section_v2(body, unit, self.TASK["balance"])
        self.assertEqual(r["status"], "ok")
        rows = {x["label"]: x for x in r["rows"]}
        self.assertAlmostEqual(rows["其他非流动资产"]["value"], 23_690_000_000.0)
        self.assertIn("承兑汇票", rows["其他非流动资产"]["reason"])
        self.assertNotIn("承兑", rows["货币资金"]["reason"])                  # 字母脚注逐行对应，不串用
        c = rc.classify(r["rows"], self.TASK, {("000333", 2025, "OTHER_NONCURRENT_ASSET"): 25_000_000_000.0})
        self.assertAlmostEqual(c["counted"], 23_690_000_000.0)

    def _run(self, text: str, parser: str) -> dict:
        import gzip
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            old = rc.cn.CACHE
            rc.cn.CACHE = Path(folder)
            try:
                (Path(folder) / "000333").mkdir()
                (Path(folder) / "000333" / "2025.txt.gz").write_bytes(gzip.compress(("的" * 500 + "\n" + text).encode()))
                row = rc.parse_task(self.TASK, dict(status="ok", url="u", title="t"), {}, {}, parser)
            finally:
                rc.cn.CACHE = old
        row.pop("extracted_at_utc")
        return row

    def test_v1_unchanged_and_v2_only_where_v1_fails(self):
        v1_text = ("25、所有权或使用权受到限制的资产\n单位：元 币种：人民币\n项目 期末账面价值 受限原因\n"
                   "货币资金 1,096,591,549.00 质押开具银行承兑汇票\n固定资产 200,000,000.00 抵押借款\n合计 1,296,591,549.00 /\n")
        self.assertEqual(self._run(v1_text, "v1"), self._run(v1_text, "v2"))
        self.assertEqual(self._run(v1_text, "v1")["status"], "ok")
        v1, v2 = self._run(self.MIDEA_2025, "v1"), self._run(self.MIDEA_2025, "v2")
        self.assertNotEqual(v1["status"], "ok")
        self.assertEqual(v2["status"], "ok")
        self.assertTrue(v2["source"].startswith("v2:"))
        self.assertAlmostEqual(float(v2["restricted_total"]), 46_584_515_000.0)

    def test_integer_table_with_numbered_footnotes(self):
        text = ("财务报表附注(续)\n2016年12月31日\n人民币千元\n五、 合并财务报表主要项目注释(续)\n"
                "55. 所有权或使用权受到限制的资产\n\n 2016年 2015年\n\n货币资金 1,238,540 1,225,984 注1\n应收票据 - 106,892\n"
                "固定资产 55,227 - 注2\n\n 1,293,767 1,332,876\n\n注1： 于2016年12月31日，本集团所有权受到限制的货币资金包括承兑汇票保证"
                "金人民币37,096千元、存款准备金人民币826,211千元。\n注2： 固定资产用于取得银行借款抵押。\n56. 外币货币性项目\n")
        body, _, unit = rc.find_section_v2(text)
        self.assertEqual(unit, 1e3)
        r = rc.parse_section_v2(body, unit, {})
        self.assertEqual(r["status"], "ok")
        rows = {x["label"]: x for x in r["rows"]}
        self.assertAlmostEqual(rows["货币资金"]["value"], 1_238_540_000.0)
        self.assertIn("承兑汇票", rows["货币资金"]["reason"])                 # 「注1」在整数表里不被当成金额
        self.assertIn("借款", rows["固定资产"]["reason"])

    def test_prose_amounts_and_parent_without_amount(self):
        # 说明里写明金额的「银行承兑汇票保证金 41,849,177.08 元」不是表格行（金石资源 2025）
        body = ("\n单位：元 币种：人民币\n项目 期末账面价值 受限类型 受限情况\n货币资金 57,843,683.87 质押 均系其他货币资金，包括：银行承"
                "兑汇票保证金\n41,849,177.08 元、环境治理恢复基金\n15,452,548.58 元、借款保证金\n541,958.21 元。\n"
                "固定资产 148,721,036.41 抵押 为银行融资提供抵押担保。\n合计 206,564,720.28 / /\n")
        r = rc.parse_section_v2(body, None, {})
        self.assertEqual(r["status"], "ok")
        self.assertEqual([x["label"] for x in r["rows"]], ["货币资金", "固定资产"])
        # 母项「货币资金」本身没有金额、明细列在「其中：」（美的 2019）
        body = ("\n  期末数  期初数\n 货币资金\n 其中：银行存款(附注四(1)) 39,491,676  5,686,629\n"
                " 其他货币资金(附注四(1)) 153,022  123,197\n存放中央银行法定准备金\n(附注四(1)) 433,149  1,126,172\n"
                " 存放同业款项(附注四(1)) -   3,000,000\n  40,077,847  9,935,998\n")
        r = rc.parse_section_v2(body, 1e3, {})
        self.assertEqual(r["status"], "ok")
        self.assertAlmostEqual(r["total"], 40_077_847_000.0)
        self.assertEqual(sorted(x["label"] for x in r["rows"]), ["其他货币资金", "货币资金", "银行存款"])
        reserve = next(x for x in r["rows"] if x["label"] == "货币资金")
        self.assertIn("法定准备金", reserve["reason"])                      # 分项行名并入原因，供准备金判定

    def test_chinese_numeral_heading_stops_at_next_note(self):
        text = ("五、合并财务报表项目注释\n（一）货币资金\n项目 期末余额\n（二十六）使用权受到限制的资产\n单位：元\n项目 期末账面价值 受限原因\n"
                "货币资金 1,000.00 银行承兑汇票保证金\n合计 1,000.00\n（二十七）短期借款\n单位：元\n项目 期末余额\n信用借款 5,000.00\n")
        body, _, unit = rc.find_section_v2(text)
        self.assertEqual(unit, 1.0)
        self.assertNotIn("信用借款", body)

    def test_table_without_any_total_needs_unit_and_balance(self):
        body = "\n单位：元\n项目 期末账面价值 受限原因\n货币资金 3,876,262.67 保函保证金\n"
        self.assertEqual(rc.parse_section_v2(body, None, {"MONETARYFUNDS": 10_000_000.0})["status"], "ok")
        self.assertEqual(rc.parse_section_v2(body, None, {"MONETARYFUNDS": 1_000_000.0})["status"], "exceeds_balance")
        bare = "\n项目 期末账面价值 受限原因\n货币资金 3,876,262.67 保函保证金\n"
        self.assertEqual(rc.parse_section_v2(bare, None, {"MONETARYFUNDS": 10_000_000.0})["status"], "no_total")


class EngineDeductionTest(unittest.TestCase):
    @staticmethod
    def parts(notes_payable: float) -> dict:
        bal = dict(TOTAL_EQUITY="1000", TOTAL_PARENT_EQUITY="1000", MONETARYFUNDS="900", NOTE_PAYABLE=str(notes_payable),
                   TOTAL_ASSETS="3000", NOTICE_DATE="2026-04-20")
        inc = dict(TOTAL_OPERATE_INCOME="1000", TOTAL_PROFIT="100", INCOME_TAX="25", FINANCE_EXPENSE="-20",
                   FE_INTEREST_INCOME="18", NOTICE_DATE="2026-04-20")
        return dict(balance=bal, income=inc)

    def test_deduction_capped_by_notes_payable_and_interest_added(self):
        base = roic_inputs._year_from_parts("000001", "2025-12-31", self.parts(300), False, 0.1, "nonop", 0.0)
        cut = roic_inputs._year_from_parts("000001", "2025-12-31", self.parts(300), False, 0.1, "nonop", 0.0, 500.0)
        self.assertAlmostEqual(cut.restricted_cash, 300.0)
        self.assertAlmostEqual(base.excess_cash - cut.excess_cash, 300.0)
        self.assertAlmostEqual(cut.restricted_interest, 300.0 * 18 / 900)
        self.assertAlmostEqual(cut.ebit - base.ebit, 6.0)

    def test_no_notes_payable_no_deduction(self):
        cut = roic_inputs._year_from_parts("000001", "2025-12-31", self.parts(0), False, 0.1, "nonop", 0.0, 500.0)
        self.assertEqual(cut.restricted_cash, 0.0)

    def test_statutory_reserve_out_of_excess_cash_not_working_capital(self):
        base = roic_inputs._year_from_parts("000001", "2025-12-31", self.parts(0), False, 0.1, "nonop", 0.0, 0.0, True)
        cut = roic_inputs._year_from_parts("000001", "2025-12-31", self.parts(0), False, 0.1, "nonop", 0.0, 0.0, True, 50.0)
        self.assertAlmostEqual(cut.statutory_reserve, 50.0)
        self.assertAlmostEqual(base.excess_cash - cut.excess_cash, 50.0)
        self.assertAlmostEqual(cut.ebit - base.ebit, 50.0 * 18 / 900)
        self.assertEqual(cut.working_capital, base.working_capital)


if __name__ == "__main__":
    unittest.main()
