#!/usr/bin/env python3
"""603501 豪威集团 独立估值（OI-291 b11，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位亿元，股本亿股，每股价值元/股。所有输入写在本脚本内，出处见正文
data/experiments/exp_independent_pool_2026q3/b11/companies/603501_豪威集团.md。

方法：设计业务（图像传感器+模拟+显示+设计服务）所有者收益 DCF（无杠杆，
股权成本 9%，终值增长 <= 2.5%，再投资 = 增长 / 增量回报）；代理销售业务按
稳态所有者收益单独估值；加经调整净现金（不含可转债）与折价后的非经营资产；
可转债逐情景按债底现值扣除与全部转股两种算法取低。
"""

PRICE = 76.91                      # 2026-10-20 收盘，A 股
SHARES_TOTAL = 12.5839             # A+H 总股本（2026-10-15 为 1,258,390,662 股，含回购专户）
TO_CANCEL = 0.08750205             # 2026-08-04 董事会拟注销的回购股份（待股东会）
SHARES = SHARES_TOTAL - TO_CANCEL  # 每股价值所用股本 12.4964 亿股
COE = 0.09

# ---------------- 资产负债表（2026-06-30，2026H1 报告） ----------------
CASH = 149.36                      # 货币资金（境外 104.40）
RESTRICTED = 0.21                  # 受限货币资金
REV_TTM = 289.24
OP_RESERVE = 0.05 * REV_TTM        # 经营备付：TTM 营收 5%
DEBT = {
    "短期借款(含票据贴现3.49)": 32.83,
    "长期借款": 25.36,
    "一年内到期的长期借款": 29.99,
    "租赁负债(含一年内到期0.45)": 1.03 + 0.45,
}
DEBT_LIKE = {
    "或有对价(湖南芯力特)": 1.00,
    "不确定税项预计负债": 4.99,
    "应付股利": 0.05,
}
POST_BS = 8.13 - 6.21              # 7 月支付的回购款（对应拟注销股份，6 月末尚未付清部分）
DEBT_TOTAL = sum(DEBT.values())
DEBT_LIKE_TOTAL = sum(DEBT_LIKE.values())
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DEBT_TOTAL - DEBT_LIKE_TOTAL - POST_BS

# 可转债（韦尔转债 113616）：2026-06-30 未转股面值 24.32336 亿元，2026-12-27 到期，
# 到期按面值 110%（含最后一期利息）赎回；转股价 159.02 元/股。
CB_FACE = 24.32336
CB_REDEEM = CB_FACE * 1.10
CB_YEARS = 68 / 365                # 2026-10-20 至 2026-12-27
CB_PV = CB_REDEEM / (1.02 ** CB_YEARS)
CONV_PX = 159.02
CONV_SHARES = CB_FACE / CONV_PX    # 全部转股新增股本（亿股）

# 非经营资产账面值（2026-06-30）
NONOP_BOOK = {
    "交易性金融资产(上市股权)": 6.43,
    "其他非流动金融资产(非上市股权16.37+产业基金28.00)": 44.37,
    "其他权益工具投资(荣芯10亿等)": 10.04,
    "长期股权投资(联营)": 6.44,
}
NONOP_KEYS = list(NONOP_BOOK)

# 存货：净额 91.87；正常周转 190 天 × 2026E 设计业务成本 146 亿元
INV_NET = 91.87
INV_NORMAL = 190 / 365 * 146.0
INV_EXCESS = INV_NET - INV_NORMAL

OTHER_INC = 0.5                    # 经常性政府补助等其他收益
T_STUB, T1 = 0.0, 0.70             # 2026H2 存根按价格日计；2027 年现金流按年中（距价格日 0.70 年）

