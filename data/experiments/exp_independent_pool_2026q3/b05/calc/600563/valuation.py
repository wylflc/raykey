# -*- coding: utf-8 -*-
"""法拉电子（600563）独立估值 —— OI-291 池内独立审计 b05（深度版）。

运行：python3 valuation.py
输入全部写在本脚本内（金额单位亿元，每股为元/股），来源见正文
`b05/companies/600563_法拉电子.md`。打印：历史利润率核对、2026 正常化归母净利三档、
三情景 V、加权 V、P/V、8%/10% 股权成本下的 V、现价隐含回报、反向 DCF、交叉验证与证伪情景 V。
"""

# ---------------------------------------------------------------- 快照
PRICE = 103.33          # 2026-10-19 收盘，元/股
SHARES = 2.2500         # 亿股（总股本，无回购专户、无可转债）
VAL_DATE = 2026 + 291 / 365.0   # 2026-10-19 折成小数年
COE = 0.09
W = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ---------------------------------------------------------------- 利润表原文（元 → 亿元）
Y = 1e8
IS = {
    # 收入, 营业成本, 税金及附加, 销售, 管理, 研发, 其他收益, 资产+信用减值, 汇兑损益(正=收益), 归母净利, 扣非归母
    "2024":   dict(rev=4771751247.83, cogs=3179182113.41, tax_s=34684374.82, sell=53939817.95,
                   adm=157607589.36, rd=166670807.86, oi=43348375.64, imp=-24730438.07 - 36433365.16,
                   fx=-634336.67, np=1039196100.11, np_ded=1023830576.68),
    "2025":   dict(rev=5326956051.66, cogs=3615957939.37, tax_s=37589756.44, sell=57326723.26,
                   adm=178416074.27, rd=186767814.24, oi=47678288.78, imp=7942089.93 - 47749364.04,
                   fx=18398382.18, np=1192180340.23, np_ded=1128326066.75),
    "2025H1": dict(rev=2499306915.58, cogs=1672599262.07, tax_s=18101698.81, sell=33997899.32,
                   adm=88056925.52, rd=89378279.29, oi=13668067.79, imp=3624404.19 - 7056757.82,
                   fx=23181344.74, np=569421625.53, np_ded=555643626.59),
    "2026H1": dict(rev=2763699647.80, cogs=1848996860.54, tax_s=21748043.98, sell=19941538.19,
                   adm=98451268.77, rd=100862548.46, oi=22558552.20, imp=-2133761.86 - 27676518.03,
                   fx=-17914822.27, np=582137240.11, np_ded=572637812.03),
}


def core_ebit(d):
    """收入 − 营业成本 − 税金及附加 − 销售 − 管理 − 研发（不含其他收益、减值、财务与投资收益）。"""
    return (d["rev"] - d["cogs"] - d["tax_s"] - d["sell"] - d["adm"] - d["rd"]) / Y


# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 18-20、56、58、66 页）
CASH = 3.6369            # 货币资金
WMP = 9.0227             # 交易性金融资产中的银行理财（债务工具）
CD_CUR = 2.4888          # 一年内到期的大额存单
CD_NONCUR = 12.3569      # 其他非流动资产中的大额存单
DEBT = 0.2007            # 短期借款（票据贴现及其他），无其他有息负债
OP_RESERVE = 3.0         # 经营备付：约 2026E 收入的 5%
DECLARED_DIV = 0.0       # 2025 年度股利已于 2026-06-12 除息发放，中期不分配
GROSS_FIN = CASH + WMP + CD_CUR + CD_NONCUR
NET_CASH_ADJ = GROSS_FIN - DEBT - OP_RESERVE - DECLARED_DIV

EQ_FV = 2.9547           # 交易性金融资产中的权益工具（西典新能 1.1344 + 未上市 1.8203）
EQ_COST = 0.15 + 0.8544 + 0.715   # 西典 1500 万、君联晟灏余额 8544 万、晟威 7150 万
LTEI = 0.4436            # 上海美星 40%（权益法）
NON_OP = EQ_FV - 0.15 * (EQ_FV - EQ_COST) + LTEI   # 未实现收益按 15% 计税

