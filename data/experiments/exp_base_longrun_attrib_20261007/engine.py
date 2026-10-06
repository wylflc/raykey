"""生产回测引擎包一层（只读，不改任何交易判据）：现行 BASE 单跑时逐日逐代码记下盈亏，供分时段归因。

引擎 run() 日末逐代码累加 `contrib[code] += 盈亏 ÷ 前一日净资产`（§12.1 第 3 款赢家尺；盈亏 = 市值变动 − 当日买入
＋ 当日卖出与分红，费用、股息税、融资利息不摊）。本包装把这一个字典换成记录型子类：每次累加时从 run() 帧读出
当日 `day`、`pnl`、`eq_prev`、`mv`，写到 `<out-dir>/<tag>_daily_pnl.csv`；同时把逐日净值（含负债与集中度列）、
5 年与 3 年滚动窗口（引擎 `rolling_windows` 原函数）写到 `<tag>_curve.csv`、`<tag>_windows.json`。其余参数原样交给引擎。

    python3 engine.py <BASE 参数…> --since 2009-11-01 --label-suffix _BASE20091101 --out-dir <目录>
"""
import collections
import csv
import json
import sys
import types
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import backtest_valuation_strategy as bt  # noqa: E402

_SRC = Path(bt.__file__).read_text(encoding='utf-8').splitlines()
_LINES = [i + 1 for i, s in enumerate(_SRC) if s.strip() == 'contrib: dict[str, float] = collections.defaultdict(float)']
assert len(_LINES) == 1, _LINES
CONTRIB_LINE, RUN_CODE = _LINES[0], bt.run.__code__
RECORDERS: list = []


class Recorder(collections.defaultdict):
    """只在 run() 帧里的累加处记行；读帧局部量，不写回。"""

    def __setitem__(self, key, value):
        if value != dict.get(self, key, 0.0):
            frame = sys._getframe(1)
            assert frame.f_code is RUN_CODE
            loc = frame.f_locals
            self.rows.append((loc['day'], key, loc['pnl'], loc['eq_prev'], loc['mv']))
        super().__setitem__(key, value)


def _defaultdict(*args, **kw):
    frame = sys._getframe(1)
    if frame.f_code is RUN_CODE and frame.f_lineno == CONTRIB_LINE:
        d = Recorder(*args, **kw)
        d.rows = []
        RECORDERS.append(d)
        return d
    return collections.defaultdict(*args, **kw)


_proxy = types.ModuleType('collections')
_proxy.__dict__.update(collections.__dict__)
_proxy.defaultdict = _defaultdict
bt.collections = _proxy


def _arg(name):
    return sys.argv[sys.argv.index(name) + 1]


if __name__ == '__main__':
    tag = _arg('--label-suffix').lstrip('_')
    out = Path(_arg('--out-dir'))
    original = bt.summarize

    def capture(name, result, capital, benchmark, risk_free):
        if name.startswith('trend_'):
            rec = [d for d in RECORDERS if dict(d) == result['contrib']]
            assert len(rec) == 1, len(rec)
            with (out / f'{tag}_daily_pnl.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['date', 'security_code', 'pnl', 'eq_prev', 'mv'])
                w.writerows((d, c, f'{p:.4f}', f'{e:.4f}', f'{m:.4f}') for d, c, p, e, m in rec[0].rows)
            with (out / f'{tag}_curve.csv').open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['date', 'net_equity', 'cash', 'positions', 'debt', 'margin_ratio', 'top1_weight', 'top3_weight'])
                for r in result['equity']:      # 无信号日的行只有 6 列（无集中度），补 0
                    r = (*r, 0.0, 0.0)[:8]
                    w.writerow([r[0], f'{r[1]:.4f}', f'{r[2]:.4f}', r[3], f'{r[4]:.4f}', f'{r[5]:.6f}', f'{r[6]:.6f}', f'{r[7]:.6f}'])
            windows = {str(y): bt.rolling_windows(result['equity'], y, risk_free) for y in (3, 5, 10)}
            (out / f'{tag}_windows.json').write_text(json.dumps(windows, ensure_ascii=False) + '\n', encoding='utf-8')
        return original(name, result, capital, benchmark, risk_free)

    bt.summarize = capture
    raise SystemExit(bt.main())
