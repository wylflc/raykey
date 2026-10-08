#!/usr/bin/env python3
"""工作流程 §6.10 烟蒂池：四类烟蒂价值、类别顺序、股东回报验证、池表校验，及第 5 条烟蒂股持仓的扫描与跟踪。"""
import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_cigar_butt_pool as build  # noqa: E402
import screen_cigar_butts as screen  # noqa: E402
import screen_daily_volume_price_signals as scan  # noqa: E402
import track_holdings_daily as tracker  # noqa: E402
from test_daily_execution_plan import hold, row  # noqa: E402

BALANCE = dict(MONETARYFUNDS=100, TRADE_FINASSET=20, NOTE_RECE=10, FINANCE_RECE=0, ACCOUNTS_RECE=40, INVENTORY=60,
               CONTRACT_ASSET=10, TOTAL_CURRENT_ASSETS=260, TOTAL_LIABILITIES=150, MINORITY_EQUITY=10,
               OTHER_EQUITY_TOOL=5, SHORT_LOAN=30, LONG_LOAN=20, LONG_EQUITY_INVEST=50, INVEST_REALESTATE=20,
               FIXED_ASSET=100, CIP=0, CREDITOR_INVEST=10, TOTAL_ASSETS=500)


class ValueTest(unittest.TestCase):
    def test_value_a_haircuts_and_claims(self):
        value, ncav = screen.value_a(BALANCE)
        # 其余流动资产 = 260 − (100+20+10+40+60+10) = 20
        expected = 100 + 0.9 * 20 + 0.9 * 10 + 0.75 * 40 + 0.5 * 60 + 0.5 * 10 + 0.25 * 20 - (150 + 10 + 5)
        self.assertAlmostEqual(value, expected)
        self.assertAlmostEqual(ncav, 260 - 165)

    def test_value_b_needs_five_positive_years_and_caps_net_cash(self):
        self.assertIsNone(screen.value_b(BALANCE, [5, 6, 7, 8], 9))
        self.assertIsNone(screen.value_b(BALANCE, [5, -1, 7, 8, 9], 9))
        net_cash = 100 + 20 - 50 - 5 - 10                      # 55，低于 NCAV 95
        self.assertAlmostEqual(screen.value_b(BALANCE, [5, 6, 7, 8, 9], 6), net_cash + 5 * 6)
        capped = dict(BALANCE, TOTAL_LIABILITIES=200)          # NCAV 45 < 净现金 55
        self.assertAlmostEqual(screen.value_b(capped, [5, 6, 7, 8, 9], 9), 45 + 5 * 7)

    def test_value_c_adds_noncurrent_at_haircuts(self):
        value_a, _ = screen.value_a(BALANCE)
        expected = value_a + 0.9 * 10 + 0.3 * 50 + 0.5 * 20 + 0.2 * 100
        self.assertAlmostEqual(screen.value_c(BALANCE, value_a), expected)

    def test_value_d_and_coe(self):
        self.assertAlmostEqual(screen.value_d_ps(20.0, [10.0, 9.0, 11.0], 11.0), 20.0 * (9 - 3) / 8)
        self.assertAlmostEqual(screen.value_d_ps(20.0, [15.0], 10.0), 20.0)       # 封顶 1 倍
        self.assertIsNone(screen.value_d_ps(20.0, [2.5], 11.0))
        self.assertEqual(screen.bank_coe("601398"), 10.0)
        self.assertEqual(screen.bank_coe("000001"), 11.0)
        self.assertEqual(screen.bank_coe("601838"), 11.5)

    def test_intermediary(self):
        self.assertFalse(screen.is_intermediary(BALANCE))
        self.assertTrue(screen.is_intermediary(dict(BALANCE, AGENT_TRADE_SECURITY=100)))


class RuleTest(unittest.TestCase):
    def test_type_order(self):
        self.assertEqual(screen.assign_type(dict(A=0.9, B=0.5, C=0.4)), "A")
        self.assertEqual(screen.assign_type(dict(A=1.2, B=0.95, C=0.4)), "B")
        self.assertEqual(screen.assign_type(dict(A=None, B=None, C=0.99)), "C")
        self.assertEqual(screen.assign_type(dict(A=1.5, B=None, C=1.01)), "")
        self.assertEqual(screen.assign_type(dict(D=0.7)), "D")

    def test_cash_verified(self):
        self.assertTrue(screen.cash_verified([3, 3, 0], [10, 10, 10]))
        self.assertFalse(screen.cash_verified([1, 1, 1], [10, 10, 10]))        # 3 < 20% × 30
        self.assertFalse(screen.cash_verified([10, 0, 0], [10, 10, 10]))       # 只有一年分红
        self.assertTrue(screen.cash_verified([1, 1, 0], [-5, -5, 1]))          # 三年亏损只看年数

    def test_cagr(self):
        self.assertAlmostEqual(screen.cagr_3y(8.0, 8.0), 0.0)
        self.assertEqual(screen.cagr_3y(-1.0, 5.0), -1.0)
        self.assertIsNone(screen.cagr_3y(5.0, 0.0))

    def test_periods(self):
        p = screen.periods("2026-06-30")
        self.assertEqual((p["fy"], p["prior"], p["three_years_ago"], p["ytd"]), (2025, "2025-06-30", "2023-06-30", True))
        self.assertEqual(p["annual"], [f"{y}-12-31" for y in range(2021, 2026)])
        self.assertFalse(screen.periods("2025-12-31")["ytd"])


