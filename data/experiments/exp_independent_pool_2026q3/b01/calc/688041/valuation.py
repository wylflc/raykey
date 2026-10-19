"""688041 海光信息：独立估值（OI-291 b01 深度版）。

运行：python3 valuation.py
金额单位亿元，每股价值单位元/股。价格日 2026-10-19，估值时点即价格日（距 2026-09-30 约 0.05 年，忽略）。

口径
- 经济收益 E = 合并净利 + 折旧摊销 − 全部资本开支（含资本化研发）− 非经常性损益。
  研发无论费用化还是资本化都按现金计入成本；历史资本化形成的无形资产摊销（2025 年约 16 亿）是沉没成本，不再重复扣除。
- 归母所有者收益 OE = (1 − 少数股东份额) × (E − 经营营运资本增量)。
- 经营营运资本 = 应收 + 预付 + 存货 + 预付产能款 − 应付 − 合同负债 − 应付职工薪酬 − 应交税费。
- 净现金按归母权益占比折算归母份额；其他权益工具投资（盛合晶微为主）扣递延税后作非经营资产。
"""

PRICE = 191.50
SHARES = 23.2434          # 亿股，A 股总股本（无其他类别股份）
COE = 0.09
G_T = 0.025
PROBS = {'bear': 0.25, 'base': 0.50, 'bull': 0.25}

# ---------- 1. 2026-09-30 资产负债表（2026Q3_report 第 6-9、12 页） ----------
CASH = 76.7654             # 货币资金
CASH_EQ = 69.4313          # 期末现金及现金等价物；差额视为受限（保证金等）
NCA_1Y = 40.1690           # 一年内到期的非流动资产（中报附注：主要为一年内到期的长期定期存款）
NCA_1Y_NONDEP = 1.0        # 其中非存款部分估计（中报为 1.09）
OTHER_NCA = 25.9457        # 其他非流动资产
OTHER_NCA_NONDEP = 5.8     # 其中预付产能款约 3.0、长期资产预付款约 2.8（中报 3.03、2.76）
OTHER_CA_DEP = 0.2         # 其他流动资产中的定期存款（中报 3.02，三季度到期收回约 3.67）
ST_LOAN, LT_LOAN, NCL_1Y, LEASE = 40.3642, 20.80, 9.6584, 0.7566
RESERVE = 15.0             # 经营备付：约 1 个月现金经营成本
PARENT_EQ, MINORITY_EQ = 264.2328, 41.0342
OEI, OEI_TAX = 6.2991, 0.12   # 其他权益工具投资及递延税

RESTRICTED = CASH - CASH_EQ
DEPOSITS = (NCA_1Y - NCA_1Y_NONDEP) + (OTHER_NCA - OTHER_NCA_NONDEP) + OTHER_CA_DEP
DEBT = ST_LOAN + LT_LOAN + NCL_1Y + LEASE
NET_CASH = CASH - RESTRICTED + DEPOSITS - DEBT - RESERVE
PARENT_SHARE_EQ = PARENT_EQ / (PARENT_EQ + MINORITY_EQ)
NET_CASH_PARENT = NET_CASH * PARENT_SHARE_EQ
NON_OP = OEI * (1 - OEI_TAX)

AR, PREPAY, INV, CAP_PREPAY = 60.2622, 58.8466, 89.2138, 3.0
AP, CONTRACT_LIAB, STAFF_PAY, TAX_PAY = 9.5966, 0.1189, 9.2864, 2.8400
WC_Q3 = AR + PREPAY + INV + CAP_PREPAY - AP - CONTRACT_LIAB - STAFF_PAY - TAX_PAY

# ---------- 2. 2026 年前三季度实际（2026Q3_report 第 1-3、9-12 页） ----------
REV_9M = 149.5471
PARENT_NP_9M = 28.4651
NONREC_9M = 2.6227         # 归母非经常性损益
NP_9M = 34.7476            # 合并净利
MINORITY_NP_9M = 6.2825
DA_9M_EST = 14.0           # 估计：无形资产摊销约 10.5（余额 30.90→21.41）+ 固定资产等约 3.5
CAPEX_9M = 14.3460
NONREC_9M_CONS = 2.70      # 合并口径非经常性损益（归母 2.62 + 少数股东 0.08）
E_9M = NP_9M + DA_9M_EST - CAPEX_9M - NONREC_9M_CONS
NONREC_Q4 = 0.9            # 第四季度归母非经常性损益估计（2025 年四季度约 0.95）

