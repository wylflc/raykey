#!/usr/bin/env python3
"""§6.5.1 第 3 条（OI-264）：负税率或低于前三年观测税率中位 10pp 以上的年份改按该中位，高于中位的不调。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from roic_inputs import RoicYear, correct_tax_anomalies  # noqa: E402


def year(period: str, raw: float | None, ebit: float = 100.0, observed: bool = True) -> RoicYear:
    rate = 0.25 if raw is None else min(max(raw, 0.0), 0.40)
    return RoicYear(period=period, notice_date=period, ebit=ebit, tax_rate=rate, tax_rate_raw=raw,
                    tax_rate_observed=observed and raw is not None, nopat=ebit * (1 - rate))


class TaxAnomalyTest(unittest.TestCase):
    def test_negative_rate_uses_prior_median(self) -> None:
        ys = {p: year(p, r) for p, r in (("2022-12-31", 0.15), ("2023-12-31", 0.16), ("2024-12-31", 0.14), ("2025-12-31", -0.20))}
        self.assertEqual(correct_tax_anomalies(ys), 1)            # 盐湖 2025：确认递延所得税使税率为负
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.15)
        self.assertAlmostEqual(ys["2025-12-31"].nopat, 85.0)

    def test_drop_beyond_gap_is_corrected_but_rise_is_not(self) -> None:
        ys = {p: year(p, r) for p, r in (("2022-12-31", 0.25), ("2023-12-31", 0.25), ("2024-12-31", 0.12), ("2025-12-31", 0.35))}
        self.assertEqual(correct_tax_anomalies(ys), 1)
        self.assertAlmostEqual(ys["2024-12-31"].tax_rate, 0.25)   # 低 13pp：改
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.35)   # 高于中位：不调（优惠取消多为持续变化）

    def test_small_drop_and_unobserved_years_untouched(self) -> None:
        ys = {p: year(p, r) for p, r in (("2023-12-31", 0.25), ("2024-12-31", 0.17), ("2025-12-31", None))}
        self.assertEqual(correct_tax_anomalies(ys), 0)
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.25)

    def test_without_history_only_negative_rates_change(self) -> None:
        ys = {"2025-12-31": year("2025-12-31", 0.05)}
        self.assertEqual(correct_tax_anomalies(ys), 0)            # 结构性低税率不按法定税率比较
        ys = {"2025-12-31": year("2025-12-31", -0.10)}
        self.assertEqual(correct_tax_anomalies(ys), 1)
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.25)

    def test_permanent_step_down_heals_within_two_years(self) -> None:
        rates = (("2020-12-31", 0.25), ("2021-12-31", 0.25), ("2022-12-31", 0.25), ("2023-12-31", 0.12),
                 ("2024-12-31", 0.12), ("2025-12-31", 0.12))
        ys = {p: year(p, r) for p, r in rates}
        self.assertEqual(correct_tax_anomalies(ys), 2)            # 取得优惠：头两年按中位，其后随中位回落、不连锁
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.12)


if __name__ == "__main__":
    unittest.main()
