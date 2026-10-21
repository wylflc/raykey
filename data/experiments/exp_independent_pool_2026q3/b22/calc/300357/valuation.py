#!/usr/bin/env python3
"""我武生物（300357）独立估值：所有者收益 DCF（归母口径）+ 经调整净现金 + 非经营资产。

运行：python3 valuation.py
金额单位：亿元；每股：元。价格日 2026-10-21，估值时点取 2026.80。
输入全部写在本脚本内，出处见正文「来源」与 json 的 spot_checks。
"""

PRICE = 19.30
SHARES = 5.23584          # 亿股，总股本 523,584,000 股（无回购专户股份、无拟注销股份）
T0 = 2026.80              # 估值时点（2026-10-21）
COE = 0.09

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1 报告第 20、90、97、105-107 页）
FIN_ASSETS = {
    "货币资金": 8.8872,
    "交易性金融资产（银行理财）": 4.5698,
    "一年内到期的非流动资产（大额存单）": 1.0738,
    "其他债权投资（大额存单）": 1.0274,
}
DEBT_SHORT_LOAN = 0.0500      # 短期借款（信用借款）
DIVIDEND_PAYABLE = 0.7854     # 应付股利：2025 年度每 10 股 1.50 元，2026-07-09 已派
OPERATING_RESERVE = 0.60      # 经营备付：约 1 个月付现成本
LEASE_LIAB = 0.0886 + 0.0443  # 租赁负债（含一年内到期）：净利润已扣使用权资产折旧与租赁利息，只列示不扣
MINORITY_EQUITY = 0.864       # 少数股东权益（干细胞 21.45%、火蝾螈 48.94%），列示
LTEI_BOOK = {"超级灵魂（39.47%）": 1.4781, "凯屹医药（35.02%）": 0.7103}

# ---------------------------------------------------------------- 2026 年 H1 实际（2026H1 报告第 9-10、16、47、111-112 页）
H1_REV = 5.1416
H1_REV_MITE, H1_REV_ART = 4.7013, 0.3559        # 粉尘螨滴剂、黄花蒿花粉变应原舌下滴剂
H1_PARENT_NP = 2.1345
H1_ONE_OFF = 0.2874 + 0.0077 * 0.85              # 超级灵魂丧失控制权重估利得（不计税）+ 非经常性补助（税后）
H1_FIN_PRETAX = 0.09175 + 0.01610 + 0.01388 + 0.03313 - 0.00066   # 利息收入+大额存单利息+理财收益+公允价值变动-借款利息
H1_ASSOC = -0.02645                              # 权益法投资损益
# H1 核心归母（剔除一次性、金融收益、联营损益）
H1_CORE = H1_PARENT_NP - H1_ONE_OFF - H1_FIN_PRETAX * 0.85 - H1_ASSOC

# ---------------------------------------------------------------- 2025 年 H2 基数（2025 年报第 9、19 页；2025 半年度业绩预告；2026-04-24、08-28 投关记录）
H2_25 = {"mite": 9.9010 - 4.5466, "art": 0.54348 - 0.21021, "other": (10.6240 - 4.8424) - (9.9010 - 4.5466) - (0.54348 - 0.21021)}
H2_25_COST = {"cogs": 0.2686, "sell": 2.1972, "admin": 0.4359, "rd": 0.5827}
VAT_PRICE_FACTOR = 1.03 * 1.03 / 1.13            # 3% 简易征收改 13%，出厂含税价上调约 3%：不含税单价 ×0.9389

TAX = 0.15
REV_OTHER_GROWTH = 0.10


