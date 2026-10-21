#!/usr/bin/env python3
"""天齐锂业（002466）独立估值 —— OI-291 池内独立审计 b21（深度版）。

运行：python3 valuation.py
打印：价格假设、Q3 拆分、经调整净现金（归母口径与合并口径）、三情景 V（可转债逐情景取低）、
加权 V、P/V 与分档、8%/10% 股权成本下的 V、现价隐含回报、反向 DCF、SQM 按市值的分部对照、
H 股对照、2026 正常化归母净利三档、证伪触发后的 V。

单位：金额 亿元人民币；Talison 单价 美元/吨 SC6；碳酸锂价格 万元/吨（SMM 电池级、含 13% 增值税）；
SQM 利润 十亿美元；每股价值 元/股。
资料：2026H1_report、2025_annual_report、forecast_20261021_723554、financing_2026020x、
IR_2026xxxx；网络事实见报告「来源」节（IGO 2026-07-28 季报、SQM 2Q26、腾讯行情 10-21 等）。
"""

import math

# ---------------------------------------------------------------- 快照与股本
PRICE = 36.15                 # A 股收盘 2026-10-21
SHARES = 17.13105208          # 亿股：A 14.76959670 + H 2.36145538（8-21 注销 113,113 股后）
SHARES_BS = 17.13218321       # 2026-06-30 资产负债表股本
H_SHARES = 2.36145538
H_PRICE_HKD = 23.54           # 9696.HK 2026-10-21 收盘
HKDCNY = 0.8504               # 2026-10-21
FX_SPOT = 6.6758              # USD/CNY 2026-10-21
FX = 6.70                     # 估值用 USD/CNY
COE = 0.09

# 可转债（H 股可转债，2027-02-09 到期，零息，到期按本金赎回）
CB_FACE = 26.00 - 6973338 * 51.85 * 0.8878 / 1e8   # 已转股 6,973,338 股 → 未转股面值 22.79 亿
CB_CONV_PX_RMB = 51.85 * 0.8878                    # 固定汇率 0.8878 → 46.03 元/股
CB_CONV_SHARES = CB_FACE / CB_CONV_PX_RMB          # 0.4951 亿股

# ---------------------------------------------------------------- 资产负债表（2026-06-30）
cash_cons = 100.30 - 0.32 + 15.04 + 2.84   # 货币资金−受限 + 结构性存款/理财 + 大额存单（其他流动资产）
debt_cons = 8.6277 + 111.4321 + 15.8672 + 0.0864 + 0.1443 + 5.9901   # 短借+长借+一年内到期长借及利息+债券利息+科创债
lease_total = 8.6386 + 2.0133              # 租赁负债（只列示，不扣：所有者收益以净利润为起点）
wf_cash = 8.6048                           # 文菲尔德货币资金（现金流量表附注）
wf_debt = 93.3404                          # 文菲尔德银团贷款担保实际余额（子公司对子公司担保表）
TALISON = 0.2601                           # 51% × 51%
KWINANA = 0.51
SQM_STAKE = 0.219                          # 62,556,568 股 A 类 / 285,637,808
SQM_SHARES_TQ = 0.62556568                 # 亿股
OPER_RESERVE = 10.0                        # 经营备付（非文菲尔德部分约 1.4 个月现金成本）
ATO_EXPECTED = 2.0                         # 澳税务局反避税事项期望负担（潜在税款 1.7 亿澳元，IGO 分担 49%）
LT_EMPLOYEE = 0.30                         # 长期应付职工薪酬 0.60 的约一半
REHAB_ATTR = TALISON * 5.5483              # 预计负债（复垦为主）按 26.01%
FX_DERIV = 0.6064 - 0.0394                 # 衍生金融负债净额
SQM_DIV_REC = 4.67                         # 应收股利（SQM 已宣派）
OTHER_ASSOC = 259.81 - 254.08 - 5.00       # 其他联营/合营账面
OTHER_INV_FV = 24.42                       # 其他权益工具投资公允价值（smart 10.66、卫蓝 3.99、中创新航 4.12、厦钨新能 2.98、SES 1.45、能投发展 1.23）

