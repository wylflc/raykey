"""安集科技（688019）独立估值：归母所有者收益 DCF（经营口径）+ 经调整净现金 + 非经营资产。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。全部输入写在本脚本内，出处见同目录上级 companies/688019_安集科技.md「来源」。
"""

PRICE = 189.32                     # 2026-10-20 收盘，A 股未复权（brief）
SHARES = 2.28356543                # 亿股：2026-08-03 登记后总股本 228,356,543 股（公告 2026-059），无回购专户、无拟注销股份
COE = 0.09
YEARS_TO_YEAREND = 72 / 365        # 2026-10-20 → 2026-12-31

# ---------------- 资产负债表（2026-06-30，2026H1_report 第 77-78、117、131、150-157 页） ----------------
CASH = 14.5628                     # 货币资金
STRUCT_DEP = 2.9625                # 交易性金融资产（全部为结构性存款）
CD_1Y = 0.2142                     # 一年内到期的大额存单
RESTRICTED = 0.1469                # 受限货币资金（信用证及担保保证金）
VEST_PROCEEDS = 0.3921             # 2026-07 收到的激励归属认购款（公告 2026-059：631.66 万 + 3,289.71 万）
USD_CASH_MUSD = 1.9678             # 美元货币资金 1.968 亿美元（第 174 页）
FX_0630, FX_0930 = 6.8109, 6.7351  # 美元中间价：6-30 折算汇率；9-30 中间价（新华网 2026-09-30）
OP_RESERVE = 1.5                   # 经营备付：约 2026E 营收 5%（约 3～4 周经营现金流出）
ST_LOAN = 1.0567                   # 短期借款
LT_LOAN = 2.4496                   # 长期借款（含一年内到期 0.0764）
LEASE = 1.7460                     # 租赁负债（含一年内到期 0.5042）
MINORITY = 0.1917                  # 少数股东权益（南京安瑞）

FUND_FV, FUND_COST = 3.4270, 1.8152  # 其他非流动金融资产（私募基金）公允价值与成本（第 136 页）
OEI = 0.5175                       # 其他权益工具投资（第 135 页）
LTEI = 1.7471                      # 长期股权投资（联营 A～E，第 134 页）
GAIN_TAX = 0.20                    # 未实现收益的所得税（母公司 15%、投资子公司 25% 的折中）
ILLIQ = 0.80                       # 非上市股权与基金份额按 80% 计

DEBT = ST_LOAN + LT_LOAN + LEASE
FX_REVAL = USD_CASH_MUSD * (FX_0930 - FX_0630)
NET_CASH_ADJ = CASH + STRUCT_DEP + CD_1Y - RESTRICTED + VEST_PROCEEDS + FX_REVAL - OP_RESERVE - DEBT
NON_OP = ILLIQ * (FUND_FV - GAIN_TAX * (FUND_FV - FUND_COST)) + ILLIQ * OEI + ILLIQ * LTEI

# ---------------- 2026 正常化归母净利 ----------------
H1_REV = 15.2636                   # 2026H1 营收
H1_KF = 4.2576                     # 2026H1 扣非归母
H1_FX_LOSS = 0.5513                # 2026H1 汇兑损失（计入扣非，第 165 页）
TAX_FX = 0.15
H1_NORM = H1_KF + H1_FX_LOSS * (1 - TAX_FX)   # 汇兑按零期望剔除；含净利息、经常性补助与股份支付
NET_INT_AT_2026 = 0.27             # 2026 税后净利息（上半年税前 0.145，下半年约 0.176，税率 15%）

SCEN = {
    # k：每新增 1 元营收需要的经营资本（营运资本+长期经营资产）；2023 末→2026-06 实际 0.98
    'bear': dict(p=0.25, h2_rev=16.8, h2_margin=0.260, m_end=0.225, k=1.10, gT=0.020,
                 g=[0.12, 0.09, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]),
    'base': dict(p=0.50, h2_rev=17.5, h2_margin=0.275, m_end=0.270, k=0.95, gT=0.025,
                 g=[0.24, 0.20, 0.17, 0.15, 0.13, 0.11, 0.09, 0.07, 0.055, 0.04]),
    'bull': dict(p=0.25, h2_rev=18.2, h2_margin=0.290, m_end=0.300, k=0.80, gT=0.025,
                 g=[0.30, 0.26, 0.22, 0.19, 0.16, 0.14, 0.12, 0.10, 0.08, 0.06]),
}
YEARS = list(range(2026, 2037))


