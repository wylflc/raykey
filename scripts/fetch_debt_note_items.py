#!/usr/bin/env python3
"""年报附注中记在其他流动负债、其他应付款与预计负债里的类债务项目抽取（§6.5.1 第 3 条股权桥，OI-261）。

东财三大报表没有单列短期应付债券／超短期融资券（记在其他流动负债）、其他应付款中的借款与资金拆借、预计负债中的
弃置／复垦义务，`roic_inputs.DEBT_FIELDS`／`FIN_LIAB_FIELDS` 读不到。本脚本对一般企业年报中「该行 ≥ 归母权益 × 2%」的
三行逐份读附注表（原文与 `fetch_cash_note_items.py` 共用缓存，按年报原版公告日生效）：

* 其他流动负债：短期应付债券、短期融资券、超短期融资券、可转换债券等债务工具（kind = bond）与明写的借款、质押式回购
  借入资金（kind = loan）计入；供应链融资、保理、票据融资、融资租赁款、贵金属租借、已贴现未到期（带追索权、未终止确认）
  的票据等融资安排另列 `review_amount`（用户 2026-10-06 裁定一并计入有息负债）；待转销项税额、预计退货、销售返利、
  已背书未终止确认的票据等经营项不计，标签写「背书或贴现」的按背书计（多照抄附注模板，以背书为主）。
* 其他应付款：「按款项性质列示」表中的借款、资金拆借、拆借款、企业借款及利息计入（kind = loan）；押金保证金、往来款、
  工程设备款、股权收购款、只写利息的应计利息等不计；财务公司吸收存款、反向保理等列 `review_amount`（裁定计入）；同一行混写借款与
  其他性质的（「借款及往来款」「暂收暂借款」）整份判 `ambiguous`、不计入。2018 年起的两级版式（应付利息、应付股利、
  其他应付款）以一级表合计核对报表行，性质表合计须与一级表的其他应付款行相符；2018 年前直接以性质表核对。
* 预计负债：弃置费用、弃置义务、复垦、环境恢复、矿山地质环境治理、垃圾填埋场封场类计入（kind = decom）；表内「减：一年内
  到期」行已转入一年内到期的非流动负债（已进有息负债），先从计入额中扣除；港式转置变动表取「长期部分」行；产品质量保证、
  未决诉讼、担保、亏损合同等不计。

版式：上交所／深交所模板、事务所版式（序号后只跟空格、合计行只有数字、单位写在页眉「金额单位为人民币千元」）、港式
（百万元、括号负数、日期作表头），两列表的空白单元格按期末、期初两列合计同时相符求解，表头写反时以与报表行相符的列为期末。

判定（`status = ok`）：附注合计与报表行值相差 ≤ 5%（或 100 万元，同 `fetch_cash_note_items.TOTAL_TOLERANCE`），逐行期末值之和
与合计相符（单元格空白的行按期末、期初两列合计同时相符求解），且计入类的行没有混写其他性质。其余状态不计入。原文无法
抽取的（文本层无字符映射、版式无法解析）按原文人工核定，登记 `MANUAL`（逐行记来源、页码与依据），写表时覆盖同一
(代码, 财年, 行)（`status = manual`），报表行值其后变动超出同一容差即记 `manual_stale`、不计入。

    python3 scripts/fetch_debt_note_items.py --plan                     # 只列清单规模
    python3 scripts/fetch_debt_note_items.py --pool --workers 6         # 定位、下载（只下缺的）、解析写表
    python3 scripts/fetch_debt_note_items.py --parse-only               # 只用缓存文本重解析
    python3 scripts/fetch_debt_note_items.py --codes 600887 --years 2025 --parse-only --show
    python3 scripts/fetch_debt_note_items.py --funds                     # 弃置专项资金（不联网，读 --out 表）

产物：`data/reference/debt_note_items.csv`（§6.5.1 第 3 条，建带 `--note-debt notes` 读），逐 (代码, 财年, 行) 一行；人工核定表 `data/reference/debt_note_manual.csv`；
`--funds` 另写 `decom_fund_items.csv`：弃置类计入额 > 0 的 (代码, 财年) 逐资产行查弃置专户、矿山地质环境治理恢复基金等
专项资金（用户 2026-10-06 裁定：报表现金行之外的计超额现金对冲，`counts_as_excess_cash = 1`；货币资金里的只列出备查）。
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
from itertools import combinations, product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_cash_note_items as cn  # noqa: E402

ROOT = cn.ROOT
OUT = ROOT / "data/reference/debt_note_items.csv"
MANUAL = ROOT / "data/reference/debt_note_manual.csv"
POOL = ROOT / "data/processed/a_share_core_valuation_pool.csv"
VERIFIED = ("ok", "manual")          # 计入股权桥的状态
MATERIALITY = 0.02                   # 该行 ≥ 归母权益 × 2% 才抽取（与附注现金类、受限资产同一门槛）
TOTAL_TOLERANCE = cn.TOTAL_TOLERANCE
LINES = {"OTHER_CURRENT_LIAB": "其他流动负债", "OTHER_PAYABLE": "其他应付款", "PREDICT_LIAB": "预计负债"}
FIELDS = ["security_code", "security_name", "fiscal_year", "report_date", "line", "line_label", "statement_amount",
          "notes_total", "breakdown_total", "counted_amount", "counted_kind", "counted_items", "deducted_amount",
          "review_amount", "review_items", "items", "unit", "status", "announcement_date", "title", "url",
          "extracted_at_utc"]
MANUAL_FIELDS = ["security_code", "security_name", "fiscal_year", "report_date", "line", "line_label", "statement_amount",
                 "notes_total", "counted_amount", "counted_kind", "counted_items", "review_amount", "review_items", "unit",
                 "source_date", "source_title", "source_url", "source_page", "basis", "registered_at"]

# ---- 分类词表（逐行标签；同一窗口内按规则顺序判定，首个命中的类别定类） -------------------------------------
# 其他流动负债：债务工具（短期应付债券、短融、超短融、中期票据、资产支持证券／票据等）与明写的借款（含质押式回购借入资金）
BOND_KEYS = ("融资券", "短融", "超短融", "债券", "公司债", "企业债", "中期票据", "债务融资工具", "定向工具",
             "资产支持证券", "资产支持票据", "资产证券化")
OCL_LOAN_KEYS = ("借款", "借入", "贷款", "拆借", "拆入", "统借统还", "贸易融资")
# 融资安排（另列 review_amount；用户 2026-10-06 裁定一并计入有息负债）：供应链融资、保理、票据融资、融资租赁、贵金属租借、
# 已贴现的信用证、财务公司吸收存款等
REVIEW_KEYS = ("供应链融资", "保理", "票据融资", "融资款", "融资租赁", "售后回租", "租借", "信用证", "资金池", "资金归集",
               "资金集中", "集中管理", "财务公司存款", "财务公司吸收", "吸收存款", "吸收成员")
REVIEW_NOT = ("保证金", "押金", "承兑汇票", "费")    # 融资租赁保证金、已背书的财务公司承兑汇票、应付保理费等不是融资本金
OCL_OTHER_KEYS = ("销项税", "增值税", "税金", "税额", "税款", "退货", "退回", "返利", "返点", "折扣", "折让", "质量", "质保",
                  "保修", "三包", "维修", "修理", "预提", "预计", "费用", "费", "准备金", "保证金", "票据", "汇票", "承兑",
                  "背书", "贴现", "债权凭证", "股利", "认购款", "意向金", "递延收益", "政府", "扶持", "补助", "套期", "合同负债",
                  "待结转", "待转", "预收", "回购权", "监管商品", "利息", "往来", "备付金", "继续涉入", "其他", "股权")
# 其他应付款：借款类；与借款混写时使整行性质不明的词（「借款及往来款」「暂收暂借款」）
LOAN_KEYS = ("借款", "拆借", "拆入", "借入", "暂借", "委托贷款", "统借统还", "贷款")
# 只写利息的行（应付利息分表的「短期借款应付利息」「分期付息到期还本的长期借款利息」）是已计入借款的应计利息，不是借款本身
INTEREST_ONLY = re.compile(r"利息")
INTEREST_WITH_PRINCIPAL = re.compile(r"(?:及|和|与|、)利息|本息|本金")
LOAN_HELPERS = ("利息", "资金", "款项", "本金", "及", "和", "与", "、", "向", "企业", "单位", "关联方", "关联", "股东", "个人",
                "非金融机构", "集团", "公司", "内部", "银行", "少数", "子公司", "第三方", "应付", "其他", "财政", "政府",
                "之间的", "的")
LOAN_MIX_KEYS = ("往来", "保证金", "押金", "工程", "设备", "股权", "收购", "转让", "费用", "代收", "代付", "暂收", "垫",
                 "运费", "广告", "租金", "质保", "风险金", "货款", "购置", "补偿", "奖励", "分红", "股利", "代扣", "代缴",
                 "代理", "预提", "应付款项", "备用金", "借支", "报销")
OP_OTHER_KEYS = LOAN_MIX_KEYS + ("其他", "限制性股票", "回购义务", "认购款", "利息", "税", "费", "款", "金")
# 预计负债：弃置、复垦、环境恢复类（含垃圾填埋场封场、租赁资产复原）；与其他性质混写的整行性质不明
DECOM_KEYS = ("弃置", "复垦", "环境恢复", "环境治理", "恢复治理", "治理恢复", "地质环境", "生态恢复", "生态修复", "环境修复",
              "闭坑", "闭矿", "关闭", "拆除", "清理义务", "环境清理", "矿山环境", "退役", "复原", "恢复费", "封场")
DECOM_MIX_KEYS = ("质量", "保修", "售后", "维修", "三包", "诉讼", "仲裁", "担保", "亏损合同", "待执行", "重组", "退货", "赔偿",
                  "罚", "安置", "辞退", "补偿", "保证", "索赔", "违约", "或有对价", "回购", "返利", "其他", "危废")
PL_OTHER_KEYS = DECOM_MIX_KEYS + ("税", "合同", "折扣", "费", "损失")       # 「义务」「准备」常是断行后的末段，不作定类词
RULES = {
    "OTHER_CURRENT_LIAB": (("bond", BOND_KEYS, ("销项税", "增值税", "退货", "返利", "票据", "汇票", "保证金", "预提", "股利")),
                           ("loan", OCL_LOAN_KEYS, ("往来", "保证金", "押金", "票据", "汇票", "费用", "股利")),
                           ("review", REVIEW_KEYS, REVIEW_NOT), ("other", OCL_OTHER_KEYS, ())),
    "OTHER_PAYABLE": (("loan", LOAN_KEYS, LOAN_MIX_KEYS), ("review", REVIEW_KEYS, REVIEW_NOT), ("other", OP_OTHER_KEYS, ())),
    "PREDICT_LIAB": (("decom", DECOM_KEYS, tuple(k for k in DECOM_MIX_KEYS)), ("other", PL_OTHER_KEYS, ())),
}
COUNTED = {"OTHER_CURRENT_LIAB": ("bond", "loan"), "OTHER_PAYABLE": ("loan",), "PREDICT_LIAB": ("decom",)}
# 已贴现未到期（带追索权、未终止确认）的票据、电子债权凭证是融资（用户 2026-10-06 裁定），列 review；「贴现利息」「贴现率」等不是本金，
# 同一标签写「背书或贴现」的按背书（与应付票据同属经营负债）
DISCOUNTED = re.compile(r"贴\s*现(?!\s*(?:率|利息|息|费|损失|收益))")
DISCOUNTED_NOT = ("背书", "保证金", "押金")
KIND = {line: "+".join(kinds) for line, kinds in COUNTED.items()}
DEDUCT = re.compile(r"^\s*(?:减\s*[:：]|减\s*一年|一年内到期|其中\s*[:：]?\s*一年内到期)")

CURRENT_WORDS = re.compile(r"(?<![上])(?:期\s*末|年\s*末|本\s*期\s*末|本\s*年\s*末)")
PRIOR_WORDS = re.compile(r"期\s*初|年\s*初|上\s*年\s*(?:年\s*)?末|上\s*期\s*末")
MOVEMENT_WORDS = re.compile(r"本\s*(?:期|年)\s*(?:增\s*加|计\s*提|减\s*少)|增\s*加\s*额|减\s*少\s*额")
TOTAL_ROW = re.compile(r"(?m)^[ \t]*(?:[\u4e00-\u9fa5]{2,12}?)?(?:合\s*计|总\s*计)(?![\u4e00-\u9fa5])")   # 「合计」「其他应付款合计」
NUMBER = re.compile(r"\(\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s*\)")          # 港式括号负数「(1,138)」


def _num(text) -> float:
    return cn._num(text)


# ---- 清单 ---------------------------------------------------------------------------------------------
def pool_codes() -> set[str]:
    with POOL.open(encoding="utf-8-sig") as handle:
        return {r["security_code"].zfill(6) for r in csv.DictReader(handle)}


def statement_lines(row: dict) -> dict[str, float]:
    """三行报表值：其他应付款取「其他应付款」子行（2018 年前版式与过渡年东财单列 `OTHER_PAYABLE`），缺失时取合计行
    `TOTAL_OTHER_PAYABLE`（2018 年起含应付利息、应付股利）。"""
    other_payable = _num(row.get("OTHER_PAYABLE")) or _num(row.get("TOTAL_OTHER_PAYABLE"))
    return {"OTHER_CURRENT_LIAB": _num(row.get("OTHER_CURRENT_LIAB")), "OTHER_PAYABLE": other_payable,
            "PREDICT_LIAB": _num(row.get("PREDICT_LIAB"))}


def plan(codes: set[str] | None, years: set[int] | None) -> list[dict]:
    """(代码, 财年) 待抽取清单：一般企业模板年报，三行中至少一行 ≥ 归母权益 × MATERIALITY（只抽达标的行）。"""
    out = []
    with cn.STMT.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("org_table") != "RPT_F10_FINANCE_GBALANCE" or not row["REPORT_DATE"][:10].endswith("12-31"):
                continue
            code, year = row["security_code"].zfill(6), int(row["REPORT_DATE"][:4])
            if year < cn.FIRST_YEAR or (codes and code not in codes) or (years and year not in years):
                continue
            eq = _num(row.get("TOTAL_PARENT_EQUITY"))
            lines = {k: v for k, v in statement_lines(row).items() if eq > 0 and v >= MATERIALITY * eq}
            if lines:
                out.append(dict(code=code, name=row.get("SECURITY_NAME_ABBR", ""), year=year,
                                report_date=row["REPORT_DATE"][:10], lines=lines, parent_equity=eq,
                                total_other_payable=_num(row.get("TOTAL_OTHER_PAYABLE")),
                                interest_payable=_num(row.get("INTEREST_PAYABLE")),
                                dividend_payable=_num(row.get("DIVIDEND_PAYABLE"))))
    return sorted(out, key=lambda r: (r["code"], r["year"]))


# ---- 文本预处理 ------------------------------------------------------------------------------------------
def readable(text: str) -> bool:
    """文本层可读：常用字「的」出现足够多次（完整年报在 900 次以上；无字符映射的 PDF 抽出的是乱码——中国海油、天山铝业
    2025——或只抽出几页，陕西煤业 2021、2024）。"""
    return text.count("的") >= 400


def scrub(text: str) -> str:
    """去页眉页脚（「××年度报告」行、「12 / 198」与独占一行的页码）、脚注标记与附注引用；港式括号负数改写为负号。"""
    text = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", text)
    lines = [ln for ln in text.split("\n")
             if not re.search(r"年(?:年度|度)?报告(?:全文)?\s*$|^\s*\d{1,4}\s*/\s*\d{1,4}\s*$|^\s*-?\s*\d{1,4}\s*-?\s*$", ln.strip())]
    text = "\n".join(lines)
    text = re.sub(r"【\s*注\s*\d*\s*】|\[\s*注\s*\d*\s*\]|[（(]\s*(?:注\s*[\d一二三四五六七八九十]*|[a-zA-Z]{1,2}|[ivx]{1,4})\s*[)）]"
                  r"|(?<![一-龥])注\s*\d{1,2}(?![\d,.])", "", text)
    text = re.sub(r"[（(]\s*(?:附注|详见|见附注|参见)(?:[^（()）\n]|[（(][^（()）\n]{0,12}[)）]){0,30}[)）]", "", text)
    text = re.sub(r"附注[一二三四五六七八九十\d、（）()．.\s]*(?=[^\d,]|$)", "", text)
    # 日期与「1 年」里的数字在千元／百万元表的整数模式下会被当成金额：「2025 年 12 月 31 日」→「2025年末」，「1 年内」→「一年内」
    text = re.sub(r"((?:19|20)\d{2})\s*年\s*12\s*月\s*31\s*日|((?:19|20)\d{2})[.．/-]12[.．/-]31(?!\d)",
                  lambda m: (m.group(1) or m.group(2)) + "年末", text)
    text = re.sub(r"((?:19|20)\d{2})\s*年\s*(?:0?[1-9]|1[01])\s*月\s*\d{1,2}\s*日", r"\1年中", text)
    text = re.sub(r"(?<![\d,.])1\s*年", "一年", text)
    text = re.sub(r"-?\d+(?:\.\d+)?\s*[%％]", "百分比", text)                  # 说明文字里的增减比例、利率不是金额
    # 行首序号（「（2）」「1）」「3、」「①」）在整数模式下会被当成金额
    text = re.sub(r"(?m)^[ \t]*(?:\d{1,2}\s*[、．.](?!\d)|[（(]\s*\d{1,2}\s*[)）]|\d{1,2}\s*[)）]|[①-⑳])", "", text)
    return NUMBER.sub(lambda m: "-" + m.group(1) + (m.group(2) or ""), text)


# 独占一行行名的退路（序号被文本层丢掉，中国神华 2017）止于下一张报表项目附注的标题行
BS_HEADINGS = ("短期借款", "应付票据", "应付账款", "预收款项", "合同负债", "应付职工薪酬", "应交税费", "其他应付款",
               "持有待售负债", "一年内到期的非流动负债", "其他流动负债", "长期借款", "应付债券", "租赁负债", "长期应付款",
               "长期应付职工薪酬", "预计负债", "递延收益", "递延所得税负债", "其他非流动负债", "股本", "资本公积")
CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def _cn_number(text: str) -> int | None:
    """一～九十九的中文数字 → 整数（「二十一」→ 21）；不认时 None。"""
    if not text or any(c not in CN_DIGITS and c != "十" for c in text):
        return None
    if "十" not in text:
        return CN_DIGITS.get(text) if len(text) == 1 else None
    tens, _, ones = text.partition("十")
    return (CN_DIGITS.get(tens, 0) if tens else 1) * 10 + (CN_DIGITS.get(ones, 0) if ones else 0)


def _cn_numeral(n: int) -> str:
    rev = {v: k for k, v in CN_DIGITS.items()}
    if n < 10:
        return rev[n]
    tens, ones = divmod(n, 10)
    return ("" if tens == 1 else rev[tens]) + "十" + (rev[ones] if ones else "")


# 标题序号：「21、」「21.」「（21）」「（二十一）」「注释 21.」，以及事务所版式的「21 其他应付款」（序号后只跟空格、行名独占一行）
NUMBERED = r"(?:^|\n)[ \t]*(?:注\s*释\s*)?(\d{1,3}\s*[、．.]|[（(](?:[一二三四五六七八九十百]+|\d{1,3})[)）])\s*"
SPACED = r"(?:^|\n)[ \t]*(\d{1,3})[ \t]+"


def heading_end(text: str, label: str, start: int) -> tuple[int, str] | None:
    """附注中以「序号 + 行名」开头的标题（其后 300 字内出现表头）→ (正文起点, 序号)；找不到时退取独占一行的行名（附注
    正文起点之后，同 `cn.section`；序号记空）。"""
    tail = r"(?![一-龥”\"])(?!\s*[（(]\s*续\s*[)）])"          # 「（续）」是跨页的续表标题
    numbered = re.compile(NUMBERED + re.escape(label) + tail)
    spaced = re.compile(SPACED + re.escape(label) + r"[ \t]*(?=\n)")
    tries = [(numbered, cn.HEADER), (numbered, cn.LOOSE_HEADER), (spaced, cn.LOOSE_HEADER)]
    if start > 0:
        tries.append((re.compile(r"(?:^|\n)[ \t]*()" + re.escape(label) + r"[ \t]*(?=\n)"), cn.LOOSE_HEADER))
        # 文本层丢了行名首字（小商品城 2017「44、 他流动负债」）：只认带序号、紧跟表头的标题
        tries.append((re.compile(NUMBERED + re.escape(label[1:]) + tail), cn.HEADER))
    for pattern, header in tries:
        for m in pattern.finditer(text, start):
            if header.search(text[m.end():m.end() + 300]):
                return m.end(), (m.group(1) or "")
    return None


def heading_candidates(text: str, label: str, start: int, limit: int = 4) -> list[tuple[int, str]]:
    """同一行名的候选标题 (正文起点, 序号)：各版式的标题（带序号的配严格或放宽的表头，事务所版式，附注起点之后的独占一行
    行名与丢首字的标题）按位置排列，附注正文起点之后的在前、其前的在后，至多 `limit` 个。合并报表附注之外还有母公司报表
    附注；旧版年报的合并附注表头不带「期末」「单位」（京东方 2010），严格表头会先命中母公司附注，由调用方逐个试到合计与
    报表行相符为止。"""
    tail = r"(?![\u4e00-\u9fa5”\"])(?!\s*[（(]\s*续\s*[)）])"
    numbered = re.compile(NUMBERED + re.escape(label) + tail)
    spaced = re.compile(SPACED + re.escape(label) + r"[ \t]*(?=\n)")
    patterns = [numbered, spaced]
    if start > 0:
        patterns += [re.compile(r"(?:^|\n)[ \t]*()" + re.escape(label) + r"[ \t]*(?=\n)"),
                     re.compile(NUMBERED + re.escape(label[1:]) + tail)]
    found: dict[int, str] = {}
    for k, pattern in enumerate(patterns):
        header = cn.HEADER if k == 3 else cn.LOOSE_HEADER
        for m in pattern.finditer(text):
            if header.search(text[m.end():m.end() + 300]) and (k < 2 or m.start() >= start):
                found.setdefault(m.end(), m.group(1) or "")
    ordered = sorted(found.items(), key=lambda x: (x[0] < start, x[0]))
    return ordered[:limit]


def next_heading(number: str) -> re.Pattern | None:
    """同一版式、序号 + 1 的下一标题。"""
    raw = number.strip()
    m = re.fullmatch(r"(\d{1,3})\s*([、．.])", raw)
    if m:
        return re.compile(r"\n[ \t]*(?:注\s*释\s*)?" + str(int(m.group(1)) + 1) + r"\s*[、．.]\s*[一-龥（(A-Za-z]")
    m = re.fullmatch(r"[（(](\d{1,3})[)）]", raw)
    if m:
        return re.compile(r"\n[ \t]*[（(]" + str(int(m.group(1)) + 1) + r"[)）]\s*[一-龥]")
    m = re.fullmatch(r"[（(]([一二三四五六七八九十]+)[)）]", raw)
    if m and _cn_number(m.group(1)):
        return re.compile(r"\n[ \t]*[（(]" + _cn_numeral(_cn_number(m.group(1)) + 1) + r"[)）]\s*[一-龥]")
    m = re.fullmatch(r"(\d{1,3})", raw)
    if m:
        return re.compile(r"\n[ \t]*" + str(int(m.group(1)) + 1) + r"[ \t]+[一-龥][^\n\d]{1,30}[ \t]*\n")
    return None


def section_body(text: str, label: str, start: int, size: int = 8000) -> str | None:
    """附注段：标题后至同一版式的下一序号标题（序号 + 1）为止，至多 `size` 字；独占一行行名的退路只取 2500 字、止于下一
    以序号起头的标题行。"""
    found = heading_end(text, label, start) or heading_end(text, label, 0)
    return None if found is None else body_at(text, found)


def body_at(text: str, found: tuple[int, str], size: int = 8000) -> str:
    """标题 (正文起点, 序号) → 附注段文字（见 `section_body`）。"""
    pos, number = found
    if not number:
        body = text[pos:pos + 2500]
        stop = re.search(r"\n[ \t]*(?:\d{1,3}\s*[、．.][ \t]*[\u4e00-\u9fa5]|(?:" + "|".join(BS_HEADINGS) + r")[ \t]*\n)", body)
        return body[:stop.start()] if stop else body
    body = text[pos:pos + size]
    nxt = next_heading(number)
    stop = nxt.search(body) if nxt else None
    return body[:stop.start()] if stop else body


# ---- 表格解析 ------------------------------------------------------------------------------------------
def amount_mode(text: str) -> tuple[re.Pattern, str]:
    return cn._pattern(text)


def tokenize(table: str, mode) -> list[tuple[str, list[float]]]:
    """表体 → [(标签, 金额列)]（`cn.table_rows`：长数字断行先拼回，相邻金额归同一行，两组金额之间的文字是下一行的标签）。"""
    return cn.table_rows(table, mode)


def column_order(header: str, n: int) -> int | None:
    """表头判期末所在列：两列表「期初 期末」顺序（预计负债常见）返回 1，「期末 期初」返回 0；变动表（期初、本期增加、本期减少、
    期末）返回最后一列；判不出返回 None。"""
    if n >= 3 and MOVEMENT_WORDS.search(header):
        return n - 1
    cur, prior = CURRENT_WORDS.search(header), PRIOR_WORDS.search(header)
    if cur and prior:
        return 1 if prior.start() < cur.start() and n >= 2 else 0
    years = [int(y) for y in re.findall(r"((?:19|20)\d{2})\s*年", header)]
    if len(years) >= 2 and years[0] != years[1]:
        return 0 if years[0] > years[1] else 1
    return None


def solve_rows(rows: list[tuple[str, list[float]]], totals: list[float], col: int, tol: float) -> list[list[float | None]] | None:
    """逐行金额 → 逐行各列值（空白为 None）。整行齐全的直接对位；缺格的行枚举其金额落在哪几列（组合数 ≤ 20000），各列之和
    都在容差内的解里取偏差最小者；期末列取值不同的两解偏差相同（相差 ≤ 1 个单位）时判不出。合计缺失的列（None）不约束。"""
    n = len(totals)                                                   # totals 里的 None：该列合计缺失，不作约束
    fixed: list[list[float | None] | None] = []
    options: list[list[list[float | None]]] = []
    free: list[int] = []
    for i, (_, vals) in enumerate(rows):
        vals = vals[-n:] if len(vals) > n else vals
        if len(vals) == n:
            fixed.append(list(vals))
        else:
            fixed.append(None)
            opts = []
            for pos in combinations(range(n), len(vals)):
                cells: list[float | None] = [None] * n
                for p, v in zip(pos, vals):
                    cells[p] = v
                opts.append(cells)
            options.append(opts)
            free.append(i)
    size = 1
    for opts in options:
        size *= len(opts)
    if size > 20000:
        return None                                                   # 缺格组合过多：判不出
    base = [sum((r[j] or 0.0) for r in fixed if r is not None) for j in range(n)]
    scored: dict[tuple, tuple[float, tuple]] = {}                 # 期末列取值 → (最小偏差, 该解)
    for combo in product(*options) if free else [()]:
        sums = list(base)
        for cells in combo:
            for j in range(n):
                sums[j] += cells[j] or 0.0
        err = max(abs(sums[j] - totals[j]) for j in range(n) if totals[j] is not None)
        if err > tol:
            continue
        key = tuple(cells[col] or None for cells in combo)
        if key not in scored or err < scored[key][0]:
            scored[key] = (err, combo)
    if not scored:
        return None
    ranked = sorted(scored.values(), key=lambda x: x[0])
    if len(ranked) > 1 and ranked[1][0] - ranked[0][0] <= max(1.0, 1e-7 * max(abs(t) for t in totals if t is not None)):
        return None                                                   # 期末列有两种同样相符的解：判不出
    solutions = [ranked[0][1]]
    combo = solutions[0]
    out = []
    it = iter(combo)
    for r in fixed:
        out.append(r if r is not None else next(it))
    return out


# 资产负债表行名：一张表里有两行以上是这些行名的（流动性风险表、外币项目表等）不是本行附注
BS_LINES = ("短期借款", "应付票据", "应付账款", "预收款项", "合同负债", "应付职工薪酬", "应交税费", "一年内到期的非流动负债",
            "长期借款", "应付债券", "租赁负债", "长期应付款", "其他流动负债", "其他应付款", "交易性金融负债", "衍生金融负债",
            "应付票据及应付账款", "货币资金", "应收账款")


def parse_table(table: str, total_vals: list[float], statement: float | list[float], unit_hint: float | None,
                mode, rel_tol: float = TOTAL_TOLERANCE, line: str | None = None) -> dict:
    """一张附注表（自表头起的表体 + 合计行金额）→ 期末列、单位、逐行期末值。`statement` 为可接受的核对值（元），
    合计与之相差 ≤ rel_tol（或 100 万元）才认这张表；期末列按表头判，判不出时取与核对值相符的列。"""
    targets = statement if isinstance(statement, list) else [statement]
    targets = [t for t in targets if t]
    units = [unit_hint] if unit_hint else [1.0, 1e4, 1e3, 1e6]
    n = len(total_vals)
    if n == 0:
        return dict(status="no_total")
    first_amount = mode[0].search(re.sub(mode[1], "", table))
    col = column_order(table[:first_amount.start()] if first_amount else table, n)
    match = None
    for unit in units:
        cols = [col] if col is not None and col < n else []
        cols += [j for j in range(n) if j not in cols]
        for j in cols:
            hit = next((t for t in targets if abs(total_vals[j] * unit - t) <= max(rel_tol * abs(t), 1e6 if rel_tol >= TOTAL_TOLERANCE else 1.0)), None)
            if hit is not None:
                match = (unit, j, hit)
                break
        if match:
            break
    if match is None:
        return dict(status="total_mismatch", notes_total=total_vals[col if col is not None and col < n else 0] * (unit_hint or 1.0))
    unit, col, target = match
    rows = drop_sub_rows(tokenize(table, mode), max(0.002 * max(abs(t) for t in total_vals), 1.0), line)
    if not rows:
        return dict(status="no_rows", notes_total=total_vals[col] * unit, unit=unit)
    if sum(1 for lab, _ in rows if re.sub(r"\s+", "", _last_line(lab)).strip("：:") in BS_LINES) >= 2 \
            or re.search(r"面\s*值|发\s*行\s*日\s*期|债\s*券\s*期\s*限|票\s*面\s*利\s*率", table[:first_amount.start()] if first_amount else ""):
        return dict(status="wrong_table", notes_total=total_vals[col] * unit, unit=unit)
    tol = max(0.002 * max(abs(t) for t in total_vals), 1.0, 0.5 * len(rows) if mode[0] is cn.INTEGER else 0.0)
    totals_used: list[float | None] = list(total_vals)
    if n == 1 and sum(1 for _, v in rows if len(v) == 2) >= max(1, len(rows) // 2):
        # 合计行只剩一列（上期合计格式有误或缺失，景津 2020）：按两列表求解、只约束期末列
        order = column_order(table[:first_amount.start()] if first_amount else table, 2)
        totals_used = [total_vals[0], None] if order in (None, 0) else [None, total_vals[0]]
        col = 0 if order in (None, 0) else 1
    cells = solve_rows(rows, totals_used, col, tol)
    if cells is None:
        # 母项与唯一子项金额相同、子项未写「其中」（天齐锂业 2016「其他 / 复垦费」）：相邻同额两行去掉一行再试
        twins = [i for i in range(1, len(rows)) if rows[i][1] == rows[i - 1][1] and len(rows[i][1]) >= 1]
        if twins:
            keep = [r for k, r in enumerate(rows) if k + 1 not in twins] if line is None else None
            if line is not None:
                drop = set()
                for i in twins:                               # 留计入类的一行
                    first_counted = classify(rows[i - 1][0], line)[0] in COUNTED[line]
                    drop.add(i if first_counted else i - 1)
                keep = [r for k, r in enumerate(rows) if k not in drop]
            again = solve_rows(keep, totals_used, col, tol)
            if again is not None:
                rows, cells = keep, again
    if cells is None and n >= 2 and all(len(v) == n for _, v in rows) and None not in totals_used:
        # 上期列被重述而对不上：逐行齐全时只要求期末列相符
        single = solve_rows([(lab, [v[col]]) for lab, v in rows], [total_vals[col]], 0, tol)
        if single is not None:
            cells = [[c[0] if k == col else None for k in range(n)] for c in single]
    if cells is None:
        return dict(status="rows_mismatch", notes_total=total_vals[col] * unit, unit=unit,
                    rows=[(_clean_label(lab), vals) for lab, vals in rows])
    out = [(lab, (c[col] or 0.0) * unit) for (lab, _), c in zip(rows, cells)]
    return dict(status="ok", notes_total=total_vals[col] * unit, unit=unit, rows=out, target=target)


def drop_sub_rows(rows: list[tuple[str, list[float]]], tol: float, line: str | None = None) -> list[tuple[str, list[float]]]:
    """去掉「小计」行与「其中：」子行：「其中」行连同其后 k 行（0～6，取最小的 k）各列金额之和与上一母项相符时一并去掉
    （重庆啤酒 2025「未决诉讼 / 其中：包销诉讼案 / 玻璃瓶诉讼案 / 其他」）；认不出时只去「其中」行本身。母项不是计入类而
    子行是（神火 2017「其他 / 其中：复垦、弃置及环境清理义务」）时改留子行、去母项。"""
    out: list[tuple[str, list[float]]] = []
    i = 0
    while i < len(rows):
        lab, vals = rows[i]
        last = re.sub(r"\s+", "", _last_line(lab))
        if re.match(r"小计", last):
            i += 1
            continue
        if re.search(r"(?:^|\n)[ \t]*其\s*中", "\n".join(lab.split("\n")[-4:])) and out:
            parent = sum(out[-1][1])
            k = next((k for k in range(0, 7) if i + k < len(rows)
                      and abs(sum(sum(v) for _, v in rows[i:i + k + 1]) - parent) <= tol), None)
            if k is not None and line:
                block = [(re.sub(r"其\s*中\s*[:：]?", "", lab_), v) for lab_, v in rows[i:i + k + 1]]
                if classify(out[-1][0], line)[0] not in COUNTED[line] and \
                        any(classify(lab_, line)[0] in COUNTED[line] for lab_, _ in block):
                    out[-1:] = block
            i += (k + 1) if k is not None else 1
            continue
        out.append((lab, vals))
        i += 1
    return out


def _last_line(label: str) -> str:
    return ([x for x in re.split(r"[\n|]", label) if x.strip()] or [""])[-1]


def _clean_label(label: str) -> str:
    return re.sub(r"\s+", "", label)[-60:]


HEADER_MARK = re.compile(r"项\s*目|(?:期|年)\s*(?:末|初)\s*(?:余\s*额|数|账\s*面)|(?:19|20)\d{2}\s*年\s*(?:末|度|中)|单\s*位\s*[:：]")
HEADER_LINE = re.compile(r"(?m)^[ \t]*(?:项\s*目.*|.*(?:期|年)\s*(?:末|初)\s*(?:余\s*额|数|账\s*面).*|"
                         r".*(?:19|20)\d{2}\s*年(?:末|度|中)?[ \t]+(?:19|20)\d{2}\s*年.*)$")


def trim(table: str, mode) -> list[tuple[str, str]]:
    """表体候选切法 → [(表体, 表头之前的上下文)]：①切到最后一个表头行（同一段里前一张无合计行的小表——如应付股利——
    不并入）；②切到首个金额之前最后一处表头（「项目」「期末余额」「2025年末」「单位：」）所在行（跨页重复表头时用这一切法）。
    上一张表的表后说明与本表标题不并入首行标签。"""
    joined = re.sub(mode[1], "", table)
    first = mode[0].search(joined)
    if not first:
        return [(joined, "")]
    cuts = []
    heads = [m for m in HEADER_LINE.finditer(joined) if not mode[0].search(m.group(0))]
    if heads:
        cuts.append(heads[-1].start())
    marks = [m for m in HEADER_MARK.finditer(joined, 0, first.start())]
    if marks:
        cuts.append(joined.rfind("\n", 0, marks[-1].start()) + 1)
    out = []
    for cut in dict.fromkeys(cuts):
        out.append((joined[cut:], joined[max(0, cut - 300):cut]))
    return out or [(joined, "")]


def total_segment(body: str, pos: int) -> tuple[str, int]:
    """合计行金额：本行其余部分，加其后只含数字片段的续行（PDF 把长数字断到下一行，至多 4 行）。→ (文字, 结束位置)。"""
    end = body.find("\n", pos)
    end = len(body) if end < 0 else end
    segment = body[pos:end]
    for _ in range(4):
        nxt = body.find("\n", end + 1)
        nxt = len(body) if nxt < 0 else nxt
        line = body[end + 1:nxt]
        if end >= len(body) or not re.fullmatch(r"[\s\d,.\-–—/]*\d[\s\d,.\-–—/]*", line):
            break
        segment += "\n" + line
        end = nxt
    return segment, end


def split_tables(body: str) -> list[dict]:
    """附注段按合计行切表 → [{cuts [(表体（自表头起）, 表头之前的上下文)], table／context 首个切法, totals 合计行金额,
    end 合计行之后的位置, mode 金额格式}]；合计行金额取本行与其后的纯数字续行（`total_segment`）。"""
    out, last = [], 0
    for m in TOTAL_ROW.finditer(body):
        segment, end = total_segment(body, m.end())
        mode = amount_mode(segment)                       # 金额格式按合计行判（表后说明里的利率等小数不左右整数表）
        vals = cn._amounts(segment, mode)
        if vals:
            cuts = trim(body[last:m.start()], mode)
            out.append(dict(cuts=cuts, table=cuts[0][0], context=cuts[0][1], totals=vals, end=end, mode=mode))
        last = end
    return out


def unlabeled_totals(body: str, statement: list[float], unit_hint: float | None = None) -> list[dict]:
    """无「合计」字样的版式（合计行只有数字）：与核对值相差 ≤ TOTAL_TOLERANCE 的纯数字行，按偏差从小到大（单位按提示，
    没有时依次试元、千元、万元、百万元；紫金矿业 2021 一级表与性质表的合计都是纯数字行，由调用方逐个试）。"""
    found = []
    units = [unit_hint] if unit_hint else [1.0, 1e3, 1e4, 1e6]
    for line in re.finditer(r"(?m)^[ \t]*((?:-?[\d,]+(?:\.\d+)?[ \t]*){1,6})$", body[:6000]):
        mode = amount_mode(line.group(1))
        vals = cn._amounts(line.group(1), mode)
        errs = [abs(v * u - t) / abs(t) for v in vals for u in units for t in statement if t]
        if errs and min(errs) <= TOTAL_TOLERANCE:
            cuts = trim(body[:line.start()], mode)
            found.append((min(errs), line.start(), dict(cuts=cuts, table=cuts[0][0], context=cuts[0][1], totals=vals,
                                                        end=line.end(), mode=mode)))
    return [t for _, _, t in sorted(found, key=lambda x: (x[0], x[1]))[:6]]


# ---- 分类 ----------------------------------------------------------------------------------------------
HEAD_WORDS = re.compile(r"项目|(?:期末|期初|年末|年初)(?:余额|数|账面价值)?|形成原因|单位[:：]\S*|币种[:：]\S*|[√□](?:不)?适用|"
                        r"(?:19|20)\d{2}年(?:末|中|度)?|（已重述）|\(已重述\)")


def _hit(text: str, line: str, prefix: str = "") -> str | None:
    """同一窗口文字按 RULES 顺序判类；计入类与本类的混写词同现记 mixed（借款类先去掉「利息」「关联方」一类修饰词再查）。
    括注只写借款的按括注定类（云南锗业 2019「往来款（股东借款）」）。`prefix` 是以连词断行的上一行（「已背书或」），
    只用于判断贴现标签是否同写背书。"""
    note = re.search(r"[（(]([^（()）]{1,12})[）)]", text)
    if note and line != "PREDICT_LIAB" and re.search(r"借款|拆借|借入", note.group(1)) \
            and not re.search(r"含|及|和|与|、|等|往来|保证金", note.group(1)):
        text = note.group(1)
    if line != "PREDICT_LIAB" and DISCOUNTED.search(text) and not any(k in prefix + text for k in DISCOUNTED_NOT):
        return "review"
    for cat, keys, mix in RULES[line]:
        if not any(key in text for key in keys):
            continue
        if cat == "loan" and INTEREST_ONLY.search(text) and not INTEREST_WITH_PRINCIPAL.search(text):
            return "other"
        if cat == "review" and "信用证" in text and "贴现" not in text and not any(k in text for k in REVIEW_KEYS if k != "信用证"):
            return "other"                                   # 应付信用证与应付票据同属经营负债；已贴现的信用证才是融资
        if mix:
            rest = text
            for key in keys + (LOAN_HELPERS if cat == "loan" else ()):
                rest = rest.replace(key, "")
            if any(key in rest for key in mix):
                return "other" if cat == "review" else "mixed"
        return cat
    return None


def classify(label: str, line: str) -> tuple[str, str]:
    """行标签 → (类别, 定类文字)。类别：bond／loan／decom（计入类见 COUNTED）、review（融资安排，另列 review_amount）、mixed（与其他性质
    混写，整份不计）、deduct（减：一年内到期）、other。从金额前最近的一行起逐行向上并入（至多 3 行），首个命中关键词的窗口
    定类；金额所在行本身已是 ≥4 字的完整标签而计入类关键词只在上方行（多为 CSRC 模板里金额空白的行）才出现的，记 mixed。"""
    lines = [HEAD_WORDS.sub("", re.sub(r"\s+", "", x)) for x in re.split(r"[\n|]", label) if x.strip()]
    lines = [x for x in lines if re.search(r"[一-龥A-Za-z]", x)]
    if not lines:
        return "other", ""
    if DEDUCT.search(lines[-1]):
        return "deduct", lines[-1][-40:]
    own = len(re.findall(r"[一-龥]", lines[-1]))
    for k in range(1, min(len(lines), 3) + 1):
        text = "".join(lines[-k:])
        above = lines[-k - 1] if k < len(lines) else ""
        cat = _hit(text, line, above if re.search(r"[或及和与、/／]$", above) else "")
        if cat is None:
            continue
        if k > 1 and own >= 4 and cat in COUNTED[line]:
            return "mixed", text[-40:]
        return cat, text[-40:]
    return "other", lines[-1][-40:]


def summarize(rows: list[tuple[str, float]], line: str) -> dict:
    """逐行 (标签, 期末值) → 计入额、待复核额与明细；预计负债的「减：一年内到期」行从弃置类计入额中扣除（以计入额为限）。"""
    counted = review = deducted = 0.0
    counted_items, review_items, items, mixed = [], [], [], []
    for label, value in rows:
        cat, name = classify(label, line)
        items.append(f"{name}:{value:.2f}:{cat}")
        if cat in COUNTED[line]:
            counted += value
            counted_items.append(f"{name}:{value:.2f}:{cat}")
        elif cat == "review":
            review += value
            review_items.append(f"{name}:{value:.2f}")
        elif cat == "deduct":
            deducted += abs(value)
        elif cat == "mixed" and abs(value) > 0:
            mixed.append(name)
    deducted = min(deducted, counted) if line == "PREDICT_LIAB" else 0.0
    return dict(counted=counted - deducted, review=review, deducted=deducted, counted_items=";".join(counted_items),
                review_items=";".join(review_items), items=";".join(items), mixed=mixed)


# ---- 三行附注 ------------------------------------------------------------------------------------------
def parse_line(text: str, start: int, line: str, task: dict) -> dict:
    """一份年报的一行附注 → 抽取结果（无网络）。"""
    first = None
    for found in heading_candidates(text, LINES[line], start):
        result = parse_body(text, found, line, task)
        if result["status"] in ("ok", "ambiguous", "no_breakdown"):
            return result
        first = first or result
    return first or dict(status="section_not_found")


def parse_body(text: str, found: tuple[int, str], line: str, task: dict) -> dict:
    """一个候选标题下的附注段 → 抽取结果。"""
    statement = task["lines"][line]
    body = scrub(body_at(text, found))
    unit_hint = unit_of(body, text[max(0, found[0] - 4000):found[0]])
    if line == "OTHER_PAYABLE":
        return parse_other_payable(body, task, unit_hint)
    if line == "PREDICT_LIAB":
        transposed = parse_transposed(body, statement, task["year"], unit_hint)
        if transposed is not None:
            return transposed
    return parse_simple(body, line, [statement], unit_hint)


UNIT_WORDS = {"元": 1.0, "千元": 1e3, "万元": 1e4, "百万元": 1e6}
PAGE_UNIT = re.compile(r"金\s*额\s*单\s*位\s*(?:为|：|:)?\s*(?:人\s*民\s*币)?\s*(百\s*万\s*元|千\s*元|万\s*元|元)|"
                       r"(?:^|\n)[^\n]{0,24}?人\s*民\s*币\s*(百\s*万\s*元|千\s*元|万\s*元|元)[ \t]*(?=\n)")   # 「2019年12月31日 人民币千元」


def unit_of(body: str, before: str) -> float | None:
    """金额单位：附注段内写明的「单位：」优先；没有时取标题前 4000 字内最近的页眉单位（事务所版式「(除特别注明外，金额
    单位为人民币千元)」、港式「人民币百万元」独占一行）。都没有返回 None（由调用方按报表行值试单位）。"""
    unit = cn._unit(body)
    if unit:
        return unit
    m = re.search(r"单\s*位\s*[:：]\s*(?:人\s*民\s*币)?\s*(百\s*万\s*元|千\s*元|万\s*元|元)", body)
    if m:
        return UNIT_WORDS[re.sub(r"\s+", "", m.group(1))]
    hits = list(PAGE_UNIT.finditer(body[:1500])) or list(PAGE_UNIT.finditer(before))
    if hits:
        word = hits[-1].group(1) or hits[-1].group(2)
        return UNIT_WORDS[re.sub(r"\s+", "", word)]
    return None


def views(t: dict) -> list[dict]:
    """一张切出的表按各候选切法展开（`trim`）。"""
    return [dict(t, table=table, context=context) for table, context in t["cuts"]]


def parse_simple(body: str, line: str, targets: list[float], unit_hint: float | None) -> dict:
    """单表附注（其他流动负债、预计负债）：合计与报表行相符的表（各候选切法有一种逐行相符即可；先试带「合计」字样的表，
    再试纯数字合计行，最后试只有一行、该行即合计的小表）。都不相符时报首个核上合计的表的失败状态。"""
    first = failed = None
    tables = split_tables(body)
    for t in tables + unlabeled_totals(body, targets, unit_hint):
        for v in views(t):
            parsed = parse_table(v["table"], v["totals"], targets, unit_hint, v["mode"], line=line)
            if parsed["status"] == "ok":
                return finish(parsed, line)
            if parsed["status"] in ("rows_mismatch", "no_rows"):
                failed = failed or parsed
            first = first or parsed
    single = single_row_table(body, targets, unit_hint)
    if single is not None:
        return finish(single, line)
    return failed or first or dict(status="no_total")


def single_row_table(body: str, targets: list[float], unit_hint: float | None) -> dict | None:
    """只有一行、没有合计行的小表（紫金矿业 2016「矿山环境恢复准备金 720,404,428 153,492,797 -2,585,501 871,311,724」）：
    该行某列与报表行值相差 ≤ 0.5% 即以该行为全表（期末列按表头判，判不出取相符的列）。"""
    for m in re.finditer(r"(?m)^[ \t]*([^\d\n-][^\d\n]{1,40}?)[ \t]+((?:-?[\d,]+(?:\.\d+)?[ \t]*){1,6})$", body[:3000]):
        mode = amount_mode(m.group(2))
        vals = cn._amounts(m.group(2), mode)
        for unit in ([unit_hint] if unit_hint else [1.0, 1e3, 1e4, 1e6]):
            hits = [k for k, v in enumerate(vals) for t in targets if t and abs(v * unit - t) <= max(0.005 * abs(t), 1.0)]
            if not hits:
                continue
            before = body[:m.start()]
            header = HEADER_LINE.findall(before[-400:])
            col = column_order(header[-1] if header else "", len(vals))
            col = col if col is not None and col in hits else hits[0]
            return dict(status="ok", notes_total=vals[col] * unit, unit=unit, rows=[(m.group(1), vals[col] * unit)])
    return None


def finish(parsed: dict, line: str) -> dict:
    s = summarize(parsed["rows"], line)
    status = "ambiguous" if s["mixed"] else "ok"
    return dict(status=status, notes_total=parsed["notes_total"], breakdown_total=parsed["notes_total"], unit=parsed["unit"],
                counted=s["counted"] if status == "ok" else 0.0, deducted=s["deducted"], review=s["review"],
                counted_items=s["counted_items"], review_items=s["review_items"],
                items=s["items"] + (f";混写:{'|'.join(s['mixed'])}" if s["mixed"] else ""))


LEVEL1 = re.compile(r"应\s*付\s*利\s*息|应\s*付\s*股\s*利")
OTHER_PAYABLE_ROW = re.compile(r"其\s*他\s*应\s*付\s*款(?:\s*项)?")
NATURE = re.compile(r"按\s*(?:款\s*项\s*)?性\s*质|款\s*项\s*性\s*质|性\s*质\s*列\s*示")
AGING = re.compile(r"账\s*龄|未\s*偿\s*还|未\s*支\s*付\s*(?:或\s*结\s*转\s*)?(?:的\s*)?原\s*因|结\s*转\s*(?:的\s*)?原\s*因")


def parse_other_payable(body: str, task: dict, unit_hint: float | None) -> dict:
    """其他应付款：一级表（应付利息、应付股利、其他应付款）合计核对报表合计行，性质表合计须与一级表的其他应付款相符；
    2018 年前版式（及过渡年东财单列 `OTHER_PAYABLE`）直接以性质表合计核对报表行。"""
    statement = task["lines"]["OTHER_PAYABLE"]
    total_line = task.get("total_other_payable") or statement
    residual = total_line - task.get("interest_payable", 0.0) - task.get("dividend_payable", 0.0)
    tables = split_tables(body)
    level1, nature_targets, line_verified, sub_target = None, [statement, residual], None, None
    for t in tables:
        for v in views(t):
            rows_text = v["table"]
            if not (LEVEL1.search(rows_text) and OTHER_PAYABLE_ROW.search(rows_text)) or NATURE.search(title(v["context"]) + rows_text[:80]):
                continue
            parsed = parse_table(rows_text, v["totals"], [total_line, statement], unit_hint, v["mode"])
            if parsed["status"] == "ok":
                level1, line_verified = t, parsed["notes_total"]
                sub = [x for lab, x in parsed["rows"] if OTHER_PAYABLE_ROW.search(_last_line(lab))]
                inline = [(lab, x) for lab, x in parsed["rows"]
                          if not (LEVEL1.search(_last_line(lab)) or OTHER_PAYABLE_ROW.search(_last_line(lab)))]
                if inline and not sub:
                    # 性质明细直接列在一级表里（公牛 2025：应付利息、应付股利、其他应付款三行空白，其下逐项列示）
                    out = finish(dict(parsed, rows=inline), "OTHER_PAYABLE")
                    out["breakdown_total"] = sum(x for _, x in inline)
                    return out
                if sub:
                    sub_target = sub[-1]
                    nature_targets = [sub[-1]] + nature_targets
                break
        if level1 is not None:
            break
    candidates = []
    for t in tables:
        if t is level1:
            continue
        for v in views(t):
            head = title(v["context"]) + "\n" + v["table"].lstrip("\n").split("\n", 1)[0]
            if AGING.search(head):
                continue                                          # 账龄超过 1 年的重要其他应付款
            if re.search(r"应\s*付\s*股\s*利|应\s*付\s*利\s*息|普通股股利|借款利息", head) and not NATURE.search(head):
                continue                                          # 应付利息、应付股利分表
            candidates.append(v)
    candidates.sort(key=lambda v: 0 if NATURE.search(title(v["context"])) else 1)

    def is_level1(rows: list[tuple[str, float]]) -> bool:
        lasts = [re.sub(r"\s+", "", _last_line(lab)) for lab, _ in rows]
        return any(LEVEL1.search(x) for x in lasts) and any(OTHER_PAYABLE_ROW.fullmatch(x) for x in lasts)

    for t in candidates:
        parsed = None
        if sub_target:                                            # 一级表的其他应付款行：性质表合计须精确相符
            parsed = parse_table(t["table"], t["totals"], [sub_target], unit_hint, t["mode"], rel_tol=0.002, line="OTHER_PAYABLE")
        if parsed is None or parsed["status"] != "ok":
            parsed = parse_table(t["table"], t["totals"], [x for x in nature_targets if x], unit_hint, t["mode"], line="OTHER_PAYABLE")
        if parsed["status"] != "ok" or is_level1(parsed["rows"]):
            continue
        out = finish(parsed, "OTHER_PAYABLE")
        out["notes_total"] = line_verified if line_verified is not None else parsed["notes_total"]
        out["breakdown_total"] = parsed["notes_total"]
        return out
    for bare in unlabeled_totals(body, [x for x in nature_targets if x], unit_hint):   # 无「合计」字样的性质表（顺丰 2025）
        for v in views(bare):
            parsed = parse_table(v["table"], v["totals"], [x for x in nature_targets if x], unit_hint, v["mode"], line="OTHER_PAYABLE")
            if parsed["status"] == "ok" and not is_level1(parsed["rows"]):
                out = finish(parsed, "OTHER_PAYABLE")
                out["notes_total"] = line_verified if line_verified is not None else parsed["notes_total"]
                out["breakdown_total"] = parsed["notes_total"]
                return out
    if level1 is not None:
        return dict(status="no_breakdown", notes_total=line_verified, unit="",
                    items="一级表已核上，未找到合计相符的性质表")
    single = re.search(r"(?m)^[ \t]*其他应付款[ \t]+(-?[\d,]+(?:\.\d{2})?)", body)
    if single:                                                    # 只有一行合计、其余为文字说明（美的 2025）
        value = float(single.group(1).replace(",", ""))
        if any(abs(value * u - x) <= max(TOTAL_TOLERANCE * abs(x), 1e6) for u in (1.0, 1e3, 1e4, 1e6) for x in nature_targets if x):
            return dict(status="no_breakdown", notes_total=statement, unit="", items="附注只列一行合计，构成只有文字说明")
    first = next((parse_table(v["table"], v["totals"], [total_line, statement, residual], unit_hint, v["mode"])
                  for t in tables for v in views(t)), None)
    if first is None:
        return dict(status="no_total")
    if first["status"] == "ok":
        # 合计与报表行相符的表只有账龄表、应付利息／应付股利分表（2015 年前多见「按账龄列示」）：没有款项性质，无从判借款
        return dict(status="no_breakdown", notes_total=first["notes_total"], unit=first.get("unit", ""),
                    items="附注只按账龄或分表列示，没有款项性质表")
    return first


def title(context: str, k: int = 2) -> str:
    """表头之前最后 k 行有意义的文字（表题）：跳过「√适用 □不适用」「单位：元 币种：人民币」一类行。"""
    lines = [ln.strip() for ln in context.split("\n")
             if ln.strip() and not re.fullmatch(r"(?:[√□]\s*(?:不)?适用\s*)+|单\s*位\s*[:：].*|币\s*种\s*[:：].*", ln.strip())]
    return "\n".join(lines[-k:])


DATE_ROW = re.compile(r"((?:19|20)\d{2})年末")


def parse_transposed(body: str, statement: float, year: int, unit_hint: float | None = None) -> dict | None:
    """港式转置的预计负债变动表（中国神华）：表头是类别（「预提复垦费用 其他 合计」），行是日期与增减（「2025年末」
    「减：一年内到期部分」「长期部分」）。合计列与报表行值相符的行（长期部分或本年末行）定单位，弃置类列的同行值计入。"""
    lines = body.split("\n")
    head_idx = next((i for i, ln in enumerate(lines[:60]) if re.search(r"合\s*计\s*$", ln.strip())
                     and len(re.split(r"\s{2,}", ln.strip())) >= 2 and not re.search(r"\d", ln)), None)
    if head_idx is None:
        return None
    names = [re.sub(r"\s+", "", x) for x in re.split(r"\s{2,}", lines[head_idx].strip()) if x.strip()]
    if not any(any(k in n for k in DECOM_KEYS) for n in names):
        return None
    mode = amount_mode("\n".join(lines[head_idx + 1:head_idx + 40]))
    rows = []
    for ln in lines[head_idx + 1:head_idx + 40]:
        first = mode[0].search(ln)
        if not first:
            continue
        vals = cn._amounts(ln[first.start():], mode)
        if len(vals) == len(names):
            rows.append((re.sub(r"\s+", "", ln[:first.start()]), vals))
    found = None
    for unit in ([unit_hint] if unit_hint else [1e6, 1e3, 1e4, 1.0]):
        hits = []
        for label, vals in rows:
            date = DATE_ROW.search(label)
            if date and int(date.group(1)) != year:
                continue
            err = abs(vals[-1] * unit - statement)
            if err <= max(TOTAL_TOLERANCE * abs(statement), 1e6):
                hits.append((0 if re.search(r"长期|非流动", label) else 1, err, label, vals))
        if hits:
            _, _, label, vals = min(hits, key=lambda h: (h[0], h[1]))   # 长期部分行优先（一年内到期部分已进有息负债）
            found = (unit, label, vals)
            break
    if found is None:
        last = next((v for lab, v in reversed(rows)), None)
        return dict(status="total_mismatch", notes_total=last[-1] if last else None, unit="",
                    items="转置表：" + ";".join(f"{lab}:{v}" for lab, v in rows[:8]))
    unit, label, vals = found
    if abs(sum(vals[:-1]) - vals[-1]) > max(0.002 * abs(vals[-1]), 1.0):
        return dict(status="rows_mismatch", notes_total=vals[-1] * unit, unit=unit)
    counted, items, counted_items = 0.0, [], []
    for name, v in zip(names[:-1], vals[:-1]):
        cat = _hit(name, "PREDICT_LIAB") or "other"
        items.append(f"{name}:{v * unit:.2f}:{cat}")
        if cat == "decom":
            counted += v * unit
            counted_items.append(f"{name}:{v * unit:.2f}:decom")
        elif cat == "mixed":
            return dict(status="ambiguous", notes_total=vals[-1] * unit, unit=unit, items=f"转置表混写列：{name}")
    return dict(status="ok", notes_total=vals[-1] * unit, breakdown_total=vals[-1] * unit, unit=unit, counted=counted,
                deducted=0.0, review=0.0, counted_items=";".join(counted_items), review_items="",
                items=f"转置表[{label}];" + ";".join(items))


def parse_task(task: dict, meta: dict) -> list[dict]:
    """缓存文本 → 达标各行的抽取结果（无网络）。"""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    day = re.search(r"finalpage/(\d{4}-\d{2}-\d{2})/", meta.get("url", ""))
    base = dict(security_code=task["code"], security_name=task["name"], fiscal_year=task["year"],
                report_date=task["report_date"], extracted_at_utc=stamp,
                announcement_date=day.group(1) if day else meta.get("date", ""),
                title=meta.get("title", ""), url=meta.get("url", ""))
    rows = []
    text = None
    if meta.get("status") == "ok":
        path = cn.CACHE / task["code"] / f"{task['year']}.txt.gz"
        try:
            text = gzip.decompress(path.read_bytes()).decode("utf-8") if path.exists() else None
        except (OSError, EOFError, UnicodeDecodeError):              # 缓存写到一半（并发下载）：按缺文本记
            text = None
    start = cn.notes_start(text) if text else 0
    for line, amount in task["lines"].items():
        row = dict(base, line=line, line_label=LINES[line], statement_amount=f"{amount:.2f}", counted_amount="0.00",
                   counted_kind=KIND[line])
        if text is None:
            rows.append(dict(row, status=meta.get("status", "missing") if meta.get("status") != "ok" else "text_missing"))
            continue
        if not readable(text):
            rows.append(dict(row, status="text_unreadable"))
            continue
        try:
            parsed = parse_line(text, start, line, task)
        except Exception as exc:                                   # noqa: BLE001 - recorded as status
            parsed = dict(status=f"parse_error:{type(exc).__name__}")
        rows.append(dict(row, status=parsed["status"],
                         notes_total="" if parsed.get("notes_total") in (None, "") else f"{parsed['notes_total']:.2f}",
                         breakdown_total="" if parsed.get("breakdown_total") in (None, "") else f"{parsed['breakdown_total']:.2f}",
                         counted_amount=f"{parsed.get('counted', 0.0) if parsed['status'] == 'ok' else 0.0:.2f}",
                         deducted_amount=f"{parsed.get('deducted', 0.0):.2f}",
                         review_amount=f"{parsed.get('review', 0.0):.2f}", counted_items=parsed.get("counted_items", ""),
                         review_items=parsed.get("review_items", ""), items=parsed.get("items", "")
                         or ";".join(f"{lab}:{vals}" for lab, vals in parsed.get("rows", [])[:20]),
                         unit=parsed.get("unit", "")))
    return rows


# ---- 人工核定与写表 -------------------------------------------------------------------------------------
def apply_manual(merged: dict[tuple[str, int], list[dict]], path: Path | None = None) -> int:
    """人工核定行覆盖同一 (代码, 财年, 行) 的抽取结果（`status = manual`）；被覆盖行的报表行值与登记值相差超出
    TOTAL_TOLERANCE（或 100 万元）即记 `manual_stale`、计入额记 0。返回登记行数。"""
    path = path or MANUAL
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        manual = list(csv.DictReader(handle))
    for m in manual:
        code, year, line = m["security_code"].zfill(6), int(m["fiscal_year"]), m["line"]
        rows = merged.get((code, year), [])
        replaced = next((r for r in rows if r["line"] == line), None)
        registered = _num(m["statement_amount"])
        stale = replaced is not None and abs(_num(replaced.get("statement_amount")) - registered) > max(
            TOTAL_TOLERANCE * abs(registered), 1e6)
        row = dict(security_code=code, security_name=m["security_name"], fiscal_year=year, report_date=m["report_date"],
                   line=line, line_label=LINES[line], statement_amount=m["statement_amount"], notes_total=m["notes_total"],
                   breakdown_total=m["notes_total"], counted_amount="0.00" if stale else m["counted_amount"],
                   counted_kind=m.get("counted_kind") or KIND[line], counted_items=m["counted_items"],
                   review_amount=m.get("review_amount", ""), review_items=m.get("review_items", ""),
                   items=f"人工核定（{m['source_page']}）：{m['basis']}", unit=m["unit"],
                   status="manual_stale" if stale else "manual", announcement_date=m["source_date"],
                   title=m["source_title"], url=m["source_url"], extracted_at_utc=m["registered_at"])
        merged[(code, year)] = [r for r in rows if r["line"] != line] + [row]
    return len(manual)


def load_existing(path: Path) -> dict[tuple[str, int], list[dict]]:
    out: dict[tuple[str, int], list[dict]] = {}
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") in ("manual", "manual_stale"):
                    continue                                       # 人工核定行每次按登记表重放
                out.setdefault((row["security_code"], int(row["fiscal_year"])), []).append(row)
    return out


def write(merged: dict, path: Path) -> None:
    rows = sorted((r for rs in merged.values() for r in rs), key=lambda r: (r["security_code"], int(r["fiscal_year"]), r["line"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def fetch(tasks: list[dict], workers: int, refresh: bool) -> dict[tuple[str, int], dict]:
    """定位（串行，检索接口限流）与下载（进程池；已缓存跳过）。返回 {(代码, 财年): 元数据}。"""
    metas: dict[tuple[str, int], dict] = {}
    orgs_path = cn.CACHE / "orgid.json"
    orgs = json.loads(orgs_path.read_text()) if orgs_path.exists() else {}
    for code in sorted({t["code"] for t in tasks}):
        try:
            cn.org_id(code, orgs)
        except Exception as exc:                                  # noqa: BLE001
            print(f"  ⚠ {code} orgId 失败：{exc}", flush=True)
    orgs_path.write_text(json.dumps(orgs, ensure_ascii=False, indent=0))
    todo = [t for t in tasks if t["code"] in orgs]
    for i, t in enumerate(todo, 1):
        before = (cn.CACHE / t["code"] / f"{t['year']}.json").exists()
        metas[(t["code"], t["year"])] = cn.locate(t, orgs, refresh)
        if not before:
            time.sleep(0.5)
        if i % 200 == 0 or i == len(todo):
            print(f"  定位 {i}/{len(todo)}", flush=True)
    pending = [t for t in todo if metas[(t["code"], t["year"])].get("status") == "located"
               or (refresh and metas[(t["code"], t["year"])].get("status") == "ok")]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(cn.fetch_report, t, metas[(t["code"], t["year"])], refresh): t for t in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            t = futures[fut]
            metas[(t["code"], t["year"])] = fut.result()
            if i % 20 == 0 or i == len(pending):
                print(f"  下载 {i}/{len(pending)}", flush=True)
    return metas


# ---- 弃置专项资金（用户 2026-10-06 裁定：弃置义务税后计入股权桥，报表现金行之外的弃置专户、矿山地质环境治理恢复基金等
#      专项资金计超额现金对冲；已在货币资金里的本就按现金计，只列出备查） ---------------------------------------------
FUNDS_OUT = ROOT / "data/reference/decom_fund_items.csv"
CASH_NOTE_MANUAL = ROOT / "data/reference/cash_note_manual.csv"
FUND_LINES = {"OTHER_CURRENT_ASSET": "其他流动资产", "NONCURRENT_ASSET_1YEAR": "一年内到期的非流动资产",
              "OTHER_NONCURRENT_ASSET": "其他非流动资产", "MONETARYFUNDS": "货币资金"}
FUND_LABEL = re.compile(r"(?:弃置|复垦|环境治理|环境恢复|恢复治理|治理恢复|地质环境|矿山环境|生态环境|生态修复|生态恢复|闭坑|闭矿)"
                        r"[^:：;；。，,\n\d]{0,14}?(?:基金|专户|保证金|专项资金|复原准备金)")
FUND_AMOUNT = re.compile(r"(?P<name>(?:弃置|复垦|环境治理|环境恢复|恢复治理|治理恢复|地质环境|矿山环境|生态环境|生态修复|生态恢复|闭坑|闭矿)"
                         r"[^:：;；。，,\d]{0,20}?(?:基金|专户|保证金|专项资金|复原准备金)[^:：;；。\d]{0,10}?(?:存款)?)"
                         r"(?P<gap>[^\d。；;]{0,30}?)(?P<amount>\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*"
                         r"(?P<unit>百万元|万元|千元|元)")
# 「人民币 440,477,664 元(2024 年…)为闭矿生态复原准备金」：金额在前、名称在后的散文（紫金矿业 2025 货币资金附注）
FUND_AMOUNT_AFTER = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s*(百万元|万元|千元|元)[^。；;]{0,40}?(?:为|系|是)"
                               r"((?:弃置|复垦|环境治理|环境恢复|恢复治理|治理恢复|地质环境|矿山环境|生态环境|生态修复|生态恢复|闭坑|闭矿)"
                               r"[^:：;；。，,\d]{0,14}?(?:基金|专户|保证金|专项资金|复原准备金))")
FUND_MIXED = re.compile(r"借款|贷款|票据|承兑|汇票|信用证|保函|履约|冻结|其他保证金|应收|ETC|及其他|等")   # 与其他性质混写的行不取
FUND_FIELDS = ["security_code", "security_name", "fiscal_year", "report_date", "line", "line_label", "statement_amount",
               "notes_total", "fund_amount", "fund_items", "counts_as_excess_cash", "status", "note_status", "source",
               "source_page", "announcement_date", "title", "url", "extracted_at_utc"]


def _fund_rows_from_note(text: str, start: int, line: str, statement: float) -> dict:
    """资产行附注表（`cn.section` + `cn.parse_section`，合计与报表行相符、逐行之和与合计相符）里的专项资金行。"""
    body = cn.section(text, FUND_LINES[line], start) or cn.section(text, FUND_LINES[line], 0)
    if body is None:
        return dict(note_status="section_not_found", funds=[], candidates=[])
    parsed = cn.parse_section(body, statement)
    candidates = [f"{m['name']}:{m['amount']}{m['unit']}" for m in FUND_AMOUNT.finditer(re.sub(r"\s+", "", body[:3000]))]
    if parsed["status"] not in ("ok", "cash_exceeds_total"):
        return dict(note_status=parsed["status"], funds=[], candidates=candidates, notes_total=parsed.get("notes_total"))
    funds = [(_fund_name(lab), v) for lab, v, _ in parsed.get("rows", [])
             if FUND_LABEL.search(lab) and not FUND_MIXED.search(_fund_name(lab, wide=True)) and v > 0]
    return dict(note_status="ok", funds=funds, candidates=candidates, notes_total=parsed["notes_total"], unit=parsed["unit"])


def _fund_name(label: str, wide: bool = False) -> str:
    """行标签里的专项资金名（「矿山地质环境治理恢复基金」）；`wide` 时连同其前后同一分句的文字，供混写判断。"""
    flat = re.sub(r"\s+", "", label)
    m = list(FUND_LABEL.finditer(flat))
    if not m:
        return flat[-30:]
    if not wide:
        return m[-1].group(0)
    head = re.split(r"[:：;；。，,]", flat[:m[-1].start()])[-1]
    tail = re.split(r"[:：;；。，,]", flat[m[-1].end():])[0]
    return head + m[-1].group(0) + tail                    # 名称所在分句的前后文字（「…基金、借款保证金、转…」算混写）


def _fund_rows_in_cash(text: str, monetary: float) -> dict:
    """货币资金附注（含受限分项、「现金和现金等价物」附注与受限资产表）里写明金额的专项资金：表格行按附注单位，散文按写明单位；
    须为正且不超过资产负债表货币资金。只作备查（已按现金计）。"""
    import fetch_restricted_cash_items as rc
    regions = []                                         # (片段, 单位, 金额格式, 是否读表格行)
    note = rc.cash_note_region(text, monetary)
    if note:
        regions.append((note[0], note[1] if (note[3] or cn._unit(note[0])) else None, note[2], True))
    for m in rc.CCE_HEAD.finditer(text):
        body = text[m.end():m.end() + 2500]
        regions.append((body, cn._unit(body) or (note[1] if note and note[3] else None), None, True))
    restricted = rc.find_section(text)
    if restricted:                                       # 受限资产表的原因列会串入下一行行名：只读散文里写明单位的金额
        regions.append((restricted[0], None, None, False))
    found: dict[str, float] = {}
    for body, unit, mode, table in regions:
        rows = rc.labeled_rows(body, mode) if table else []
        two_col = sum(1 for r in rows if len(r["amounts"]) >= 2) * 2 >= max(len(rows), 1)
        for r in rows:
            if not FUND_LABEL.search(r["label"]) or FUND_MIXED.search(_fund_name(r["label"], wide=True)):
                continue
            if not (r["unit"] or unit) or (two_col and len(r["amounts"]) == 1 and not r["unit"]):
                continue                                 # 单位不明，或两列表里只剩一个数（期末空白、只有期初，兖矿 2019）
            value = r["amounts"][0] * (r["unit"] or unit)
            if 0 < value <= monetary * 1.001:
                found.setdefault(_fund_name(r["label"]), value)
        flat = re.sub(r"\s+", "", body)
        prose = [(m["name"] + m["gap"], m["amount"], m["unit"]) for m in FUND_AMOUNT.finditer(flat)]
        prose += [(m.group(3), m.group(1), m.group(2)) for m in FUND_AMOUNT_AFTER.finditer(flat)]
        for name, amount, unit_word in prose:
            if FUND_MIXED.search(_fund_name(name, wide=True)):
                continue
            value = float(amount.replace(",", "")) * rc.UNITS[unit_word]
            if 0 < value <= monetary * 1.001 and not any(abs(value - v) <= 1.0 for v in found.values()):
                found.setdefault(_fund_name(name), value)
    # 同一笔资金在几处附注重复出现：同额只计一次
    unique: dict[str, float] = {}
    for label, value in found.items():
        if not any(abs(value - v) <= max(1.0, 1e-6 * value) for v in unique.values()):
            unique[label] = value
    return dict(note_status="ok" if note else "section_not_found", funds=list(unique.items()))


def _manual_funds(code: str, year: int) -> list[dict]:
    """`cash_note_manual.csv`（附注现金类人工核定表，只读）依据栏写明的弃置专户等专项资金（文本层无字符映射的年报，中国海油）。"""
    out = []
    if not CASH_NOTE_MANUAL.exists():
        return out
    with CASH_NOTE_MANUAL.open(encoding="utf-8") as handle:
        for m in csv.DictReader(handle):
            if m["security_code"].zfill(6) != code or int(m["fiscal_year"]) != year or m["line"] not in FUND_LINES:
                continue
            for hit in FUND_AMOUNT.finditer(re.sub(r"\s+", "", m.get("basis", ""))):
                if FUND_MIXED.search(hit["name"] + hit["gap"]):
                    continue
                value = float(hit["amount"].replace(",", "")) * {"元": 1.0, "千元": 1e3, "万元": 1e4, "百万元": 1e6}[hit["unit"]]
                out.append(dict(line=m["line"], label=_fund_name(hit["name"]), value=value, statement=_num(m["statement_amount"]),
                                page=m.get("source_page", ""), url=m.get("source_url", ""), date=m.get("source_date", ""),
                                title=m.get("source_title", "")))
    return out


def decom_funds(debt_path: Path, extra: set[tuple[str, int]] | None = None) -> list[dict]:
    """弃置类计入额 > 0（`debt_path` 中 PREDICT_LIAB 行 status ∈ VERIFIED）的 (代码, 财年)，逐行查专项资金：其他流动资产、
    一年内到期的非流动资产、其他非流动资产按附注表（合计核对报表行）取（`counts_as_excess_cash = 1`，计超额现金对冲）；
    货币资金只列出备查（`0`）。附注表核不上或文本层不可读时退取 `cash_note_manual.csv` 依据栏（status = manual）。"""
    targets: set[tuple[str, int]] = set(extra or ())
    with debt_path.open(encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            if r["line"] == "PREDICT_LIAB" and r["status"] in VERIFIED and _num(r["counted_amount"]) > 0:
                targets.add((r["security_code"], int(r["fiscal_year"])))
    balance: dict[tuple[str, int], dict] = {}
    with cn.STMT.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = (row["security_code"].zfill(6), int(row["REPORT_DATE"][:4]))
            if key in targets and row["REPORT_DATE"][:10].endswith("12-31"):
                balance[key] = row
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for code, year in sorted(targets):
        b = balance.get((code, year))
        if b is None:
            continue
        meta_path = cn.CACHE / code / f"{year}.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        day = re.search(r"finalpage/(\d{4}-\d{2}-\d{2})/", meta.get("url", ""))
        base = dict(security_code=code, security_name=b.get("SECURITY_NAME_ABBR", ""), fiscal_year=year,
                    report_date=b["REPORT_DATE"][:10], announcement_date=day.group(1) if day else meta.get("date", ""),
                    title=meta.get("title", ""), url=meta.get("url", ""), extracted_at_utc=stamp)
        text = None
        if meta.get("status") == "ok" and (cn.CACHE / code / f"{year}.txt.gz").exists():
            text = gzip.decompress((cn.CACHE / code / f"{year}.txt.gz").read_bytes()).decode("utf-8")
        manual = _manual_funds(code, year)
        start = cn.notes_start(text) if text else 0
        outside: list[float] = []                          # 报表现金行之外已认的专项资金（货币资金附注若引用同一笔，不重复列）
        for line, label in FUND_LINES.items():
            statement = _num(b.get(line))
            if statement <= 0:
                continue
            row = dict(base, line=line, line_label=label, statement_amount=f"{statement:.2f}", fund_amount="0.00",
                       counts_as_excess_cash="0" if line == "MONETARYFUNDS" else "1", status="not_found", source="")
            mine = [m for m in manual if m["line"] == line]
            if text is None or not readable(text):
                note = dict(note_status="text_unreadable" if text else meta.get("status", "not_fetched"), funds=[])
            elif line == "MONETARYFUNDS":
                note = _fund_rows_in_cash(text, statement)
            else:
                note = _fund_rows_from_note(text, start, line, statement)
            if line == "MONETARYFUNDS":
                note["funds"] = [(lab, v) for lab, v in note["funds"] if not any(abs(v - o) <= 1.0 for o in outside)]
            if note["funds"]:
                total = sum(v for _, v in note["funds"])
                if line != "MONETARYFUNDS":
                    outside.extend(v for _, v in note["funds"])
                row.update(status="ok", fund_amount=f"{total:.2f}", source="note_table" if line != "MONETARYFUNDS" else "cash_note",
                           fund_items=";".join(f"{lab}:{v:.2f}" for lab, v in note["funds"]),
                           notes_total="" if note.get("notes_total") in (None, "") else f"{note['notes_total']:.2f}")
            elif mine:
                m = mine[0]
                stale = abs(m["statement"] - statement) > max(TOTAL_TOLERANCE * abs(statement), 1e6)
                if not stale:
                    outside.extend(x["value"] for x in mine)
                row.update(status="not_found" if stale else "manual", source="cash_note_manual", source_page=m["page"],
                           fund_amount="0.00" if stale else f"{sum(x['value'] for x in mine):.2f}",
                           fund_items=";".join(f"{x['label']}:{x['value']:.2f}" for x in mine), url=m["url"] or base["url"],
                           announcement_date=m["date"] or base["announcement_date"], title=m["title"] or base["title"])
            else:
                row.update(fund_items="；".join(note.get("candidates", []))[:300],
                           notes_total="" if note.get("notes_total") in (None, "") else f"{note['notes_total']:.2f}")
            row["note_status"] = note["note_status"]
            out.append(row)
    return out


def write_funds(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FUND_FIELDS, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["security_code"], int(r["fiscal_year"]), r["line"])))
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--codes", help="逗号分隔")
    parser.add_argument("--years", help="逗号分隔财年，或区间 2015-2025")
    parser.add_argument("--pool", action="store_true", help="只取核心估值池成员")
    parser.add_argument("--plan", action="store_true", help="只打印清单规模")
    parser.add_argument("--refresh", action="store_true", help="重下原文")
    parser.add_argument("--parse-only", action="store_true", help="只用已缓存文本解析，不联网")
    parser.add_argument("--workers", type=int, default=6, help="下载与文本提取的进程数")
    parser.add_argument("--limit", type=int, default=0, help="只取清单前 N 份（分批下载）")
    parser.add_argument("--out", type=Path, default=OUT, help="输出表（缺省生产表）")
    parser.add_argument("--manual", type=Path, default=MANUAL, help="人工核定表")
    parser.add_argument("--show", action="store_true", help="打印逐行解析结果（调试）")
    parser.add_argument("--funds", action="store_true",
                        help="只按 --out 表里弃置类计入额 > 0 的 (代码, 财年) 查弃置专项资金，写 --funds-out（不联网）")
    parser.add_argument("--funds-out", type=Path, default=FUNDS_OUT, help="弃置专项资金表（缺省生产表）")
    args = parser.parse_args()
    if args.funds:
        rows = decom_funds(args.out)
        write_funds(rows, args.funds_out)
        stats: dict[str, int] = {}
        for r in rows:
            stats[r["status"]] = stats.get(r["status"], 0) + 1
        counted = sum(_num(r["fund_amount"]) for r in rows if r["status"] in VERIFIED and r["counts_as_excess_cash"] == "1")
        memo = sum(_num(r["fund_amount"]) for r in rows if r["status"] in VERIFIED and r["counts_as_excess_cash"] == "0")
        print(f"专项资金 {len(rows)} 行：{stats}；报表现金行之外 {counted / 1e8:.1f} 亿（计超额现金），货币资金内 {memo / 1e8:.1f} 亿（备查）")
        return 0
    codes = {c.strip().zfill(6) for c in args.codes.split(",")} if args.codes else None
    if args.pool:
        codes = (codes & pool_codes()) if codes else pool_codes()
    years = None
    if args.years:
        years = set()
        for part in args.years.split(","):
            lo, _, hi = part.partition("-")
            years |= set(range(int(lo), int(hi or lo) + 1))
    tasks = plan(codes, years)
    if args.limit:
        tasks = tasks[:args.limit]
    lines = sum(len(t["lines"]) for t in tasks)
    print(f"清单 {len(tasks)} 份年报、{lines} 行（{len({t['code'] for t in tasks})} 家）", flush=True)
    if args.plan:
        missing = [t for t in tasks if not (cn.CACHE / t["code"] / f"{t['year']}.json").exists()]
        print(f"未定位 {len(missing)} 份")
        return 0
    metas: dict[tuple[str, int], dict] = {}
    if not args.parse_only:
        metas = fetch(tasks, args.workers, args.refresh)
    for t in tasks:
        path = cn.CACHE / t["code"] / f"{t['year']}.json"
        if (t["code"], t["year"]) not in metas:
            metas[(t["code"], t["year"])] = json.loads(path.read_text()) if path.exists() else dict(status="not_fetched")
    results = {}
    for t in tasks:
        results[(t["code"], t["year"])] = parse_task(t, metas[(t["code"], t["year"])])
        if args.show:
            for r in results[(t["code"], t["year"])]:
                print(t["code"], t["year"], r["line"], r["status"], r.get("statement_amount"), r.get("notes_total"),
                      r.get("counted_amount"), "|", r.get("counted_items"), "|", r.get("review_items"), "|", r.get("items"))
    merged = {**load_existing(args.out), **results}
    apply_manual(merged, args.manual)
    write(merged, args.out)
    rows = [r for rs in results.values() for r in rs]
    stats: dict[str, int] = {}
    for r in rows:
        key = (r.get("status") or "").split(":")[0]
        stats[key] = stats.get(key, 0) + 1
    ok = [r for rs in merged.values() for r in rs if r.get("status") in VERIFIED]
    print(f"本次行状态：{stats}")
    for line in LINES:
        sel = [r for r in ok if r["line"] == line]
        print(f"  {LINES[line]}：核定 {len(sel)} 行，计入 {sum(_num(r['counted_amount']) for r in sel) / 1e8:.1f} 亿"
              f"（{sum(1 for r in sel if _num(r['counted_amount']) > 0)} 行非零）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
