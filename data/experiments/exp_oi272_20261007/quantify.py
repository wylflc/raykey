"""OI-272 全池量化：业务属性判「存量」（`demand_runway = 存量`）的 ROIC `growth` 路径池成员，g0 按上限 10%／8%／5.5%／3%
截断后的 V 与 `P/V`（信号日 2026-09-30 的候选侧与持仓侧池带；研究开关，生产未改）。

做法：池带行即 §6.7 第 4 步产物（叠加、研究数、除权归一化之后）。先按带上记录的 `exright_factor`／`exright_cash` 反解归一化前的
IV 与 EV（无配股时 V = IV ÷ F − C，逐行核对误差 ≤ 1e-3），再用 `apply_forecast_band_overlay` 同一引擎
（`intrinsic_value`、§6.5.1 统一参数与股权桥）按截断后的 g0 重算 EV 比例，经股权桥得新 IV，再归一化回现价口径。
研究数行的每股 NOPAT 与 ROIC0 已是研究口径，与 `apply_research_overlay` 按 `research_g0` 重算逐式相同。

    python3 quantify.py     # → results.json、readings.md
"""
import csv
import json
import statistics
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_forecast_band_overlay as ov  # noqa: E402
from apply_forecast_band_overlay import num, equity_from_ev  # noqa: E402
from screen_daily_volume_price_signals import SEC93_BUY_LINE  # noqa: E402

PROC = ROOT / 'data/processed'
CAPS = (0.10, 0.08, 0.055, 0.03)
SIGNAL_DATE = '2026-09-30'


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return {r['security_code'].zfill(6): r for r in csv.DictReader(fh)}


def trend_ok(q, held):
    """§9.3.1 走势条件（09-30 收盘）：已持仓 MA20 > MA60；新建仓近 3 日未创 20 日新低且收盘 > MA5、> MA20。"""
    close, ma5, ma20, ma60 = (num(q.get(k)) for k in ('close', 'ma5', 'ma20', 'ma60'))
    if None in (close, ma20, ma60):
        return '缺数'
    ok = ma20 > ma60 if held else (q.get('bt_stable') == 'True' and ma5 is not None and close > ma5 and close > ma20)
    return ('达标' if ok else '未达标') + ('（加仓）' if held else '（新建仓）')


def capped_value(row, g_new):
    """池带行（现价口径）按 g0 = g_new 重算的 V；返回 (V_新, 归一化反解误差)。"""
    F, C = num(row.get('exright_factor')) or 1.0, num(row.get('exright_cash')) or 0.0
    assert '配股' not in (row.get('exright_note') or ''), row['security_code']
    v = num(row['intrinsic_value'])
    iv_pre, ev_pre = (v + C) * F, num(row['ev_ps']) * F
    nd_pre = ev_pre - iv_pre
    err = abs(equity_from_ev(row, ev_pre, nd_pre) - iv_pre) / iv_pre
    nopat, roic0, wacc, g0, g_t = (num(row.get(k)) for k in ('nopat_ps', 'roic0', 'wacc', 'g0', 'g_terminal'))
    ev = lambda g: ov.intrinsic_value(nopat, roic0, g, wacc, roe_terminal=min(wacc + ov.TERMINAL_EXCESS, roic0),
                                      g_terminal=g_t, **ov.FADE).intrinsic_value
    iv_new = equity_from_ev(row, ev_pre * ev(g_new) / ev(g0), nd_pre)
    return iv_new / F - C, err


