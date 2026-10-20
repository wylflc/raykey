#!/usr/bin/env python3
"""伟星新材（002372）独立估值：所有者收益 DCF、三情景、反向 DCF 与交叉验证。

全部输入写在本脚本内，`python3 valuation.py` 打印正文与 json 用到的全部数字。
金额单位亿元，每股价值元/股。来源页码见正文「来源」一节。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 8.68                    # 2026-10-19 收盘（brief）
SHARES = 15.9204                # 总股本（含回购专户股份，brief）
REPO = 0.2017                   # 回购专户 20,170,000 股（2026H1_report 第 32 页），未公告注销
SHARES_EX = SHARES - REPO       # 剔除回购专户股份后的股本（分红基数 1,571,867,988 股）
VAL_DATE = date(2026, 10, 19)
COE = 0.09
T0 = (date(2026, 12, 31) - VAL_DATE).days / 365.25   # 2026 下半年现金流折现期（年末惯例）

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 35-37、74-75、94-96 页）
CASH = 10.7249                  # 货币资金
RESTRICTED = 1.3502             # 受限：票据保证金 1.2039 + 冻结保函等 0.1463（第 17 页）
TFA = 9.9042                    # 交易性金融资产：结构性存款 9.50 + 理财 0.4042（第 75 页）
LEASE = 0.1484 + 0.0297         # 租赁负债 + 一年内到期租赁负债；无银行借款
ACQ_PAYABLE = 0.3685 + 0.0304   # 其他应付款中应付股权收购款 + 长期应付款（广州合信）
POST_ACQ = 0.16                 # 2026-08 收购浙江可瑞 40%（mna_20260812 第 1 页），期后付现
DIVIDEND_DECLARED = 0.0         # 半年度不分配（2026H1_report 第 2 页），无已宣派未付股利

# 东鹏合立（47% 有限合伙份额，权益法，2026H1_report 第 84、113 页；在投成本 2.38 亿，2025_annual_report 第 60 页）
DP_BOOK = 4.2513
DP_COST = 2.38
DP_TAX = 0.25                   # 退出时增值部分按 25% 计税（保守）

# ---------------------------------------------------------------- 2026 上半年实际（2026H1_report 第 40-41、99-102 页）
H1_REV = 18.967
# 核心经营利润 = 营业利润 4.1343 − 投资收益 1.3663 − 公允价值变动 0.0042 − 利息收入 0.0460
#             − 计入非经常性损益的政府补助 0.0970（第 8 页）
H1_CORE_EBIT = 4.1343 - 1.3663 - 0.0042 - 0.0460 - 0.0970
H1_NET_INTEREST = 0.0460 + 0.1166 + 0.0042 - 0.0054   # 存款利息 + 理财收益 + 公允价值 − 利息支出
H2_NET_INTEREST = 0.15          # 下半年存款与结构性存款收益（约 19 亿 × 1.6% / 2）

REV_2025 = 53.820
H2_2025_REV = 33.043            # 2025 三、四季度营收合计（2025_annual_report 第 9 页）

# ---------------------------------------------------------------- 三情景
# growth：2027-2031 营收增速；margin：核心经营利润率（含其他收益中经常性部分、存货与信用减值，
# 不含投资收益、利息、商誉减值与计入非经常性损益的补助）；k：每增加 1 元营收需净投入的经营资本；
# floor：每年至少的净再投资（海外与智能化改造，资本开支高于折旧部分）；ronic：终值期新增投资回报。
SCEN = {
    'bear': dict(p=0.25, h2_rev=30.0, h2_margin=0.145,
                 growth=[-0.06, -0.03, 0.00, 0.02, 0.02],
                 margin=[0.135, 0.135, 0.138, 0.140, 0.140],
                 tg=0.010, ronic=0.15, tax=0.185, reserve=5.0, dp_haircut=0.50, k=0.45, floor=0.30),
    'base': dict(p=0.50, h2_rev=31.0, h2_margin=0.160,
                 growth=[-0.02, 0.02, 0.035, 0.035, 0.03],
                 margin=[0.150, 0.154, 0.159, 0.163, 0.166],
                 tg=0.020, ronic=0.18, tax=0.175, reserve=4.0, dp_haircut=0.25, k=0.45, floor=0.30),
    'bull': dict(p=0.25, h2_rev=32.0, h2_margin=0.170,
                 growth=[0.03, 0.05, 0.05, 0.045, 0.04],
                 margin=[0.160, 0.168, 0.175, 0.180, 0.182],
                 tg=0.025, ronic=0.25, tax=0.170, reserve=3.0, dp_haircut=0.10, k=0.40, floor=0.30),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def net_cash_adj(reserve):
    """经调整净现金：非受限现金与结构性存款 − 有息负债与类债务 − 期后收购款 − 经营备付。"""
    return CASH - RESTRICTED + TFA - LEASE - ACQ_PAYABLE - POST_ACQ - DIVIDEND_DECLARED - reserve


def dongpeng_value(haircut):
    after_tax = DP_BOOK - DP_TAX * (DP_BOOK - DP_COST)
    return after_tax * (1 - haircut)


def project(s):
    """返回逐年路径：营收、核心经营利润、NOPAT、再投资、所有者收益。"""
    h2_ebit = s['h2_rev'] * s['h2_margin']
    rev26 = H1_REV + s['h2_rev']
    ebit26 = H1_CORE_EBIT + h2_ebit
    rows = []
    rev_prev = rev26
    for g, m in zip(s['growth'], s['margin']):
        rev = rev_prev * (1 + g)
        ebit = rev * m
        nopat = ebit * (1 - s['tax'])
        reinv = max(s['floor'], s['k'] * (rev - rev_prev))
        rows.append(dict(rev=rev, ebit=ebit, nopat=nopat, reinv=reinv, oe=nopat - reinv))
        rev_prev = rev
    h2_oe = h2_ebit * (1 - s['tax']) - s['floor'] / 2
    oe26 = ebit26 * (1 - s['tax']) - s['floor']
    return dict(rev26=rev26, ebit26=ebit26, h2_ebit=h2_ebit, h2_oe=h2_oe, oe26=oe26, rows=rows)


def equity_value(s, r, tg=None, ronic=None):
    tg = s['tg'] if tg is None else tg
    ronic = s['ronic'] if ronic is None else ronic
    pj = project(s)
    pv = pj['h2_oe'] / (1 + r) ** T0
    for i, row in enumerate(pj['rows']):
        pv += row['oe'] / (1 + r) ** (T0 + i + 1)
    last = pj['rows'][-1]
    oe_next = last['nopat'] * (1 + tg) * (1 - tg / ronic)
    tv = oe_next / (r - tg)
    pv_tv = tv / (1 + r) ** (T0 + len(pj['rows']))
    ops = pv + pv_tv
    nc = net_cash_adj(s['reserve'])
    dp = dongpeng_value(s['dp_haircut'])
    eq = ops + nc + dp
    return dict(eq=eq, ops=ops, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / eq, nc=nc, dp=dp,
                v=eq / SHARES, v_ex=eq / SHARES_EX)


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


def normalized_np_2026(s):
    pj = project(s)
    return (pj['ebit26'] + H1_NET_INTEREST + H2_NET_INTEREST) * (1 - s['tax'])


def variant(base, **kw):
    s = dict(base)
    s.update(kw)
    return s


def main():
    print(f"价格日 {VAL_DATE}  现价 {PRICE}  总股本 {SHARES} 亿股（剔除回购专户 {SHARES_EX:.4f}）  T0={T0:.3f} 年")
    print(f"2026H1 核心经营利润 {H1_CORE_EBIT:.3f}（营收 {H1_REV}，利润率 {H1_CORE_EBIT / H1_REV:.1%}）")
    print(f"东鹏合立税后账面 {DP_BOOK - DP_TAX * (DP_BOOK - DP_COST):.3f}")
    print()
    res = {}
    for name, s in SCEN.items():
        pj = project(s)
        r9 = equity_value(s, COE)
        r8 = equity_value(s, 0.08)
        r10 = equity_value(s, 0.10)
        res[name] = dict(r9=r9, r8=r8, r10=r10, pj=pj)
        print(f"== {name}（概率 {s['p']:.0%}）")
        print(f"  2026E 营收 {pj['rev26']:.2f}（同比 {pj['rev26'] / REV_2025 - 1:+.1%}），下半年营收 {s['h2_rev']:.1f}"
              f"（同比 {s['h2_rev'] / H2_2025_REV - 1:+.1%}），核心经营利润 {pj['ebit26']:.2f}"
              f"（{pj['ebit26'] / pj['rev26']:.1%}），2026 正常化归母净利 {normalized_np_2026(s):.2f}，"
              f"2026 所有者收益 {pj['oe26']:.2f}")
        prev = pj['oe26']
        for y, row in zip(YEARS, pj['rows']):
            print(f"  {y}: 营收 {row['rev']:6.2f}  核心经营利润 {row['ebit']:5.2f}（{row['ebit'] / row['rev']:.1%}）"
                  f"  NOPAT {row['nopat']:5.2f}  再投资 {row['reinv']:4.2f}  所有者收益 {row['oe']:5.2f}"
                  f"（{row['oe'] / prev - 1:+.1%}）")
            prev = row['oe']
        print(f"  终值增长 {s['tg']:.1%}，终值期新增投资回报 {s['ronic']:.0%}，终值期再投资率 {s['tg'] / s['ronic']:.1%}")
        print(f"  经营价值 {r9['ops']:.2f}（显性期 {r9['pv_explicit']:.2f} + 终值现值 {r9['pv_tv']:.2f}）"
              f" + 经调整净现金 {r9['nc']:.2f} + 东鹏合立 {r9['dp']:.2f} = 股权 {r9['eq']:.2f}；终值占股权 {r9['tv_share']:.1%}")
        print(f"  V(9%) = {r9['v']:.2f}  V(8%) = {r8['v']:.2f}  V(10%) = {r10['v']:.2f}  剔除回购股份 V(9%) = {r9['v_ex']:.2f}")
        print()
    vw = sum(SCEN[n]['p'] * res[n]['r9']['v'] for n in SCEN)
    vw8 = sum(SCEN[n]['p'] * res[n]['r8']['v'] for n in SCEN)
    vw10 = sum(SCEN[n]['p'] * res[n]['r10']['v'] for n in SCEN)
    vw_ex = sum(SCEN[n]['p'] * res[n]['r9']['v_ex'] for n in SCEN)
    pv_ratio = PRICE / vw
    tier = '明显低估' if pv_ratio <= 0.75 else '温和低估' if pv_ratio <= 0.90 else '大致合理' if pv_ratio <= 1.10 else '偏贵或价值陷阱风险高'
    print(f"加权 V(9%) = {vw:.2f}  P/V = {pv_ratio:.3f}（{tier}）")
    print(f"加权 V(8%) = {vw8:.2f}  加权 V(10%) = {vw10:.2f}")
    print(f"剔除回购专户股份：加权 V = {vw_ex:.2f}  P/V = {PRICE / vw_ex:.3f}")
    print(f"V 不变时各档价格：明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}～{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}～{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")

    base = SCEN['base']
    irr = solve(lambda r: equity_value(base, r)['v'], 0.04, 0.20, PRICE)
    print(f"现价隐含回报（基准情景现金流 + 终值 + 净现金）= {irr:.2%}")

    # 反向 DCF（a）：基准 2026 所有者收益起步，10 年恒定增速 g，其后 2.5% 永续
    pj = project(base)
    mcap = PRICE * SHARES
    target_ops = mcap - net_cash_adj(base['reserve']) - dongpeng_value(base['dp_haircut'])

    def ops_10y(g):
        pv = pj['h2_oe'] / (1 + COE) ** T0
        oe = pj['oe26']
        for n in range(1, 11):
            oe *= 1 + g
            pv += oe / (1 + COE) ** (T0 + n)
        tv = oe * 1.025 / (COE - 0.025)
        return pv + tv / (1 + COE) ** (T0 + 10)

    g10 = solve(ops_10y, -0.05, 0.20, target_ops)
    # 反向 DCF（b）：以 2027 基准 NOPAT 为起点的永续增长（新增投资回报 18%）
    nopat27 = pj['rows'][0]['nopat']
    pv_h2 = pj['h2_oe'] / (1 + COE) ** T0

    def ops_perp(g):
        return pv_h2 + nopat27 * (1 - g / base['ronic']) / (COE - g) / (1 + COE) ** T0

    gp = solve(ops_perp, -0.05, 0.085, target_ops)
    print(f"反向 DCF：市值 {mcap:.2f} − 净现金 {net_cash_adj(base['reserve']):.2f} − 东鹏合立 {dongpeng_value(base['dp_haircut']):.2f}"
          f" = 经营部分 {target_ops:.2f}；隐含 10 年所有者收益年增速 {g10:.2%}（其后 2.5%），"
          f"或以 2027 NOPAT {nopat27:.2f} 起的永续增速 {gp:.2%}")

    # 2026 正常化归母净利三档（含净利息，剔除一次性项目）
    print("2026 正常化归母净利：" + "  ".join(f"{n} {normalized_np_2026(SCEN[n]):.2f}" for n in SCEN))

    # 基准情景增长路径与再投资
    rows = pj['rows']
    oe_series = [pj['oe26']] + [r['oe'] for r in rows]
    growth = [oe_series[i + 1] / oe_series[i] - 1 for i in range(5)]
    reinv_rate = sum(r['reinv'] for r in rows) / sum(r['nopat'] for r in rows)
    print("基准所有者收益增速 2027-2031：" + ", ".join(f"{g:+.1%}" for g in growth)
          + f"；显性期平均再投资率 {reinv_rate:.1%}；显性期新增营收的税后回报 "
          f"{base['margin'][-1] * (1 - base['tax']) / base['k']:.0%}，终值期 {base['ronic']:.0%}")

    # 交叉验证
    np_norm = normalized_np_2026(base)
    ev = mcap - net_cash_adj(base['reserve']) - dongpeng_value(base['dp_haircut'])
    print(f"交叉验证：市值/2026 正常化归母净利 = {mcap / np_norm:.1f}×；EV/2026E 核心经营利润 = {ev / pj['ebit26']:.1f}×；"
          f"市值/归母权益 = {mcap / 47.1775:.2f}×")
    for pe in (16.1, 21.1):
        print(f"  历史 PE {pe}× × 2026 正常化归母净利 → {pe * np_norm / SHARES:.2f} 元/股")
    dps_ttm = 0.45
    print(f"  过去 12 个月每股分红 {dps_ttm} → 股息率 {dps_ttm / PRICE:.2%}（无回购）；"
          f"按 2026 正常化归母净利 90% 分配、剔除回购股本 → 每股 {0.9 * np_norm / SHARES_EX:.3f}，"
          f"股息率 {0.9 * np_norm / SHARES_EX / PRICE:.2%}")
    dps_fwd = 0.9 * np_norm / SHARES_EX
    print(f"  股利折现（9%，增长 2%，另加经调整净现金与东鹏合立）→ "
          f"{dps_fwd / (COE - 0.02) * SHARES_EX / SHARES + (net_cash_adj(base['reserve']) + dongpeng_value(base['dp_haircut'])) / SHARES:.2f} 元/股")

    # 证伪条件触发后的 V（9%）
    f1 = variant(base, h2_rev=30.0, h2_margin=0.150, growth=[-0.06, -0.02, 0.02, 0.03, 0.03],
                 margin=[0.140, 0.143, 0.148, 0.152, 0.155])
    f2 = variant(base, margin=[m - 0.015 for m in base['margin']], h2_margin=base['h2_margin'] - 0.010)
    f3_loss = 2.5
    f4 = variant(base, growth=[0.04, 0.04, 0.04, 0.035, 0.03], margin=[0.165, 0.170, 0.175, 0.178, 0.180])
    v_f1 = equity_value(f1, COE)['v']
    v_f2 = equity_value(f2, COE)['v']
    v_f3 = equity_value(variant(base, dp_haircut=0.6), COE)['v'] - f3_loss / SHARES
    v_f4 = equity_value(f4, COE)['v']
    print(f"证伪触发后 V：F1 需求继续下台阶 {v_f1:.2f}；F2 毛利率跌破 39.5% {v_f2:.2f}；"
          f"F3 资本配置失误 {v_f3:.2f}；F4 恢复增长且利润率回升 {v_f4:.2f}")

    # 敏感性（基准情景，9%）
    s1 = equity_value(variant(base, floor=0.80), COE)['v']
    s2 = equity_value(variant(base, reserve=0.0, dp_haircut=0.0), COE)['v']
    s3 = equity_value(variant(base, tg=0.025), COE)['v']
    s4 = equity_value(variant(base, margin=[m + 0.01 for m in base['margin']]), COE)['v']
    print(f"敏感性（基准 9%）：净再投资下限 0.8 亿 → {s1:.2f}；不留经营备付且东鹏合立按税后账面 → {s2:.2f}；"
          f"终值增长 2.5% → {s3:.2f}；2027-2031 利润率各 +1 个百分点 → {s4:.2f}")

    # 2026 三季度预估（基准下半年拆分：三季度占下半年营收 39%，核心经营利润率 18.6%）
    q3_rev = base['h2_rev'] * 12.891 / H2_2025_REV
    q3_ebit = q3_rev * 0.186
    q3_deduct = (q3_ebit + 0.03) * (1 - base['tax'])
    print(f"2026Q3 预估：营收 {q3_rev:.2f}（同比 {q3_rev / 12.891 - 1:+.1%}），核心经营利润 {q3_ebit:.2f}，"
          f"扣非归母约 {q3_deduct:.2f}（2025Q3 为 2.216）；前三季度扣非约 {2.154 + q3_deduct:.2f}")


if __name__ == '__main__':
    main()
