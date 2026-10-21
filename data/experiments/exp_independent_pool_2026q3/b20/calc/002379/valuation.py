#!/usr/bin/env python3
"""002379 宏桥控股 独立估值（OI-291 b20，价格日 2026-10-21）。

运行：python3 valuation.py
单位：金额亿元，价格元/吨（沪铝、氧化铝含税；成本不含税），每股元。
口径：所有者收益 DCF（归母，100% 持股），经调整净现金为负 → 有杠杆口径为主，无杠杆口径对照。
来源页码见正文 companies/002379_宏桥控股.md。
"""

PRICE = 14.14
SHARES = 130.3112          # 亿股，总股本（无回购专户股份）
COE = 0.09
G = 0.015                  # 名义增长与终值增长（价格与成本同步通胀，量不增）
TAX = 0.225

# ---------------- 资产负债（2026-06-30，2026H1_report 第 61-63、97、106、118-122、132 页） ----------------
CASH = 118.12
RESTRICTED = 20.00         # 保证金 19.997 + 冻结 0.004
TFA = 14.06                # 交易性金融资产（理财产品及其他）
REV_TTM = 1659.55
OP_RESERVE = 0.02 * REV_TTM  # 经营备付：TTM 营收 2%
ST_LOAN = 18.18
LT_LOAN_CUR = 47.09        # 一年内到期的长期借款
LT_LOAN = 116.33
RP_LOAN = 2.91             # 关联方借款（其他应付款内，筹资活动负债表）
TRANSITION_PAYABLE = 69.16  # 其他应付款-过渡期损益（应付魏桥铝电等原交易对方）
LEASE = 3.32               # 租赁负债（含一年内到期），只列示不扣
NON_OP = 1.57 + 2.88       # 其他权益工具投资（创新新材股票）+ 长期股权投资

cash_like = CASH - RESTRICTED + TFA - OP_RESERVE
debt_like = ST_LOAN + LT_LOAN_CUR + LT_LOAN + RP_LOAN + TRANSITION_PAYABLE
ND = debt_like - cash_like                 # 经调整净负债（无杠杆口径）
NET_CASH_ADJ = -ND
RD = 0.040                                 # 有息负债实际平均利率：H1 利息 4.57×2 ÷ 平均有息负债 226.1 ≈ 4.0%

# ---------------- 经营模型（校准见正文第 2 节） ----------------
VOL = 655.0        # 万吨铝产品（电解铝含合金锭、再生铝 + 深加工），2025 年 658.8
REAL = 0.89        # 不含税实现价 / 沪铝含税均价
AO_NET = 750.0     # 万吨，氧化铝净多头（产量 2,014 − 自用约 1,258）
C_AO = 2450.0      # 氧化铝自产单位成本（不含税）
IMP = 3.0          # 常态减值（亿元/年）
VOL_Q = VOL / 4


def ebit(p_al, p_ao, c_al, vol=VOL, imp=IMP):
    """全口径 EBIT（亿元）：铝产品价差 + 氧化铝净外销价差 − 常态减值。c_al 含期间费用、按自产成本计氧化铝。"""
    return vol * (REAL * p_al - c_al) / 1e4 + AO_NET * (p_ao / 1.13 - C_AO) / 1e4 - imp


# 校准（隐含全口径单位成本，自产氧化铝口径）
CAL = {
    '2024': dict(shfe=19996, ebit_pre_imp=271.6, ao_gp=81.3, ao_mkt=3609, vol=655.0),
    '2025': dict(shfe=20695, ebit_pre_imp=275.2, ao_gp=36.7, ao_mkt=2851, vol=658.8),
    '2026H1': dict(shfe=24169, ebit_pre_imp=415.9, ao_gp=3.2, ao_mkt=2500, vol=655.0),
}
K_YN = 0.55   # 云南外购氧化铝（吨/吨铝），把外购按市价的部分折回自产成本口径


def implied_cost(c):
    per_t = (c['ebit_pre_imp'] - c['ao_gp']) / c['vol'] * 1e4
    c_obs = REAL * c['shfe'] - per_t
    return c_obs - K_YN * (c['ao_mkt'] - C_AO)


