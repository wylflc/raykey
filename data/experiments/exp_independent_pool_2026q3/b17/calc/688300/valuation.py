#!/usr/bin/env python3
"""688300 联瑞新材 独立估值（OI-291 b17，价格日 2026-10-21 北京时间收盘）。

输入全部写在脚本内，`python3 valuation.py` 打印：股本与可转债核对、经调整净现金、2026 正常化归母净利三档、
三情景 V（可转债逐情景取低：债务口径与全部转股口径）、加权 V、P/V 与分档价格、8%/10% 下的 V、
基准情景隐含回报、反向 DCF、交叉验证与证伪条件触发后的 V。
金额单位：亿元；每股：元。来源页码见 companies/688300_联瑞新材.md「来源」。
"""

# ---------------- 价格与股本 ----------------
PRICE = 102.20                     # 2026-10-21 收盘（腾讯日线，转增除权后）
SHARES = 3.1392                    # 亿股 = 313,916,240 股（2026H1 权益分派实施公告 第 2 页；无回购专户）
SHARES_PRE = 2.41474031            # 转增前股本（含 4,841 股转股）
TRANSFER = 0.3                     # 每股转增 0.3 股；登记日 2026-10-15，除权日 2026-10-16
COE = 0.09
G_T = 0.025
T0 = 0.197                         # 2026-10-21 → 2026-12-31（年），各年现金流按年末折现

# ---------------- 可转债（联瑞转债 118064） ----------------
CB_ISSUED = 6.95                   # 亿元面值，2026-01-08 发行，6 年，2032-01-07 到期
CB_OUT = 6.94694                   # 截至 2026-09-30 未转股余额 694,694,000 元（2026-10-09 转股结果公告）
CB_PRICE = 48.50                   # 10-16 起转股价（63.05/1.3）
CB_COUPONS = [(0.214, 0.10), (1.214, 0.30), (2.214, 0.60), (3.214, 1.00), (4.214, 1.50), (5.214, 110.0)]
CB_FLOOR_YIELD = 0.03              # 债底折现率（AA 级 5 年期信用债量级，假设）
CB_NEW_SHARES = CB_OUT / CB_PRICE  # 亿股
SHARES_DIL = SHARES + CB_NEW_SHARES

# ---------------- 经调整净现金（2026-06-30，不含可转债） ----------------
FIN = {"货币资金": 2.94001, "交易性金融资产（银行理财）": 8.25238, "一年内到期大额存单/定期": 1.00206,
       "其他流动资产-定期存款本息": 0.17769, "其他非流动资产-一年以上大额存单": 1.49401}
RESTRICTED = 0.26667               # 票据保证金、外汇掉期保证金
SHORT_LOAN = 1.00                  # 信用借款
OP_RESERVE = 0.80                  # 经营备付：约 1 个月付现成本
DIVIDEND_DECLARED = 0.0            # 2025 年度股利已于 6 月付清；中期仅转增
LEASE = 0.25389                    # 租赁负债（含一年内到期）：所有者收益已扣租赁利息，列示不扣
NET_CASH_ADJ = sum(FIN.values()) - RESTRICTED - SHORT_LOAN - OP_RESERVE - DIVIDEND_DECLARED
NON_OP = 0.52785                   # 长期股权投资：东莞君度生益股权投资基金（11.21%），按账面

# ---------------- 2026H1 实际（亿元，2026H1_report 第 62-66、144-148 页） ----------------
H1 = dict(rev=6.29369, cogs=3.89931, tax_add=0.05477, sell=0.09863, admin=0.29983, rd=0.32598,
          other_inc=0.10618, fin_inc=0.01277 + 0.05531 + 0.06922, int_exp=0.05780, fx=-0.13625,
          eq_inc=0.03643, np=1.49017)
H1_CORE_EBIT = (H1["rev"] - H1["cogs"] - H1["tax_add"] - H1["sell"] - H1["admin"] - H1["rd"]
                + H1["other_inc"])
