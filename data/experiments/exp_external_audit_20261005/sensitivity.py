"""外部审计对照：8 只股票的模型 V 拆解与单项假设敏感度（同一引擎 `intrinsic_value`，只换一项输入）。

A 股四只的输入读生产带（候选侧）与 09-30 扫描；海外四只的输入抄自 `overseas_watchlist_valuation.csv` 的 band_derivation_text
（2026-10-05 读取）。审计区间抄自用户贴来的两份网页版审计（Opus 5.5、Fable 5.1），独立基准取
`docs/reports/independent_valuation_holdings_2026-09-30.zh.md`。

    python3 sensitivity.py      # → sensitivity.json、audit_compare.csv
"""
import csv
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from bank_valuation import ddm_value  # noqa: E402
from intrinsic_value import intrinsic_value  # noqa: E402

R, G_T, ROIC_T, LAM = 0.10, 0.03, 0.12, 0.12


def ev(nopat_ps, roic0, g0, lam=LAM, roic_t=None):
    roic_t = min(ROIC_T, roic0) if roic_t is None else roic_t
    return intrinsic_value(nopat_ps, roic0, g0, R, roe_terminal=roic_t, g_terminal=G_T, n=10, consistent=True,
                           roe_lam=lam, horizon=50).intrinsic_value