# 现时与情景假设
SPOT_AL = 23050      # 沪铝主连 2026-10-21
FWD_AL_2027 = 22385  # 沪铝 2709 合约 2026-10-21 收盘
Q3_AL = 23631        # 2026Q3 沪铝主连月均（(开+收)/2）均值
SPOT_AO = 2680       # 氧化铝现货（2026-09 约 2,670-2,690）
C_Q3 = 15350         # 2026Q3 全口径单位成本（H1 隐含 15,182 + 煤价上行，约 3.2 元/吨铝 每 1 元/吨煤）
C_Q4 = 15700         # 2026Q4（秦港 5500 大卡 1,003 元/吨，山东关联电价公式联动）
H2_CAPEX_EXCESS = 28.0   # 2026H2 资本开支超出折旧部分（全年指引约 90，H1 现金 20.8）

SCEN = {
    #        概率   沪铝    氧化铝  全口径成本  关联收购损失
    'bear': dict(p=0.25, al=18000, ao=2600, c=14800, solar=-20.0),
    'base': dict(p=0.50, al=20500, ao=2900, c=15050, solar=-10.0),
    'bull': dict(p=0.25, al=23000, ao=3300, c=15400, solar=-3.0),
}

IC = 673.0                 # 投入资本（固定资产+在建+无形+使用权+设备预付+经营营运资本）
RELOC_CAPEX = {2027: 40.0, 2028: 24.0}   # 云南搬迁超出折旧的资本开支
RELOC_SAVING_2029 = 10.0   # 2029 起税后节省（2029 年币值），随通胀增长

# 定增（2026-09-08 股东会通过，待深交所审核、证监会注册）
SPO_PROB = 0.70
SPO_GROSS = 120.0
SPO_NET = 119.0
SPO_PRICE = 12.0           # 约现价 85%（底价为发行期首日前 20 日均价 80%）
SPO_NPV = -15.0            # 风光 79 + 深加工 23 亿投资的 NPV（回报低于 9%）

T_H2 = 0.10                # 2026H2 所有者收益折现年限
YEARS = [2027, 2028, 2029, 2030, 2031]


def scenario_flows(s):
    """返回 (2026H2 所有者收益, {年份: (NOPAT, OE)})，年份含 2027-2032。"""
    # 2026H2：实际价格（Q3 均价、Q4 现价）与现时成本
    e_q3 = VOL_Q * (REAL * Q3_AL - C_Q3) / 1e4 + AO_NET / 4 * (SPOT_AO / 1.13 - C_AO) / 1e4 - 1.5
    e_q4 = VOL_Q * (REAL * SPOT_AL - C_Q4) / 1e4 + AO_NET / 4 * (SPOT_AO / 1.13 - C_AO) / 1e4 - 1.5
    nopat_h2 = (e_q3 + e_q4) * (1 - TAX)
    oe_h2 = nopat_h2 - H2_CAPEX_EXCESS - G * IC / 2
    flows = {}
    ic = IC
    for y in YEARS + [2032]:
        infl = (1 + G) ** (y - 2027)
        if y == 2027:   # 一年过渡：价格与成本各取现时与情景常态的中点
            al = 0.5 * FWD_AL_2027 + 0.5 * s['al']
            ao = 0.5 * SPOT_AO + 0.5 * s['ao']
            c = 0.5 * C_Q4 + 0.5 * s['c']
            nopat = ebit(al, ao, c) * (1 - TAX)
        else:
            nopat = ebit(s['al'], s['ao'], s['c']) * (1 - TAX) * infl
        if y >= 2029:
            nopat += RELOC_SAVING_2029 * (1 + G) ** (y - 2029)
        reinv = G * ic
        reloc = RELOC_CAPEX.get(y, 0.0)
        oe = nopat - reinv - reloc
        ic = ic + reinv + reloc
        flows[y] = (nopat, oe)
    return oe_h2, flows