class ValidateTest(unittest.TestCase):
    def row(self, **kw):
        base = {f: "" for f in screen.POOL_FIELDS}
        base.update(security_code="600001", security_name="甲", cb_type="B", status="candidate", pv_cb="0.9",
                    cash_verified="yes")
        base.update(kw)
        return base

    def test_candidate_threshold(self):
        self.assertEqual(build.validate([self.row()], {}), [])
        self.assertTrue(build.validate([self.row(pv_cb="1.2")], {}))

    def test_focus_requirements(self):
        registry = {"iv:600001": dict(status="current", pv="0.85")}
        ok = self.row(status="focus", pv_cb="0.7", catalysts="股息率 5%", independent_review_id="iv:600001",
                      reviewed_at="2026-10-07")
        self.assertEqual(build.validate([ok], registry), [])
        self.assertTrue(build.validate([dict(ok, pv_cb="0.85")], registry))          # B 类重点级门槛 0.8
        self.assertTrue(build.validate([dict(ok, cash_verified="no")], registry))
        self.assertTrue(build.validate([dict(ok, independent_review_id="")], registry))
        self.assertEqual(build.validate([dict(ok, buy_eligible="yes")], registry), [])
        self.assertTrue(build.validate([dict(ok, buy_eligible="yes")], {"iv:600001": dict(status="current", pv="0.95")}))

    def test_reviewed_value_for_c_and_d(self):
        registry = {"iv:600001": dict(status="current", pv="0.85")}
        bank = self.row(cb_type="D", status="focus", pv_cb="0.6", catalysts="股息率 5%", independent_review_id="iv:600001",
                        reviewed_at="2026-10-07")
        self.assertTrue(build.validate([bank], registry))                               # 缺复核值
        ok = dict(bank, v_cb_reviewed_yi="100", pv_cb_reviewed="0.7")
        self.assertEqual(build.validate([ok], registry), [])
        self.assertTrue(build.validate([dict(ok, pv_cb_reviewed="0.8")], registry))     # 按复核值判门槛 0.75

    def test_rejected_needs_reason(self):
        self.assertTrue(build.validate([self.row(status="rejected", reviewed_at="2026-10-07")], {}))


CB = dict(security_code="600987", security_name="航民股份", cb_type="B", status="watch", price="6.28",
          market_cap_yi="64.11", v_cb_yi="69.9", v_cb_reviewed_yi="65.66")


