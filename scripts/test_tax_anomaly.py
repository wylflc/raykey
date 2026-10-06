#!/usr/bin/env python3
"""§6.5.1 第 3 条（OI-264）：税率低于 −5% 的年份改按前三年观测税率（非负原值）中位；前三年无非负观测不改。"""
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
        ys = {p: year(p, r) for p, r in (("2021-12-31", 0.07), ("2022-12-31", 0.07), ("2023-12-31", -0.062), ("2024-12-31", -0.013))}
        self.assertEqual(correct_tax_anomalies(ys), 1)            # 圣邦：2023 −6.2% 改，2024 −1.3% 不改
        self.assertAlmostEqual(ys["2023-12-31"].tax_rate, 0.07)
        self.assertAlmostEqual(ys["2024-12-31"].tax_rate, 0.0)

    def test_without_nonnegative_history_untouched(self) -> None:
        ys = {"2025-12-31": year("2025-12-31", -0.10)}
        self.assertEqual(correct_tax_anomalies(ys), 0)            # 不退回法定税率
        rates = (("2018-12-31", -0.004), ("2019-12-31", -0.003), ("2020-12-31", 0.0), ("2021-12-31", -0.004), ("2024-12-31", -0.002))
        ys = {p: year(p, r) for p, r in rates}                    # 牧原：农业免税，历年微负
        self.assertEqual(correct_tax_anomalies(ys), 0)

    def test_small_negative_below_threshold_untouched(self) -> None:
        ys = {p: year(p, r) for p, r in (("2022-12-31", 0.12), ("2023-12-31", 0.12), ("2024-12-31", 0.12), ("2025-12-31", -0.045))}
        self.assertEqual(correct_tax_anomalies(ys), 0)            # 抵免不足税前利润 5%（拓荆 2025 −4.5%）


if __name__ == "__main__":
    unittest.main()