def h2_2026(vol):
    """2026 年 H2 估计：vol 为粉尘螨滴剂销量同比（价格系数按增值税切换折算）。"""
    mite = H2_25["mite"] * (1 + vol) * VAT_PRICE_FACTOR
    art_g = {0.01: 1.25, 0.05: 1.40, 0.09: 1.55}[vol]
    art = H2_25["art"] * art_g
    other = H2_25["other"]
    rev = mite + art + other
    sell_g = {0.01: 1.03, 0.05: 1.04, 0.09: 1.05}[vol]
    cogs = 0.047 * rev
    taxes = 0.095
    sell = H2_25_COST["sell"] * sell_g
    admin = H2_25_COST["admin"] * 1.08
    rd = H2_25_COST["rd"] * 0.95
    ebit = rev - cogs - taxes - sell - admin - rd
    pretax = ebit + 0.030 - 0.005 - 0.035          # 经常性其他收益、信用减值、捐赠
    core = pretax * (1 - TAX) + 0.045              # 少数股东分担的子公司亏损
    return dict(rev=rev, mite=mite, art=art, other=other, cogs=cogs, taxes=taxes, sell=sell,
                admin=admin, rd=rd, ebit=ebit, core=core)


H1_SURCHARGE_BENEFIT = 0.03 * 0.85               # H1 留抵进项冲减附加税的一次性好处（正常化扣回）
FIN_2026_AFTER_TAX = H1_FIN_PRETAX * 0.85 + 0.135 * 0.85
ASSOC_2026 = H1_ASSOC - 0.05

SCEN = {
    # 熊：ACARIZAX（ALK/金赛）2028 年前后获批后份额与价格承压，粉尘螨收入 2029-2030 年下滑；销售费用率每年 +0.5pp
    "bear": dict(p=0.30, vol26=0.01,
                 mite_g=[0.03, 0.01, -0.02, -0.02, 0.00], art_g=[0.20, 0.15, 0.10, 0.08, 0.06],
                 sell_ratio_step=+0.005, rd_g=[0.06] * 5, rr=0.05, g_term=0.015, rr_term=0.10, ltei_pct=0.2),
    # 基准：2027 年仍无舌下片竞品，2028 年起竞品分流，粉尘螨增速 7%→4%；黄花蒿高增长逐年回落
    "base": dict(p=0.50, vol26=0.05,
                 mite_g=[0.07, 0.06, 0.04, 0.04, 0.04], art_g=[0.35, 0.28, 0.22, 0.18, 0.15],
                 sell_ratio_step=0.0, rd_g=[0.08, 0.06, 0.06, 0.06, 0.06], rr=0.08, g_term=0.025, rr_term=0.10, ltei_pct=0.5),
    # 牛：两家共同教育市场，渗透率加快，粉尘螨增速 10%→7%，屋尘螨膜剂接力；销售费用率每年 -0.5pp
    "bull": dict(p=0.20, vol26=0.09,
                 mite_g=[0.10, 0.09, 0.08, 0.07, 0.07], art_g=[0.45, 0.35, 0.30, 0.25, 0.20],
                 sell_ratio_step=-0.005, rd_g=[0.08] * 5, rr=0.10, g_term=0.025, rr_term=0.10, ltei_pct=0.8),
}
COGS_R, TAXES_R, ADMIN_G, OTHER_RECUR, MINORITY_ADD = 0.047, 0.017, 0.05, -0.05, 0.09


def net_cash_adj():
    return sum(FIN_ASSETS.values()) - DEBT_SHORT_LOAN - DIVIDEND_PAYABLE - OPERATING_RESERVE


