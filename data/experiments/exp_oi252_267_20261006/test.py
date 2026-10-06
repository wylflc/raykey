"""OI-252＋OI-267 读数（preregister.md 读数 1～7）：`scripts/experimental/caliber_fairness.py` 的 N 臂公允性检验。

分组（读数 5，按 C 臂该观测所用带的可得日、与建带同口径从三表计算）：
- `dic_small`：五年窗 ΔIC ÷ 窗首投入资本 < 10%（G1／G2 针对）；
- `wc_major`：窗口 ΔWC > 0 且大于「资本开支 − 折旧摊销 + ΔWC」的一半（G3 针对）；
- `rd_low`／`rd_mid`／`rd_high`：最新年报研发三年复合增速的三分位（R1／R2 针对，只取有研发的观测）。

    python3 test.py      # → results.json、cases.csv、cache/observations.json
"""
import json
import sys
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import caliber_fairness as cf  # noqa: E402
import roic_inputs  # noqa: E402
from build import ARMS  # noqa: E402

CASES = ('605305', '600600', '600938', '600887', '002001', '300910', '688278', '920599',
         '002594', '002920', '300866', '600690', '603855', '600970')
GROUPS = ('dic_small', 'wc_major', 'rd_low', 'rd_mid', 'rd_high')
_YEARS, _RD = {}, {}


def features(band, rec):
    code, avail = rec['code'], band.get('available_at', '')
    if not _YEARS:                                   # 一次装载全名册三表（与建带同口径）
        _YEARS.update(roic_inputs.load_statements(None, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc',
                                                  tax_anomaly='median3'))
        _RD.update(roic_inputs.load_rd_expense(None))
    hist = sorted(roic_inputs.years_before(_YEARS.get(code, {}), avail, 5), key=lambda y: y.period)
    out = {}
    if len(hist) >= 2 and hist[0].invested_capital and hist[-1].invested_capital and hist[0].invested_capital > 0:
        out['dic_small'] = bool((hist[-1].invested_capital - hist[0].invested_capital) / hist[0].invested_capital < 0.10)
        capex = sum(y.capex for y in hist[1:]) - sum(y.dep_amort for y in hist[1:])
        if hist[0].working_capital is not None and hist[-1].working_capital is not None:
            dwc = hist[-1].working_capital - hist[0].working_capital
            out['wc_major'] = bool(dwc > 0 and dwc > 0.5 * (capex + dwc))
    rd = _RD.get(code, {})
    if hist:
        last = hist[-1].period
        y0 = f'{int(last[:4]) - 3}{last[4:]}'
        if rd.get(last) and rd.get(y0) and rd[y0] > 0:
            out['rd_growth'] = float((rd[last] / rd[y0]) ** (1 / 3) - 1)
    return out


def main():
    arms = {a: EXP / 'states' / a for a in ARMS}
    cache = EXP / 'cache/observations.json'
    (EXP / 'cache').mkdir(exist_ok=True)
    if not cache.exists():
        rows = cf.collect(arms, '2010-01-01', features)
        growth = np.array([r['groups']['rd_growth'] for r in rows if 'rd_growth' in r['groups']])
        lo, hi = np.percentile(growth, [100 / 3, 200 / 3])
        for r in rows:
            g = r['groups'].pop('rd_growth', None)
            if g is not None:
                r['groups'].update(rd_low=bool(g < lo), rd_mid=bool(lo <= g < hi), rd_high=bool(g >= hi))
        cache.write_text(json.dumps(rows, ensure_ascii=False))
        (EXP / 'cache/rd_terciles.json').write_text(json.dumps(dict(lo=float(lo), hi=float(hi), n=int(len(growth)))))
    cf.run(EXP, arms, group_names=GROUPS, cases=CASES)


if __name__ == '__main__':
    main()
