#!/usr/bin/env python3
"""603508 思维列控 独立估值（OI-291 b06，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位亿元，每股价值单位元。全部输入写在本文件内；出处见
data/experiments/exp_independent_pool_2026q3/b06/companies/603508_思维列控.md。
"""

# ---------------------------------------------------------------- 快照
PRICE = 20.67            # 2026-10-20 收盘（腾讯行情）
SHARES = 3.8127          # 亿股：总股本 381,274,377 股；无回购专户、无拟注销股份（2026H1_report 第 43-44 页）
MCAP = PRICE * SHARES

# ---------------------------------------------------------------- 利润表输入（亿元）
# 2026H1_report 第 51-52、144-146 页；2025_annual_report 第 7-9、180-184 页；2024 与 2025H1 取东财 F10（与原文核对一致）
# 核心 EBIT = 营业利润 − 利息收入 − 投资收益 − 公允价值变动 − 信用减值 − 资产减值 − 资产处置（含其他收益/增值税即征即退）
P = {
    "2024":   dict(rev=15.1514, op=6.5944, ii=0.4213, inv=0.0011, fv=0.0000, cr=-0.3650, ai=-0.0487, disp=-0.0008, vat=0.4090, np=5.4838, npd=5.4857),
    "2025":   dict(rev=15.1961, op=6.7925, ii=0.3224, inv=0.0154, fv=0.0001, cr=0.2236, ai=-0.0188, disp=-0.0105, vat=0.3299, np=5.5615, npd=5.5183),
    "2025H1": dict(rev=6.8919, op=3.6302, ii=0.2142, inv=0.0072, fv=0.0000, cr=0.0968, ai=-0.0066, disp=-0.0069, vat=0.2873, np=3.0355, npd=3.0189),
    "2026H1": dict(rev=7.2869, op=3.8153, ii=0.0706, inv=0.0244, fv=0.0031, cr=0.1202, ai=0.0040, disp=0.0005, vat=0.4769, np=3.1765, npd=3.1506),
}
TTM = {k: P["2025"][k] - P["2025H1"][k] + P["2026H1"][k] for k in P["2025"]}


def core_ebit(d):
    return d["op"] - d["ii"] - d["inv"] - d["fv"] - d["cr"] - d["ai"] - d["disp"]


VAT_NORM = 0.025         # 增值税即征即退正常化占收入（2024 2.7%、2025 2.2%；2026H1 6.5% 属退税节奏）
IMP_NORM = 0.008         # 正常化减值（信用+资产）占收入（2021-2025 年均约 1%）
TAX = 0.155              # 正常化所得税率（主体 15% 高新税率；2024 12.8%、2025 15.8%、2026H1 13.5%）
MINORITY = 0.032         # 少数股东占净利（思维信息 24.76%、思维鑫科 24.75% 少数股权；2025 2.9%，2026H1 3.6%）
INT_YIELD = 0.016        # 现金税前收益率（2026H1 利息收入+理财收益约 0.10 亿，年化约 1.6%）
WC_INT = 0.60            # 增量营运资本 / 增量收入（2026-06-30 净营运资本约 10.4 亿，为 TTM 收入 67%）

# ---------------------------------------------------------------- 资产负债（2026-06-30；2026H1_report 第 46-48、103、125 页）
CASH = 11.9108           # 货币资金（含未到期应收利息 0.2608、受限履约保证金 0.0923）
TFA = 1.0003             # 交易性金融资产（结构性存款）
RESTRICTED = 0.0923
DEBT = 0.0               # 无有息负债
OP_RESERVE = 1.5         # 经营备付，约 10% 收入（季节性回款、年末奖金与税费集中支付）
MINORITY_CASH = 1.0      # 少数股东应占子公司现金（少数股东权益 1.50 亿的约 2/3）
DECLARED_DIV = 0.0       # 已宣派未付股利：无（2025 年末期股利 2026-05-21 已付）
NET_CASH_ADJ = CASH + TFA - RESTRICTED - DEBT - OP_RESERVE - MINORITY_CASH - DECLARED_DIV
INV_PROPERTY = 1.2       # 投资性房地产：账面 2.01 亿，2024 年租金 0.193 亿；会计净贡献≈0，单列并折价
OTHER_EQUITY = 0.0256    # 其他权益工具投资
NON_OP = INV_PROPERTY + OTHER_EQUITY
MINORITY_BOOK = 1.5042   # 少数股东权益账面（EV 计算用）
PARENT_EQUITY = 41.2149

