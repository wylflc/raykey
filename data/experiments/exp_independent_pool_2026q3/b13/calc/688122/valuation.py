#!/usr/bin/env python3
"""西部超导（688122）独立估值（OI-291 b13，价格日 2026-10-20）。

用法：python3 valuation.py
输入全部写在脚本内（亿元，另注明者除外），来源见同名公司文件：
  2026H1_report（2026 半年报）、2025_annual_report（2025 审计报告附注）、
  2026Q1_report，以及正文所列网络事实（西安奕材日线）。
方法：
  - 2026 正常化：H1 实际 + H2 估计，剔除公允价值变动、汇兑、按比例剔除非经常性补助、
    减值按收入比例正常化，权益法投资收益不计入经营（联营投资按账面列非经营资产）。
  - 经营所有者收益 = NOPAT − k×Δ营收（增量投入资本），乘归母比例；
  - 经调整净现金为负 → 有杠杆口径：净负债按现规模滚动、不还本，
    扣其税后利息现值（9% 折现）；另列无杠杆（全额扣除）对照。
"""

PRICE = 55.40          # 元/股，2026-10-20 收盘
SHARES = 6.4966        # 亿股（腾讯行情口径，无库存股、无拟注销回购）
COE = 0.09
G_TERM = 0.025
TAX = 0.11             # 正常化有效税率（2025 年 8.5%；2026H1 剔除以前年度调整约 9.0%）

# ---------- 资产负债（2026-06-30，2026H1_report 第 70–72、114–115、155–163 页）----------
CASH = 24.527                  # 货币资金
RESTRICTED = 1.028             # 其他货币资金（承兑、信用证、保函保证金，受限）
STRUCT_DEP = 8.796             # 交易性金融资产中的结构性存款
STRUCT_FROZEN = 0.10           # 结构性存款本金冻结（受限资产表）
DEBT = {"短期借款": 9.752, "长期借款": 14.970, "应付债券（含聚能高合股权融资0.18）": 10.152,
        "一年内到期非流动负债": 5.812, "租赁负债": 0.001}
DIV_PAYABLE = 2.600            # 应付股利（2025 年末期 0.4 元/股，2026-07-22 已付；价格日已除息）
TTM_REVENUE = 51.15
OPER_RESERVE = 0.05 * TTM_REVENUE   # 经营备付：TTM 营收的 5%
INT_RATE = 0.0185              # 有息负债实际平均利率：H1 利息 0.332×2 ÷ 平均有息负债 36.7

# 非经营资产
YC_SHARES = 0.0523             # 亿股：西安奕材持股，由 6-30 账面 3.110 ÷（61.92×(1−4% 限售折扣)）反推
YC_PRICE = 22.67               # 西安奕材 2026-10-20 收盘（东财日线）
YC_COST = 0.4708               # 最初投资成本
JX_BOOK, JX_COST = 0.2304, 0.0974   # 健信超导 6-30 账面与成本（未核价格日市价）
OTHER_EQUITY = 0.3186          # 其他权益工具投资（天大股份等，非上市）
ASSOCIATES = 2.0667            # 长期股权投资（西安欧中、汉唐检测等联营，按账面）
GAIN_TAX = 0.15

# ---------- 2026H1 实际（2026H1_report 第 74–75、169–173 页；分部见第 169 页）----------
H1 = dict(rev=26.119, gp=7.860, opex=4.579,      # 税金及附加0.150+销售0.154+管理1.669+研发2.607
          oi_recurring=0.225, oi_nonrec=0.254,     # 其他收益 0.479 中非经常性补助 0.254
          interest=0.28)                           # 利息费用0.332−利息收入0.054；汇兑损失0.071 视为一次性
H1_SEG = {"高端钛合金": (11.996, 4.095), "超导产品": (7.428, 2.118),
          "高温合金": (5.336, 1.225), "其他": (1.358, 0.422)}

