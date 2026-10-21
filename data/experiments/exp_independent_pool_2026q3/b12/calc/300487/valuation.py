#!/usr/bin/env python3
"""300487 蓝晓科技 独立估值（OI-291 b12，深度版）。

运行：python3 valuation.py
金额单位亿元，股本亿股，每股价值元/股。全部输入写在本脚本内，出处见正文「来源」一节。
方法：所有者收益 DCF（经营 NOPAT×(1-再投资率)，前 5 年逐年、第 6-10 年线性衰减到终值增速，
年中折现），加经调整净现金（无杠杆口径，不含可转债）与非经营资产；可转债逐情景取低
（债务法扣除 max(未转股面值, 债底现值) vs 全部转股法加股本不扣债）。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
VAL_DATE = date(2026, 10, 20)
PRICE = 64.95                 # 2026-10-20 收盘（brief）
SHARES = 5.0914               # 亿股，腾讯行情总股本，含回购专户股份（brief）
TREASURY = 0.0055             # 亿股，回购专户 550,000 股，未公告注销（dividend_20260921 第 1 页）
COE = 0.09

# ---------------------------------------------------------------- 可转债：蓝晓转02（123195）
CB_FACE = 5.455263            # 2026-09-30 剩余面值（financing_20261008 第 1、5 页）
CB_CONV_PRICE = 59.09         # 2026-09-29 起转股价（同上第 1 页）
CB_SHARES = CB_FACE / CB_CONV_PRICE          # 全部转股新增股本，亿股
# 票面利率 0.4/0.6/1.1/1.8/2.5/3.0%，到期 2029-04-16 按面值 115%（含最后一期利息）赎回
# （2025 年度受托管理事务报告第 3、7 页；2026H1_report 第 135-136 页）
CB_FLOWS = [(date(2027, 4, 17), 1.8), (date(2028, 4, 17), 2.5), (date(2029, 4, 17), 115.0)]  # 每百元面值
CB_FLOOR_YIELD = 0.035        # 债底折现率：A+ 主体（新世纪评级），约 2.5 年


def yf(d):
    """估值日起的年数。"""
    return (d - VAL_DATE).days / 365.25


def cb_floor(yld=CB_FLOOR_YIELD):
    return CB_FACE * sum(cf / 100 / (1 + yld) ** yf(d) for d, cf in CB_FLOWS)


CB_DEBT = max(CB_FACE, cb_floor())  # 债务法全额扣除的金额（取大者，对股东取低）

# ---------------------------------------------------------------- 2026-06-30 资产负债（2026H1_report 第 61-64、111、146-147 页）
CASH = 26.0104                # 货币资金
TRADING_FA = 2.6098           # 交易性金融资产（理财 2.503 + 股票等 0.107）
RESTRICTED = 0.0540           # 冻结、保函保证金等（第 24、111 页）
OP_RESERVE = 2.00             # 经营备付：约 1.5 个月经营现金流出（上半年经营流出 7.83 亿）
DIV_PAYABLE_0630 = 0.8799     # 2025 年度分红，6-30 应付股利，7-03 派发
DIV_INTERIM_0929 = 0.6001     # 2026 半年度分红 60,013,721.36 元，9-29 派发（现价已除息）
ST_LOAN = 0.3958
NCL_1Y = 0.0101
LEASE = 0.0299
ABANDON_PROV = 0.4089         # 预计负债：危废处置设施弃置义务（类债务）
# 外币现金按估值日汇率重估：6-30 美元 2.88 亿美元@6.8109，欧元 0.427 亿欧元@7.7671（第 146 页）
USD_CASH = 2.87996386
USD_0630, USD_NOW = 6.8109, 6.7220   # 10-16 中间价 6.7220（中国经济网/CFETS）
EUR_CASH = 0.42708795
EUR_0630 = 7.7671
EUR_CHG = USD_NOW / USD_0630 - 1     # 欧元兑人民币未查到，按与美元同幅度保守处理
FX_MARK = USD_CASH * (USD_NOW - USD_0630) + EUR_CASH * EUR_0630 * EUR_CHG

NET_CASH_ADJ = (CASH + TRADING_FA - RESTRICTED - OP_RESERVE - DIV_PAYABLE_0630 - DIV_INTERIM_0929
                - ST_LOAN - NCL_1Y - LEASE - ABANDON_PROV + FX_MARK)

# 非经营资产（账面）：青海锦泰钾肥 1.6092（其他权益工具投资）、联营企业 1.1570（微纯生物 0.677、
# 峰鑫泽 0.208、谱键 0.108、伊莱柯 0.090、蓝屹 0.058、南大 0.016）、结则茶卡委托加工产线在建工程 3.2578
JINTAI = 1.6092
ASSOC = 1.1570
ZECHAKA_CIP = 3.2578

# ---------------------------------------------------------------- 核心 EBIT 桥（剔除利息、汇兑、投资收益、公允价值变动、营业外）
def core_ebit(pbt, int_exp, int_inc, fx_loss, inv, fv, nonop_in, nonop_out):
    return pbt + int_exp - int_inc + fx_loss - inv - fv - nonop_in + nonop_out


EBIT_2025 = core_ebit(10.48668, 0.43035, 0.66872, 0.22658, 0.05200, -0.06843, 0.24910, 0.08362)
EBIT_25H1 = core_ebit(5.01158, 0.20834, 0.32707, -0.19446, 0.04242, -0.00554, 0.00119, 0.00212)
EBIT_26H1 = core_ebit(4.65671, 0.22521, 0.22760, 0.81050, -0.00630, 0.01943, 0.00048, 0.00375)
EBIT_25H2 = EBIT_2025 - EBIT_25H1
REV_2025, REV_25H1, REV_26H1 = 27.8583, 12.4743, 13.7804
LI_REV_2025H2 = 1.13          # 2025 年盐湖提锂大项目收入全部在下半年确认（IR_20251025 第 1 页：前三季度无提锂大项目收入；2025 年报第 32、34 页）
LI_MARGIN = 0.31              # 提锂系统装置 EBIT 贡献率（系统装置毛利率 34.7%-36.1%，扣直接费用）


def ebit_2026e(h2_growth_ex_li, li_rev_h2):
    base_h2_2025 = EBIT_25H2 - LI_REV_2025H2 * LI_MARGIN
    return EBIT_26H1 + base_h2_2025 * (1 + h2_growth_ex_li) + li_rev_h2 * LI_MARGIN


EBIT_2026E_BASE = ebit_2026e(0.11, 0.35)
TAX_BASE = 0.13
NOPAT26_BASE = EBIT_2026E_BASE * (1 - TAX_BASE)
NET_INT_AT = 0.05             # 正常化净利息税后（利息收入约 0.45 + 理财收益约 0.03 − 可转债实际利率利息约 0.42）

# ---------------------------------------------------------------- 情景
SCEN = {
    'bear': dict(p=0.25, nopat26=9.00, g=[0.05, 0.05, 0.04, 0.04, 0.03], rr=[0.40, 0.35, 0.25, 0.22, 0.20],
                 gT=0.020, roicT=0.15, nonop=0.6 * JINTAI + ASSOC, zechaka=0.0, cash_adj=-0.50,
                 desc='生命科学价格战与金属景气回落，核心 EBIT 率回到约 36%；提锂停在谷底；产业园照建但回报低；'
                      '结则茶卡产线减值；阿根廷合同和解 −0.5 亿'),
    'base': dict(p=0.50, nopat26=round(NOPAT26_BASE, 2), g=[0.11, 0.10, 0.09, 0.08, 0.07],
                 rr=[0.45, 0.40, 0.32, 0.28, 0.25], gT=0.025, roicT=0.20, nonop=0.8 * JINTAI + ASSOC,
                 zechaka=0.6 * ZECHAKA_CIP, cash_adj=0.0,
                 desc='基础业务收入约 +9%、核心 EBIT 率约 39%；蒲城产业园 2026-28 年投入约 11 亿；提锂维持低位'),
    'bull': dict(p=0.25, nopat26=10.60, g=[0.17, 0.15, 0.13, 0.11, 0.09], rr=[0.50, 0.44, 0.38, 0.32, 0.27],
                 gT=0.025, roicT=0.25, nonop=JINTAI + ASSOC, zechaka=1.2 * ZECHAKA_CIP, cash_adj=0.0,
                 desc='GLP-1/小核酸载体与超纯水放量、产业园满产；碳酸锂 10 万元/吨以上带来提锂中周期订单；结则茶卡投产'),
}
YEARS = list(range(2027, 2037))


def path(s):
    """返回逐年 (年份, 增速, 再投资率, NOPAT, 所有者收益)。"""
    g5, rr5 = s['g'][-1], s['rr'][-1]
    roic5 = g5 / rr5
    gs, rrs = list(s['g']), list(s['rr'])
    for k in range(1, 6):
        g = g5 + (s['gT'] - g5) * k / 5
        roic = roic5 + (s['roicT'] - roic5) * k / 5
        gs.append(g)
        rrs.append(g / roic)
    rows, nopat = [], s['nopat26']
    for y, g, rr in zip(YEARS, gs, rrs):
        nopat *= 1 + g
        rows.append((y, g, rr, nopat, nopat * (1 - rr)))
    return rows


def ops_value(s, r, fade=True):
    rows = path(s) if fade else path(s)[:5]
    h2_2026 = s['nopat26'] * 0.5 * (1 - s['rr'][0])          # 2026 下半年所有者收益（6-30 净现金之后）
    pv = h2_2026
    for y, g, rr, nopat, oe in rows:
        pv += oe / (1 + r) ** yf(date(y, 7, 1))
    last_nopat = rows[-1][3]
    oe_t = last_nopat * (1 + s['gT']) * (1 - s['gT'] / s['roicT'])
    tv = oe_t / (r - s['gT'])
    pv_tv = tv / (1 + r) ** yf(date(rows[-1][0], 7, 1))
    return pv + pv_tv, pv_tv


def equity_pre_cb(s, r, fade=True):
    ops, _ = ops_value(s, r, fade)
    return ops + NET_CASH_ADJ + s['cash_adj'] + s['nonop'] + s['zechaka']


def per_share(s, r, shares=SHARES, fade=True):
    e = equity_pre_cb(s, r, fade)
    v_debt = (e - CB_DEBT) / shares
    v_conv = e / (shares + CB_SHARES)
    return min(v_debt, v_conv), v_debt, v_conv


def weighted(r, shares=SHARES, scen=None, fade=True):
    scen = scen or SCEN
    return sum(s['p'] * per_share(s, r, shares, fade)[0] for s in scen.values())


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


def implied_irr():
    return solve(lambda r: per_share(SCEN['base'], r)[0], 0.04, 0.15, PRICE)


def reverse_dcf_10y(roic=0.30, gT=0.025, roicT=0.20, r=COE):
    """现价隐含的 10 年 NOPAT 增速（再投资率 = g/ROIC），之后 2.5% 永续。"""
    def val(g):
        s = dict(SCEN['base'])
        s.update(g=[g] * 5, rr=[g / roic] * 5, gT=gT, roicT=roicT)
        # 第 6-10 年保持同一增速：直接逐年计算
        nopat, pv = s['nopat26'], s['nopat26'] * 0.5 * (1 - g / roic)
        for y in YEARS:
            nopat *= 1 + g
            pv += nopat * (1 - g / roic) / (1 + r) ** yf(date(y, 7, 1))
        tv = nopat * (1 + gT) * (1 - gT / roicT) / (r - gT)
        pv += tv / (1 + r) ** yf(date(YEARS[-1], 7, 1))
        e = pv + NET_CASH_ADJ + s['nonop'] + s['zechaka']
        return min((e - CB_DEBT) / SHARES, e / (SHARES + CB_SHARES))
    return solve(val, 0.0, 0.40, PRICE)


def reverse_perpetual(r=COE, roicT=0.20):
    """现价隐含的永续增速（自 2027 年起，再投资率 = g/ROIC）。"""
    def val(g):
        n27 = SCEN['base']['nopat26'] * (1 + g)
        pv = n27 * (1 - g / roicT) / (r - g) / (1 + r) ** yf(date(2027, 7, 1))
        e = pv + NET_CASH_ADJ + SCEN['base']['nonop'] + SCEN['base']['zechaka']
        return min((e - CB_DEBT) / SHARES, e / (SHARES + CB_SHARES))
    return solve(val, 0.0, r - 0.001, PRICE)


def band(v):
    pv = PRICE / v
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def main():
    print('== 核心 EBIT 桥（亿元）')
    print(f'2025 核心 EBIT {EBIT_2025:.3f}（率 {EBIT_2025 / REV_2025:.1%}）；2025H1 {EBIT_25H1:.3f}；'
          f'2026H1 {EBIT_26H1:.3f}（率 {EBIT_26H1 / REV_26H1:.1%}，同比 {EBIT_26H1 / EBIT_25H1 - 1:+.1%}）')
    ttm = EBIT_25H2 + EBIT_26H1
    print(f'TTM 核心 EBIT {ttm:.3f}（TTM 营收 {REV_2025 - REV_25H1 + REV_26H1:.2f}）；2026E 基准 {EBIT_2026E_BASE:.3f}，'
          f'税率 {TAX_BASE:.0%} → NOPAT {NOPAT26_BASE:.2f}')
    print()
    print('== 经调整净现金（无杠杆口径，不含可转债）')
    print(f'现金 {CASH:.2f} + 交易性金融资产 {TRADING_FA:.2f} − 受限 {RESTRICTED:.3f} − 经营备付 {OP_RESERVE:.2f} '
          f'− 已宣派股利 {DIV_PAYABLE_0630 + DIV_INTERIM_0929:.2f} − 有息负债 {ST_LOAN + NCL_1Y + LEASE:.3f} '
          f'− 弃置义务 {ABANDON_PROV:.3f} + 外币重估 {FX_MARK:+.3f} = {NET_CASH_ADJ:.2f}')
    print(f'可转债：面值 {CB_FACE:.3f}，债底现值（{CB_FLOOR_YIELD:.1%}）{cb_floor():.3f}，债务法扣 {CB_DEBT:.3f}；'
          f'全部转股新增 {CB_SHARES * 1e4:.0f} 万股（转股价 {CB_CONV_PRICE}）')
    print()
    print('== 情景（股权成本 9%）')
    for k, s in SCEN.items():
        ops, pv_tv = ops_value(s, COE)
        v, vd, vc = per_share(s, COE)
        np26 = s['nopat26'] + NET_INT_AT
        print(f'[{k}] p={s["p"]:.2f} NOPAT26={s["nopat26"]:.2f} 正常化归母={np26:.2f} 经营价值={ops:.1f} '
              f'（终值占 {pv_tv / ops:.0%}） 非经营={s["nonop"] + s["zechaka"]:.2f}')
        print(f'      股权价值（未处理可转债）{equity_pre_cb(s, COE):.1f}；V 债务法 {vd:.2f} / 全部转股 {vc:.2f} → 取低 {v:.2f}')
        rows = path(s)
        print('      ' + '；'.join(f'{y}: g {g:.1%} RR {rr:.0%} OE {oe:.2f}' for y, g, rr, n, oe in rows[:5]))
    b_rows = path(SCEN['base'])[:5]
    reinv = sum(n * rr for y, g, rr, n, oe in b_rows)
    d_nopat = b_rows[-1][3] - SCEN['base']['nopat26']
    print(f'基准 2027-31 平均再投资率 {sum(r[2] for r in b_rows) / 5:.0%}，累计再投资 {reinv:.1f}，'
          f'NOPAT 增量 {d_nopat:.2f} → 增量回报 {d_nopat / reinv:.0%}')
    vw = weighted(COE)
    print()
    print(f'加权 V = {vw:.2f}；P/V = {PRICE / vw:.2f}（{band(vw)}）')
    print(f'分档价格（V 不变）：≤ {0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}-{0.90 * vw:.2f} 温和低估；'
          f'{0.90 * vw:.2f}-{1.10 * vw:.2f} 大致合理；> {1.10 * vw:.2f} 偏贵')
    vw_ex = weighted(COE, SHARES - TREASURY)
    print(f'剔除回购专户股份后 V = {vw_ex:.2f}；P/V = {PRICE / vw_ex:.2f}')
    for r in (0.08, 0.10):
        vs = {k: per_share(s, r)[0] for k, s in SCEN.items()}
        print(f'股权成本 {r:.0%}：' + '，'.join(f'{k} {v:.2f}' for k, v in vs.items())
              + f'；加权 {weighted(r):.2f}；P/V {PRICE / weighted(r):.2f}')
    print(f'对照：不设第 6-10 年衰减期（第 5 年后直接进入终值）加权 V {weighted(COE, fade=False):.2f}')
    print(f'现价隐含回报（基准情景使现值=现价的折现率）：{implied_irr():.2%}')
    print(f'反向 DCF：现价隐含 10 年 NOPAT 年增速 {reverse_dcf_10y():.1%}（再投资率=g/30%，之后 2.5% 永续）；'
          f'隐含永续增速 {reverse_perpetual():.2%}（ROIC 20%）')
    print()
    print('== 交叉验证')
    np_base = SCEN['base']['nopat26'] + NET_INT_AT
    ev = PRICE * SHARES - NET_CASH_ADJ + CB_FACE - (SCEN['base']['nonop'])
    # 券商一致预期路径（数据包：2026、2027 年预测 PE 30.56、24.57 → 归母约 10.8、13.5 亿，后年增速 21.7%），
    # 2029-31 年假设 17%/14%/11%，再投资率 = g/35%，其后同样衰减；仅作参照，不入加权
    cons = dict(SCEN['bull'], nopat26=10.8, g=[0.25, 0.217, 0.17, 0.14, 0.11],
                rr=[g / 0.35 for g in (0.25, 0.217, 0.17, 0.14, 0.11)])
    print(f'参照：券商一致预期路径 V {per_share(cons, COE)[0]:.2f}（8% 下 {per_share(cons, 0.08)[0]:.2f}）')
    print(f'市值 {PRICE * SHARES:.1f}；市值/2026 正常化归母 {PRICE * SHARES / np_base:.1f}x；'
          f'EV {ev:.1f} / 2026E 核心 EBIT {ev / EBIT_2026E_BASE:.1f}x；'
          f'近 12 个月股息率 {0.4710 / PRICE:.2%}；PB {PRICE * SHARES / 47.2592:.2f}')
    print()
    print('== 证伪触发后的 V（股权成本 9%）')
    b, m, u = (per_share(SCEN[k], COE)[0] for k in ('bear', 'base', 'bull'))
    vc = per_share(cons, COE)[0]
    print(f'F1 兑现一致预期增速（一致预期路径 0.5、牛市 0.5）：{0.5 * vc + 0.5 * u:.2f}')
    print(f'F2 吸附材料增速失速（熊 0.6、基准 0.4）：{0.6 * b + 0.4 * m:.2f}')
    print(f'F3 毛利率连续两季低于 50%（熊 0.5、基准 0.5）：{0.5 * b + 0.5 * m:.2f}')
    no_z = {k: dict(s, zechaka=0.0) for k, s in SCEN.items()}
    print(f'F4 结则茶卡产线未投产或减值（三情景均按 0 计）：加权 {weighted(COE, scen=no_z):.2f}')
    print(f'F5 碳酸锂回到 15 万元/吨以上且新签提锂订单 ≥ 5 亿（牛 0.5、基准 0.5）：{0.5 * u + 0.5 * m:.2f}')
    print()
    print('== 2026 年三季报核对参照（基准）')
    q3_25_core = core_ebit(7.7169, 0.3179, 0.4593, -0.0385, 0.0700, -0.0006, 0.0012, 0.0055) - EBIT_25H1
    print(f'2025Q3 核心 EBIT {q3_25_core:.2f}（营收 6.86）；2026Q3E 核心 EBIT {q3_25_core * 1.11:.2f}；'
          f'若三季度汇兑损失 0.1-0.2 亿、税率 13.5%，归母约 '
          f'{(q3_25_core * 1.11 - 0.2) * 0.865:.2f}-{(q3_25_core * 1.11 - 0.1) * 0.865:.2f} 亿（2025Q3 为 2.07）')


if __name__ == '__main__':
    main()
