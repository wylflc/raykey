"""OI-266＋OI-268 读数（preregister.md 读数 1～7）：`scripts/experimental/caliber_fairness.py` 的 N 臂公允性检验。

分组（读数 5，取 C 臂该观测所用带与同口径三表）：
- `lam0`：带 `growth_trust` = 0；`v_pos`：带 `trough_weight` > 0；
- `anchor15`：机械锚（每股 NOPAT × `shares_est`）≥ 1.5 倍 TTM 等价 NOPAT（最新年报 NOPAT × `ttm_factor`，§7.3 谷底侧复核条件）；
- `book_gap`：最新年报较两年前年报的归母权益增速高于 NOPAT 增速 20pp 以上（OI-268 的 42 只口径）。

    python3 test.py      # → results.json、cases.csv、cache/observations.json
"""
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import caliber_fairness as cf  # noqa: E402
import roic_inputs  # noqa: E402
from build import ARMS  # noqa: E402

CASES = ('000786', '600970', '603279', '000568', '000596', '603369', '000858', '600809', '000651', '600690', '300316')
GROUPS = ('lam0', 'v_pos', 'anchor15', 'book_gap')
_YEARS = {}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def features(band, rec):
    if not _YEARS:
        _YEARS.update(roic_inputs.load_statements(None, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc',
                                                  tax_anomaly='median3'))
    out = dict(lam0=num(band.get('growth_trust')) == 0.0, v_pos=(num(band.get('trough_weight')) or 0.0) > 0.0)
    hist = sorted(roic_inputs.years_before(_YEARS.get(rec['code'], {}), band.get('available_at', ''), 3), key=lambda y: y.period)
    nopat_ps, shares, f_ttm = num(band.get('nopat_ps')), num(band.get('shares_est')), num(band.get('ttm_factor'))
    if hist and hist[-1].nopat and nopat_ps and shares:
        ttm = hist[-1].nopat * (1.0 if f_ttm is None else f_ttm)
        out['anchor15'] = ttm <= 0 or nopat_ps * shares >= 1.5 * ttm
    if len(hist) == 3 and all(y.nopat and y.nopat > 0 and y.parent_equity and y.parent_equity > 0 for y in (hist[0], hist[-1])):
        book = hist[-1].parent_equity / hist[0].parent_equity - 1
        profit = hist[-1].nopat / hist[0].nopat - 1
        out['book_gap'] = book - profit > 0.20
    return out


def main():
    cf.run(EXP, {a: EXP / 'states' / a for a in ARMS}, groups=features, group_names=GROUPS, cases=CASES)


if __name__ == '__main__':
    main()