TAX = 0.135              # 2025 年实际税率 13.3%，2026H1 13.3%；高新 15% 叠加研发加计

# ---------------------------------------------------------------- 情景
SC = {
    "bear": dict(rev26=57.0, margin=0.210, oi=0.30, imp=-0.60, yld=0.015,
                 g=[0.03, 0.03, 0.03, 0.03, 0.03], gT=0.020, roiic=0.18, ronic=0.12),
    "base": dict(rev26=58.0, margin=0.235, oi=0.38, imp=-0.50, yld=0.018,
                 g=[0.08, 0.08, 0.07, 0.06, 0.05], gT=0.025, roiic=0.25, ronic=0.15),
    "bull": dict(rev26=59.0, margin=0.255, oi=0.40, imp=-0.45, yld=0.020,
                 g=[0.12, 0.12, 0.10, 0.09, 0.08], gT=0.025, roiic=0.30, ronic=0.20),
}


def nopat26(p):
    """2026 正常化经营税后利润（不含现金收益、汇兑、公允价值与投资收益、营业外）。"""
    return (p["rev26"] * p["margin"] + p["oi"] + p["imp"]) * (1 - TAX)


def np26_norm(p):
    """2026 正常化归母净利：经营部分 + 金融资产税后收益（含净利息），剔除一次性项目。"""
    return nopat26(p) + GROSS_FIN * p["yld"] * (1 - TAX)


def growth_path(p):
    """2027-2031 逐年增速，2032-2036 线性衰减到终值增速。"""
    g = list(p["g"])
    g5, gT = g[-1], p["gT"]
    for k in range(1, 6):
        g.append(g5 + (gT - g5) * k / 5.0)
    return g  # 10 个值，对应 2027..2036


