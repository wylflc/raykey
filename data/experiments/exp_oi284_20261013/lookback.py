"""OI-284 回看：2026 年中报公告日当天那根 K 线与其后一根，哪一根才是财报反应日。"""
import csv, json, sys, statistics as st
from concurrent.futures import ThreadPoolExecutor
from datetime import date
sys.path.insert(0, 'scripts')
import screen_daily_volume_price_signals as S

pool = {r['security_code'].zfill(6): r for r in csv.DictReader(open('data/processed/a_share_core_valuation_pool.csv', encoding='utf-8-sig'))}
bands = [r for r in csv.DictReader(open('data/processed/a_share_pool_model_bands_adopted.csv', encoding='utf-8-sig'))
         if r.get('report_date', '')[:10] == '2026-06-30' and (r.get('pre_overlay_notice_date') or r.get('notice_date'))]
def one(band):
    code = band['security_code'].zfill(6)
    notice = (band.get('pre_overlay_notice_date') or band['notice_date'])[:10]
    try:
        _, rows = S.fetch_daily_rows(code, pool[code].get('exchange', ''), '2026-10-13', 10.0)
    except Exception as exc:
        return code, notice, None, str(exc)[:60]
    days = [str(r['date']) for r in rows]; close = [float(r['close']) for r in rows]
    i0 = next((i for i, d in enumerate(days) if d >= notice), None)
    if i0 is None or i0 == 0 or i0 + 1 >= len(days):
        return code, notice, None, 'no bars'
    d0 = close[i0] / close[i0 - 1] - 1
    d1 = close[i0 + 1] / close[i0] - 1
    return code, notice, dict(on_notice_day=days[i0] == notice, bar0=days[i0], d0=d0, bar1=days[i0 + 1], d1=d1), ''
with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(one, bands))
ok = [(c, n, r) for c, n, r, _ in res if r]
print('中报带', len(bands), '取到', len(ok), '失败', [(c, e) for c, n, r, e in res if not r][:5])
td = [x for x in ok if x[2]['on_notice_day']]; wk = [x for x in ok if not x[2]['on_notice_day']]
print('公告日是交易日', len(td), '；公告日非交易日', len(wk))
for label, grp in (('公告日是交易日', td), ('公告日非交易日', wk)):
    if not grp: continue
    a0 = [abs(x[2]['d0']) for x in grp]; a1 = [abs(x[2]['d1']) for x in grp]
    print(f'{label}：|Δ| 均值 公告日当天或之后首根 {100*st.mean(a0):.2f}%，再后一根 {100*st.mean(a1):.2f}%；中位 {100*st.median(a0):.2f}% / {100*st.median(a1):.2f}%')
    print(f'   |Δ|≥7%：首根 {sum(v >= .07 for v in a0)} 只，后一根 {sum(v >= .07 for v in a1)} 只，两根任一 {sum(max(p, q) >= .07 for p, q in zip(a0, a1))} 只')
    print('   首根≥7%:', [(pool[c]['security_name'], n, f"{100*r['d0']:+.1f}%") for c, n, r in grp if abs(r['d0']) >= .07])
    print('   后一根≥7%:', [(pool[c]['security_name'], n, f"{100*r['d1']:+.1f}%") for c, n, r in grp if abs(r['d1']) >= .07])
json.dump([(c, n, r) for c, n, r in ok], open(sys.argv[1], 'w'), ensure_ascii=False)
