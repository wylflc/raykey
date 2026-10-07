#!/usr/bin/env python3
"""Build a markdown data pack per company from raw/<code>.json (statements, segments, dividends, prices)."""
import json, sys, math
from pathlib import Path
from collections import defaultdict

RAW = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
CODES = sys.argv[3].split(',')
PRICE_DATE = '2026-09-30'

def f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except (TypeError, ValueError):
        return 0.0

def yi(x):  # yuan -> 亿元 string
    return f"{x/1e8:,.2f}" if x else "—"

def pct(x, nd=1):
    return f"{x*100:.{nd}f}%" if x is not None and math.isfinite(x) else "—"

def by_date(rows):
    out = {}
    for r in rows:
        d = (r.get('REPORT_DATE') or '')[:10]
        if d and d not in out:
            out[d] = r
    return out

def cash_like(b):
    keys = ['MONETARYFUNDS', 'TRADE_FINASSET_NOTFVTPL', 'TRADE_FINASSET', 'DERIVE_FINASSET']
    return sum(f(b.get(k)) for k in keys)

def other_fin(b):
    keys = ['OTHER_CURRENT_ASSET', 'NONCURRENT_ASSET_1YEAR', 'CREDITOR_INVEST', 'OTHER_CREDITOR_INVEST',
            'OTHER_NONCURRENT_FINASSET', 'OTHER_EQUITY_INVEST', 'AVAILABLE_SALE_FINASSET', 'HOLD_MATURITY_INVEST',
            'BUY_RESALE_FINASSET', 'LOAN_ADVANCE', 'LONG_EQUITY_INVEST']
    return {k: f(b.get(k)) for k in keys if f(b.get(k))}

def debt(b):
    keys = ['SHORT_LOAN', 'LONG_LOAN', 'BOND_PAYABLE', 'NONCURRENT_LIAB_1YEAR', 'LEASE_LIAB', 'TRADE_FINLIAB_NOTFVTPL',
            'TRADE_FINLIAB', 'DERIVE_FINLIAB', 'ACCEPT_DEPOSIT_INTERBANK', 'BORROW_FUND', 'SELL_REPO_FINASSET',
            'LOAN_PBC', 'SHORT_BOND_PAYABLE']
    return {k: f(b.get(k)) for k in keys if f(b.get(k))}

def op_liab(b):
    keys = ['NOTE_PAYABLE', 'ACCOUNTS_PAYABLE', 'NOTE_ACCOUNTS_PAYABLE', 'ADVANCE_RECEIVABLES', 'CONTRACT_LIAB',
            'OTHER_CURRENT_LIAB', 'TOTAL_OTHER_PAYABLE', 'STAFF_SALARY_PAYABLE', 'TAX_PAYABLE', 'PREDICT_LIAB', 'DEFER_INCOME']
    return {k: f(b.get(k)) for k in keys if f(b.get(k))}

def op_assets(b):
    keys = ['NOTE_RECE', 'ACCOUNTS_RECE', 'NOTE_ACCOUNTS_RECE', 'FINANCE_RECE', 'PREPAYMENT', 'TOTAL_OTHER_RECE',
            'INVENTORY', 'CONTRACT_ASSET', 'LONG_RECE', 'FIXED_ASSET', 'CIP', 'INTANGIBLE_ASSET', 'GOODWILL',
            'USERIGHT_ASSET', 'INVEST_REALESTATE', 'DEVELOP_EXPENSE', 'LONG_PREPAID_EXPENSE', 'DEFER_TAX_ASSET', 'OTHER_NONCURRENT_ASSET']
    return {k: f(b.get(k)) for k in keys if f(b.get(k))}