# ---------- 3. 情景 ----------
# g: 2027-2036 营收增速；e: 2027-2036 经济收益率 E/营收；ms: 2026Q4 起少数股东份额（11 个值）
# w: 2027-2036 年末经营营运资本/营收；w26: 2026 年末（None 表示维持三季度末金额）
# q4_rev/q4_e/q4_npm: 2026 年四季度营收、经济收益率与报表净利率
SCEN = {
    'bear': dict(q4_rev=62.0, q4_e=0.12, q4_npm=0.14,
                 g=[0.15, 0.03, 0.07, 0.06, 0.05, 0.04, 0.035, 0.03, 0.03, 0.025],
                 e=[0.21, 0.21, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20],
                 ms=[0.22] * 11, w26=0.90,
                 w=[0.85] + [0.82] * 9),
    'base': dict(q4_rev=68.4, q4_e=0.15, q4_npm=0.17,
                 g=[0.32, 0.24, 0.18, 0.13, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03],
                 e=[0.25, 0.265, 0.275] + [0.28] * 7,
                 ms=[0.20, 0.18, 0.17, 0.16] + [0.15] * 7, w26=None,
                 w=[0.80, 0.74, 0.70, 0.67] + [0.65] * 6),
    'bull': dict(q4_rev=72.0, q4_e=0.17, q4_npm=0.185,
                 g=[0.42, 0.32, 0.25, 0.20, 0.16, 0.12, 0.10, 0.08, 0.06, 0.04],
                 e=[0.27, 0.295, 0.31] + [0.32] * 7,
                 ms=[0.18, 0.15, 0.13] + [0.12] * 8, w26=0.85,
                 w=[0.72, 0.64, 0.58, 0.55] + [0.52] * 6),
}

# 报表净利路径（仅用于市盈率对照，不进入 DCF）：资本开支/营收与非遗留折旧摊销/营收
CAPEX_RATIO = [0.07, 0.065, 0.06, 0.06, 0.06]
LEGACY_AMORT = [12.0, 4.5, 1.0, 0.0, 0.0]      # 历史资本化无形资产摊销余额消化
OTHER_DA_RATIO = [0.028, 0.034, 0.040, 0.044, 0.048]


def pad(lst, n):
    return list(lst) + [lst[-1]] * (n - len(lst))


def run(s, r=COE, growth=None):
    """返回每股价值与明细。growth 可覆盖 2027 起的营收增速序列（任意长度）。"""
    g = list(growth if growth is not None else s['g'])
    n = len(g)
    e, w = pad(s['e'], n), pad(s['w'], n)
    ms = pad(s['ms'], n + 1)
    rev26 = REV_9M + s['q4_rev']
    wc26 = s['w26'] * rev26 if s['w26'] is not None else WC_Q3
    q4_oe = (1 - ms[0]) * (s['q4_rev'] * s['q4_e'] - (wc26 - WC_Q3))
    pv_exp = q4_oe / (1 + r) ** 0.1
    rows = []
    R, wc_prev = rev26, wc26
    for i in range(n):
        R1 = R * (1 + g[i])
        E = R1 * e[i]
        wc = w[i] * R1
        oe = (1 - ms[i + 1]) * (E - (wc - wc_prev))
        t = 0.7 + i
        pv = oe / (1 + r) ** t
        pv_exp += pv
        rows.append(dict(year=2027 + i, rev=R1, E=E, ms=ms[i + 1], dwc=wc - wc_prev, oe=oe, pv=pv,
                         parent_E=(1 - ms[i + 1]) * E))
        R, wc_prev = R1, wc
    R_t = R * (1 + G_T)
    oe_t = (1 - ms[-1]) * (R_t * e[-1] - w[-1] * (R_t - R))
    tv = oe_t / (r - G_T)
    pv_tv = tv / (1 + r) ** (0.2 + n)
    equity = pv_exp + pv_tv + NET_CASH_PARENT + NON_OP
    return dict(v=equity / SHARES, equity=equity, pv_exp=pv_exp, pv_tv=pv_tv,
                tv_share=pv_tv / (pv_exp + pv_tv), rows=rows, rev26=rev26, wc26=wc26,
                q4_oe=q4_oe, oe_t=oe_t, tv=tv)


