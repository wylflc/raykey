"""§7.5 临时冻结 8 只的逐只复核底稿（OI-265，用户 2026-10-06 裁定「维持至逐只复核结束」）。

逐只给信号日 2026-09-30 的三种口径：现行模型 V（候选侧池带）、采用研究数（§6.5.2.2，只换 NOPAT、g0 照带）、采用研究数＋研究增长
（§6.5.2.2 同式 `min(增量 ROIC, 40%) × 带再投资率（上限 1）`，起点取各年报、终点照带，只列出供判断，是否构成结构性变化另看毛利率），
并列 OI-259 审查的独立基准 V。各年 NOPAT 与投入资本按生产口径（v4.232 四项、nonop、受限现金 notes_wc、研发资本化）重算。

    python3 review.py [--bands 池带 CSV] [--note-debt notes]     # → review.json、review.md
"""
import argparse
import csv
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_forecast_band_overlay as ov  # noqa: E402
import roic_inputs  # noqa: E402

AUDIT = ROOT / 'data/experiments/exp_oi259_lowpv_20261005/companies'
HOLDS = ROOT / 'data/reference/review_holds.csv'
DOSSIERS = ROOT / 'data/processed/a_share_valuation_dossiers.csv'
QUOTES = ROOT / 'data/processed/daily_buy_candidates.csv'
INDUSTRY = ROOT / 'data/reference/a_share_csrc_industry.csv'
BUY_LINE, CAP = 1.0034, 0.40


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def gross_margins(codes):
    out = {}
    with (roic_inputs.STMT_DIR / 'income.csv').open(encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            code, period = (row.get('security_code') or '').zfill(6), (row.get('REPORT_DATE') or '')[:10]
            if code in codes and period.endswith('-12-31'):
                rev = roic_inputs._num(row.get('TOTAL_OPERATE_INCOME')) or roic_inputs._num(row.get('OPERATE_INCOME'))
                cost = roic_inputs._num(row.get('OPERATE_COST'))
                if rev and cost is not None:
                    out[(code, period)] = 1 - cost / rev
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bands', type=Path, default=ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv')
    ap.add_argument('--note-debt', default='off', choices=roic_inputs.NOTE_DEBT_MODES)
    ap.add_argument('--out', default='review')
    args = ap.parse_args()
    args.bands = args.bands.resolve()
    holds = [h for h in read(HOLDS) if not h['released_at']]
    codes = {h['security_code'] for h in holds}
    bands = {r['security_code']: r for r in read(args.bands)}
    dossiers = {r['security_code']: r for r in read(DOSSIERS)}
    quotes = {r['security_code']: r for r in read(QUOTES)}
    industry = {r['security_code'].zfill(6): r.get('csrc_industry', '') for r in read(INDUSTRY)}
    years = roic_inputs.load_statements(codes, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc', tax_anomaly='median3',
                                        note_debt=args.note_debt)
    rd = roic_inputs.load_rd_expense(codes)
    gm = gross_margins(codes)
    rows = []
    for h in holds:
        code = h['security_code']
        band, dossier, close = bands[code], dossiers[code], float(quotes[code]['close'])
        life = roic_inputs.rd_life(industry.get(code))
        cap = roic_inputs.capitalize_rd(years[code], rd.get(code, {}), life) if rd.get(code) else None
        ys = cap[0] if cap else years[code]
        end = band.get('wc_last_period') or '2025-12-31'
        rr = min(float(band['reinvestment_rate'] or 0.0), 1.0)
        model_v = float(band['intrinsic_value'])
        res = ov.apply_research_overlay(dict(band), {'research_nopat_yi': dossier['research_nopat_yi'], 'divergence_reviewed_at': '2026-10-06'})
        research_v = res[1]
        series, windows = [], []
        for period in sorted(p for p in ys if p.endswith('-12-31') and '2015-12-31' <= p <= end):
            y = ys[period]
            series.append(dict(year=period[:4], nopat_yi=round(y.nopat / 1e8, 2), ic_yi=round(y.invested_capital / 1e8, 2),
                               roic=round(y.nopat / y.invested_capital, 4) if y.invested_capital else None,
                               gross_margin=round(gm[(code, period)], 4) if (code, period) in gm else None))
            if period < end and '2019-12-31' <= period:
                e = ys[end]
                dic = e.invested_capital - y.invested_capital
                iroic = (e.nopat - y.nopat) / dic if dic > 0 else None
                g = round(min(max(iroic, 0.0), CAP) * rr, 4) if iroic is not None else 0.0
                v = ov.apply_research_overlay(dict(band), {'research_nopat_yi': dossier['research_nopat_yi'], 'research_g0': str(g),
                                                           'divergence_reviewed_at': '2026-10-06'})[1]
                windows.append(dict(start=period[:4], iroic=round(iroic, 4) if iroic is not None else None, g0=g, V=round(v, 2),
                                    pv=round(close / v, 3)))
        audit = next(iter(json.loads(p.read_text(encoding='utf-8')) for p in AUDIT.glob(f'{code}_*.json')), {})
        ind = audit.get('independent', {})
        model_yi = float(band['nopat_ps']) * float(band['shares_est']) / 1e8
        rows.append(dict(code=code, name=h['security_name'], close=close, model_V=round(model_v, 2), model_pv=round(close / model_v, 3),
                         research_yi=float(dossier['research_nopat_yi']), model_yi=round(model_yi, 2),
                         gap=round(max(model_yi, float(dossier['research_nopat_yi'])) / min(model_yi, float(dossier['research_nopat_yi'])) - 1, 4),
                         research_V=round(research_v, 2), research_pv=round(close / research_v, 3),
                         g0_band=float(band['g0']), window_band=f"{(band.get('wc_first_period') or '')[:4]}→{end[:4]}", reinvest=rr,
                         independent_V=ind.get('V', {}).get('base'), independent_pv=ind.get('pv', {}).get('base'),
                         independent_range=[ind.get('V', {}).get('bear'), ind.get('V', {}).get('bull')],
                         hold_note=h['note'], series=series, windows=windows))
    (EXP / f'{args.out}.json').write_text(json.dumps(dict(bands=str(args.bands.relative_to(ROOT)), note_debt=args.note_debt, buy_line=BUY_LINE,
                                                         rows=rows), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    md = [f'# §7.5 临时冻结 8 只逐只复核底稿（信号日 2026-09-30；池带 `{args.bands.relative_to(ROOT)}`）', '',
          '| 代码 | 名称 | 收盘 | 模型 V | P/V | 研究数／模型锚（亿） | 研究 V | P/V | 带 g0（窗口） | 独立基准 V | P/V |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        md.append(f"| {r['code']} | {r['name']} | {r['close']:.2f} | {r['model_V']:.2f} | {r['model_pv']:.3f} | {r['research_yi']:.2f}／{r['model_yi']:.2f}（{r['gap']:.1%}） | "
                  f"{r['research_V']:.2f} | {r['research_pv']:.3f} | {r['g0_band']:.2%}（{r['window_band']}） | {r['independent_V']} | {r['independent_pv']} |")
    md += ['', '研究增长参考（终点照带、起点逐年；`min(增量 ROIC, 40%) × 带再投资率`，与研究数同算）与毛利率：', '']
    for r in rows:
        md.append(f"- {r['name']}：" + '；'.join(f"{w['start']} 起 g0 {w['g0']:.2%} → V {w['V']:.2f}（P/V {w['pv']:.3f}）" for w in r['windows']))
        md.append('  毛利率 ' + '、'.join(f"{s['year']} {s['gross_margin']:.1%}" for s in r['series'] if s['gross_margin'] is not None))
    (EXP / f'{args.out}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
