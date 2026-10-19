"""浙江鼎力（603338）独立估值：所有者收益 DCF、反向 DCF、隐含回报、三情景加权。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入均写在脚本内，出处见注释与正文「来源」一节。
"""

PRICE = 52.32               # 2026-10-19 收盘（brief）
SHARES = 5.06347879         # 亿股，2026H1_report 第 46 页股本 506,347,879 股
COE = 0.09                  # 股权成本基准
YEARS_TO_YE = 0.2           # 2026-10-19 至 2026-12-31 约 0.2 年
TAX = 0.15                  # 母公司高新技术企业税率，汇兑等调整项按此计税

# ---------- 2026-06-30 资产负债（2026H1_report 第 44-46 页，附注第 95-96、124、128-129 页） ----------
CASH = 48.2199              # 货币资金 4,821,986,661.28（其他货币资金仅 0.03，无受限资金，第 95、123-124 页）
TFA = 4.3239                # 交易性金融资产 432,393,767.30
TFA_EQUITY = 0.2501         # 其中宏信建发股票 25,013,032.72（第 16-17 页）
OEI = 0.1720                # 其他权益工具投资（宏信建发）17,200,642.60
DERIV_ASSET = 0.3708        # 衍生金融资产（远期外汇）
DERIV_LIAB = 0.0058         # 衍生金融负债
DEBT = {
    "短期借款": 7.1107,
    "长期借款": 2.3237,
    "一年内到期长期借款": 3.1472,   # 含上海鼎策以融资租赁款质押/保理借款，合计保证借款 4.96
    "租赁负债": 1.3092,
    "一年内到期租赁负债": 0.2196,
}
OP_RESERVE = 8.0            # 经营备付：约 1 个月现金成本（营收约 100 亿 × 8%）
# 2026-06-30 无已宣派未付股利（2025 年度 1.15 元/股已于 2026-06-26 除息发放）

gross_fin = CASH + (TFA - TFA_EQUITY) + DERIV_ASSET - DERIV_LIAB
debt_total = sum(DEBT.values())
NET_CASH_JUN = gross_fin - debt_total - OP_RESERVE
NON_OP = TFA_EQUITY + OEI   # 宏信建发股票按 6-30 公允价值

# ---------- 利润正常化 ----------
H1_REV = 54.1403            # 2026H1 营收
H1_KF = 9.6488              # 2026H1 扣非归母 964,877,333.21（第 6 页）
H1_FX = 2.8467              # 2026H1 汇兑损失 284,670,770.83（第 135 页）
H1_EXFX = H1_KF + H1_FX * (1 - TAX)

H2_25_REV = 85.7548 - 43.3612                     # 2025 下半年营收
H2_25_KF = 18.2461 - 10.5003                      # 2025 下半年扣非（年报第 7 页分季度 − 2025H1）
H2_25_FX = 0.3830 - 2.1993                        # 2025 全年汇兑收益 0.383 − 上半年收益 2.199 = 下半年损失
H2_25_EXFX = H2_25_KF - H2_25_FX * (1 - TAX)      # 约 9.29

# 三季度汇兑估计：美元中间价 6.8109(6-30) → 6.7351(9-30)，净美元货币性资产约 8.95 亿美元，
# 加欧元、英镑敞口，税前约 -0.80 亿，税后 -0.68 亿；作为一次性损失从 V 扣除
Q3_FX_AFTER_TAX = -0.80 * (1 - TAX)

CASH_INTEREST_AT = 1.60     # 现金税后净利息（存款利息约 2.0 亿/年税前，扣借款利息），DCF 中剔除以免与净现金重复

