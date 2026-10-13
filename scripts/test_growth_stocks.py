#!/usr/bin/env python3
"""§9.3.6 成长股模块：登记与重点复核记录的判定，及执行清单中的成长股卖出、复核闸门与总额上限。"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import growth_stocks as gs
import screen_daily_volume_price_signals as scan
from test_daily_execution_plan import hold, row


class ReviewStatusTest(unittest.TestCase):
    band = {"available_at": "2026-08-22", "forecast_notice_date": ""}
    register = {"registered_at": "2026-10-01"}

    def test_missing_record(self) -> None:
        self.assertEqual(gs.review_status({}, self.band, self.register)[0], "missing")
        self.assertEqual(gs.review_status({"growth_reviewed_at": "2026-10-02"}, self.band, self.register)[0], "missing")

    def test_pass_and_fail_are_valid_until_newer_evidence(self) -> None:
        passed = {"growth_reviewed_at": "2026-10-02", "growth_review_conclusion": gs.REVIEW_PASS}
        self.assertEqual(gs.review_status(passed, self.band, self.register)[0], "pass")
        failed = dict(passed, growth_review_conclusion=gs.REVIEW_FAIL)
        self.assertEqual(gs.review_status(failed, self.band, self.register)[0], "fail")

    def test_new_report_forecast_or_register_change_makes_record_stale(self) -> None:
        passed = {"growth_reviewed_at": "2026-10-02", "growth_review_conclusion": gs.REVIEW_PASS}
        for band, register in (({"available_at": "2026-10-28"}, self.register),
                               ({"available_at": "2026-08-22", "forecast_notice_date": "2026-10-10"}, self.register),
                               (self.band, {"registered_at": "2026-10-05"})):
            status, why = gs.review_status(passed, band, register)
            self.assertEqual(status, "stale")
            self.assertIn("记录失效", why)

    def test_report_check_due_after_band_absorbs_newer_report(self) -> None:
        """§9.3.6 第 6 条：带的定期报告晚于登记日与上次核对日的较晚者才待核对；预告不算。"""
        self.assertIsNone(gs.report_check_due(self.register, self.band))
        self.assertIsNone(gs.report_check_due(self.register, {"available_at": "2026-08-22", "forecast_notice_date": "2026-10-09"}))
        self.assertIn("2026-10-24", gs.report_check_due(self.register, {"available_at": "2026-10-24"}))
        checked = dict(self.register, falsifier_checked_at="2026-10-24")
        self.assertIsNone(gs.report_check_due(checked, {"available_at": "2026-10-24"}))
        self.assertIsNotNone(gs.report_check_due(checked, {"available_at": "2027-03-28"}))

    def test_prereview_only_near_buy_line_without_valid_pass(self) -> None:
        state = gs.GrowthState(growth={"A", "B", "C"}, report_checks={"A": "x", "B": "x"},
                               reviews={"A": ("missing", ""), "B": ("pass", ""), "C": ("missing", "")})
        line = 1.0
        self.assertTrue(gs.prereview_needed(state, "A", line * gs.PREREVIEW_PV_MULTIPLE, line))
        self.assertFalse(gs.prereview_needed(state, "A", line * gs.PREREVIEW_PV_MULTIPLE + 0.001, line))
        self.assertFalse(gs.prereview_needed(state, "B", 0.9, line))    # 已有有效通过记录
        self.assertFalse(gs.prereview_needed(state, "C", 0.9, line))    # 当晚无新报告待核对

    def test_record_check_writes_only_the_two_columns_and_keeps_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            business, log = Path(tmp) / "business.csv", Path(tmp) / "log.csv"
            head = "security_code,security_name,derived_class,falsifier,registered_at\r\n"
            body = '688278,特宝生物,结构成长型,"营收年增<10%,连续两年",2026-10-01\r\n600519,贵州茅台,稳定型,x,2026-10-01\r\n'
            business.write_bytes((head + body).encode("utf-8"))
            row = gs.record_check("688278", "2026-10-24", "三季报营收 +21%，未触发", business=business, log_path=log)
            self.assertEqual(row["falsifier_checked_at"], "2026-10-24")
            self.assertEqual(business.read_bytes().decode("utf-8"),
                             "security_code,security_name,derived_class,falsifier,registered_at,falsifier_checked_at,falsifier_check_note\r\n"
                             '688278,特宝生物,结构成长型,"营收年增<10%,连续两年",2026-10-01,2026-10-24,三季报营收 +21%，未触发\r\n'
                             "600519,贵州茅台,稳定型,x,2026-10-01,,\r\n")
            self.assertIn("growth_falsifier_check:688278:2026-10-24", log.read_text(encoding="utf-8"))
            state = gs.load_growth_state(business, None, {"688278": {"available_at": "2026-10-24"}})
            self.assertEqual(state.report_checks, {})
            for code, day in (("600519", "2026-10-24"), ("688278", "2026-10-20"), ("000001", "2026-10-24")):
                with self.assertRaises(ValueError):
                    gs.record_check(code, day, "x", business=business, log_path=log)

    def test_load_state_reads_register_and_dossiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            business, dossiers = Path(tmp) / "business.csv", Path(tmp) / "dossiers.csv"
            with business.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["security_code", "derived_class", "replicability", "replicability_confidence",
                                                   "rejudged_from", "registered_at"])
                w.writeheader()
                w.writerows([dict(security_code="300308", derived_class="结构成长型", replicability="难复制",
                                  replicability_confidence="高", registered_at="2026-10-01"),
                             dict(security_code="002463", derived_class="结构成长型", replicability="难复制",
                                  replicability_confidence="低", registered_at="2026-10-01"),
                             dict(security_code="600183", derived_class="可复制成长型", replicability="易复制",
                                  rejudged_from="结构成长型", registered_at="2026-10-01"),
                             dict(security_code="600600", derived_class="稳定型", replicability="难复制", registered_at="2026-10-01")])
            with dossiers.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["security_code", "growth_reviewed_at", "growth_review_conclusion"])
                w.writeheader()
                w.writerow(dict(security_code="300308", growth_reviewed_at="2026-10-02", growth_review_conclusion="通过"))
            state = gs.load_growth_state(business, dossiers, {"300308": {"available_at": "2026-08-22"}})
        self.assertEqual(state.growth, {"300308", "002463"})
        self.assertEqual(state.exiting, {"600183"})
        self.assertEqual(state.low_confidence, {"002463"})
        self.assertTrue(state.passed("300308"))
        self.assertTrue(state.gated("002463"))
        self.assertFalse(state.gated("600600"))


class GrowthPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        scan.CLOSE_SERIES.clear()
        self.nav = 3_000_000.0            # 一档 15 万；成长股总额上限 60 万

    def plan(self, rows, holdings, funds, growth, members=None):
        members = members if members is not None else {str(r["security_code"]) for r in rows}
        return scan.section93_execution_plan(rows, self.nav, funds, holdings, set(), set(), members, {}, None,
                                             sell_counters={}, growth=growth)

    def test_growth_holding_skips_gain_trim_and_trims_on_valuation(self) -> None:
        # 涨幅 150% 的成长股：持仓侧 P/V 1.5 不卖（不做涨幅减持）；P/V 2.1 减一档
        growth = gs.GrowthState(growth={"300001"}, reviews={"300001": ("pass", "")})
        for pv, expected in ((1.5, []), (2.1, ["成长股估值减持"])):
            rows = [row("300001", "G", close=250.0, ma20=240.0, ma60=200.0, pv=pv)]
            res = self.plan(rows, {"300001": hold("G", 4000, 100.0, None)}, funds=0.0, growth=growth)
            self.assertEqual([s["rule"] for s in res["sells"]], expected)
        # 对照：非成长股同一输入按涨幅减持
        rows = [row("300001", "G", close=250.0, ma20=240.0, ma60=200.0, pv=1.5)]
        res = self.plan(rows, {"300001": hold("G", 4000, 100.0, None)}, funds=0.0, growth=gs.GrowthState())
        self.assertEqual([s["rule"] for s in res["sells"]], ["涨幅减持"])

    def test_growth_holding_is_not_swap_source(self) -> None:
        # 盈利 50%、收盘为 MA20 的 1.25 倍：常规持仓让位给未持仓候选 C，成长股持仓不让位
        rows = [row("300001", "G", close=150.0, ma20=120.0, ma60=100.0, pv=1.5),
                row("000003", "C", close=100.0, ma20=95.0, ma60=90.0, pv=0.5)]
        holdings = lambda: {"300001": hold("G", 2000, 100.0, None)}
        res = self.plan(rows, holdings(), funds=0.0, growth=gs.GrowthState())
        self.assertEqual([s["rule"] for s in res["sells"]], ["换仓"])
        res = self.plan(rows, holdings(), funds=0.0, growth=gs.GrowthState(growth={"300001"}, reviews={"300001": ("pass", "")}))
        self.assertEqual(res["sells"], [])
        self.assertIn("无满足让位条件的持仓", res["swap_stop_reason"])

    def test_unreviewed_growth_candidate_is_gated(self) -> None:
        rows = [row("300002", "N", close=100.0, ma20=95.0, ma60=90.0, pv=0.6),
                row("000003", "C", close=100.0, ma20=95.0, ma60=90.0, pv=0.8)]
        for status, bought in (("missing", ["000003"]), ("stale", ["000003"]), ("fail", ["000003"]), ("pass", ["300002", "000003"])):
            growth = gs.GrowthState(growth={"300002"}, reviews={"300002": (status, "")})
            res = self.plan(rows, {}, funds=1_000_000.0, growth=growth)
            self.assertEqual([p["security_code"] for p in res["plan"]], bought, status)
            self.assertEqual([r["security_code"] for r in res["growth_out"]], [] if status == "pass" else ["300002"])

    def test_growth_cap_limits_buys_to_room(self) -> None:
        # 成长股持仓 57 万 → 余量 3 万：第一只成长股只买 300 股，第二只被总额上限挡下；非成长股照买一档
        growth = gs.GrowthState(growth={"300001", "300002", "300003"},
                                reviews={c: ("pass", "") for c in ("300001", "300002", "300003")})
        rows = [row("300001", "G", close=190.0, ma20=180.0, ma60=150.0, pv=1.2),
                row("300002", "N1", close=100.0, ma20=95.0, ma60=90.0, pv=0.5),
                row("300003", "N2", close=100.0, ma20=95.0, ma60=90.0, pv=0.6),
                row("000004", "C", close=100.0, ma20=95.0, ma60=90.0, pv=0.7)]
        res = self.plan(rows, {"300001": hold("G", 3000, 180.0, None)}, funds=1_000_000.0, growth=growth)
        self.assertEqual([(p["security_code"], p["shares"]) for p in res["plan"]], [("300002", 300), ("000004", 1500)])
        self.assertEqual([c["security_code"] for c, _w in res["growth_capped"]], ["300003"])
        self.assertAlmostEqual(res["growth_value_after"], 570_000.0 + 30_000.0)

    def test_rejudged_holding_exits_and_is_not_bought(self) -> None:
        growth = gs.GrowthState(exiting={"300005"})
        rows = [row("300005", "X", close=100.0, ma20=95.0, ma60=90.0, pv=0.5)]
        res = self.plan(rows, {"300005": hold("X", 3000, 100.0, None)}, funds=1_000_000.0, growth=growth)
        self.assertEqual([(s["rule"], s["sell_shares"]) for s in res["sells"]], [("成长股改判", 1500)])
        self.assertEqual(res["plan"], [])
        # 清仓后不再持有：不再是成长股，按常规候选买入
        res = self.plan(rows, {}, funds=1_000_000.0, growth=growth)
        self.assertEqual([p["security_code"] for p in res["plan"]], ["300005"])


if __name__ == "__main__":
    unittest.main()
