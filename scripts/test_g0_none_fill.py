#!/usr/bin/env python3
"""OI-290 研究开关 `--g0-none-fill` 的回归测试。

Run: ``python3 scripts/test_g0_none_fill.py``

锁住三件事：
1. 缺省 off（生产口径不变）；
2. f3／f5 取 3%／5%；fr 在再投资率 ≤ 0 或增量回报算不出时取窗口营收增速与 3% 各半、夹 [0, 10%]，其余取 3%；
3. 窗口营收增速按首尾年报、跨度不足 2 年或端点非正时不算。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_historical_valuation_bands as bands  # noqa: E402
from roic_inputs import RoicYear  # noqa: E402


def window(*revenues: float | None, start: int = 2021) -> list[RoicYear]:
    return [RoicYear(period=f"{start + i}-12-31", notice_date=f"{start + i + 1}-04-30", revenue=r) for i, r in enumerate(revenues)]


class G0NoneFillTest(unittest.TestCase):
    def test_default_is_off(self) -> None:
        source = Path(bands.__file__).read_text(encoding="utf-8")
        self.assertIn('"--g0-none-fill", choices=("off", "f3", "f5", "fr"), default="off"', source)
        self.assertIn('fill = getattr(args, "g0_none_fill", "off")', source)

    def test_fixed_fills(self) -> None:
        self.assertEqual(bands.g0_none_fill_value("f3", -0.2, None, window(100, 120)), 0.03)
        self.assertEqual(bands.g0_none_fill_value("f5", 0.3, -0.1, window(100, 120)), 0.05)

    def test_revenue_fill_when_capital_leg_undefined(self) -> None:
        hist = window(100, 106, 112.36, 119.1016, 126.247696)          # 营收年化 6%
        self.assertAlmostEqual(bands.g0_none_fill_value("fr", -0.1, 0.5, hist), 0.045)
        self.assertAlmostEqual(bands.g0_none_fill_value("fr", 0.4, None, hist), 0.045)
        fast = window(100, 200, 400)                                    # 营收翻倍：取上限 10%
        self.assertEqual(bands.g0_none_fill_value("fr", None, None, fast), 0.10)
        shrink = window(100, 50, 25)                                    # 营收腰斩：夹到 0
        self.assertEqual(bands.g0_none_fill_value("fr", -0.3, None, shrink), 0.0)

    def test_revenue_fill_falls_back_to_base(self) -> None:
        self.assertEqual(bands.g0_none_fill_value("fr", -0.1, None, window(100, 110)), 0.03)    # 跨度 1 年
        self.assertEqual(bands.g0_none_fill_value("fr", -0.1, None, window(None, 0, 110)), 0.03)
        self.assertEqual(bands.g0_none_fill_value("fr", 0.2, -0.05, window(100, 200, 400)), 0.03)  # 增量回报 ≤ 0

    def test_window_revenue_cagr(self) -> None:
        self.assertAlmostEqual(bands.window_revenue_cagr(window(100, 110, 121)), 0.10)
        self.assertIsNone(bands.window_revenue_cagr(window(100)))
        self.assertIsNone(bands.window_revenue_cagr(window(100, 120)))


if __name__ == "__main__":
    unittest.main()
