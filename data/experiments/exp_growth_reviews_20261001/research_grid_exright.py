"""research_grid.py 的除权带版本（605305 复核时补写，2026-10-01）。

生产带已按 §6.5.2.3 除权归一化（`exright_note` 非空）时，`apply_research_overlay` 拒绝套用
（「带已除权归一化，须从 §6.7 第 4 步重建池带后再套用」），research_grid.py 因此只打印这句话。
本脚本按生产顺序复现：先用 `exright_factor`／`exright_cash` 把带还原到归一化前
（无配股时 iv_前 = (iv_后 + cash_cum) × factor，ev_前 = ev_后 × factor），
再套研究数（apply_research_overlay），最后用同一 `exright_normalize` 与公司行动表折回现价口径。
只读生产文件，不改任何带。用法同 research_grid.py：
    python3 research_grid_exright.py 605305:4.70,3.60,5.60
第一行另打印「研究数 = 机械锚」的回算 V，应逐位回到生产带 V（自检）。
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path('/gpfs/scratch1/shared/zwang/mm_quant/RayKey')
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_forecast_band_overlay import apply_research_overlay, exright_normalize, num  # noqa: E402

bands = {r['security_code']: r for r in csv.DictReader(
    open(ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv', encoding='utf-8'))}
close = {}
for r in csv.DictReader(open(ROOT / 'data/processed/daily_buy_candidates.csv', encoding='utf-8')):
    if r['trade_date'] == '2026-09-30':
        close[r['security_code'].zfill(6)] = float(r['close'])
actions: dict[str, list[dict]] = {}
for r in csv.DictReader(open(ROOT / 'data/raw/corporate_actions/a_share_corporate_actions.csv', encoding='utf-8-sig')):
    actions.setdefault((r.get('security_code') or '').strip(), []).append(r)


def restore(band: dict) -> tuple[dict, str]:
    """还原到除权归一化之前；返回 (还原后的带, as_of)。有配股时拒绝（cash_cum 不含配股项，式子不成立）。"""
    row = dict(band)
    note = (row.get('exright_note') or '').strip()
    if not note:
        return row, ''
    if '配股' in note:
        raise ValueError('含配股事件，不能按 cash_cum 还原')
    m = re.search(r'(\d{4}-\d{2}-\d{2}) 现价口径', note)
    as_of = m.group(1) if m else '2026-09-30'
    factor, cash = num(row.get('exright_factor')) or 1.0, num(row.get('exright_cash')) or 0.0
    for key in ('intrinsic_value', 'band_low', 'band_high'):
        row[key] = f"{(num(row[key]) + cash) * factor:.6f}"
    ev_pre = num(row.get('ev_ps')) * factor
    row['ev_ps'] = f"{ev_pre:.6f}"
    row['net_debt_ps'] = f"{ev_pre - num(row['intrinsic_value']):.6f}"
    row['exright_note'] = row['exright_cash'] = row['exright_factor'] = ''
    return row, as_of


def research_v(band: dict, research_yi: float) -> tuple[float, str] | str:
    pre, as_of = restore(band)
    res = apply_research_overlay(pre, {'research_nopat_yi': f'{research_yi}', 'divergence_reviewed_at': '2026-10-01'})
    if isinstance(res, str):
        return res
    if as_of:
        exright_normalize(pre, actions.get(band['security_code'], []), as_of)
    return num(pre['intrinsic_value']), pre.get('terminal_share', '')


for arg in sys.argv[1:]:
    code, grid = arg.split(':')
    b = bands[code]
    nopat_ps, shares = num(b['nopat_ps']), num(b['shares_est'])
    model = nopat_ps * shares / 1e8
    print(code, b['security_name'], f'model anchor {model:.4f} 亿; V {b["intrinsic_value"]}; exright {b.get("exright_note", "")!r}; close {close.get(code)}')
    check = research_v(b, model)
    print(f'   自检 research=机械锚 {model:.4f} 亿 → V {check[0]:.4f}（生产带 {b["intrinsic_value"]}）' if not isinstance(check, str) else f'   自检失败：{check}')
    for x in grid.split(','):
        out = research_v(b, float(x))
        if isinstance(out, str):
            print('  ', x, out)
            continue
        v, term = out
        print(f'   research {float(x):>6.2f} 亿  k {float(x) / model:5.3f}  V {v:8.4f}  P/V {close[code] / v:6.3f}'
              f'  P/V=1.0034 价 {v * 1.0034:7.2f}  terminal_share {term}')
