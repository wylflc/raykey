#!/usr/bin/env python3
"""§6.4 预告补录（OI-288）：「业绩预告」栏目表外公告的检出、补录表校验与并入预告文件。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fetch_a_share_earnings_forecasts as f


def _table(code: str, notice: str, finance: str = "004", lower: str = "1", upper: str = "2") -> dict[str, object]:
    return {"security_code": code, "security_name": f"N{code}", "report_date": "2026-09-30", "notice_date": notice,
            "predict_finance_code": finance, "predict_type": "预增", "predict_amt_lower": lower,
            "predict_amt_upper": upper, "is_latest": "T", "source": "eastmoney:RPT_PUBLIC_OP_NEWPREDICT"}


def _ann(code: str, notice: str, title: str, art: str) -> dict[str, object]:
    return {"art_code": art, "title": title, "notice_date": f"{notice} 00:00:00",
            "codes": [{"stock_code": code, "short_name": f"N{code}"}]}


def _sup(code: str, notice: str, disposition: str = "叠加", art: str = "", lower: str = "5.542e8",
         upper: str = "5.632e8") -> dict[str, str]:
    return {"security_code": code, "security_name": f"N{code}", "report_date": "2026-09-30", "notice_date": notice,
            "art_code": art, "disposition": disposition, "predict_type": "预增",
            "predict_amt_lower": lower if disposition == "叠加" else "",
            "predict_amt_upper": upper if disposition == "叠加" else ""}


class TitlePeriodTest(unittest.TestCase):
    def test_periods(self) -> None:
        cases = {
            "乐鑫科技关于2026年第三季度业绩预告的自愿性披露公告": "2026-09-30",
            "2026年前三季度业绩预告": "2026-09-30",
            "2025年第二季度业绩预告的自愿性披露公告": "2025-06-30",
            "关于2025年半年度业绩预告的自愿性披露公告": "2025-06-30",
            "2026年第一季度业绩预增公告": "2026-03-31",
            "2025年度业绩快报暨业绩预告更正公告": "2025-12-31",
            "2024年年度业绩预增公告": "2024-12-31",
            "百济神州有限公司自愿披露关于2026年度经营业绩预测的公告": "2026-12-31",
        }
        for title, period in cases.items():
            self.assertEqual(f.title_period(title), period, title)
        self.assertIsNone(f.title_period("中控技术2026年1月-2月业绩预告的自愿性披露公告"))
        self.assertIsNone(f.title_period("业绩预告"))


class UnregisteredTest(unittest.TestCase):
    def test_only_this_period_outside_table_and_register(self) -> None:
        anns = [
            _ann("688018", "2026-10-14", "乐鑫科技关于2026年第三季度业绩预告的自愿性披露公告", "AN1"),
            _ann("002648", "2026-10-15", "2026年前三季度业绩预告", "AN2"),           # 表内 ±3 天
            _ann("600885", "2026-10-15", "关于2026年第三季度业绩说明会预告公告", "AN3"),  # 说明会
            _ann("688235", "2026-10-15", "自愿披露关于2027年度经营业绩预测的公告", "AN4"),  # 他期
            _ann("688777", "2026-10-15", "2026年1月-9月经营情况的自愿性披露公告", "AN5"),  # 识别不出，留
            _ann("123456", "2026-10-15", "可转债：2026年前三季度业绩预告", "AN6"),         # 非 A 股代码
        ]
        out = f.unregistered_announcements(anns, [_table("002648", "2026-10-13")], [], "2026-09-30", "t")
        self.assertEqual([(r["security_code"], r["art_code"]) for r in out], [("688018", "AN1"), ("688777", "AN5")])
        self.assertEqual(out[0]["url"], "https://pdf.dfcfw.com/pdf/H2_AN1_1.pdf")
        registered = [_sup("688018", "2026-10-14", art="AN1"), _sup("688777", "2026-10-16", "不叠加")]
        self.assertEqual(f.unregistered_announcements(anns, [_table("002648", "2026-10-13")], registered,
                                                      "2026-09-30", "t"), [])


class MergeTest(unittest.TestCase):
    def test_supplement_added_when_table_has_no_newer_row(self) -> None:
        table = [_table("002648", "2026-10-15")]
        rows = f.merge_supplements(table, [_sup("688018", "2026-10-14", art="AN1"), _sup("688777", "2026-10-15", "不叠加"),
                                           dict(_sup("600000", "2026-07-10"), report_date="2026-06-30")],
                                   "2026-09-30", "t")
        self.assertEqual(len(rows), 2)
        added = rows[-1]
        self.assertEqual((added["security_code"], added["predict_finance_code"], added["is_latest"], added["source"]),
                         ("688018", "004", "T", "补录:AN1"))
        self.assertEqual((added["predict_amt_lower"], added["predict_amt_upper"]), ("5.542e8", "5.632e8"))

    def test_table_wins_unless_supplement_is_newer(self) -> None:
        rows = f.merge_supplements([_table("688018", "2026-10-14")], [_sup("688018", "2026-10-14")], "2026-09-30", "t")
        self.assertEqual(len(rows), 1)
        table = [_table("688018", "2026-10-09"), _table("688018", "2026-10-09", finance="006")]
        rows = f.merge_supplements(table, [_sup("688018", "2026-10-14")], "2026-09-30", "t")
        self.assertEqual([(r["predict_finance_code"], r["is_latest"]) for r in rows], [("004", "F"), ("006", "T"), ("004", "T")])


class LoadSupplementsTest(unittest.TestCase):
    head = ",".join(f.SUPPLEMENT_FIELDS) + "\n"

    def load(self, body: str) -> list[dict[str, str]]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sup.csv"
            path.write_text(self.head + body, encoding="utf-8")
            return f.load_supplements(path)

    def test_valid_rows_and_missing_file(self) -> None:
        self.assertEqual(f.load_supplements(Path("/nonexistent/sup.csv")), [])
        rows = self.load("688018,乐鑫科技,2026-09-30,2026-10-14,AN1,叠加,预增,554226056.86,572226056.86,单季,2026-10-15,\n"
                         "688777,中控技术,2026-03-31,2026-03-05,AN5,不叠加,,,,非报告期,2026-10-15,\n")
        self.assertEqual(len(rows), 2)

    def test_invalid_rows_raise(self) -> None:
        for body in ("688018,乐鑫科技,2026-09-30,2026-10-14,AN1,叠加,预增,,,单季,2026-10-15,\n",
                     "688018,乐鑫科技,2026-09-30,2026-10-14,AN1,叠加,预增,9,1,单季,2026-10-15,\n",
                     "688018,乐鑫科技,2026-09-30,2026-10-14,AN1,待定,,,,x,2026-10-15,\n",
                     "68801,乐鑫科技,2026-09-30,2026-10-14,AN1,不叠加,,,,x,2026-10-15,\n"):
            with self.assertRaises(ValueError, msg=body):
                self.load(body)


if __name__ == "__main__":
    unittest.main()