def main():
    attrs = read(PROC / 'a_share_business_attributes.csv')
    cand, hold = read(PROC / 'a_share_pool_model_bands_adopted.csv'), read(PROC / 'a_share_pool_model_bands_hold.csv')
    quotes = read(PROC / 'daily_buy_candidates.csv')
    holdings = read(PROC / 'a_share_holdings.csv')
    rows, max_err = [], 0.0
    for code, b in cand.items():
        a = attrs.get(code) or {}
        if b.get('roic_path') != 'growth' or a.get('demand_runway') != '存量':
            continue
        q = quotes.get(code) or {}
        close, g0, v = num(q.get('close')), num(b.get('g0')), num(b.get('intrinsic_value'))
        if close is None or g0 is None or not v:
            continue
        rec = dict(code=code, name=b.get('security_name', ''), cls=a.get('derived_class', ''), g0=g0, V=round(v, 4),
                   pv=round(close / v, 4), model_pv=num(q.get('model_pv')), research=bool(b.get('research_overlay')),
                   trend=trend_ok(q, code in holdings), held=code in holdings, iroic=num(b.get('incremental_roic')),
                   rr=num(b.get('reinvestment_rate')))
        for cap in CAPS:
            if g0 > cap:
                v_new, err = capped_value(b, cap)
                max_err = max(max_err, err)
                rec[f'V_{cap:g}'], rec[f'pv_{cap:g}'] = round(v_new, 4), round(close / v_new, 4)
        if code in holdings and code in hold:
            hb = hold[code]
            hg0, hv = num(hb.get('g0')), num(hb.get('intrinsic_value'))
            rec['hold'] = dict(g0=hg0, V=hv, pv=round(close / hv, 4) if hv else None,
                               **{f'pv_{cap:g}': round(close / capped_value(hb, cap)[0], 4) for cap in CAPS if hg0 and hg0 > cap})
        rows.append(rec)
    assert max_err <= 1e-3, max_err
    line = SEC93_BUY_LINE
    summary = {}
    for cap in CAPS:
        hit = [r for r in rows if f'V_{cap:g}' in r]
        chg = [r[f'V_{cap:g}'] / r['V'] - 1 for r in hit]
        summary[f'{cap:g}'] = dict(
            changed=len(hit), by_class={c: sum(r['cls'] == c for r in hit) for c in sorted({r['cls'] for r in hit})},
            dv_median=round(statistics.median(chg), 4) if chg else None, dv_min=round(min(chg), 4) if chg else None,
            exits=[dict(code=r['code'], name=r['name'], g0=r['g0'], pv=r['pv'], pv_new=r[f'pv_{cap:g}']) for r in hit
                   if r['pv'] <= line < r[f'pv_{cap:g}']],
            zone_moved=[dict(code=r['code'], name=r['name'], g0=r['g0'], pv=r['pv'], pv_new=r[f'pv_{cap:g}']) for r in hit
                        if r['pv'] <= line and r[f'pv_{cap:g}'] <= line])
    g_dist = dict(n=len(rows), ge10=sum(r['g0'] >= 0.10 for r in rows), ge8=sum(r['g0'] >= 0.08 for r in rows),
                  ge55=sum(r['g0'] >= 0.055 for r in rows), median=round(statistics.median(r['g0'] for r in rows), 4))
    res = dict(signal_date=SIGNAL_DATE, buy_line=line, max_inversion_err=max_err, g0_distribution=g_dist, summary=summary, rows=rows)
    (EXP / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    pct = lambda x: '—' if x is None else f'{x:+.1%}'
    md = [f'# OI-272 存量型公司 g0 上限的全池量化（信号日 {SIGNAL_DATE}，候选侧池带；研究开关，生产未改）', '',
          f"对象：业务属性 `demand_runway = 存量` 的 ROIC `growth` 路径池成员 {g_dist['n']} 只；g0 中位 {g_dist['median']:.1%}，"
          f"≥ 10% 的 {g_dist['ge10']} 只、≥ 8% 的 {g_dist['ge8']} 只、≥ 5.5% 的 {g_dist['ge55']} 只。买入线 {line}。"
          f"归一化反解最大误差 {max_err:.1e}。结构扩张型不在本表，不受影响。", '',
          '| g0 上限 | 改动只数（按类别） | V 变化中位／最大降幅 | 出买入区 | 仍在买入区的变化 |', '|---|---|---|---|---|']
    for cap in CAPS:
        s = summary[f'{cap:g}']
        cls = '、'.join(f'{k} {v}' for k, v in s['by_class'].items())
        ex = '、'.join(f"{x['name']}（g0 {x['g0']:.1%}，{x['pv']:.3f}→{x['pv_new']:.3f}）" for x in s['exits']) or '无'
        mv = '、'.join(f"{x['name']} {x['pv']:.3f}→{x['pv_new']:.3f}" for x in s['zone_moved']) or '无'
        md.append(f"| {cap:.1%} | {s['changed']}（{cls}） | {pct(s['dv_median'])}／{pct(s['dv_min'])} | {ex} | {mv} |")
    md += ['', '## g0 ≥ 8% 的存量型池成员', '',
           '| 代码 | 名称 | 类别 | g0 | 增量 ROIC × 再投资率 | 研究数 | 当前 P/V | 上限 10% | 8% | 5.5% | 3% | 09-30 走势 |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: -r['g0']):
        if r['g0'] < 0.08:
            continue
        cells = ' | '.join('—' if f'pv_{c:g}' not in r else f"{r[f'pv_{c:g}']:.3f}" for c in CAPS)
        legs = f"{min(r['iroic'], 0.40):.1%}×{r['rr']:.1%}" if r['iroic'] is not None and r['rr'] is not None else '—'
        md.append(f"| {r['code']} | {r['name']} | {r['cls']} | {r['g0']:.1%} | {legs} | {'是' if r['research'] else ''} | {r['pv']:.3f} | {cells} | {r['trend']} |")
    held = [r for r in rows if r.get('hold')]
    md += ['', '## 持仓（持仓侧池带）', '']
    md += [f"- {r['name']}：持仓侧 g0 {r['hold']['g0']:.1%}、P/V {r['hold']['pv']:.3f}；"
           + ('；'.join(f"上限 {c:.1%} → {r['hold'][f'pv_{c:g}']:.3f}" for c in CAPS if f'pv_{c:g}' in r['hold']) or '各档都不截断')
           for r in held] or ['- 现有持仓中没有存量型 growth 路径公司。']
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
