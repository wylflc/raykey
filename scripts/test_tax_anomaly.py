#!/usr/bin/env python3
"""§6.5.1 第 3 条（OI-264，用户 2026-10-06 裁定只纠负税率）：负税率年份改按前三年观测税率（非负原值）中位，其余不动。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from roic_inputs import RoicYear, correct_tax_anomalies  # noqa: E402


def year(period: str, raw: float | None, ebit: float = 100.0) -> RoicYear:
    rate = 0.25 if raw is None else min(max(raw, 0.0), 0.40)
    return RoicYear(period=period, notice_date=period, ebit=ebit, tax_rate=rate, tax_rate_raw=raw,
                    tax_rate_observed=raw is not None, nopat=ebit * (1 - rate))


class TaxAnomalyTest(unittest.TestCase):
    def test_negative_rate_uses_prior_median(self) -> None:
        ys = {p: year(p, r) for p, r in (("2022-12-31", 0.08), ("2023-12-31", 0.12), ("2024-12-31", 0.15), ("2025-12-31", -0.24))}
        self.assertEqual(correct_tax_anomalies(ys), 1)            # 盐湖 2025：确认递延所得税使税率为负
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.12)
        self.assertAlmostEqual(ys["2025-12-31"].nopat, 88.0)

    def test_low_positive_rates_after_high_years_untouched(self) -> None:
        rates = (("2018-12-31", 0.40), ("2019-12-31", 0.40), ("2020-12-31", 0.40), ("2021-12-31", 0.40),
                 ("2022-12-31", 0.19), ("2023-12-31", 0.18))
        ys = {p: year(p, r) for p, r in rates}                    # 神火：此前子公司亏损不可抵扣使税率偏高，其后正常年份不得改高
        self.assertEqual(correct_tax_anomalies(ys), 0)
        self.assertAlmostEqual(ys["2023-12-31"].tax_rate, 0.18)

    def test_prior_negative_years_excluded_from_reference(self) -> None:
        ys = {p: year(p, r) for p, r in (("2021-12-31", 0.07), ("2022-12-31", 0.07), ("2023-12-31", -0.06), ("2024-12-31", -0.01))}
        self.assertEqual(correct_tax_anomalies(ys), 2)            # 圣邦 2023–2024
        self.assertAlmostEqual(ys["2024-12-31"].tax_rate, 0.07)

    def test_without_history_negative_uses_statutory(self) -> None:
        ys = {"2025-12-31": year("2025-12-31", -0.10)}
        self.assertEqual(correct_tax_anomalies(ys), 1)
        self.assertAlmostEqual(ys["2025-12-31"].tax_rate, 0.25)
        ys = {"2025-12-31": year("2025-12-31", 0.05)}
        self.assertEqual(correct_tax_anomalies(ys), 0)


if __name__ == "__main__":
    unittest.main()
