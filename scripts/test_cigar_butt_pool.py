#!/usr/bin/env python3
"""工作流程 §6.10 烟蒂池：四类烟蒂价值、类别顺序、股东回报验证与池表校验。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_cigar_butt_pool as build  # noqa: E402
import screen_cigar_butts as screen  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
