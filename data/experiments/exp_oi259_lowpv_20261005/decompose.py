"""OI-259 低 P/V 审查第一段：池内 P/V < 1 各票的模型价值机械拆解（09-30 信号日生产带，只读）。

    python3 decompose.py      # → decomposition.csv、decomposition.md

V = EV − 每股净金融负债 fin_nd − 少数股东扣减 + 外生权益 x（§6.5.1 第 3 条）；银行保险另列 DDM 口径。
价格隐含 EV/NOPAT = (P + fin_nd + 少数扣减 − x) ÷ 每股 NOPAT 锚，与模型 EV/NOPAT 对照，看低 P/V 来自盈利锚、增长还是现金。
"""
import csv
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PROC = ROOT / 'data/processed'
FIN = ROOT / 'data/raw/financials'
PV_MAX = 1.0


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def panel(period):
    path = FIN / f'{period}.csv'
    if not path.exists():
        return {}
    with path.open(encoding='utf-8') as f:
        return {r['security_code'].zfill(6): r for r in csv.DictReader(f)}


def main():
    quotes = {r['security_code'].zfill(6): r for r in csv.DictReader((PROC / 'daily_buy_candidates.csv').open(encoding='utf-8'))}
    bands = {r['security_code'].zfill(6): r for r in csv.DictReader((PROC / 'a_share_pool_model_bands_adopted.csv').open(encoding='utf-8'))}
    attrs = {}
    p = PROC / 'a_share_business_attributes.csv'
    if p.exists():
        attrs = {r['security_code'].zfill(6): r for r in csv.DictReader(p.open(encoding='utf-8'))}
    fy = {y: panel(f'{y}-12-31') for y in (2021, 2022, 2023, 2024, 2025)}
    h1 = {y: panel(f'{y}-06-30') for y in (2025, 2026)}
    rows = []
    for code, q in quotes.items():
        pv = num(q['model_pv'])
        if pv is None or pv >= PV_MAX:
            continue
        b = bands.get(code, {})
        price, v = num(q['close']), num(q['model_intrinsic_value'])
        shares = num(b.get('shares_est'))      # 股数（股）
        nopat_ps = num(b.get('nopat_ps'))
        fin_nd = num(b.get('fin_net_debt_ps')) or 0.0
        nd = num(b.get('net_debt_ps')) or 0.0
        x = num(b.get('external_equity_ps')) or 0.0
        minority = nd - fin_nd + x
        ev = num(b.get('ev_ps'))
        npy = {y: num(fy[y].get(code, {}).get('parent_netprofit')) for y in fy}
        ttm = None
        if npy[2025] is not None and num(h1[2026].get(code, {}).get('parent_netprofit')) is not None \
                and num(h1[2025].get(code, {}).get('parent_netprofit')) is not None:
            ttm = npy[2025] + num(h1[2026][code]['parent_netprofit']) - num(h1[2025][code]['parent_netprofit'])
        mcap = price * shares if price and shares else None
        row = dict(code=code, name=q['security_name'], tier=q['quality_tier'], close=price, V=v, pv=pv,
                   hold_pv=num(q['hold_pv']), path=b.get('roic_path'), mode=b.get('roic_nopat_mode'),
                   research=b.get('research_overlay') or '', attribute=attrs.get(code, {}).get('business_attribute', ''),
                   report_date=b.get('report_date'), shares_yi=(shares / 1e8 if shares else None),
                   nopat_anchor_yi=(nopat_ps * shares / 1e8 if nopat_ps and shares else None),
                   np_2021=npy[2021], np_2022=npy[2022], np_2023=npy[2023], np_2024=npy[2024], np_2025=npy[2025], np_ttm=ttm,
                   roic0=num(b.get('roic0')), g0=num(b.get('g0')), g_source=b.get('roic_g_source'),
                   incremental_roic=num(b.get('incremental_roic')), reinvestment=num(b.get('reinvestment_rate')),
                   terminal_share=num(b.get('terminal_share')), ev_ps=ev, nopat_ps=nopat_ps,
                   model_ev_nopat=(ev / nopat_ps if ev and nopat_ps else None),
                   implied_ev_nopat=((price + fin_nd + minority - x) / nopat_ps if price and nopat_ps else None),
                   net_cash_ps=-fin_nd, net_cash_share_of_v=(-fin_nd / v if v else None), minority_ps=minority, x_ps=x,
                   pe_ttm=(mcap / ttm if mcap and ttm and ttm > 0 else None),
                   peak_w=num(b.get('peak_weight')), trough_w=num(b.get('trough_weight')), trust=num(b.get('growth_trust')),
                   ttm_factor=num(b.get('ttm_factor')), v_bear_ratio=(num(b.get('v_bear')) / v if num(b.get('v_bear')) and v else None),
                   quality_score=num(b.get('valuation_quality_score')), roe0=num(b.get('roe0')), payout=num(b.get('payout')),
                   bps=num(b.get('bps')))
        for k in ('np_2021', 'np_2022', 'np_2023', 'np_2024', 'np_2025', 'np_ttm'):
            row[k] = row[k] / 1e8 if row[k] is not None else None
        rows.append(row)
    rows.sort(key=lambda r: r['pv'])
    with (EXP / 'decomposition.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fmt = lambda v, d=2: '—' if v is None else f'{v:.{d}f}'
    md = ['# OI-259 池内 P/V < 1 机械拆解（信号日 2026-09-30，生产候选侧带）', '',
          '| 代码 | 名称 | P/V | V | 现价 | 路径/锚 | NOPAT 锚(亿) | 归母 2024/2025/TTM(亿) | g0 | ROIC0 | 模型 EV/NOPAT | 价格隐含 | 净现金/V | PE(TTM) | 研究数 |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        md.append(f"| {r['code']} | {r['name']} | {r['pv']:.3f} | {fmt(r['V'])} | {fmt(r['close'])} | {r['path']}/{r['mode']} | "
                  f"{fmt(r['nopat_anchor_yi'], 1)} | {fmt(r['np_2024'], 1)}/{fmt(r['np_2025'], 1)}/{fmt(r['np_ttm'], 1)} | "
                  f"{fmt(r['g0'] * 100 if r['g0'] is not None else None, 1)}% | {fmt(r['roic0'] * 100 if r['roic0'] is not None else None, 1)}% | "
                  f"{fmt(r['model_ev_nopat'], 1)} | {fmt(r['implied_ev_nopat'], 1)} | {fmt(r['net_cash_share_of_v'] * 100 if r['net_cash_share_of_v'] is not None else None, 0)}% | "
                  f"{fmt(r['pe_ttm'], 1)} | {r['research'] or ''} |")
    (EXP / 'decomposition.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    (EXP / 'decomposition.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
