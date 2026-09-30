"""Research-caliber V (§6.5.2.2 same engine) over a grid of research NOPAT values, on a copy of the production pool band."""
import csv, sys
from pathlib import Path
ROOT = Path('/gpfs/scratch1/shared/zwang/mm_quant/RayKey')
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_forecast_band_overlay import apply_research_overlay
bands = {r['security_code']: r for r in csv.DictReader(open(ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv', encoding='utf-8'))}
close = {}
for r in csv.DictReader(open(ROOT / 'data/processed/daily_buy_candidates.csv', encoding='utf-8')):
    if r['trade_date'] == '2026-09-30':
        close[r['security_code'].zfill(6)] = float(r['close'])
for arg in sys.argv[1:]:
    code, grid = arg.split(':')
    b = bands[code]
    model = float(b['nopat_ps']) * float(b['shares_est']) / 1e8
    print(code, b['security_name'], 'model anchor', round(model, 2), '亿; V', b['intrinsic_value'], 'exright', repr(b.get('exright_note', '')), 'close', close.get(code))
    for x in grid.split(','):
        row = dict(b)
        res = apply_research_overlay(row, {'research_nopat_yi': x, 'divergence_reviewed_at': '2026-10-01'})
        if isinstance(res, str):
            print('  ', x, res); continue
        iv0, iv1 = res
        print(f"   research {x:>6} 亿  k {float(x)/model:5.2f}  V {iv1:8.2f}  P/V {close[code]/iv1:6.3f}  terminal_share {row.get('terminal_share')}")