H1_ETR = 0.1227
H1_NOPAT = H1_CORE_EBIT * (1 - H1_ETR)
TAX = 0.125                        # 15% 高新税率扣研发加计
LEASE_INT_AT = 0.0136 * (1 - TAX)  # 租赁利息税后，每年从 NOPAT 扣除
FIN_NET_2026 = 0.14                # 2026 全年净利息（理财/存款收益 − 计入损益的利息支出），税前
EQ_INC_2026 = 0.04                 # 权益法收益（产业基金），常态化

# ---------------- 情景 ----------------
SC = {
    "bear": dict(p=0.25, h2_rev=6.75, h2_m=0.250, mLT=0.195, roic=0.16, roicT=0.12,
                 g=[0.10, 0.07, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.03, 0.025],
                 note="AI 资本开支 2027 年进入消化期；华飞（雅克）、锦艺、百图、壹石通与日系扩产压价；"
                      "液相法项目量价不及规划约一半；NOPAT 率 22.9%→19.5%；增量 ROIC 16%"),
    "base": dict(p=0.50, h2_rev=7.15, h2_m=0.275, mLT=0.235, roic=0.28, roicT=0.20,
                 g=[0.25, 0.21, 0.17, 0.13, 0.10, 0.08, 0.065, 0.05, 0.035, 0.025],
                 note="3,600 吨超纯球硅与 1.6 万吨球铝按募集说明书节奏投产、价格略低于规划；"
                      "既有业务年增 9%-10%；NOPAT 率 24.0%→23.5%；增量 ROIC 28%"),
    "bull": dict(p=0.25, h2_rev=7.70, h2_m=0.295, mLT=0.290, roic=0.38, roicT=0.25,
                 g=[0.38, 0.32, 0.22, 0.16, 0.12, 0.10, 0.08, 0.06, 0.04, 0.025],
                 note="M8/M9 与 HBM 高端填料紧缺延续、提价落地，三期提前并追加产线；"
                      "NOPAT 率 25.0%→29%；增量 ROIC 38%"),
}
YEARS = list(range(2026, 2037))


def run(s, r=COE, g=None, roic=None, mLT=None):
    """返回情景明细。g/roic/mLT 可覆盖（反向 DCF 用）。"""
    g = s["g"] if g is None else g
    roic0 = s["roic"] if roic is None else roic
    roicT = s["roicT"] if roic is None else min(s["roicT"], roic)
    mLT = s["mLT"] if mLT is None else mLT
    h2_nopat = s["h2_rev"] * s["h2_m"] * (1 - TAX)
    rev = [H1["rev"] + s["h2_rev"]]
    for x in g:
        rev.append(rev[-1] * (1 + x))
    nop0 = H1_NOPAT + h2_nopat
    m0 = nop0 / rev[0]
    marg = [m0 + (mLT - m0) * min(i, 5) / 5 for i in range(11)]
    nop = [rev[i] * marg[i] for i in range(11)]
    rc = [roic0] * 6 + [roic0 + (roicT - roic0) * k / 5 for k in range(1, 6)]
    oe, reinv = [], []
    for i in range(1, 11):
        rv = (nop[i + 1] - nop[i]) / rc[i + 1] if i < 10 else nop[i] * G_T / roicT
        reinv.append(rv)
        oe.append(nop[i] - rv - LEASE_INT_AT)
    oe_h2 = h2_nopat - 0.5 * (nop[1] - nop[0]) / rc[1] - LEASE_INT_AT / 2
    pv_list = [oe_h2 / (1 + r) ** T0] + [x / (1 + r) ** (T0 + i + 1) for i, x in enumerate(oe)]
    pv = sum(pv_list)
    oe_T = (nop[10] * (1 + G_T)) * (1 - G_T / roicT) - LEASE_INT_AT
    tv = oe_T / (r - G_T)
    pv_tv = tv / (1 + r) ** (T0 + 10)
    E = pv + pv_tv + NET_CASH_ADJ + NON_OP
    v_debt = (E - CB_OUT) / SHARES
    v_conv = E / SHARES_DIL
    return dict(rev=rev, nop=nop, marg=marg, oe=oe, oe_h2=oe_h2, reinv=reinv, pv=pv, pv_tv=pv_tv,
                E=E, v_debt=v_debt, v_conv=v_conv, v=min(v_debt, v_conv), m0=m0, nop0=nop0,
                tv_share=pv_tv / (pv + pv_tv), rc=rc)


