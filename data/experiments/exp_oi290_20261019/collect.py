"""OI-290 月末观测：四臂候选侧逐日状态的月末 `P/V`、受影响标记与其后 3／5 年含分红年化回报（preregister.md 读数 2～5）。

样本同 `exp_external_audit_20261005/feature_bias.py`：2010-01 起、ROIC 路径（growth／zero_growth）非金融公司，
带 ok、非沿用旧带；四臂都可估的月份才进样本。受影响 = 对照臂该月所用带为 growth 路径、`roic_g_source = none`。

    python3 collect.py      # → data/scratch/experiments/exp_oi290_20261019/observations.csv
"""
import bisect
import csv
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import build_historical_valuation_bands as bhv  # noqa: E402
from divspread_names import is_divspread_financial  # noqa: E402
from moat_param_lab import forward_annualized, total_return_index  # noqa: E402

ARMS = ('C', 'F3', 'F5', 'FR')
SCRATCH = Path(os.environ.get('OI290_DIR', ROOT / 'data/scratch/experiments/exp_oi290_20261019')) / 'states'
OUT = SCRATCH.parent / 'observations.csv'
PANEL = ROOT / 'data/processed/pit_attention/panel_moat_bank_v6b.csv'
START = '2010-01-01'
ROIC_PATHS = {'growth', 'zero_growth'}
HORIZONS = (3, 5)


def num(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def load_bands(arm: str):
    info, rejected = {}, defaultdict(list)
    with (SCRATCH / arm / 'roic_bands.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ok = r['status'] == 'ok'
            info[(r['security_code'], r['report_date'], r['available_at'])] = (
                ok, r['roic_path'], r['roic_g_source'], num(r['g0']))
            if not ok:
                rejected[r['security_code']].append((r['available_at'], r['report_date']))
    steps = {}
    for code, rows in rejected.items():
        rows.sort()
        keys, best, cur = [], [], ''
        for avail, report in rows:
            cur = max(cur, report)
            keys.append(avail); best.append(cur)
        steps[code] = (keys, best)
    return info, steps


def month_ends(arm: str, codes: set) -> dict:
    out = {}
    with (SCRATCH / arm / 'a_share_daily_states_adopted.csv').open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        h = next(reader)
        ic, idt, irp, iav, ipv = (h.index(k) for k in ('security_code', 'date', 'band_report_date', 'band_available_at', 'valuation_ratio'))
        for row in reader:
            code = row[ic]
            if code not in codes or row[idt] < START:
                continue
            key = (code, row[idt][:7])
            if key not in out or row[idt] > out[key][0]:
                out[key] = (row[idt], row[ipv], row[irp], row[iav])
    return out


def judge(rec, code, info, steps):
    """(P/V, 带信息) 或 None：ok 的 ROIC 路径带、非沿用旧带、P/V > 0。"""
    if rec is None or not rec[1]:
        return None
    day, pv, report, avail = rec
    band = info.get((code, report, avail))
    if band is None or not band[0] or band[1] not in ROIC_PATHS:
        return None
    step = steps.get(code)
    if step:
        i = bisect.bisect_right(step[0], day)
        if i and step[1][i - 1] > report:
            return None
    value = num(pv)
    return (value, band) if value and value > 0 else None


def load_names():
    names = {}
    for path in (ROOT / 'data/raw/a_share_securities.csv', ROOT / 'data/processed/a_share_company_analysis_index.csv', PANEL):
        with path.open(newline='', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                names.setdefault(r['security_code'].zfill(6), r['security_name'])
    return names


def load_spans() -> dict:
    spans = defaultdict(list)
    with PANEL.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            spans[r['security_code'].zfill(6)].append((r['effective_from'], r.get('effective_to') or '9999-12-31'))
    return spans


def main() -> None:
    names = load_names()
    bands = {arm: load_bands(arm) for arm in ARMS}
    info_c = bands['C'][0]
    codes = {k[0] for k, (ok, path, _s, _g) in info_c.items() if ok and path in ROIC_PATHS}
    codes = {c for c in codes if not is_divspread_financial(c, names.get(c, ''))}
    states = {arm: month_ends(arm, codes) for arm in ARMS}
    spans = load_spans()
    actions = bhv.load_actions()
    by_code = defaultdict(list)
    for key in states['C']:
        by_code[key[0]].append(key)
    fields = ['code', 'name', 'month', 'date', 'panel', 'affected', 'src_C', *[f'g0_{a}' for a in ARMS],
              *[f'pv_{a}' for a in ARMS], *[f'f{h}' for h in HORIZONS]]
    n = 0
    with OUT.open('w', newline='', encoding='utf-8') as fo:
        w = csv.DictWriter(fo, fieldnames=fields)
        w.writeheader()
        for code in sorted(codes):
            prices = bhv.load_ohlcv(code)
            if not prices:
                continue
            days = [d for d, _ in prices]
            tr = total_return_index(prices, actions.get(code, []))
            for key in sorted(by_code.get(code, ())):
                got = {arm: judge(states[arm].get(key), code, *bands[arm]) for arm in ARMS}
                if any(v is None for v in got.values()):
                    continue
                day = states['C'][key][0]
                if any(states[arm][key][0] != day for arm in ARMS):
                    continue
                band_c = got['C'][1]
                fwd = {h: (forward_annualized(tr, days, day, h) if day in tr else None) for h in HORIZONS}
                w.writerow(dict(code=code, name=names.get(code, ''), month=key[1], date=day,
                                panel=any(a <= day <= b for a, b in spans.get(code, ())),
                                affected=band_c[1] == 'growth' and band_c[2] == 'none', src_C=band_c[2],
                                **{f'g0_{a}': got[a][1][3] for a in ARMS}, **{f'pv_{a}': got[a][0] for a in ARMS},
                                **{f'f{h}': fwd[h] for h in HORIZONS}))
                n += 1
    print('observations', n, '→', OUT)


if __name__ == '__main__':
    main()