# ---------- 情景 ----------
# H2 分部：(收入, 毛利率)；opex_h2 = 税金及附加+销售 0.40 + 管理 + 研发
SCEN = {
    "bear": dict(p=0.25,
                 h2_seg={"高端钛合金": (11.0, 0.31), "超导产品": (7.6, 0.26), "高温合金": (5.4, 0.22), "其他": (1.4, 0.30)},
                 opex_h2=0.40 + 1.75 + 2.40, oi_rec_h2=0.27, oi_nonrec_h2=0.45, grant_keep=0.0,
                 impair_pct=0.030, interest=0.62, minority26=0.25, minority=0.24,
                 growth=[0.02, 0.03, 0.03, 0.03, 0.03], margin=[0.095, 0.10, 0.10, 0.10, 0.10],
                 k=1.4, ronic=0.09,
                 note="钛合金审价降价与新进入者分流成为常态，毛利率停在 31%～33%；研发维持 9% 收入；"
                      "库存减值每年约 3% 收入；营收年增 2%～3%，EBIT 利润率 10%；增量投入 1.4 元/元营收；终值增量回报 9%"),
    "base": dict(p=0.50,
                 h2_seg={"高端钛合金": (12.5, 0.33), "超导产品": (8.2, 0.275), "高温合金": (5.8, 0.235), "其他": (1.4, 0.30)},
                 opex_h2=0.40 + 1.70 + 2.20, oi_rec_h2=0.27, oi_nonrec_h2=0.45, grant_keep=0.5,
                 impair_pct=0.025, interest=0.59, minority26=0.23, minority=0.21,
                 growth=[0.07, 0.08, 0.08, 0.07, 0.06], margin=[0.13, 0.14, 0.145, 0.15, 0.15],
                 k=1.25, ronic=0.11,
                 note="H2 与 2025H2 相当（军品收货确认部分后移），2027 起十五五批产与民机、燃机、MRI/MCZ 拉动营收年增 6%～8%；"
                      "EBIT 利润率由 12.3% 修复到 15%（低于 2025 年核心 18.8%，降价视为结构性）；增量投入 1.25 元/元营收；终值增量回报 11%"),
    "bull": dict(p=0.25,
                 h2_seg={"高端钛合金": (14.0, 0.35), "超导产品": (8.8, 0.29), "高温合金": (6.2, 0.25), "其他": (1.5, 0.30)},
                 opex_h2=0.40 + 1.65 + 2.00, oi_rec_h2=0.27, oi_nonrec_h2=0.45, grant_keep=1.0,
                 impair_pct=0.020, interest=0.57, minority26=0.21, minority=0.19,
                 growth=[0.14, 0.14, 0.12, 0.11, 0.10], margin=[0.165, 0.175, 0.185, 0.19, 0.19],
                 k=1.0, ronic=0.14,
                 note="军品与 C919/CJ-1000 放量、聚变（BEST 等）与 MRI/MCZ/量子带动超导，高温合金燃机外贸放量；"
                      "营收年增 10%～14%，EBIT 利润率回到 19%；周转改善，增量投入 1.0 元/元营收；终值增量回报 14%"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def adjusted_net_cash():
    debt = sum(DEBT.values())
    cash_like = CASH - RESTRICTED + STRUCT_DEP - STRUCT_FROZEN
    return cash_like - OPER_RESERVE - debt - DIV_PAYABLE, debt, cash_like


def non_operating():
    yc = YC_SHARES * YC_PRICE
    yc_net = yc - max(yc - YC_COST, 0) * GAIN_TAX
    jx_net = JX_BOOK - max(JX_BOOK - JX_COST, 0) * GAIN_TAX
    return dict(西安奕材=yc_net, 健信超导=jx_net, 其他权益工具=OTHER_EQUITY, 联营投资=ASSOCIATES,
                合计=yc_net + jx_net + OTHER_EQUITY + ASSOCIATES, 奕材市值=yc)


def normalize_2026(s):
    rev_h2 = sum(r for r, _ in s["h2_seg"].values())
    gp_h2 = sum(r * m for r, m in s["h2_seg"].values())
    rev = H1["rev"] + rev_h2
    gp = H1["gp"] + gp_h2
    opex = H1["opex"] + s["opex_h2"]
    oi = H1["oi_recurring"] + s["oi_rec_h2"] + s["grant_keep"] * (H1["oi_nonrec"] + s["oi_nonrec_h2"])
    impair = s["impair_pct"] * rev
    ebit = gp - opex + oi - impair
    pretax = ebit - s["interest"]
    ni = pretax * (1 - TAX)
    parent = ni * (1 - s["minority26"])
    return dict(rev=rev, gp=gp, opex=opex, oi=oi, impair=impair, ebit=ebit,
                margin=ebit / rev, pretax=pretax, ni=ni, parent=parent)


def path(s):
    n = normalize_2026(s)
    rev, rows = n["rev"], []
    for g, m in zip(s["growth"], s["margin"]):
        new = rev * (1 + g)
        nopat = new * m * (1 - TAX)
        reinv = s["k"] * (new - rev)
        oe = (nopat - reinv) * (1 - s["minority"])
        rows.append(dict(rev=new, nopat=nopat, reinv=reinv, oe=oe, growth=g, margin=m))
        rev = new
    nopat_t1 = rows[-1]["nopat"] * (1 + G_TERM)
    oe_term = nopat_t1 * (1 - G_TERM / s["ronic"]) * (1 - s["minority"])
    return n, rows, oe_term


def value(s, coe=COE, levered=True):
    n, rows, oe_term = path(s)
    pv_oe = sum(r["oe"] / (1 + coe) ** (i + 1) for i, r in enumerate(rows))
    tv = oe_term / (coe - G_TERM)
    pv_tv = tv / (1 + coe) ** len(rows)
    op = pv_oe + pv_tv
    nca, debt, _ = adjusted_net_cash()
    nonop = non_operating()["合计"]
    if nca < 0 and levered:
        debt_adj = -nca * INT_RATE * (1 - TAX) / coe      # 净负债税后利息永续现值
        eq = op - debt_adj + nonop
    else:
        debt_adj = -nca
        eq = op + nca + nonop
    return dict(v=eq / SHARES, eq=eq, op=op, pv_oe=pv_oe, pv_tv=pv_tv, tv_share=pv_tv / op,
                debt_adj=debt_adj, nonop=nonop, rows=rows, n=n, oe_term=oe_term)


def weighted(coe=COE, levered=True):
    return sum(s["p"] * value(s, coe, levered)["v"] for s in SCEN.values())


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: value(SCEN["base"], r)["v"], 0.03, 0.20, PRICE)


def reverse_dcf():
    """现价隐含：以基准 2026 正常化稳态所有者收益为起点的 10 年增速（其后 2.5%）与永续增速。"""
    s = SCEN["base"]
    n = normalize_2026(s)
    oe0 = n["ebit"] * (1 - TAX) * (1 - G_TERM / s["ronic"]) * (1 - s["minority"])
    nca, _, _ = adjusted_net_cash()
    target = PRICE * SHARES + (-nca) * INT_RATE * (1 - TAX) / COE - non_operating()["合计"]

    def pv10(g):
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= 1 + g
            pv += oe / (1 + COE) ** t
        return pv + oe * (1 + G_TERM) / (COE - G_TERM) / (1 + COE) ** 10

    g10 = solve(pv10, -0.05, 0.60, target)
    g_perp = (target * COE - oe0) / (target + oe0)
    return oe0, target, g10, g_perp


# ---------- 分部（基准，交叉验证用）----------
# 2026 正常化 EBIT 按分部拆分：高温合金参照子公司聚能高合（2026H1 净利率 12.9%，第 184 页），
# 超导参照线材/磁体子公司高盈利（2025 线材净利 1.87/营收 6.87，第 92 页），钛合金取余数。
# 归母比例：钛合金 100%；超导约 60%（线材 65%、磁体 34.82%、合肥聚能 26.917%，第 182 页）；高温合金 47.29%。
SEG = {  # rev26, ebit26_margin, growth 2027-31, margin2031, k, ronic, parent_share
    "高端钛合金": (24.50, None, 0.05, 0.135, 1.30, 0.10, 1.00),
    "超导产品": (15.63, 0.140, 0.10, 0.160, 1.10, 0.12, 0.60),
    "高温合金": (11.14, 0.130, 0.12, 0.140, 1.20, 0.11, 0.4729),
    "其他": (2.76, 0.110, 0.03, 0.110, 1.00, 0.09, 0.90),
}


def segment_check(coe=COE):
    total_ebit = normalize_2026(SCEN["base"])["ebit"]
    known = sum(r * m for r, m, *_ in SEG.values() if m is not None)
    out = {}
    for name, (rev, m0, g, m5, k, ronic, ps) in SEG.items():
        ebit0 = (total_ebit - known) if m0 is None else rev * m0
        m0 = ebit0 / rev
        pv, r0 = 0.0, rev
        for t in range(1, 6):
            r1 = r0 * (1 + g)
            m = m0 + (m5 - m0) * t / 5
            oe = (r1 * m * (1 - TAX) - k * (r1 - r0)) * ps
            pv += oe / (1 + coe) ** t
            r0 = r1
        oe_t = r0 * m5 * (1 - TAX) * (1 + G_TERM) * (1 - G_TERM / ronic) * ps
        pv += oe_t / (coe - G_TERM) / (1 + coe) ** 5
        out[name] = dict(ebit0=ebit0, m0=m0, parent_nopat0=ebit0 * (1 - TAX) * ps, value=pv)
    return out


def cross_checks():
    nca, _, _ = adjusted_net_cash()
    mcap = PRICE * SHARES
    base26 = normalize_2026(SCEN["base"])
    ebit25_core = 10.45 - 1.044 - 0.101 + 0.524   # 2025 营业利润 − 公允价值 − 权益法收益 + 财务费用（2025 附注第 82–83 页）
    ev = mcap - nca + 7.806 - non_operating()["合计"]   # 少数股东权益按账面
    yc = non_operating()
    yc_930 = YC_SHARES * 26.92 * 0.99
    return dict(mcap=mcap, ev=ev, ev_ebit26=ev / base26["ebit"], ev_ebit25=ev / ebit25_core, ebit25_core=ebit25_core,
                pe_ttm=mcap / 6.38, pe_kf=mcap / 3.45, pb=mcap / 72.251, div_yield=(0.40 + 0.20) / PRICE,
                q3_fv_loss=3.110 - yc_930, yc_value=yc["奕材市值"])


def main():
    nca, debt, cash_like = adjusted_net_cash()
    no = non_operating()
    print("== 经调整净现金（2026-06-30，亿元）==")
    print(f"现金类 {cash_like:.2f}（货币资金 {CASH} − 受限 {RESTRICTED} + 结构性存款 {STRUCT_DEP} − 冻结 {STRUCT_FROZEN}）")
    print(f"− 经营备付 {OPER_RESERVE:.2f} − 有息负债 {debt:.2f} − 应付股利 {DIV_PAYABLE} = {nca:.2f}")
    print(f"有杠杆口径：净负债 {-nca:.2f} × {INT_RATE:.2%} × (1−{TAX}) ÷ {COE} = 税后利息现值 {(-nca)*INT_RATE*(1-TAX)/COE:.2f}")
    print("非经营资产：" + "，".join(f"{k} {v:.2f}" for k, v in no.items()))
    print()
    print("== 2026 正常化（亿元）==")
    for k, s in SCEN.items():
        n = normalize_2026(s)
        print(f"{k}: 营收 {n['rev']:.2f} 毛利 {n['gp']:.2f}（{n['gp']/n['rev']:.1%}） 费用 {n['opex']:.2f} 其他收益 {n['oi']:.2f} "
              f"减值 {n['impair']:.2f} EBIT {n['ebit']:.2f}（{n['margin']:.1%}） 利润总额 {n['pretax']:.2f} "
              f"净利 {n['ni']:.2f} 归母 {n['parent']:.2f}")
    print()
    print("== 三情景（9%，有杠杆口径为准）==")
    for k, s in SCEN.items():
        r = value(s)
        u = value(s, levered=False)
        print(f"{k} p={s['p']:.2f}: V={r['v']:.2f} 元/股（经营现值 {r['op']:.1f}，其中终值 {r['tv_share']:.0%}；"
              f"净负债扣减 {r['debt_adj']:.2f}；非经营 {r['nonop']:.2f}）；无杠杆全额扣除 V={u['v']:.2f}")
        for y, row in zip(YEARS, r["rows"]):
            print(f"   {y}: 营收 {row['rev']:.1f}（{row['growth']:+.0%}） EBIT率 {row['margin']:.1%} NOPAT {row['nopat']:.2f} "
                  f"再投资 {row['reinv']:.2f} 归母所有者收益 {row['oe']:.2f}")
        reinv_rate = sum(x["reinv"] for x in r["rows"]) / sum(x["nopat"] for x in r["rows"])
        n0 = r["n"]
        inc = (r["rows"][-1]["nopat"] - n0["ebit"] * (1 - TAX)) / sum(x["reinv"] for x in r["rows"])
        print(f"   终值归母所有者收益 {r['oe_term']:.2f}；2027-31 再投资率 {reinv_rate:.0%}；增量回报 {inc:.1%}")
    vw = weighted()
    vu = weighted(levered=False)
    print()
    print(f"加权 V = {vw:.2f} 元/股，P/V = {PRICE/vw:.2f}；无杠杆口径加权 V = {vu:.2f}，P/V = {PRICE/vu:.2f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}；10%：加权 V = {weighted(0.10):.2f}")
    for c in (0.08, 0.10):
        print(f"   {c:.0%} 各情景：" + "，".join(f"{k} {value(s, c)['v']:.2f}" for k, s in SCEN.items()))
    print(f"现价隐含回报（基准情景所有者收益流）= {implied_irr():.2%}")
    oe0, target, g10, gp = reverse_dcf()
    print(f"反向 DCF：基准稳态所有者收益起点 {oe0:.2f} 亿，需覆盖 {target:.1f} 亿 → 10 年年增 {g10:.1%}（其后 2.5%），或永续增速 {gp:.1%}")
    print()
    print("== 分档价格（V 不变）==")
    print(f"≤0.75 明显低估：≤ {0.75*vw:.2f}；0.75～0.90：{0.75*vw:.2f}～{0.90*vw:.2f}；0.90～1.10：{0.90*vw:.2f}～{1.10*vw:.2f}；>1.10：> {1.10*vw:.2f}")
    print()
    print("== 分部交叉验证（基准，9%，归母经营价值，亿元）==")
    sc = segment_check()
    for k, v in sc.items():
        print(f"{k}: 2026 正常化 EBIT {v['ebit0']:.2f}（{v['m0']:.1%}），归母 NOPAT {v['parent_nopat0']:.2f}，经营价值 {v['value']:.1f}")
    seg_sum = sum(v["value"] for v in sc.values())
    seg_v = (seg_sum - value(SCEN["base"])["debt_adj"] + non_operating()["合计"]) / SHARES
    print(f"分部合计 {seg_sum:.1f}（一体化基准经营现值 {value(SCEN['base'])['op']:.1f}）→ 每股 {seg_v:.2f} 元")
    cc = cross_checks()
    print()
    print("== 其他交叉验证 ==")
    print(f"市值 {cc['mcap']:.1f}；PE(TTM 归母 6.38) {cc['pe_ttm']:.1f}×；PE(TTM 扣非 3.45) {cc['pe_kf']:.1f}×；PB {cc['pb']:.2f}×；"
          f"未来一年股息率（0.40+0.20）{cc['div_yield']:.2%}，无回购")
    print(f"EV（市值+经调整净负债+少数股东账面−非经营）{cc['ev']:.1f}：÷2026 正常化基准 EBIT = {cc['ev_ebit26']:.1f}×；"
          f"÷2025 核心 EBIT {cc['ebit25_core']:.2f} = {cc['ev_ebit25']:.1f}×")
    print(f"三季度估计：西安奕材 9-30 收盘 26.92 → 持仓约 {YC_SHARES*26.92*0.99:.2f} 亿，较 6-30 账面 3.110 公允价值变动约 −{cc['q3_fv_loss']:.2f} 亿（税前）；"
          f"10-20 市值 {cc['yc_value']:.2f} 亿")
    print()
    print("== 证伪触发后的 V ==")
    b, m, u = (value(SCEN[k])["v"] for k in ("bear", "base", "bull"))
    print(f"F1 2026 年报扣非归母 < 3.0 亿且钛合金毛利率 < 32% → 取熊市 V = {b:.2f}")
    print(f"F2 2026 三季报：前三季度扣非归母 < 2.2 亿（Q3 单季 < 0.65 亿）→ 熊/基准各半 V = {0.5*b+0.5*m:.2f}")
    print(f"F3 2027 中报：钛合金收入同比 ≥ +20% 且毛利率 ≥ 38%、扣非归母 ≥ 3.5 亿 → 基准/牛市各半 V = {0.5*m+0.5*u:.2f}")
    s_k = dict(SCEN["base"], k=1.5)
    print(f"F4 2026 年末存货+应收（含票据）> 100 亿或全年经营现金流 < 1 亿 → 基准 k=1.5：V = {value(s_k)['v']:.2f}；加权 V = "
          f"{0.25*b + 0.5*value(s_k)['v'] + 0.25*u:.2f}")
    print(f"F5 2027 年超导产品收入 ≥ 22 亿且毛利率 ≥ 30% → 权重改 0.15/0.50/0.35：V = {0.15*b+0.5*m+0.35*u:.2f}")


if __name__ == "__main__":
    main()