def norm_np_2026(s):
    """2026 正常化归母净利（报表口径，含净利息，剔除汇兑损益等一次性项目）。"""
    return run(s)["nop0"] + FIN_NET_2026 * (1 - TAX) + EQ_INC_2026


def weighted(r=COE, w=None):
    w = w or {k: s["p"] for k, s in SC.items()}
    return sum(w[k] * run(SC[k], r)["v"] for k in SC)


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


def bond_floor():
    return sum(cf / (1 + CB_FLOOR_YIELD) ** t for t, cf in CB_COUPONS) / 100 * CB_OUT


if __name__ == "__main__":
    p = print
    p("== 股本与可转债 ==")
    p(f"转增前股本 {SHARES_PRE * 1e8:,.0f} 股 × 1.3 = {SHARES_PRE * (1 + TRANSFER) * 1e8:,.0f} 股"
      f"（行情字段 313,916,240 股，brief 口径 {SHARES} 亿股）")
    p(f"转增调整后：近一年低点 52.86→{52.86 / 1.3:.2f}；高点 272.54→{272.54 / 1.3:.2f}；"
      f"现价较高点 {PRICE / (272.54 / 1.3) - 1:+.1%}，较低点 {PRICE / (52.86 / 1.3) - 1:+.1%}；"
      f"10-15 收盘 136.01→{136.01 / 1.3:.2f}")
    p(f"未转股面值 {CB_OUT:.4f} 亿；转股价 {CB_PRICE}；全部转股新增 {CB_NEW_SHARES:.4f} 亿股；"
      f"稀释股本 {SHARES_DIL:.4f} 亿股；债底现值（{CB_FLOOR_YIELD:.0%}）{bond_floor():.3f} 亿")
    p(f"转股价值 {PRICE / CB_PRICE * 100:.1f} 元/百元面值；强赎触发价 {CB_PRICE * 1.3:.2f} 元")
    p("\n== 经调整净现金（2026-06-30） ==")
    p(f"金融资产合计 {sum(FIN.values()):.3f} − 受限 {RESTRICTED:.3f} − 短借 {SHORT_LOAN:.2f} − 经营备付 {OP_RESERVE:.2f}"
      f" = {NET_CASH_ADJ:.3f}；租赁负债 {LEASE:.3f} 列示不扣；非经营资产 {NON_OP:.3f}；可转债另按情景取低")
    p(f"H1 核心 EBIT {H1_CORE_EBIT:.4f}（率 {H1_CORE_EBIT / H1['rev']:.2%}）；H1 NOPAT {H1_NOPAT:.4f}")
    p("\n== 2026 正常化归母净利（亿元） ==")
    for k, s in SC.items():
        o = run(s)
        p(f"{k}: 营收 {o['rev'][0]:.2f}，NOPAT {o['nop0']:.3f}（率 {o['m0']:.2%}），正常化归母 {norm_np_2026(s):.2f}")
    rep = H1["np"] + (SC["base"]["h2_rev"] * SC["base"]["h2_m"] + FIN_NET_2026 / 2 + EQ_INC_2026 / 2) * (1 - TAX)
    p(f"基准报表口径 2026E 归母（含 H1 汇兑损失 {H1['fx']:.3f}）≈ {rep:.2f}")
    p("\n== 三情景（股权成本 9%，终值增长 2.5%） ==")
    res = {}
    for k, s in SC.items():
        o = run(s)
        res[k] = o
        gN = [o["nop"][i + 1] / o["nop"][i] - 1 for i in range(5)]
        rr = [o["reinv"][i] / o["nop"][i + 1] for i in range(5)]
        p(f"[{k}] p={s['p']}  {s['note']}")
        p("  营收 " + " ".join(f"{y}:{v:.1f}" for y, v in zip(YEARS, o["rev"])))
        p("  NOPAT " + " ".join(f"{y}:{v:.2f}" for y, v in zip(YEARS, o["nop"])))
        p("  所有者收益 2026H2:{:.2f} ".format(o["oe_h2"]) + " ".join(f"{y}:{v:.2f}" for y, v in zip(YEARS[1:], o["oe"])))
        p(f"  NOPAT 增速 2027-31 {[round(x, 3) for x in gN]}；再投资率 2027-31 {[round(x, 2) for x in rr]}"
          f"（均值 {sum(rr) / 5:.2f}）")
        p(f"  经营价值 {o['pv'] + o['pv_tv']:.2f}（终值占 {o['tv_share']:.1%}）+ 净现金 {NET_CASH_ADJ:.2f} + 非经营 {NON_OP:.2f}"
          f" = 股权 {o['E']:.2f}；债务口径 {o['v_debt']:.2f} 元，转股口径 {o['v_conv']:.2f} 元 → 取低 {o['v']:.2f} 元")
    vw = weighted()
    pv_ratio = PRICE / vw
    band = ("明显低估" if pv_ratio <= 0.75 else "温和低估" if pv_ratio <= 0.90 else
            "大致合理" if pv_ratio <= 1.10 else "偏贵或价值陷阱风险高")
    p("\n== 加权与分档 ==")
    p(f"加权 V {vw:.2f} 元；P/V {pv_ratio:.2f} → {band}")
    p(f"V 不变时：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}-{0.90 * vw:.2f} 温和低估；"
      f"{0.90 * vw:.2f}-{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    v8, v10 = weighted(0.08), weighted(0.10)
    p(f"股权成本 8%：V {v8:.2f}（P/V {PRICE / v8:.2f}）；10%：V {v10:.2f}（P/V {PRICE / v10:.2f}）")
    p("  各情景 8%/10%：" + "；".join(f"{k} {run(SC[k], 0.08)['v']:.2f}/{run(SC[k], 0.10)['v']:.2f}" for k in SC))
    irr = solve(lambda r: run(SC["base"], r)["v"], G_T + 0.0005, 0.30, PRICE)
    p(f"基准情景隐含回报（现值=现价的折现率）{irr:.2%}")
    irr_bull = solve(lambda r: run(SC["bull"], r)["v"], G_T + 0.0005, 0.30, PRICE)
    p(f"  牛市情景隐含回报 {irr_bull:.2%}")
    p("\n== 反向 DCF（基准利润率与 ROIC，2027-2036 年等速增长，之后 2.5%） ==")
    for rc in (0.28, 0.38, 0.50):
        gimp = solve(lambda x: run(SC["base"], g=[x] * 10, roic=rc)["v"], 0.0, 1.5, PRICE)
        o = run(SC["base"], g=[gimp] * 10, roic=rc)
        p(f"  增量 ROIC {rc:.0%}：隐含营收/NOPAT 年增 {gimp:.1%}，2036 年营收 {o['rev'][10]:.0f} 亿、NOPAT {o['nop'][10]:.1f} 亿"
          f"（2026 年的 {o['rev'][10] / o['rev'][0]:.0f} 倍）")
    E_mkt = PRICE * SHARES + CB_OUT
    op_mkt = E_mkt - NET_CASH_ADJ - NON_OP
    p(f"  现价股权+转债 {E_mkt:.1f} 亿，扣净现金与非经营后经营价值 {op_mkt:.1f} 亿 = 2026 基准 NOPAT 的 {op_mkt / res['base']['nop0']:.0f} 倍")
    p("\n== 交叉验证 ==")
    np25, np_ttm, eq = 2.92645, 3.03018, 17.86123
    p(f"市值 {PRICE * SHARES:.2f} 亿；PE 2025 {PRICE * SHARES / np25:.1f}×，TTM {PRICE * SHARES / np_ttm:.1f}×，"
      f"2026 正常化基准 {PRICE * SHARES / norm_np_2026(SC['base']):.1f}×；PB {PRICE * SHARES / eq:.2f}×")
    p("  历史年末 PE 2019-2025：52.3/36.3/55.1/32.2/56.5/47.6/51.2；PB 4.36/4.18/8.72/4.93/7.30/7.93/8.79")
    dps_adj = 0.50 / (1 + TRANSFER)
    p(f"  近 12 月股息 0.50 元/转增前股 = {dps_adj:.3f} 元/现股，股息率 {dps_adj / PRICE:.2%}；无回购")
    ebit_ttm = 3.2455 - 1.4912 + H1_CORE_EBIT
    ev = PRICE * SHARES + CB_OUT + SHORT_LOAN + LEASE - (sum(FIN.values()) - RESTRICTED) - NON_OP
    p(f"  EV {ev:.1f} 亿 / TTM 核心 EBIT {ebit_ttm:.3f} 亿 = {ev / ebit_ttm:.0f}×")
    p(f"  卖方：东财一致预期 2026-28 归母 3.84/5.45/7.72 亿（市值 324.0/PE 84.4、59.5、42.0）；"
      f"基准 2028 年 NOPAT {res['base']['nop'][2]:.2f}、牛市 {res['bull']['nop'][2]:.2f}")
    p("\n== 证伪条件触发后的 V ==")
    F = {
        "F1 2026Q3 单季营收≥3.90 亿且毛利率≥42%": {"bear": 0.15, "base": 0.45, "bull": 0.40},
        "F2 2026Q3 单季毛利率<35% 或 2026 年毛利率<37%": {"bear": 0.45, "base": 0.45, "bull": 0.10},
        "F3 2027 年扣非归母≥5.5 亿且超纯球硅项目二期投产": {"bear": 0.10, "base": 0.40, "bull": 0.50},
        "F4 2027 年营收增速<12% 或超纯球硅项目 2027 年效益<0.30 亿": {"bear": 0.50, "base": 0.40, "bull": 0.10},
    }
    for name, w in F.items():
        p(f"  {name}：V {weighted(w=w):.2f}")
    hi = dict(SC["bull"], h2_rev=8.0, h2_m=0.30, mLT=0.30, roic=0.45, roicT=0.25,
              g=[0.75, 0.68, 0.25, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04, 0.025])
    o = run(hi)
    p(f"  F5 卖方高预期兑现（2027 年扣非归母≥7 亿、2028 年 NOPAT {o['nop'][2]:.1f} 亿≈华创 2028 年 12.03 亿量级，"
      f"营收 {o['rev'][2]:.0f} 亿）：V {o['v']:.2f}，P/V {PRICE / o['v']:.2f}")
    trap = {"bear": 0.40, "base": 0.45, "bull": 0.15}
    p(f"  陷阱信号（5%以上股东减持股份≥总股本 2% 或生益集团关联销售占比<8%）：V {weighted(w=trap):.2f}")
    p("\n== 其他敏感性（不参与加权） ==")
    full_conv = sum(SC[k]['p'] * run(SC[k])['v_conv'] for k in SC)
    p(f"强赎完成、全部转股后按转股口径的加权 V {full_conv:.2f}（V 低于转股价时转股对现股东增值）")
    bf = (NET_CASH_ADJ + NON_OP + run(SC['base'])['pv'] + run(SC['base'])['pv_tv'] - bond_floor()) / SHARES
    p(f"基准情景债务口径改用债底现值 {bond_floor():.3f} 亿：V {bf:.2f}")
