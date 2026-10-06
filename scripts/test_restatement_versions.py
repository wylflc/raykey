#!/usr/bin/env python3
"""OI-130／OI-129／OI-128 机制单元测试：重述前版本按可得日选用、无存档延后、面板版本切换、主体重置 known_from、
预告叠加的股权桥重算。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import restatement_archive  # noqa: E402
import roic_inputs  # noqa: E402
from roic_inputs import RoicYear, version_as_of, years_before  # noqa: E402
import build_historical_valuation_bands as bhvb  # noqa: E402
import apply_forecast_band_overlay as overlay  # noqa: E402


class RowsDifferTest(unittest.TestCase):
    def test_metadata_and_rounding_ignored(self) -> None:
        old = {"TOTAL_PARENT_EQUITY": "100.0", "UPDATE_DATE": "2026-04-15", "retrieved_at_utc": "a", "FOO": ""}
        new = {"TOTAL_PARENT_EQUITY": "100.3", "UPDATE_DATE": "2026-08-26", "retrieved_at_utc": "b", "FOO": "0"}
        self.assertEqual(restatement_archive.rows_differ(old, new), [])
        new["TOTAL_PARENT_EQUITY"] = "123.5"
        self.assertEqual(restatement_archive.rows_differ(old, new), ["TOTAL_PARENT_EQUITY"])


class StatementVersionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cur = RoicYear(period="2025-12-31", notice_date="2026-04-15", parent_equity=471.0)
        self.old = RoicYear(period="2025-12-31", notice_date="2026-04-15", parent_equity=382.0)
        self.cur.superseded = [("2026-08-26", self.old)]
        self.prev = RoicYear(period="2024-12-31", notice_date="2025-04-20", parent_equity=346.0)

    def test_version_as_of(self) -> None:
        self.assertIs(version_as_of(self.cur, "2026-05-01"), self.old)
        self.assertIs(version_as_of(self.cur, "2026-08-26"), self.cur)

    def test_years_before_uses_version_in_effect(self) -> None:
        years = {"2025-12-31": self.cur, "2024-12-31": self.prev}
        self.assertEqual([y.parent_equity for y in years_before(years, "2026-05-01", 2)], [382.0, 346.0])
        self.assertEqual([y.parent_equity for y in years_before(years, "2026-09-01", 2)], [471.0, 346.0])

    def test_delay_without_archive(self) -> None:
        cur = RoicYear(period="2025-12-31", notice_date="2026-04-15", parent_equity=471.0, delayed_until="2026-08-26")
        years = {"2025-12-31": cur, "2024-12-31": self.prev}
        self.assertEqual([y.period for y in years_before(years, "2026-05-01", 2)], ["2024-12-31"])
        self.assertEqual([y.period for y in years_before(years, "2026-08-26", 2)], ["2025-12-31", "2024-12-31"])


class PanelVersionTest(unittest.TestCase):
    def test_series_as_of_and_entity_reset(self) -> None:
        old = {"bps": "17.04", "notice_date": "2026-04-15"}
        cur = {"bps": "15.97", "notice_date": "2026-04-15", "_superseded": [("2026-08-26", old)]}
        series = {"2025-12-31": cur, "2024-12-31": {"bps": "15.4", "notice_date": "2025-04-20"}}
        self.assertEqual(bhvb.series_as_of(series, "2026-04-15")["2025-12-31"]["bps"], "17.04")
        self.assertEqual(bhvb.series_as_of(series, "2026-08-26")["2025-12-31"]["bps"], "15.97")
        self.assertIs(bhvb.series_as_of(series, "2026-08-26")["2024-12-31"], series["2024-12-31"])
        bhvb.ENTITY_RESET["000001"], bhvb.ENTITY_RESET_KNOWN["000001"] = "2025-12-31", "2026-08-26"
        try:
            self.assertIsNone(bhvb.entity_reset_for("000001", "2026-04-15"))
            self.assertEqual(bhvb.entity_reset_for("000001", "2026-08-26"), "2025-12-31")
            bhvb.ENTITY_RESET_KNOWN["000001"] = ""
            self.assertEqual(bhvb.entity_reset_for("000001", "2020-01-01"), "2025-12-31")
        finally:
            bhvb.ENTITY_RESET.pop("000001", None)
            bhvb.ENTITY_RESET_KNOWN.pop("000001", None)

    def test_entity_reset_loader_reads_known_from(self) -> None:
        resets = roic_inputs.load_entity_reset()
        self.assertIn("known_from", next(iter(resets.values())))


class VersionBpsTest(unittest.TestCase):
    """§6.3 第 2 条（OI-262）：三表存档推重述前 BPS 用普通股权益；股本不是股数时按面板 BPS 反推股数。"""

    def tearDown(self) -> None:
        bhvb.SHARE_EQUITY = "parent"

    def test_parent_mode_reproduces_old_formula(self) -> None:
        bal = {"TOTAL_PARENT_EQUITY": "1272875", "OTHER_EQUITY_TOOL": "177457", "SHARE_CAPITAL": "25220"}
        self.assertAlmostEqual(bhvb.version_bps(bal, 43.43, None), 1272875 / 25220)      # 招行 50.47：含永续债与优先股

    def test_common_equity_excludes_other_equity_instruments(self) -> None:
        bhvb.SHARE_EQUITY = "common"
        bal = {"TOTAL_PARENT_EQUITY": "1272875", "OTHER_EQUITY_TOOL": "177457", "SHARE_CAPITAL": "25220"}
        self.assertAlmostEqual(bhvb.version_bps(bal, 43.43, {"TOTAL_PARENT_EQUITY": 1272875.0, "OTHER_EQUITY_TOOL": 177457.0,
                                                             "SHARE_CAPITAL": 25220.0}), 43.4345, places=3)

    def test_share_capital_not_share_count_uses_panel_bps(self) -> None:
        bhvb.SHARE_EQUITY = "common"                     # 中国海油：股本 751.8 亿元、475.3 亿股、面板 BPS 16.889
        bal = {"TOTAL_PARENT_EQUITY": "802750", "SHARE_CAPITAL": "75180"}
        now = {"TOTAL_PARENT_EQUITY": 802750.0, "OTHER_EQUITY_TOOL": None, "SHARE_CAPITAL": 75180.0}
        self.assertAlmostEqual(bhvb.version_bps(bal, 16.889, now), 16.889, places=6)
        restated = {"TOTAL_PARENT_EQUITY": "780000", "SHARE_CAPITAL": "75180"}
        self.assertAlmostEqual(bhvb.version_bps(restated, 16.889, now), 16.889 * 780000 / 802750, places=6)

    def test_pre_restatement_panel_still_matches_old_statements(self) -> None:
        bhvb.SHARE_EQUITY = "common"                     # 面值 1 元：面板仍是重述前口径，旧表 ÷ 股本 = 面板 BPS
        old = {"TOTAL_PARENT_EQUITY": "100", "SHARE_CAPITAL": "10"}
        now = {"TOTAL_PARENT_EQUITY": 90.0, "OTHER_EQUITY_TOOL": None, "SHARE_CAPITAL": 10.0}
        self.assertAlmostEqual(bhvb.version_bps(old, 10.0, now), 10.0)


class OverlayBridgeTest(unittest.TestCase):
    def test_minority_share_scales_with_ev(self) -> None:
        band = {"roic_path": "growth", "nopat_ps": "2.0", "ev_ps": "40.0", "net_debt_ps": "12.0",
                "fin_net_debt_ps": "4.0", "minority_book_ps": "2.0", "minority_share": "0.25",
                "external_equity_ps": "1.0"}
        ev_new, iv_new, field = overlay.recompute(band, 1.5)
        self.assertEqual(field, "nopat_ps")
        self.assertAlmostEqual(ev_new, 60.0)
        # 总权益 56，盈利份额 0.25×56 = 14 > 账面 2 → 归母 42 + x 1
        self.assertAlmostEqual(iv_new, 43.0)
        band["minority_share"] = "0.01"        # 账面下界生效
        self.assertAlmostEqual(overlay.recompute(band, 1.5)[1], 60.0 - 4.0 - 2.0 + 1.0)
        del band["fin_net_debt_ps"]            # 旧带文件：退回净负债整体不动
        self.assertAlmostEqual(overlay.recompute(band, 1.5)[1], 60.0 - 12.0)


if __name__ == "__main__":
    unittest.main()