def weighted(r=COE, scen=SCEN, probs=PROBS):
    return sum(probs[k] * run(scen[k], r)['v'] for k in probs)


def solve(f, lo, hi, target, it=200):
    """二分求 f(x)=target，f 单调。"""
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def normalized_np_2026(s):
    """2026 年报表口径归母净利与正常化（扣非）归母净利。"""
    q4_parent = s['q4_rev'] * s['q4_npm'] * (1 - s['ms'][0])
    reported = PARENT_NP_9M + q4_parent
    return reported, reported - NONREC_9M - NONREC_Q4


def reported_np_path(s):
    """基准报表净利路径：NP = E + 资本开支 − 折旧摊销（合并），再乘归母份额。"""
    res = run(s)
    out = []
    for i, row in enumerate(res['rows'][:5]):
        capex = CAPEX_RATIO[i] * row['rev']
        da = LEGACY_AMORT[i] + OTHER_DA_RATIO[i] * row['rev']
        np_cons = row['E'] + capex - da
        out.append(dict(year=row['year'], np_cons=np_cons, np_parent=np_cons * (1 - row['ms']),
                        net_capex=capex - da, dwc=row['dwc']))
    return out


def base_q4_e():
    s = SCEN['base']
    return s['q4_rev'] * s['q4_e']


def variant(base, **kw):
    s = dict(base)
    s.update(kw)
    return s