def norm_np_2026(s):
    return H1_NORM + s['h2_rev'] * s['h2_margin']


def path(s, g_override=None, m_end=None):
    g = g_override if g_override is not None else s['g']
    rev26 = H1_REV + s['h2_rev']
    m26 = (norm_np_2026(s) - NET_INT_AT_2026) / rev26
    m_end = s['m_end'] if m_end is None else m_end
    rev = [rev26]
    for x in g:
        rev.append(rev[-1] * (1 + x))
    m = [m26 + (m_end - m26) * min(i, 5) / 5 for i in range(11)]
    op_np = [a * b for a, b in zip(rev, m)]
    return rev, m, op_np


def value(s, r=COE, g_override=None, m_end=None, k=None):
    k = s['k'] if k is None else k
    rev, m, op_np = path(s, g_override, m_end)
    gT = s['gT']
    rev37 = rev[10] * (1 + gT)
    np37 = op_np[10] * (1 + gT)
    oe = []
    for t in range(1, 11):
        nxt = rev[t + 1] if t < 10 else rev37
        oe.append(op_np[t] - k * max(nxt - rev[t], 0.0))
    h2_np = s['h2_rev'] * s['h2_margin']
    oe_h2 = h2_np - 0.5 * k * max(rev[1] - rev[0], 0.0)
    oe37 = np37 - k * gT * rev37
    tv = oe37 / (r - gT)
    pv_oe = sum(oe[t - 1] / (1 + r) ** (t - 0.5) for t in range(1, 11))
    pv_tv = tv / (1 + r) ** 10
    eq_ye = pv_oe + pv_tv + NET_CASH_ADJ + oe_h2 + NON_OP - MINORITY
    eq_now = eq_ye / (1 + r) ** YEARS_TO_YEAREND
    reinv = [1 - oe[i] / op_np[i + 1] for i in range(10)]
    roiic = [m[i] / k for i in range(11)]
    return dict(rev=rev, m=m, op_np=op_np, oe=oe, oe_h2=oe_h2, pv_oe=pv_oe, pv_tv=pv_tv, tv=tv, oe37=oe37,
                tv_share=pv_tv / (pv_oe + pv_tv), eq=eq_now, v=eq_now / SHARES, reinv=reinv, roiic=roiic,
                reinv_T=k * gT * rev37 / np37)


def weighted(r=COE, weights=None, **kw):
    w = weights or {k: s['p'] for k, s in SCEN.items()}
    return sum(w[k] * value(SCEN[k], r, **kw)['v'] for k in SCEN)


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


def h_dilution(v, p_h, frac_post=0.10, overallot=0.15, fee=0.03):
    n = SHARES * frac_post / (1 - frac_post) * (1 + overallot)
    return (v * SHARES + p_h * (1 - fee) * n) / (SHARES + n), n


