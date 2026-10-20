# -*- coding: utf-8 -*-
"""豪迈科技（002595）独立估值（OI-291 b05，深度版）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。全部输入写在本脚本内，出处见同目录上级
companies/002595_豪迈科技.md 的来源节。估值日 2026-10-19，现价 38.60 元，
总股本 11.6000 亿股（2026-05-11 转增后；回购专户已于 2025-11-28 全部过户给
2025 年员工持股计划，无专户股份可剔除）。
"""

PRICE = 38.60
SHARES = 11.60          # 亿股
COE = 0.09
TAX = 0.125             # 正常化所得税率：2023-2025 实际 12.6%/12.2%/12.5%

# ---------------------------------------------------------------- 1. 经调整净现金（2026-06-30）
CASH = 9.0018                 # 货币资金，2026H1_report 第 84-85 页
RESTRICTED = 0.1024           # 保函/信用证/结售汇保证金，同上
ENTRUSTED_LOANS = 4.30        # 委托贷款余额：2026-09-14 公告“财务资助总余额 4.30 亿元”（中报为 4.3576）
TIME_DEPOSIT = 0.1511         # 其他流动资产-银行定期存单，2026H1_report 第 92 页
LARGE_CD = 1.2837             # 其他非流动资产-大额存单，2026H1_report 第 101 页
OPERATING_RESERVE = 3.0       # 经营备付：约 2.5% 营收，约半个月付现成本
DEBT = 0.7084 + 0.0807 + 0.1013   # 短期借款+一年内到期租赁+租赁负债
UNION_FUND = 4.1448           # 应付职工薪酬-工会经费和职工教育经费余额（累积计提、极少支付），按类债务扣除
DIV_DECLARED = 0.0            # 2025 年度 8.0 亿元现金红利已于 2026-05-11 发放

cash_like = CASH - RESTRICTED + ENTRUSTED_LOANS + TIME_DEPOSIT + LARGE_CD
NET_CASH_ADJ = cash_like - OPERATING_RESERVE - DEBT - UNION_FUND - DIV_DECLARED
# 非经营资产：长期股权投资（济南豪迈动力基金等，账面）+ 投资性房地产（账面）
NON_OP = 1.0020 + 0.7941

# ---------------------------------------------------------------- 2. 2026 年正常化
# 核心税前利润 = 利润总额 - 非经常性损益(税前) + 汇兑损失
CORE_PBT = {
    '2025Q1': 5.40, '2025Q2': 7.435, '2025Q3': 6.34, '2025Q4': 6.28,
    '2026Q1': 6.32, '2026Q2': 6.90,
}
REV = {'2025Q1': 22.79, '2025Q2': 29.86, '2025Q3': 28.11, '2025Q4': 30.02,
       '2026Q1': 26.68, '2026Q2': 33.49}
# 2026Q3/Q4 估计：营收同比 +9%/+8%，核心税前利润率 21%（近四季 21.8%，2026Q2 20.6%）
REV_Q3E, REV_Q4E = 28.11 * 1.09, 30.02 * 1.08
CORE_PBT_Q3E, CORE_PBT_Q4E = REV_Q3E * 0.21, REV_Q4E * 0.21
FX_LOSS_Q3E = 0.35            # 三季度人民币对美元即期升值约 1.18%，按约 30 亿元外币净敞口估
NONREC_Q3E, NONREC_Q4E = 0.22, 0.70   # 补助、委贷利息等（四季度补助集中）
BANK_INTEREST_AT = 0.12       # 银行存款利息（税后），含在核心利润里
FIN_ASSET_INTEREST_AT = 0.33  # 委托贷款 4.30 亿×约 7%、存单约 1.4 亿×2.5% 的税后利息

core_pbt_2026 = CORE_PBT['2026Q1'] + CORE_PBT['2026Q2'] + CORE_PBT_Q3E + CORE_PBT_Q4E
core_np_2026 = core_pbt_2026 * (1 - TAX)
OP_NP_BASE = round(core_np_2026 - BANK_INTEREST_AT, 1)       # 经营归母净利（不含任何利息）

