#!/usr/bin/env python3
"""OI-291 批次材料：给每家公司的独立代理准备统一的数据包与公告原文。

每家公司抓取：
- 东财 F10 全部报告期三表（一般企业口径，银行、保险另存专用口径）、主营构成、分红明细、日 K（不复权）与月 K（前复权）；
- 腾讯月线（不复权、后复权）、近一年日线与报价；
- 东财同业比较（估值、成长、杜邦）；
- 2025-01-01 至价格日的公告目录，按标题规则选取定期报告全文与重要公告，下载 PDF 并抽成逐页文本；
- 近 6 个月东财资讯标题。

原始数据写 data/scratch/experiments/exp_independent_pool_2026q3/<批次>/raw/<代码>/（不入库，14 天未改动即被清理），
数据包写 data/experiments/exp_independent_pool_2026q3/<批次>/packs/<代码>_<名称>.md。

    python3 -I tools/build_kit.py --batch b01 --price-date 2026-10-19 --codes 600066,920394 [--workers 8]
    python3 -I tools/build_kit.py --batch b01 --price-date 2026-10-19 --codes 600066 --pack-only   # 只用已有原始数据重出数据包
"""
import argparse
import csv
import json
import math
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_independent_pool_2026q3'

F10 = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
WEB = "https://datacenter-web.eastmoney.com/api/data/v1/get"
ANN = "https://np-anotice-stock.eastmoney.com/api/security/ann"
PEER = "https://emweb.securities.eastmoney.com/PC_HSF10/IndustryAnalysis/PageAjax"
NEWS = "https://search-api-web.eastmoney.com/search/jsonp"
H_EM = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}
H_TX = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
ANN_SINCE = '2025-01-01'
NEWS_MONTHS = 6
PDF_TIMEOUT = 900

# 公告选取：定期报告全文取最新一份；其余类别按公告日倒序取前 N 份。
EXCLUDE = re.compile(r'摘要|英文|English|H股|提示性公告|披露的提示|更正公告|补充公告|说明会|问询|审核|鉴证|专项说明|内部控制|社会责任|ESG|可持续|自愿性|网上|决议|第三支柱')
PERIODIC = [  # 「2025年度报告」「2026半年度报告」等写法都要认
    ('2025_annual_report', re.compile(r'2025\s*年?\s*(年度报告|年报)')),
    ('2026Q1_report', re.compile(r'2026\s*年?\s*(第一季度|一季度|1\s*季度)报告')),
    ('2026H1_report', re.compile(r'2026\s*年?\s*(半年度报告|中期报告|半年报)')),
    ('2026Q3_report', re.compile(r'2026\s*年?\s*(第三季度|三季度|3\s*季度)报告')),
]
CATEGORIES = [  # (前缀, 包含, 排除, 份数)
    ('forecast', r'业绩预告|业绩快报|业绩预增|业绩预减|业绩预亏|扭亏为盈', r'说明会|2024\s*年', 4),
    ('IR', r'投资者关系活动记录|投资者关系管理信息|调研活动|接待.*调研', r'制度', 4),
    ('results_call', r'业绩说明会.*(召开情况|记录|纪要)|说明会.*(召开情况|记录)', r'', 2),
    ('dividend', r'利润分配|权益分派|分红', r'说明会|制度|规划（', 4),
    ('buyback', r'回购', r'回购注销|说明会|制度|业绩补偿', 3),
    ('holders', r'减持|增持|质押|可交换|协议转让|权益变动', r'制度|说明会', 5),
    ('related_party', r'日常关联交易|财务公司', r'制度', 2),
    ('regulatory', r'问询函|关注函|监管函|警示函|监管措施|行政处罚|处罚决定|立案|留置|调查|责令改正|纪律处分|通报批评|监管工作函', r'制度|回复.*延期', 8),
    ('mna', r'收购|重大资产|重组|出售资产|购买资产|吸收合并|分拆', r'回购|要约收购义务|制度|管理办法', 3),
    ('incentive', r'激励计划（草案）|激励计划\(草案\)|员工持股计划（草案）|员工持股计划\(草案\)', r'摘要', 2),
    ('contract', r'重大合同|中标|签订.*合同|框架协议', r'制度', 2),
    ('invest', r'对外投资|投资建设|项目投资|扩产|募集资金投资项目|新建.*项目', r'制度|理财|现金管理', 3),
    ('auditor', r'(变更|续聘|拟聘|改聘|聘任|聘请).*会计师事务所|会计师事务所.*(变更|续聘|拟聘|改聘)', r'制度|费用', 1),
    ('litigation', r'诉讼|仲裁', r'制度', 2),
    ('impairment', r'计提.*减值|资产减值准备|核销', r'制度', 2),
    ('financing', r'向特定对象发行|非公开发行|配股|可转换公司债券|发行股份', r'摘要|制度|发行结果暨|解除限售|上市流通', 2),
    ('management', r'辞职|辞任|聘任.*(总经理|总裁|财务负责人)|选举.*董事长|董事长.*变更', r'制度|独立董事', 3),
    ('risk', r'风险提示', r'异常波动|停牌', 2),
]


NOISE = re.compile(r'法律意见书|核查意见|自查报告|独立财务顾问|承诺函|律师事务所关于|保荐|持续督导|摘要|英文|English')


def secucode(code: str) -> str:
    if code.startswith(('92', '8', '4')):
        return code + '.BJ'
    return code + ('.SH' if code[0] in '69' else '.SZ')


def tx_symbol(code: str) -> str:
    if code.startswith(('92', '8', '4')):
        return 'bj' + code
    return ('sh' if code[0] in '69' else 'sz') + code