net_cash_attr_raw = (cash_cons - wf_cash) - (debt_cons - wf_debt) + TALISON * (wf_cash - wf_debt)
NET_CASH_ADJ = net_cash_attr_raw - OPER_RESERVE - ATO_EXPECTED - LT_EMPLOYEE - REHAB_ATTR - FX_DERIV
net_cash_cons_adj = cash_cons - debt_cons - OPER_RESERVE - ATO_EXPECTED - 0.598 - 5.5483 - FX_DERIV

# ---------------------------------------------------------------- 价格链与经营参数
CONV_RATIO = 7.6       # 吨 SC6 / 吨 LCE
CONV_COST = 20.0       # 千元/吨 LCE：非一体化转化成本（含精矿内陆物流）
REAL_LC = 0.97         # 锂盐实现价 / SMM 现货（不含税）
K_TALISON = 0.90       # 泰利森实现价 / SC6 CIF 中国（股东折扣与运费）
ROYALTY = 0.05         # 西澳权益金
DISC_NET = 0.07        # 中国工厂从 TLEA 拿矿的净折扣（扣额外运费）
TQ_INEFF = 1.0         # 千元/吨：天齐自有转化相对市场边际转化的差
CAPEX_EXCESS_USD_T = 30.0   # 格林布什维持性资本开支超出折旧（美元/吨）
WF_INT_USD = 0.074     # 十亿美元/年：文菲尔德银团利息（约 13.9 亿美元 × 5.3%）

SC = {
    'bear': dict(p=0.25, lc=7.5, mk=2.0, v27=1.55, v28=1.60, c27=409.0, c28=405.0, c26=410.0,
                 g=0.015, roic_inc=0.20, china=8.5, kw27=-1.5, kw28=-0.5, hq=-2.8,
                 h2=1.4, sqm_cut=0.35, sqm_g=0.020, zabuye=3.0, other_inv=15.0, shield=2.3,
                 extra=-2.0, zab_np=0.2, kw26=-2.0, wc=10.0, cuola=0.0),
    'base': dict(p=0.50, lc=11.0, mk=3.0, v27=1.68, v28=1.78, c27=386.0, c28=373.0, c26=400.0,
                 g=0.020, roic_inc=0.25, china=9.5, kw27=-1.3, kw28=-0.8, hq=-3.0,
                 h2=7.8, sqm_cut=0.25, sqm_g=0.025, zabuye=5.0, other_inv=19.5, shield=4.0,
                 extra=0.0, zab_np=0.6, kw26=-1.3, wc=8.0, cuola=4.0),
    'bull': dict(p=0.25, lc=16.0, mk=4.0, v27=1.75, v28=1.95, c27=365.0, c28=357.0, c26=390.0,
                 g=0.025, roic_inc=0.30, china=10.0, kw27=-0.4, kw28=-0.4, hq=-3.2,
                 h2=15.2, sqm_cut=0.15, sqm_g=0.030, zabuye=8.0, other_inv=22.0, shield=6.9,
                 extra=1.0, zab_np=1.2, kw26=-0.4, wc=5.0, cuola=10.0),
}
T = [0.7, 1.7, 2.7, 3.7, 4.7]     # 2027–2031 年中距估值日（2026-10-21）的年数


def lc_exvat(lc_wan):
    """SMM 含税万元/吨 → 天齐实现价（不含税，千元/吨）。"""
    return REAL_LC * lc_wan * 10.0 / 1.13


def sc6_from_lc(lc_wan, mk):
    """按市场转化利润 mk（千元/吨）倒推 SC6 CIF（美元/吨）。"""
    return (lc_exvat(lc_wan) - mk - CONV_COST) * 1000.0 / (CONV_RATIO * FX)


def talison_np_t(sc6, c):
    """泰利森每吨税后利润（美元/吨，未扣利息）。"""
    return (K_TALISON * sc6 * (1 - ROYALTY) - c) * (1 - 0.30)


def conv_margin(lc_wan, mk):
    sc6 = sc6_from_lc(lc_wan, mk)
    return (mk - TQ_INEFF) + DISC_NET * sc6 * CONV_RATIO * FX / 1000.0   # 千元/吨，税前


def sqm_np(lc_wan, vol_adj=0.0):
    """SQM 归属股东净利（十亿美元，SQM 口径）；2027–2030 产量约 30 万吨。"""
    p = REAL_LC * lc_wan * 10.0 / 1.13 / FX     # 千美元/吨
    return 0.65 + 0.125 * (p - 8.6) + vol_adj