def v_ops(s, r=COE, g=G):
    oe_h2, flows = scenario_flows(s)
    pv = oe_h2 / (1 + r) ** T_H2
    for y in YEARS:
        t = y - 2026.30            # 年中折现：2027 → 0.70 年
        pv += flows[y][1] / (1 + r) ** t
    tv = flows[2032][1] / (r - g)
    pv_tv = tv / (1 + r) ** (2031.5 - 2026.80)
    return pv + pv_tv, pv_tv


def spo_adjust(v_pre_ps):
    """定增对每股价值的期望影响（元/股）。"""
    new_sh = SPO_GROSS / SPO_PRICE
    v_post = (v_pre_ps * SHARES + SPO_NET + SPO_NPV) / (SHARES + new_sh)
    return SPO_PROB * (v_post - v_pre_ps)


def v_per_share(s, r=COE, levered=True, with_spo=True):
    ops, _ = v_ops(s, r)
    debt_charge = ND * RD * (1 - TAX) / r if levered else ND
    eq = ops - debt_charge + NON_OP + s['solar']
    v = eq / SHARES
    if with_spo:
        v += spo_adjust(v)
    return v


def weighted(r=COE, levered=True, with_spo=True):
    return sum(SCEN[k]['p'] * v_per_share(SCEN[k], r, levered, with_spo) for k in SCEN)


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


