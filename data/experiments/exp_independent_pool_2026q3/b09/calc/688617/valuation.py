# -*- coding: utf-8 -*-
"""惠泰医疗（688617）独立估值：所有者收益 DCF（无杠杆口径，净现金为正）。

运行：python3 valuation.py
金额单位亿元，每股价值单位元。全部输入写在本脚本内，出处见正文「来源」。
"""

# ---------------- 快照 ----------------
PRICE = 252.34                 # 2026-10-20 收盘（brief）
SHARES = 1.41529162            # 总股本（亿股），含回购专户 2,301,876 股（buyback_20260521 第 3 页；holders_20261021_723667 第 5 页）
TREASURY = 0.02301876          # 回购专户股份，用于股权激励，不注销
SHARES_EX_T = SHARES - TREASURY

# ---------------- 2026H1 资产负债表（2026H1_report 第 74-76 页、第 29 页） ----------------
CASH = 13.48558                # 货币资金
TFA = 0.75588                  # 交易性金融资产（理财）
RESTRICTED = 0.18365           # 保函保证金及利息（受限）
OP_RESERVE = 1.50              # 经营备付：约 1 个月付现成本（2025 年付现成本约 17.7 亿元/年）
DEBT_LIKE = 0.09158 + 0.04578 + 0.30   # 一年内到期非流动负债 + 租赁负债 + 皓影向上海惠股借款（其他应付款内，第 57-58、157 页）
NET_CASH_ADJ = CASH + TFA - RESTRICTED - OP_RESERVE - DEBT_LIKE
NONOP = 0.48470                # 其他权益工具投资（公允价值，第 30 页）；联营投资收益留在利润内，不另加

# ---------------- 2026 年正常化归母净利 ----------------
H1_DEDUCT = 5.28772            # 2026H1 扣非归母（第 7 页）
H1_FX_LOSS = 0.15002           # 2026H1 汇兑损失（财务费用附注，第 167 页），税前
TAX = 0.15                     # 高新技术企业税率
H1_NORM = H1_DEDUCT + H1_FX_LOSS * (1 - TAX)
H2_2025_DEDUCT = 7.90876 - 4.10821   # 2025 全年扣非 − 2025H1 扣非（年报、2025 中报，F10）
H2_2025_FX_LOSS = 0.0744       # 2025 全年汇兑损失约 0.053，H1 为汇兑收益 0.021，故 H2 损失约 0.074（推算），税前
H2_2025_NORM = H2_2025_DEDUCT + H2_2025_FX_LOSS * (1 - TAX)
INT_AT = (0.05108 + 0.03490 + 0.00588) * 2 * (1 - TAX)   # 年化利息与理财收益（税后），计入正常化净利，DCF 中剔除以免与净现金重复

COE = 0.09
TG = 0.025                     # 终值增长
ROIIC_T = 0.25                 # 终值阶段增量回报 → 终值再投资率 10%
T0 = 0.70                      # 2027 年现金流年中距估值日（2026-10-20）约 0.70 年

SCEN = {
    # h2_g: 2026H2 正常化扣非同比；g26: 2026 全年增长（用于 2026H2 再投资率）；path: 2027-2035 经营口径归母净利增速；roiic: 增量回报
    'bear': dict(p=0.25, h2_g=0.14, g26=0.20, roiic=0.40,
                 path=[0.08, 0.09, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04]),
    'base': dict(p=0.50, h2_g=0.25, g26=0.24, roiic=0.65,
                 path=[0.19, 0.18, 0.17, 0.15, 0.13, 0.11, 0.09, 0.07, 0.05]),
    'bull': dict(p=0.25, h2_g=0.32, g26=0.26, roiic=0.80,
                 path=[0.24, 0.23, 0.22, 0.20, 0.17, 0.14, 0.11, 0.08, 0.06]),
}


def norm_np_2026(s):
    return H1_NORM + H2_2025_NORM * (1 + s['h2_g'])