def own_cashflows(s, lc=None, coe=COE):
    """自有锂业务（归母、无杠杆）所有者收益路径与现值。"""
    lc = s['lc'] if lc is None else lc
    sc6 = sc6_from_lc(lc, s['mk'])
    conv = conv_margin(lc, s['mk']) * (1 - 0.25) * s['china'] / 10.0 - 0.5
    rows = []
    rr = s['g'] / s['roic_inc']          # 增长再投资占 NOPAT 比例（2027 起）
    # 2027、2028：量由 CGP3 爬坡带来（不需新增产能），维持性资本开支超折旧部分与增长再投资均扣除
    for v, c, kw in ((s['v27'], s['c27'], s['kw27']), (s['v28'], s['c28'], s['kw28'])):
        tal = TALISON * v * talison_np_t(sc6, c) * FX / 100.0
        cap = TALISON * CAPEX_EXCESS_USD_T * v * FX / 100.0
        nopat = tal + conv + 0.5 + kw + s['hq']
        maint = cap + 0.5
        oe = nopat - maint - rr * nopat
        rows.append((nopat, oe))
    # 2029–2031：名义增长 g
    nopat, oe = rows[-1]
    for _ in range(3):
        nopat = nopat * (1 + s['g'])
        maint = maint * (1 + s['g'])
        oe = nopat - maint - rr * nopat
        rows.append((nopat, oe))
    pv = sum(o / (1 + coe) ** t for (_, o), t in zip(rows, T))
    n5, _ = rows[-1]
    n6 = n5 * (1 + s['g'])
    oe6 = n6 - maint * (1 + s['g']) - rr * n6
    tv = oe6 / (coe - s['g'])
    pv_tv = tv / (1 + coe) ** T[-1]
    h2 = (s['h2'] + s['wc']) / (1 + coe) ** 0.25
    return dict(sc6=sc6, rows=rows, pv_years=pv, pv_tv=pv_tv, h2=h2, total=pv + pv_tv + h2, oe6=oe6, rr=rr, maint=maint)


def sqm_value(s, lc=None, coe=COE):
    """SQM 21.9% 股权（亿元）：2027–2030 第一阶段，2031 起 Codelco 控股后按 sqm_cut 折减。"""
    lc = s['lc'] if lc is None else lc
    np1 = sqm_np(lc)
    oe1 = 0.80 * np1
    pv1 = sum(oe1 / (1 + coe) ** t for t in T[:4])
    np2 = np1 * (1 - s['sqm_cut'])
    pv2 = 0.80 * np2 / (coe - s['sqm_g']) / (1 + coe) ** T[3]
    q4 = 0.80 * np1 / 4.0 / (1 + coe) ** 0.2
    usd_bn = pv1 + pv2 + q4
    return dict(np1=np1, np2=np2, value=SQM_STAKE * usd_bn * FX * 10.0)


def scenario_value(name, lc=None, coe=COE, sqm_override=None):
    s = SC[name]
    own = own_cashflows(s, lc, coe)
    sqm = sqm_value(s, lc, coe)
    sqm_v = sqm['value'] if sqm_override is None else sqm_override
    others = s['zabuye'] + s['other_inv'] + OTHER_ASSOC + SQM_DIV_REC + s['shield'] + s['cuola']   # 措拉锂矿（80%）按风险折算的期权价值
    eq_pre_cb = own['total'] + sqm_v + others + NET_CASH_ADJ + s['extra']
    v_debt = (eq_pre_cb - CB_FACE) / SHARES
    v_conv = eq_pre_cb / (SHARES + CB_CONV_SHARES)
    return dict(own=own, sqm=sqm, sqm_v=sqm_v, others=others, eq_pre_cb=eq_pre_cb,
                v_debt=v_debt, v_conv=v_conv, v=min(v_debt, v_conv))


def weighted(coe=COE, probs=None, sqm_market=False):
    probs = probs or {k: SC[k]['p'] for k in SC}
    tot = 0.0
    for k in SC:
        ov = SQM_MKT if sqm_market else None
        tot += probs[k] * scenario_value(k, coe=coe, sqm_override=ov)['v']
    return tot


def bisect(f, lo, hi, it=200):
    flo = f(lo)
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid)
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