# 分部毛利法交叉核对（2026E：轮胎装备 / 大型零部件 / 数控机床 / 其他）
SEG = {
    #        收入   熊GM   基GM   牛GM
    'tire': (68.7, 0.350, 0.375, 0.390),
    'parts': (41.1, 0.180, 0.205, 0.220),
    'cnc': (8.5, 0.330, 0.360, 0.370),
    'other': (2.4, 0.72, 0.72, 0.72),
}
SEG_REV_SHIFT = {'bear': {'tire': 0.90, 'parts': 1.0, 'cnc': 0.94, 'other': 0.92},
                 'base': {'tire': 1.0, 'parts': 1.0, 'cnc': 1.0, 'other': 1.0},
                 'bull': {'tire': 1.012, 'parts': 1.022, 'cnc': 1.06, 'other': 1.0}}
OPEX_RATE = {'bear': 0.105, 'base': 0.102, 'bull': 0.100}   # 税金附加+销售+管理+研发
CREDIT_LOSS = {'bear': 0.45, 'base': 0.40, 'bull': 0.40}
NET_BANK_INT_PT = 0.14


def segment_np(case):
    idx = {'bear': 1, 'base': 2, 'bull': 3}[case]
    rev = gp = 0.0
    for k, v in SEG.items():
        r = v[0] * SEG_REV_SHIFT[case][k]
        rev += r
        gp += r * v[idx]
    ebit = gp - rev * OPEX_RATE[case] - CREDIT_LOSS[case]
    tax = TAX if case != 'bull' else 0.12
    np_ = (ebit + NET_BANK_INT_PT) * (1 - tax)
    return rev, gp, ebit, np_


# ---------------------------------------------------------------- 3. 情景
# op_np: 2026 正常化经营归母净利（不含利息）；g5: 2027-2031 归母净利增速；
# 之后 2032-2036 线性收敛到 gT；ron: 显性期增量回报；ronT: 终值期增量回报。
SCEN = {
    'bear': dict(p=0.25, op_np=18.3, g5=[0.02, 0.03, 0.04, 0.04, 0.03], gT=0.020, ron=0.10, ronT=0.10),
    'base': dict(p=0.50, op_np=OP_NP_BASE, g5=[0.065, 0.075, 0.075, 0.07, 0.06], gT=0.025, ron=0.18, ronT=0.15),
    'bull': dict(p=0.25, op_np=25.4, g5=[0.11, 0.12, 0.11, 0.10, 0.09], gT=0.025, ron=0.22, ronT=0.18),
}
FADE_YEARS = 5
T_STUB = 0.1     # 2026H2 所有者收益：中报后已累积，按 0.1 年折现
# 2026 年再投资按实际资本开支计划：资本开支约 12 亿 − 折旧摊销约 4.5 亿 + 营运资本约 5.9 亿 ≈ 13.4 亿，约归母 55%
STUB_REINVEST = 0.55
T_FIRST = 0.7    # 2027 年中点距估值日（2026-10-19）约 0.7 年


def growth_path(g5, gT, fade=FADE_YEARS):
    gs = list(g5)
    last = g5[-1]
    for i in range(1, fade + 1):
        gs.append(last + (gT - last) * i / fade)
    return gs


def dcf(op_np, g5, gT, ron, ronT, r, cash=None, nonop=None, shares=SHARES, detail=False):
    """所有者收益 = 归母净利 ×（1 − 下一年增速/增量回报）。返回每股价值。"""
    cash = NET_CASH_ADJ if cash is None else cash
    nonop = NON_OP if nonop is None else nonop
    gs = growth_path(g5, gT)
    pv = 0.5 * op_np * (1 - STUB_REINVEST) / (1 + r) ** T_STUB
    npv = op_np
    rows = []
    for i, g in enumerate(gs):
        npv *= 1 + g
        last = i + 1 == len(gs)
        g_next = gT if last else gs[i + 1]
        rr = ronT if last else ron
        reinv = g_next / rr
        oe = npv * (1 - reinv)
        t = T_FIRST + i
        pv += oe / (1 + r) ** t
        rows.append((2027 + i, g, npv, reinv, oe))
    np_t = npv * (1 + gT)
    oe_t = np_t * (1 - gT / ronT)
    tv = oe_t / (r - gT)
    tv_pv = tv / (1 + r) ** (T_FIRST + len(gs) - 1)
    equity = pv + tv_pv + cash + nonop
    v = equity / shares
    if detail:
        return v, dict(pv_explicit=pv, tv_pv=tv_pv, equity=equity, rows=rows, tv_share=tv_pv / (pv + tv_pv))
    return v


