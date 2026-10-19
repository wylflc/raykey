#!/usr/bin/env python3
"""Targeted regression tests for the off-pool archive without inferred quality tiers."""

import unittest

import build_a_share_core_valuation_pool as pool


class OffPoolDossierSectionTests(unittest.TestCase):
    def test_only_user_named_off_pool_dossiers_are_rendered(self):
        dossiers = [
            {
                "security_code": "000001",
                "security_name": "边界公司",
                "band_low": "10",
                "band_high": "12",
                "band_method": "内在价值模型·ROIC 口径（测试）",
                "reviewed_at": "2026-08-26",
                "dossier_dir": "data/companies/000001_边界公司",
                "notes": "用户点名建档；不入池",
            },
            {
                "security_code": "000002",
                "security_name": "已入池公司",
                "notes": "用户点名建档；后来入池",
            },
            {
                "security_code": "000003",
                "security_name": "批量档案",
                "notes": "全市场批量建档",
            },
        ]
        triage = [
            {"security_code": "000001", "attention_class": "boundary_pending"},
            {"security_code": "000002", "attention_class": "worth_attention"},
            {"security_code": "000003", "attention_class": "boundary_pending"},
        ]

        lines, count = pool.build_off_pool_dossier_section(dossiers, triage)
        text = "\n".join(lines)

        self.assertEqual(count, 1)
        self.assertIn("[边界公司](../data/companies/000001_边界公司/README.md)", text)
        self.assertIn("| — | boundary_pending | 10.00-12.00 | 11.00 |", text)
        self.assertNotIn("| 000001 |", text)
        self.assertNotIn("已入池公司", text)
        self.assertNotIn("批量档案", text)
        self.assertNotIn("| P/V |", text)

    def test_dossier_link_is_relative_to_the_markdown_location(self):
        dossiers = [{
            "security_code": "000001", "security_name": "边界公司",
            "dossier_dir": "data/companies/000001_边界公司", "notes": "用户点名建档",
        }]
        triage = [{"security_code": "000001", "attention_class": "boundary_pending"}]
        lines, _ = pool.build_off_pool_dossier_section(
            dossiers, triage, output_md=pool.ROOT / "data/processed/a_share_core_valuation_pool.md"
        )
        self.assertIn("[边界公司](../companies/000001_边界公司/README.md)", "\n".join(lines))
        lines, _ = pool.build_off_pool_dossier_section(dossiers, triage, output_md=pool.ROOT / "docs/x.md")
        self.assertIn("[边界公司](../data/companies/000001_边界公司/README.md)", "\n".join(lines))

    def test_unvaluable_named_dossier_keeps_structured_status(self):
        dossiers = [{
            "security_code": "600001",
            "security_name": "不可估公司",
            "band_low": "",
            "band_high": "",
            "reviewed_at": "2026-08-20",
            "notes": "用户点名建档",
        }]
        triage = [{
            "security_code": "600001",
            "attention_class": "documented_not_attention",
        }]

        lines, count = pool.build_off_pool_dossier_section(
            dossiers, triage, tiers={"600001": {"quality_tier": "L4"}}
        )
        text = "\n".join(lines)

        self.assertEqual(count, 1)
        self.assertIn("| L4 | documented_not_attention | — | — | 无法估值 |", text)


class IndependentColumnTests(unittest.TestCase):
    review = {"v_base": "33.37", "review_date": "2026-10-19"}

    def test_pv_is_spot_over_independent_value(self):
        self.assertEqual(pool.independent_cells(33.19, self.review, "2026-07-25"), ("0.995", "2026-10-19"))

    def test_new_periodic_report_after_review_marks_date(self):
        self.assertEqual(pool.independent_cells(33.19, self.review, "2026-10-28"), ("0.995", "2026-10-19*"))

    def test_missing_review_or_price_renders_dash(self):
        self.assertEqual(pool.independent_cells(33.19, None, "2026-10-28"), ("—", "—"))
        self.assertEqual(pool.independent_cells(None, self.review, ""), ("—", "2026-10-19"))


class QualityCellTests(unittest.TestCase):
    def test_tier_and_score_share_one_cell(self):
        self.assertEqual(pool.quality_cell("L1", "89.1"), "L1 (89.1)")

    def test_missing_score_or_tier_renders_tier_or_dash(self):
        self.assertEqual(pool.quality_cell("boundary_pending", ""), "boundary_pending")
        self.assertEqual(pool.quality_cell("L2", "—"), "L2")
        self.assertEqual(pool.quality_cell(None, "70"), "—")


if __name__ == "__main__":
    unittest.main()