def normalized_np_2026(name):
    """2026 年正常化归母净利（报表口径：含 SQM 购买价分摊摊销、净利息，剔除存货跌价/价差收益与汇兑等一次性）。"""
    s = SC[name]
    sc6 = sc6_from_lc(s['lc'], s['mk'])
    v26 = 1.56
    tal = TALISON * (v26 * talison_np_t(sc6, s['c26']) - WF_INT_USD * 1000 * (1 - 0.30)) * FX / 100.0
    conv = conv_margin(s['lc'], s['mk']) * (1 - 0.25) * 10.0 / 10.0
    net_int = -0.3
    p = REAL_LC * s['lc'] * 10.0 / 1.13 / FX
    sqm_2026 = 0.62 + 0.12 * (p - 8.6) - 0.19          # 2026 产量约 28 万吨；天齐口径扣 PPA 摊销约 1.9 亿美元
    sqm_inc = SQM_STAKE * sqm_2026 * FX * 10.0
    total = tal + conv + s['kw26'] + s['hq'] + net_int + sqm_inc + s['zab_np']
    return dict(talison=tal, conv=conv, sqm=sqm_inc, total=total)


def own_oe_2026n(name):
    """2026 年正常化自有业务所有者收益（归母、无杠杆；2026 年量 1.56 百万吨、中国 10 万吨）。"""
    s = SC[name]
    sc6 = sc6_from_lc(s['lc'], s['mk'])
    tal = TALISON * 1.56 * talison_np_t(sc6, s['c26']) * FX / 100.0
    cap = TALISON * CAPEX_EXCESS_USD_T * 1.56 * FX / 100.0
    conv = conv_margin(s['lc'], s['mk']) * (1 - 0.25) * 10.0 / 10.0 - 0.5
    nopat = tal + conv + 0.5 + s['kw26'] + s['hq']
    return nopat - cap - 0.5 - s['g'] / s['roic_inc'] * nopat


SQM_MKT = 58.86 * SQM_SHARES_TQ * FX_SPOT     # 亿元：SQM ADR 10-21 盘中 58.86 美元

