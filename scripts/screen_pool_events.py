#!/usr/bin/env python3
"""§7.4 负面事件：池成员与持仓的公告、新闻标题筛查，以及待复核行的登记与处置（OI-285）。

每晚取证后运行。公告读当日取证快照 `data/interim/daily_announcements_<日期>.json`；新闻取东财资讯搜索，
按证券代码、公司简称与 `data/reference/pool_news_aliases.csv` 登记的别名各检索一次，标题须含简称或别名。
关键词命中数到接口上限时并取相关度排序的第一页；此时若时间排序的第一页标题无一含简称或别名（关键词被拆成
常用词、被无关文章淹没），该关键词不再翻页。未能按时间取全的关键词记入产物并在报告列出。标题命中词表的写
`data/interim/pool_event_hits_<日期>.json`，每家命中的公司在 `data/reference/pool_event_reviews.csv`
登记一条待复核行；待复核行由 `build_report_update_queue.py` 记 `event_review` 并冻结新增买入，处置后解除。
上次扫描日产物里已出现的条目不重复登记；已处置的当日行不因重跑而改动，重跑新见的条目只在输出列出，当晚人工看。

    python3 scripts/screen_pool_events.py --signal-date YYYY-MM-DD --since <上次成功扫描日>
    python3 scripts/screen_pool_events.py --dispose <代码> --detected-on YYYY-MM-DD \\
        --disposition 事件复核|不构成事件 --note "..."
    # 筛查之外发现的事件（用户点名、存量补核）
    python3 scripts/screen_pool_events.py --add <代码> --detected-on YYYY-MM-DD --headline "..." \\
        [--first-event-date YYYY-MM-DD]

新闻源取数失败的公司记入产物 `news_failed_codes` 并非零退出；`--allow-news-gaps` 才继续（当日报告须列缺口）。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POOL = ROOT / "data/processed/a_share_core_valuation_pool.csv"
DEFAULT_HOLDINGS = ROOT / "data/processed/a_share_holdings.csv"
DEFAULT_ALIASES = ROOT / "data/reference/pool_news_aliases.csv"
DEFAULT_REGISTER = ROOT / "data/reference/pool_event_reviews.csv"
INTERIM = ROOT / "data/interim"
REGISTER_FIELDS = ["security_code", "security_name", "detected_on", "sources", "first_event_date", "headline", "hits",
                   "disposition", "reviewed_at", "note"]
DISPOSITIONS = ("事件复核", "不构成事件")
NEWS_URL = "https://search-api-web.eastmoney.com/search/jsonp"
NEWS_PAGE_SIZE = 100
NEWS_MAX_PAGES = 5
NEWS_WORKERS = 4
NEWS_HITS_CAP = 10000   # 搜索接口的命中数上限；到上限的关键词并取相关度第一页

# §7.4 负面词表：唯一定义。公告与新闻各一张，排除词两者共用。
ANNOUNCEMENT_TERMS = re.compile(
    "行政处罚|处罚决定|事先告知书|立案|留置|被调查|接受调查|强制措施|逮捕|拘留|刑事|失联"
    "|监管措施|警示函|监管警示|监管函|监管工作函|监管关注|通报批评|公开谴责|纪律处分|责令改正|问询函|关注函"
    "|诉讼|仲裁|事故|制裁|337调查|反倾销|反补贴|召回|停产|停业"
    "|保留意见|无法表示意见|否定意见|会计差错|前期差错|违规担保|失信被执行|被冻结|风险警示|终止上市|澄清"
    "|占用及清偿|违规占用|占用.{0,8}(?:归还|清偿|整改)")
ANNOUNCEMENT_COLUMNS = re.compile("处罚|违法违规|通报批评|公开谴责|监管工作函|监管关注|纪律处分")
NEWS_TERMS = re.compile(
    "处罚|罚款|罚没|被罚|立案|留置|被查|调查|失联|警示函|监管函|监管措施|问询函|约谈|通报"
    "|超标|不合格|召回|下架|致歉|道歉|事故|爆炸|起火|火灾|停产|中毒|污染"
    "|造假|虚假|违规|违法|涉嫌|举报|质疑|被曝|诉讼|仲裁|索赔|侵权|垄断|制裁|禁令|黑榜|维权"
    "|暴雷|爆雷|失信|冻结|被执行|退市|做空|裁员|欠薪")
# 例行文件与常规事项：再融资审核问询、五年合规自查、制度文本、占用情况汇总表、装置检修等。
EXCLUDE_TERMS = re.compile(
    "最近五年|管理办法|管理制度|制度\\(|制度（|审核问询函|汇总表|专项说明|专项审核|法律意见|募集资金专户"
    "|反洗钱|责任追究|内部问责|认定标准|检修")


def clean_name(name: str) -> str:
    """去掉简称末尾的 A／B 股标记（京东方A → 京东方），新闻标题不带。"""
    return re.sub(r"[ABＡＢ]$", "", (name or "").strip())


def load_members(pool: Path = DEFAULT_POOL, holdings: Path = DEFAULT_HOLDINGS) -> dict[str, str]:
    """筛查范围与公告取证同口径：核心池与持仓表的全部代码。"""
    members: dict[str, str] = {}
    for path in (pool, holdings):
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                code = (row.get("security_code") or "").strip().zfill(6)
                if code.strip("0"):
                    members.setdefault(code, (row.get("security_name") or "").strip())
    return members


def load_aliases(path: Path = DEFAULT_ALIASES) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    if not Path(path).exists():
        return aliases
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            alias = (row.get("alias") or "").strip()
            if len(alias) < 2:
                raise ValueError(f"新闻别名至少两个字：{row}")
            aliases.setdefault((row.get("security_code") or "").strip().zfill(6), []).append(alias)
    return aliases


def announcement_hit(title: str, columns: list[str] | None = None) -> bool:
    title = re.sub(r"</?em>", "", title or "")
    if EXCLUDE_TERMS.search(title):
        return False
    return bool(ANNOUNCEMENT_TERMS.search(title) or any(ANNOUNCEMENT_COLUMNS.search(c or "") for c in columns or []))


# 别名在标题里撞上的无关词：「工行」之于「员工行为」「员工行拘」。
NAME_NOISE = re.compile("员工行")


def news_hit(title: str, names: list[str]) -> bool:
    title = re.sub(r"</?em>|\s+", "", title or "")
    named = NAME_NOISE.sub("", title)
    return bool(any(n and n in named for n in names) and NEWS_TERMS.search(title) and not EXCLUDE_TERMS.search(title))


def search_news(keyword: str, page: int, sort: str = "time") -> tuple[list[dict[str, str]], int]:
    """东财资讯搜索一页；返回 (条目, 接口报告的命中数)。`sort` 取 time（时间倒序）或 default（相关度）。"""
    param = {"uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web",
             "clientVersion": "curr",
             "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": sort, "pageIndex": page,
                                            "pageSize": NEWS_PAGE_SIZE, "preTag": "", "postTag": ""}}}
    url = NEWS_URL + "?cb=cb&param=" + urllib.parse.quote(json.dumps(param, ensure_ascii=False))
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://so.eastmoney.com/"})
    raw = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
    data = json.loads(raw[raw.index("(") + 1:raw.rindex(")")])
    rows = [dict(date=(a.get("date") or "")[:10], title=a.get("title") or "", media=a.get("mediaName") or "",
                 url=a.get("url") or "") for a in (data.get("result") or {}).get("cmsArticleWebOld") or []]
    return rows, int(data.get("hitsTotal") or 0)


def screen_announcements(snapshot: dict, members: dict[str, str]) -> list[dict[str, str]]:
    hits = []
    for item in snapshot.get("announcements") or []:
        title = item.get("title") or item.get("title_ch") or ""
        columns = [c.get("column_name") or "" for c in item.get("columns") or []]
        if not announcement_hit(title, columns):
            continue
        for ref in item.get("codes") or []:
            code = (ref.get("stock_code") or "").zfill(6)
            if code in members:
                art = item.get("art_code") or ""
                hits.append(dict(code=code, name=members[code], source="公告", date=(item.get("notice_date") or "")[:10],
                                 title=re.sub(r"</?em>", "", title), key=f"ann:{art}",
                                 url=f"https://pdf.dfcfw.com/pdf/H2_{art}_1.pdf"))
    return hits


def _news_for(code: str, name: str, names: list[str], since: str, fetch, pause: float, retries: int):
    """一家公司的新闻命中；返回 (命中, 是否取数失败, 未能按时间取全的关键词)。"""
    found, partial = {}, []
    if not names[0]:
        return [], True, []

    def page_of(query: str, page: int, sort: str):
        for attempt in range(retries):
            try:
                return fetch(query, page, sort)
            except Exception:   # noqa: BLE001 - 重试后仍失败则整家记缺口
                if attempt == retries - 1:
                    raise
                time.sleep(7.5 * pause * (attempt + 1))

    def titled(row: dict[str, str]) -> bool:
        title = re.sub(r"</?em>|\s+", "", row["title"])
        return any(n in title for n in names)

    def keep(rows: list[dict[str, str]]) -> None:
        for row in rows:
            if row["date"] >= since and news_hit(row["title"], names):
                key = f"news:{row['url'] or row['title']}"
                found[key] = dict(code=code, name=name, source="新闻", date=row["date"], title=row["title"].strip(),
                                  key=key, url=row["url"], media=row.get("media", ""))

    try:
        for query in dict.fromkeys([code, *names]):
            for page in range(1, NEWS_MAX_PAGES + 1):
                rows, total = page_of(query, page, "time")
                keep(rows)
                if page == 1 and total >= NEWS_HITS_CAP:
                    keep(page_of(query, 1, "default")[0])
                    if not any(titled(r) for r in rows):   # 被无关文章淹没，继续翻页无益
                        partial.append(query)
                        break
                if len(rows) < NEWS_PAGE_SIZE or min(r["date"] for r in rows) < since:
                    break
                time.sleep(pause)
            else:
                partial.append(query)
            time.sleep(pause)
    except Exception:   # noqa: BLE001
        return list(found.values()), True, partial
    return list(found.values()), False, partial


def screen_news(members: dict[str, str], aliases: dict[str, list[str]], since: str, *, fetch=search_news,
                pause: float = 0.2, retries: int = 3, workers: int = NEWS_WORKERS):
    """逐家检索 `since` 当日及以后的新闻标题；返回 (命中, 取数失败的代码, {代码: 未能按时间取全的关键词})。"""
    from concurrent.futures import ThreadPoolExecutor
    items = sorted(members.items())
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(lambda kv: _news_for(kv[0], kv[1], [clean_name(kv[1])] + aliases.get(kv[0], []),
                                                     since, fetch, pause, retries), items))
    hits = [h for found, _, _ in results for h in found]
    failed = [code for (code, _), (_, bad, _) in zip(items, results) if bad]
    partial = {code: queries for (code, _), (_, _, queries) in zip(items, results) if queries}
    return hits, failed, partial


def load_register(path: Path = DEFAULT_REGISTER) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for row in rows:
        row["security_code"] = (row.get("security_code") or "").zfill(6)
        key = (row["security_code"], row.get("detected_on") or "")
        if len(key[1]) != 10 or key in seen or (row.get("disposition") or "") not in ("",) + DISPOSITIONS:
            raise ValueError(f"负面事件登记行无效或重复：{key}")
        seen.add(key)
    return rows


def write_register(rows: list[dict[str, str]], path: Path = DEFAULT_REGISTER) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in REGISTER_FIELDS} for row in rows)


def pending_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """代码 → 最早一条待复核行（队列冻结与报告用）。"""
    out: dict[str, dict[str, str]] = {}
    for row in sorted(rows, key=lambda r: r.get("detected_on") or ""):
        if not (row.get("disposition") or "").strip():
            out.setdefault((row.get("security_code") or "").zfill(6), row)
    return out


def summarize(hits: list[dict[str, str]]) -> dict[str, str]:
    """一家公司当日命中汇成登记行字段：来源、最早日期、标题（公告优先）、不同标题数。"""
    ordered = sorted(hits, key=lambda h: (h["source"] != "公告", h["date"], h["title"]))
    sources = [s for s in ("公告", "新闻") if any(h["source"] == s for h in hits)]
    return dict(sources="+".join(sources), first_event_date=min(h["date"] for h in hits),
                headline=ordered[0]["title"][:80], hits=str(len({h["title"] for h in hits})))


def upsert_pending(rows: list[dict[str, str]], hits: list[dict[str, str]], detected_on: str,
                   seen: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """把未见过的命中登记为当日待复核行；返回 (登记表, 计入当日的命中)。已处置的当日行不改，其新命中不计入。"""
    by_key = {(r["security_code"], r["detected_on"]): r for r in rows}
    fresh: dict[str, list[dict[str, str]]] = {}
    for hit in hits:
        if hit["key"] not in seen:
            fresh.setdefault(hit["code"], []).append(hit)
    counted: list[dict[str, str]] = []
    for code, group in sorted(fresh.items()):
        row = by_key.get((code, detected_on))
        if row is not None and (row.get("disposition") or "").strip():
            continue
        if row is None:
            row = dict.fromkeys(REGISTER_FIELDS, "")
            row.update(security_code=code, security_name=group[0]["name"], detected_on=detected_on)
            rows.append(row)
        row.update(summarize(group))
        counted += group
    return rows, counted


def log_decision(row: dict[str, str], decision_type: str, result: str, reason: str, log_path: Path | None) -> None:
    from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log
    append_decision_log(log_path or DEFAULT_DECISION_LOG, [{
        "logged_at_utc": datetime.now(timezone.utc).isoformat(), "workflow_stage": "quality_review",
        "run_id": f"pool_event_{row['detected_on']}", "as_of": row.get("reviewed_at") or row["detected_on"],
        "security_code": row["security_code"], "security_name": row["security_name"],
        "decision_type": decision_type, "decision_result": result, "summary_reason": reason,
        "input_files": f"data/interim/pool_event_hits_{row['detected_on']}.json", "source_urls": "",
        "output_file": "data/reference/pool_event_reviews.csv", "operator_or_script": "screen_pool_events.py",
        "workflow_version": WORKFLOW_VERSION,
        "decision_id": f"pool_event:{row['security_code']}:{row['detected_on']}:{decision_type}",
        "supersedes_decision_id": ""}])


def dispose(code: str, detected_on: str, disposition: str, note: str, reviewed_at: str, *,
            register: Path = DEFAULT_REGISTER, log_path: Path | None = None) -> dict[str, str]:
    """处置一条待复核行并写决策日志；每行只处置一次。"""
    code = code.zfill(6)
    date.fromisoformat(detected_on), date.fromisoformat(reviewed_at)
    if disposition not in DISPOSITIONS or not note.strip() or reviewed_at < detected_on:
        raise ValueError("处置须给有效结论与说明，处置日不早于检出日")
    rows = load_register(register)
    row = next((r for r in rows if (r["security_code"], r["detected_on"]) == (code, detected_on)), None)
    if row is None or (row.get("disposition") or "").strip():
        raise ValueError(f"没有待复核的登记行：{code} {detected_on}")
    row.update(disposition=disposition, reviewed_at=reviewed_at, note=note.strip())
    write_register(rows, register)
    log_decision(row, "pool_event_disposition", disposition,
                 f"§7.4 负面事件处置：{row['sources']}｜{row['headline']}｜{note.strip()}", log_path)
    return row


def add(code: str, detected_on: str, headline: str, first_event_date: str = "", *, sources: str = "人工",
        members: dict[str, str] | None = None, register: Path = DEFAULT_REGISTER,
        log_path: Path | None = None) -> dict[str, str]:
    """登记筛查之外发现的事件（用户点名、存量补核）为待复核行。"""
    code = code.zfill(6)
    members = load_members() if members is None else members
    date.fromisoformat(detected_on)
    first_event_date = first_event_date or detected_on
    date.fromisoformat(first_event_date)
    if code not in members or not headline.strip():
        raise ValueError("须给池内或持仓代码与事件标题")
    rows = load_register(register)
    if any((r["security_code"], r["detected_on"]) == (code, detected_on) for r in rows):
        raise ValueError(f"该公司当日已有登记行：{code} {detected_on}")
    row = dict.fromkeys(REGISTER_FIELDS, "")
    row.update(security_code=code, security_name=members[code], detected_on=detected_on, sources=sources,
               first_event_date=first_event_date, headline=headline.strip()[:80], hits="1")
    rows.append(row)
    write_register(rows, register)
    log_decision(row, "pool_event_registered", "待复核", f"§7.4 负面事件登记：{sources}｜{row['headline']}", log_path)
    return row


def run(signal_date: str, since: str, *, allow_news_gaps: bool = False, pool: Path = DEFAULT_POOL,
        holdings: Path = DEFAULT_HOLDINGS, aliases_path: Path = DEFAULT_ALIASES, register: Path = DEFAULT_REGISTER,
        interim: Path = INTERIM, fetch=search_news, pause: float = 0.2) -> int:
    if since >= signal_date:
        raise ValueError("筛查起点须早于信号日")
    snapshot = json.loads((interim / f"daily_announcements_{signal_date}.json").read_text(encoding="utf-8"))
    if snapshot.get("signal_date") != signal_date or snapshot.get("query_start", "9") > since:
        raise ValueError("公告取证快照的日期或区间与本次筛查不符")
    members = load_members(pool, holdings)
    missing = sorted(set(members) - set(snapshot.get("locally_filtered_codes") or []))
    if missing:
        raise ValueError(f"公告取证未覆盖全部池与持仓代码，须重新取证：{missing[:8]}")
    previous = interim / f"pool_event_hits_{since}.json"
    seen = set(json.loads(previous.read_text(encoding="utf-8")).get("keys") or []) if previous.exists() else set()
    news, failed, partial = screen_news(members, load_aliases(aliases_path), since, fetch=fetch, pause=pause)
    found = screen_announcements(snapshot, members) + news
    rows, counted = upsert_pending(load_register(register), found, signal_date, seen)
    write_register(rows, register)
    out = interim / f"pool_event_hits_{signal_date}.json"
    if out.exists():   # 重跑：当日已处置的行保留上一次计入的条目，新见的只列出
        disposed = {r["security_code"] for r in rows
                    if r["detected_on"] == signal_date and (r.get("disposition") or "").strip()}
        counted = [h for h in json.loads(out.read_text(encoding="utf-8")).get("hits") or []
                   if h["code"] in disposed] + counted
    known = seen | {h["key"] for h in counted}
    late = sorted({h["key"]: h for h in found if h["key"] not in known}.values(), key=lambda h: (h["code"], h["date"]))
    out.write_text(json.dumps(dict(
        signal_date=signal_date, since=since, retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        covered_codes=sorted(members), news_source=NEWS_URL, news_failed_codes=failed, news_partial_queries=partial,
        news_gaps_allowed=bool(failed and allow_news_gaps), hits=counted,
        keys=sorted({h["key"] for h in counted})), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pending = pending_rows(rows)
    today = [r for r in rows if r["detected_on"] == signal_date and ("公告" in r["sources"] or "新闻" in r["sources"])]
    print(f"负面事件筛查（{since}，{signal_date}]：覆盖 {len(members)} 只；当日命中 {len(today)} 家"
          f"（公告 {sum('公告' in r['sources'] for r in today)}，新闻 {sum('新闻' in r['sources'] for r in today)}）；"
          f"待复核 {len(pending)} 家" + ("，当晚逐条处置（§7.4）" if pending else ""))
    for code, row in sorted(pending.items()):
        print(f"  [待复核] {code} {row['security_name']}｜检出 {row['detected_on']}｜{row['sources']}｜"
              f"{row['hits']} 条｜{row['headline']}")
    for hit in late:   # 已处置公司在重跑中新见的条目：不改登记行，当晚人工看
        print(f"  [重跑新见·未计入] {hit['code']} {hit['name']}｜{hit['source']} {hit['date']}｜{hit['title'][:60]}")
    if partial:   # 只列出，不拦截：该关键词翻到页数上限仍未越过 since，或被无关文章淹没；其余关键词照常取全
        print(f"新闻未按时间取全的关键词（{len(partial)} 只，其余关键词已取全）："
              + "、".join(f"{members[c] or c}〔{'／'.join(q)}〕" for c, q in sorted(partial.items())))
    if failed:
        print(f"新闻源取数失败 {len(failed)} 只：{'、'.join(members[c] or c for c in failed[:20])}"
              + ("（已按 --allow-news-gaps 继续，报告须列缺口）" if allow_news_gaps else ""))
        return 0 if allow_news_gaps else 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--signal-date", help="筛查：信号日")
    parser.add_argument("--since", help="筛查：上次成功扫描日")
    parser.add_argument("--allow-news-gaps", action="store_true", help="新闻源有公司取数失败时仍继续")
    parser.add_argument("--dispose", metavar="代码", help="处置该代码的待复核行")
    parser.add_argument("--add", metavar="代码", help="登记筛查之外发现的事件")
    parser.add_argument("--detected-on", help="--dispose／--add：登记行的检出日")
    parser.add_argument("--disposition", choices=DISPOSITIONS, help="--dispose：结论")
    parser.add_argument("--note", default="", help="--dispose：复核结论或不构成事件的理由")
    parser.add_argument("--reviewed-at", help="--dispose：处置日，缺省同检出日")
    parser.add_argument("--headline", default="", help="--add：事件标题")
    parser.add_argument("--first-event-date", default="", help="--add：事件首次公开日，缺省同检出日")
    args = parser.parse_args()
    if args.dispose:
        if not (args.detected_on and args.disposition):
            parser.error("--dispose 须同时给 --detected-on 与 --disposition")
        row = dispose(args.dispose, args.detected_on, args.disposition, args.note, args.reviewed_at or args.detected_on)
        print(f"已处置：{row['security_code']} {row['security_name']} {row['detected_on']} → {row['disposition']}")
        return 0
    if args.add:
        if not args.detected_on:
            parser.error("--add 须给 --detected-on")
        row = add(args.add, args.detected_on, args.headline, args.first_event_date)
        print(f"已登记待复核：{row['security_code']} {row['security_name']} {row['detected_on']}｜{row['headline']}")
        return 0
    if not (args.signal_date and args.since):
        parser.error("筛查须给 --signal-date 与 --since")
    return run(args.signal_date, args.since, allow_news_gaps=args.allow_news_gaps)


if __name__ == "__main__":
    raise SystemExit(main())