def http(url: str, params: dict | None = None, headers: dict | None = None, raw: bool = False, enc: str = 'utf-8', tries: int = 3):
    full = url + ('?' + urllib.parse.urlencode(params) if params else '')
    err = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers=headers or H_EM), timeout=60) as resp:
                body = resp.read()
            return body if raw else body.decode(enc, 'replace')
        except Exception as exc:  # 网络抖动重试
            err = exc
            time.sleep(2 + 2 * i)
    raise RuntimeError(f'{full[:160]}: {err}')


def em_rows(url: str, params: dict) -> list:
    try:
        payload = json.loads(http(url, params))
    except Exception as exc:
        print('  取数失败', params.get('reportName'), exc, flush=True)
        return []
    return ((payload.get('result') or {}).get('data')) or []


def fetch_f10(code: str) -> dict:
    d: dict = {}
    for kind, suffix in (('income', 'INCOME'), ('balance', 'BALANCE'), ('cashflow', 'CASHFLOW')):
        for prefix, key in (('G', kind), ('B', f'{kind}_bank'), ('I', f'{kind}_insurance')):
            rows = em_rows(F10, {"reportName": f"RPT_F10_FINANCE_{prefix}{suffix}", "columns": "ALL",
                                 "filter": f'(SECUCODE="{secucode(code)}")', "pageNumber": "1", "pageSize": "200",
                                 "sortTypes": "-1", "sortColumns": "REPORT_DATE", "source": "HSF10", "client": "PC"})
            if rows or prefix == 'G':
                d[key] = rows
            time.sleep(0.2)
    d['mainop'] = em_rows(F10, {"reportName": "RPT_F10_FN_MAINOP", "columns": "ALL", "filter": f'(SECUCODE="{secucode(code)}")',
                                "pageNumber": "1", "pageSize": "500", "sortTypes": "-1", "sortColumns": "REPORT_DATE",
                                "source": "HSF10", "client": "PC"})
    d['dividends'] = em_rows(WEB, {"reportName": "RPT_SHAREBONUS_DET", "columns": "ALL", "filter": f'(SECURITY_CODE="{code}")',
                                   "pageNumber": "1", "pageSize": "100", "sortTypes": "-1", "sortColumns": "PLAN_NOTICE_DATE",
                                   "source": "WEB", "client": "WEB"})
    return d