def main():
    print('=== 校准：隐含全口径单位成本（自产氧化铝口径，元/吨） ===')
    for k, c in CAL.items():
        print(f'  {k}: {implied_cost(c):,.0f}')
    print('\n=== 经调整净现金（2026-06-30，亿元） ===')
    print(f'  现金类 {cash_like:.2f} = 货币资金 {CASH} − 受限 {RESTRICTED} + 理财 {TFA} − 经营备付 {OP_RESERVE:.2f}')
    print(f'  类债务 {debt_like:.2f} = 短借 {ST_LOAN} + 一年内到期长借 {LT_LOAN_CUR} + 长借 {LT_LOAN} '
          f'+ 关联方借款 {RP_LOAN} + 过渡期损益应付 {TRANSITION_PAYABLE}')
    print(f'  net_cash_adj = {NET_CASH_ADJ:.2f}；租赁负债 {LEASE} 只列示；非经营资产 {NON_OP:.2f}')
    print(f'  有杠杆口径扣减 = 净负债 × {RD:.1%} × (1−{TAX:.1%}) ÷ 9% = {ND * RD * (1 - TAX) / COE:.2f}')

    print('\n=== 情景常态 EBIT / NOPAT（2027 年币值）与 2026 正常化归母净利 ===')
    net_int_at = ND * RD * (1 - TAX)
    norm_np = {}
    for k, s in SCEN.items():
        e = ebit(s['al'], s['ao'], s['c'])
        nopat = e * (1 - TAX)
        np26 = nopat / (1 + G) - net_int_at
        norm_np[k] = np26
        print(f'  {k}: 沪铝 {s["al"]:,} 氧化铝 {s["ao"]:,} 成本 {s["c"]:,} → EBIT {e:.1f}  NOPAT {nopat:.1f}  '
              f'2026 正常化归母净利 {np26:.1f}')
    print(f'  税后净利息（按经调整净负债滚动）{net_int_at:.1f}')

    oe_h2, fb = scenario_flows(SCEN['base'])
    e_q3 = VOL_Q * (REAL * Q3_AL - C_Q3) / 1e4 + AO_NET / 4 * (SPOT_AO / 1.13 - C_AO) / 1e4 - 1.5
    e_q4 = VOL_Q * (REAL * SPOT_AL - C_Q4) / 1e4 + AO_NET / 4 * (SPOT_AO / 1.13 - C_AO) / 1e4 - 1.5
    q_int = 1.8
    np_q3 = (e_q3 - q_int) * (1 - 0.216)
    np_q4 = (e_q4 - q_int) * (1 - 0.216)
    print('\n=== 2026 下半年（实际价格） ===')
    print(f'  Q3 EBIT {e_q3:.1f} → 归母净利约 {np_q3:.1f}；Q4 EBIT {e_q4:.1f} → 归母净利约 {np_q4:.1f}')
    print(f'  2026E 归母净利约 {156.45 + np_q3 + np_q4:.1f}；2026H2 所有者收益 {oe_h2:.1f}')
    spot_ebit = ebit(SPOT_AL, SPOT_AO, C_Q4)
    print(f'  现价现时成本年化 EBIT {spot_ebit:.1f}，NOPAT {spot_ebit * (1 - TAX):.1f}')

    print('\n=== 基准情景逐年（亿元） ===')
    prev = None
    growth = []
    for y in YEARS + [2032]:
        nopat, oe = fb[y]
        gr = '' if prev is None else f'{oe / prev - 1:+.1%}'
        if prev is not None and y <= 2031:
            growth.append(oe / prev - 1)
        print(f'  {y}: NOPAT {nopat:.1f}  OE {oe:.1f}  {gr}')
        prev = oe
    nopat26 = ebit(SCEN['base']['al'], SCEN['base']['ao'], SCEN['base']['c']) * (1 - TAX) / (1 + G)
    oe26 = nopat26 - G * IC
    gpath = [fb[2027][1] / oe26 - 1] + growth
    print(f'  2026 常态 OE（基准，2026 币值）{oe26:.1f}；JSON 增长路径 2027-2031：{[round(x, 3) for x in gpath]}')
    reinv_rate = G * IC / fb[2028][0]
    print(f'  稳态再投资率 {reinv_rate:.1%}（g×IC÷NOPAT），常态 ROIC {fb[2028][0] / IC:.1%}，'
          f'搬迁增量回报 {RELOC_SAVING_2029 / (sum(RELOC_CAPEX.values()) + H2_CAPEX_EXCESS):.1%}')
    print(f'  2028→2031 OE 增速：{", ".join(f"{x:.1%}" for x in growth)}')

    print('\n=== 各情景 2027 过渡年假设与 2027-2032 所有者收益（亿元） ===')
    for k, s_ in SCEN.items():
        _, fl = scenario_flows(s_)
        al27 = 0.5 * FWD_AL_2027 + 0.5 * s_['al']
        ao27 = 0.5 * SPOT_AO + 0.5 * s_['ao']
        c27 = 0.5 * C_Q4 + 0.5 * s_['c']
        print(f'  {k}: 2027 沪铝 {al27:,.0f} 氧化铝 {ao27:,.0f} 成本 {c27:,.0f}；OE ' +
              ' / '.join(f'{y}:{fl[y][1]:.0f}' for y in YEARS + [2032]))

    print('\n=== 三情景每股价值（有杠杆口径，含关联收购与定增期望影响） ===')
    res = {}
    for k, s in SCEN.items():
        ops, pv_tv = v_ops(s)
        v = v_per_share(s)
        v_unlev = v_per_share(s, levered=False)
        v_nospo = v_per_share(s, with_spo=False)
        res[k] = v
        print(f'  {k} (p={s["p"]:.2f}): 经营现值 {ops:.0f}（终值占 {pv_tv / ops:.0%}） V={v:.2f}  '
              f'无杠杆 {v_unlev:.2f}  不计定增 {v_nospo:.2f}  定增影响 {spo_adjust(v_nospo):+.2f}')
    vw = weighted()
    vw_unlev = weighted(levered=False)
    print(f'\n  加权 V（有杠杆）= {vw:.2f}，P/V = {PRICE / vw:.3f}')
    print(f'  加权 V（无杠杆）= {vw_unlev:.2f}，P/V = {PRICE / vw_unlev:.3f}')
    alt = 0.30 * res['bear'] + 0.50 * res['base'] + 0.20 * res['bull']
    print(f'  概率改为 30/50/20 时加权 V = {alt:.2f}，P/V = {PRICE / alt:.3f}')
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'  股权成本 8%：{v8:.2f}；10%：{v10:.2f}')
    for lab, thr in [('明显低估上限 0.75', 0.75), ('温和低估上限 0.90', 0.90), ('大致合理上限 1.10', 1.10)]:
        print(f'  V 不变时 P/V={thr} 对应价格 {vw * thr:.2f}（{lab}）')

    irr = solve(lambda r: v_per_share(SCEN['base'], r), 0.06, 0.25, PRICE)
    print(f'\n  现价隐含回报（基准情景，有杠杆）= {irr:.2%}')
    irr_u = solve(lambda r: v_per_share(SCEN['base'], r, levered=False), 0.06, 0.25, PRICE)
    print(f'  现价隐含回报（基准情景，无杠杆）= {irr_u:.2%}')

    # 反向 DCF：现价隐含的常态沪铝价（其余同基准）
    def v_at_al(al):
        s = dict(SCEN['base'])
        s['al'] = al
        return v_per_share(s)
    al_imp = solve(v_at_al, 15000, 26000, PRICE)
    print(f'  反向 DCF：现价隐含 2028 年起常态沪铝 {al_imp:,.0f} 元/吨（基准成本 {SCEN["base"]["c"]:,}，氧化铝 2,900）')

    def v_at_g(g):
        ops, _ = v_ops(SCEN['base'], COE, g)
        eq = ops - ND * RD * (1 - TAX) / COE + NON_OP + SCEN['base']['solar']
        return eq / SHARES
    g_imp = solve(v_at_g, -0.08, 0.06, PRICE)
    print(f'  反向 DCF：基准常态利润下现价隐含永续增速 {g_imp:.2%}（不计定增）')

    # 证伪情景
    print('\n=== 证伪触发后的独立 V（有杠杆，加权或指定情景） ===')
    # 1) 常态铝价下移：三情景各降 1,500
    def shifted(dal=0.0, dc=0.0, solar_extra=0.0):
        tot = 0.0
        for k, s in SCEN.items():
            s2 = dict(s)
            s2['al'] = s['al'] + dal
            s2['c'] = s['c'] + dc
            s2['solar'] = s['solar'] + solar_extra
            tot += s['p'] * v_per_share(s2)
        return tot
    print(f'  F1 常态沪铝三情景各 −1,500：{shifted(dal=-1500):.2f}')
    print(f'  F2 煤价常态上移（成本 +700）：{shifted(dc=700):.2f}')
    print(f'  F3 三季报显示成本高于假设（常态成本 +500）：{shifted(dc=500):.2f}')
    print(f'  F4 再发生 50 亿级关联收购、价值损失 30 亿：{shifted(solar_extra=-30):.2f}')
    print(f'  F1+F2 铝价 −1,500 且成本 +700：{shifted(dal=-1500, dc=700):.2f}')
    print('  敏感性（常态沪铝三情景同向平移）：' + '；'.join(f'{d:+d} → {shifted(dal=d):.2f}' for d in (-1000, -500, 500, 1000)))
    print(f'  仅熊市情景 V：{res["bear"]:.2f}')

    # 交叉验证
    print('\n=== 交叉验证 ===')
    mcap = PRICE * SHARES
    ev = mcap + ND
    print(f'  市值 {mcap:.1f}；经调整 EV {ev:.1f}；EV/常态 EBIT(基准) {ev / ebit(20500, 2900, 15050):.1f}x；'
          f'EV/现时年化 EBIT {ev / spot_ebit:.1f}x')
    hk_mcap_hkd = 1857.83
    hkdcny = 0.8686
    hk_rmb = hk_mcap_hkd * hkdcny
    stake = 0.8899
    print(f'  中国宏桥市值 {hk_mcap_hkd} 亿港元 ≈ {hk_rmb:.0f} 亿元；其 88.99% 宏桥控股按 A 股价 {stake * mcap:.0f} 亿元；'
          f'按加权 V {stake * vw * SHARES:.0f} 亿元')
    for other in (0.0, 200.0):
        print(f'  若中国宏桥其余资产净值 {other:.0f} 亿：港股隐含宏桥控股每股 {(hk_rmb - other) / stake / SHARES:.2f} 元')

    print('\n=== JSON 关键数 ===')
    print({k: round(v, 2) for k, v in res.items()}, round(vw, 2), round(PRICE / vw, 3),
          round(v8, 2), round(v10, 2), round(irr, 4))
    print({k: round(v, 1) for k, v in norm_np.items()}, round(NET_CASH_ADJ, 2), round(NON_OP, 2))


if __name__ == '__main__':
    main()
