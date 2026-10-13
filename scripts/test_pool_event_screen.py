#!/usr/bin/env python3
"""§7.4 负面事件筛查（OI-285）：词表、登记表的检出与处置、重跑与缺口。"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import screen_pool_events as ev

# OI-286 回扫清单里的公告标题：当日必须检出。
EVENT_TITLES = [
    "双汇发展:关于收到《行政处罚决定书》的公告",
    "恒立液压:江苏恒立液压股份有限公司关于公司实际控制人、董事长被留置的公告",
    "贵州茅台:贵州茅台关于高级管理人员被实施留置的公告",
    "景津装备:景津装备股份有限公司关于公司实际控制人、董事长兼总经理解除留置的公告",
    "道通科技:道通科技关于收到深圳证监局对公司采取责令改正并对相关责任人出具警示函措施的公告",
    "关于对深圳市道通科技股份有限公司及有关责任人予以通报批评的决定",
    "乐鑫科技:乐鑫科技关于收到上海证监局行政监管措施决定书的公告",
    "片仔癀:漳州片仔癀药业股份有限公司关于公司2025年年度报告的信息披露监管问询函回复公告",
    "关于对宁波东方电缆股份有限公司拟购买房产暨关联交易的监管工作函",
    "瑞丰新材:关于公司被欧盟列入制裁名单的公告",
    "爱美客:关于公司控股子公司REGENBiotech,Inc.重大仲裁的进展公告",
    "晶盛机电:关于涉及诉讼事项的提示性公告",
    "立讯精密:关于公司及控股子公司涉及美国国际贸易委员会337调查的公告",
    "兴业银锡:关于子公司发生安全事故的公告",
    "恩华药业:关于子公司召回重酒石酸卡巴拉汀胶囊的公告",
    "五粮液:关于前期会计差错更正的公告",
]
# 例行文件：不得检出。
ROUTINE_TITLES = [
    "特宝生物:关于最近五年不存在被证券监管部门和证券交易所处罚或采取监管措施的公告",
    "长川科技:关于杭州长川科技股份有限公司申请向特定对象发行股票的审核问询函的回复(豁免版)",
    "双汇发展:2026年半年度非经营性资金占用及其他关联资金往来情况汇总表",
    "万华化学:万华化学烟台产业园MDI装置停产检修公告",
    "小商品城:《反洗钱及经济制裁管理制度(草案)》(H股发行并上市后适用)",
    "中航高科:中航高科违规经营投资责任追究管理办法",
    "北方华创:关于归还暂时补充流动资金的闲置募集资金的公告",
    "双汇发展:2026年8月31日投资者调研记录",
]
# 双汇 2026-05 事件的新闻标题：没有交易所公告，只能由新闻检出。
SHUANGHUI_MAY = [
    ("2026-05-21", "望奎双汇北大荒一批次猪肉抗生素超标：样品真实性异议不成立！"),
    ("2026-05-22", "抗生素残留超标38倍 双汇发展子公司猪肉抽检不合格"),
    ("2026-05-28", "子公司猪肉抗生素残留超标37.5倍， 双汇发展公开致歉"),
]


class LexiconTest(unittest.TestCase):
    def test_event_announcements_hit(self) -> None:
        for title in EVENT_TITLES:
            self.assertTrue(ev.announcement_hit(title), title)

    def test_routine_announcements_do_not_hit(self) -> None:
        for title in ROUTINE_TITLES:
            self.assertFalse(ev.announcement_hit(title), title)

    def test_category_hits_when_title_is_neutral(self) -> None:
        self.assertTrue(ev.announcement_hit("某公司:关于收到相关文件的公告", ["违法违规"]))
        self.assertFalse(ev.announcement_hit("某公司:关于最近五年被处罚情况的公告", ["处罚"]))

    def test_news_needs_name_or_alias_and_negative_term(self) -> None:
        for _, title in SHUANGHUI_MAY:
            self.assertTrue(ev.news_hit(title, ["双汇发展", "双汇"]), title)
        self.assertFalse(ev.news_hit(SHUANGHUI_MAY[0][1], ["双汇发展"]))          # 无别名时首日标题不含简称
        self.assertFalse(ev.news_hit("双汇发展：公司高度重视产品质量管理", ["双汇发展", "双汇"]))
        self.assertFalse(ev.news_hit("开市客中国被罚32万", ["双汇发展", "双汇"]))
        self.assertFalse(ev.news_hit("万华化学：烟台产业园乙烯二期装置停产检修", ["万华化学", "万华"]))
        self.assertFalse(ev.news_hit("中船财务被罚100万，涉员工行为管理严重违规", ["工商银行", "工行"]))   # 别名撞词
        self.assertTrue(ev.news_hit("工行安庆分行被罚30万，涉员工行为管理不到位", ["工商银行", "工行"]))

    def test_share_class_suffix_is_dropped_for_news(self) -> None:
        self.assertEqual(ev.clean_name("京东方A"), "京东方")
        self.assertEqual(ev.clean_name("贵州茅台"), "贵州茅台")


class RunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pool, self.holdings = self.dir / "pool.csv", self.dir / "holdings.csv"
        self.aliases, self.register = self.dir / "aliases.csv", self.dir / "register.csv"
        self.pool.write_text("security_code,security_name\n000895,双汇发展\n601100,恒立液压\n600309,万华化学\n", encoding="utf-8")
        self.holdings.write_text("security_code,security_name,current_shares\n000651,格力电器,100\n", encoding="utf-8")
        self.aliases.write_text("security_code,security_name,alias\n000895,双汇发展,双汇\n", encoding="utf-8")
        self.news: dict[str, list[dict[str, str]]] = {}
        self.fail: set[str] = set()
        self.pages: dict[str, list[list[dict[str, str]]]] = {}
        self.totals: dict[str, int] = {}
        self.calls: list[tuple[str, int, str]] = []

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def snapshot(self, day: str, since: str, items: list[tuple[str, str, str]]) -> None:
        value = dict(signal_date=day, query_start=since, locally_filtered_codes=["000651", "000895", "600309", "601100"],
                     announcements=[dict(art_code=art, title=title, notice_date=f"{day} 00:00:00", columns=[],
                                         codes=[dict(stock_code=code)]) for code, art, title in items])
        (self.dir / f"daily_announcements_{day}.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def fetch(self, keyword: str, page: int, sort: str = "time") -> tuple[list[dict[str, str]], int]:
        self.calls.append((keyword, page, sort))
        if keyword in self.fail:
            raise OSError("down")
        if sort == "time" and keyword in self.pages:
            rows = self.pages[keyword][page - 1] if page <= len(self.pages[keyword]) else []
        else:
            rows = self.news.get(keyword if sort == "time" else keyword + "#relevance", []) if page == 1 else []
        return rows, self.totals.get(keyword, len(rows))

    def run_screen(self, day: str, since: str, **kwargs) -> int:
        return ev.run(day, since, pool=self.pool, holdings=self.holdings, aliases_path=self.aliases,
                      register=self.register, interim=self.dir, fetch=self.fetch, pause=0, **kwargs)

    def rows(self) -> list[dict[str, str]]:
        with self.register.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_news_only_event_is_registered_on_first_report_day(self) -> None:
        """双汇 5 月事件回放：公告流为空，新闻首日即登记待复核。"""
        self.snapshot("2026-05-21", "2026-05-20", [])
        self.news["双汇发展"] = [dict(date=d, title=t, url=f"u{i}", media="m") for i, (d, t) in enumerate(SHUANGHUI_MAY[:1])]
        self.assertEqual(self.run_screen("2026-05-21", "2026-05-20"), 0)
        rows = self.rows()
        self.assertEqual([(r["security_code"], r["detected_on"], r["sources"], r["disposition"]) for r in rows],
                         [("000895", "2026-05-21", "新闻", "")])
        self.assertEqual(ev.pending_rows(rows)["000895"]["first_event_date"], "2026-05-21")

    def test_announcement_and_news_merge_and_rerun_is_idempotent(self) -> None:
        self.snapshot("2026-03-23", "2026-03-20", [("601100", "AN1", EVENT_TITLES[1]), ("600309", "AN2", ROUTINE_TITLES[3])])
        self.news["恒立液压"] = [dict(date="2026-03-21", title="恒立液压董事长被留置", url="n1", media="m"),
                             dict(date="2026-03-19", title="恒立液压被罚旧闻", url="n0", media="m")]
        for _ in range(2):
            self.assertEqual(self.run_screen("2026-03-23", "2026-03-20"), 0)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["security_code"], rows[0]["sources"], rows[0]["hits"]), ("601100", "公告+新闻", "2"))
        self.assertEqual(rows[0]["headline"], EVENT_TITLES[1].split(":", 1)[0] + ":" + EVENT_TITLES[1].split(":", 1)[1])
        keys = json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))["keys"]
        self.assertEqual(keys, ["ann:AN1", "news:n1"])

    def test_items_seen_last_scan_are_not_registered_again(self) -> None:
        self.snapshot("2026-03-23", "2026-03-20", [("601100", "AN1", EVENT_TITLES[1])])
        self.run_screen("2026-03-23", "2026-03-20")
        self.snapshot("2026-03-24", "2026-03-23", [("601100", "AN1", EVENT_TITLES[1])])
        self.run_screen("2026-03-24", "2026-03-23")
        self.assertEqual([r["detected_on"] for r in self.rows()], ["2026-03-23"])

    def test_disposed_row_is_kept_on_rerun_and_new_items_wait_for_next_scan(self) -> None:
        log = self.dir / "log.csv"
        self.snapshot("2026-03-23", "2026-03-20", [("601100", "AN1", EVENT_TITLES[1])])
        self.run_screen("2026-03-23", "2026-03-20")
        ev.dispose("601100", "2026-03-23", "事件复核", "Q4 78→62", "2026-03-23", register=self.register, log_path=log)
        self.news["恒立液压"] = [dict(date="2026-03-23", title="恒立液压回应董事长被留置", url="n9", media="m")]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.run_screen("2026-03-23", "2026-03-20")
        self.assertIn("[重跑新见·未计入] 601100 恒立液压｜新闻 2026-03-23｜恒立液压回应董事长被留置", out.getvalue())
        rows = self.rows()
        self.assertEqual([(r["disposition"], r["note"], r["hits"]) for r in rows], [("事件复核", "Q4 78→62", "1")])
        self.assertEqual(ev.pending_rows(rows), {})
        self.assertEqual(json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))["keys"], ["ann:AN1"])
        self.snapshot("2026-03-24", "2026-03-23", [])
        self.run_screen("2026-03-24", "2026-03-23")
        self.assertEqual([(r["detected_on"], r["sources"], r["disposition"]) for r in self.rows()],
                         [("2026-03-23", "公告", "事件复核"), ("2026-03-24", "新闻", "")])
        with self.assertRaises(ValueError):
            ev.dispose("601100", "2026-03-23", "不构成事件", "重复", "2026-03-24", register=self.register, log_path=log)
        self.assertIn("pool_event:601100:2026-03-23:pool_event_disposition", log.read_text(encoding="utf-8"))

    def test_code_name_and_alias_are_all_searched_and_swamped_keyword_falls_back_to_relevance(self) -> None:
        """代码、简称、别名各检索一次；简称命中数到上限且首页标题无一含名称时并取相关度第一页、不再翻页并记入产物。"""
        self.snapshot("2026-03-23", "2026-03-20", [])
        (self.dir / "aliases.csv").write_text("security_code,security_name,alias\n601100,恒立液压,恒立\n", encoding="utf-8")
        self.news["601100"] = [dict(date="2026-03-21", title="恒立液压：董事长被留置", url="c1", media="m")]
        self.news["恒立"] = [dict(date="2026-03-22", title="恒立回应被查传闻", url="a1", media="m")]
        self.news["恒立液压"] = [dict(date="2026-03-23", title="某公司被罚（无关的最新文章）", url="x1", media="m")]
        self.news["恒立液压#relevance"] = [dict(date="2026-03-22", title="恒立液压回应董事长被调查", url="r1", media="m"),
                                       dict(date="2026-03-01", title="恒立液压被罚旧闻", url="r0", media="m")]
        self.totals["恒立液压"] = ev.NEWS_HITS_CAP
        self.assertEqual(self.run_screen("2026-03-23", "2026-03-20"), 0)
        product = json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))
        self.assertEqual(product["keys"], ["news:a1", "news:c1", "news:r1"])
        self.assertEqual(product["news_partial_queries"], {"601100": ["恒立液压"]})
        self.assertEqual([c for c in self.calls if c[0] in ("601100", "恒立", "恒立液压")],
                         [("601100", 1, "time"), ("恒立液压", 1, "time"), ("恒立液压", 1, "default"), ("恒立", 1, "time")])

    def test_keyword_at_hits_cap_keeps_paging_when_time_sort_is_relevant(self) -> None:
        """命中数到上限但首页标题含名称（公司本身条目多）：并取相关度第一页，时间排序照常翻页，翻到上限记入产物。"""
        self.snapshot("2026-03-23", "2026-03-20", [])
        page = [dict(date="2026-03-23", title=f"恒立液压日常报道{i}", url=f"n{i}", media="m") for i in range(ev.NEWS_PAGE_SIZE)]
        self.pages["恒立液压"] = [page] * ev.NEWS_MAX_PAGES
        self.totals["恒立液压"] = ev.NEWS_HITS_CAP
        self.assertEqual(self.run_screen("2026-03-23", "2026-03-20"), 0)
        product = json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))
        self.assertEqual(product["news_partial_queries"], {"601100": ["恒立液压"]})
        self.assertEqual(sum(c[0] == "恒立液压" and c[2] == "time" for c in self.calls), ev.NEWS_MAX_PAGES)

    def test_news_source_failure_blocks_unless_gap_is_allowed(self) -> None:
        self.snapshot("2026-03-23", "2026-03-20", [])
        self.fail.add("恒立液压")
        self.assertEqual(self.run_screen("2026-03-23", "2026-03-20"), 1)
        value = json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))
        self.assertEqual((value["news_failed_codes"], value["news_gaps_allowed"]), (["601100"], False))
        self.assertEqual(self.run_screen("2026-03-23", "2026-03-20", allow_news_gaps=True), 0)
        self.assertTrue(json.loads((self.dir / "pool_event_hits_2026-03-23.json").read_text(encoding="utf-8"))["news_gaps_allowed"])

    def test_announcement_snapshot_must_cover_window_and_members(self) -> None:
        self.snapshot("2026-03-23", "2026-03-21", [])
        with self.assertRaises(ValueError):
            self.run_screen("2026-03-23", "2026-03-20")
        self.snapshot("2026-03-23", "2026-03-20", [])
        self.pool.write_text("security_code,security_name\n000895,双汇发展\n300750,宁德时代\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_screen("2026-03-23", "2026-03-20")

    def test_manual_registration_for_events_found_outside_the_screen(self) -> None:
        log = self.dir / "log.csv"
        members = ev.load_members(self.pool, self.holdings)
        row = ev.add("000651", "2026-10-13", "用户点名：某事件", "2026-05-14", members=members, register=self.register, log_path=log)
        self.assertEqual((row["sources"], row["first_event_date"], row["disposition"]), ("人工", "2026-05-14", ""))
        with self.assertRaises(ValueError):
            ev.add("000651", "2026-10-13", "重复", members=members, register=self.register, log_path=log)
        with self.assertRaises(ValueError):
            ev.add("999999", "2026-10-13", "池外", members=members, register=self.register, log_path=log)


if __name__ == "__main__":
    unittest.main()