SCEN = {
    # h2_g/h2_m: 2026 下半年营收同比与扣汇兑净利率；fx_drag: 正常化口径的预期汇率拖累（税后）
    # op_fx: 熊市中经营项目的结构性汇率拖累；growth: 2027-2031 经营归母（剔现金利息）增速
    # k_up: 每增加 1 元营收需追加的营运资本+固定资产；k_down: 营收下降时营运资本释放比例
    # h2_wc: 下半年季节性营运资本回收；contingent: 美国双反追溯补税与 IEEPA 退税的净额
    "bear": dict(p=0.30, h2_g=0.03, h2_m=0.190, fx_drag=1.5, op_fx=0.7,
                 growth=[-0.15, 0.00, 0.03, 0.03, 0.03], g_t=0.020, ronic_t=0.12,
                 k_up=0.65, k_down=0.15, h2_wc=1.0, contingent=-3.0),
    "base": dict(p=0.50, h2_g=0.07, h2_m=0.210, fx_drag=0.8, op_fx=0.0,
                 growth=[-0.06, 0.07, 0.06, 0.05, 0.04], g_t=0.025, ronic_t=0.16,
                 k_up=0.55, k_down=0.30, h2_wc=1.5, contingent=-1.0),
    "bull": dict(p=0.20, h2_g=0.10, h2_m=0.220, fx_drag=0.0, op_fx=0.0,
                 growth=[0.05, 0.09, 0.08, 0.07, 0.05], g_t=0.025, ronic_t=0.18,
                 k_up=0.50, k_down=0.30, h2_wc=2.5, contingent=0.5),
}
GROWTH_CAPEX = [3.0, 1.5, 0.0, 0.0, 0.0]   # 年产 2 万台项目剩余投入（超出折旧部分），2027、2028
H2_GROWTH_CAPEX = 1.5                      # 2026 下半年项目投入
YEARS = [2027, 2028, 2029, 2030, 2031]


def build(s):
    h2_rev = H2_25_REV * (1 + s["h2_g"])
    h2_np = h2_rev * s["h2_m"]
    rev26 = H1_REV + h2_rev
    exfx26 = H1_EXFX + h2_np
    norm26 = exfx26 - s["fx_drag"]                    # 登记口径：含净利息、剔一次性
    op26 = exfx26 - CASH_INTEREST_AT - s["op_fx"]      # DCF 口径：剔现金利息
    margin = op26 / rev26
    h2_fcf = h2_np + Q3_FX_AFTER_TAX - H2_GROWTH_CAPEX + s["h2_wc"]
    net_cash_ye = NET_CASH_JUN + h2_fcf + s["contingent"] + NON_OP
    return dict(rev26=rev26, exfx26=exfx26, norm26=norm26, op26=op26, margin=margin,
                h2_fcf=h2_fcf, net_cash_ye=net_cash_ye)