if __name__ == '__main__':
    print('=== 输入与调整 ===')
    print(f'总股本 {SHARES:.4f} 亿股；现价 {PRICE}；市值 {PRICE * SHARES:.1f} 亿元')
    print(f'有息负债 {DEBT:.2f}；美元现金按 9-30 中间价重估 {FX_REVAL:+.2f}；经调整净现金 {NET_CASH_ADJ:.2f}；非经营资产 {NON_OP:.2f}；少数股东 {MINORITY:.2f}')
    print(f'2026H1 正常化归母 {H1_NORM:.3f}（扣非 {H1_KF} + 汇兑损失税后 {H1_FX_LOSS * (1 - TAX_FX):.3f}）')

    print('\n=== 三情景（股权成本 9%） ===')
    res = {}
    for k, s in SCEN.items():
        r = value(s)
        res[k] = r
        rev, m, op = r['rev'], r['m'], r['op_np']
        print(f"[{k}] p={s['p']:.2f}  V={r['v']:.1f} 元/股  股权价值 {r['eq']:.1f} 亿  终值占比 {r['tv_share']:.0%}  2026 正常化归母 {norm_np_2026(s):.2f}")
        print('   营收增速 2027-31:', [f'{x:.0%}' for x in s['g'][:5]], ' 2032-36:', [f'{x:.1%}' for x in s['g'][5:]], f" 永续 {s['gT']:.1%}")
        print('   营收      :', ' '.join(f'{y}:{x:.1f}' for y, x in zip(YEARS, rev)))
        print('   经营净利率:', ' '.join(f'{y}:{x:.1%}' for y, x in zip(YEARS, m)))
        print('   经营归母  :', ' '.join(f'{y}:{x:.2f}' for y, x in zip(YEARS, op)))
        print('   所有者收益:', f'2026H2:{r["oe_h2"]:.2f}', ' '.join(f'{y}:{x:.2f}' for y, x in zip(YEARS[1:], r['oe'])))
        oe_g = [r['oe'][i] / r['oe'][i - 1] - 1 for i in range(1, 5)]
        print('   所有者收益增速 2028-31:', [f'{x:.0%}' for x in oe_g], ' 再投资率 2027-31:', [f'{x:.0%}' for x in r['reinv'][:5]],
              f" 终值再投资率 {r['reinv_T']:.0%}；增量资本/增量营收 {s['k']:.2f}，增量回报 {r['roiic'][1]:.0%}→{r['roiic'][10]:.0%}")
    b = res['base']
    g_np = [b['op_np'][i] / b['op_np'][i - 1] - 1 for i in range(1, 6)]
    print('\n基准增长路径（经营归母，2027-31）:', [f'{x:.1%}' for x in g_np],
          f"；再投资率 2027-31 均值 {sum(b['reinv'][:5]) / 5:.0%}；增量回报 {b['roiic'][1]:.1%}→{b['roiic'][10]:.1%}；终值再投资率 {b['reinv_T']:.0%}")
    for k in SCEN:
        rv = res[k]['rev']
        print(f"  {k}: 2026-36 营收复合 {(rv[10] / rv[0]) ** 0.1 - 1:.1%}，2036 营收 {rv[10]:.1f} 亿，2031 营收 {rv[5]:.1f} 亿")
    vw = weighted()
    print(f'\n加权 V = {vw:.1f} 元/股；P/V = {PRICE / vw:.2f}')
    for k in SCEN:
        print(f'  {k}: V {res[k]["v"]:.1f}，P/V {PRICE / res[k]["v"]:.2f}')
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'股权成本 8%：加权 V {v8:.1f}（熊 {value(SCEN["bear"], 0.08)["v"]:.1f} / 基准 {value(SCEN["base"], 0.08)["v"]:.1f} / 牛 {value(SCEN["bull"], 0.08)["v"]:.1f}）')
    print(f'股权成本 10%：加权 V {v10:.1f}（熊 {value(SCEN["bear"], 0.10)["v"]:.1f} / 基准 {value(SCEN["base"], 0.10)["v"]:.1f} / 牛 {value(SCEN["bull"], 0.10)["v"]:.1f}）')

    irr = solve(lambda r: value(SCEN['base'], r)['v'], 0.03, 0.20, PRICE)
    irr_bull = solve(lambda r: value(SCEN['bull'], r)['v'], 0.03, 0.20, PRICE)
    print(f'现价隐含回报（基准情景现金流）：{irr:.2%}；牛市情景现金流：{irr_bull:.2%}')

    base = SCEN['base']
    g_imp = solve(lambda g: value(base, g_override=[g] * 10, m_end=value(base)['m'][0])['v'], 0.0, 0.6, PRICE)
    print(f'反向 DCF：经营净利率维持 2026 水平、增量资本/营收 0.95、2036 后永续 2.5%，现价隐含 2027-36 营收（≈经营归母）年增 {g_imp:.1%}')
    g10 = [g_imp] * 10
    rev_imp = value(base, g_override=g10, m_end=value(base)['m'][0])['rev'][-1]
    print(f'   即 2036 营收约 {rev_imp:.0f} 亿元（基准情景 {res["base"]["rev"][-1]:.0f} 亿）')

    def v_perp(g):
        s = dict(base, g=[g] * 10, gT=g)
        return value(s, g_override=[g] * 10, m_end=value(base)['m'][0])['v']
    g_perp = solve(v_perp, 0.0, 0.0899, PRICE)
    print(f'   若自 2027 起永续同速增长，现价隐含永续增速 {g_perp:.2%}（增量资本/营收 0.95）')

    print('\n=== 交叉验证 ===')
    mcap = PRICE * SHARES
    np26 = norm_np_2026(base)
    np27 = res['base']['op_np'][1] + 0.30
    ev = mcap - NET_CASH_ADJ - NON_OP + MINORITY
    ebit26 = (np26 - NET_INT_AT_2026) / (1 - 0.10)
    print(f'市值/2026 正常化归母 {mcap / np26:.1f}×；市值/2027 基准归母 {mcap / np27:.1f}×（2027 基准归母 {np27:.2f}）；EV {ev:.0f} 亿，EV/2026 正常化 EBIT {ev / ebit26:.1f}×（EBIT {ebit26:.2f}）')
    for pe in (33.7, 40.0, 46.9):
        print(f'  历史 PE {pe}× × 2026 正常化归母 → 每股 {(pe * np26 + 0) / SHARES:.0f} 元')
    print(f'  股息率 {0.875 / mcap:.2%}（2025 年度派现 0.875 亿元），无回购；激励归属年增发约 0.4%')

    print('\n=== H 股发行敏感性（不超过发行后总股本 10%，超额配售 15%，费用 3%） ===')
    for p_h in (100, 130, 160):
        v_new, n = h_dilution(vw, p_h)
        print(f'  发行价折合 {p_h} 元：新增 {n:.3f} 亿股，加权 V {vw:.1f} → {v_new:.1f}')

    print('\n=== 证伪条件触发后的 V ===')
    f1 = weighted(weights={'bear': 0.5, 'base': 0.4, 'bull': 0.1})
    f2 = sum(SCEN[k]['p'] * value(SCEN[k], m_end=me)['v'] for k, me in (('bear', 0.20), ('base', 0.24), ('bull', 0.27)))
    f3 = weighted(weights={'bear': 0.6, 'base': 0.4, 'bull': 0.0})
    f4 = sum(SCEN[k]['p'] * value(SCEN[k], k=kk)['v'] for k, kk in (('bear', 1.30), ('base', 1.15), ('bull', 0.95)))
    f5 = weighted(weights={'bear': 0.1, 'base': 0.4, 'bull': 0.5})
    f6, _ = h_dilution(vw, 100)
    print(f'F1 三季报单季营收 <7.8 亿或扣非（剔汇兑）净利率 <24%：权重 50/40/10 → V {f1:.1f}')
    print(f'F2 2026 年报 CMP 毛利率 <52%：终局净利率 熊 20%/基准 24%/牛 27% → V {f2:.1f}')
    print(f'F3 2027 中报营收同比 <12%：权重 60/40/0 → V {f3:.1f}')
    print(f'F4 2026 年末存货 >16 亿元或全年存货减值 >0.6 亿元：增量资本/营收 熊 1.30/基准 1.15/牛 0.95 → V {f4:.1f}')
    print(f'F5（上行）2027 年营收 ≥44 亿元且正常化净利率 ≥29%：权重 10/40/50 → V {f5:.1f}')
    print(f'F6 H 股按折合 100 元/股足额发行（含超额配售）→ V {f6:.1f}')

    print('\n=== V 不变时进入各档的价格 ===')
    print(f'≤0.75 明显低估：≤{0.75 * vw:.1f}；0.75～0.90 温和低估：{0.75 * vw:.1f}～{0.90 * vw:.1f}；0.90～1.10 大致合理：{0.90 * vw:.1f}～{1.10 * vw:.1f}；>1.10 偏贵：>{1.10 * vw:.1f}')