def main():
    print('== 净现金与非经营资产（2026-09-30）==')
    print(f'受限资金 {RESTRICTED:.2f}；定期存款合计 {DEPOSITS:.2f}；有息及类债务 {DEBT:.2f}；经营备付 {RESERVE:.1f}')
    print(f'经调整净现金（合并）{NET_CASH:.2f}；归母份额 {PARENT_SHARE_EQ:.3f} → {NET_CASH_PARENT:.2f}；'
          f'非经营资产 {NON_OP:.2f}；三季度末经营营运资本 {WC_Q3:.2f}')
    print(f'前三季度经济收益 E {E_9M:.2f}（占营收 {E_9M / REV_9M:.1%}）；少数股东份额 {MINORITY_NP_9M / NP_9M:.1%}')

    print('\n== 三情景（股权成本 9%）==')
    res = {k: run(SCEN[k]) for k in SCEN}
    for k in SCEN:
        x = res[k]
        r36 = x['rows'][-1]['rev']
        print(f"{k}: V={x['v']:.1f} 元/股，p={PROBS[k]:.2f}，2026 营收 {x['rev26']:.1f}，2031 营收 {x['rows'][4]['rev']:.0f}，"
              f"2036 营收 {r36:.0f}，终值占比 {x['tv_share']:.0%}，2026Q4 所有者收益 {x['q4_oe']:.1f}")
    vw = weighted()
    print(f'加权 V = {vw:.1f} 元/股；P/V = {PRICE / vw:.2f}')
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'股权成本 8%：加权 V {v8:.1f}（熊 {run(SCEN["bear"], 0.08)["v"]:.1f}／基 {run(SCEN["base"], 0.08)["v"]:.1f}／'
          f'牛 {run(SCEN["bull"], 0.08)["v"]:.1f}）')
    print(f'股权成本 10%：加权 V {v10:.1f}（熊 {run(SCEN["bear"], 0.10)["v"]:.1f}／基 {run(SCEN["base"], 0.10)["v"]:.1f}／'
          f'牛 {run(SCEN["bull"], 0.10)["v"]:.1f}）')

    irr = solve(lambda r: run(SCEN['base'], r)['v'], 0.0255, 0.20, PRICE)
    print(f'现价隐含回报（基准情景流＋终值＋净现金）= {irr:.2%}')
    irr_bull = solve(lambda r: run(SCEN['bull'], r)['v'], 0.0255, 0.20, PRICE)
    print(f'（对照）牛市情景流的隐含回报 = {irr_bull:.2%}')

    print('\n== 基准增长路径（归母经济收益，扣全部资本开支、未扣营运资本）==')
    pe26 = (E_9M * (1 - MINORITY_NP_9M / NP_9M)
            + SCEN['base']['q4_rev'] * SCEN['base']['q4_e'] * (1 - SCEN['base']['ms'][0]))
    prev = pe26
    growth = []
    for row in res['base']['rows'][:5]:
        gr = row['parent_E'] / prev - 1
        growth.append(gr)
        print(f"{row['year']}: 营收 {row['rev']:.1f}，E {row['E']:.1f}，归母 E {row['parent_E']:.1f}（{gr:+.1%}），"
              f"营运资本增量 {row['dwc']:.1f}，归母所有者收益 {row['oe']:.1f}")
        prev = row['parent_E']
    print(f'2026 归母经济收益 {pe26:.1f}；终值年归母所有者收益 {res["base"]["oe_t"]:.1f}，终值 {res["base"]["tv"]:.0f}')
    path = reported_np_path(SCEN['base'])
    np26_rep, np26_norm = normalized_np_2026(SCEN['base'])
    q4_cons = SCEN['base']['q4_rev'] * SCEN['base']['q4_npm'] - NONREC_Q4 / (1 - SCEN['base']['ms'][0])
    np26_cons_norm = NP_9M - NONREC_9M_CONS + q4_cons
    reinv = sum(p['dwc'] + p['net_capex'] for p in path)
    sum_np = sum(p['np_cons'] for p in path)
    inc_ret = (path[-1]['np_cons'] - np26_cons_norm) / reinv
    print(f'2027-2031 再投资（营运资本＋资本开支净额）{reinv:.1f}，同期合并净利合计 {sum_np:.1f} → 再投资率 {reinv / sum_np:.0%}；'
          f'增量回报 {inc_ret:.0%}（2031 合并净利 {path[-1]["np_cons"]:.1f} 对 2026 正常化 {np26_cons_norm:.1f}）')
    e26 = E_9M + base_q4_e()
    d_rev = res['base']['rows'][4]['rev'] - res['base']['rev26']
    print(f'2026 全年经济收益 E {e26:.1f}（占营收 {e26 / res["base"]["rev26"]:.1%}）；2026→2031 营收增加 {d_rev:.0f}，'
          f'每元增量营收占用资本 {reinv / d_rev:.2f} 元，按长期 E 率 28% 的增量回报 {0.28 / (reinv / d_rev):.0%}')
    print('基准报表口径归母净利与市盈率：' + '；'.join(
        f"{p['year']} {p['np_parent']:.1f}（{PRICE * SHARES / p['np_parent']:.0f}×）" for p in path))
    print(f'2026E 报表归母净利 {np26_rep:.1f}（{PRICE * SHARES / np26_rep:.0f}×）')

    print('\n== 2026 正常化归母净利（报表口径，扣非）==')
    for k in SCEN:
        rep, norm = normalized_np_2026(SCEN[k])
        print(f'{k}: 报表 {rep:.1f}，正常化 {norm:.1f}')

    print('\n== 反向 DCF ==')
    base = SCEN['base']
    g_uni = solve(lambda g: run(base, growth=[g] * 10)['v'], 0.0, 0.6, PRICE)
    rev36 = run(base, growth=[g_uni] * 10)['rows'][-1]['rev']
    print(f'基准利润率/营运资本/少数股东不变：2027-2036 营收需年增 {g_uni:.1%}（2036 年 {rev36:.0f} 亿，为 2026 年的 '
          f'{rev36 / run(base)["rev26"]:.1f} 倍），之后 2.5% 永续')

    def v_years(nyr, gh=0.32):
        fade = [gh - (gh - G_T) * (j + 1) / 6 for j in range(5)]
        return run(base, growth=[gh] * nyr + fade)['v']
    for nyr in range(1, 21):
        if v_years(nyr) >= PRICE:
            lo, hi = v_years(nyr - 1), v_years(nyr)
            frac = (PRICE - lo) / (hi - lo)
            fade = [0.32 - (0.32 - G_T) * (j + 1) / 6 for j in range(5)]
            r_end = run(base, growth=[0.32] * nyr + fade)['rows'][-1]['rev']
            print(f'或：营收 32% 增速需维持约 {nyr - 1 + frac:.1f} 年，再用 5 年从 27% 线性放缓到 7%，之后 2.5% 永续'
                  f'（取整 {nyr} 年时末年营收 {r_end:.0f} 亿；基准只有 2027 年一年 32%）')
            break
    oe0 = pe26
    pv_target = PRICE * SHARES - NET_CASH_PARENT - NON_OP

    def pv_simple(g):
        pv, x = 0.0, oe0
        for t in range(1, 11):
            x *= 1 + g
            pv += x / (1 + COE) ** (t - 0.3)
        return pv + x * (1 + G_T) / (COE - G_T) / (1 + COE) ** 10.2
    g_oe = solve(pv_simple, 0.0, 0.8, pv_target)
    print(f'宽松口径：把 2026 归母经济收益 {oe0:.1f} 亿视作可全部分配，现价隐含 10 年增速 {g_oe:.1%}（不扣营运资本）')

    print('\n== 证伪触发后的 V（股权成本 9%）==')
    tilt = {'bear': 0.5, 'base': 0.4, 'bull': 0.1}
    f1 = weighted(probs=tilt)
    b_margin = variant(base, e=[0.23, 0.225, 0.22] + [0.22] * 7)
    f2 = 0.25 * run(SCEN['bear'])['v'] + 0.5 * run(b_margin)['v'] + 0.25 * run(SCEN['bull'])['v']
    b_wc = variant(base, w=[0.85] * 10)
    f3 = 0.25 * run(SCEN['bear'])['v'] + 0.5 * run(b_wc)['v'] + 0.25 * run(SCEN['bull'])['v']
    b_ms = variant(base, ms=[0.25] * 11)
    f4 = 0.25 * run(SCEN['bear'])['v'] + 0.5 * run(b_ms)['v'] + 0.25 * run(SCEN['bull'])['v']
    f5 = weighted(probs={'bear': 0.1, 'base': 0.4, 'bull': 0.5})
    print(f'F1 营收不及（权重熊 50/基 40/牛 10）：{f1:.1f}')
    print(f'F2 毛利率失守（基准长期 E 率 22%）：{f2:.1f}（基准情景 {run(b_margin)["v"]:.1f}）')
    print(f'F3 营运资本不回落（基准 w 维持 0.85）：{f3:.1f}（基准情景 {run(b_wc)["v"]:.1f}）')
    print(f'F4 少数股东份额回升至 25%：{f4:.1f}（基准情景 {run(b_ms)["v"]:.1f}）')
    print(f'F5 上行：2027 达到牛市路径（权重熊 10/基 40/牛 50）：{f5:.1f}')

    print('\n== 分档价格（V 不变）==')
    print(f'明显低估 ≤ {0.75 * vw:.1f}；温和低估 ≤ {0.90 * vw:.1f}；大致合理 ≤ {1.10 * vw:.1f}；高于 {1.10 * vw:.1f} 为偏贵')

    print('\n== 交叉验证 ==')
    mcap = PRICE * SHARES
    ev = mcap + MINORITY_EQ - NET_CASH - NON_OP
    ebit_ttm = 43.76 - 1.24 - 3.6   # 营业利润 TTM（36.05−28.39+36.10）− 净利息收入 − 非经常性补助等
    print(f'市值 {mcap:.0f}；市值/TTM 归母 {mcap / 34.30:.0f}×；PB {mcap / PARENT_EQ:.2f}×；EV {ev:.0f}，EV/EBIT(TTM) {ev / ebit_ttm:.0f}×')
    print(f'股息率 {0.24 / PRICE:.2%}；拟回购 5-8 亿占市值 {5 / mcap:.2%}-{8 / mcap:.2%}')


if __name__ == '__main__':
    main()