if __name__ == '__main__':
    print('=== 价格链（估值用 USD/CNY %.2f）===' % FX)
    for k, s in SC.items():
        print(f"{k:4s} 碳酸锂 {s['lc']:.1f} 万元/吨 → SC6 CIF {sc6_from_lc(s['lc'], s['mk']):,.0f} 美元/吨；"
              f"泰利森实现价 {K_TALISON * sc6_from_lc(s['lc'], s['mk']):,.0f}；"
              f"天齐转化利润 {conv_margin(s['lc'], s['mk']):.2f} 千元/吨；SQM 净利 {sqm_np(s['lc']):.2f} 十亿美元")

    print('\n=== 三季度拆分（预告 51–60 亿，上半年 42.42 亿）===')
    h1, q2 = 42.42, 23.66
    q3_lo, q3_hi = 51.0 - h1, 60.0 - h1
    q3_mid = (q3_lo + q3_hi) / 2
    sqm_q3 = SQM_STAKE * (0.550 - 0.048) * 6.75 * 10.0      # SQM 3Q 净利假设 5.5 亿美元，天齐口径调整 −0.48 亿美元
    print(f"Q3 归母 {q3_lo:.2f}–{q3_hi:.2f}（中值 {q3_mid:.2f}，Q2 {q2:.2f}）；扣非 {50.3 - 41.9966:.2f}–{59.3 - 41.9966:.2f}")
    print(f"SQM Q3 投资收益估计 {sqm_q3:.2f}；自有业务 Q3 ≈ {q3_mid - sqm_q3 - 0.15:.2f}"
          f"（Q1 {18.76 - 4.28:.2f}、Q2 {23.66 - 10.06:.2f}）")

    print('\n=== 经调整净现金（可转债、租赁另列）===')
    print(f"合并现金类 {cash_cons:.2f}；合并有息负债（不含租赁与可转债）{debt_cons:.2f}；租赁 {lease_total:.2f}（只列示）")
    print(f"文菲尔德 现金 {wf_cash:.2f} / 银团 {wf_debt:.2f}；非文菲尔德 现金 {cash_cons - wf_cash:.2f} / 负债 {debt_cons - wf_debt:.2f}")
    print(f"归母口径经调整净现金 {NET_CASH_ADJ:.2f}（调整前 {net_cash_attr_raw:.2f}）→ 为正，按无杠杆口径全额计入")
    print(f"合并口径经调整净现金 {net_cash_cons_adj:.2f}（仅作对照：其中约 74% 的文菲尔德负债由少数股东承担）")
    print(f"可转债未转股面值 {CB_FACE:.2f} 亿；转股价 {CB_CONV_PX_RMB:.2f} 元；可转股 {CB_CONV_SHARES:.4f} 亿股")

    print('\n=== 三情景（股权成本 9%）===')
    res = {k: scenario_value(k) for k in SC}
    for k, r in res.items():
        o = r['own']
        oes = ', '.join(f'{x[1]:.2f}' for x in o['rows'])
        print(f"{k:4s} p={SC[k]['p']:.2f} OE2027–31 [{oes}] 终值现值 {o['pv_tv']:.1f} 自有合计 {o['total']:.1f}；"
              f"SQM {r['sqm_v']:.1f}（净利 {r['sqm']['np1']:.2f}→{r['sqm']['np2']:.2f}）；其他 {r['others']:.1f}；"
              f"净现金 {NET_CASH_ADJ + SC[k]['extra']:.1f}")
        print(f"      权益(转债前) {r['eq_pre_cb']:.1f} → 债务法 {r['v_debt']:.2f} / 转股法 {r['v_conv']:.2f} → V = {r['v']:.2f}；"
              f"终值占自有 {o['pv_tv'] / o['total']:.0%}")
    vw = weighted()
    pv = PRICE / vw
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.2f} → {verdict(pv)}")
    print(f"分档价格（V 不变）：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；≤{1.10 * vw:.2f} 大致合理")
    b = res['base']['own']
    oe26 = own_oe_2026n('base')
    seq = [oe26] + [x[1] for x in b['rows']]
    gr = [seq[i + 1] / seq[i] - 1 for i in range(5)]
    reinv = (b['maint'] + b['rr'] * b['rows'][-1][0]) / b['rows'][-1][0]
    print("基准自有所有者收益：2026N %.2f → " % oe26 + ' → '.join(f'{x:.2f}' for x in seq[1:])
          + "；增速 " + '/'.join(f'{x:.1%}' for x in gr)
          + f"；终值增长 {SC['base']['g']:.1%}；再投资率 {reinv:.1%}；增量回报 {SC['base']['roic_inc']:.0%}")
    avg_rate = 2 * 2.7583 / 163.0                       # 2026H1 利息费用年化 / 平均带息负债（含租赁、可转债）
    pv_int = -net_cash_cons_adj * avg_rate * (1 - 0.25) / COE
    v_lev_ref = {k: (res[k]['eq_pre_cb'] - NET_CASH_ADJ - SC[k]['extra'] - pv_int - CB_FACE) / SHARES for k in SC}
    print(f"对照（合并口径有杠杆：净负债 {-net_cash_cons_adj:.1f} 亿按 {avg_rate:.2%} 税后利息滚动、现值 {pv_int:.1f}）：" +
          '，'.join(f"{k} {v:.2f}" for k, v in v_lev_ref.items()) +
          f"；加权 {sum(SC[k]['p'] * v_lev_ref[k] for k in SC):.2f}（不采用：少数股东承担 73.99% 的文菲尔德负债）")
    v_bs = weighted() * SHARES / SHARES_BS
    print(f"（无回购专户股份；按 6-30 资产负债表股本 17.1322 亿计 V ≈ {v_bs:.2f}）")

    print('\n=== 股权成本敏感性 ===')
    v8, v10 = weighted(0.08), weighted(0.10)
    for c in (0.08, 0.10):
        print(f"CoE {c:.0%}: " + '，'.join(f"{k} {scenario_value(k, coe=c)['v']:.2f}" for k in SC) + f"；加权 {weighted(c):.2f}")

    irr = bisect(lambda r: scenario_value('base', coe=r)['v'] - PRICE, 0.04, 0.12)
    irr_w = bisect(lambda r: weighted(r) - PRICE, 0.04, 0.12)
    print(f"现价隐含回报（基准情景现金流）{irr:.2%}；（三情景加权现金流）{irr_w:.2%}")

    print('\n=== 反向 DCF ===')
    lc_imp = bisect(lambda x: scenario_value('base', lc=x)['v'] - PRICE, 6.0, 25.0)
    print(f"现价隐含长期碳酸锂 {lc_imp:.2f} 万元/吨（SC6 约 {sc6_from_lc(lc_imp, 3.0):,.0f} 美元/吨，其余取基准）")

    def v_with_g(g):
        s = dict(SC['base']); s['g'] = g
        SC['tmp'] = s
        v = scenario_value('tmp')['v']
        del SC['tmp']
        return v
    g_imp = bisect(lambda g: v_with_g(g) - PRICE, 0.0, 0.08)
    print(f"基准价格下现价隐含自有业务永续增长 {g_imp:.2%}（ROIC_inc 25%）")

    print('\n=== 分部对照：SQM 按市值 ===')
    print(f"SQM 21.9% 市值 {SQM_MKT:.1f} 亿（ADR 58.86 美元 × 0.6256 亿股 × {FX_SPOT}）；权益法账面 254.08；6-30 公允价值 285.28")
    for k in SC:
        print(f"{k:4s} SQM DCF {res[k]['sqm_v']:.1f} → V {res[k]['v']:.2f}；SQM 按市值 V "
              f"{scenario_value(k, sqm_override=SQM_MKT)['v']:.2f}")
    vw_mkt = weighted(sqm_market=True)
    print(f"SQM 按市值的加权 V {vw_mkt:.2f}，P/V {PRICE / vw_mkt:.2f}")
    mc_ah = (SHARES - H_SHARES) * PRICE + H_SHARES * H_PRICE_HKD * HKDCNY
    implied_own = PRICE * SHARES - SQM_MKT - res['base']['others'] - NET_CASH_ADJ + CB_FACE
    print(f"A×总股本 {PRICE * SHARES:.1f} 亿；A+H 各按其价 {mc_ah:.1f} 亿；"
          f"扣 SQM 市值、其他投资与净现金后市场给自有业务 {implied_own:.1f} 亿（基准 DCF {res['base']['own']['total']:.1f}）")

    print('\n=== H 股对照 ===')
    h_rmb = H_PRICE_HKD * HKDCNY
    print(f"H 股 {H_PRICE_HKD} 港元 = {h_rmb:.2f} 元；A/H 溢价 {PRICE / h_rmb - 1:.1%}；H 股 P/V {h_rmb / vw:.2f} → {verdict(h_rmb / vw)}")

    print('\n=== 2026 正常化归母净利（报表口径）===')
    for k in SC:
        n = normalized_np_2026(k)
        print(f"{k:4s} {n['total']:.1f}（泰利森 {n['talison']:.1f}、转化 {n['conv']:.1f}、SQM {n['sqm']:.1f}）")

    print('\n=== 证伪触发后的 V（加权）===')
    print(f"F1 碳酸锂 2027H1 均价 ≤8 万（权重 50/40/10）：{weighted(probs={'bear': .5, 'base': .4, 'bull': .1}):.2f}")
    print(f"F2 碳酸锂 2027Q2–Q3 均价 ≥15 万且 SC6 ≥2,000（权重 10/50/40）：{weighted(probs={'bear': .1, 'base': .5, 'bull': .4}):.2f}")
    saved = {k: dict(SC[k]) for k in SC}
    for k in SC:
        SC[k]['v28'] -= 0.15; SC[k]['v27'] -= 0.10; SC[k]['c27'] += 25; SC[k]['c28'] += 25
    print(f"F3 格林布什 FY27 产量 <1.50 百万吨或现金成本 >460 澳元/吨（产量 −0.15、成本 +25 美元）：{weighted():.2f}")
    for k in SC:
        SC[k].update(saved[k])
    for k in SC:
        SC[k]['sqm_cut'] = min(0.6, SC[k]['sqm_cut'] + 0.15)
    v_f4 = weighted()
    for k in SC:
        SC[k].update(saved[k])
    print(f"F4 SQM 2031 起归属利润折减再加 15 个百分点：{v_f4:.2f}")
    print(f"F5 2026 年报归母 <58 亿（即 Q4 归母 <约 3 亿、自有业务转亏；权重 35/50/15）：{weighted(probs={'bear': .35, 'base': .5, 'bull': .15}):.2f}")
    print(f"（对照）SQM 按现市值、其余不变：{vw_mkt:.2f}")