def fetch_tencent(code: str, price_date: str, d: dict) -> None:
    sym = tx_symbol(code)
    begin = (date.fromisoformat(price_date) - timedelta(days=380)).isoformat()
    for fq, key in (('', 'tx_month'), ('hfq', 'tx_hfqmonth')):
        try:
            data = json.loads(http(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},month,2010-01-01,{price_date},400,{fq}", headers=H_TX))['data'][sym]
            d[key] = data.get('hfqmonth' if fq else 'month') or data.get('month') or []
        except Exception:
            d[key] = []
    try:
        data = json.loads(http(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{begin},{price_date},400,", headers=H_TX))['data'][sym]
        d['tx_day'] = data.get('day') or []
    except Exception:
        d['tx_day'] = []
    quote = http(f"https://qt.gtimg.cn/q={sym}", headers=H_TX, enc='gbk')
    d['tx_quote'] = quote.split('"')[1].split('~') if '"' in quote else []


def fetch_peers(code: str) -> dict:
    prefix = 'BJ' if secucode(code).endswith('BJ') else secucode(code)[-2:]
    try:
        return json.loads(http(PEER, {"code": f"{prefix}{code}"}))
    except Exception as exc:
        return {'error': str(exc)}


def fetch_announcements(code: str, begin: str, end: str) -> list:
    out, page = [], 1
    while True:
        try:
            data = json.loads(http(ANN, dict(sr=-1, page_size=100, page_index=page, ann_type='A', client_source='web',
                                             stock_list=code, begin_time=begin, end_time=end), headers={"User-Agent": "Mozilla/5.0"})).get('data') or {}
        except Exception as exc:
            print('  公告目录失败', code, page, exc, flush=True)
            break
        rows = data.get('list') or []
        out.extend(rows)
        if not rows or len(out) >= int(data.get('total_hits') or 0) or page >= 30:
            break
        page += 1
        time.sleep(0.3)
    return out


def fetch_news(name: str, since: str) -> list:
    seen, out = set(), []
    for page in (1, 2, 3):
        param = {"uid": "", "keyword": name, "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web", "clientVersion": "curr",
                 "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "time", "pageIndex": page, "pageSize": 100,
                                                "preTag": "", "postTag": ""}}}
        try:
            raw = http(NEWS + "?cb=cb&param=" + urllib.parse.quote(json.dumps(param, ensure_ascii=False)),
                       headers={"User-Agent": "Mozilla/5.0", "Referer": "https://so.eastmoney.com/"})
            data = json.loads(raw[raw.index('(') + 1:raw.rindex(')')])
        except Exception:
            break
        rows = (data.get('result') or {}).get('cmsArticleWebOld') or []
        for a in rows:
            title = re.sub(r'</?em>', '', a.get('title') or '').strip()
            day = (a.get('date') or '')[:10]
            if day < since or name not in title or title in seen:
                continue
            seen.add(title)
            out.append(dict(date=day, title=title, media=a.get('mediaName') or '', url=a.get('url') or ''))
        if not rows or min((a.get('date') or '9')[:10] for a in rows) < since:
            break
        time.sleep(0.3)
    return out


def clean_title(item: dict) -> str:
    return re.sub(r'</?em>', '', item.get('title_ch') or item.get('title') or '').strip()


def select_documents(anns: list, until: str) -> list[dict]:
    items = sorted(({'art': a.get('art_code') or '', 'date': (a.get('notice_date') or '')[:10], 'title': clean_title(a)} for a in anns),
                   key=lambda x: (x['date'], x['art']), reverse=True)
    items = [x for x in items if x['art'] and x['date'] <= until]
    picked, used = [], set()
    for stem, pattern in PERIODIC:
        cands = [x for x in items if pattern.search(x['title']) and not EXCLUDE.search(x['title'])]
        if cands:
            x = cands[0]
            picked.append(dict(x, file=stem, category='periodic'))
            used.add(x['art'])
    for prefix, inc, exc, limit in CATEGORIES:
        inc_re, exc_re = re.compile(inc), re.compile(exc) if exc else None
        n = 0
        for x in items:
            if n >= limit:
                break
            if x['art'] in used or not inc_re.search(x['title']) or (exc_re and exc_re.search(x['title'])):
                continue
            if NOISE.search(x['title']):
                continue
            picked.append(dict(x, file=f"{prefix}_{x['date'].replace('-', '')}_{x['art'][-6:]}", category=prefix))
            used.add(x['art'])
            n += 1
    return picked


CONTENT = "https://np-cnotice-stock.eastmoney.com/api/content/ann"


def content_fallback(doc: dict, pdf_path: Path, txt_path: Path) -> None:
    """标准链接不是 PDF 时（科创板投资者关系记录等）：先取内容接口给出的附件 PDF，取不到就把正文逐页写成文本。"""
    try:
        data = json.loads(http(CONTENT, dict(art_code=doc['art'], client_source='web', page_index=1),
                               headers={"User-Agent": "Mozilla/5.0"})).get('data') or {}
    except Exception as exc:
        doc['error'] = f'内容接口失败：{str(exc)[:80]}'
        return
    for att in data.get('attach_list') or []:
        url = att.get('attach_url') or ''
        if not url:
            continue
        try:
            body = http(url, headers={"User-Agent": "Mozilla/5.0"}, raw=True)
        except Exception:
            continue
        if body[:4] == b'%PDF':
            pdf_path.write_bytes(body)
            doc['url'] = url.split('?')[0]
            doc.pop('error', None)
            return
    pages = [data.get('notice_content') or '']
    for i in range(2, int(data.get('page_size') or 1) + 1):
        try:
            more = json.loads(http(CONTENT, dict(art_code=doc['art'], client_source='web', page_index=i),
                                   headers={"User-Agent": "Mozilla/5.0"})).get('data') or {}
            pages.append(more.get('notice_content') or '')
        except Exception:
            break
    if any(x.strip() for x in pages):
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(''.join(f'\n=== 第 {i} 页 ===\n{x}\n' for i, x in enumerate(pages, 1)), encoding='utf-8')
        doc['url'] = f"{CONTENT}?art_code={doc['art']}&client_source=web&page_index=1"
        doc['error'] = ''
        doc['text_only'] = True
    else:
        doc['error'] = '非 PDF 且无正文'


def download_docs(code: str, docs: list[dict], raw_dir: Path) -> None:
    pdf_dir = raw_dir / 'pdf'
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        path = pdf_dir / f"{doc['file']}.pdf"
        txt = raw_dir / 'txt' / f"{doc['file']}.txt"
        doc['url'] = f"https://pdf.dfcfw.com/pdf/H2_{doc['art']}_1.pdf"
        if (path.exists() and path.stat().st_size > 1000) or (txt.exists() and txt.stat().st_size > 0):
            continue
        try:
            body = http(doc['url'], headers={"User-Agent": "Mozilla/5.0"}, raw=True)
            if body[:4] == b'%PDF':
                path.write_bytes(body)
            else:
                content_fallback(doc, path, txt)
        except Exception as exc:
            doc['error'] = str(exc)[:120]
        time.sleep(0.2)


def extract_texts(jobs: list[tuple[Path, Path]], workers: int) -> None:
    def run(job):
        pdf, txt = job
        if txt.exists() and txt.stat().st_size > 0:
            return
        txt.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run([sys.executable, '-I', str(TOOLS / 'pdf_text.py'), str(pdf), str(txt)], timeout=PDF_TIMEOUT,
                           check=True, capture_output=True)
        except Exception as exc:
            txt.write_text(f'[文本抽取失败：{type(exc).__name__}]\n', encoding='utf-8')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run, jobs))


# ---------------------------------------------------------------- 数据包

def f(x) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except (TypeError, ValueError):
        return 0.0


def yi(x: float) -> str:
    return f"{x / 1e8:,.2f}" if x else "—"


