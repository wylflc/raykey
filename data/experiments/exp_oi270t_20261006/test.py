"""OI-270 汇兑与研发年限的估值准确性读数（preregister.md）：`scripts/experimental/caliber_fairness.py` 的 N 臂检验。

分组（读数 5，按 C 臂该观测所用带的可得日取最新可得年报）：
- `fx_big`：|财务费用 − (利息费用 − 利息收入)| ÷ |利润总额| ≥ 4%（FX 针对）；
- `rd_long`／`rd_short`／`rd_5`：按证监会大类的研发摊销年限 10／3／5 年，只取有研发的观测（RD5 针对）。

    python3 test.py      # → results.json、cases.csv、cache/observations.json
"""
import bisect
import csv
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import caliber_fairness as cf  # noqa: E402
import roic_inputs  # noqa: E402
from build import ARMS  # noqa: E402

CASES = ('600970', '002001', '688278', '600276', '300685', '600066')
GROUPS = ('fx_big', 'rd_long', 'rd_short', 'rd_5')
FX_MIN = 0.04
_FIN, _RD, _IND = {}, {}, {}


def _load():
    with (roic_inputs.STMT_DIR / 'income.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            code, period = (r.get('security_code') or '').zfill(6), (r.get('REPORT_DATE') or '')[:10]
            if not period.endswith('-12-31'):
                continue
            notice = (r.get('NOTICE_DATE') or '')[:10]
            fe, ie, ii, tp = (roic_inputs._num(r.get(k)) for k in ('FINANCE_EXPENSE', 'FE_INTEREST_EXPENSE', 'FE_INTEREST_INCOME', 'TOTAL_PROFIT'))
            share = (abs(fe - ((ie or 0.0) - (ii or 0.0))) / abs(tp)) if fe is not None and ie is not None and tp else None
            _FIN.setdefault(code, []).append((notice or period, share))
    for v in _FIN.values():
        v.sort(key=lambda x: x[0])
    _RD.update({c: bool(v) for c, v in roic_inputs.load_rd_expense(None).items()})
    with (ROOT / 'data/reference/a_share_csrc_industry.csv').open(encoding='utf-8', newline='') as fh:
        _IND.update({r['security_code'].zfill(6): r.get('csrc_industry', '') for r in csv.DictReader(fh)})


def features(band, rec):
    if not _FIN:
        _load()
    code, avail = rec['code'], band.get('available_at', '')
    out = {}
    seq = _FIN.get(code, [])
    i = bisect.bisect_right([d for d, _ in seq], avail) - 1
    if i >= 0 and seq[i][1] is not None:
        out['fx_big'] = bool(seq[i][1] >= FX_MIN)
    if _RD.get(code):
        life = roic_inputs.rd_life(_IND.get(code))
        out.update(rd_long=life == 10, rd_short=life == 3, rd_5=life == 5)
    return out


def main():
    arms = {a: EXP / 'states' / a for a in ARMS}
    cache = EXP / 'cache/observations.json'
    (EXP / 'cache').mkdir(exist_ok=True)
    if not cache.exists():
        rows = cf.collect(arms, '2010-01-01', features)
        cache.write_text(json.dumps(rows, ensure_ascii=False))
    cf.run(EXP, arms, group_names=GROUPS, cases=CASES)


if __name__ == '__main__':
    main()