def scen_values(r, scen=SCEN, **kw):
    return {k: dcf(s['op_np'], s['g5'], s['gT'], s['ron'], s['ronT'], r, **kw) for k, s in scen.items()}


def weighted(vals, probs):
    return sum(vals[k] * probs[k] for k in vals)


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
    probs = {k: s['p'] for k, s in SCEN.items()}
    print('== 1. 经调整净现金（2026-06-30，亿元）')
    print(f'  现金类合计 {cash_like:.2f} = 货币资金 {CASH:.2f} − 受限 {RESTRICTED:.2f} + 委托贷款 {ENTRUSTED_LOANS:.2f}'
          f' + 定期存单 {TIME_DEPOSIT:.2f} + 大额存单 {LARGE_CD:.2f}')
    print(f'  − 经营备付 {OPERATING_RESERVE:.2f} − 有息负债 {DEBT:.2f} − 工会经费等累积计提 {UNION_FUND:.2f}'
          f' = 经调整净现金 {NET_CASH_ADJ:.2f}；非经营资产 {NON_OP:.2f}')
    print(f'  每股：净现金 {NET_CASH_ADJ / SHARES:.2f} 元，非经营资产 {NON_OP / SHARES:.2f} 元；'
          f'若不把工会经费计为类债务，V 每股 +{UNION_FUND / SHARES:.2f} 元')

    print('\n== 2. 2026 正常化')
    print(f'  2026E 营收 {REV["2026Q1"] + REV["2026Q2"] + REV_Q3E + REV_Q4E:.1f}；'
          f'Q3E 营收 {REV_Q3E:.1f}、核心税前 {CORE_PBT_Q3E:.2f}、汇兑损失 {FX_LOSS_Q3E:.2f}、'
          f'归母净利约 {(CORE_PBT_Q3E - FX_LOSS_Q3E + NONREC_Q3E) * (1 - 0.115):.2f}')
    print(f'  2026E 核心税前 {core_pbt_2026:.2f} → 核心归母 {core_np_2026:.2f}；经营归母（不含利息）基准 {OP_NP_BASE:.1f}')
    for c in ('bear', 'base', 'bull'):
        rev, gp, ebit, np_ = segment_np(c)
        print(f'  分部毛利法 {c}: 营收 {rev:.1f} 毛利 {gp:.2f}（{gp / rev:.1%}） EBIT {ebit:.2f} 归母 {np_:.2f}')
    norm = {k: SCEN[k]['op_np'] + FIN_ASSET_INTEREST_AT + BANK_INTEREST_AT for k in SCEN}
    print('  2026 正常化归母净利（含净利息）：' + '，'.join(f'{k} {v:.1f}' for k, v in norm.items()))

    print('\n== 3. 三情景（股权成本 9%）')
    for k, s in SCEN.items():
        v, d = dcf(s['op_np'], s['g5'], s['gT'], s['ron'], s['ronT'], COE, detail=True)
        print(f'  {k}: V = {v:.2f} 元（p={s["p"]:.2f}），显性期现值 {d["pv_explicit"]:.1f}，终值现值 {d["tv_pv"]:.1f}，'
              f'终值占比 {d["tv_share"]:.0%}')
        print('     年份  增速   归母净利  再投资率  所有者收益')
        for y, g, n, re_, oe in d['rows'][:5]:
            print(f'     {y}  {g:5.1%}  {n:7.2f}  {re_:6.1%}  {oe:7.2f}')
        print(f'     2032-2036 增速线性收敛至 {s["gT"]:.1%}；终值增量回报 {s["ronT"]:.0%}，'
              f'终值再投资率 {s["gT"] / s["ronT"]:.1%}')
    vals9 = scen_values(COE)
    vw = weighted(vals9, probs)
    pv_ratio = PRICE / vw
    print(f'  加权 V = {vw:.2f} 元；P/V = {pv_ratio:.3f} → {verdict(pv_ratio)}')

    print('\n== 4. 股权成本敏感性')
    out = {}
    for r in (0.08, 0.09, 0.10):
        vs = scen_values(r)
        out[r] = weighted(vs, probs)
        print(f'  r={r:.0%}: 熊 {vs["bear"]:.2f} 基 {vs["base"]:.2f} 牛 {vs["bull"]:.2f} → 加权 {out[r]:.2f}，'
              f'P/V {PRICE / out[r]:.3f}')

    b = SCEN['base']
    irr = solve(lambda r: dcf(b['op_np'], b['g5'], b['gT'], b['ron'], b['ronT'], r), 0.05, 0.20, PRICE)
    irr_w = solve(lambda r: weighted(scen_values(r), probs), 0.05, 0.20, PRICE)
    print(f'\n== 5. 现价隐含回报：基准情景 {irr:.2%}；按三情景概率加权 {irr_w:.2%}')

    g10 = solve(lambda g: dcf(b['op_np'], [g] * 5, b['gT'], b['ron'], b['ronT'], COE, ), 0.0, 0.25, PRICE)
    # 上式后 5 年由 g 线性收敛至 2.5%；另算 10 年恒定增速
    def v_const10(g):
        sc = dict(op_np=b['op_np'], g5=[g] * 5, gT=b['gT'], ron=b['ron'], ronT=b['ronT'])
        gs = [g] * 10
        pv = 0.5 * sc['op_np'] * (1 - STUB_REINVEST) / (1 + COE) ** T_STUB
        n = sc['op_np']
        for i, gg in enumerate(gs):
            n *= 1 + gg
            last = i == 9
            oe = n * (1 - (sc['gT'] / sc['ronT'] if last else gg / sc['ron']))
            pv += oe / (1 + COE) ** (T_FIRST + i)
        tv = n * (1 + sc['gT']) * (1 - sc['gT'] / sc['ronT']) / (COE - sc['gT'])
        pv += tv / (1 + COE) ** (T_FIRST + 9)
        return (pv + NET_CASH_ADJ + NON_OP) / SHARES
    g_const = solve(v_const10, 0.0, 0.30, PRICE)
    np27 = b['op_np'] * 1.065
    g_perp = solve(lambda g: (np27 * (1 - g / b['ron']) / (COE - g) + NET_CASH_ADJ + NON_OP) / SHARES,
                   0.0, 0.085, PRICE)
    print(f'== 6. 反向 DCF（9%，基准 2026 经营归母 {b["op_np"]:.1f}、增量回报 18%）：')
    print(f'  2027-2036 恒定增速 {g_const:.1%} 后接 2.5% 终值；或 2027-2031 恒定 {g10:.1%} 后五年收敛至 2.5%；'
          f'或永续增速 {g_perp:.1%}（以 2027 归母 {np27:.1f} 起）')

    print('\n== 7. 交叉验证')
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NON_OP
    ebit_norm = core_pbt_2026 - BANK_INTEREST_AT / (1 - TAX)
    print(f'  市值 {mcap:.1f}；EV {ev:.1f}；EV/正常化 EBIT {ev / ebit_norm:.1f}×；'
          f'PE（TTM 23.30）{mcap / 23.30:.1f}×；PE（2026 正常化含息 {norm["base"]:.1f}）{mcap / norm["base"]:.1f}×')
    print(f'  股息率（2025 年度 8.0 亿元 / 市值）{8.0 / mcap:.2%}；回购 0')
    seg_np = {'tire': 16.3, 'parts': 3.6, 'cnc': 1.6, 'other': 1.3}
    seg_pe = {'tire': 17.0, 'parts': 12.0, 'cnc': 25.0, 'other': 10.0}
    sotp = sum(seg_np[k] * seg_pe[k] for k in seg_np) + NET_CASH_ADJ + NON_OP
    print(f'  分部加总（轮胎装备 16.3×17、零部件 3.6×12、机床 1.6×25、其他 1.3×10）= {sotp:.1f} 亿，{sotp / SHARES:.2f} 元')
    pe_lo, pe_mid, pe_hi = 14.8, 21.0, 28.2
    print(f'  历史年末 PE {pe_lo}～{pe_hi}×（中位约 {pe_mid}×）乘 2026 正常化含息归母 {norm["base"]:.1f}：'
          f'{pe_lo * norm["base"] / SHARES:.2f}／{pe_mid * norm["base"] / SHARES:.2f}／{pe_hi * norm["base"] / SHARES:.2f} 元'
          f'（历史区间含 2015、2020、2025 年题材估值，且当时增速高于本文基准）')
    print(f'  回购专户：2025-11-28 已全部过户给员工持股计划，剔除口径与总股本口径相同，V {vw:.2f} 元')

    print('\n== 8. 证伪条件触发后的独立 V（9%）')
    def scen_mod(**mods):
        sc = {k: dict(v) for k, v in SCEN.items()}
        for key, val in mods.items():
            case, field = key.split('__')
            sc[case][field] = val
        return sc
    tilt_bear = {'bear': 0.40, 'base': 0.45, 'bull': 0.15}
    # F1 三季报：基准经营归母降到 22.0，权重向熊市倾斜
    v_f1 = weighted(scen_values(COE, scen=scen_mod(base__op_np=22.0)), tilt_bear)
    # F2 2026 年报：基准经营归母 21.5、牛市 24.0，权重向熊市倾斜
    f2 = scen_mod(base__op_np=21.5, bull__op_np=24.0)
    v_f2 = weighted(scen_values(COE, scen=f2), tilt_bear)
    # F3 模具资本开支周期转向：熊市权重 50%
    v_f3 = weighted(scen_values(COE), {'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    # F4 关联交易、委贷与现金质量：权重向熊市倾斜，增量回报下调，委托贷款折价 30%
    f4 = scen_mod(base__ron=0.15, base__ronT=0.13, bull__ron=0.18, bull__ronT=0.15)
    v_f4 = weighted(scen_values(COE, scen=f4, cash=NET_CASH_ADJ - ENTRUSTED_LOANS * 0.3), tilt_bear)
    # U1 上行证伪：基准经营归母上调到 24.5，权重向牛市倾斜
    v_u1 = weighted(scen_values(COE, scen=scen_mod(base__op_np=24.5)), {'bear': 0.15, 'base': 0.50, 'bull': 0.35})
    print(f'  F1 2026Q3 扣非 <5.0 亿且单季毛利率 <30.5%：{v_f1:.2f}')
    print(f'  F2 2026 年扣非 <21.5 亿，或模具毛利率 <35.5%：{v_f2:.2f}')
    print(f'  F3 2027H1 汽车轮胎装备收入 ≤34.89 亿（同比不增）：{v_f3:.2f}')
    print(f'  F4 2026 年关联销售占营收 >20%，或年末应收豪迈国际贸易 >3.5 亿，或委贷逾期，或经营现金流 <8 亿：{v_f4:.2f}')
    print(f'  U1 2027H1 扣非同比 >15% 且毛利率 ≥34%：{v_u1:.2f}（P/V {PRICE / v_u1:.3f}）')

    print('\n== 汇总')
    print(f'  熊 {vals9["bear"]:.2f} / 基 {vals9["base"]:.2f} / 牛 {vals9["bull"]:.2f}；加权 {vw:.2f}；P/V {pv_ratio:.3f}；'
          f'8% {out[0.08]:.2f}；10% {out[0.10]:.2f}；隐含回报（基准）{irr:.2%}')
    for tag, thr in (('明显低估', 0.75), ('温和低估', 0.90), ('大致合理上沿', 1.10)):
        print(f'  V 不变时 {tag} 价格 ≤ {vw * thr:.2f} 元')


if __name__ == '__main__':
    main()
