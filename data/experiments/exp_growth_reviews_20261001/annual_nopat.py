"""Model-caliber annual NOPAT (nonop cash, notes_wc restricted cash, IC floor 0.1, R&D capitalized) vs net profit."""
import csv, sys
from pathlib import Path
ROOT = Path('/gpfs/scratch1/shared/zwang/mm_quant/RayKey')
sys.path.insert(0, str(ROOT / 'scripts'))
import roic_inputs as ri
codes = set(sys.argv[1].split(','))
years = ri.load_statements(codes, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc')
rd = ri.load_rd_expense(codes)
ind = {r['security_code']: r.get('csrc_industry') or r.get('industry') or '' for r in csv.DictReader(open(ROOT / 'data/reference/a_share_csrc_industry.csv', encoding='utf-8'))}
for code in sorted(codes):
    ys = years.get(code, {})
    life = ri.rd_life(ind.get(code))
    cap = ri.capitalize_rd(ys, rd.get(code, {}), life)
    adj = cap[0] if cap else ys
    for p in sorted(adj)[-5:]:
        y, y0 = adj[p], ys[p]
        f = lambda v: f"{v/1e8:.2f}" if v is not None else '—'
        print(code, p, 'life', life, 'NOPAT(rd)', f(y.nopat), 'NOPAT(raw)', f(y0.nopat), 'net', f(y.net_profit), 'parent', f(y.parent_netprofit),
              'minority', f(y.minority_profit), 'IC', f(y.invested_capital), 'rev', f(y.revenue), 'tax', f"{y.tax_rate:.3f}" if y.tax_rate else '—',
              'nonop', f(y.nonop_income))
