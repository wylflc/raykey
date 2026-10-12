#!/usr/bin/env python3
"""格力电器出口下滑对 V 与 P/V 的量级（只作分析，不改档案、带与规则）。

事实与利润影响的估计见同目录 `gree_export_factcheck.md`（独立代理，不读仓库）；本脚本只做两件事：
把那里的税后利润变动放进生产带同一引擎与股权桥算 V，以及列出独立估值口径下的对应读数。

    python3 data/experiments/exp_gree_export_20261012/analyze.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_forecast_band_overlay as ov  # noqa: E402
from apply_forecast_band_overlay import num, equity_from_ev  # noqa: E402

EXP = Path(__file__).resolve().parent
CLOSE = 39.59                      # 2026-10-12 收盘
BUY_LINE = 1.0034                  # §9.3.1
NET_PROFIT_2025 = 290.03           # 2025 年归母净利润，亿元
# 外销单项的税后利润变动（亿元，相对 2025 年；gree_export_factcheck.md 第 3.3 节，下半年毛利率取 32%、税率 15%）
SCENARIOS = [
    ('上半年已实现（外销 −21.98%）', -3.6),
    ('下半年降幅收窄到 −5%（全年 −15.1%）', -5.1),
    ('下半年维持 −22%（全年 −22.0%）', -10.2),
    ('下半年 −30%，接近 7～8 月出货降幅（全年 −25.2%）', -12.6),
    ('全年 −35%（压力测试）', -19.9),
    ('2027 年再降 10%（相对 2025 年累计）', -23.7),
    ('外销利润全部消失（上限，按完全分摊口径 32 亿元）', -32.0),
]

band = next(r for r in csv.DictReader((ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv').open(encoding='utf-8-sig'))
            if r['security_code'] == '000651')
assert not any((band.get(k) or '').strip() for k in ('exright_note', 'forecast_overlay', 'research_overlay', 'growth_cap_note'))
nopat, roic0, wacc, g0, g_t = (num(band[k]) for k in ('nopat_ps', 'roic0', 'wacc', 'g0', 'g_terminal'))
iv, ev_ps, nd, shares = num(band['intrinsic_value']), num(band['ev_ps']), num(band['net_debt_ps']), num(band['shares_est'])
base_yi = nopat * shares / 1e8


def ev(k, g):
    r0 = roic0 * k
    return ov.intrinsic_value(nopat * k, r0, g, wacc, roe_terminal=min(wacc + ov.TERMINAL_EXCESS, r0), g_terminal=g_t, **ov.FADE).intrinsic_value


def value(nopat_yi, g=g0):
    return equity_from_ev(band, ev_ps * ev(nopat_yi / base_yi, g) / ev(1.0, g0), nd)


out = dict(close=CLOSE, model=dict(report_date=band['report_date'], available_at=band['available_at'], nopat_yi=round(base_yi, 2),
                                   g0=g0, wacc=wacc, ev_ps=ev_ps, net_cash_ps=round(-nd, 4), V=iv, pv=round(CLOSE / iv, 4),
                                   net_cash_share_of_V=round(-nd / iv, 4), buy_line_price=round(BUY_LINE * iv, 2)))
out['sensitivity_per_1pct_nopat'] = dict(dV_pct=round(100 * (value(base_yi * 0.99) / iv - 1), 3),
                                         dPV=round(CLOSE / value(base_yi * 0.99) - CLOSE / iv, 4))
rows = []
for name, delta in SCENARIOS:
    v = value(base_yi + delta)
    rows.append(dict(name=name, profit_change_yi=delta, share_of_2025_profit_pct=round(100 * delta / NET_PROFIT_2025, 1),
                     nopat_yi=round(base_yi + delta, 1), V=round(v, 2), dV_pct=round(100 * (v / iv - 1), 2), pv=round(CLOSE / v, 4)))
out['scenarios'] = rows
# NOPAT 要降到多少，现价才碰到买入线
lo, hi = 0.0, base_yi
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if CLOSE / value(mid) > BUY_LINE else (lo, mid)
out['nopat_at_buy_line'] = dict(nopat_yi=round(hi, 1), drop_pct=round(100 * (hi / base_yi - 1), 1))
# 独立估值（2026-10-07，登记 iv20261007_top10:000651）：正常化归母 260 亿元已低于 2025 年实际 290.03 亿元
out['independent'] = dict(V=58.2, bear=34.9, base=62.4, bull=82.6, pv=round(CLOSE / 58.2, 3), pv_bear=round(CLOSE / 34.9, 3),
                          normalized_profit_yi=260, haircut_vs_2025_yi=round(NET_PROFIT_2025 - 260, 2))
(EXP / 'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=1))