COE = 0.09
T0 = 0.2                 # 2026-10-20 至 2026-12-31；各年现金流按年末到账
YEARS = [2027, 2028, 2029, 2030, 2031]

SCEN = {
    #        2026 正常化收入  核心EBIT率   2027-2031 收入增速                 终值增长   概率
    "bear": dict(rev=12.5, m=0.34, g=[0.00, 0.00, 0.01, 0.01, 0.01], gt=0.010, p=0.25),
    "base": dict(rev=14.5, m=0.39, g=[0.03, 0.03, 0.03, 0.03, 0.03], gt=0.020, p=0.50),
    "bull": dict(rev=15.8, m=0.41, g=[0.06, 0.06, 0.06, 0.06, 0.06], gt=0.025, p=0.25),
}


def nopat_parent(rev, m):
    return rev * m * (1 - TAX) * (1 - MINORITY)


def interest_after_tax():
    return (CASH + TFA - RESTRICTED) * INT_YIELD * (1 - TAX) * (1 - MINORITY)


def norm_np(s):
    """2026 正常化归母净利：经营部分 + 现金税后收益（剔除一次性与节奏性项目）。"""
    return nopat_parent(s["rev"], s["m"]) + interest_after_tax()


def path(s):
    revs, nps, oes, reinv = [], [], [], []
    prev = s["rev"]
    for g in s["g"]:
        r = prev * (1 + g)
        npat = nopat_parent(r, s["m"])
        dwc = WC_INT * (r - prev)
        revs.append(r); nps.append(npat); oes.append(npat - dwc); reinv.append(dwc)
        prev = r
    oe_t = nps[-1] * (1 + s["gt"]) - WC_INT * revs[-1] * s["gt"]
    rr1 = reinv[0] / nps[0]
    stub = 0.5 * nopat_parent(s["rev"], s["m"]) * (1 - rr1)
    return dict(revs=revs, nps=nps, oes=oes, reinv=reinv, oe_t=oe_t, stub=stub, rr1=rr1)


def value(s, r=COE):
    p = path(s)
    pv = p["stub"] / (1 + r) ** T0
    for i, oe in enumerate(p["oes"]):
        pv += oe / (1 + r) ** (T0 + i + 1)
    pv_tv = p["oe_t"] / (r - s["gt"]) / (1 + r) ** (T0 + len(p["oes"]))
    eq = pv + pv_tv + NET_CASH_ADJ + NON_OP
    return eq / SHARES, eq, pv_tv / (pv + pv_tv)


def weighted(r=COE, w=None):
    w = w or {k: s["p"] for k, s in SCEN.items()}
    return sum(w[k] * value(SCEN[k], r)[0] for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: value(SCEN["base"], r)[0], 0.05, 0.30, PRICE)


def reverse_dcf_10y(gt=0.02, r=COE):
    """自基准正常化起点（收入 14.5、EBIT 率 39%），求 10 年恒定收入增速使 V=现价，之后终值增长 2%。"""
    b = SCEN["base"]

    def v(g):
        prev = b["rev"]
        rr1 = WC_INT * g * prev / nopat_parent(prev * (1 + g), b["m"])
        pv = 0.5 * nopat_parent(prev, b["m"]) * (1 - rr1) / (1 + r) ** T0
        for i in range(10):
            rv = prev * (1 + g)
            pv += (nopat_parent(rv, b["m"]) - WC_INT * (rv - prev)) / (1 + r) ** (T0 + i + 1)
            prev = rv
        oe_t = nopat_parent(prev, b["m"]) * (1 + gt) - WC_INT * prev * gt
        pv += oe_t / (r - gt) / (1 + r) ** (T0 + 10)
        return (pv + NET_CASH_ADJ + NON_OP) / SHARES

    return solve(v, -0.10, 0.15, PRICE)