def band(code):
    with (ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv').open(newline='', encoding='utf-8-sig') as f:
        return next(r for r in csv.DictReader(f) if r['security_code'].zfill(6) == code)


def scan(code):
    with (ROOT / 'data/processed/daily_buy_candidates.csv').open(newline='', encoding='utf-8-sig') as f:
        return next(r for r in csv.DictReader(f) if r['security_code'].zfill(6) == code)


def a_share():
    out = {}
    # 格力：每股 NOPAT 锚、ROIC0、净金融资产；TTM 锚 = 锚 ÷ 1.13 与保守现金 24.5、净占款回吐 15.4 元取自 09-30 独立估值
    b, s = band('000651'), scan('000651')
    nopat, roic0, cash, price = float(b['nopat_ps']), float(b['roic0']), -float(b['net_debt_ps']), float(s['close'])
    ttm = nopat / 1.13
    cases = [('生产', ev(nopat, roic0, 0.0), cash), ('锚改 TTM', ev(ttm, roic0 * ttm / nopat, 0.0), cash),
             ('现金改 24.5（扣未抵消受限）', ev(nopat, roic0, 0.0), 24.5),
             ('TTM＋现金 24.5', ev(ttm, roic0 * ttm / nopat, 0.0), 24.5),
             ('TTM＋现金 24.5＋净占款回吐 15.4', ev(ttm, roic0 * ttm / nopat, 0.0), 24.5 - 15.4)]
    out['000651 格力电器'] = [dict(case=c, ev=round(e, 2), v=round(e + k, 2), pv=round(price / (e + k), 3)) for c, e, k in cases]
    # 中创智领：独立基准正常化 NOPAT 27 亿 ≈ 1.51 元／股；TTM 锚按 TTM 因子 0.7876 粗取 × 0.80
    b, s = band('601717'), scan('601717')
    nopat, roic0, g0, nd, price = float(b['nopat_ps']), float(b['roic0']), float(b['g0']), float(b['net_debt_ps']), float(s['close'])
    cases = [('生产', nopat, roic0, g0), ('g0 = 0', nopat, roic0, 0.0), ('锚改独立正常化 1.51', 1.51, roic0 * 1.51 / nopat, g0),
             ('锚 1.51＋g0 = 0', 1.51, roic0 * 1.51 / nopat, 0.0), ('锚改 TTM（×0.80）', nopat * 0.80, roic0 * 0.80, g0)]
    out['601717 中创智领'] = [dict(case=c, v=round(ev(n, ro, g) - nd, 2), pv=round(price / (ev(n, ro, g) - nd), 3)) for c, n, ro, g in cases]
    # 平安：V = V_DDM × Ḡ；Ḡ 由生产 V 反推，ROE 锚换成营运利润口径的 12%～14%
    b, s = band('601318'), scan('601318')
    bps, payout, roe0, v_live, price = float(b['bps']), float(b['payout']), float(b['roe0']), float(s['model_intrinsic_value']), float(s['close'])
    base = ddm_value(bps, roe0, payout)
    g_bar = v_live / base
    rows = [dict(case=f'生产 roe0 {roe0:.4f}（Ḡ {g_bar:.3f}）', v_ddm=round(base, 2), v=round(v_live, 2), pv=round(price / v_live, 3))]
    for roe in (0.14, 0.135, 0.13):
        v = ddm_value(bps, roe, payout) * g_bar
        rows.append(dict(case=f'roe0 {roe:.3f}', v_ddm=round(v / g_bar, 2), v=round(v, 2), pv=round(price / v, 3)))
    out['601318 中国平安'] = rows
    return out


def overseas():
    out = {}
    # 腾讯（CNY；HKD 1.1668）：锚 25.307、ROIC0 27.0%、g0 0、净现金 41.368
    rows = []
    for c, g, lam in (('生产 g0 = 0', 0.0, LAM), ('g0 5%', 0.05, LAM), ('g0 8%', 0.08, LAM), ('g0 10%', 0.10, LAM),
                      ('g0 8%＋衰减 0.06', 0.08, 0.06)):
        v = (ev(25.307, 0.270, g, lam) + 41.368) * 1.1668
        rows.append(dict(case=c, v=round(v, 1), pv=round(439.80 / v, 3)))
    out['00700 腾讯控股'] = rows
    rows = []
    for c, g, lam in (('生产 g0 = 0', 0.0, LAM), ('g0 5%', 0.05, LAM), ('g0 8%', 0.08, LAM), ('g0 10%', 0.10, LAM),
                      ('g0 8%＋衰减 0.06', 0.08, 0.06)):
        v = ev(20.285, 0.422, g, lam) - 3.148
        rows.append(dict(case=c, v=round(v, 1), pv=round(235.47 / v, 3)))
    out['ADBE Adobe'] = rows
    rows = []
    for c, g, lam, rt in (('生产', 0.102, LAM, None), ('衰减 0.06', 0.102, 0.06, None), ('衰减 0.03', 0.102, 0.03, None),
                          ('g0 15%', 0.15, LAM, None), ('g0 15%＋衰减 0.03', 0.15, 0.03, None), ('终值回报 30%', 0.102, LAM, 0.30)):
        v = ev(11.572, 0.495, g, lam, rt) + 21.307
        rows.append(dict(case=c, v=round(v, 1), pv=round(343.92 / v, 3)))
    out['GOOGL Alphabet'] = rows
    # PDD（CNY／股；每 ADR 4 股 × 0.1488）：受限现金 772.74 亿为商家待结算款
    k, shares, escrow = 4 * 0.1488, 5907.0, 77274.0
    ttm = 0.208 / 0.252
    rows = []
    for c, n, ro, cash in (('生产', 17.954, 2.728, 100.723), ('剔除受限托管现金', 17.954, 2.728, 100.723 - escrow / shares),
                           ('锚改 TTM', 17.954 * ttm, 2.728 * ttm, 100.723),
                           ('TTM＋剔除受限', 17.954 * ttm, 2.728 * ttm, 100.723 - escrow / shares),
                           ('TTM＋剔除受限＋余下现金五折', 17.954 * ttm, 2.728 * ttm, (100.723 - escrow / shares) * 0.5)):
        v = (ev(n, ro, 0.0) + cash) * k
        rows.append(dict(case=c, v=round(v, 1), pv=round(77.57 / v, 3)))
    out['PDD 拼多多'] = rows
    return out


# 审计区间（审计所用价格）与 09-30 独立基准 P/V
AUDITS = [
    # 名称, 模型 P/V, Opus 价格, Opus 区间, Fable 价格, Fable 区间, 09-30 独立基准 P/V
    ('格力电器', 0.511, 38.5, (42, 50), 38.3, (39, 49), 0.59),
    ('招商银行', 0.889, 40.6, (46, 54), 40.6, (47, 57), 0.80),
    ('中国平安', 0.983, 52.4, (60, 71), 52.4, (59, 71), 0.80),
    ('中创智领', 0.565, 13.1, (13, 17), 13.35, (13, 17), 0.89),
    ('腾讯控股', 1.405, 440, (530, 620), 440, (530, 640), None),
    ('PDD', 0.448, 75.4, (90, 115), 75.4, (83, 118), None),
    ('Adobe', 1.324, 237.7, (300, 380), 237.7, (280, 350), None),
    ('Alphabet', 2.151, 343.5, (295, 375), 343.5, (305, 386), None),
]


def main():
    res = dict(a_share=a_share(), overseas=overseas())
    (EXP / 'sensitivity.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with (EXP / 'audit_compare.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['name', 'model_pv', 'opus_pv_low', 'opus_pv_mid', 'opus_pv_high', 'fable_pv_low', 'fable_pv_mid', 'fable_pv_high',
                    'independent_0930_pv'])
        for name, pv, op, (ol, oh), fp, (fl, fh), ind in AUDITS:
            w.writerow([name, pv, round(op / oh, 3), round(op / ((ol + oh) / 2), 3), round(op / ol, 3),
                        round(fp / fh, 3), round(fp / ((fl + fh) / 2), 3), round(fp / fl, 3), ind])
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