def pct(x, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%" if x is not None and isinstance(x, float) and math.isfinite(x) else "—"


def by_date(rows: list) -> dict:
    out = {}
    for r in rows:
        d = (r.get('REPORT_DATE') or '')[:10]
        if d and d not in out:
            out[d] = r
    return out


# 拆出资金计入现金类：财务公司把吸收的存款拆给同业，负债端的吸收存款及同业存放已计入 DEBT
CASH_KEYS = ['MONETARYFUNDS', 'LEND_FUND', 'TRADE_FINASSET_NOTFVTPL', 'TRADE_FINASSET', 'DERIVE_FINASSET']
OTHER_FIN = ['OTHER_CURRENT_ASSET', 'NONCURRENT_ASSET_1YEAR', 'CREDITOR_INVEST', 'OTHER_CREDITOR_INVEST', 'OTHER_NONCURRENT_FINASSET',
             'OTHER_EQUITY_INVEST', 'AVAILABLE_SALE_FINASSET', 'HOLD_MATURITY_INVEST', 'BUY_RESALE_FINASSET', 'LOAN_ADVANCE', 'LONG_EQUITY_INVEST']
DEBT = ['SHORT_LOAN', 'LONG_LOAN', 'BOND_PAYABLE', 'NONCURRENT_LIAB_1YEAR', 'LEASE_LIAB', 'TRADE_FINLIAB_NOTFVTPL', 'TRADE_FINLIAB',
        'DERIVE_FINLIAB', 'ACCEPT_DEPOSIT_INTERBANK', 'BORROW_FUND', 'SELL_REPO_FINASSET', 'LOAN_PBC', 'SHORT_BOND_PAYABLE']
OP_LIAB = ['NOTE_PAYABLE', 'ACCOUNTS_PAYABLE', 'NOTE_ACCOUNTS_PAYABLE', 'ADVANCE_RECEIVABLES', 'CONTRACT_LIAB', 'OTHER_CURRENT_LIAB',
           'TOTAL_OTHER_PAYABLE', 'STAFF_SALARY_PAYABLE', 'TAX_PAYABLE', 'PREDICT_LIAB', 'DEFER_INCOME']
OP_ASSETS = ['NOTE_RECE', 'ACCOUNTS_RECE', 'NOTE_ACCOUNTS_RECE', 'FINANCE_RECE', 'PREPAYMENT', 'TOTAL_OTHER_RECE', 'INVENTORY',
             'CONTRACT_ASSET', 'LONG_RECE', 'FIXED_ASSET', 'CIP', 'INTANGIBLE_ASSET', 'GOODWILL', 'USERIGHT_ASSET', 'INVEST_REALESTATE',
             'DEVELOP_EXPENSE', 'LONG_PREPAID_EXPENSE', 'DEFER_TAX_ASSET', 'OTHER_NONCURRENT_ASSET']


def pick(b: dict, keys: list) -> dict:
    return {k: f(b.get(k)) for k in keys if f(b.get(k))}


def price_on(d: dict, price_date: str) -> tuple[float, str]:
    """价格日收盘（腾讯日线，不复权）；日线缺该日时退回报价现价。"""
    for row in reversed(d.get('tx_day') or []):
        if len(row) > 2 and row[0] <= price_date:
            return f(row[2]), f'腾讯日线 {row[0]}'
    q = d.get('tx_quote') or []
    return (f(q[3]) if len(q) > 3 else 0.0), '腾讯报价'


def peer_section(peers: dict) -> list[str]:
    L = ["\n## 九、同业比较（东财 F10 同行业，按东财行业分类；预测类读数为券商一致预期）\n"]
    if not peers or peers.get('error'):
        L.append(f"未取到（{peers.get('error') if peers else '空'}）")
        return L
    gz = peers.get('gzbj') or []
    if gz:
        L.append("| 公司 | PE(静) | PE(TTM) | PE(今年预测) | PE(明年预测) | PB(MRQ) | PS(TTM) | PCF(TTM) | PEG |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in gz:
            def n(k):
                v = r.get(k)
                return f"{float(v):.2f}" if isinstance(v, (int, float)) else '—'
            L.append(f"| {r.get('CORRE_SECURITY_NAME')}（{r.get('CORRE_SECURITY_CODE')}） | {n('PE')} | {n('PE_TTM')} | {n('PE_1Y')} | {n('PE_2Y')} | {n('PB_MRQ')} | {n('PS_TTM')} | {n('PCF_TTM')} | {n('PEG')} |")
    cz = peers.get('czxbj') or []
    if cz:
        L.append("\n| 公司 | 营收同比% | 净利同比% | 营收 3 年复合% | 净利 3 年复合% | 营收 TTM 同比% | 净利 TTM 同比% | 预测净利增速今年／明年／后年% |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in cz:
            def n(k):
                v = r.get(k)
                return f"{float(v):.1f}" if isinstance(v, (int, float)) else '—'
            L.append(f"| {r.get('CORRE_SECURITY_NAME')}（{r.get('CORRE_SECURITY_CODE')}） | {n('YYSRTB')} | {n('JLRTB')} | {n('YYSR_3Y')} | {n('JLR_3Y')} | {n('YYSRTTM')} | {n('JLRTTM')} | {n('JLR_1E')}／{n('JLR_2E')}／{n('JLR_3E')} |")
        L.append(f"\n成长与估值比较的报告期：{(cz[0].get('REPORT_DATE') or '')[:10]}。")
    db = peers.get('dbfxbj') or []
    if db:
        L.append("\n| 公司 | ROE 三年平均% | 净利率三年平均% | 总资产周转% | 权益乘数% |")
        L.append("|---|---|---|---|---|")
        for r in db:
            def n(k):
                v = r.get(k)
                return f"{float(v):.2f}" if isinstance(v, (int, float)) else '—'
            L.append(f"| {r.get('CORRE_SECURITY_NAME')}（{r.get('CORRE_SECURITY_CODE')}） | {n('ROE_AVG')} | {n('XSJLL_AVG')} | {n('TOAZZL_AVG')} | {n('QYCS_AVG')} |")
    return L


def build_pack(code: str, d: dict, price_date: str, docs: list[dict], news: list[dict], raw_rel: str) -> tuple[str, str, dict]:
    inc, bal, cf = by_date(d['income']), by_date(d['balance']), by_date(d['cashflow'])
    q = d.get('tx_quote') or []
    name = (q[1] if len(q) > 1 and q[1] else None) or (d['income'][0].get('SECURITY_NAME_ABBR') if d['income'] else code)
    price, price_src = price_on(d, price_date)
    total_shares = f(q[73]) if len(q) > 73 else 0.0
    float_shares = f(q[72]) if len(q) > 72 else 0.0
    years = sorted(k for k in inc if k.endswith('12-31'))
    periods = sorted(inc)
    latest = periods[-1] if periods else ''
    bL = bal.get(latest, {})
    sc_latest = f(bL.get('SHARE_CAPITAL'))
    shares = total_shares or sc_latest
    mcap = price * shares
    special = [k for k in ('income_bank', 'income_insurance') if d.get(k)]
    L = [f"# {name}（{code}）独立分析数据包\n",
         f"数据来源：东方财富 F10 三大报表、主营构成、分红明细与同行业比较，腾讯行情，东财公告与资讯；抓取于 {date.today().isoformat()}。"
         f"金额单位亿元（另注明者除外）。价格日 {price_date}。原始数据在 `{raw_rel}/`。\n"]
    if special:
        L.append(f"本公司为{'银行' if 'income_bank' in special else '保险'}，一般企业口径的表格只作参考，专用口径三表在原始 JSON 的 `{'、'.join(special)}` 等键，关键监管指标看定期报告原文。\n")
    L.append("## 一、快照\n")
    L.append(f"- 收盘价（{price_date}，A 股未复权，来源 {price_src}）：**{price:.2f}** 元；总股本（行情口径）{shares / 1e8:,.4f} 亿股"
             f"（流通 {float_shares / 1e8:,.4f} 亿股）；资产负债表股本（{latest}）{sc_latest / 1e8:,.4f} 亿股")
    L.append(f"- A 股价 × 总股本 = **{mcap / 1e8:,.2f} 亿元**（腾讯行情字段：总市值 {q[45] if len(q) > 45 else '—'} 亿、PB {q[46] if len(q) > 46 else '—'}、"
             f"PE(TTM) {q[39] if len(q) > 39 else '—'}）。有 H 股或其他类别股份的，按各自价格另计。")
    days = [(r[0], f(r[2])) for r in (d.get('tx_day') or []) if len(r) > 2]
    if days:
        hi, lo = max(days, key=lambda x: x[1]), min(days, key=lambda x: x[1])
        L.append(f"- 近一年（{days[0][0]}→{days[-1][0]}）收盘区间 {lo[1]:.2f}（{lo[0]}）～{hi[1]:.2f}（{hi[0]}），区间涨跌 {(days[-1][1] / days[0][1] - 1) * 100:+.1f}%（未复权，未含分红）")

    def ttm(key, src):
        if not latest:
            return float('nan')
        if latest.endswith('12-31'):
            return f(src.get(latest, {}).get(key))
        prev_end, same_last = f"{int(latest[:4]) - 1}-12-31", f"{int(latest[:4]) - 1}{latest[4:]}"
        if prev_end in src and same_last in src and latest in src:
            return f(src[latest].get(key)) + f(src[prev_end].get(key)) - f(src[same_last].get(key))
        return float('nan')
    ttm_rev, ttm_np, ttm_dnp = ttm('TOTAL_OPERATE_INCOME', inc), ttm('PARENT_NETPROFIT', inc), ttm('DEDUCT_PARENT_NETPROFIT', inc)
    ttm_ocf, ttm_capex = ttm('NETCASH_OPERATE', cf), ttm('CONSTRUCT_LONG_ASSET', cf)
    peq = f(bL.get('TOTAL_PARENT_EQUITY'))
    L.append(f"- TTM（截至 {latest}）：营收 {yi(ttm_rev)}、归母净利 {yi(ttm_np)}、扣非归母 {yi(ttm_dnp)}、经营现金流 {yi(ttm_ocf)}、购建长期资产 {yi(ttm_capex)}")
    if peq and ttm_np and math.isfinite(ttm_np) and ttm_np > 0:
        L.append(f"- 市值/TTM 归母 = **{mcap / ttm_np:.2f}×**；市值/TTM 扣非 = {mcap / ttm_dnp if ttm_dnp and math.isfinite(ttm_dnp) and ttm_dnp > 0 else float('nan'):.2f}×；"
                 f"市值/最新归母权益 = **{mcap / peq:.2f}×**（归母权益 {yi(peq)}）")
    L.append(f"\n## 二、最新资产负债表结构（{latest}）\n")
    cl, dbt = sum(f(bL.get(k)) for k in CASH_KEYS), pick(bL, DEBT)
    L.append(f"- 货币资金 {yi(f(bL.get('MONETARYFUNDS')))}；拆出资金 {yi(f(bL.get('LEND_FUND')))}；"
             f"交易性金融资产 {yi(f(bL.get('TRADE_FINASSET_NOTFVTPL')) + f(bL.get('TRADE_FINASSET')))}；"
             f"衍生金融资产 {yi(f(bL.get('DERIVE_FINASSET')))} → 现金类合计 **{yi(cl)}**")
    L.append("- 其他可能含金融资产的科目（须结合附注判断）：" + ("；".join(f"{k} {yi(v)}" for k, v in pick(bL, OTHER_FIN).items()) or "无"))
    L.append("- 有息及类金融负债：" + ("；".join(f"{k} {yi(v)}" for k, v in dbt.items()) or "无") + f" → 合计 **{yi(sum(dbt.values()))}**")
    L.append(f"- 现金类 − 有息负债 = **{yi(cl - sum(dbt.values()))}**（未计其他金融资产；受限资金、客户存款等须看附注）")
    L.append("- 经营性负债：" + "；".join(f"{k} {yi(v)}" for k, v in pick(bL, OP_LIAB).items()))
    L.append("- 经营性资产：" + "；".join(f"{k} {yi(v)}" for k, v in pick(bL, OP_ASSETS).items()))
    L.append(f"- 总资产 {yi(f(bL.get('TOTAL_ASSETS')))}；总负债 {yi(f(bL.get('TOTAL_LIABILITIES')))}；归母权益 {yi(peq)}；"
             f"少数股东权益 {yi(f(bL.get('MINORITY_EQUITY')))}；库存股 {yi(f(bL.get('TREASURY_SHARES')))}")
    L.append("\n## 三、年度利润表与现金流（亿元）\n")
    hdr = ("| 年度 | 营收 | 同比 | 毛利率 | 销售费率 | 管理费率 | 研发费率 | 营业利润率 | 归母净利 | 扣非归母 | 净利率 | ROE(平均归母) | 经营现金流 | "
           "购建长期资产 | 自由现金流 | 折旧摊销 | 分配股利利息付现 | 投资收益+公允价值 | 减值损失(资产+信用) | 其他收益 | 少数股东损益 |")
    L += [hdr, "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|"]
    prev_rev = prev_eq = None
    for y in years:
        r, c, b = inc[y], cf.get(y, {}), bal.get(y, {})
        rev = f(r.get('TOTAL_OPERATE_INCOME'))
        oi = f(r.get('OPERATE_INCOME')) or rev
        gm = 1 - f(r.get('OPERATE_COST')) / oi if oi else float('nan')
        eq = f(b.get('TOTAL_PARENT_EQUITY'))
        np_, dnp = f(r.get('PARENT_NETPROFIT')), f(r.get('DEDUCT_PARENT_NETPROFIT'))
        roe = np_ / ((eq + prev_eq) / 2) if prev_eq else (np_ / eq if eq else float('nan'))
        ocf, capex = f(c.get('NETCASH_OPERATE')), f(c.get('CONSTRUCT_LONG_ASSET'))
        da = f(c.get('FA_IR_DEPR')) + f(c.get('IA_AMORTIZE')) + f(c.get('LPE_AMORTIZE')) + f(c.get('USERIGHT_ASSET_AMORTIZE'))
        inv = f(r.get('INVEST_INCOME')) + f(r.get('FAIRVALUE_CHANGE_INCOME'))
        imp = (f(r.get('ASSET_IMPAIRMENT_INCOME')) + f(r.get('CREDIT_IMPAIRMENT_INCOME'))
               - f(r.get('ASSET_IMPAIRMENT_LOSS')) - f(r.get('CREDIT_IMPAIRMENT_LOSS')))
        if y >= '2013-12-31':
            yoy = (rev / prev_rev - 1) if prev_rev else float('nan')
            ratio = (lambda k: pct(f(r.get(k)) / rev) if rev else '—')
            L.append(f"| {y[:4]} | {yi(rev)} | {pct(yoy)} | {pct(gm)} | {ratio('SALE_EXPENSE')} | {ratio('MANAGE_EXPENSE')} | {ratio('RESEARCH_EXPENSE')} | "
                     f"{ratio('OPERATE_PROFIT')} | {yi(np_)} | {yi(dnp)} | {pct(np_ / rev) if rev else '—'} | {pct(roe)} | {yi(ocf)} | {yi(capex)} | "
                     f"{yi(ocf - capex)} | {yi(da)} | {yi(f(c.get('ASSIGN_DIVIDEND_PORFIT')))} | {yi(inv)} | {yi(imp)} | {yi(f(r.get('OTHER_INCOME')))} | "
                     f"{yi(f(r.get('MINORITY_INTEREST')))} |")
        prev_rev, prev_eq = rev, eq
    L.append("\n## 四、年度资产负债要点（亿元，年末）\n")
    hdr = ("| 年末 | 现金类 | 有息负债 | 现金类−有息负债 | 应收(票据+账款+融资) | 存货 | 合同资产 | 合同负债+预收 | 应付(票据+账款) | 其他流动负债 | "
           "固定资产+在建 | 商誉 | 归母权益 | 少数股东权益 | 总股本(亿股) |")
    L += [hdr, "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|"]
    for y in years:
        b = bal.get(y, {})
        if y < '2013-12-31' or not b:
            continue
        rec = f(b.get('NOTE_RECE')) + f(b.get('ACCOUNTS_RECE')) + f(b.get('FINANCE_RECE'))
        if not (f(b.get('NOTE_RECE')) or f(b.get('ACCOUNTS_RECE'))):
            rec += f(b.get('NOTE_ACCOUNTS_RECE'))
        pay = f(b.get('NOTE_PAYABLE')) + f(b.get('ACCOUNTS_PAYABLE')) or f(b.get('NOTE_ACCOUNTS_PAYABLE'))
        dd, cc = sum(pick(b, DEBT).values()), sum(f(b.get(k)) for k in CASH_KEYS)
        L.append(f"| {y[:4]} | {yi(cc)} | {yi(dd)} | {yi(cc - dd)} | {yi(rec)} | {yi(f(b.get('INVENTORY')))} | {yi(f(b.get('CONTRACT_ASSET')))} | "
                 f"{yi(f(b.get('CONTRACT_LIAB')) + f(b.get('ADVANCE_RECEIVABLES')))} | {yi(pay)} | {yi(f(b.get('OTHER_CURRENT_LIAB')))} | "
                 f"{yi(f(b.get('FIXED_ASSET')) + f(b.get('CIP')))} | {yi(f(b.get('GOODWILL')))} | {yi(f(b.get('TOTAL_PARENT_EQUITY')))} | "
                 f"{yi(f(b.get('MINORITY_EQUITY')))} | {f(b.get('SHARE_CAPITAL')) / 1e8:,.4f} |")
    L.append("\n## 五、近 12 个季度单季数据（亿元）\n")

    def single(key, src, p):
        r = src.get(p)
        if not r:
            return float('nan')
        if p[5:] == '03-31':
            return f(r.get(key))
        pr = src.get(p[:5] + {'06-30': '03-31', '09-30': '06-30', '12-31': '09-30'}[p[5:]])
        return f(r.get(key)) - f(pr.get(key)) if pr else float('nan')
    hdr = "| 单季 | 营收 | 营收同比 | 毛利率 | 归母净利 | 归母同比 | 扣非归母 | 经营现金流 |"
    L += [hdr, "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|"]
    for p in [p for p in periods if p >= '2023-01-01'][-12:]:
        rev, oi, oc = single('TOTAL_OPERATE_INCOME', inc, p), single('OPERATE_INCOME', inc, p), single('OPERATE_COST', inc, p)
        np_, dnp, ocf = single('PARENT_NETPROFIT', inc, p), single('DEDUCT_PARENT_NETPROFIT', inc, p), single('NETCASH_OPERATE', cf, p)
        lp = f"{int(p[:4]) - 1}{p[4:]}"
        rev_l, np_l = single('TOTAL_OPERATE_INCOME', inc, lp), single('PARENT_NETPROFIT', inc, lp)
        gm = 1 - oc / oi if oi and math.isfinite(oi) else float('nan')
        L.append(f"| {p} | {yi(rev) if math.isfinite(rev) else '—'} | {pct(rev / rev_l - 1) if rev_l and math.isfinite(rev_l) and math.isfinite(rev) else '—'} | {pct(gm)} | "
                 f"{yi(np_) if math.isfinite(np_) else '—'} | {pct(np_ / np_l - 1) if np_l and math.isfinite(np_l) and np_l > 0 and math.isfinite(np_) else '—'} | "
                 f"{yi(dnp) if math.isfinite(dnp) else '—'} | {yi(ocf) if math.isfinite(ocf) else '—'} |")
    L.append("\n## 六、主营构成（最新年报、最新中报与两年前年报）\n")
    mo = d.get('mainop') or []
    rep_dates = sorted({(r.get('REPORT_DATE') or '')[:10] for r in mo}, reverse=True)
    chosen = []
    for rd in rep_dates:
        if rd.endswith('06-30') and not any(p.endswith('06-30') for p in chosen):
            chosen.append(rd)
        if rd.endswith('12-31') and not any(p.endswith('12-31') for p in chosen):
            chosen.append(rd)
        if len(chosen) >= 2:
            break
    ann_dates = [rd for rd in rep_dates if rd.endswith('12-31')]
    if len(ann_dates) >= 3:
        chosen.append(ann_dates[2])
    tmap = {'1': '按行业', '2': '按产品', '3': '按地区'}
    for rd in chosen:
        rows = [r for r in mo if (r.get('REPORT_DATE') or '')[:10] == rd]
        for t in ('1', '2', '3'):
            rr = [r for r in rows if str(r.get('MAINOP_TYPE')) == t]
            if rr:
                L.append(f"**{rd} {tmap[t]}**：" + "；".join(
                    f"{r.get('ITEM_NAME')} {yi(f(r.get('MAIN_BUSINESS_INCOME')))}（占 {pct(f(r.get('MBI_RATIO')))}，毛利率 {pct(f(r.get('GROSS_RPOFIT_RATIO')))}）"
                    for r in sorted(rr, key=lambda r: -f(r.get('MAIN_BUSINESS_INCOME')))[:10]))
                L.append("")
    L.append("## 七、分红记录（税前现金）\n")
    divs = d.get('dividends') or []
    hdr = "| 报告期 | 方案 | 进度 | 除息日 | 每股现金 | 当期基本EPS | 分红率(每股现金/EPS) |"
    L += [hdr, "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|"]
    for r in sorted(divs, key=lambda r: r.get('REPORT_DATE') or '', reverse=True)[:16]:
        dps, eps = f(r.get('PRETAX_BONUS_RMB')) / 10, f(r.get('BASIC_EPS'))
        L.append(f"| {(r.get('REPORT_DATE') or '')[:10]} | {r.get('IMPL_PLAN_PROFILE')} | {r.get('ASSIGN_PROGRESS')} | {(r.get('EX_DIVIDEND_DATE') or '')[:10]} | "
                 f"{dps:.4f} | {eps:.4f} | {pct(dps / eps) if eps > 0 else '—'} |")
    start = (date.fromisoformat(price_date) - timedelta(days=364)).isoformat()
    ttm_dps = sum(f(r.get('PRETAX_BONUS_RMB')) / 10 for r in divs
                  if start <= (r.get('EX_DIVIDEND_DATE') or '')[:10] <= price_date and r.get('ASSIGN_PROGRESS') == '实施分配')
    L.append(f"\n- 过去 12 个月（{start}～{price_date} 除息）每股现金合计 {ttm_dps:.4f} 元，按现价股息率 **{pct(ttm_dps / price if price else float('nan'), 2)}**（未调整送转）")
    L.append("\n## 八、历史估值（年末 A 股收盘 × 年末总股本 ÷ 当年归母净利；÷ 年末归母权益）\n")
    ye_close = {r[0][:4]: f(r[2]) for r in (d.get('tx_month') or []) if len(r) > 2 and r[0][5:7] == '12'}
    hdr = "| 年末 | 收盘 | 总股本(亿股) | 市值 | PE(当年归母) | PB(年末归母权益) |"
    L += [hdr, "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|"]
    for y in years:
        yy = y[:4]
        if yy < '2014' or yy not in ye_close:
            continue
        b, r = bal.get(y, {}), inc[y]
        sh = f(b.get('SHARE_CAPITAL'))
        mc = ye_close[yy] * sh
        np_, eq = f(r.get('PARENT_NETPROFIT')), f(b.get('TOTAL_PARENT_EQUITY'))
        L.append(f"| {yy} | {ye_close[yy]:.2f} | {sh / 1e8:,.4f} | {yi(mc)} | {mc / np_:.1f} | {mc / eq:.2f} |" if np_ > 0 and eq > 0
                 else f"| {yy} | {ye_close[yy]:.2f} | {sh / 1e8:,.4f} | {yi(mc)} | 亏损 | — |")
    L.append("\n注：未复权价格；送转与拆股年份以年末股本与收盘同口径即可比。")
    L += peer_section(d.get('peers') or {})
    L.append(f"\n## 十、公告原文（PDF 与逐页文本在 `{raw_rel}/pdf/`、`{raw_rel}/txt/`；页码指 PDF 物理页，即文本中的「=== 第 N 页 ===」）\n")
    L.append("| 文件 | 类别 | 公告日 | 标题 | 页数 |")
    L.append("|---|---|---|---|---|")
    for doc in docs:
        L.append(f"| `{doc['file']}` | {doc['category']} | {doc['date']} | {doc['title']} | {doc.get('pages', '—') if not doc.get('error') else '下载失败'} |")
    L.append("\n原文链接：`https://pdf.dfcfw.com/pdf/H2_<公告编号>_1.pdf`，编号见原始目录 `INDEX.tsv`。完整公告目录（2025-01-01 起）在 `announcements.json`。")
    L.append(f"\n## 十一、近 {NEWS_MONTHS} 个月东财资讯标题（标题含公司简称，按日期倒序，最多 60 条）\n")
    for n in news[:60]:
        L.append(f"- {n['date']} {n['title']}（{n['media']}）")
    if not news:
        L.append("未取到。")
    info = dict(name=name, price=price, price_src=price_src, shares_yi=shares / 1e8, mcap_yi=mcap / 1e8, latest=latest,
                pe_ttm=(mcap / ttm_np if ttm_np and math.isfinite(ttm_np) and ttm_np > 0 else None), pb=(mcap / peq if peq else None),
                parent_np_ttm_yi=(ttm_np / 1e8 if math.isfinite(ttm_np) else None), parent_equity_yi=peq / 1e8)
    return name, "\n".join(L) + "\n", info


def count_pages(txt: Path) -> int:
    try:
        return txt.read_text(encoding='utf-8').count('=== 第 ')
    except OSError:
        return 0


def process(code: str, args, raw_root: Path) -> list[tuple[Path, Path]]:
    raw = raw_root / code
    raw.mkdir(parents=True, exist_ok=True)
    jf = raw / 'f10.json'
    if args.pack_only and jf.exists():
        return []
    t0 = time.time()
    d = fetch_f10(code)
    fetch_tencent(code, args.price_date, d)
    d['peers'] = fetch_peers(code)
    jf.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    anns = fetch_announcements(code, ANN_SINCE, args.evidence_until)
    (raw / 'announcements.json').write_text(json.dumps(anns, ensure_ascii=False), encoding='utf-8')
    docs = select_documents(anns, args.evidence_until)
    download_docs(code, docs, raw)
    with (raw / 'INDEX.tsv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['file', 'category', 'art_code', 'notice_date', 'title', 'url', 'error'])
        for doc in docs:
            w.writerow([doc['file'], doc['category'], doc['art'], doc['date'], doc['title'], doc.get('url', ''), doc.get('error', '')])
    q = d.get('tx_quote') or []
    name = q[1] if len(q) > 1 and q[1] else code
    since = (date.fromisoformat(args.price_date) - timedelta(days=30 * NEWS_MONTHS)).isoformat()
    (raw / 'news.json').write_text(json.dumps(fetch_news(name, since), ensure_ascii=False), encoding='utf-8')
    print(f"{code} {name}：报表 {len(d['income'])} 期，公告 {len(anns)} 条，选取 {len(docs)} 份，{time.time() - t0:.0f} 秒", flush=True)
    return [(raw / 'pdf' / f"{doc['file']}.pdf", raw / 'txt' / f"{doc['file']}.txt") for doc in docs
            if not doc.get('error') and not doc.get('text_only')]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', required=True)
    ap.add_argument('--price-date', required=True)
    ap.add_argument('--codes', required=True)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--pack-only', action='store_true')
    ap.add_argument('--evidence-until', default=None, help='公告日上限，缺省为运行日（北京时间）次日：晚间发布的公告记次日日期')
    args = ap.parse_args()
    if not args.evidence_until:
        beijing_today = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
        args.evidence_until = (beijing_today + timedelta(days=1)).isoformat()
    codes = [c.strip().zfill(6) for c in args.codes.split(',') if c.strip()]
    raw_root = SCRATCH / args.batch / 'raw'
    packs = EXP / args.batch / 'packs'
    packs.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=min(args.workers, len(codes))) as pool:
        jobs = [j for js in pool.map(lambda c: process(c, args, raw_root), codes) for j in js]
    extract_texts(jobs, args.workers)
    summary = []
    for code in codes:
        raw = raw_root / code
        d = json.loads((raw / 'f10.json').read_text(encoding='utf-8'))
        docs = []
        with (raw / 'INDEX.tsv').open(encoding='utf-8') as fh:
            for row in csv.DictReader(fh, delimiter='\t'):
                docs.append(dict(file=row['file'], category=row['category'], art=row['art_code'], date=row['notice_date'],
                                 title=row['title'], error=row['error'], pages=count_pages(raw / 'txt' / f"{row['file']}.txt")))
        news = json.loads((raw / 'news.json').read_text(encoding='utf-8')) if (raw / 'news.json').exists() else []
        raw_rel = str(raw.relative_to(ROOT))
        name, text, info = build_pack(code, d, args.price_date, docs, news, raw_rel)
        (packs / f"{code}_{name}.md").write_text(text, encoding='utf-8')
        failed = [x['file'] for x in docs if x['error'] or not x['pages']]
        periodic = sorted(x['file'] for x in docs if x['category'] == 'periodic' and not x['error'])
        summary.append(dict(code=code, **info, docs=len(docs), failed=failed, periodic=periodic))
        print(f"{code} {name} 价 {info['price']:.2f}（{info['price_src']}）市值 {info['mcap_yi']:,.1f} 亿 最新期 {info['latest']} "
              f"定期报告 {periodic} 失败 {failed}", flush=True)
    (SCRATCH / args.batch / 'kit_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
