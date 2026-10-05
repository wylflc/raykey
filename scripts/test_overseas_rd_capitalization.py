#!/usr/bin/env python3
"""§6.8 海外研发费用资本化（OI-255）的回归测试。

Run: ``python3 scripts/test_overseas_rd_capitalization.py``

锁住：12 月年结的财年编号即年份（A 股逐位不变）；非 12 月年结按期末先后编号；资本化在两种年结下同额；
年报维护行由 SEC 同期研发补入；港股 F10 已有研发行时补充表不得再给；资本化后保留年报行另挂的股数等属性，
TTM 因子按资本化前的年报 NOPAT 计。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_overseas_roic_bands as bands  # noqa: E402
import fetch_overseas_statements as statements  # noqa: E402
import roic_inputs  # noqa: E402
from test_overseas_caliber import model_years  # noqa: E402


def years_at(periods):
    out = {}
    for i, period in enumerate(periods):
        y = roic_inputs.RoicYear(period=period, notice_date=period)
        y.revenue, y.ebit, y.nopat, y.tax_rate = 1000.0 + 100 * i, 150.0, 120.0, 0.2
        y.invested_capital, y.capex, y.dep_amort = 600.0, 60.0, 40.0
        out[period] = y
    return out


class FiscalLabelTest(unittest.TestCase):
    def test_december_year_ends_are_calendar_years(self):
        self.assertEqual(roic_inputs.fiscal_labels(["2019-12-31", "2017-12-31"]), {"2017-12-31": 2017, "2019-12-31": 2019})

    def test_non_december_year_ends_follow_sequence(self):
        self.assertEqual(roic_inputs.fiscal_labels(["2023-12-01", "2024-11-29", "2025-11-28"]),
                         {"2023-12-01": 2023, "2024-11-29": 2024, "2025-11-28": 2025})
        self.assertEqual(roic_inputs.fiscal_labels(["2024-01-28", "2025-01-26", "2026-01-25"]),
                         {"2024-01-28": 2023, "2025-01-26": 2024, "2026-01-25": 2025})
        # 52／53 周年结跨 7 月 1 日：仍按先后各占一年，不撞号
        self.assertEqual(roic_inputs.fiscal_labels(["2016-07-01", "2017-06-30", "2018-06-29"]),
                         {"2016-07-01": 2016, "2017-06-30": 2017, "2018-06-29": 2018})


class CapitalizeTest(unittest.TestCase):
    def test_same_adjustment_for_both_year_end_conventions(self):
        dec = [f"{y}-12-31" for y in range(2015, 2026)]
        nov = [f"{y}-11-28" for y in range(2015, 2026)]
        spend = [50.0 + 5 * i for i in range(len(dec))]
        a = roic_inputs.capitalize_rd(years_at(dec), dict(zip(dec, spend)), 3)
        b = roic_inputs.capitalize_rd(years_at(nov), dict(zip(nov, spend)), 3)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        for pd, pn in zip(dec, nov):
            ya, yb = a[0][pd], b[0][pn]
            self.assertAlmostEqual(ya.nopat, yb.nopat)
            self.assertAlmostEqual(ya.invested_capital, yb.invested_capital)
            self.assertAlmostEqual(ya.capex, yb.capex)
        # 第 t 年：研发资产 Σ R&D_{t−k}·(N−k)/N，NOPAT 加回 (研发 − 摊销) × (1 − t)
        t = a[0]["2025-12-31"]
        r = spend[-4:]
        self.assertAlmostEqual(t.invested_capital, 600.0 + r[3] + r[2] * 2 / 3 + r[1] / 3)
        self.assertAlmostEqual(t.nopat, 120.0 + (r[3] - sum(r[:3]) / 3) * 0.8)


class FetchTest(unittest.TestCase):
    def build(self, period, rd=None):
        return statements._build_row("US", "X", "X", period, period, "USD", 1000.0, 100.0, 95.0, 20.0, 5.0, 400.0, 400.0,
                                     0.0, 100.0, 500.0, 60.0, 40.0, 110.0, 50.0, {}, "test", 0.21, rd=rd)

    def test_override_rd_filled_from_sec(self):
        extracted = [dict(self.build("2025-05-31", rd=10.0), period_type="annual")]
        override = dict(self.build("2025-05-31"), period_type="annual")
        self.assertIsNone(override["rd_expense"])
        self.assertEqual(statements.fill_override_rd([override], extracted), ["2025-05-31"])
        self.assertEqual(override["rd_expense"], 10.0)
        self.assertIn("rd_expense=SEC companyfacts", override["tags_used"])

    def test_hong_kong_double_source_is_rejected(self):
        table = [dict(DATE_TYPE_CODE="001", REPORT_DATE="2025-12-31 00:00:00", STD_ITEM_NAME=name, AMOUNT=value)
                 for name, value in (("营业额", 1000.0), ("除税前溢利", 120.0), ("经营溢利", 110.0), ("研发费用", 30.0),
                                     ("总权益", 500.0), ("股东权益", 500.0))]
        supplements = {"rd_expense": {"2025-12-31": dict(period_kind="annual", value=30.0, _used=False)}}
        with self.assertRaises(statements.SupplementError):
            statements.hk_extract("03888", "X", {"income": table, "balance": table}, 100.0, supplements=supplements)
        rows = statements.hk_extract("03888", "X", {"income": table, "balance": table}, 100.0)
        self.assertEqual(rows[0]["rd_expense"], 30.0)


class BuildTest(unittest.TestCase):
    def test_attributes_kept_and_ttm_factor_uses_raw_nopat(self):
        years = model_years()
        rd = {y.period: 30.0 + 2 * i for i, y in enumerate(years)}
        adjusted, raw, note = bands.capitalized_years(years, rd, "信息传输、软件和信息技术服务业-软件和信息技术服务业", "2026-10-05")
        self.assertIn("研发资本化 3 年", note)
        self.assertEqual([y.shares for y in adjusted], [y.shares for y in years])
        self.assertEqual([y.dividends_paid for y in adjusted], [y.dividends_paid for y in years])
        self.assertEqual(raw["2025-12-31"], years[-1].nopat)
        current = model_years()[-1]
        current.period, current.nopat = "2026-06-30", years[-1].nopat * 1.1
        result = bands.value_company("T", "L2", adjusted, {}, current, raw_nopat=raw, rd_note=note)
        self.assertEqual(result["status"], "ok")
        self.assertAlmostEqual(result["f_ttm"], 1.1)
        self.assertEqual(bands.capitalized_years(years, None, None, "2026-10-05"), (years, None, ""))


if __name__ == "__main__":
    unittest.main()