def value(s, r, growth=None, g_t=None, detail=False):
    b = build(s)
    growth = s["growth"] if growth is None else growth
    g_t = s["g_t"] if g_t is None else g_t
    op_prev, rev_prev = b["op26"], b["rev26"]
    pv, rows = 0.0, []
    for i, g in enumerate(growth, start=1):
        op = op_prev * (1 + g)
        rev = op / b["margin"]
        d_rev = rev - rev_prev
        reinv = s["k_up"] * d_rev if d_rev > 0 else s["k_down"] * d_rev
        capex = GROWTH_CAPEX[i - 1] if i <= len(GROWTH_CAPEX) else 0.0
        oe = op - reinv - capex
        pv += oe / (1 + r) ** (i - 0.5)                # 年中折现
        rows.append((2026 + i, op, rev, reinv + capex, oe))
        op_prev, rev_prev = op, rev
    n = len(growth)
    op_t = op_prev * (1 + g_t)
    oe_t = op_t * (1 - g_t / s["ronic_t"])
    tv = oe_t / (r - g_t) * (1 + r) ** 0.5 / (1 + r) ** n
    equity_ye = pv + tv + b["net_cash_ye"]
    v = equity_ye / (1 + r) ** YEARS_TO_YE / SHARES
    if detail:
        return v, dict(rows=rows, pv=pv, tv=tv, tv_share=tv / (pv + tv), b=b, oe_t=oe_t)
    return v


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print("== 浙江鼎力 603338 独立估值（价格日 2026-10-19，现价 %.2f 元，股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("2026-06-30 金融资产 %.2f，有息负债 %.2f，经营备付 %.1f → 调整后净现金 %.2f；非经营资产 %.2f"
          % (gross_fin, debt_total, OP_RESERVE, NET_CASH_JUN, NON_OP))
    print("2026H1 扣非 %.2f + 汇兑损失税后 %.2f = 扣汇兑 %.2f；2025H2 扣汇兑 %.2f"
          % (H1_KF, H1_FX * (1 - TAX), H1_EXFX, H2_25_EXFX))
    vs = {}
    for name, s in SCEN.items():
        v, d = value(s, COE, detail=True)
        vs[name] = v
        b = d["b"]
        print("\n[%s] p=%.2f  2026 营收 %.1f，扣汇兑归母 %.2f，正常化归母 %.2f，经营归母(剔现金利息) %.2f，净利率 %.1f%%"
              % (name, s["p"], b["rev26"], b["exfx26"], b["norm26"], b["op26"], b["margin"] * 100))
        print("    下半年自由现金流 %.2f，年末净现金(含或有 %.1f、非经营) %.2f" % (b["h2_fcf"], s["contingent"], b["net_cash_ye"]))
        for y, op, rev, re, oe in d["rows"]:
            print("    %d 经营归母 %.2f  营收 %.1f  再投资 %.2f  所有者收益 %.2f" % (y, op, rev, re, oe))
        print("    终值增长 %.1f%%，终值期再投资率 %.1f%%（RONIC %.0f%%），终值占经营现值 %.0f%%"
              % (s["g_t"] * 100, s["g_t"] / s["ronic_t"] * 100, s["ronic_t"] * 100, d["tv_share"] * 100))
        print("    V = %.2f 元/股" % v)
    vw = sum(SCEN[k]["p"] * vs[k] for k in SCEN)
    pv_ratio = PRICE / vw
    v8 = sum(SCEN[k]["p"] * value(SCEN[k], 0.08) for k in SCEN)
    v10 = sum(SCEN[k]["p"] * value(SCEN[k], 0.10) for k in SCEN)
    base = SCEN["base"]
    irr = solve(lambda r: value(base, r), 0.03, 0.30, PRICE)
    # 反向 DCF 一：10 年恒定增速 + 2.5% 永续，其余参数同基准
    g10 = solve(lambda g: value(base, COE, growth=[g] * 10), -0.10, 0.30, PRICE)
    # 反向 DCF 二：自 2027 起单段永续增速（再投资率 = g / 16%）
    b = build(base)
    nc = b["net_cash_ye"]

    def gordon(g):
        oe1 = b["op26"] * (1 + g) * (1 - g / base["ronic_t"])
        return (oe1 / (COE - g) * (1 + COE) ** 0.5 + nc) / (1 + COE) ** YEARS_TO_YE / SHARES
    g_perp = solve(gordon, -0.05, 0.085, PRICE)
    print("\n== 汇总 ==")
    print("三情景 V：熊 %.2f / 基准 %.2f / 牛 %.2f（概率 %.2f/%.2f/%.2f）"
          % (vs["bear"], vs["base"], vs["bull"], SCEN["bear"]["p"], SCEN["base"]["p"], SCEN["bull"]["p"]))
    print("加权 V = %.2f 元/股，P/V = %.3f" % (vw, pv_ratio))
    print("股权成本 8%%：加权 V = %.2f；10%%：加权 V = %.2f" % (v8, v10))
    print("基准情景隐含回报（使基准 V = 现价的折现率）= %.2f%%" % (irr * 100))
    print("反向 DCF：现价隐含 10 年经营所有者收益增速 %.2f%%（其后 2.5%%）；或自 2027 起永续增速 %.2f%%"
          % (g10 * 100, g_perp * 100))
    print("2026 正常化归母净利：熊 %.2f / 基准 %.2f / 牛 %.2f"
          % (build(SCEN["bear"])["norm26"], build(SCEN["base"])["norm26"], build(SCEN["bull"])["norm26"]))
    for lab, ratio in (("明显低估(≤0.75)", 0.75), ("温和低估上沿(0.90)", 0.90), ("大致合理上沿(1.10)", 1.10)):
        print("V 不变时 %s 对应价格 %.2f 元" % (lab, vw * ratio))
    # 交叉验证
    mcap = PRICE * SHARES
    print("\n== 交叉验证 ==")
    print("市值 %.1f 亿；市值/2026 基准正常化归母 %.1f 倍；剔净现金后 EV/税后经营利润 %.1f 倍"
          % (mcap, mcap / build(base)["norm26"], (mcap - NET_CASH_JUN - OP_RESERVE) / build(base)["op26"]))
    ebit = build(base)["op26"] / (1 - TAX)
    print("EV/EBIT（扣汇兑、剔现金利息）≈ %.1f 倍；股息率 %.2f%%（1.15 元）" % ((mcap - NET_CASH_JUN - OP_RESERVE) / ebit, 1.15 / PRICE * 100))
    # 基准情景再投资率与增量回报（2027-2031）
    _, d = value(base, COE, detail=True)
    reinv = sum(r[3] for r in d["rows"])
    ops = sum(r[1] for r in d["rows"])
    d_op = d["rows"][-1][1] - build(base)["op26"]
    print("基准 2027-2031 再投资率 %.1f%%，增量回报（经营归母增量/累计再投资）%.1f%%，终值期再投资率 %.1f%%"
          % (reinv / ops * 100, d_op / reinv * 100, base["g_t"] / base["ronic_t"] * 100))

    import copy
    lo, hi = 13 * build(base)["norm26"], 16 * build(base)["norm26"]
    print("历史 PE 13～16 倍 × 基准正常化归母：市值 %.0f～%.0f 亿，即 %.1f～%.1f 元" % (lo, hi, lo / SHARES, hi / SHARES))

    # ---------- 基准情景敏感性 ----------
    print("\n== 基准敏感性（其余参数不变） ==")
    for lab, upd in (("2027 年 -12%", {"growth": [-0.12, 0.07, 0.06, 0.05, 0.04]}),
                     ("2027 年 -20%", {"growth": [-0.20, 0.07, 0.06, 0.05, 0.04]}),
                     ("前 5 年零增长", {"growth": [0.0] * 5}),
                     ("或有损失 -5 亿", {"contingent": -5.0}),
                     ("营运资本强度 0.75", {"k_up": 0.75}),
                     ("终值 RONIC 12%", {"ronic_t": 0.12})):
        s = copy.deepcopy(base)
        s.update(upd)
        print("%s：V = %.2f" % (lab, value(s, COE)))

    # ---------- 证伪条件触发后的独立 V（重设情景或概率后重新加权） ----------

    def reweight(scen, probs):
        return sum(probs[k] * value(scen[k], COE) for k in scen)

    print("\n== 证伪触发后的 V ==")
    # F1：三季报弱于门槛（营收同比转负或扣汇兑归母 < 4.5 亿）：基准下修，概率向熊市移
    f1 = copy.deepcopy(SCEN)
    f1["base"].update(h2_g=0.0, h2_m=0.18, growth=[-0.10, 0.04, 0.04, 0.04, 0.03])
    print("F1 三季报弱：V = %.2f" % reweight(f1, {"bear": 0.35, "base": 0.50, "bull": 0.15}))
    # F2：2027H1 营收同比 < -10% 或扣汇兑扣非 < 8.5 亿：熊市成为主情景
    print("F2 美国业务塌陷兑现：V = %.2f" % reweight(SCEN, {"bear": 0.60, "base": 0.40, "bull": 0.0}))
    # F3：应收质量恶化（1-2 年账龄 > 6 亿或全年信用减值 > 2 亿）：一次性损失 5 亿，基准营运资本强度升至 0.70
    f3 = copy.deepcopy(SCEN)
    for k in f3:
        f3[k]["contingent"] -= 5.0
    f3["base"]["k_up"] = 0.70
    print("F3 应收与租赁款减值：V = %.2f" % reweight(f3, {"bear": 0.35, "base": 0.50, "bull": 0.15}))
    # F4：美元兑人民币中间价 ≤ 6.50：经营净利率结构性下移约 1 个百分点（各情景经营归母 -5%）
    f4 = copy.deepcopy(SCEN)
    for k in f4:
        f4[k]["op_fx"] += 1.0
    print("F4 人民币继续大幅升值：V = %.2f" % reweight(f4, {k: SCEN[k]["p"] for k in SCEN}))
    # F5：欧盟对鼎力启动反规避或复审致其合并税率 ≥ 35%：欧洲利润受损，熊市权重升至 0.45
    print("F5 欧盟税率上调：V = %.2f" % reweight(SCEN, {"bear": 0.45, "base": 0.45, "bull": 0.10}))


if __name__ == "__main__":
    main()