def build(s):
    h2 = h2_2026(s["vol26"])
    core26 = H1_CORE + h2["core"] - H1_SURCHARGE_BENEFIT
    norm26 = core26 + FIN_2026_AFTER_TAX + ASSOC_2026
    rev = {"mite": H1_REV_MITE + h2["mite"], "art": H1_REV_ART + h2["art"],
           "other": (H1_REV - H1_REV_MITE - H1_REV_ART) + h2["other"]}
    rev26 = sum(rev.values())
    sell_ratio = (1.9357 + h2["sell"]) / rev26
    admin = 0.4191 + h2["admin"]
    rd = 0.4790 + h2["rd"]
    years, core, rev_path = [], [], []
    for i in range(5):
        rev["mite"] *= 1 + s["mite_g"][i]
        rev["art"] *= 1 + s["art_g"][i]
        rev["other"] *= 1 + REV_OTHER_GROWTH
        r = sum(rev.values())
        sell_ratio += s["sell_ratio_step"]
        admin *= 1 + ADMIN_G
        rd *= 1 + s["rd_g"][i]
        ebit = r * (1 - COGS_R - TAXES_R - sell_ratio) - admin - rd
        c = (ebit + OTHER_RECUR) * (1 - TAX) + MINORITY_ADD
        years.append(2027 + i); core.append(c); rev_path.append(r)
    # 2032-2036：增速从 2031 年线性收敛到终值增速
    g5 = core[-1] / core[-2] - 1
    for k in range(1, 6):
        g = g5 + (s["g_term"] - g5) * k / 5
        core.append(core[-1] * (1 + g)); years.append(2031 + k)
    rr_path = [s["rr"]] * 5 + [s["rr"] + (s["rr_term"] - s["rr"]) * k / 5 for k in range(1, 6)]
    oe = [c * (1 - rr) for c, rr in zip(core, rr_path)]
    h2_oe = (h2["core"] - H1_SURCHARGE_BENEFIT) * (1 - s["rr"])
    growth5 = [core[0] / core26 - 1] + [core[i] / core[i - 1] - 1 for i in range(1, 5)]
    return dict(h2=h2, core26=core26, norm26=norm26, rev26=rev26, years=years, core=core, oe=oe,
                h2_oe=h2_oe, rev_path=rev_path, growth5=growth5, rr_path=rr_path)


def value(s, m, r):
    pv = m["h2_oe"]
    for y, f in zip(m["years"], m["oe"]):
        pv += f / (1 + r) ** (y - (T0 - 0.5))
    oe_next = m["core"][-1] * (1 + s["g_term"]) * (1 - s["rr_term"])
    tv = oe_next / (r - s["g_term"])
    pv_tv = tv / (1 + r) ** (m["years"][-1] - (T0 - 0.5))
    non_op = sum(LTEI_BOOK.values()) * s["ltei_pct"]
    eq = pv + pv_tv + net_cash_adj() + non_op
    return dict(eq=eq, ps=eq / SHARES, pv_ops=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), non_op=non_op)


