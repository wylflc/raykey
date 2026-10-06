"""§7.3 结构性增长复核（OI-249、OI-250）判定：峰守卫砍掉每股 NOPAT ≥ 40%，且量驱动（放宽后 w = 0）或登记为结构成长型才标记。"""
import unittest

import structural_growth_review as sgr


def _band(w: float, nopat: float, value: float = 10.0) -> dict[str, str]:
    return {"status": "ok", "peak_weight": f"{w:.3f}", "nopat_ps": f"{nopat:.4f}", "intrinsic_value": f"{value:.4f}"}


class ReviewTest(unittest.TestCase):
    key = ("300308", "2025-03-31", "2025-04-21")
    pool = [{"security_code": "300308", "security_name": "中际旭创", "report_date": "2025-03-31", "available_at": "2025-04-21"}]

    def run_review(self, guarded, relaxed, unguarded, business=None):
        return sgr.review(self.pool, {self.key: guarded}, {self.key: relaxed}, {self.key: unguarded}, "2025-04-18",
                          industry={"300308": ("电子设备-光电子器件-光通信", False)}, business=business)[0]

    def test_volume_driven_cut_above_threshold_is_flagged(self) -> None:
        row = self.run_review(_band(1.0, 2.9042), _band(0.0, 6.2277), _band(0.0, 6.2277))
        self.assertTrue(row["volume_driven"])
        self.assertEqual(row["trigger"], "volume")
        self.assertTrue(row["flagged"])
        self.assertAlmostEqual(float(row["cut"]), 1 - 2.9042 / 6.2277, places=4)

    def test_registered_structural_grower_is_flagged_without_volume_signal(self) -> None:
        row = self.run_review(_band(1.0, 3.1886), _band(1.0, 3.1886), _band(0.0, 8.1026), {"300308": "结构成长型"})
        self.assertFalse(row["volume_driven"])
        self.assertEqual(row["trigger"], "business")
        self.assertTrue(row["flagged"])

    def test_no_trigger_is_not_flagged_even_with_large_cut(self) -> None:
        row = self.run_review(_band(1.0, 2.0), _band(1.0, 2.0), _band(0.0, 5.0), {"300308": "成本领先周期型"})
        self.assertEqual(row["trigger"], "")
        self.assertFalse(row["flagged"])
        self.assertAlmostEqual(float(row["cut"]), 0.6, places=4)

    def test_small_cut_is_not_flagged(self) -> None:
        row = self.run_review(_band(0.3, 3.6), _band(0.0, 4.0), _band(0.0, 4.0), {"300308": "结构成长型"})
        self.assertEqual(row["trigger"], "volume+business")
        self.assertFalse(row["flagged"])

    def test_missing_rebuilt_band_is_reported(self) -> None:
        row = sgr.review(self.pool, {}, {}, {}, "2025-04-18")[0]
        self.assertEqual(row["band_match"], "missing")
        self.assertFalse(row["flagged"])


def _roic(code: str = "000786", nopat_ps: float = 2.6, shares: float = 1.69e9, lam: str = "0.0", v: str = "0.000",
          ttm: str = "0.8000", path: str = "growth", **extra) -> dict[str, str]:
    return {"security_code": code, "security_name": f"N{code}", "roic_path": path, "nopat_ps": f"{nopat_ps:.4f}",
            "shares_est": f"{shares:.0f}", "growth_trust": lam, "trough_weight": v, "ttm_factor": ttm,
            "report_date": "2026-06-30", "available_at": "2026-08-21", **extra}


class TroughReviewTest(unittest.TestCase):
    """§7.3 谷底侧复核（OI-265）：机械锚 ≥ 1.5 倍 TTM 等价 NOPAT（最新年报 NOPAT × ttm_factor），且 λ = 0 或 v > 0 才标记。"""

    annual = {"000786": ("2025-12-31", 31.57e8)}

    def one(self, band, annual=None):
        return sgr.trough_review([band], self.annual if annual is None else annual, "2026-09-30")[0]

    def test_lagging_anchor_with_zero_trust_is_flagged(self) -> None:
        row = self.one(_roic())                      # 锚 2.6 × 16.9 亿股 = 43.94 亿；TTM 等价 31.57 × 0.8 = 25.26 亿
        self.assertTrue(row["flagged"])
        self.assertAlmostEqual(float(row["anchor_ttm_multiple"]), 43.94 / 25.256, places=3)

    def test_trough_guard_flags_even_with_positive_trust(self) -> None:
        self.assertTrue(self.one(_roic(lam="0.5", v="0.200"))["flagged"])

    def test_trusted_growth_without_guard_is_not_flagged(self) -> None:
        self.assertFalse(self.one(_roic(lam="0.5", v="0.000"))["flagged"])

    def test_multiple_below_threshold_is_not_flagged(self) -> None:
        self.assertFalse(self.one(_roic(ttm="1.0000", nopat_ps=2.5))["flagged"])   # 42.25 ÷ 31.57 = 1.34

    def test_adopted_research_reads_mechanical_anchor(self) -> None:
        row = self.one(_roic(nopat_ps=1.5, research_overlay="2026-10-06", model_nopat_ps="2.6000"))
        self.assertEqual(row["anchor_basis"], "model_nopat_ps")
        self.assertTrue(row["flagged"])

    def test_nonpositive_ttm_is_flagged_and_missing_annual_is_not(self) -> None:
        self.assertTrue(self.one(_roic(ttm="-0.1000"))["flagged"])
        row = self.one(_roic(), annual={})
        self.assertFalse(row["flagged"])
        self.assertEqual(row["note"], "无可得年报 NOPAT")

    def test_non_roic_path_is_skipped(self) -> None:
        self.assertEqual(sgr.trough_review([_roic(path="equity_fallback")], self.annual, "2026-09-30"), [])


if __name__ == "__main__":
    unittest.main()