def dcf(p, r=COE, nopat0=None, g_override=None, extra_cash=0.0, detail=False):
    """所有者收益 DCF：OE = NOPAT × (1 − g/ROIIC)；终值 OE = NOPAT × (1 − gT/RONIC)。
    现金流时点：2026H2 取 2026-10-01，之后每年取年中；折到 2026-10-19。"""
    n0 = nopat26(p) if nopat0 is None else nopat0
    gs = growth_path(p) if g_override is None else g_override
    rows = []
    # 2026 下半年
    t = 2026.75 - VAL_DATE
    oe = 0.5 * n0 * (1 - gs[0] / p["roiic"])
    pv = oe / (1 + r) ** t
    rows.append(("2026H2", None, 0.5 * n0, oe, t, pv))
    total = pv
    n = n0
    for i, g in enumerate(gs):
        yr = 2027 + i
        n = n * (1 + g)
        oe = n * (1 - g / p["roiic"])
        t = yr + 0.5 - VAL_DATE
        pv = oe / (1 + r) ** t
        rows.append((str(yr), g, n, oe, t, pv))
        total += pv
    t_last = rows[-1][4]
    oe_T = n * (1 + p["gT"]) * (1 - p["gT"] / p["ronic"])
    tv = oe_T / (r - p["gT"])
    pv_tv = tv / (1 + r) ** t_last
    v_oper = total + pv_tv
    equity = v_oper + NET_CASH_ADJ + NON_OP + extra_cash
    out = dict(v_oper=v_oper, pv_explicit=total, pv_tv=pv_tv, tv_share=pv_tv / equity,
               equity=equity, per_share=equity / SHARES, rows=rows)
    return out if detail else out["per_share"]


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
    print("=== 一、历史核对（亿元） ===")
    for k, d in IS.items():
        ce = core_ebit(d)
        gm = 1 - d["cogs"] / d["rev"]
        print(f"{k:7s} 收入 {d['rev']/Y:6.2f}  毛利率 {gm*100:5.1f}%  核心经营利润 {ce:6.2f}"
              f" ({ce/(d['rev']/Y)*100:4.1f}%)  其他收益 {d['oi']/Y:5.2f}  减值 {d['imp']/Y:5.2f}"
              f"  汇兑 {d['fx']/Y:+5.2f}  归母 {d['np']/Y:5.2f}  扣非 {d['np_ded']/Y:5.2f}")
    h2 = {k: IS["2025"][k] - IS["2025H1"][k] for k in IS["2025"]}
    ce = core_ebit(h2)
    print(f"2025H2  收入 {h2['rev']/Y:6.2f}  毛利率 {(1-h2['cogs']/h2['rev'])*100:5.1f}%  核心经营利润 {ce:6.2f}"
          f" ({ce/(h2['rev']/Y)*100:4.1f}%)  汇兑 {h2['fx']/Y:+5.2f}  归母 {h2['np']/Y:5.2f}  扣非 {h2['np_ded']/Y:5.2f}")
    # 2021-2025 再投资与增量回报（数据包年度表）
    np_ = [8.31, 10.07, 10.24, 10.39, 11.92]
    fcf = [6.05, 4.57, 6.52, 8.68, 7.28]
    reinv = sum(np_) - sum(fcf)
    print(f"2021-2025 累计归母 {sum(np_):.2f}，累计自由现金流 {sum(fcf):.2f}，再投资 {reinv:.2f}"
          f"（再投资率 {reinv/sum(np_)*100:.0f}%）；收入 28.11→53.27，每元新增收入占用资本 {reinv/(53.27-28.11):.2f}")
    print(f"  同期归母增量 {11.92-8.31:.2f} / 2022-2025 再投资 {sum(np_[1:])-sum(fcf[1:]):.2f}"
          f" = 实现增量回报 {(11.92-8.31)/(sum(np_[1:])-sum(fcf[1:]))*100:.0f}%")

    print("\n=== 二、净现金与非经营资产（2026-06-30，亿元） ===")
    print(f"货币资金 {CASH:.2f} + 银行理财 {WMP:.2f} + 大额存单 {CD_CUR:.2f}+{CD_NONCUR:.2f} = {GROSS_FIN:.2f}")
    print(f"− 短期借款 {DEBT:.2f} − 经营备付 {OP_RESERVE:.2f} − 已宣派未付股利 {DECLARED_DIV:.2f}"
          f" = 经调整净现金 {NET_CASH_ADJ:.2f}（{NET_CASH_ADJ/SHARES:.2f} 元/股）")
    print(f"非经营资产：权益投资 {EQ_FV:.2f}（扣未实现收益税 {0.15*(EQ_FV-EQ_COST):.2f}）+ 上海美星 {LTEI:.2f}"
          f" = {NON_OP:.2f}（{NON_OP/SHARES:.2f} 元/股）")

    print("\n=== 三、2026 正常化（亿元） ===")
    for k, p in SC.items():
        print(f"{k:4s} 收入 {p['rev26']:.1f} × 核心利润率 {p['margin']*100:.1f}% + 其他收益 {p['oi']:.2f}"
              f" + 减值 {p['imp']:.2f} → 经营税后 {nopat26(p):.2f}；金融资产收益率 {p['yld']*100:.1f}%"
              f" → 正常化归母 {np26_norm(p):.2f}")

    print("\n=== 四、三情景 DCF（股权成本 9%） ===")
    res = {}
    for k, p in SC.items():
        d = dcf(p, detail=True)
        res[k] = d
        print(f"--- {k}：ROIIC {p['roiic']*100:.0f}%，终值增速 {p['gT']*100:.1f}%，终值 RONIC {p['ronic']*100:.0f}%")
        for name, g, n, oe, t, pv in d["rows"][:6]:
            gs = "  —  " if g is None else f"{g*100:4.1f}%"
            print(f"   {name}: 增速 {gs} NOPAT {n:6.2f} 再投资率 {(1-oe/n)*100:4.1f}% 所有者收益 {oe:6.2f} t={t:4.2f} PV {pv:5.2f}")
        print(f"   2032-2036 增速 {', '.join(f'{x*100:.1f}%' for x in growth_path(p)[5:])}")
        print(f"   经营价值 {d['v_oper']:.1f}（显性 {d['pv_explicit']:.1f} + 终值 {d['pv_tv']:.1f}）"
              f" + 净现金 {NET_CASH_ADJ:.1f} + 非经营 {NON_OP:.1f} = {d['equity']:.1f} 亿；"
              f"终值占比 {d['tv_share']*100:.0f}%；V = {d['per_share']:.2f} 元")
    vw = sum(W[k] * res[k]["per_share"] for k in SC)
    pv_ratio = PRICE / vw
    tier = ("明显低估" if pv_ratio <= 0.75 else "温和低估" if pv_ratio <= 0.90 else
            "大致合理" if pv_ratio <= 1.10 else "偏贵或价值陷阱风险高")
    print(f"\n加权 V = {vw:.2f} 元；P/V = {pv_ratio:.3f}（{tier}）")
    print(f"V 不变时各档价格：≤{0.75*vw:.1f} 明显低估；{0.75*vw:.1f}～{0.90*vw:.1f} 温和低估；"
          f"{0.90*vw:.1f}～{1.10*vw:.1f} 大致合理；>{1.10*vw:.1f} 偏贵")

    print("\n=== 五、股权成本敏感性 ===")
    sens = {}
    for r in (0.08, 0.09, 0.10):
        vs = {k: dcf(p, r=r) for k, p in SC.items()}
        sens[r] = sum(W[k] * vs[k] for k in SC)
        print(f"r={r*100:.0f}%：熊 {vs['bear']:.2f} / 基准 {vs['base']:.2f} / 牛 {vs['bull']:.2f} → 加权 {sens[r]:.2f}")

    print("\n=== 六、现价隐含回报与反向 DCF ===")
    irr = solve(lambda r: dcf(SC["base"], r=r), 0.05, 0.15, PRICE)
    print(f"基准情景现金流使现值等于现价的折现率：{irr*100:.2f}%")
    irr_w = solve(lambda r: sum(W[k] * dcf(p, r=r) for k, p in SC.items()), 0.05, 0.15, PRICE)
    print(f"（概率加权现金流对应：{irr_w*100:.2f}%）")
    b = SC["base"]
    g10 = solve(lambda g: dcf(b, g_override=[g] * 10), -0.05, 0.20, PRICE)
    print(f"现价隐含 2027-2036 年所有者收益（=NOPAT）年增速：{g10*100:.2f}%（基准利润率、ROIIC 25%，之后 2.5%）")

    def gordon(g):
        p = dict(b, gT=g, ronic=b["roiic"])
        return dcf(p, g_override=[g] * 10)
    gp = solve(gordon, -0.02, 0.085, PRICE)
    print(f"现价隐含永续增速：{gp*100:.2f}%（自 2027 年起单一增速，再投资率 = g/25%）")
    m_impl = solve(lambda m: dcf(dict(b, margin=m)), 0.15, 0.35, PRICE)
    print(f"基准增速下现价隐含核心利润率：{m_impl*100:.1f}%（基准 23.5%）")

    print("\n=== 七、交叉验证 ===")
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NON_OP
    ebit_b = SC["base"]["rev26"] * SC["base"]["margin"] + SC["base"]["oi"] + SC["base"]["imp"]
    print(f"市值 {mcap:.2f}；EV（扣经调整净现金与非经营资产）{ev:.1f}；2026 正常化 EBIT {ebit_b:.2f} → EV/EBIT {ev/ebit_b:.1f}×")
    print(f"P/正常化归母（基准）{mcap/np26_norm(SC['base']):.1f}×；扣现金后 PE {ev/nopat26(SC['base']):.1f}×；"
          f"PE(TTM) {mcap/12.05:.1f}×；PB {mcap/60.94:.2f}×")
    print(f"股息率 {2.30/PRICE*100:.2f}%（分红率 43.4%，无回购）；TTM 自由现金流收益率 {(12.37-5.52)/mcap*100:.2f}%；"
          f"基准 2027 所有者收益/EV {res['base']['rows'][1][3]/ev*100:.2f}%")
    for k in SC:
        print(f"V({k}) 对应 2026 正常化 PE {res[k]['per_share']*SHARES/np26_norm(SC[k]):.1f}×")

    print("\n=== 八、证伪情景 V（股权成本 9%） ===")
    fz = falsifier_values()
    for name, v in fz.items():
        print(f"{name}: V = {v:.2f}（P/V {PRICE/v:.2f}）")

    print("\n=== 九、2026 三季度与全年估计（三季报 2026-10-31 预约，下次核对点） ===")
    q = q3_estimate()
    for k, (rev, npq) in q.items():
        print(f"Q3 {k}: 收入 {rev:.2f}（同比 {(rev/14.45-1)*100:+.1f}%），归母 {npq:.2f}（同比 {(npq/3.18-1)*100:+.1f}%）")
    np_fy = 5.82 + q["中值"][1] + 3.00
    print(f"2026 全年归母（H1 5.82 + Q3 中值 + Q4 约 3.00）≈ {np_fy:.2f} 亿，对照基准正常化 {np26_norm(SC['base']):.2f}")

    print("\n=== 十、基准情景单项敏感性（9%，元/股） ===")
    b = SC["base"]
    cases = [
        ("核心利润率 22.5% / 24.5%", dict(b, margin=0.225), dict(b, margin=0.245)),
        ("2027-2031 增速 −2pp / +2pp", dict(b, g=[x - 0.02 for x in b["g"]]), dict(b, g=[x + 0.02 for x in b["g"]])),
        ("ROIIC 20% / 30%", dict(b, roiic=0.20), dict(b, roiic=0.30)),
        ("终值 RONIC 12% / 20%", dict(b, ronic=0.12), dict(b, ronic=0.20)),
        ("终值增速 2.0% / 2.5%(基准)", dict(b, gT=0.020), dict(b)),
    ]
    for name, lo, hi in cases:
        print(f"{name}: {dcf(lo):.2f} / {dcf(hi):.2f}")
    print(f"经营备付 0 / 6 亿: {dcf(b, extra_cash=OP_RESERVE):.2f} / {dcf(b, extra_cash=-OP_RESERVE):.2f}")
    print(f"所得税率 25%（高新资格失效）: {dcf(dict(b), nopat0=nopat26(b) * 0.75 / (1 - TAX)):.2f}")
    return res, vw


