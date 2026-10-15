#!/usr/bin/env python3
"""§7.5 临时冻结名单：定期报告后的复看到期判定与复看登记（OI-289）。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import review_holds as rh


class RecheckDueTest(unittest.TestCase):
    hold = {"ruled_at": "2026-10-13", "released_at": ""}

    def test_due_only_after_ruling_and_last_recheck(self) -> None:
        self.assertIsNone(rh.recheck_due(self.hold, ""))
        self.assertIsNone(rh.recheck_due(self.hold, "2026-10-13"))
        due = rh.recheck_due(self.hold, "2026-10-28", "2026年 三季报")
        self.assertEqual(due, "2026年 三季报 2026-10-28 晚于上次复看 2026-10-13")
        self.assertIsNone(rh.recheck_due(dict(self.hold, rechecked_at="2026-10-28"), "2026-10-28"))
        self.assertIsNotNone(rh.recheck_due(dict(self.hold, rechecked_at="2026-10-28"), "2027-03-20"))

    def test_released_hold_is_never_due(self) -> None:
        self.assertIsNone(rh.recheck_due(dict(self.hold, released_at="2026-10-20"), "2026-10-28"))
        self.assertIsNone(rh.recheck_due(None, "2026-10-28"))


class RecordRecheckTest(unittest.TestCase):
    head = "security_code,security_name,basis,ruled_at,release_condition,released_at,note\r\n"
    body = ('603279,景津装备,§10.1 第 2 条,2026-10-13,涉案或整改结论披露，或用户另行裁定,,"留置, 11 月解除"\r\n'
            "603855,华荣股份,OI-265,2026-10-06,逐只复核结束,2026-10-06,x\r\n")

    def test_writes_only_the_two_columns_and_keeps_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            holds, log = Path(tmp) / "holds.csv", Path(tmp) / "log.csv"
            holds.write_bytes((self.head + self.body).encode("utf-8"))
            row = rh.record_recheck("603279", "2026-10-30", "三季报无涉案栏目进展，建议保留", holds=holds, log_path=log)
            self.assertEqual(row["rechecked_at"], "2026-10-30")
            self.assertEqual(holds.read_bytes().decode("utf-8"),
                             self.head.replace("note\r\n", "note,rechecked_at,recheck_note\r\n")
                             + '603279,景津装备,§10.1 第 2 条,2026-10-13,涉案或整改结论披露，或用户另行裁定,,'
                               '"留置, 11 月解除",2026-10-30,三季报无涉案栏目进展，建议保留\r\n'
                             + "603855,华荣股份,OI-265,2026-10-06,逐只复核结束,2026-10-06,x,,\r\n")
            text = log.read_text(encoding="utf-8")
            self.assertIn("user_review_hold_recheck:603279:2026-10-30", text)
            self.assertIn("rechecked", text)
            self.assertIsNone(rh.recheck_due(row, "2026-10-30"))

    def test_rejects_released_unknown_or_backdated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            holds, log = Path(tmp) / "holds.csv", Path(tmp) / "log.csv"
            holds.write_bytes((self.head + self.body).encode("utf-8"))
            for code, day in (("603855", "2026-10-30"), ("000001", "2026-10-30"), ("603279", "2026-10-12")):
                with self.assertRaises(ValueError):
                    rh.record_recheck(code, day, "x", holds=holds, log_path=log)
            with self.assertRaises(ValueError):
                rh.record_recheck("603279", "2026-10-30", "  ", holds=holds, log_path=log)
            rh.record_recheck("603279", "2026-10-30", "x", holds=holds, log_path=log)
            with self.assertRaises(ValueError):
                rh.record_recheck("603279", "2026-10-29", "y", holds=holds, log_path=log)


if __name__ == "__main__":
    unittest.main()