SC = {
    "bear": dict(
        p=0.25, rev=218.0, gm=0.320, opex=0.195, imp=0.016, svc=1.3, tax=0.21,
        g=[0.00, 0.03, 0.03, 0.025, 0.025], gt=0.020, ronic=0.10,
        dist_ebit=1.5, dist_g=0.00, dist_ronic=0.08, net_int_at=1.0,
        stub_conv=0.40, inv_release=0.0,
        haircut=[0.25, 0.50, 0.70, 0.70],
        assumptions="手机CIS份额流失被确认、国内汽车需求2027年仍弱；设计收入218亿元、毛利率32%、"
                    "费用率19.5%、经常性减值1.6%、税率21%；2027年零增长、此后3%→2.5%，终值2%，增量回报10%；"
                    "超额存货不释放；非经营资产折价25%～70%"),
    "base": dict(
        p=0.50, rev=230.0, gm=0.345, opex=0.183, imp=0.013, svc=1.5, tax=0.18,
        g=[0.06, 0.06, 0.055, 0.05, 0.04], gt=0.025, ronic=0.16,
        dist_ebit=2.4, dist_g=0.02, dist_ronic=0.12, net_int_at=1.2,
        stub_conv=0.60, inv_release=0.5,
        haircut=[0.15, 0.35, 0.50, 0.50],
        assumptions="设计收入正常化230亿元（2026E约223亿元）、毛利率34.5%（=2026H1）、费用率18.3%、"
                    "经常性减值1.3%、税率18%；增长6%/6%/5.5%/5%/4%，终值2.5%，增量回报16%；"
                    "超额存货一半于2027年释放；代理EBIT 2.4亿元；非经营资产折价15%～50%"),
    "bull": dict(
        p=0.25, rev=240.0, gm=0.365, opex=0.173, imp=0.009, svc=1.8, tax=0.155,
        g=[0.10, 0.10, 0.08, 0.07, 0.06], gt=0.025, ronic=0.22,
        dist_ebit=3.2, dist_g=0.03, dist_ronic=0.15, net_int_at=1.4,
        stub_conv=0.75, inv_release=0.7,
        haircut=[0.10, 0.25, 0.40, 0.40],
        assumptions="汽车ADAS、专业影像、机器视觉与端侧AI放量，手机2028年恢复；设计收入240亿元、"
                    "毛利率36.5%（三季度指引口径延续）、费用率17.3%、减值0.9%、税率15.5%；"
                    "增长10%/10%/8%/7%/6%，终值2.5%，增量回报22%；超额存货70%释放；非经营资产折价10%～40%"),
}


def nonop_value(s):
    return sum(NONOP_BOOK[k] * (1 - h) for k, h in zip(NONOP_KEYS, s["haircut"]))


def design_ebit(s):
    return s["rev"] * (s["gm"] - s["opex"] - s["imp"]) + s["svc"] * 0.95 + OTHER_INC


def design_nopat(s):
    return design_ebit(s) * (1 - s["tax"])


def dist_nopat(s):
    return s["dist_ebit"] * (1 - s["tax"])


def normalized_np(s):
    """2026 正常化归母净利：设计 NOPAT + 代理 NOPAT + 税后净利息（剔除一次性项目）。"""
    return design_nopat(s) + dist_nopat(s) + s["net_int_at"]


def design_path(s, g_list=None, gt=None):
    """返回 (年份, NOPAT, 增长, 再投资率, 所有者收益) 列表与终值年 NOPAT。"""
    g_list = s["g"] if g_list is None else g_list
    gt = s["gt"] if gt is None else gt
    n = design_nopat(s)
    rows = []
    for i, g in enumerate(g_list):
        n *= 1 + g
        rr = g / s["ronic"]
        rows.append((2027 + i, n, g, rr, n * (1 - rr)))
    return rows, n * (1 + gt)


def op_value(s, r, g_list=None, gt=None):
    gt = s["gt"] if gt is None else gt
    rows, n_next = design_path(s, g_list, gt)
    pv = 0.0
    t = T1
    for (_, _, _, _, oe) in rows:
        pv += oe / (1 + r) ** t
        t_last = t
        t += 1
    tv = n_next * (1 - gt / s["ronic"]) / (r - gt)
    pv_tv = tv / (1 + r) ** t_last
    stub = 0.5 * (design_nopat(s) + dist_nopat(s)) * s["stub_conv"]
    inv = s["inv_release"] * INV_EXCESS / (1 + r) ** T1
    d_oe = dist_nopat(s) * (1 - s["dist_g"] / s["dist_ronic"])
    dist_val = d_oe / (r - s["dist_g"])
    return dict(flows=pv, tv=pv_tv, stub=stub, inv=inv, dist=dist_val,
                design=pv + pv_tv, total=pv + pv_tv + stub + inv + dist_val)