def q3_estimate():
    """2025Q3 收入 14.45（含 2025-10-31 出表的变压器约 0.29），归母 3.18，扣非 3.11。
    电容器及其他收入同比 +6%/+10%/+14%；核心利润率 23.0%/24.0%/24.5%；
    汇兑：三季度人民币对美元中间价升值约 1.1%（6.8109→6.7351），按上半年升值约 3.1% 对应
    汇兑损失 0.18 亿等比例估约 −0.07 亿。"""
    base_rev = 14.45 - 0.29
    fx_q3 = -0.07
    out = {}
    for name, g, m in (("低值", 0.06, 0.230), ("中值", 0.10, 0.240), ("高值", 0.14, 0.245)):
        rev = base_rev * (1 + g)
        pbt = rev * m + 0.10 - 0.13 + GROSS_FIN * 0.018 / 4 + fx_q3
        out[name] = (rev, pbt * (1 - TAX))
    return out


def falsifier_values():
    b, be = SC["base"], SC["bear"]
    out = {}
    # F1 2026 年报扣非 < 11.0 亿或毛利率 < 30.5%：利润率降到 21.5%，增速按基准减 2 个百分点
    out["F1 利润率 21.5% 且增速降 2pp"] = dcf(dict(b, margin=0.215, g=[x - 0.02 for x in b["g"]]))
    # F2 国内价格战延续：2027 中报电容器收入同比 < 3% 且境内毛利率 < 27% → 熊市参数
    out["F2 熊市参数"] = dcf(be)
    # F3 2026 三季报单季收入 < 14.9 亿或扣非 < 2.8 亿：2027 增速 4%、利润率 22.5%
    out["F3 三季报偏弱"] = dcf(dict(b, margin=0.225, g=[0.04, 0.06, 0.06, 0.05, 0.05]))
    # F4 资本配置：2026 年度分红率 < 35% 或单笔非主业投资 > 10 亿：净现金按半数计价
    out["F4 现金折半"] = dcf(b, extra_cash=-0.5 * NET_CASH_ADJ)
    # F5 上行：2026 年报毛利率 ≥ 34% 且境外收入增速 ≥ 15% → 牛市参数
    out["F5 牛市参数（上行）"] = dcf(SC["bull"])
    return out


if __name__ == "__main__":
    main()
