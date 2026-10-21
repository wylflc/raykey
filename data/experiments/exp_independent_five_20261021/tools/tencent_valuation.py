#!/usr/bin/env python3
"""腾讯控股（00700.HK）独立估值，估值基准日 2026-10-21。

运行：python3 tools/tencent_valuation.py
金额单位：十亿元人民币（RMB bn），每股价值折成港元。输入全部写在本文件内，
出处见 companies/00700_腾讯控股.md 的来源清单（公告页码为 PDF 物理页）。

方法：
  所有者收益 E = 正常化经营利润（扣全部股权激励、并购无形资产摊销与 SSV&CPP，
  剔除其他收益/亏损与一次性项）× (1 − 税率) × (1 − 少数股东占比)，不含联营合营、
  不含净利息。FCF = E − 再投资；2026H2～2028 再投资取「资本开支口径」与
  「增长/增量 ROIC 口径」的较大者，2029 年起取增长/增量 ROIC 口径。
  股权价值 = 经营 FCF 现值 + 经调整净现金 + 投资组合（打折）；联营收益不进 E，
  避免与组合价值重复。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 快照
PRICE_HKD = 393.80            # 2026-10-21 港股收盘（雅虎行情 0700.HK）
HKDCNY = 0.8503               # 2026-10-21
COE_BASE = 0.10
SHARES_ISSUED_1015 = 9_092_644_829          # 2026-10-15 翌日披露报表 Part A 收盘结余
PENDING_CANCEL_1015 = [227_000, 230_000, 231_000, 227_000, 232_000, 234_000, 238_000, 238_000,
                       235_000, 238_000, 241_000, 239_000, 235_000, 237_000, 237_000, 240_000]
SHARES = (SHARES_ISSUED_1015 - sum(PENDING_CANCEL_1015)) / 1e9   # 十亿股

# ---------------------------------------------------------------- 已报告数据（公告原文）
FY2025 = dict(revenue=751.766, ifrs_np=224.842, nonifrs_np=259.626, nonifrs_op=280.656,
              ifrs_op=241.562, sbc_op=31.859, sbc_oneoff=4.0, acq_amort_op=6.345, ssv_op=0.890,
              other_gl=-3.177, capex=79.198, cfo=303.052,
              # 东财 F10 现金流量表行（与公告季度 FCF 合计 183 相符）
              capex_paid=87.48, intangibles_paid=25.39, lease_principal=6.78,
              sbc_equity_settled=25.660, nonifrs_assoc=33.457)
H1_2025 = dict(ifrs_np=103.449, cfo=151.265, ppe_paid=45.558, intangibles_paid=11.899, lease_principal=3.265)
H1_2026 = dict(revenue=401.243, ifrs_np=114.115, nonifrs_np=136.320, nonifrs_op=151.263,
               sbc_op=13.113, acq_amort_op=3.180, ssv_op=0.319, other_gl=0.773,
               cfo=154.061, ppe_paid=95.615, intangibles_paid=11.547, lease_principal=3.636,
               fcf_company=56.7 - 13.8, sbc_equity_settled=11.046, nonifrs_assoc=13.482,
               assoc_sbc=2.137, assoc_acq_amort=2.968, int_income=8.227, int_expense=6.346,
               capex=84.720, q2_compute_prepay=(37.6 - (-13.8)))
FY2024_FCF_INPUTS = dict(cfo=258.521, capex_paid=62.93, intangibles_paid=33.12, lease_principal=6.37)
EXAI_OP = dict(q1_2026=84.4, q2_2026=86.1)   # 剔除新 AI 产品的非国际准则经营利润
NONIFRS_OP_Q = dict(q1_2026=75.627, q2_2026=75.636, q3_2025=72.570, q4_2025=69.518)
EXAI_H2_2025 = 77.6 + 76.7   # Q4 2025 = 84.4/1.10（公告环比 +10%）；Q3 2025 假设 AI 亏损约 50 亿

TAX = 0.195        # 经营利润有效税率（含境内股息预提税计提），2025 与 2026H1 测算 19.2%～19.5%
NCI = 0.03         # 少数股东占非国际准则利润 2.75%（2025）、2.88%（2026H1）

# ---------------------------------------------------------------- 资产负债表（2026-06-30，公告第 20～21 页）
BS_0630 = dict(cash=206.930, term_dep_others=304.224, borrowings=298.942, notes=154.021,
               lease_liab=13.366 + 5.499, restricted_cash=7.729)
NET_CASH_0630 = BS_0630['cash'] + BS_0630['term_dep_others'] - BS_0630['borrowings'] - BS_0630['notes']
BUYBACK_JUL_OCT_SHARES = 50_465_700 - 22_034_100 - 10_186_000   # 授权后累计 − 6 月 − 5 月（5 月均在 5-13 业绩后）
BUYBACK_JUL_OCT_HKD_BN = BUYBACK_JUL_OCT_SHARES * 440 / 1e9      # 均价约 440 港元（推断）
ADJ = dict(buyback_after_0630=BUYBACK_JUL_OCT_HKD_BN * HKDCNY,
           operating_buffer=30.0,        # 经营备付，约 3 周现金经营支出（假设）
           wht_repatriation=6.0,         # 境内净现金汇出预提税 5%～10%（假设）
           declared_unpaid_div=0.0)
NET_CASH_ADJ = NET_CASH_0630 - ADJ['buyback_after_0630'] - ADJ['operating_buffer'] - ADJ['wht_repatriation'] - ADJ['declared_unpaid_div']

# 投资组合（公告第 17 页：上市按公允价值、按权益计；非上市按账面）
LISTED_FV_0630 = 487.2
UNLISTED_BOOK_0630 = 387.9
LISTED_MARK_1021 = 0.96   # 6-30→10-21 代理：PDD +3%、Sea −19%、快手 −33%、Spotify +14%、KWEB −3%（推断）

# 经营性投入资本（不含现金、存款、理财与投资组合），公告资产负债表
def oic(ppe, cip, lur, rou, ip, intang, prepay_nc, prepay_c, fin_in_prepay, ar, inv,
        ap, other_pay, def_rev, tax_pay, other_tax, lt_pay):
    return (ppe + cip + lur + rou + ip + intang + prepay_nc + prepay_c - fin_in_prepay + ar + inv
            - ap - other_pay - def_rev - tax_pay - other_tax - lt_pay)

OIC = {
    # 2024-12-31 用东财标准科目；预付中金融类（借给被投企业、应收利息等）约 200 亿为假设
    '2024-12-31': oic(80.19, 12.30, 23.12, 17.68, 0.80, 196.13, 42.83, 101.04, 20.0, 48.20, 0.44,
                      118.71, 84.03, 106.34, 20.62, 0.0, 10.20),
    '2025-12-31': oic(149.905, 9.670, 22.339, 17.367, 0.950, 205.999, 24.540, 111.270,
                      3.868 + 4.845 + 11.935 + 2.009, 49.930, 0.530,
                      121.127, 96.496, 110.309 + 2.210, 18.558, 3.723, 10.544),
    '2026-06-30': oic(198.909, 7.089, 21.961, 17.724, 0.965, 206.064, 91.203, 137.449,
                      3.196 + 4.717 + 11.389 + 2.582, 55.606, 0.685,
                      175.579, 88.586, 133.676 + 2.127, 16.878, 4.324, 12.252),
}

# ---------------------------------------------------------------- 情景
SCEN = {
    'bear': dict(p=0.30, exai_h2_growth=0.10, ai_loss_h2=30.0,
                 growth=[0.02, 0.04, 0.05, 0.04, 0.04], g_term=0.020, roic_inc=0.10,
                 capex_cash=[125.0, 230.0, 210.0], capex_accr_h2=115.0, prepay_release=[0.0, 10.0, 10.0],
                 listed_mark_extra=0.85, listed_disc=0.40, unlisted_disc=0.45,
                 note='核心增速放缓到 10%，新 AI 产品亏损扩大且 2027～2028 资本开支维持 2100 亿以上，增量 ROIC 等于股权成本'),
    'base': dict(p=0.50, exai_h2_growth=0.15, ai_loss_h2=24.0,
                 growth=[0.10, 0.10, 0.09, 0.08, 0.07], g_term=0.025, roic_inc=0.20,
                 capex_cash=[110.0, 200.0, 175.0], capex_accr_h2=100.0, prepay_release=[0.0, 20.0, 20.0],
                 listed_mark_extra=1.00, listed_disc=0.30, unlisted_disc=0.35,
                 note='核心（剔除新 AI）增速 15% 并逐年回落，AI 亏损 2027 年见顶后收窄，2026 年资本开支约 1850 亿、2027 年 2000 亿见顶，增量 ROIC 20%'),
    'bull': dict(p=0.20, exai_h2_growth=0.18, ai_loss_h2=20.0,
                 growth=[0.14, 0.14, 0.12, 0.10, 0.09], g_term=0.025, roic_inc=0.30,
                 capex_cash=[110.0, 200.0, 175.0], capex_accr_h2=100.0, prepay_release=[0.0, 20.0, 20.0],
                 listed_mark_extra=1.00, listed_disc=0.20, unlisted_disc=0.25,
                 note='WorkBuddy、小微与云把 AI 投入变现，AI 亏损 2028 年转正，增量 ROIC 30%'),
}
H2_SBC, H2_ACQ, H2_SSV = 13.4, 3.2, 0.35
VAL_DATE_TO_MID2027 = 253 / 365.25     # 2026-10-21 → 2027-07-01
T_H2_2026 = 0.10


def core_op_after_sbc_h1():
    h = H1_2026
    return h['nonifrs_op'] - h['sbc_op'] - h['acq_amort_op'] - h['ssv_op'] - h['other_gl']


def e_2026(s):
    """2026 年所有者收益（经营、归母、扣股权激励、不含联营与净利息），返回 (全年, H1, H2, 非国际准则经营利润全年)。"""
    exai_h2 = EXAI_H2_2025 * (1 + s['exai_h2_growth'])
    nonifrs_op_h2 = exai_h2 - s['ai_loss_h2']
    core_h2 = nonifrs_op_h2 - H2_SBC - H2_ACQ - H2_SSV
    k = (1 - TAX) * (1 - NCI)
    e_h1 = core_op_after_sbc_h1() * k
    e_h2 = core_h2 * k
    return e_h1 + e_h2, e_h1, e_h2, H1_2026['nonifrs_op'] + nonifrs_op_h2


def da_path(s):
    """资本开支相关折旧摊销：PPE 按 5 年直线（期初 20% + 当期新增 10%），加使用权资产与其他。"""
    ppe = 198.909
    add_h2 = 0.95 * s['capex_accr_h2']
    dep_h2 = 0.10 * ppe + 0.05 * add_h2
    ppe = ppe + add_h2 - dep_h2
    out = [dep_h2 + 3.3 + 1.0]
    for capex in s['capex_cash'][1:]:
        add = 0.95 * capex
        dep = 0.20 * ppe + 0.10 * add
        ppe = ppe + add - dep
        out.append(dep + 6.8 + 2.0)
    return out


def growth_series(s):
    g = list(s['growth'])                       # 2027-2031
    last, gt = g[-1], s['g_term']
    g += [last - (last - gt) * i / 5 for i in range(1, 6)]   # 2032-2036 线性回落
    return g                                     # 10 个值：2027..2036


def flows(s, override_growth=None):
    e26, e_h1, e_h2, _ = e_2026(s)
    g = override_growth if override_growth is not None else growth_series(s)
    e = [e26]
    for gi in g:
        e.append(e[-1] * (1 + gi))               # e[0]=2026, e[1]=2027 ... e[10]=2036
    e_2037 = e[-1] * (1 + s['g_term'])
    da = da_path(s)
    rows = []
    # 2026H2
    ni_capex = (1 - NCI) * (s['capex_cash'][0] - da[0] - s['prepay_release'][0])
    ni_g = e_h2 * g[0] / s['roic_inc']
    rows.append(('2026H2', T_H2_2026, e_h2, max(ni_capex, ni_g), ni_capex, ni_g))
    for i in range(1, 11):
        year = 2026 + i
        g_next = g[i] if i < 10 else s['g_term']
        ni_g = e[i] * g_next / s['roic_inc']
        ni_capex = None
        if i <= 2:
            ni_capex = (1 - NCI) * (s['capex_cash'][i] - da[i] - s['prepay_release'][i])
            ni = max(ni_capex, ni_g)
        else:
            ni = ni_g
        rows.append((str(year), VAL_DATE_TO_MID2027 + (i - 1), e[i], ni, ni_capex, ni_g))
    tv_fcf = e_2037 * (1 - s['g_term'] / s['roic_inc'])
    return rows, tv_fcf, e


def portfolio(s, listed_fv=LISTED_FV_0630, mark=LISTED_MARK_1021):
    listed = listed_fv * mark * s['listed_mark_extra'] * (1 - s['listed_disc'])
    unlisted = UNLISTED_BOOK_0630 * (1 - s['unlisted_disc'])
    return listed + unlisted, listed, unlisted


def value(s, r, override_growth=None, listed_fv=LISTED_FV_0630, mark=LISTED_MARK_1021, detail=False):
    rows, tv_fcf, _ = flows(s, override_growth)
    pv_ops, last_t = 0.0, 0.0
    for name, t, e, ni, _, _ in rows:
        pv_ops += (e - ni) / (1 + r) ** t
        last_t = t
    tv = tv_fcf / (r - s['g_term'])
    pv_tv = tv / (1 + r) ** last_t
    port, _, _ = portfolio(s, listed_fv, mark)
    ops = pv_ops + pv_tv
    eq_incl = ops + NET_CASH_ADJ + port
    eq_excl = ops + NET_CASH_ADJ
    v_incl = eq_incl / SHARES / HKDCNY
    v_excl = eq_excl / SHARES / HKDCNY
    if detail:
        return dict(pv_explicit=pv_ops, pv_tv=pv_tv, ops=ops, port=port, eq_incl=eq_incl,
                    v_incl=v_incl, v_excl=v_excl, tv_share=pv_tv / ops)
    return v_incl


def weighted(r, scen=SCEN, probs=None, **kw):
    probs = probs or {k: v['p'] for k, v in scen.items()}
    return sum(probs[k] * value(scen[k], r, **kw) for k in scen)


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def main():
    mcap_rmb = SHARES * PRICE_HKD * HKDCNY
    print('== 快照')
    print(f'股价 {PRICE_HKD:.2f} 港元；股本 {SHARES*10:.4f} 亿股（10-15 已发行 {SHARES_ISSUED_1015:,} − 待注销 {sum(PENDING_CANCEL_1015):,}）')
    print(f'市值 {SHARES*PRICE_HKD:.1f} 十亿港元 = {mcap_rmb:.1f} 十亿元')

    print('\n== IFRS 与非国际准则、所有者收益')
    core25 = FY2025['nonifrs_op'] - (FY2025['sbc_op'] - FY2025['sbc_oneoff']) - FY2025['acq_amort_op'] - FY2025['ssv_op'] - FY2025['other_gl']
    k = (1 - TAX) * (1 - NCI)
    e25 = core25 * k
    print(f"2025 IFRS 归母 {FY2025['ifrs_np']:.1f}，非国际准则归母 {FY2025['nonifrs_np']:.1f}，非国际准则经营利润 {FY2025['nonifrs_op']:.1f}")
    print(f'2025 正常化经营利润（扣经常性股权激励 {FY2025["sbc_op"]-FY2025["sbc_oneoff"]:.1f}）{core25:.1f}，所有者收益 E {e25:.1f}')
    for name, s in SCEN.items():
        e26, e_h1, e_h2, op26 = e_2026(s)
        print(f'2026E {name}: 非国际准则经营利润 {op26:.1f}，E {e26:.1f}（H1 {e_h1:.1f}，H2 {e_h2:.1f}）')

    print('\n== 2026 正常化归母净利（IFRS 口径、扣股权激励、含净利息与联营经常性收益、剔除投资收益与减值）')
    net_int_at = (2 * (H1_2026['int_income'] - H1_2026['int_expense']) - 0.6) * (1 - TAX)
    assoc_rec = {'bear': 14.0, 'base': 16.3, 'bull': 18.0}
    np26 = {}
    for name, s in SCEN.items():
        e26 = e_2026(s)[0]
        np26[name] = e26 + net_int_at + assoc_rec[name]
        print(f'{name}: 经营 {e26:.1f} + 税后净利息 {net_int_at:.1f} + 联营经常性 {assoc_rec[name]:.1f} = {np26[name]:.1f}（{np26[name]*10:.0f} 亿）')

    print('\n== FCF（经营现金流 − 资本开支 − 媒体内容 − 租赁本金；再扣股权激励）')
    def fcf(cfo, capex_paid, intangibles_paid, lease_principal):
        return cfo - capex_paid - intangibles_paid - lease_principal
    f24 = fcf(**FY2024_FCF_INPUTS)
    f25 = fcf(FY2025['cfo'], FY2025['capex_paid'], FY2025['intangibles_paid'], FY2025['lease_principal'])
    fh125 = fcf(H1_2025['cfo'], H1_2025['ppe_paid'], H1_2025['intangibles_paid'], H1_2025['lease_principal'])
    fh126 = fcf(H1_2026['cfo'], H1_2026['ppe_paid'], H1_2026['intangibles_paid'], H1_2026['lease_principal'])
    ttm = f25 - fh125 + fh126
    sbc25 = FY2025['sbc_equity_settled'] - FY2025['sbc_oneoff']
    print(f'2024 FCF {f24:.1f}；2025 FCF {f25:.1f}，扣股权激励 {sbc25:.1f} 后 {f25-sbc25:.1f}，归母 {(f25-sbc25)*(1-NCI):.1f}')
    print(f'2026H1 FCF {fh126:.1f}（公司口径 {H1_2026["fcf_company"]:.1f}；Q2 算力预付 {H1_2026["q2_compute_prepay"]:.1f}）；TTM {ttm:.1f}')
    e26b = e_2026(SCEN['base'])[0]
    ops_ev = mcap_rmb - NET_CASH_ADJ - portfolio(SCEN['base'])[0]
    fcf26_cash = (fh126 - H1_2026['sbc_equity_settled']) * (1 - NCI) + flows(SCEN['base'])[0][0][2] - flows(SCEN['base'])[0][0][3]
    print(f'正常化 FCF（维持性资本开支 = 折旧，基准 E）{e26b:.1f}，占经营 EV {ops_ev:.1f} 的 {e26b/ops_ev:.1%}；2025 实际扣 SBC 归母 FCF 占 {((f25-sbc25)*(1-NCI))/ops_ev:.1%}')
    print(f'2026E 实际（H1 实际扣 SBC + 基准 H2）归母 FCF {fcf26_cash:.1f}，占经营 EV {fcf26_cash/ops_ev:.1%}')
    nonifrs_np26 = e_2026(SCEN['base'])[3] * FY2025['nonifrs_np'] / FY2025['nonifrs_op']
    ttm_ifrs = FY2025['ifrs_np'] - H1_2025['ifrs_np'] + H1_2026['ifrs_np']
    print(f'市盈率：IFRS TTM 归母 {ttm_ifrs:.1f} → {mcap_rmb/ttm_ifrs:.1f} 倍；2025 非国际准则 {mcap_rmb/FY2025["nonifrs_np"]:.1f} 倍；2026E 非国际准则约 {nonifrs_np26:.0f} → {mcap_rmb/nonifrs_np26:.1f} 倍；经营 EV / 基准 E2026 {ops_ev/e26b:.1f} 倍')

    print('\n== ROIC（经营性投入资本，不含现金与投资组合）')
    for kd, v in OIC.items():
        print(f'{kd} OIC {v:.1f}')
    nopat25 = core25 * (1 - TAX)
    avg25 = (OIC['2024-12-31'] + OIC['2025-12-31']) / 2
    nopat_h1 = core_op_after_sbc_h1() * (1 - TAX) * 2
    avg_h1 = (OIC['2025-12-31'] + OIC['2026-06-30']) / 2
    print(f'2025 NOPAT {nopat25:.1f} / 平均 OIC {avg25:.1f} = {nopat25/avg25:.0%}；2026H1 年化 {nopat_h1:.1f} / {avg_h1:.1f} = {nopat_h1/avg_h1:.0%}')
    for name, s in SCEN.items():
        rows, _, e = flows(s)
        ni_26_28 = sum(r[3] for r in rows[:3]) + 0.97 * (H1_2026['capex'] - 21.1 + 67.0)
        d_e = e[3] - e25
        print(f'{name}: 2026～2028 再投资合计（含 H1 实际约 {0.97*(H1_2026["capex"]-21.1+67.0):.0f}）{ni_26_28:.0f}，E 2029 − E 2025 = {d_e:.1f}，隐含增量 ROIC {d_e/ni_26_28:.0%}')

    print('\n== 净现金')
    print(f'公司口径 2026-06-30 净现金 {NET_CASH_0630:.1f}（现金 {BS_0630["cash"]} + 定期存款及其他 {BS_0630["term_dep_others"]} − 借款 {BS_0630["borrowings"]} − 票据 {BS_0630["notes"]}）')
    print(f'7-1～10-15 回购约 {BUYBACK_JUL_OCT_SHARES/1e6:.2f} 百万股、{BUYBACK_JUL_OCT_HKD_BN:.1f} 十亿港元 → {ADJ["buyback_after_0630"]:.1f} 十亿元')
    print(f'经调整净现金 {NET_CASH_ADJ:.1f}（扣经营备付 {ADJ["operating_buffer"]}、汇出预提税 {ADJ["wht_repatriation"]}；租赁负债 {BS_0630["lease_liab"]:.1f} 只列示）')

    print('\n== 投资组合')
    for name, s in SCEN.items():
        tot, li, un = portfolio(s)
        print(f'{name}: 上市 {LISTED_FV_0630}×{LISTED_MARK_1021}×{s["listed_mark_extra"]}×(1−{s["listed_disc"]}) = {li:.1f}；非上市 {UNLISTED_BOOK_0630}×(1−{s["unlisted_disc"]}) = {un:.1f}；合计 {tot:.1f}（每股 {tot/SHARES/HKDCNY:.1f} 港元）')
    print(f'不打折：上市（10-21 代理）{LISTED_FV_0630*LISTED_MARK_1021:.1f} + 非上市 {UNLISTED_BOOK_0630} = {LISTED_FV_0630*LISTED_MARK_1021+UNLISTED_BOOK_0630:.1f}')

    for sname in ('bear', 'base', 'bull'):
        print(f'\n== 增长路径与 FCF（{sname}）')
        rows, tv_fcf, e = flows(SCEN[sname])
        g = growth_series(SCEN[sname])
        for (name, t, ei, ni, nic, nig), gi in zip(rows, [None] + g):
            gtxt = '' if gi is None else f' g={gi:5.1%}'
            ctxt = '' if nic is None else f'（资本开支口径 {nic:.1f}，增长口径 {nig:.1f}）'
            print(f'{name:>6} t={t:5.2f}{gtxt} E={ei:6.1f} 再投资={ni:6.1f}{ctxt} FCF={ei-ni:6.1f}')
        print(f'终值：g={SCEN[sname]["g_term"]:.1%}，再投资率 {SCEN[sname]["g_term"]/SCEN[sname]["roic_inc"]:.1%}，2037 年 FCF {tv_fcf:.1f}')

    print('\n== 三情景（股权成本 10%）')
    res = {}
    for name, s in SCEN.items():
        d = value(s, COE_BASE, detail=True)
        res[name] = d
        g = growth_series(s)
        per = lambda x: x / SHARES / HKDCNY
        print(f"{name} 每股：经营 {per(d['ops']):.1f} + 净现金 {per(NET_CASH_ADJ):.1f} + 组合 {per(d['port']):.1f} 港元")
        print(f"{name} p={s['p']:.2f} V={d['v_incl']:.1f} 港元（不含组合 {d['v_excl']:.1f}）；经营 {d['ops']:.0f}（终值占 {d['tv_share']:.0%}），组合 {d['port']:.0f}；"
              f"增速 2027-31 {[round(x,3) for x in g[:5]]}，终值 {s['g_term']}，增量 ROIC {s['roic_inc']}")
    vw = sum(SCEN[k]['p'] * res[k]['v_incl'] for k in SCEN)
    vw_ex = sum(SCEN[k]['p'] * res[k]['v_excl'] for k in SCEN)
    pv = PRICE_HKD / vw
    print(f'加权 V = {vw:.1f} 港元，P/V = {pv:.3f}（{verdict(pv)}）；不含组合加权 V = {vw_ex:.1f}，P/V = {PRICE_HKD/vw_ex:.3f}')
    print(f'合理市值 {vw*SHARES:.0f} 十亿港元（{vw*SHARES*HKDCNY:.0f} 十亿元）；现价相对 V 折价 {1-pv:.1%}')
    print(f'分档价格：≤{0.75*vw:.0f} 明显低估；{0.75*vw:.0f}～{0.90*vw:.0f} 温和低估；{0.90*vw:.0f}～{1.10*vw:.0f} 大致合理；>{1.10*vw:.0f} 偏贵')

    print('\n== 股权成本敏感性（加权 V，港元）')
    for r in (0.08, 0.09, 0.10, 0.11, 0.12):
        v = weighted(r)
        print(f'COE {r:.0%}: V={v:.1f}，P/V={PRICE_HKD/v:.3f}；熊 {value(SCEN["bear"], r):.1f} 基准 {value(SCEN["base"], r):.1f} 牛 {value(SCEN["bull"], r):.1f}')

    print('\n== 隐含回报（IRR，基准情景含组合与净现金）')
    irr = solve(lambda r: value(SCEN['base'], r), 0.06, 0.30, PRICE_HKD)
    irr_w = solve(lambda r: weighted(r), 0.06, 0.30, PRICE_HKD)
    print(f'基准 IRR = {irr:.2%}；三情景加权 IRR = {irr_w:.2%}')

    print('\n== 反向 DCF（10% 股权成本，基准的组合、净现金、增量 ROIC 20%）')
    def v_uniform(g):
        gs = [g] * 5
        gs += [g - (g - 0.025) * i / 5 for i in range(1, 6)]
        return value(SCEN['base'], COE_BASE, override_growth=gs)
    g_star = solve(v_uniform, -0.05, 0.25, PRICE_HKD)
    def v_flat(g):
        return value(SCEN['base'], COE_BASE, override_growth=[g] * 10)
    g_flat = solve(v_flat, -0.05, 0.15, PRICE_HKD)
    base_noport = dict(SCEN['base'], listed_disc=1.0, unlisted_disc=1.0)
    g_star_noport = solve(lambda g: value(base_noport, COE_BASE, override_growth=[g] * 5 + [g - (g - 0.025) * i / 5 for i in range(1, 6)]), -0.05, 0.30, PRICE_HKD)
    print(f'现价隐含 2027～2031 年 E 年增 {g_star:.2%}（2032～2036 线性回落到 2.5%）；若十年同速则 {g_flat:.2%}')
    print(f'若投资组合按零计，现价隐含 2027～2031 年增 {g_star_noport:.2%}')

    print('\n== 股东回报（按现价）')
    mcap_hkd = SHARES * PRICE_HKD
    div25, bb25 = 40.966, 80.036
    div26, bb26_h1 = 47.9, 24.408
    bb26_ytd = bb26_h1 + BUYBACK_JUL_OCT_HKD_BN
    print(f'2025：分红 {div25:.1f} + 回购 {bb25:.1f} = {div25+bb25:.1f} 十亿港元，占现市值 {(div25+bb25)/mcap_hkd:.2%}')
    print(f'2026 至 10-15：分红 {div26:.1f} + 回购 {bb26_ytd:.1f}（H1 {bb26_h1:.1f} 事实 + 7～10 月 {BUYBACK_JUL_OCT_HKD_BN:.1f} 推断）= {div26+bb26_ytd:.1f}，占 {(div26+bb26_ytd)/mcap_hkd:.2%}')
    print(f'股息率（HKD5.30）{5.30/PRICE_HKD:.2%}；2026 回购年化约 {bb26_ytd/(9.5/12)/mcap_hkd:.2%}')
    net_red_25 = 1 - 9_120_235_999 / 9_224_914_953
    net_red_26 = 1 - SHARES * 1e9 / 9_120_235_999
    print(f'净缩股：2025 年 {net_red_25:.2%}；2026 年初至 10-15 {net_red_26:.2%}（回购被股权激励发行抵消大半）')

    print('\n== 证伪条件触发后的 V（港元）')
    f = {}
    f['F1 资本开支高企而回报不见'] = value(SCEN['bear'], COE_BASE)
    f['F2 核心增速跌破 8%'] = weighted(COE_BASE, probs={'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    base_lo = dict(SCEN['base'], growth=[x - 0.03 for x in SCEN['base']['growth'][:3]] + SCEN['base']['growth'][3:])
    f['F3 AI 单季亏损超 150 亿'] = (SCEN['bear']['p'] * value(SCEN['bear'], COE_BASE) + SCEN['base']['p'] * value(base_lo, COE_BASE)
                                + SCEN['bull']['p'] * value(SCEN['bull'], COE_BASE))
    f['F4 国内游戏连续两季同比降 5% 以上'] = weighted(COE_BASE, probs={'bear': 0.60, 'base': 0.40, 'bull': 0.0})
    sc5 = {k: dict(v, listed_disc=v['listed_disc'] + 0.10, unlisted_disc=v['unlisted_disc'] + 0.10) for k, v in SCEN.items()}
    sc5['base']['roic_inc'] = 0.15
    f['F5 回购收缩且股本净增'] = weighted(COE_BASE, scen=sc5)
    f['（参考）组合上市部分跌到 4000 亿'] = weighted(COE_BASE, listed_fv=400.0, mark=1.0)
    for kf, v in f.items():
        print(f'{kf}: V={v:.1f}，P/V={PRICE_HKD/v:.3f}')

    return dict(res=res, vw=vw, vw_ex=vw_ex, irr=irr, irr_w=irr_w, g_star=g_star, np26=np26)


if __name__ == '__main__':
    main()