def equity(s, r, g_list=None, gt=None):
    ov = op_value(s, r, g_list, gt)
    base = ov["total"] + NET_CASH_ADJ + nonop_value(s)
    v_debt = (base - CB_PV) / SHARES
    v_conv = base / (SHARES + CONV_SHARES)
    return dict(ov=ov, eq_debt=base - CB_PV, v_debt=v_debt, v_conv=v_conv,
                v=min(v_debt, v_conv), v_incl_treasury=(base - CB_PV) / SHARES_TOTAL)


def weighted(r, probs=None):
    probs = probs or {k: SC[k]["p"] for k in SC}
    return sum(probs[k] * equity(SC[k], r)["v"] for k in SC)


def solve(f, lo, hi, target, iters=200):
    flo = f(lo) - target
    for _ in range(iters):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 股本与资产负债调整（亿元/亿股） ==")
    print(f"总股本(含回购专户) {SHARES_TOTAL:.4f}；拟注销 {TO_CANCEL:.4f}；估值股本 {SHARES:.4f}")
    print(f"现金 {CASH:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {OP_RESERVE:.2f} − 有息负债 {DEBT_TOTAL:.2f} "
          f"− 类债务 {DEBT_LIKE_TOTAL:.2f} − 期后回购款 {POST_BS:.2f} = 经调整净现金 {NET_CASH_ADJ:.2f}")
    print(f"可转债：面值 {CB_FACE:.4f}，到期赎回 {CB_REDEEM:.2f}，债底现值 {CB_PV:.2f}；"
          f"转股价 {CONV_PX} → 转股 {CONV_SHARES:.4f} 亿股")
    print(f"存货 {INV_NET:.2f}，正常水平 {INV_NORMAL:.2f}，超额 {INV_EXCESS:.2f}")
    print(f"非经营资产账面 {sum(NONOP_BOOK.values()):.2f}；"
          + "；".join(f"{k} 折后 {nonop_value(SC[k]):.2f}" for k in SC))

    print("\n== 2026 正常化（亿元） ==")
    for k, s in SC.items():
        print(f"{k}: 设计EBIT {design_ebit(s):.2f} → 设计NOPAT {design_nopat(s):.2f}；"
              f"代理NOPAT {dist_nopat(s):.2f}；税后净利息 {s['net_int_at']:.2f}；"
              f"正常化归母净利 {normalized_np(s):.2f}")

    print("\n== 基准情景增长路径（设计业务） ==")
    rows, n_next = design_path(SC["base"])
    for y, n, g, rr, oe in rows:
        print(f"{y}: 增长 {g:.1%}  NOPAT {n:.2f}  再投资率 {rr:.1%}  所有者收益 {oe:.2f}")
    print(f"终值年 NOPAT {n_next:.2f}，终值增长 {SC['base']['gt']:.1%}，"
          f"终值再投资率 {SC['base']['gt'] / SC['base']['ronic']:.1%}")

    print("\n== 三情景每股价值（元/股） ==")
    res = {}
    for k, s in SC.items():
        e = equity(s, COE)
        res[k] = e
        ov = e["ov"]
        share_tv = ov["tv"] / (ov["total"] + NET_CASH_ADJ + nonop_value(s) - CB_PV)
        print(f"{k} p={s['p']:.2f}: 设计DCF {ov['design']:.1f}（其中终值 {ov['tv']:.1f}）+ 2026H2存根 {ov['stub']:.1f} "
              f"+ 存货释放 {ov['inv']:.1f} + 代理 {ov['dist']:.1f} + 净现金 {NET_CASH_ADJ:.1f} "
              f"+ 非经营 {nonop_value(s):.1f}；按债务扣转债 V={e['v_debt']:.2f}，全部转股 V={e['v_conv']:.2f} "
              f"→ 取低 {e['v']:.2f}（终值占股权价值 {share_tv:.0%}；含回购专户股本口径 {e['v_incl_treasury']:.2f}）")
    vw = weighted(COE)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv:.2f}（{verdict(pv)}）")
    vw_incl = sum(SC[k]['p'] * res[k]['v_incl_treasury'] for k in SC)
    print(f"含回购专户股本(12.5839亿股)口径加权 V = {vw_incl:.2f}，P/V = {PRICE / vw_incl:.2f}")
    print("分档价格：≤0.75 → ≤{:.2f}；0.75～0.90 → {:.2f}～{:.2f}；0.90～1.10 → {:.2f}～{:.2f}".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw))

    print("\n== 股权成本敏感性 ==")
    for r in (0.08, 0.09, 0.10):
        vals = {k: equity(SC[k], r)["v"] for k in SC}
        print(f"r={r:.0%}: 熊 {vals['bear']:.2f} 基 {vals['base']:.2f} 牛 {vals['bull']:.2f} 加权 {weighted(r):.2f}")

    base = SC["base"]
    irr = solve(lambda r: equity(base, r)["v"], 0.035, 0.20, PRICE)
    print(f"\n现价隐含回报（基准情景现金流+终值+净现金）：{irr:.2%}")
    irr_w = solve(lambda r: weighted(r), 0.035, 0.20, PRICE)
    print(f"现价隐含回报（三情景加权）：{irr_w:.2%}")

    # 反向 DCF：设计业务 NOPAT 2027-2036 年恒定增长，再投资 = 增长 / 增量回报，终值 2.5%，9% 折现
    v16 = equity(base, COE, [0.159] * 10, 0.025)["v"]
    print(f"反向DCF：增量回报16%（基准）下，即使10年复合增长15.9%，V 也只有 {v16:.2f}，无解")
    g10 = solve(lambda g: equity(dict(base, ronic=0.20), COE, [g] * 10, 0.025)["v"], 0.0, 0.199, PRICE)
    print(f"反向DCF：增量回报20%，现价隐含设计业务 NOPAT 10 年复合增速 {g10:.2%}")
    g10b = solve(lambda g: equity(dict(base, ronic=0.25), COE, [g] * 10, 0.025)["v"], 0.0, 0.249, PRICE)
    print(f"反向DCF：增量回报25%，现价隐含设计业务 NOPAT 10 年复合增速 {g10b:.2%}")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES
    ev = mcap + DEBT_TOTAL + DEBT_LIKE_TOTAL + CB_PV - (CASH - RESTRICTED) - sum(NONOP_BOOK.values())
    ebit_2025 = 46.06 - 0.12 - 0.74 + (-0.74)   # 营业利润 − 投资收益 − 公允价值变动 + 财务费用（净收益为负）
    ebit_norm = design_ebit(base) + base["dist_ebit"]
    print(f"市值(估值股本) {mcap:.1f}；EV {ev:.1f}；EV/EBIT(2025 {ebit_2025:.1f}) {ev / ebit_2025:.1f}x；"
          f"EV/EBIT(正常化 {ebit_norm:.1f}) {ev / ebit_norm:.1f}x")
    print(f"市值/正常化归母净利(基准 {normalized_np(base):.2f}) {mcap / normalized_np(base):.1f}x；"
          f"市值/2025 归母 40.45 = {mcap / 40.45:.1f}x；PB(327.08) {PRICE * SHARES_TOTAL / 327.08:.2f}")
    print(f"股息率(过去12个月 0.50 元) {0.50 / PRICE:.2%}；2026 年回购 8.13 亿元 = 市值 {8.13 / mcap:.2%}；"
          f"新方案 2.5～5 亿元 = {2.5 / mcap:.2%}～{5 / mcap:.2%}；同期 H 股融资净额 46.77 亿元 = {46.77 / mcap:.2%}")
    print(f"V 对应正常化市盈率：{vw * SHARES / normalized_np(base):.1f}x（基准正常化净利）")

    print("\n== 证伪条件触发后的 V ==")
    f1 = weighted(COE, {"bear": 0.45, "base": 0.45, "bull": 0.10})
    f2 = res["bear"]["v"]
    f3 = weighted(COE, {"bear": 0.10, "base": 0.40, "bull": 0.50})
    f4 = weighted(COE, {"bear": 0.40, "base": 0.50, "bull": 0.10})
    print(f"F1 三季报毛利率<29.0% 或设计收入<57亿元：V={f1:.2f}")
    print(f"F2 2026年报存货≥95亿元且设计收入<220亿元：V={f2:.2f}（熊市情景）")
    print(f"F3 2027H1 设计收入同比≥+15% 且设计毛利率≥35.5%：V={f3:.2f}")
    print(f"F4 控股股东质押≥70%持股或新增关联方投资≥10亿元：V={f4:.2f}")
    return dict(vw=vw, pv=pv, irr=irr, g10=g10, f=(f1, f2, f3, f4))


if __name__ == "__main__":
    main()