for code in CODES:
    d = json.loads((RAW / f"{code}.json").read_text())
    inc, bal, cf = by_date(d['income']), by_date(d['balance']), by_date(d['cashflow'])
    name = (d['income'][0].get('SECURITY_NAME_ABBR') if d['income'] else code)
    q = d.get('tx_quote') or []
    price = f(q[3]) if len(q) > 3 else 0.0
    total_shares = f(q[73]) if len(q) > 73 else 0.0
    float_shares = f(q[72]) if len(q) > 72 else 0.0
    L = []
    L.append(f"# {name}（{code}）独立分析数据包\n")
    L.append(f"数据来源：东方财富 F10 三大报表／主营构成／分红明细，腾讯行情；抓取于 2026-10-07。金额单位亿元（另注明者除外）。价格日 {PRICE_DATE}（国庆休市前最后交易日）。\n")
    # snapshot
    years = sorted([k for k, r in inc.items() if k.endswith('12-31')])
    last_annual = years[-1] if years else None
    periods = sorted(inc.keys())
    latest = periods[-1]
    bL = bal.get(latest, {})
    sc_latest = f(bL.get('SHARE_CAPITAL'))
    shares = total_shares or sc_latest
    mcap = price * shares
    L.append("## 一、快照\n")
    L.append(f"- 收盘价（{PRICE_DATE}，A 股未复权）：**{price:.2f}** 元；总股本（行情口径）{shares/1e8:,.4f} 亿股（流通 {float_shares/1e8:,.4f} 亿股）；资产负债表股本（{latest}）{sc_latest/1e8:,.4f} 亿股")
    L.append(f"- 按 A 股价 × 总股本的总市值：**{mcap/1e8:,.2f} 亿元**（腾讯行情字段：总市值 {q[45] if len(q)>45 else '—'} 亿、PB {q[46] if len(q)>46 else '—'}、PE(TTM) {q[39] if len(q)>39 else '—'}）")
    # 52w range
    days = d.get('tx_day') or []
    if days:
        closes = [(r[0], f(r[2])) for r in days if len(r) > 2]
        hi = max(closes, key=lambda x: x[1]); lo = min(closes, key=lambda x: x[1])
        first = closes[0]
        L.append(f"- 2026 年内（{first[0]}→{closes[-1][0]}）收盘区间 {lo[1]:.2f}（{lo[0]}）～{hi[1]:.2f}（{hi[0]}）；年初首日收盘 {first[1]:.2f}，年内涨跌 {(closes[-1][1]/first[1]-1)*100:+.1f}%（未复权，未含分红）")
    # TTM
    def ttm(key, src):
        if latest.endswith('12-31'):
            return f(src[latest].get(key))
        prev_year_end = f"{int(latest[:4])-1}-12-31"
        same_last = f"{int(latest[:4])-1}{latest[4:]}"
        if prev_year_end in src and same_last in src and latest in src:
            return f(src[latest].get(key)) + f(src[prev_year_end].get(key)) - f(src[same_last].get(key))
        return float('nan')
    ttm_rev = ttm('TOTAL_OPERATE_INCOME', inc); ttm_np = ttm('PARENT_NETPROFIT', inc); ttm_dnp = ttm('DEDUCT_PARENT_NETPROFIT', inc)
    ttm_ocf = ttm('NETCASH_OPERATE', cf); ttm_capex = ttm('CONSTRUCT_LONG_ASSET', cf)
    pe_ttm = mcap / ttm_np if ttm_np and ttm_np > 0 else float('nan')
    pe_ded = mcap / ttm_dnp if ttm_dnp and ttm_dnp > 0 else float('nan')
    peq = f(bL.get('TOTAL_PARENT_EQUITY'))
    L.append(f"- TTM（截至 {latest}）：营收 {yi(ttm_rev)}、归母净利 {yi(ttm_np)}、扣非归母 {yi(ttm_dnp)}、经营现金流 {yi(ttm_ocf)}、购建长期资产 {yi(ttm_capex)}")
    L.append(f"- 市值/TTM 归母 = **{pe_ttm:.2f}×**；市值/TTM 扣非 = {pe_ded:.2f}×；市值/最新归母权益 = **{mcap/peq:.2f}×**（归母权益 {yi(peq)}）" if peq else "")
    # balance sheet structure latest
    L.append(f"\n## 二、最新资产负债表结构（{latest}）\n")
    cl = cash_like(bL); dbt = debt(bL); ofin = other_fin(bL); ol = op_liab(bL); oa = op_assets(bL)
    L.append(f"- 货币资金 {yi(f(bL.get('MONETARYFUNDS')))}；交易性金融资产 {yi(f(bL.get('TRADE_FINASSET_NOTFVTPL')) + f(bL.get('TRADE_FINASSET')))}；衍生金融资产 {yi(f(bL.get('DERIVE_FINASSET')))} → 现金类合计 **{yi(cl)}**")
    L.append("- 其他可能含金融资产的科目（须结合附注判断）：" + "；".join(f"{k} {yi(v)}" for k, v in ofin.items()))
    L.append("- 有息及类金融负债：" + ("；".join(f"{k} {yi(v)}" for k, v in dbt.items()) or "无") + f" → 合计 **{yi(sum(dbt.values()))}**")
    L.append(f"- 现金类 − 有息负债 = **{yi(cl - sum(dbt.values()))}**（未计其他金融资产；受限资金、客户存款等须看附注）")
    L.append("- 经营性负债：" + "；".join(f"{k} {yi(v)}" for k, v in ol.items()))
    L.append("- 经营性资产：" + "；".join(f"{k} {yi(v)}" for k, v in oa.items()))
    L.append(f"- 总资产 {yi(f(bL.get('TOTAL_ASSETS')))}；总负债 {yi(f(bL.get('TOTAL_LIABILITIES')))}；归母权益 {yi(peq)}；少数股东权益 {yi(f(bL.get('MINORITY_EQUITY')))}；库存股 {yi(f(bL.get('TREASURY_SHARES')))}")
    # annual table
    L.append("\n## 三、年度利润表与现金流（亿元）\n")
    hdr = "| 年度 | 营收 | 同比 | 毛利率 | 销售费率 | 管理费率 | 研发费率 | 营业利润率 | 归母净利 | 扣非归母 | 净利率 | ROE(平均归母) | 经营现金流 | 购建长期资产 | 自由现金流 | 折旧摊销 | 分配股利利息付现 | 投资收益+公允价值 | 减值损失(资产+信用) | 其他收益 |"
    L.append(hdr); L.append("|" + "---|" * hdr.count('|')[:-1] if False else "|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|")
    prev_rev = None; prev_eq = None
    ann = [y for y in years if y >= '2013-12-31']
    for y in years:
        r = inc[y]; c = cf.get(y, {}); b = bal.get(y, {})
        rev = f(r.get('TOTAL_OPERATE_INCOME')); oi = f(r.get('OPERATE_INCOME')) or rev; oc = f(r.get('OPERATE_COST'))
        gm = 1 - oc / oi if oi else float('nan')
        eq = f(b.get('TOTAL_PARENT_EQUITY'))
        np_ = f(r.get('PARENT_NETPROFIT')); dnp = f(r.get('DEDUCT_PARENT_NETPROFIT'))
        roe = np_ / ((eq + prev_eq) / 2) if prev_eq else (np_ / eq if eq else float('nan'))
        ocf = f(c.get('NETCASH_OPERATE')); capex = f(c.get('CONSTRUCT_LONG_ASSET'))
        da = f(c.get('FA_IR_DEPR')) + f(c.get('IA_AMORTIZE')) + f(c.get('LPE_AMORTIZE')) + f(c.get('USERIGHT_ASSET_AMORTIZE'))
        inv = f(r.get('INVEST_INCOME')) + f(r.get('FAIRVALUE_CHANGE_INCOME'))
        imp = f(r.get('ASSET_IMPAIRMENT_INCOME')) + f(r.get('CREDIT_IMPAIRMENT_INCOME')) - f(r.get('ASSET_IMPAIRMENT_LOSS')) - f(r.get('CREDIT_IMPAIRMENT_LOSS'))
        if y in ann:
            yoy = (rev / prev_rev - 1) if prev_rev else float('nan')
            L.append(f"| {y[:4]} | {yi(rev)} | {pct(yoy)} | {pct(gm)} | {pct(f(r.get('SALE_EXPENSE'))/rev if rev else float('nan'))} | {pct(f(r.get('MANAGE_EXPENSE'))/rev if rev else float('nan'))} | {pct(f(r.get('RESEARCH_EXPENSE'))/rev if rev else float('nan'))} | {pct(f(r.get('OPERATE_PROFIT'))/rev if rev else float('nan'))} | {yi(np_)} | {yi(dnp)} | {pct(np_/rev if rev else float('nan'))} | {pct(roe)} | {yi(ocf)} | {yi(capex)} | {yi(ocf-capex)} | {yi(da)} | {yi(f(c.get('ASSIGN_DIVIDEND_PORFIT')))} | {yi(inv)} | {yi(imp)} | {yi(f(r.get('OTHER_INCOME')))} |")
        prev_rev = rev; prev_eq = eq
    # annual balance table
    L.append("\n## 四、年度资产负债要点（亿元，年末）\n")
    hdr = "| 年末 | 现金类 | 有息负债 | 现金类−有息负债 | 应收(票据+账款+融资) | 存货 | 合同资产 | 合同负债+预收 | 应付(票据+账款) | 其他流动负债 | 固定资产+在建 | 商誉 | 归母权益 | 总股本(亿股) |"
    L.append(hdr); L.append("|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|")
    for y in years:
        if y < '2013-12-31':
            continue
        b = bal.get(y, {})
        if not b:
            continue
        rec = f(b.get('NOTE_RECE')) + f(b.get('ACCOUNTS_RECE')) + f(b.get('FINANCE_RECE')) + (0 if (f(b.get('NOTE_RECE')) or f(b.get('ACCOUNTS_RECE'))) else f(b.get('NOTE_ACCOUNTS_RECE')))
        pay = f(b.get('NOTE_PAYABLE')) + f(b.get('ACCOUNTS_PAYABLE'))
        if not pay:
            pay = f(b.get('NOTE_ACCOUNTS_PAYABLE'))
        dd = sum(debt(b).values()); cc = cash_like(b)
        L.append(f"| {y[:4]} | {yi(cc)} | {yi(dd)} | {yi(cc-dd)} | {yi(rec)} | {yi(f(b.get('INVENTORY')))} | {yi(f(b.get('CONTRACT_ASSET')))} | {yi(f(b.get('CONTRACT_LIAB'))+f(b.get('ADVANCE_RECEIVABLES')))} | {yi(pay)} | {yi(f(b.get('OTHER_CURRENT_LIAB')))} | {yi(f(b.get('FIXED_ASSET'))+f(b.get('CIP')))} | {yi(f(b.get('GOODWILL')))} | {yi(f(b.get('TOTAL_PARENT_EQUITY')))} | {f(b.get('SHARE_CAPITAL'))/1e8:,.4f} |")
    # quarterly single-quarter
    L.append("\n## 五、近 12 个季度单季数据（亿元）\n")
    def single(key, src, p):
        r = src.get(p)
        if not r:
            return float('nan')
        m = p[5:]
        if m == '03-31':
            return f(r.get(key))
        prevp = {'06-30': '03-31', '09-30': '06-30', '12-31': '09-30'}[m]
        pr = src.get(p[:5] + prevp)
        if not pr:
            return float('nan')
        return f(r.get(key)) - f(pr.get(key))
    qs = [p for p in periods if p >= '2023-01-01'][-12:]
    hdr = "| 单季 | 营收 | 营收同比 | 毛利率 | 归母净利 | 归母同比 | 扣非归母 | 经营现金流 |"
    L.append(hdr); L.append("|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|")
    for p in qs:
        rev = single('TOTAL_OPERATE_INCOME', inc, p); oi = single('OPERATE_INCOME', inc, p); oc = single('OPERATE_COST', inc, p)
        np_ = single('PARENT_NETPROFIT', inc, p); dnp = single('DEDUCT_PARENT_NETPROFIT', inc, p); ocf = single('NETCASH_OPERATE', cf, p)
        lp = f"{int(p[:4])-1}{p[4:]}"
        rev_l = single('TOTAL_OPERATE_INCOME', inc, lp); np_l = single('PARENT_NETPROFIT', inc, lp)
        gm = 1 - oc / oi if oi and math.isfinite(oi) and oi else float('nan')
        L.append(f"| {p} | {yi(rev)} | {pct(rev/rev_l-1) if rev_l and math.isfinite(rev_l) else '—'} | {pct(gm)} | {yi(np_)} | {pct(np_/np_l-1) if np_l and math.isfinite(np_l) and np_l>0 else '—'} | {yi(dnp)} | {yi(ocf)} |")
    # segments
    L.append("\n## 六、主营构成（最新年报与最新中报）\n")
    mo = d.get('mainop') or []
    rep_dates = sorted({(r.get('REPORT_DATE') or '')[:10] for r in mo}, reverse=True)
    pick = []
    for rd in rep_dates:
        if rd.endswith('06-30') and not any(p.endswith('06-30') for p in pick):
            pick.append(rd)
        if rd.endswith('12-31') and not any(p.endswith('12-31') for p in pick):
            pick.append(rd)
        if len(pick) >= 2:
            break
    # also add the annual two years earlier for trend
    ann_dates = [rd for rd in rep_dates if rd.endswith('12-31')]
    if len(ann_dates) >= 3:
        pick.append(ann_dates[2])
    tmap = {'1': '按行业', '2': '按产品', '3': '按地区'}
    for rd in pick:
        rows = [r for r in mo if (r.get('REPORT_DATE') or '')[:10] == rd]
        for t in ('1', '2', '3'):
            rr = [r for r in rows if str(r.get('MAINOP_TYPE')) == t]
            if not rr:
                continue
            L.append(f"**{rd} {tmap[t]}**：" + "；".join(
                f"{r.get('ITEM_NAME')} {yi(f(r.get('MAIN_BUSINESS_INCOME')))}（占 {pct(f(r.get('MBI_RATIO')))}，毛利率 {pct(f(r.get('GROSS_RPOFIT_RATIO')))}）"
                for r in sorted(rr, key=lambda r: -f(r.get('MAIN_BUSINESS_INCOME')))[:10]))
        L.append("")
    # dividends
    L.append("## 七、分红记录（每 10 股税前现金，元）\n")
    divs = d.get('dividends') or []
    hdr = "| 报告期 | 方案 | 进度 | 除息日 | 每股现金 | 当期基本EPS | 分红率(每股现金/EPS) |"
    L.append(hdr); L.append("|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|")
    for r in sorted(divs, key=lambda r: r.get('REPORT_DATE') or '', reverse=True)[:16]:
        dps = f(r.get('PRETAX_BONUS_RMB')) / 10
        eps = f(r.get('BASIC_EPS'))
        L.append(f"| {(r.get('REPORT_DATE') or '')[:10]} | {r.get('IMPL_PLAN_PROFILE')} | {r.get('ASSIGN_PROGRESS')} | {(r.get('EX_DIVIDEND_DATE') or '')[:10]} | {dps:.4f} | {eps:.4f} | {pct(dps/eps) if eps>0 else '—'} |")
    # dividend TTM yield
    ttm_dps = 0.0
    for r in divs:
        ex = (r.get('EX_DIVIDEND_DATE') or '')[:10]
        if ex and '2025-10-01' <= ex <= '2026-09-30' and r.get('ASSIGN_PROGRESS') == '实施分配':
            ttm_dps += f(r.get('PRETAX_BONUS_RMB')) / 10
    L.append(f"\n- 过去 12 个月（2025-10-01～2026-09-30 除息）每股现金合计 {ttm_dps:.4f} 元，按现价股息率 **{pct(ttm_dps/price if price else float('nan'),2)}**（未调整送转；如期间有送转需另核）")
    # historical valuation: year-end market cap / NP
    L.append("\n## 八、历史估值（年末 A 股收盘 × 年末总股本 ÷ 当年归母净利；年末 ÷ 年末归母权益）\n")
    mon = d.get('tx_month') or []
    ye_close = {}
    for r in mon:
        if len(r) > 2 and r[0][5:7] == '12':
            ye_close[r[0][:4]] = f(r[2])
    hdr = "| 年末 | 收盘 | 总股本(亿股) | 市值 | PE(当年归母) | PB(年末归母权益) |"
    L.append(hdr); L.append("|" + "|".join(["---"] * (hdr.count('|') - 1)) + "|")
    for y in years:
        yy = y[:4]
        if yy < '2014' or yy not in ye_close:
            continue
        b = bal.get(y, {}); r = inc[y]
        sh = f(b.get('SHARE_CAPITAL')); mc = ye_close[yy] * sh
        np_ = f(r.get('PARENT_NETPROFIT')); eq = f(b.get('TOTAL_PARENT_EQUITY'))
        L.append(f"| {yy} | {ye_close[yy]:.2f} | {sh/1e8:,.4f} | {yi(mc)} | {mc/np_:.1f} | {mc/eq:.2f} |" if np_ > 0 and eq > 0 else f"| {yy} | {ye_close[yy]:.2f} | {sh/1e8:,.4f} | {yi(mc)} | 亏损 | — |")
    L.append("\n注：送转/拆股年份年末股本与收盘口径一致即可比；未复权价格。")
    (OUT / f"{code}_{name}.md").write_text("\n".join(x for x in L if x is not None), encoding='utf-8')
    print(code, name, f"price {price} mcap {mcap/1e8:,.1f}亿 PE_TTM {pe_ttm:.2f} PB {mcap/peq if peq else float('nan'):.2f}")