def ops_pv(s, coe=COE, detail=False):
    """经营所有者收益现值（不含净现金），返回 (现值, 终值现值占比, 明细)。"""
    np26 = norm_np_2026(s)
    np_op = np26 - INT_AT
    h2_op = np_op - (H1_NORM - INT_AT / 2)
    rr26 = s['g26'] / s['roiic']
    pv = h2_op * (1 - rr26)          # 2026H2 所有者收益，估值日前后，不折现
    rows = []
    t = T0
    for i, g in enumerate(s['path']):
        np_op *= 1 + g
        rr = max(g / s['roiic'], TG / ROIIC_T)
        oe = np_op * (1 - rr)
        pv += oe / (1 + coe) ** t
        rows.append((2027 + i, np_op, rr, oe))
        t += 1
    oe_next = np_op * (1 + TG) * (1 - TG / ROIIC_T)
    tv = oe_next / (coe - TG)
    tv_pv = tv / (1 + coe) ** (t - 0.5)
    total = pv + tv_pv
    return total, tv_pv / total, rows


def value_per_share(s, coe=COE, shares=SHARES):
    ops, tvs, _ = ops_pv(s, coe)
    return (ops + NET_CASH_ADJ + NONOP) / shares


def weighted(coe=COE, weights=None, shares=SHARES):
    w = weights or {k: v['p'] for k, v in SCEN.items()}
    return sum(w[k] * value_per_share(SCEN[k], coe, shares) for k in SCEN)


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print('=== 输入与正常化 ===')
    print(f'经调整净现金 {NET_CASH_ADJ:.2f} 亿元（现金类 {CASH + TFA:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {OP_RESERVE:.2f} − 有息及类债务 {DEBT_LIKE:.2f}）；非经营资产 {NONOP:.2f}')
    print(f'2026H1 正常化扣非 {H1_NORM:.3f}（扣非 {H1_DEDUCT:.3f} + 汇兑损失税后 {H1_FX_LOSS * (1 - TAX):.3f}）；2025H2 正常化扣非 {H2_2025_NORM:.3f}；年化税后利息理财 {INT_AT:.3f}')
    for k, s in SCEN.items():
        print(f'{k}: 2026 正常化归母净利 {norm_np_2026(s):.2f} 亿元（2026H2 同比 {s["h2_g"]:+.0%}）')

    print('\n=== 三情景（股权成本 9%） ===')
    res = {}
    for k, s in SCEN.items():
        ops, tvs, rows = ops_pv(s)
        v = value_per_share(s)
        res[k] = v
        print(f'{k}: V = {v:.1f} 元/股，权重 {s["p"]:.2f}，经营价值 {ops:.1f} 亿元，终值占比 {tvs:.0%}，ROIIC {s["roiic"]:.0%}')
        for y, npv, rr, oe in rows[:5]:
            print(f'   {y}: 经营口径归母净利 {npv:.2f}，再投资率 {rr:.0%}，所有者收益 {oe:.2f}')
        print(f'   2035: 经营口径归母净利 {rows[-1][1]:.2f}；之后增长 {TG:.1%}，终值再投资率 {TG / ROIIC_T:.0%}')
    vw = weighted()
    print(f'\n加权 V = {vw:.1f} 元/股；P/V = {PRICE / vw:.3f}')
    vw_ex = weighted(shares=SHARES_EX_T)
    print(f'剔除回购专户股份（{SHARES_EX_T:.4f} 亿股）：加权 V = {vw_ex:.1f}，P/V = {PRICE / vw_ex:.3f}')

    print('\n=== 股权成本敏感性（加权） ===')
    for coe in (0.08, 0.10):
        vv = weighted(coe)
        parts = '，'.join(f'{k} {value_per_share(SCEN[k], coe):.1f}' for k in SCEN)
        print(f'CoE {coe:.0%}: 加权 V = {vv:.1f}（{parts}），P/V = {PRICE / vv:.3f}')

    mcap = PRICE * SHARES
    base = SCEN['base']
    irr = solve(lambda r: ops_pv(base, r)[0] + NET_CASH_ADJ + NONOP, 0.03, 0.20, mcap)
    print(f'\n现价隐含回报（基准情景现金流 + 终值 + 净现金 = 市值 {mcap:.1f} 亿元）：{irr:.2%}')

    # 反向 DCF 1：2027-2035 恒定增速 g（ROIIC 65%），之后 2.5%
    def v_const(g):
        s = dict(base, path=[g] * 9)
        return value_per_share(s)
    g_imp = solve(v_const, 0.0, 0.40, PRICE)
    print(f'反向 DCF：现价隐含 2027-2035 年经营口径归母净利年均增长 {g_imp:.1%}（ROIIC 65%，之后 2.5%）')
    # 反向 DCF 2：以基准 2027 所有者收益计的永续增速
    oe27 = ops_pv(base)[2][0][3]
    ev_ops = mcap - NET_CASH_ADJ - NONOP
    g_perp = COE - oe27 / ev_ops
    print(f'反向 DCF：以基准 2027 年所有者收益 {oe27:.2f} 亿元计，现价隐含永续增速 {g_perp:.1%}')

    print('\n=== 交叉验证 ===')
    np26b = norm_np_2026(base)
    print(f'现价 PE（2026 正常化基准 {np26b:.2f}）= {mcap / np26b:.1f}x；加权 V 对应 PE = {vw * SHARES / np26b:.1f}x')
    np27b = (np26b - INT_AT) * 1.19 + INT_AT
    print(f'现价 PE（2027 基准 {np27b:.2f}）= {mcap / np27b:.1f}x')
    ebit26 = (np26b - INT_AT) / (1 - 0.13)
    print(f'EV/EBIT（EV {ev_ops:.1f}，2026E EBIT 约 {ebit26:.1f}）= {ev_ops / ebit26:.1f}x')
    div_bb = 1.3917 + 4.5003
    print(f'2026 年股息（2025 年度 1 元/股，1.39 亿元）+ 回购 4.50 亿元 = {div_bb:.2f} 亿元，收益率 {div_bb / mcap:.2%}')
    adj = 471.12 / (1.45 * 1.45)
    print(f'迈瑞 2024-01 控制权受让价 471.12 元/股，按两次 10 转 4.5 复权约 {adj:.1f} 元；2026-10-20 深迈控大宗受让价 222.57 元')

    print('\n=== 分档价格（V 不变） ===')
    print(f'明显低估 ≤ {0.75 * vw:.1f}；温和低估 {0.75 * vw:.1f}～{0.90 * vw:.1f}；大致合理 {0.90 * vw:.1f}～{1.10 * vw:.1f}；偏贵 > {1.10 * vw:.1f}')

    print('\n=== 证伪触发后的 V ===')
    f = {
        'F1 福建续标纳入 PFA 且降幅 ≥50% 或主力品类未中选': dict(bear=0.50, base=0.40, bull=0.10),
        'F2 2026 年营收 < 31.0 亿元或 2026Q3 营收同比 < 15%': dict(bear=0.40, base=0.50, bull=0.10),
        'F3 2027H1 毛利率 < 68%': dict(bear=0.50, base=0.50, bull=0.00),
        'F5 2027 年归母净利 ≥ 13.5 亿元且毛利率 ≥ 72%': dict(bear=0.00, base=0.50, bull=0.50),
    }
    for name, w in f.items():
        print(f'{name}: V = {weighted(weights=w):.1f}')
    print(f'F4 收购成正辉家族所持皓影股权或家族企业资产，或 2027 年与迈瑞关联交易预计 > 1.5 亿元且新增迈瑞代理销售（治理折价 8%）: V = 加权 V × 0.92 = {vw * 0.92:.1f}')


if __name__ == '__main__':
    main()