def reverse_perpetual(npat, r=COE):
    """单阶段：给定起点归母经营利润，求永续增速使 V=现价（再投资按 WC_INT 随增长计提）。"""
    rev_equiv = npat / (SCEN["base"]["m"] * (1 - TAX) * (1 - MINORITY))

    def v(g):
        oe1 = npat * (1 + g) - WC_INT * rev_equiv * g
        return (0.5 * npat / (1 + r) ** T0 + oe1 / (r - g) / (1 + r) ** T0 + NET_CASH_ADJ + NON_OP) / SHARES

    return solve(v, -0.10, 0.085, PRICE)


def with_overrides(fn, **kw):
    """临时替换模块级输入后计算 fn()，用于证伪情形。"""
    g = globals(); saved = {k: g[k] for k in kw}
    g.update(kw)
    try:
        return fn()
    finally:
        g.update(saved)


def tier(pv):
    return "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"


def main():
    print("== 603508 思维列控 独立估值（价格日 2026-10-20）==")
    print(f"现价 {PRICE:.2f} 元，总股本 {SHARES:.4f} 亿股，市值 {MCAP:.2f} 亿元；股权成本 {COE:.0%}")

    print("\n-- 1. 核心 EBIT（含其他收益；剔除利息、投资收益、公允价值、减值与处置）--")
    for k in ["2024", "2025", "2025H1", "2026H1"]:
        d = P[k]; ce = core_ebit(d)
        print(f"{k:7s} 收入 {d['rev']:6.2f} 核心EBIT {ce:5.2f}（{ce/d['rev']*100:4.1f}%）即征即退 {d['vat']:.3f}（{d['vat']/d['rev']*100:.1f}%）归母 {d['np']:.2f} 扣非 {d['npd']:.2f}")
    ce_ttm = core_ebit(TTM)
    ce_ttm_n = ce_ttm - TTM["vat"] + VAT_NORM * TTM["rev"] - IMP_NORM * TTM["rev"]
    np_ttm_op = ce_ttm_n * (1 - TAX) * (1 - MINORITY)
    np_ttm_n = np_ttm_op + interest_after_tax()
    print(f"TTM     收入 {TTM['rev']:6.2f} 核心EBIT {ce_ttm:5.2f}（{ce_ttm/TTM['rev']*100:4.1f}%）即征即退 {TTM['vat']:.3f}；归母 {TTM['np']:.2f} 扣非 {TTM['npd']:.2f}")
    print(f"TTM 即征即退与减值正常化后 EBIT {ce_ttm_n:.2f}（{ce_ttm_n/TTM['rev']*100:.1f}%）→ 按现收入正常化归母 {np_ttm_n:.2f} 亿")

    kf = (1 - TAX) * (1 - MINORITY)
    vat_x = (TTM["vat"] - VAT_NORM * TTM["rev"]) * kf
    imp_ttm = TTM["cr"] + TTM["ai"]
    imp_x = (imp_ttm + IMP_NORM * TTM["rev"]) * kf
    nonrec = TTM["np"] - TTM["npd"]
    resid = TTM["np"] - vat_x - imp_x - nonrec - np_ttm_n
    b = SCEN["base"]
    cyc = np_ttm_n - norm_np(b)
    print("\n-- 2. TTM 归母拆分：报告值 = 一次性/节奏性 + 周期性 + 结构性（基准正常化）--")
    print(f"报告 TTM 归母 {TTM['np']:.2f} = 即征即退超常 {vat_x:.2f} + 减值转回超常（TTM 合计 {imp_ttm:+.2f}，正常 {-IMP_NORM*TTM['rev']:.2f}）{imp_x:.2f}"
          f" + 非经常性 {nonrec:.2f} + 口径重叠（理财收益、补助已含于正常化利息与 EBIT）{resid:+.2f} + 周期性（收入 {TTM['rev']:.2f}→{b['rev']:.1f}、EBIT 率 {ce_ttm_n/TTM['rev']*100:.1f}%→{b['m']*100:.0f}%）{cyc:.2f}"
          f" + 结构性 {norm_np(b):.2f}")

    print("\n-- 3. 经调整净现金（2026-06-30）与非经营资产 --")
    print(f"现金类 {CASH+TFA:.2f} − 受限 {RESTRICTED:.2f} − 有息负债 {DEBT:.2f} − 经营备付 {OP_RESERVE:.2f} − 少数股东应占现金 {MINORITY_CASH:.2f} − 已宣派股利 {DECLARED_DIV:.2f} = {NET_CASH_ADJ:.2f} 亿（为正，按无杠杆口径；无可转债）")
    print(f"非经营资产 {NON_OP:.2f} 亿（投资性房地产 {INV_PROPERTY:.2f} + 其他权益工具 {OTHER_EQUITY:.3f}）；合计每股 {(NET_CASH_ADJ+NON_OP)/SHARES:.2f} 元")

    print("\n-- 4. 三情景所有者收益 DCF --")
    for name, s in SCEN.items():
        p = path(s)
        v9, eq, tvshare = value(s)
        v8 = value(s, 0.08)[0]; v10 = value(s, 0.10)[0]
        oe26 = p["stub"] * 2
        oe_g = [p["oes"][0] / oe26 - 1] + [p["oes"][i] / p["oes"][i - 1] - 1 for i in range(1, 5)]
        rr_avg = sum(p["reinv"]) / sum(p["nps"])
        d_np = p["nps"][-1] - nopat_parent(s["rev"], s["m"])
        roiic = d_np / sum(p["reinv"]) if sum(p["reinv"]) > 0 else float("nan")
        print(f"[{name}] p={s['p']:.2f} 2026 正常化收入 {s['rev']:.1f}、核心EBIT率 {s['m']*100:.0f}% → 正常化归母 {norm_np(s):.2f} 亿（经营 {nopat_parent(s['rev'], s['m']):.2f} + 利息 {interest_after_tax():.2f}）")
        print(f"   收入 {', '.join(f'{y}:{r:.2f}' for y, r in zip(YEARS, p['revs']))}")
        print(f"   所有者收益 {', '.join(f'{y}:{o:.2f}' for y, o in zip(YEARS, p['oes']))}（2026H2 存根 {p['stub']:.2f}）")
        print(f"   所有者收益增速 {', '.join(f'{g*100:.1f}%' for g in oe_g)}；终值增长 {s['gt']*100:.1f}%；再投资率(2027-31 平均) {rr_avg*100:.1f}%；增量回报 {roiic*100:.0f}%；终值占经营价值 {tvshare*100:.0f}%")
        print(f"   V@9% {v9:.2f} 元（股权 {eq:.1f} 亿）；V@8% {v8:.2f}；V@10% {v10:.2f}")

    vw = weighted(); vw8 = weighted(0.08); vw10 = weighted(0.10)
    pv = PRICE / vw
    print(f"\n加权 V@9% = {vw:.2f} 元；P/V = {pv:.3f}（{tier(pv)}）")
    print(f"加权 V@8% = {vw8:.2f} 元（P/V {PRICE/vw8:.2f}）；加权 V@10% = {vw10:.2f} 元（P/V {PRICE/vw10:.2f}）")
    print("无回购专户股份与拟注销股份：剔除口径 V、P/V 同上")
    print(f"V 不变时各档价格：≤{0.75*vw:.2f} 明显低估；{0.75*vw:.2f}～{0.90*vw:.2f} 温和低估；{0.90*vw:.2f}～{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵")

    print("\n-- 5. 隐含回报与反向 DCF --")
    print(f"现价隐含回报（基准情景所有者收益流+终值+净现金=现价）：{implied_irr()*100:.2f}%")
    print(f"自基准正常化起点：现价隐含 10 年收入/所有者收益年增 {reverse_dcf_10y()*100:.2f}%（之后 2%）")
    print(f"单阶段永续：基准正常化经营利润 {nopat_parent(b['rev'], b['m']):.2f} 亿起点隐含 {reverse_perpetual(nopat_parent(b['rev'], b['m']))*100:.2f}%；"
          f"TTM 正常化经营利润 {np_ttm_op:.2f} 亿起点隐含 {reverse_perpetual(np_ttm_op)*100:.2f}%")

    print("\n-- 6. 基准 V 敏感性（正常化收入 × 核心EBIT率，9%）--")
    for rv in (13.5, 14.5, 15.5):
        row = []
        for m in (0.37, 0.39, 0.41):
            row.append(value(dict(SCEN["base"], rev=rv, m=m))[0])
        print(f"收入 {rv:.1f}：EBIT率 37% {row[0]:.2f}｜39% {row[1]:.2f}｜41% {row[2]:.2f}")
    for rv, m in ((15.5, 0.41), (13.5, 0.37)):
        alt = dict(SCEN, base=dict(SCEN["base"], rev=rv, m=m))
        vw_alt = sum(alt[k]["p"] * value(alt[k])[0] for k in alt)
        print(f"基准改为收入 {rv:.1f}、EBIT率 {m*100:.0f}%（熊牛不变）：加权 V {vw_alt:.2f}，P/V {PRICE/vw_alt:.2f}")

    print("\n-- 7. 交叉验证 --")
    ev = MCAP - (CASH + TFA - RESTRICTED) + DEBT + MINORITY_BOOK
    print(f"EV ≈ {ev:.1f} 亿：EV/TTM 正常化 EBIT {ev/ce_ttm_n:.1f}×；EV/基准正常化 EBIT {ev/(b['rev']*b['m']):.1f}×")
    print(f"PE：市值/TTM 归母 {MCAP/TTM['np']:.1f}×；市值/基准正常化归母 {MCAP/norm_np(b):.1f}×；PB {MCAP/PARENT_EQUITY:.2f}×")
    pe_hist = {2021: 16.2, 2022: 18.0, 2023: 14.5, 2024: 16.5, 2025: 27.82 * SHARES / 5.5615}
    pe_avg = sum(pe_hist.values()) / len(pe_hist)
    print(f"年末 PE 2021-2025：{', '.join(f'{y}:{v:.1f}' for y, v in pe_hist.items())}，均值 {pe_avg:.1f}× → ×基准正常化 EPS {norm_np(b)/SHARES:.2f} = {pe_avg*norm_np(b)/SHARES:.2f} 元")
    print(f"股息率：近 12 个月 0.5245 元 → {0.5245/PRICE*100:.2f}%；60% 分红下限 × 基准正常化归母 → {0.6*norm_np(b)/SHARES/PRICE*100:.2f}%；FY2025 合计每股 2.6245 元（含 2.10 元特别中期）")

    print("\n-- 8. 证伪触发后的 V（9%）--")
    f = {
        "F1 2026 年收入<14.5 亿或扣非<5.0 亿（熊45/基45/牛10）": weighted(w=dict(bear=0.45, base=0.45, bull=0.10)),
        "F2 2027 年列控<6.0 亿或收入<13.5 亿（熊50/基40/牛10）": weighted(w=dict(bear=0.50, base=0.40, bull=0.10)),
        "F3 高新复审失败，正常化税率 15.5%→22%": with_overrides(weighted, TAX=0.22),
        "F4 新一代普速列控份额<30%（熊50/基50/牛0）": weighted(w=dict(bear=0.50, base=0.50, bull=0.0)),
        "F5 赵建州事项波及公司/蓝信或客户暂停投标（熊60/基35/牛5）": weighted(w=dict(bear=0.60, base=0.35, bull=0.05)),
    }
    for k, v in f.items():
        print(f"{k}: V = {v:.2f} 元，P/V = {PRICE/v:.2f}")


if __name__ == "__main__":
    main()