class PoolLookupTest(unittest.TestCase):
    def test_pv_cb_at_close_prefers_reviewed_value(self):
        self.assertAlmostEqual(screen.pv_cb_at(CB, 6.28), 64.11 / 65.66)
        self.assertAlmostEqual(screen.pv_cb_at(CB, 7.0), 64.11 * 7.0 / 6.28 / 65.66)
        self.assertAlmostEqual(screen.pv_cb_at(dict(CB, v_cb_reviewed_yi=""), 6.28), 64.11 / 69.9)
        self.assertIsNone(screen.pv_cb_at(CB, None))
        self.assertIsNone(screen.pv_cb_at(dict(CB, v_cb_yi="", v_cb_reviewed_yi=""), 6.28))

    def test_rows_any_status_but_not_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pool.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=screen.POOL_FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows([CB, dict(CB, security_code="601997", status="rejected"), dict(CB, security_code="600036")])
            found = screen.cigar_butt_rows({"600987", "601997", "600036", "000651"}, {"600036"}, path)
            self.assertEqual(sorted(found), ["600987", "601997"])
            self.assertEqual(sorted(screen.cigar_butt_rows({"600036"}, None, path)), ["600036"])
            with self.assertRaises(ValueError):
                screen.cigar_butt_rows({"600987"}, set(), Path(tmp) / "missing.csv")

    def test_held_candidate_kept_as_exited(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pool.csv"
            candidate = {f: "" for f in screen.POOL_FIELDS} | dict(security_code="600987", cb_type="B",
                                                                    status="candidate", pv_cb="0.95")
            for held, expected in ((set(), []), ({"600987"}, ["exited"])):
                screen._write(path, [candidate], screen.POOL_FIELDS)
                with patch.object(screen, "POOL", path):
                    stats = screen.update_pool([], "2026-10-31", held)
                self.assertEqual([r["status"] for r in screen._read(path)], expected)
                self.assertEqual(stats["removed"], 0 if held else 1)


class HoldingExemptionTest(unittest.TestCase):
    """§6.10 第 5 条：池表在册且不在 worth_attention 的持仓不做出名单、涨幅减持与换仓卖出源；股债总仓位上限照常。"""

    def setUp(self) -> None:
        scan.CLOSE_SERIES.clear()
        self.nav = 3_000_000.0

    def plan(self, holdings, members, cigar, funds=0.0, rows=None, holding_rows=None, **kw):
        rows = rows if rows is not None else [row("000003", "C", close=100.0, ma20=95.0, ma60=90.0, pv=0.5)]
        holding_rows = holding_rows if holding_rows is not None else [
            row("600987", "航民股份", close=250.0, ma20=200.0, ma60=180.0, pv=None)]
        return scan.section93_execution_plan(rows, self.nav, funds, holdings, set(), set(), members, {}, holding_rows,
                                             sell_counters={}, cigar=cigar, **kw)

    def test_no_exit_gain_trim_or_swap_source(self) -> None:
        # 涨幅 150%、收盘为 MA20 的 1.25 倍：常规持仓会出名单或涨幅减持、并可让位；烟蒂股都不做
        res = self.plan({"600987": hold("航民股份", 4000, 100.0, None)}, {"000003"}, {"600987": CB})
        self.assertEqual(res["sells"], [])
        self.assertIn("无满足让位条件的持仓", res["swap_stop_reason"])
        self.assertEqual([(n, s) for n, _pv, s in res["cigar_held"]], [("航民股份", "watch")])
        self.assertAlmostEqual(res["cigar_held"][0][1], 64.11 * 250.0 / 6.28 / 65.66)
        # 对照：不在池表即出名单；进入 worth_attention 即按 §9.3 涨幅减持
        res = self.plan({"600987": hold("航民股份", 4000, 100.0, None)}, {"000003"}, {})
        self.assertEqual([s["rule"] for s in res["sells"]], ["出名单"])
        res = self.plan({"600987": hold("航民股份", 4000, 100.0, None)}, {"000003", "600987"}, {"600987": CB})
        self.assertEqual([s["rule"] for s in res["sells"]], ["涨幅减持"])
        self.assertEqual(res["cigar_held"], [])

    def test_equity_bond_cap_still_reduces_cigar_holding(self) -> None:
        # 净资产 200 万：烟蒂股 200 万 + 常规 100 万 = 150%，上限 100% → 两只按 1/3 比例减仓
        self.nav = 2_000_000.0
        rows = [row("000001", "A", close=50.0, ma20=51.0, ma60=40.0, pv=2.5)]
        holding_rows = [row("600987", "航民股份", close=100.0, ma20=101.0, ma60=90.0, pv=None)]
        holdings = {"000001": hold("A", 20000, None, None), "600987": hold("航民股份", 20000, 100.0, None)}
        res = self.plan(holdings, {"000001"}, {"600987": CB}, rows=rows, holding_rows=holding_rows,
                        exposure_cap=1.0, cap_cash=-1_000_000.0)
        self.assertEqual(res["eb_sells"], ["000001", "600987"])
        self.assertEqual({s["security_code"]: s["sell_shares"] for s in res["sells"]}, {"000001": 6700, "600987": 6700})

    def test_tracker_marks_user_decided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            holdings_file = Path(tmp) / "holdings.csv"
            with holdings_file.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["security_code", "security_name", "current_shares", "cost_basis",
                                                   "entry_stop_price"])
                w.writeheader()
                w.writerow(dict(security_code="600987", security_name="航民股份", current_shares=4000, cost_basis=5.0))
            for close, action in ((12.0, "烟蒂股（用户决定）"), (None, "数据缺失")):
                rows = tracker.track(holdings_file, Path(tmp) / "pool.csv", date(2026, 10, 8), "", 1,
                                     snapshots={"600987": dict(close=close, ma20=10.0, ma60=9.0)},
                                     hold_bands={}, candidate_bands={}, members=set(), cigar={"600987": CB})
                self.assertEqual(rows[0]["action"], action)
                self.assertEqual(rows[0]["pv_cb"], f"{64.11 * 12.0 / 6.28 / 65.66:.3f}" if close else "")
                for text in ("逐日清仓", "涨幅减持一档", "满足换仓让位条件", "持仓均价未填"):
                    self.assertNotIn(text, rows[0]["note"])
                self.assertIn("烟蒂股（§6.10 第 5 条）", rows[0]["note"])


if __name__ == "__main__":
    unittest.main()