def solve(fn, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (fn(mid) - target) * (fn(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def reverse_dcf(base_s, base_m):
    """现价隐含：(a) 2027-2036 核心归母恒定增速 g（终值 2.5%）；(b) 自 2027 年起的永续增速。"""
    target = PRICE * SHARES

    def v_const(g):
        core, c = [], base_m["core26"]
        for _ in range(10):
            c *= 1 + g; core.append(c)
        mm = dict(base_m, core=core, oe=[x * (1 - rr) for x, rr in zip(core, base_m["rr_path"])])
        return value(base_s, mm, COE)["eq"]

    g10 = solve(v_const, -0.10, 0.30, target)
    oe27 = base_m["oe"][0]
    fixed = base_m["h2_oe"] + net_cash_adj() + sum(LTEI_BOOK.values()) * base_s["ltei_pct"]

    def v_perp(g):
        return fixed + oe27 / (COE - g) / (1 + COE) ** (2027 - (T0 - 0.5))

    gp = solve(v_perp, -0.05, 0.085, target)
    return g10, gp


def main():
    nc = net_cash_adj()
    print("=== 我武生物 300357 独立估值（价格日 2026-10-21，现价 %.2f 元，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("金融资产合计 %.3f 亿；经调整净现金 %.3f 亿（扣短借 %.3f、应付股利 %.3f、经营备付 %.2f）；租赁负债 %.3f 只列示；少数股东权益 %.3f"
          % (sum(FIN_ASSETS.values()), nc, DEBT_SHORT_LOAN, DIVIDEND_PAYABLE, OPERATING_RESERVE, LEASE_LIAB, MINORITY_EQUITY))
    print("H1 2026 核心归母（剔一次性/金融收益/联营）%.3f；H1 税前金融收益 %.3f" % (H1_CORE, H1_FIN_PRETAX))
    res, models = {}, {}
    for k, s in SCEN.items():
        m = build(s); models[k] = m
        v9, v8, v10 = value(s, m, COE), value(s, m, 0.08), value(s, m, 0.10)
        res[k] = (v9, v8, v10)
        h2 = m["h2"]
        print("\n[%s] p=%.2f  2026 正常化归母 %.3f（核心 %.3f + 金融税后 %.3f + 联营 %.3f）；2026 营收 %.2f；H2 营收 %.3f、H2 核心归母 %.3f"
              % (k, s["p"], m["norm26"], m["core26"], FIN_2026_AFTER_TAX, ASSOC_2026, m["rev26"], h2["rev"], h2["core"]))
        print("  核心归母 2027-2031：" + "、".join("%.2f" % c for c in m["core"][:5])
              + "；增速 " + "、".join("%.1f%%" % (g * 100) for g in m["growth5"]))
        print("  营收 2027-2031：" + "、".join("%.2f" % r for r in m["rev_path"]))
        print("  2032-2036 核心归母：" + "、".join("%.2f" % c for c in m["core"][5:]) + "；终值增速 %.1f%%，再投资率 %.0f%%→%.0f%%"
              % (s["g_term"] * 100, s["rr"] * 100, s["rr_term"] * 100))
        print("  V(9%%)=%.2f 元（经营现值 %.1f 亿，终值现值 %.1f 亿，终值占经营价值 %.0f%%，净现金 %.1f，非经营 %.2f）；V(8%%)=%.2f；V(10%%)=%.2f"
              % (v9["ps"], v9["pv_ops"], v9["pv_tv"], v9["tv_share"] * 100, nc, v9["non_op"], v8["ps"], v10["ps"]))
    vw = sum(SCEN[k]["p"] * res[k][0]["ps"] for k in SCEN)
    vw8 = sum(SCEN[k]["p"] * res[k][1]["ps"] for k in SCEN)
    vw10 = sum(SCEN[k]["p"] * res[k][2]["ps"] for k in SCEN)
    pv = PRICE / vw
    print("\n加权 V(9%%)=%.2f 元；P/V=%.3f；加权 V(8%%)=%.2f；加权 V(10%%)=%.2f" % (vw, pv, vw8, vw10))
    alt = 0.25 * res["bear"][0]["ps"] + 0.50 * res["base"][0]["ps"] + 0.25 * res["bull"][0]["ps"]
    print("对照：概率取 0.25/0.50/0.25 时加权 V=%.2f 元，P/V=%.3f；无回购专户股份，剔除口径 V 不变" % (alt, PRICE / alt))
    norm = {k: models[k]["norm26"] for k in SCEN}
    print("2026 正常化归母（含净利息、剔一次性）：熊 %.2f / 基准 %.2f / 牛 %.2f 亿" % (norm["bear"], norm["base"], norm["bull"]))
    bm0 = models["base"]
    reinv = [SCEN["base"]["rr"] * c for c in [bm0["core26"]] + bm0["core"][:4]]
    inc_ret = (bm0["core"][4] - bm0["core26"]) / sum(reinv)
    print("基准所有者收益增速 2027-2031：" + "、".join("%.3f" % g for g in bm0["growth5"])
          + "；再投资率 %.0f%%；2026-2030 累计再投资 %.2f 亿，对应 2031 年较 2026 年核心归母增量 %.2f 亿，增量回报 %.2f"
          % (SCEN["base"]["rr"] * 100, sum(reinv), bm0["core"][4] - bm0["core26"], inc_ret))

    bs, bm = SCEN["base"], models["base"]
    irr = solve(lambda r: value(bs, bm, r)["eq"], 0.03, 0.30, PRICE * SHARES)
    g10, gp = reverse_dcf(bs, bm)
    print("基准情景现价隐含回报（IRR）%.2f%%" % (irr * 100))
    print("反向 DCF：现价隐含 2027-2036 核心归母年增速 %.1f%%（终值 2.5%%）；或自 2027 年所有者收益 %.2f 亿起的永续增速 %.2f%%"
          % (g10 * 100, bm["oe"][0], gp * 100))
    # 交叉验证
    ev = PRICE * SHARES - nc - sum(LTEI_BOOK.values()) * bs["ltei_pct"]
    ebit26 = 2.0241 + bm["h2"]["ebit"]
    print("交叉：市值 %.2f 亿；P/E(2026 正常化基准) %.1f×；EV %.1f 亿；EV/EBIT(2026E 核心) %.1f×；股息率(过去 12 个月 0.25 元) %.2f%%"
          % (PRICE * SHARES, PRICE * SHARES / norm["base"], ev, ev / ebit26, 0.25 / PRICE * 100))
    for lab, th in (("明显低估(≤0.75)", 0.75), ("温和低估(≤0.90)", 0.90), ("大致合理上沿(≤1.10)", 1.10)):
        print("  V 不变时 %s 的价格 ≤ %.2f 元" % (lab, vw * th))
    # 证伪情形：
    fz = {}
    # F1：基准增速路径不变，但粉尘螨 2027-2028 增速降到 2%（竞品舌下片获批 / 价格政策）
    s1 = dict(bs, mite_g=[0.02, 0.02, 0.03, 0.03, 0.03]); m1 = build(s1)
    fz["F1 粉尘螨 2027-2028 增速≤2%"] = sum(SCEN[k]["p"] * (value(s1, m1, COE)["ps"] if k == "base" else res[k][0]["ps"]) for k in SCEN)
    # F2：熊情景概率升到 50%（基准 40%、牛 10%）
    fz["F2 熊情景升至 50%"] = 0.5 * res["bear"][0]["ps"] + 0.4 * res["base"][0]["ps"] + 0.1 * res["bull"][0]["ps"]
    # F2b：熊情景为既成事实（ACARIZAX 获批且粉尘螨收入同比转负）
    fz["F2b 熊情景兑现"] = res["bear"][0]["ps"]
    # F3：现金被投向低回报项目：经调整净现金按 70% 计价
    fz["F3 现金按 70% 计价"] = vw - 0.3 * nc / SHARES
    # F4：粉尘螨销量年化增速回到 10% 以上并持续（牛情景权重提到 50%）
    fz["F4 牛情景升至 50%"] = 0.1 * res["bear"][0]["ps"] + 0.4 * res["base"][0]["ps"] + 0.5 * res["bull"][0]["ps"]
    # 三季报核对点：Q3 营收约占 H2 的 63%，Q3 扣非约占 H2 扣非口径的 82%（2025 年 Q3/H2 比例）
    for k in SCEN:
        h2 = models[k]["h2"]
        kf_h2 = h2["core"] + 0.08 - 0.05 + 0.03   # 加回银行利息（税后）、联营亏损、捐赠（扣非口径）
        print("  三季报核对[%s]：Q3 营收约 %.2f 亿（同比 %+.1f%%），Q3 扣非约 %.2f 亿（同比 %+.1f%%）"
              % (k, h2["rev"] * 0.63, (h2["rev"] * 0.63 / 3.6912 - 1) * 100, kf_h2 * 0.82, (kf_h2 * 0.82 / 1.6743 - 1) * 100))
    for k, v in fz.items():
        print("  证伪 %s：V≈%.2f 元，P/V=%.2f" % (k, v, PRICE / v))
    return dict(res=res, vw=vw, pv=pv, vw8=vw8, vw10=vw10, irr=irr, g10=g10, gp=gp, norm=norm, models=models, fz=fz)


if __name__ == "__main__":
    main()
