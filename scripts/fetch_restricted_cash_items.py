#!/usr/bin/env python3
"""年报受限资产附注中为应付票据质押的现金类抽取（§6.5.1 超额现金口径，OI-219）。

爱玛、格力等靠银行承兑汇票付款的公司把定期存单、票据保证金质押给银行开票：存单计入了超额现金，
其担保的应付票据又按经营负债（垫款）处理，同一笔资金计了两次。本脚本对「应付票据 ≥ 归母权益 × 下限」
的一般企业年报读「所有权或使用权受限资产」附注（缺失时读管理层讨论的「主要资产受限情况」表），
逐行取期末账面价值、受限原因（含「注 N」脚注原文），按用户 2026-09-25 裁定的口径计数：

* 现金类行（货币资金、存单、定期存款、交易性金融资产、债权投资、一年内到期的非流动资产、其他流动资产、
  其他非流动资产等）且原因含票据、承兑、汇票、信用证或保函之一的整行计入（同一行混写借款的也计入）；
  只写借款的不计；其余原因（笼统的「质押」「保证金」、冻结、存款准备金等）另列 `generic_yuan`，不计入。
* 附注三行（其他流动资产、一年内到期的非流动资产、其他非流动资产）只有 `cash_note_items.csv` 核定为现金的部分
  进了超额现金，计入额以该行核定现金为限；其余现金类行以报表行值为限。
* 以当期应付票据封顶在 `roic_inputs` 里做（同一份报表），本表只给 `counted_yuan`。
* 货币资金类行原因笼统时（OI-257，用户 2026-10-05 裁定），改读货币资金附注与「现金和现金等价物」附注列出的受限货币资金分项：
  分项期末值之和须与该行受限额相符；分项名含票据类原因的计入 `fallback_yuan`（并入 `counted_yuan`），混有借款质押保证金的
  先减 `data/reference/restricted_cash_manual.csv` 登记的余额（按筹资活动逐年增减累计人工核定）。
* 财务公司存放中央银行的法定存款准备金（OI-257）记 `reserve_yuan`：取受限分项，没有分项时取货币资金附注写明的期末额，
  不以受限资产表为前提；同一受限行另写票据类原因而整行计入的，先从该行拆出。`roic_inputs` 不计超额现金、不进营运资金。
* 抽取范围另加报表有吸收存款、发放贷款或财务公司利息收入的年报（准备金不受应付票据门槛限制）。

    python3 scripts/fetch_restricted_cash_items.py --plan
    python3 scripts/fetch_restricted_cash_items.py --workers 24        # 定位、下载（与现金附注共用缓存）、解析写表
    python3 scripts/fetch_restricted_cash_items.py --parse-only        # 只用缓存文本重解析
    python3 scripts/fetch_restricted_cash_items.py --codes 603529 --years 2025 --parse-only --show

产物 `data/reference/restricted_cash_items.csv`：逐 (代码, 财年) 一行；`status = ok` 表示逐行期末值之和与附注合计相符，
其余状态不扣（与改前口径相同）。原文按年报原版公告日生效，缓存 `data/raw/annual_reports/` 与 `fetch_cash_note_items.py` 共用。
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_cash_note_items as cn  # noqa: E402

ROOT = cn.ROOT
OUT = ROOT / "data/reference/restricted_cash_items.csv"
CASH_NOTES = cn.OUT
MATERIALITY = 0.02            # 应付票据 ≥ 归母权益 × 2% 才抽取（与现金附注同一门槛）
MANUAL = ROOT / "data/reference/restricted_cash_manual.csv"
FIELDS = ["security_code", "security_name", "fiscal_year", "report_date", "notes_payable", "restricted_total",
          "cash_like_yuan", "counted_yuan", "generic_yuan", "loan_only_yuan", "items", "source", "status",
          "fallback_yuan", "reserve_yuan", "reserve_source", "breakdown_source", "breakdown_items", "loan_pledge_manual_yuan",
          "announcement_date", "title", "url", "extracted_at_utc"]
# 有财务公司迹象的报表字段（OI-257：法定存款准备金不受应付票据门槛限制）
FINANCE_BALANCE_FIELDS = ("ACCEPT_DEPOSIT_INTERBANK", "ACCEPT_DEPOSIT", "LOAN_ADVANCE")
FINANCE_INCOME_FIELD = "INTEREST_INCOME"
INCOME = cn.STMT.parent / "income.csv"
HEADING = re.compile(r"(?:^|\n)[ \t]*(?:(\d{1,3})\s*[、．.]\s*|[（(](?:[一二三四五六七八九十百]+|\d{1,3})[)）]\s*)"
                     r"所\s*有\s*权\s*(?:或\s*使\s*用\s*权\s*)?受\s*(?:到\s*)?限\s*(?:制\s*)?(?:的\s*)?资\s*产")
NONE_STATED = re.compile(r"不存在(?:主要)?资产(?:被查封、扣押、冻结或者?被抵押、质押等)?(?:权利)?受限|无(?:所有权或使用权)?受限(?:制)?(?:的)?资产|不存在所有权或使用权受(?:到)?限(?:制)?")
MDA = re.compile(r"(?:主要资产受限情况|资产权利受限情况|主要资产被查封、扣押、冻结或者被抵押、质押情况)")
# 资产负债表行名与附注常见子项；按长度降序匹配（「其他非流动资产」先于「非流动资产」）
ITEMS = sorted({
    "货币资金", "其他货币资金", "银行存款", "定期存款", "大额存单", "定期存单", "存单", "保证金存款", "银行承兑汇票保证金",
    "交易性金融资产", "以公允价值计量且其变动计入当期损益的金融资产", "债权投资", "其他债权投资", "持有至到期投资",
    "一年内到期的非流动资产", "其他流动资产", "其他非流动资产", "理财产品", "结构性存款", "应收票据", "应收账款",
    "应收款项融资", "预付款项", "其他应收款", "存货", "合同资产", "长期应收款", "长期股权投资", "其他权益工具投资",
    "其他非流动金融资产", "可供出售金融资产", "投资性房地产", "固定资产", "在建工程", "生产性生物资产", "使用权资产",
    "无形资产", "开发支出", "长期待摊费用", "应收利息", "土地使用权", "房屋建筑物", "房屋及建筑物", "机器设备",
    "子公司股权", "股权", "持有待售资产", "发放贷款和垫款", "发放贷款及垫款", "买入返售金融资产", "应收保理款",
    "应收融资租赁款", "一年内到期的长期应收款", "股权投资", "应收票据及应收账款", "应收账款及应收票据", "其他资产",
}, key=len, reverse=True)
CASH_ITEMS = {"货币资金", "其他货币资金", "银行存款", "定期存款", "大额存单", "定期存单", "存单", "保证金存款",
              "银行承兑汇票保证金", "交易性金融资产", "以公允价值计量且其变动计入当期损益的金融资产", "债权投资",
              "其他债权投资", "持有至到期投资", "一年内到期的非流动资产", "其他流动资产", "其他非流动资产",
              "理财产品", "结构性存款"}
NOTE_LINES = {"其他流动资产": "OTHER_CURRENT_ASSET", "一年内到期的非流动资产": "NONCURRENT_ASSET_1YEAR",
              "其他非流动资产": "OTHER_NONCURRENT_ASSET"}
BALANCE_FIELD = {"货币资金": "MONETARYFUNDS", "交易性金融资产": "TRADE_FINASSET",
                 "以公允价值计量且其变动计入当期损益的金融资产": "TRADE_FINASSET",
                 "债权投资": "CREDITOR_INVEST", "其他债权投资": "OTHER_CREDITOR_INVEST", "持有至到期投资": "HOLD_MATURITY_INVEST"}
NOTES_REASON = re.compile(r"票据|承兑|汇票|信用证|保函")
LOAN_REASON = re.compile(r"借款|贷款|授信|融资")
TOLERANCE = 0.005


def finance_income(codes: set[str] | None) -> set[tuple[str, int]]:
    """利润表有财务公司利息收入（`INTEREST_INCOME` > 0）的 (代码, 财年)。"""
    out = set()
    if not INCOME.exists():
        return out
    with INCOME.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            code = row["security_code"].zfill(6)
            if row["REPORT_DATE"][:10].endswith("12-31") and (not codes or code in codes) \
                    and cn._num(row.get(FINANCE_INCOME_FIELD)) > 0:
                out.add((code, int(row["REPORT_DATE"][:4])))
    return out


def plan(codes: set[str] | None, years: set[int] | None) -> list[dict]:
    """(代码, 财年) 清单：一般企业模板年报，应付票据 ≥ 归母权益 × MATERIALITY（应付票据空白即 0），
    或有财务公司迹象（吸收存款、发放贷款或财务公司利息收入，OI-257 法定存款准备金）。"""
    out = []
    finance = finance_income(codes)
    with cn.STMT.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("org_table") != "RPT_F10_FINANCE_GBALANCE" or not row["REPORT_DATE"][:10].endswith("12-31"):
                continue
            code, year = row["security_code"].zfill(6), int(row["REPORT_DATE"][:4])
            if year < cn.FIRST_YEAR or (codes and code not in codes) or (years and year not in years):
                continue
            eq, notes = cn._num(row.get("TOTAL_PARENT_EQUITY")), cn._num(row.get("NOTE_PAYABLE"))
            finance_signal = (code, year) in finance or any(cn._num(row.get(f)) > 0 for f in FINANCE_BALANCE_FIELDS)
            if eq > 0 and (notes >= MATERIALITY * eq or finance_signal):
                balance = {f: cn._num(row.get(f)) for f in set(BALANCE_FIELD.values())}
                out.append(dict(code=code, name=row.get("SECURITY_NAME_ABBR", ""), year=year,
                                report_date=row["REPORT_DATE"][:10], notes_payable=notes, balance=balance))
    return sorted(out, key=lambda r: (r["code"], r["year"]))


def load_note_cash() -> dict[tuple[str, int, str], float]:
    """附注三行中核定为现金类的金额（`cn.VERIFIED`：抽取核定与人工核定），受限额以此为限。"""
    out: dict[tuple[str, int, str], float] = {}
    if CASH_NOTES.exists():
        with CASH_NOTES.open(encoding="utf-8") as handle:
            for r in csv.DictReader(handle):
                if r.get("status") in cn.VERIFIED:
                    out[(r["security_code"], int(r["fiscal_year"]), r["line"])] = cn._num(r.get("cash_like_amount"))
    return out


CASH_TABLE = re.compile(r"(?:(?:受\s*限\s*制|有\s*限\s*制|受\s*到\s*限\s*制)\s*的|不\s*属\s*于\s*现\s*金\s*及\s*现\s*金\s*等\s*价\s*物\s*的)\s*货\s*币\s*资\s*金\s*(?:的)?\s*(?:明\s*细|情\s*况|列\s*示)?\s*(?:如\s*下)?\s*[:：]?")


# 货币资金附注正文里写明金额的开票类保证金（2016 年前常见的散文式披露）：「票据保证金 15,000,000.00 元」
PROSE = re.compile(r"((?:银行)?(?:承兑)?(?:汇票|票据|承兑|信用证|保函)(?:及信用证|、信用证)?保证金)[^\d。；;]{0,16}?"
                   r"(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(万元|元)")


PROSE_AFTER = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(万元|元)[^\d。；;]{0,4}?(?:系|为|是)"
                         r"((?:银行)?(?:承兑)?(?:汇票|票据|承兑|信用证|保函)(?:及信用证|、信用证)?保证金)")


def prose_margins(text: str) -> dict | None:
    """货币资金附注（至下一附注标题）里的开票类保证金逐项求和；同一金额重复出现只计一次。"""
    body = cn.section(text, "货币资金", cn.notes_start(text)) or ""
    stop = re.search(r"\n[ \t]*(?:\d{1,3}\s*[、．.]|[（(][一二三四五六七八九十\d]+[)）])\s*(?:交易性|以公允|应收票据|衍生)", body)
    body = body[:stop.start()] if stop else body
    flat = re.sub(r"\s+", "", body)
    seen, rows = set(), []
    hits = [(m.group(1), m.group(2), m.group(3)) for m in PROSE.finditer(flat)]
    hits += [(m.group(3), m.group(1), m.group(2)) for m in PROSE_AFTER.finditer(flat)]
    for label, amount, unit in hits:
        value = float(amount.replace(",", "")) * (1e4 if unit == "万元" else 1.0)
        if value <= 0 or amount in seen:
            continue
        seen.add(amount)
        rows.append(dict(label="货币资金", value=value, reason=label))
    return dict(status="ok", total=sum(r["value"] for r in rows), rows=rows) if rows else None


def find_section(text: str) -> tuple[str, str] | None:
    """附注「所有权或使用权受限资产」段（至下一序号标题或 6000 字）；无则管理层讨论的受限情况表；
    再无则货币资金附注里「受限制的货币资金明细」小表（2016 年前常见，行名即受限原因）。"""
    start = cn.notes_start(text)
    for m in list(HEADING.finditer(text, start)) + list(HEADING.finditer(text, 0, start)):
        head = text[m.end():m.end() + 400]
        if not re.search(r"项\s*目|单位|期末|受限|账面", head) or re.search(r"^\s*[”\"」]", head):
            continue
        body = text[m.end():m.end() + 6000]
        if m.group(1):
            nxt = re.search(r"\n[ \t]*" + str(int(m.group(1)) + 1) + r"\s*[、．.]\s*[一-龥（(]", body)
            if nxt:
                body = body[:nxt.start()]
        return body, "note"
    for m in MDA.finditer(text):
        body = text[m.end():m.end() + 3000]
        if cn.AMOUNT.search(body[:1500]) and re.search(r"受限原因|原因", body[:600]):
            stop = re.search(r"\n[ \t]*(?:\d\s*[、．.]|[（(][一二三四五六七八九十\d]+[)）])\s*[一-龥]", body[40:])
            return (body[:40 + stop.start()] if stop else body), "mda"
    for m in CASH_TABLE.finditer(text):
        body = text[m.end():m.end() + 1500]
        if re.search(r"期\s*末|年\s*末", body[:200]) and cn.AMOUNT.search(body[:600]):
            # 小表止于合计行、下一序号标题或「上述」说明，不越到下一张表
            stop = re.search(r"合\s*计[^\n]*\n|\n[ \t]*(?:[（(][一二三四五六七八九十\d]+[)）]|\d{1,2}\s*[、．.])|\n[ \t]*上述|\n[ \t]*注", body)
            return (body[:stop.end()] if stop else body[:600]), "cash_note"
    return None


def _clean(body: str) -> str:
    """去页眉页脚（「××年度报告」行、「12 / 198」页码行）与表外说明中的脚注引用标记。"""
    lines = [ln for ln in body.split("\n")
             if not re.search(r"年(?:年度|度)?报告(?:全文)?\s*$|^\s*\d{1,4}\s*/\s*\d{1,4}\s*$", ln.strip())]
    return "\n".join(lines)


def parse_section(body: str, cash_note: bool = False) -> dict:
    """附注表 → 逐行 (行名, 期末账面价值, 原因)；期末值之和须与合计相符。"""
    body = _clean(body)
    unit = cn._unit(body) or 1.0
    foot_at = re.search(r"其他说明|注\s*\d?\s*[:：]", body)
    mode = cn._pattern(body)
    pattern, join = mode
    joined = re.sub(join, "", body)
    values: list[float] = []

    def token(m: re.Match) -> str:
        values.append(float(m.group().replace(",", "")))
        return f"⟦{len(values) - 1}⟧"
    tokenized = pattern.sub(token, joined)
    synthetic = False
    flat = re.sub(r"\s+", "", tokenized)
    if "合计" not in flat and not cash_note:
        # 无「合计」字样的版式（H 股格式）：末尾连续的纯金额行里，取与各行期末值之和相符的那个数作合计（下方校验）
        lines = tokenized.split("\n")
        bare = [i for i, ln in enumerate(lines) if re.fullmatch(r"[\s\-—]*(?:⟦\d+⟧[\s\-—]*)+", ln)]
        run = []
        for i in reversed(bare):
            if run and any(re.search(r"[\u4e00-\u9fa5]", ln) for ln in lines[i + 1:run[-1]]):
                break
            run.append(i)
        if run:
            head = re.sub(r"\s+", "", "\n".join(lines[:min(run)]))
            ids = [t for i in sorted(run) for t in re.findall(r"⟦\d+⟧", lines[i])]
            flat = head + "合计" + "".join(ids)
            synthetic = True
    total_m = re.search(r"合计((?:⟦\d+⟧)+)", flat)
    if not total_m and cash_note:
        flat += "合计" + re.search(r"((?:⟦\d+⟧)+)", flat).group(1) if flat.count("⟦") and len(
            re.findall(r"[\u4e00-\u9fa5]{2,}(?:⟦\d+⟧)+", flat)) == 1 else ""      # 单行小表无合计行：该行即合计
        total_m = re.search(r"合计((?:⟦\d+⟧)+)", flat)
    if not total_m:
        return dict(status="no_total")
    table, after = flat[:total_m.start()], flat[total_m.end():]
    total_vals = [values[int(i)] for i in re.findall(r"⟦(\d+)⟧", total_m.group(1))]
    two_amounts = bool(re.search(r"账面余额.{0,12}账面价值", table[:400]))
    per = 2 if two_amounts else 1
    rows = []
    if cash_note:
        # 行 = 中文行名（即受限原因）+ 金额；首个金额为期末
        for m in re.finditer(r"((?:[\u4e00-\u9fa5、及和与/]|[（(][^（()）⟦]{0,6}[)）]){2,40}?)((?:⟦\d+⟧)+)", table):
            label = m.group(1)
            if re.search(r"项目|期末|年末|年初|期初|余额", label) and not re.search(r"保证金|存款|存单|冻结|质押", label):
                continue
            rows.append(dict(label="货币资金", amounts=[values[int(i)] for i in re.findall(r"⟦(\d+)⟧", m.group(2))],
                             end=m.end(), sub=label.startswith("其中"), cash_reason=label))
    item_re = "|".join(map(re.escape, ITEMS))
    # 行 = 行名紧接金额；行名前面的文字是上一行的原因
    for m in ([] if cash_note else re.finditer(r"(?:其中[:：])?(" + item_re + r")(?:[（(][^⟦）)]{0,20}[)）])?((?:⟦\d+⟧)+)", table)):
        if rows:
            rows[-1]["reason"] = table[rows[-1]["end"]:m.start()]
        rows.append(dict(label=m.group(1), amounts=[values[int(i)] for i in re.findall(r"⟦(\d+)⟧", m.group(2))],
                         end=m.end(), sub=m.group(0).startswith("其中")))
    if not rows:
        return dict(status="no_rows")
    rows[-1]["reason"] = table[rows[-1]["end"]:]
    for r in rows:                                   # 原因里夹的期初金额（新版式）不是原因
        tail = r.get("cash_reason") or r["reason"]
        extra = [values[int(i)] for i in re.findall(r"⟦(\d+)⟧", tail)]
        r["later"], r["raw"] = extra, tail
        r["reason"] = re.sub(r"⟦\d+⟧", " ", tail).strip(" /／-—")
    rows = [r for r in rows if not r["sub"]]
    target = total_vals[per - 1] if len(total_vals) >= per else total_vals[0]

    def end_value(r) -> float:
        return r["amounts"][per - 1] if len(r["amounts"]) >= per else r["amounts"][0]
    vals = [end_value(r) for r in rows]
    if synthetic:                                    # 纯金额行里与期末值之和最接近的数
        target = min(total_vals, key=lambda v: abs(v - sum(vals)))
    tol = max(TOLERANCE * abs(target), 1.0)
    excluded: set[int] = set()
    rescued = False
    if abs(sum(vals) - target) > tol:
        # 只有期初数的行（新版式期末单元格空白）：剔除 1～3 行使期末合计相符
        single = [i for i, r in enumerate(rows) if len(r["amounts"]) <= per and not r["later"]]
        found = None
        for size in (1, 2, 3):
            found = next((c for c in combinations(single, size)
                          if abs(sum(v for j, v in enumerate(vals) if j not in c) - target) <= tol), None)
            if found:
                break
        if found is None:
            # 行名不在词表里的行（「兖煤澳大利亚有限公司净资产」「改制专户的各项资产」）被并进上一行的原因：
            # 原因里「中文 + 金额」的片段逐个当作一行，取 1～4 个使期末合计相符（容差收紧到 0.1%），这些行不作现金类
            embedded = []
            for r in rows:
                for g in re.finditer(r"[\u4e00-\u9fa5][^⟦]{1,60}?((?:⟦\d+⟧)+)", r["raw"]):
                    ids = [int(i) for i in re.findall(r"⟦(\d+)⟧", g.group(1))]
                    embedded.append(values[ids[per - 1]] if len(ids) >= per else values[ids[0]])
            missing, tight = target - sum(vals), max(0.001 * abs(target), 1.0)
            hit = None
            for size in (1, 2, 3, 4):
                hit = next((c for c in combinations(range(len(embedded)), size)
                            if abs(sum(embedded[i] for i in c) - missing) <= tight), None) if len(embedded) <= 40 else None
                if hit:
                    break
            if hit is not None:
                found, rescued = (), True
        if found is None:
            return dict(status="rows_mismatch", total=target * unit,
                        rows=[(r["label"], v * unit, r["reason"][:60]) for r, v in zip(rows, vals)])
        excluded = set(found)
    footnotes = {}
    for fm in re.finditer(r"注(\d+)[:：](.*?)(?=注\d+[:：]|$)", after):
        footnotes[fm.group(1)] = re.sub(r"⟦\d+⟧", " ", fm.group(2))[:600]
    out_rows = []
    for i, (r, v) in enumerate(zip(rows, vals)):
        if i in excluded:
            continue
        reason = r["reason"]
        for ref in re.findall(r"注(\d+)", reason):
            reason += "｜" + footnotes.get(ref, "")
        if not re.search(r"[\u4e00-\u9fa5]", reason):
            # 表内无原因列（原因只写在表后「其他说明」里）：以表后说明为原因
            reason = re.sub(r"⟦\d+⟧", " ", after)[:800]
        out_rows.append(dict(label=r["label"], value=v * unit, reason=reason))
    return dict(status="ok", total=target * unit, rows=out_rows, rescued=rescued)


def classify(rows: list[dict], task: dict, note_cash: dict) -> dict:
    """现金类行按原因分三类；附注三行以核定现金为限，报表行以行值为限。`rows` 另回逐行行名、计数值、类别与原因。"""
    cash_like = counted = generic = loan = 0.0
    items, detail = [], []
    for r in rows:
        if r["label"] not in CASH_ITEMS or r["value"] <= 0:
            continue
        cap = None
        if r["label"] in NOTE_LINES:
            cap = note_cash.get((task["code"], task["year"], NOTE_LINES[r["label"]]), 0.0)
        elif r["label"] in BALANCE_FIELD:
            cap = task["balance"].get(BALANCE_FIELD[r["label"]]) or None
        value = min(r["value"], cap) if cap is not None else r["value"]
        cat = "notes" if NOTES_REASON.search(r["reason"]) else "loan" if LOAN_REASON.search(r["reason"]) else "generic"
        cash_like += value
        counted += value if cat == "notes" else 0.0
        generic += value if cat == "generic" else 0.0
        loan += value if cat == "loan" else 0.0
        items.append(f"{r['label']}:{value:.2f}:{cat}")
        detail.append(dict(label=r["label"], value=value, cat=cat, reason=r["reason"]))
    return dict(cash_like=cash_like, counted=counted, generic=generic, loan=loan, items=";".join(items), rows=detail)


# OI-257：货币资金类行原因笼统时读受限分项（货币资金附注、「现金和现金等价物」附注），与法定存款准备金
MONEY_LABELS = {"货币资金", "其他货币资金", "银行存款", "保证金存款"}
RESERVE = re.compile(r"(?<!超额)(?:法定(?:存款)?(?:准备金|保证金)|存款准备金)(?!率)")
SUB_LOAN = re.compile(r"借款|贷款|融资")
SUB_KEY = re.compile(r"保证金|准备金|存单|定期存款|冻结|受限|质押|专户|担保|基金|专项")
SUB_TOTAL = re.compile(r"合计|小计|总额|使用受到限制|使用权受到限制|受限制的|限制使用|不属于现金|对使用有限制|其中受限制|主要包括")
MONEY_HEAD = re.compile(r"(?:^|\n)[ \t]*(?:注\s*释\s*)?(?:\d{1,3}\s*[、．.]|[（(](?:[一二三四五六七八九十百]+|\d{1,3})[)）])\s*"
                        r"货\s*币\s*资\s*金(?![\u4e00-\u9fa5])")
# 「主要为银行承兑汇票保证金、保函保证金…等，其中受限制资金为 X 元」：泛称的受限资金取前一分句的构成作行名
RESTRICTED_PHRASE = re.compile(r"^(?:其中)?(?:使用)?受(?:到)?限(?:制)?(?:的)?(?:资金|存款|货币资金)$")
PROSE_RESERVE = re.compile(r"存放中央银行[^。；;\d]{0,20}?法定(?:存款)?准备金[^。；;\d]{0,12}?"
                           r"(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+\.\d{1,2})\s*(百万元|万元|千元|元)")
NEXT_NOTE = re.compile(r"\n[ \t]*(?:\d{1,3}\s*[、．.]|[（(](?:[一二三四五六七八九十]+|\d{1,3})[)）])\s*"
                       r"(?:交易性|以公允|衍生|应收票据|应收账款|应收款项融资|结算备付|拆出|预付|买入返售)")
CCE_HEAD = re.compile(r"现\s*金\s*(?:和|及)\s*现\s*金\s*等\s*价\s*物\s*(?:的\s*)?构\s*成|"
                      r"不\s*属\s*于\s*现\s*金\s*及\s*现\s*金\s*等\s*价\s*物\s*的\s*货\s*币\s*资\s*金")
UNIT_SUFFIX = re.compile(r"\s*(百万元|万元|千元|元)")
# 「现金和现金等价物」附注片段止于其后的受限资产表或外币项目（否则受限资产表本身的货币资金行会与受限额自相符）
CCE_STOP = re.compile(r"所\s*有\s*权\s*或\s*使\s*用\s*权|使\s*用\s*权\s*受\s*(?:到\s*)?限\s*(?:制\s*)?的\s*资\s*产|外\s*币\s*货\s*币\s*性\s*项\s*目")
UNITS = {"元": 1.0, "千元": 1e3, "万元": 1e4, "百万元": 1e6}
SUB_TOLERANCE = 0.002        # 分项期末值之和与受限额的容差（或 1 元）


def sub_category(label: str) -> str:
    """受限分项：法定存款准备金 → reserve；含票据类原因 → notes（混写借款的整项计入，借款部分靠人工核定先减）；
    只写借款／贷款／融资 → loan；其余（保证金、冻结、质押存单等）→ generic。"""
    if RESERVE.search(label):
        return "reserve"
    if NOTES_REASON.search(label):
        return "notes"
    return "loan" if SUB_LOAN.search(label) else "generic"


# 表头与原因列的固定词（「项目 期末余额 期初余额」「不属于现金及现金等价物的理由 … 使用权受限」）不是分项名
HEADER_WORDS = re.compile(r"项目|(?:上年)?(?:期末|期初|年末|年初)(?:余额|数|账面价值)?|(?:本期|上期)(?:金额|发生额)|"
                          r"(?:不|仍)属于现金及现金等价物的理由|理由|受限(?:原因|类型|情况)|账面(?:余额|价值)|使用权受限|"
                          r"不可随时支取|单位|币种|人民币|千元|万元|金额|元")
AMOUNT_MODES = {"decimal": (cn.AMOUNT, r"(?<=[\d,.])[ \t]*\n[ \t]*(?=[\d,.])"), "integer": (cn.INTEGER, r"(?<=,)[ \t]*\n[ \t]*(?=\d)")}


def _scrub(region: str) -> str:
    """去页眉页脚、页码行、脚注标记、附注引用与行首序号（千元表的整数模式下它们会被当成金额）。"""
    text = _clean(region)
    text = re.sub(r"(?m)^[ \t]*\d{1,4}[ \t]*$", "", text)
    text = re.sub(r"【\s*注\s*\d*\s*】|\[\s*注\s*\d*\s*\]|[（(]\s*(?:注\s*\d*|[a-zA-Z]{1,2})\s*[)）]", "", text)
    text = re.sub(r"附注[一二三四五六七八九十\d、（）()．.\s]*", "", text)
    return re.sub(r"(?m)^[ \t]*(?:\d{1,2}\s*[、．.](?!\d)|[（(]\d{1,2}[)）]|[①-⑳])", "", text)


def labeled_rows(region: str, mode: str | None = None) -> list[dict]:
    """附注片段 → [行名, 金额列, 显式单位]：长数字断行先拼回，相邻金额归同一行（期末在前）；行名取上一金额之后
    最后一个标点之后的文字，去掉表头词、序号、脚注标记、附注引用与「为」等连接词。`mode` 缺省按 `cn._pattern` 判金额格式。"""
    text = _scrub(region)
    pattern, join = AMOUNT_MODES[mode] if mode else cn._pattern(text)
    joined = re.sub(join, "", text)
    rows: list[dict] = []
    last = 0
    for m in pattern.finditer(joined):
        gap = joined[last:m.start()]
        after = UNIT_SUFFIX.match(joined, m.end())
        last = after.end() if after else m.end()
        value = float(m.group().replace(",", ""))
        if rows and re.fullmatch(r"[\s|/—\-]*", gap):
            rows[-1]["amounts"].append(value)
            continue
        parts = re.split(r"[，。；;,:：！!？?]", re.sub(r"\s+", "", gap))
        label = parts[-1]
        # 上一行以完整分项名收尾（「理由」列重复行名，兖矿 2023）时只取金额所在行的文字；跨行断开的行名（「借款质押\n保证金」）仍取整段
        lines = [x for x in (HEADER_WORDS.sub("", re.split(r"[，。；;,:：！!？?]", re.sub(r"[ \t]+", "", y))[-1])
                             for y in gap.split("\n")[-2:]) if x] if "\n" in gap else []
        restricted_phrase = RESTRICTED_PHRASE.match(re.sub(r"(?:为|约|共计)+$", "", HEADER_WORDS.sub("", label)))
        if len(parts) > 1 and restricted_phrase and (NOTES_REASON.search(parts[-2]) or RESERVE.search(parts[-2])):
            label = parts[-2]
        elif len(lines) == 2 and not restricted_phrase and re.search(r"(?:保证金|准备金|存单|存款|基金|资金|款项)$", lines[0]) \
                and (SUB_KEY.search(lines[1]) or RESERVE.search(lines[1])):
            label = lines[1]
        label = re.split(r"项目(?=期末|期初|年末|年初|本期|上期|账面|金额)", label)[-1]   # 表头「项目 期末数 …」之前是表题
        label = HEADER_WORDS.sub("", label)
        label = re.split(r"明细|如下|包括", label)[-1] or label      # 表题（「受限制的货币资金明细」「主要包括」）不并入首行
        label = re.sub(r"^[、]*(?:其中|减|加)?", "", label)
        label = re.sub(r"(?:为|约|共计)+$", "", label)
        rows.append(dict(label=label, amounts=[value], unit=UNITS[after.group(1)] if after else None))
    return rows


def find_breakdown(rows: list[dict], target: float, unit_hint: float | None) -> dict | None:
    """连续受限分项行（各取期末值）之和与 target 相符（SUB_TOLERANCE 或 1 元）的最长窗口；合计类行跳过，
    非分项行截断窗口。两列表里只有一个金额的行可能是期末空白（只剩期初），至多 3 行按 0 计再试。
    表格行按提示单位（无则依次试元、万元、千元、百万元），散文行按其后写明的单位。"""
    if target <= 0:
        return None
    kinds = ["total" if SUB_TOTAL.search(r["label"]) else "item" if SUB_KEY.search(r["label"]) or RESERVE.search(r["label"])
             else "break" for r in rows]
    tol = max(SUB_TOLERANCE * target, 1.0)
    for unit in [u for u in dict.fromkeys([unit_hint, 1.0, 1e4, 1e3, 1e6]) if u]:
        best: tuple[int, float, list[int], set[int]] | None = None      # (分项数, 偏差, 窗口, 按期末空白计 0 的行)
        for i in range(len(rows)):
            if kinds[i] != "item":
                continue
            picked: list[int] = []
            for j in range(i, len(rows)):
                if kinds[j] == "break":
                    break
                if kinds[j] == "total":
                    continue
                picked.append(j)
                values = {k: rows[k]["amounts"][0] * (rows[k]["unit"] or unit) for k in picked}
                two_col = any(len(rows[k]["amounts"]) >= 2 for k in picked)
                single = [k for k in picked if len(rows[k]["amounts"]) == 1 and not rows[k]["unit"]] if two_col else []
                diff, blank = min(((abs(sum(v for k, v in values.items() if k not in c) - target), set(c))
                                   for size in range(0, min(3, len(single)) + 1) for c in combinations(single, size)),
                                  key=lambda x: (x[0], len(x[1])))
                if diff <= tol:
                    key = (len(picked) - len(blank), -diff)
                    if best is None or key > (best[0], -best[1]):
                        best = (len(picked) - len(blank), diff, list(picked), blank)
        if best:
            _, _, picked, blank = best
            return dict(unit=unit, items=[dict(label=rows[j]["label"], value=rows[j]["amounts"][0] * (rows[j]["unit"] or unit),
                                               cat=sub_category(rows[j]["label"])) for j in picked if j not in blank])
    return None


def cash_note_region(text: str, monetary: float) -> tuple[str, float | None, str | None, bool] | None:
    """货币资金附注（标题至下一报表项目附注）→ (片段, 单位, 金额格式, 是否经报表核对)。先找表内有金额与资产负债表货币资金相符
    （1% 或 100 万元）的一处，以此认位置、单位与金额格式（千元表里夹汇率、利率等两位小数时 `cn._pattern` 会误判为小数格式，
    两种都试）；报表行值已被其后年报重述（兖矿 2019、2022，中材国际 2020）而认不上时，退取附注正文起点后首个带表头的
    货币资金附注，单位只认写明的「单位：」。"""
    start = cn.notes_start(text)
    heads = list(MONEY_HEAD.finditer(text, start)) or list(MONEY_HEAD.finditer(text))
    bodies = []
    for m in heads:
        body = text[m.end():m.end() + 8000]
        stop = NEXT_NOTE.search(body)
        bodies.append(body[:stop.start()] if stop else body[:5000])
    if monetary > 0:
        for body in bodies:
            head = _scrub(body[:3000])
            for mode in ("decimal", "integer"):
                pattern, join = AMOUNT_MODES[mode]
                values = [float(x.replace(",", "")) for x in pattern.findall(re.sub(join, "", head))]
                for unit in dict.fromkeys([cn._unit(body) or 1.0, 1.0, 1e3, 1e4, 1e6]):
                    if any(abs(v * unit - monetary) <= max(0.01 * monetary, 1e6) for v in values):
                        return body, unit, mode, True
    for body in bodies:
        if cn.HEADER.search(body[:300]):
            return body, cn._unit(body), None, False
    return None


def standalone_reserve(regions: list[tuple], monetary: float, text: str = "") -> tuple[float, str]:
    """货币资金附注或「现金和现金等价物」附注写明的法定存款准备金期末额（首个，散文按写明单位、表格按附注单位）；
    附注位置认不出时，取附注正文起点之后首个「存放中央银行…法定存款准备金…X 元」散文。须为正且不超过资产负债表货币资金。"""
    for source, body, unit, mode, validated in regions:
        for r in labeled_rows(body, mode):
            if RESERVE.search(r["label"]) and not SUB_TOTAL.search(r["label"]):
                if not (r["unit"] or validated or cn._unit(body)):
                    continue                                   # 单位不明（报表未核上、也没写「单位：」）不取
                value = r["amounts"][0] * (r["unit"] or unit or 1.0)
                if 0 < value <= monetary * 1.001:
                    return value, source
    if text:
        flat = re.sub(r"\s+", "", text[cn.notes_start(text):])
        m = PROSE_RESERVE.search(flat)
        if m:
            value = float(m.group(1).replace(",", "")) * UNITS[m.group(2)]
            if 0 < value <= monetary * 1.001:
                return value, "prose"
    return 0.0, ""


def cash_note_breakdown(text: str, task: dict, detail: list[dict], generic: float, manual_loan: float) -> dict:
    """OI-257：受限资产表货币资金类行原因笼统时，按受限分项补计票据类保证金（先减人工核定的借款质押余额）；
    法定存款准备金取分项，没有分项时取附注写明的期末额；整行计入的票据类行写明准备金时先拆出。"""
    monetary = task["balance"].get("MONETARYFUNDS") or 0.0
    money = [r for r in detail if r["label"] in MONEY_LABELS]
    g_gen = sum(r["value"] for r in money if r["cat"] == "generic")
    g_all = sum(r["value"] for r in money)
    n_money = sum(r["value"] for r in money if r["cat"] == "notes")
    notes_with_reserve = sum(r["value"] for r in money if r["cat"] == "notes" and RESERVE.search(r["reason"]))
    generic_with_reserve = any(r["cat"] == "generic" and RESERVE.search(r["reason"]) for r in money)
    regions: list[tuple] = []                             # (来源, 片段, 单位, 金额格式, 单位是否经报表核对)
    note = cash_note_region(text, monetary)
    if note:
        regions.append(("cash_note", *note))
    for m in CCE_HEAD.finditer(text):                   # 现金流量表附注可在报表项目注释起点之前（格力 2021、2022）
        body = text[m.end():m.end() + 2500]
        stop = CCE_STOP.search(body)
        body = body[:stop.start()] if stop else body
        regions.append(("cce", body, cn._unit(body) or (note[1] if note and note[3] else None), None, bool(note and note[3])))
    out = dict(fallback=0.0, reserve=0.0, carve=0.0, manual=0.0, reserve_source="", breakdown_source="", breakdown_items="")
    # 受限资产表货币资金类行的原因只写法定存款准备金（茅台 2021）：整行即准备金
    reserve_rows = sum(r["value"] for r in money if r["cat"] == "generic" and RESERVE.search(r["reason"])
                       and not re.search(r"保证金|质押|冻结|存单|定期|借款|贷款|融资|诉讼|其他", RESERVE.sub("", r["reason"])))
    found = None
    if g_gen > 0 or notes_with_reserve > 0:
        for target, scope in ((g_gen, "generic"), (g_all, "all")):
            # 各附注都相符时取泛称（generic）分项最少的一份
            cands = [(source, scope, bd) for source, body, unit, mode, _ in regions
                     if (bd := find_breakdown(labeled_rows(body, mode), target, cn._unit(body) or unit))]
            if cands:
                found = min(cands, key=lambda c: sum(i["value"] for i in c[2]["items"] if i["cat"] == "generic"))
                break
    if found:
        source, scope, bd = found
        notes_sum = sum(i["value"] for i in bd["items"] if i["cat"] == "notes")
        out["manual"] = min(manual_loan, notes_sum)
        notes_net = notes_sum - out["manual"]
        out["fallback"] = notes_net if scope == "generic" else min(max(0.0, notes_net - n_money), g_gen)
        reserve = sum(i["value"] for i in bd["items"] if i["cat"] == "reserve")
        if reserve > 0:
            out["reserve"], out["reserve_source"] = reserve, f"breakdown:{source}"
        out["breakdown_source"] = f"{source}:{scope}"
        out["breakdown_items"] = ";".join(f"{i['label']}:{i['value']:.2f}:{i['cat']}" for i in bd["items"])
    if out["reserve"] <= 0 and reserve_rows > 0:
        out["reserve"], out["reserve_source"] = reserve_rows, "restricted_table"
    if out["reserve"] <= 0:
        out["reserve"], out["reserve_source"] = standalone_reserve(regions, monetary, text)
    if notes_with_reserve > 0 and out["reserve"] > 0 and not (found and found[1] == "generic"):
        out["carve"] = min(out["reserve"], notes_with_reserve)
    in_generic = (found and found[1] == "generic" and out["reserve_source"].startswith("breakdown")) or generic_with_reserve \
        or out["reserve_source"] == "restricted_table"
    out["generic"] = max(0.0, generic - out["fallback"] - (max(0.0, out["reserve"] - out["carve"]) if in_generic else 0.0))
    return out


def load_manual(path: Path | None = None) -> dict[tuple[str, int], float]:
    """`restricted_cash_manual.csv` → {(代码, 财年): 混在票据类保证金里的借款质押保证金余额（元）}（OI-257 人工核定）。"""
    path = path or MANUAL
    out: dict[tuple[str, int], float] = {}
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for r in csv.DictReader(handle):
                out[(r["security_code"].zfill(6), int(r["fiscal_year"]))] = cn._num(r.get("loan_pledge_yuan"))
    return out


def _extra_fields(extra: dict) -> dict:
    return dict(fallback_yuan=f"{extra['fallback']:.2f}", reserve_yuan=f"{extra['reserve']:.2f}",
                reserve_source=extra["reserve_source"], breakdown_source=extra["breakdown_source"],
                breakdown_items=extra["breakdown_items"], loan_pledge_manual_yuan=f"{extra['manual']:.2f}")


def _parse_task_v1(task: dict, meta: dict, note_cash: dict, manual: dict | None = None) -> dict:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    day = re.search(r"finalpage/(\d{4}-\d{2}-\d{2})/", meta.get("url", ""))
    row = dict(security_code=task["code"], security_name=task["name"], fiscal_year=task["year"],
               report_date=task["report_date"], notes_payable=f"{task['notes_payable']:.2f}", extracted_at_utc=stamp,
               announcement_date=day.group(1) if day else meta.get("date", ""), title=meta.get("title", ""),
               url=meta.get("url", ""), counted_yuan="0.00")
    if meta.get("status") != "ok":
        return dict(row, status=meta.get("status", "missing"))
    text = gzip.decompress((cn.CACHE / task["code"] / f"{task['year']}.txt.gz").read_bytes()).decode("utf-8")
    manual_loan = (manual or {}).get((task["code"], task["year"]), 0.0)

    def reserve_only(**fields) -> dict:            # 受限资产表未核定：只取法定存款准备金（不以该表为前提）
        return dict(row, **fields, **_extra_fields(cash_note_breakdown(text, task, [], 0.0, 0.0)))

    def counted(c: dict, **fields) -> dict:
        extra = cash_note_breakdown(text, task, c["rows"], c["generic"], manual_loan)
        return dict(row, **fields, status="ok", cash_like_yuan=f"{c['cash_like']:.2f}",
                    counted_yuan=f"{c['counted'] + extra['fallback'] - extra['carve']:.2f}",
                    generic_yuan=f"{extra['generic']:.2f}", loan_only_yuan=f"{c['loan']:.2f}", items=c["items"],
                    **_extra_fields(extra))
    found = find_section(text)
    if found is None:
        prose = prose_margins(text)
        if prose is not None:
            return counted(classify(prose["rows"], task, note_cash), source="cash_prose", restricted_total=f"{prose['total']:.2f}")
        return reserve_only(status="none_stated" if NONE_STATED.search(re.sub(r"\s+", "", text)) else "section_not_found")
    body, source = found
    if re.match(r"[:：]?(?:□适用)?√?不适用|[:：]?无[。；;]?(?:$|[^\u4e00-\u9fa5])", re.sub(r"\s+", "", body)):
        return reserve_only(source=source, status="none_stated")
    parsed = parse_section(body, cash_note=source == "cash_note")
    if parsed["status"] != "ok":
        return reserve_only(source=source, status=parsed["status"],
                            restricted_total=f"{parsed['total']:.2f}" if parsed.get("total") is not None else "")
    return counted(classify(parsed["rows"], task, note_cash), source=source + ("+rescue" if parsed.get("rescued") else ""),
                   restricted_total=f"{parsed['total']:.2f}")


def parse_task(task: dict, meta: dict, note_cash: dict, manual: dict | None = None, parser: str = "v1") -> dict:
    """一份年报 → 一行结果。`parser = "v1"`（缺省）为原解析；`"v2"`（OI-263）先跑 v1，v1 核定（`status = ok`）的行原样保留，
    其余行再用 v2 版式（`find_section_v2`／`parse_section_v2`）重解析，v2 找到附注段即以其结果为准。"""
    row = _parse_task_v1(task, meta, note_cash, manual)
    if parser == "v1" or row.get("status") == "ok" or meta.get("status") != "ok":
        return row
    v2 = _parse_task_v2(task, meta, note_cash, manual, row)
    return v2 if v2 is not None else row


# ---- v2 版式（OI-263）：「使用权受到限制的资产」标题、千元／万元表（单位写在页眉）、无「合计」字样的表、(a)(b)(c) 字母脚注 ----
PARSERS = ("v1", "v2")
HEADING_V2 = re.compile(r"(?:^|\n)[ \t]*(?:(\d{1,3})\s*[、．.]\s*|[（(]((?:[一二三四五六七八九十百]+|\d{1,3}))[)）]\s*|(\d{1,3})[ \t]+)"
                        r"(?:所\s*有\s*权\s*(?:或\s*)?)?(?:使\s*用\s*权\s*)?受\s*(?:到\s*)?限\s*(?:制\s*)?(?:的\s*)?资\s*产"
                        r"(?![一-龥])(?!\s*[（(]\s*续)")
PAGE_UNIT_V2 = re.compile(r"金\s*额\s*单\s*位\s*(?:为|：|:)?\s*(?:人\s*民\s*币)?\s*(百\s*万\s*元|千\s*元|万\s*元|元)|"
                          r"(?:^|\n)[^\n]{0,24}?人\s*民\s*币\s*(百\s*万\s*元|千\s*元|万\s*元|元)[ \t]*(?=\n)|"
                          r"单\s*位\s*[:：]\s*(?:人\s*民\s*币)?\s*(百\s*万\s*元|千\s*元|万\s*元|元)")
FOOTNOTE_V2 = re.compile(r"(?:^|\n)[ \t]*[（(]\s*([a-zA-Z]|[ivx]{1,4})\s*[)）][ \t]*(.+?)(?=\n[ \t]*[（(]\s*(?:[a-zA-Z]|[ivx]{1,4})\s*[)）]|\n[ \t]*\n[ \t]*\n|$)",
                         re.S)
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
# v2：财务公司与保证金类的货币资金分项行（美的 2015～2017「存放中央银行款项」「存放同业款项」，伊利 2025「存放中央银行法定
# 存款准备金」「担保保证金」）按货币资金计，原行名并入原因（法定存款准备金、票据类保证金由原因判定）
CASH_SUB_V2 = ("存放中央银行法定存款准备金", "存放中央银行法定准备金", "存放中央银行款项", "存放同业款项", "存放同业", "法定存款准备金",
               "已抵押银行存款及其他受限资金", "担保保证金", "期货保证金", "信用证保证金", "保函保证金", "履约保证金", "票据保证金",
               "借款保证金")


SPACES_V2 = "[" + "".join(map(chr, (0x00A0, 0x202F, 0x205F, 0x3000))) + chr(0x2000) + "-" + chr(0x200B) + "]"   # 不换行空格、细空格等


def _v2_unit(body: str, before: str) -> float | None:
    """v2 单位：段内「单位：」优先，其次段首或标题前 4000 字内最近的页眉单位（「金额单位为人民币千元」「人民币千元」）。"""
    for region in (body[:2500], before):
        hits = list(PAGE_UNIT_V2.finditer(region))
        if hits:
            word = next(g for g in hits[-1].groups() if g)
            return UNITS[re.sub(r"\s+", "", word)]
    return None


def _v2_next(number: str) -> re.Pattern:
    """同一版式、序号 + 1 的下一标题（「(26)」→「(27)」，「54.」→「55.」，「（十五）」→「（十六）」）。"""
    if number.isdigit():
        n = int(number) + 1
        return re.compile(r"\n[ \t]*(?:" + str(n) + r"\s*[、．.]|[（(]" + str(n) + r"[)）]|" + str(n) + r"[ \t]+)\s*[一-龥]")
    if "十" in number:
        tens, _, ones = number.partition("十")
        value = (CN_NUM.get(tens, 0) if tens else 1) * 10 + CN_NUM.get(ones, 0)
    else:
        value = CN_NUM.get(number, 0)
    rev = {v: k for k, v in CN_NUM.items()}
    n = value + 1
    word = rev[n] if n < 10 else ("" if n // 10 == 1 else rev[n // 10]) + "十" + (rev[n % 10] if n % 10 else "")
    return re.compile(r"\n[ \t]*[（(]" + word + r"[)）]\s*[一-龥]")


def find_section_v2(text: str) -> tuple[str, str, float | None] | None:
    """v2 附注段：「(所有权或)使用权受(到)限(制)的资产」标题（序号「26、」「(26)」「（二十六）」或事务所版式「26 」），其后 400 字内
    有表头或金额；段止于同一版式的下一序号标题（至多 6000 字）。→ (段文字, 来源, 单位提示)。"""
    start = cn.notes_start(text)
    for m in list(HEADING_V2.finditer(text, start)) + list(HEADING_V2.finditer(text, 0, start)):
        head = text[m.end():m.end() + 400]
        if re.search(r"^\s*[”\"」]", head) or not re.search(r"项\s*目|单位|期末|年末|受限|账面|\d{4}\s*年|\d{1,3}(?:,\d{3})+", head):
            continue
        body = text[m.end():m.end() + 6000]
        number = next((g for g in m.groups() if g), "")
        if number:
            stop = _v2_next(number).search(body)
            if stop:
                body = body[:stop.start()]
        return body, "note", _v2_unit(body, text[max(0, m.start() - 4000):m.start()])
    return None


def parse_section_v2(body: str, unit_hint: float | None, balance: dict) -> dict:
    """v2 受限资产表 → 逐行 (行名, 期末账面价值, 原因)。与 v1 的不同：单位取页眉；行名后的字母脚注「(a)」与「见其他说明（1）」
    按表下同号说明取原因；没有「合计」字样时依次试表末 1～3 个纯金额行作合计（行内金额被 PDF 拆到下一行的版式里，上期数也
    独占一行，美的 2016）；连合计行也没有时，单位写明且各现金类行不超过报表对应行值（v1 容差）即认；说明里写明金额的
    「…保证金 41,849,177.08 元」不当表格行；财务公司与保证金类的货币资金分项（CASH_SUB_V2）按货币资金计。"""
    body = re.sub(SPACES_V2, " ", _clean(body))
    # 事务所版式的页眉（公司名、「××年度财务报表附注」「(除特别注明外，金额单位为人民币千元)」「四 合并财务报表项目附注(续)」）
    body = "\n".join(ln for ln in body.split("\n") if not re.search(
        r"财务报表附注|金额单位为|项目(?:附注|注释)\s*[（(]续[)）]|^\s*[一-龥（）()]{2,30}公司\s*$|^\s*\d{1,4}\s*$", ln))
    body = re.sub(r"((?:19|20)\d{2})\s*年\s*12\s*月\s*31\s*日", r"\1年末", body)
    body = re.sub(r"(?<=\d) ?, ?(?=\d{3}(?![\d]))", ",", body)          # 千分位逗号两侧多出的空格（中兴通讯 2015「106, 892」「79 ,963」）
    body = re.sub(r"\d[\d,]*(?:\.\d+)?\s*(?:万|千)?元(?![一-龥]{0,2}币)", "", body)   # 说明文字里的金额
    # 附注引用（「(附注四(1))」，可断行）里的数字在整数模式下会被当成金额
    body = re.sub(r"[（(]\s*附\s*注[^（()）]{0,20}(?:[（(][^（()）]{0,10}[)）][^（()）]{0,10})?[)）]", "", body)
    foot = re.search(r"\n[ \t]*(?:[（(]\s*[a-zA-Z]\s*[)）][ \t]*[一-龥]|注\s*\d*\s*[:：]|其他说明)", body)
    table, after = (body[:foot.start()], body[foot.start():]) if foot else (body, "")
    # 表内脚注序号（「注1」「见其他说明（1）」）在整数模式下会被当成金额：改写成中文数字
    numeral = "一二三四五六七八九十"
    table = re.sub(r"注\s*(\d)(?![\d,.])", lambda m: "注" + numeral[int(m.group(1)) - 1] if m.group(1) != "0" else m.group(0), table)
    table = re.sub(r"说明\s*[（(]\s*(\d)\s*[)）]", lambda m: "说明（" + (numeral[int(m.group(1)) - 1] if m.group(1) != "0" else "零") + "）", table)
    unit = cn._unit(body) or unit_hint or 1.0
    pattern, join = cn._pattern(table)
    values: list[float] = []

    def token(m: re.Match) -> str:
        values.append(float(m.group().replace(",", "")))
        return f"⟦{len(values) - 1}⟧"
    tokenized = pattern.sub(token, re.sub(join, "", table))
    flat = re.sub(r"\s+", "", tokenized)
    head_end = flat.find("⟦")
    if re.search(r"本(?:年|期)增加.{0,12}本(?:年|期)减少", flat[:max(head_end, 0) + 1]):
        return dict(status="movement_table")                  # 年初、增加、减少、年末的变动表（华润三九 2008、2009）不认
    per = 2 if re.search(r"账面余额.{0,12}账面价值", flat[:max(head_end, 0) + 1]) else 1
    item_re = "|".join(map(re.escape, sorted(set(ITEMS) | set(CASH_SUB_V2), key=len, reverse=True)))

    def end_value(r: dict) -> float:
        return r["amounts"][per - 1] if len(r["amounts"]) >= per else r["amounts"][0]

    def rows_of(part: str) -> list[dict]:
        rows: list[dict] = []
        for m in re.finditer(r"(?:其中[:：])?(" + item_re + r")(?:[-—–][一-龥]{1,10})?((?:[（(][^⟦）)]{0,20}[)）])?)[-—–]*"
                             r"((?:⟦\d+⟧)+)", part):
            if rows:
                rows[-1]["reason"] = part[rows[-1]["end"]:m.start()]
            rows.append(dict(label=m.group(1), ref=re.sub(r"[（()）\s]", "", m.group(2) or ""), end=m.end(),
                             amounts=[values[int(i)] for i in re.findall(r"⟦(\d+)⟧", m.group(3))],
                             sub=m.group(0).startswith("其中")))
        if rows:
            rows[-1]["reason"] = part[rows[-1]["end"]:]
        for r in rows:
            r["reason"] = re.sub(r"⟦\d+⟧", " ", r["reason"]).strip(" /／-—")
        return rows

    def reconcile(rows: list[dict], total_vals: list[float], synthetic: bool) -> dict:
        """逐行期末值之和与合计相符：先去掉「其中」行，母项本身没有金额（美的 2019「货币资金 / 其中：银行存款」）对不上时
        保留；两种都可剔除 0～3 行只有期初数的行（精确相符优先，否则须在 v1 容差内）。"""
        target = total_vals[per - 1] if len(total_vals) >= per else total_vals[0]
        tol = max(TOLERANCE * abs(target), 1.0)
        if synthetic and len(total_vals) not in (per, 2 * per):
            return dict(status="rows_mismatch", total=target * unit, rows=[])   # 纯金额行个数与表的列数不符
        exact = max(1.0, 1e-6 * abs(target))
        variants = [[r for r in rows if not r["sub"]]] + ([rows] if any(r["sub"] for r in rows) else [])
        fallback = None
        for cand in variants:
            vals = [end_value(r) for r in cand]
            single = [i for i, r in enumerate(cand) if len(r["amounts"]) <= per]
            options = [(abs(sum(v for j, v in enumerate(vals) if j not in c) - target), len(c), c)
                       for size in (0, 1, 2, 3) for c in combinations(single, size)][:5000]
            err, _, best = min(options, key=lambda x: (x[0] > exact, x[0], x[1]))
            if err <= tol:
                keep = [i for i in range(len(cand)) if i not in best]
                return dict(status="ok", total=target, rows=[cand[i] for i in keep], vals=[vals[i] for i in keep], note="")
            fallback = fallback or dict(status="rows_mismatch", total=target * unit,
                                        rows=[(r["label"], v * unit, r["reason"][:60]) for r, v in zip(cand, vals)])
        return fallback

    result = None
    labeled = re.search(r"合计((?:⟦\d+⟧)+)", flat)
    if labeled:
        rows = rows_of(flat[:labeled.start()])
        if not rows:
            return dict(status="no_rows")
        result = reconcile(rows, [values[int(i)] for i in re.findall(r"⟦(\d+)⟧", labeled.group(1))], False)
    else:
        # 表末纯金额行作合计：自最后一行起取 1～3 行（中间可隔空行），取首个逐行相符的切法
        lines = tokenized.split("\n")
        bare = [i for i, ln in enumerate(lines) if re.fullmatch(r"[\s\-—–]*(?:⟦\d+⟧[\s\-—–]*)+", ln)]
        if bare and not any(re.search(r"[一-龥]", ln) for ln in lines[bare[-1] + 1:]):
            run = [bare[-1]]
            for k in reversed(bare[:-1]):
                if len(run) == 3 or any(ln.strip() for ln in lines[k + 1:run[-1]]):
                    break
                run.append(k)
            for size in range(1, len(run) + 1):
                first = run[size - 1]
                rows = rows_of(re.sub(r"\s+", "", "\n".join(lines[:first])))
                if not rows:
                    continue
                total_vals = [values[int(t)] for k in sorted(run[:size]) for t in re.findall(r"⟦(\d+)⟧", lines[k])]
                attempt = reconcile(rows, total_vals, True)
                if attempt["status"] == "ok":
                    result = attempt
                    break
                result = result or attempt
        if result is None:
            # 没有合计行：单位写明、各现金类行不超过资产负债表对应行（v1 容差），且至少有一行现金类可核对
            rows = [r for r in rows_of(flat) if not r["sub"]]
            if not rows:
                return dict(status="no_rows")
            if any(len(r["amounts"]) > 2 * per for r in rows):
                return dict(status="no_total")                # 列数多于两期（变动表等）时无合计行无从核对
            vals = [end_value(r) for r in rows]
            per_field: dict[str, float] = {}
            for r, v in zip(rows, vals):
                field = BALANCE_FIELD.get("货币资金" if r["label"] in CASH_SUB_V2 else r["label"])
                if field and balance.get(field):
                    per_field[field] = per_field.get(field, 0.0) + v * unit
            if any(total > balance[field] * (1 + TOLERANCE) + 1.0 for field, total in per_field.items()):
                return dict(status="exceeds_balance", total=None)    # 同一报表行的受限额合计不得超过该行
            checked = len(per_field)
            if not checked or not (cn._unit(body) or unit_hint):
                return dict(status="no_total")
            result = dict(status="ok", total=sum(vals), rows=rows, vals=vals, note="nototal")
    if result["status"] != "ok":
        return result
    notes = {m.group(1).lower(): re.sub(r"\s+", "", m.group(2))[:600] for m in FOOTNOTE_V2.finditer(after)}
    notes.update({m.group(1): re.sub(r"\s+", "", m.group(2))[:600] for m in re.finditer(
        r"(?:^|\n)[ \t]*[（(]\s*(\d{1,2})\s*[)）][ \t]*(.+?)(?=\n[ \t]*[（(]\s*\d{1,2}\s*[)）]|$)", after, re.S)})
    numbered = {m.group(1): re.sub(r"⟦\d+⟧|\s+", "", m.group(2))[:600]
                for m in re.finditer(r"注\s*(\d+)\s*[:：](.*?)(?=注\s*\d+\s*[:：]|$)", after, re.S)}
    out_rows = []
    for r, v in zip(result["rows"], result["vals"]):
        reason = r["reason"]
        if r["ref"] and r["ref"].lower() in notes:
            reason += "｜" + notes[r["ref"].lower()]
        for ref in re.findall(r"说明\s*[（(]\s*([一二三四五六七八九十])\s*[)）]", reason):      # 「见“其他说明（1）”」
            reason += "｜" + notes.get(str(numeral.index(ref) + 1), "")
        for ref in re.findall(r"注([一二三四五六七八九十])", reason):
            reason += "｜" + numbered.get(str(numeral.index(ref) + 1), "")
        if not re.search(r"[一-龥]", reason) and not notes:
            reason = re.sub(r"⟦\d+⟧|\s+", "", after)[:800]          # 表内无原因列、也没有逐行脚注：以表后说明为原因
        label = r["label"]
        if label in CASH_SUB_V2:
            label, reason = "货币资金", label + "｜" + reason
        out_rows.append(dict(label=label, value=v * unit, reason=reason))
    return dict(status="ok", total=result["total"] * unit, rows=out_rows, note=result["note"], unit=unit)


def _parse_task_v2(task: dict, meta: dict, note_cash: dict, manual: dict | None, v1_row: dict) -> dict | None:
    """v2 重解析（只在 v1 未核定时调用）：找不到 v2 附注段返回 None（沿用 v1 结果）。"""
    text = gzip.decompress((cn.CACHE / task["code"] / f"{task['year']}.txt.gz").read_bytes()).decode("utf-8")
    keep = {k: v1_row[k] for k in ("security_code", "security_name", "fiscal_year", "report_date", "notes_payable",
                                   "extracted_at_utc", "announcement_date", "title", "url")}
    row = dict(keep, counted_yuan="0.00")
    if text.count("的") < 400:                         # 文本层无字符映射或只抽出几页（天山铝业 2025）
        return dict(v1_row, status="text_unreadable")
    found = find_section_v2(text)
    if found is None:
        if re.search(r"(?:主要资产受限情况|资产权利受限情况)[^\n]{0,4}\n?[\s□]*(?:适用)?[\s]*√\s*不适用", text):
            return dict(row, source="v2:mda", status="none_stated",           # 管理层讨论写明不适用（中国巨石 2025）
                        **_extra_fields(cash_note_breakdown(text, task, [], 0.0, 0.0)))
        return None
    body, source, unit_hint = found
    manual_loan = (manual or {}).get((task["code"], task["year"]), 0.0)
    if re.match(r"[:：]?(?:□适用)?√?不适用|[:：]?无[。；;]?(?:$|[^一-龥])", re.sub(r"\s+", "", body)):
        return dict(row, source="v2:" + source, status="none_stated",
                    **_extra_fields(cash_note_breakdown(text, task, [], 0.0, 0.0)))
    parsed = parse_section_v2(body, unit_hint, task["balance"])
    if parsed["status"] != "ok":
        return dict(row, source="v2:" + source, status=parsed["status"],
                    restricted_total=f"{parsed['total']:.2f}" if parsed.get("total") is not None else "",
                    **_extra_fields(cash_note_breakdown(text, task, [], 0.0, 0.0)))
    c = classify(parsed["rows"], task, note_cash)
    extra = cash_note_breakdown(text, task, c["rows"], c["generic"], manual_loan)
    return dict(row, source="v2:" + source + ("+" + parsed["note"] if parsed.get("note") else ""), status="ok",
                restricted_total=f"{parsed['total']:.2f}", cash_like_yuan=f"{c['cash_like']:.2f}",
                counted_yuan=f"{c['counted'] + extra['fallback'] - extra['carve']:.2f}",
                generic_yuan=f"{extra['generic']:.2f}", loan_only_yuan=f"{c['loan']:.2f}", items=c["items"],
                **_extra_fields(extra))


def load_existing(path: Path | None = None) -> dict[tuple[str, int], dict]:
    path = path or OUT
    out = {}
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for r in csv.DictReader(handle):
                out[(r["security_code"], int(r["fiscal_year"]))] = r
    return out


def write(merged: dict, path: Path | None = None) -> None:
    path = path or OUT
    rows = sorted(merged.values(), key=lambda r: (r["security_code"], int(r["fiscal_year"])))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--codes", help="逗号分隔")
    parser.add_argument("--years", help="逗号分隔财年")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="重下原文")
    parser.add_argument("--parse-only", action="store_true", help="只用已缓存文本解析，不联网")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--show", action="store_true", help="打印逐行解析结果（调试）")
    parser.add_argument("--parser", choices=PARSERS, default="v1",
                        help="v2（生产，§6.7 第 1 步）：v1 未核定的行再按 OI-263 新版式重解析；v1（缺省）只作复现")
    parser.add_argument("--out", type=Path, default=OUT, help="输出表（缺省生产表）")
    args = parser.parse_args()
    codes = {c.strip().zfill(6) for c in args.codes.split(",")} if args.codes else None
    years = {int(y) for y in args.years.split(",")} if args.years else None
    tasks = plan(codes, years)
    print(f"清单 {len(tasks)} 份年报（{len({t['code'] for t in tasks})} 家）", flush=True)
    if args.plan:
        return 0
    metas: dict[tuple[str, int], dict] = {}
    if not args.parse_only:
        orgs_path = cn.CACHE / "orgid.json"
        orgs = json.loads(orgs_path.read_text()) if orgs_path.exists() else {}
        for code in sorted({t["code"] for t in tasks}):
            try:
                cn.org_id(code, orgs)
            except Exception as exc:                          # noqa: BLE001
                print(f"  ⚠ {code} orgId 失败：{exc}", flush=True)
        orgs_path.write_text(json.dumps(orgs, ensure_ascii=False, indent=0))
        todo = [t for t in tasks if t["code"] in orgs]
        for i, t in enumerate(todo, 1):                      # 串行定位（检索接口限流）
            before = (cn.CACHE / t["code"] / f"{t['year']}.json").exists()
            metas[(t["code"], t["year"])] = cn.locate(t, orgs, args.refresh)
            if not before:
                time.sleep(0.3)
            if i % 200 == 0 or i == len(todo):
                print(f"  定位 {i}/{len(todo)}", flush=True)
        pending = [t for t in todo if metas[(t["code"], t["year"])].get("status") == "located"
                   or (args.refresh and metas[(t["code"], t["year"])].get("status") == "ok")]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(cn.fetch_report, t, metas[(t["code"], t["year"])], args.refresh): t for t in pending}
            for i, fut in enumerate(as_completed(futures), 1):
                t = futures[fut]
                metas[(t["code"], t["year"])] = fut.result()
                if i % 100 == 0 or i == len(pending):
                    print(f"  下载 {i}/{len(pending)}", flush=True)
    for t in tasks:
        path = cn.CACHE / t["code"] / f"{t['year']}.json"
        if (t["code"], t["year"]) not in metas:
            metas[(t["code"], t["year"])] = json.loads(path.read_text()) if path.exists() else dict(status="not_fetched")
    note_cash, manual = load_note_cash(), load_manual()
    results = {}
    for t in tasks:
        meta = metas[(t["code"], t["year"])]
        results[(t["code"], t["year"])] = parse_task(t, meta, note_cash, manual, args.parser)
        if args.show and meta.get("status") == "ok":
            text = gzip.decompress((cn.CACHE / t["code"] / f"{t['year']}.txt.gz").read_bytes()).decode("utf-8")
            found = find_section(text)
            print(t["code"], t["year"], json.dumps(parse_section(found[0], found[1] == "cash_note") if found else None,
                                                   ensure_ascii=False, indent=1))
            r = results[(t["code"], t["year"])]
            print("  受限分项", {k: r.get(k) for k in ("counted_yuan", "fallback_yuan", "reserve_yuan", "reserve_source",
                                                   "breakdown_source", "breakdown_items", "loan_pledge_manual_yuan")})
    merged = {**load_existing(args.out), **results}
    write(merged, args.out)
    stats: dict[str, int] = {}
    for r in results.values():
        key = (r.get("status") or "").split(":")[0]
        stats[key] = stats.get(key, 0) + 1
    ok = [r for r in results.values() if r.get("status") == "ok"]
    print(f"状态：{stats}")
    print(f"核定 {len(ok)} 份：计入 {sum(cn._num(r['counted_yuan']) for r in ok) / 1e8:.1f} 亿"
          f"（其中受限分项补计 {sum(cn._num(r.get('fallback_yuan')) for r in ok) / 1e8:.1f} 亿），"
          f"笼统原因 {sum(cn._num(r['generic_yuan']) for r in ok) / 1e8:.1f} 亿，只写借款 {sum(cn._num(r['loan_only_yuan']) for r in ok) / 1e8:.1f} 亿")
    reserve = [r for r in results.values() if cn._num(r.get("reserve_yuan")) > 0]
    print(f"法定存款准备金 {len(reserve)} 份（{len({r['security_code'] for r in reserve})} 家）"
          f"{sum(cn._num(r['reserve_yuan']) for r in reserve) / 1e8:.1f} 亿")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
