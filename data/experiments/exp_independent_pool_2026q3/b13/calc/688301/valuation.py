# -*- coding: utf-8 -*-
"""奕瑞科技（688301）独立估值（OI-291 b13 深度版）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。全部输入写在本文件内，来源见同批 companies/688301_奕瑞科技.md。
口径：归母所有者收益 DCF（分部：X 线业务 + 硅基微显示背板），经调整净现金为负，按框架用有杠杆口径。
"""

PRICE = 77.70                 # 2026-10-20 收盘
SHARES = 3.13409395           # 亿股，2026H1 报告第 74 页：报告期后转股至 313,409,395 股（含回购专户）
TREASURY = 0.00141704         # 亿股，回购专户 141,704 股（2026H1 第 73 页，权益分派登记日口径；用于员工持股/激励，不注销）
COE = 0.09
VAL_DATE = 2026.80            # 2026-10-20

# ---------------- 资产负债（2026-06-30，2026H1 第 84-86、127-128、162-170、205 页） ----------------
CASH = 34.6182                # 货币资金
STRUCT_DEP = 2.2039           # 交易性金融资产：结构性存款、大额存单
RESTRICTED = 0.0000           # 受限货币资金 463.49 元
OP_RESERVE = 2.40             # 经营备付：约 1 个月经营现金流出（H1 经营现金流出 14.59 亿 / 6）
DEBT = {
    "短期借款(含未终止确认贴现0.195)": 2.8405,
    "长期借款": 30.6407,
    "一年内到期长期借款": 0.0424,
    "租赁负债(含一年内到期)": 0.7856 + 0.1775,
}
SHIYA_DEPOSIT = 5.3806        # 视涯科技履约保证金（其他应付款，关联方，可退还）→ 类债务
CB_RESIDUAL_FACE = 1.08712    # 6/30 未转股可转债面值；7/6 摘牌前已几乎全部转股（股本 312,096,294→313,409,395）
CB_CASH_REDEEMED = 0.018      # 估算：1.08712 - 1,313,101 股 × 81.43 元 ≈ 0.018 亿以现金赎回
NON_OP_ASSETS = 1.3600 + 1.5998   # 其他非流动金融资产 1.36 + 长期股权投资 1.60（联营：E-ray、联新医健基金、无锡麦默），账面
DEBT_RATE = 0.023             # 银行借款实际平均利率：H1 银行利息（费用化约 0.23 + 资本化 0.11）×2 / 平均借款约 30.5 亿
TAX_INT = 0.15
HEFEI_PARENT = 1 - 0.1779     # 奕瑞合肥少数股东 17.79%（2026H1 第 194 页）

debt_total = sum(DEBT.values())
NET_CASH_ADJ = CASH + STRUCT_DEP - RESTRICTED - OP_RESERVE - debt_total - SHIYA_DEPOSIT


# ---------------- 情景假设 ----------------
# X 线业务（探测器、核心部件、综合解决方案、配件、租赁等）：2026 = H1 13.20 + H2 估（H2 2025 为 11.30；Q2 2026 同比 +27%）
# 背板业务：2026 = H1 3.51 + H2 估；2026 关联交易预计上限 8.6 亿（视涯），公司 3-4 月 IR 预计背板超 8 亿
SCEN = {
    "bear": dict(
        p=0.30,
        x_rev26=26.0, x_g=[0.05, 0.05, 0.04, 0.04, 0.035, 0.03, 0.03, 0.03, 0.025, 0.02], x_tg=0.02,
        x_m=0.25, x_ronic=0.12,
        b_rev=[7.6, 7.0, 5.5, 5.0, 5.0, 5.0], b_g_after=0.0, b_tg=0.0,
        b_m=[0.15, 0.05, -0.05, -0.03, 0.00, 0.03], b_m_after=0.03, b_ronic=None,
        b_maint=0.6,
        desc="X 线：增速 5%→2%，EBIT 率 25%（国产价格战、关税与集采压价），增量回报 12%；背板：视涯/终端单一客户放量不及预期，2027 年 7.0 亿、2028 年 5.5 亿、2029 年起 5 亿，EBIT 率 5%→−5%→3%（部分产能转产 CMOS 传感器）",
    ),
    "base": dict(
        p=0.50,
        x_rev26=26.7, x_g=[0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03], x_tg=0.025,
        x_m=0.30, x_ronic=0.15,
        b_rev=[8.3, 11.0, 13.0, 14.0, 14.5, 15.0], b_g_after=0.02, b_tg=0.015,
        b_m=[0.21, 0.17, 0.19, 0.19, 0.19, 0.19], b_m_after=0.19, b_ronic=0.12,
        b_maint=0.8,
        desc="X 线：增速 10%→3%，EBIT 率 30%（2024-2026 中枢；含 2025 年水平的常规补助，H1 新增补助不外推；剔除汇兑与股份支付公允价值变动），增量回报 15%；背板：二期转固后 2027 年 11 亿、2030 年 14.5 亿后年增 2%，EBIT 率 19%",
    ),
    "bull": dict(
        p=0.20,
        x_rev26=27.2, x_g=[0.14, 0.12, 0.11, 0.10, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03], x_tg=0.025,
        x_m=0.33, x_ronic=0.18,
        b_rev=[8.6, 14.0, 18.0, 21.0, 23.0, 24.0], b_g_after=0.03, b_tg=0.02,
        b_m=[0.23, 0.22, 0.24, 0.24, 0.24, 0.24], b_m_after=0.24, b_ronic=0.15,
        b_maint=0.8,
        desc="X 线：CT 全链、球管、工业与海外放量，增速 14%→3%，EBIT 率 33%（H1 新增补助大部分持续），增量回报 18%；背板：终端客户产品成功并新增客户，2031 年 24 亿，EBIT 率 24%",
    ),
}

X_REV25 = 22.51 - 0.56          # 2025 X 线收入（总收入 − 背板 0.56）
X_TAX = 0.12                    # 高新 15% 减研发加计扣除（H1 实际所得税率 11.2%）
X_DA26 = 2.90                   # X 线业务折旧摊销（H1 合计 2.26 亿，年化 4.5；合肥约 1.6）
X_WC_INT = 0.35                 # 增量营运资金 / 增量收入
X_FA_INT = 0.25                 # 2029 起增量固定资产 / 增量收入（海宁二期投产后留有产能余量）
X_COMMITTED = {2026.5: 2.5, 2027: 6.0, 2028: 5.0}   # 海宁二期剩余约 12.6 亿 + 合肥研发基地剩余部分
X_CAPEX_PAYABLE = 0.5            # 6/30 应付长期资产款 3.23 亿高于常态，超出部分 H2 付现（X 线 0.5、背板 1.5）
X_LIFE = 12.0

B_TAX = [0.12, 0.12, 0.15, 0.15, 0.15, 0.15]
B_DA = [1.6, 3.3, 3.4, 3.4, 3.4, 3.4]           # 二期 18 亿预算项目 2026H2 转固
B_COMMITTED = {2026.5: 1.5, 2027: 1.2}           # 二期剩余预算约 2.7 亿
B_CAPEX_PAYABLE = 1.5
B_CAPACITY_REV = 20.0                            # 两期合计可支撑收入约 20 亿（估）
B_FA_INT_NEW = 0.9                               # 超出产能后每 1 元新增收入需固定资产约 0.9 元
B_WC_INT = 0.10                                  # 30 天账期

YEARS = list(range(2027, 2037))


def xray_flows(s):
    """返回 [(t, OE)]（含 2026H2 存根），以及终值所需的末年 NOPAT 与参数。"""
    flows = []
    rev26 = s["x_rev26"]
    # 2026H2 存根
    h2_rev = rev26 - 13.20
    nopat_h2 = h2_rev * s["x_m"] * (1 - X_TAX)
    da_h2 = X_DA26 / 2
    capex_h2 = da_h2 + X_COMMITTED[2026.5] + X_CAPEX_PAYABLE
    dwc_h2 = X_WC_INT * (rev26 - X_REV25) / 2
    flows.append((0.1, nopat_h2 + da_h2 - capex_h2 - dwc_h2, nopat_h2))
    rev_prev, da = rev26, X_DA26
    growth_capex_prev = X_COMMITTED[2026.5] * 2
    rows = []
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["x_g"][i])
        da = da + growth_capex_prev / X_LIFE
        nopat = rev * s["x_m"] * (1 - X_TAX)
        growth_capex = X_COMMITTED.get(y, X_FA_INT * (rev - rev_prev))
        capex = da + growth_capex
        dwc = X_WC_INT * (rev - rev_prev)
        oe = nopat + da - capex - dwc
        flows.append(((y - VAL_DATE) - 0.5, oe, nopat))
        rows.append((y, rev, nopat, growth_capex + dwc, oe))
        rev_prev, growth_capex_prev = rev, growth_capex
    return flows, rows


def backplane_flows(s):
    flows, rows = [], []
    revs = s["b_rev"]
    # 2026H2 存根
    h2_rev = revs[0] - 3.51
    nopat_h2 = h2_rev * s["b_m"][0] * (1 - B_TAX[0])
    da_h2 = B_DA[0] / 2
    capex_h2 = da_h2 * s["b_maint"] + B_COMMITTED[2026.5] + B_CAPEX_PAYABLE
    dwc_h2 = B_WC_INT * (h2_rev - 3.51)
    flows.append((0.1, (nopat_h2 + da_h2 - capex_h2 - dwc_h2) * HEFEI_PARENT, nopat_h2 * HEFEI_PARENT))
    rev_prev = revs[0]
    for i, y in enumerate(YEARS):
        k = i + 1
        if k < len(revs):
            rev = revs[k]
            m = s["b_m"][k]
            tax = B_TAX[k]
            da = B_DA[k]
        else:
            rev = rev_prev * (1 + s["b_g_after"])
            m = s["b_m_after"]
            tax = 0.15
            da = B_DA[-1]
        nopat = rev * m * (1 - tax)
        maint = da * s["b_maint"]
        growth_capex = B_COMMITTED.get(y, 0.0)
        if rev > B_CAPACITY_REV:
            growth_capex += B_FA_INT_NEW * max(0.0, rev - max(rev_prev, B_CAPACITY_REV))
        dwc = B_WC_INT * (rev - rev_prev)
        oe = (nopat + da - maint - growth_capex - dwc) * HEFEI_PARENT
        flows.append(((y - VAL_DATE) - 0.5, oe, nopat * HEFEI_PARENT))
        rows.append((y, rev, nopat * HEFEI_PARENT, (maint - da + growth_capex + dwc) * HEFEI_PARENT, oe))
        rev_prev = rev
    return flows, rows


def terminal(nopat_last, g, ronic, r, t_last):
    """价值驱动式终值：OE_{T+1} = NOPAT_{T+1} × (1 − g/RONIC)。"""
    nopat_next = nopat_last * (1 + g)
    reinvest = 0.0 if (ronic is None or g <= 0) else g / ronic
    tv = nopat_next * (1 - reinvest) / (r - g)
    return tv / (1 + r) ** t_last


def equity_value(s, r, include_interest=True):
    xf, _ = xray_flows(s)
    bf, _ = backplane_flows(s)
    pv = 0.0
    for t, oe, _ in xf + bf:
        pv += oe / (1 + r) ** t
    t_last = xf[-1][0]
    tv_x = terminal(xf[-1][2], s["x_tg"], s["x_ronic"], r, t_last)
    tv_b = terminal(bf[-1][2], s["b_tg"], s["b_ronic"], r, t_last)
    pv_ops = pv + tv_x + tv_b
    pv_int = (-NET_CASH_ADJ) * DEBT_RATE * (1 - TAX_INT) / r if (include_interest and NET_CASH_ADJ < 0) else 0.0
    eq_levered = pv_ops - pv_int + NON_OP_ASSETS
    eq_unlevered = pv_ops + NET_CASH_ADJ + NON_OP_ASSETS
    return dict(pv_ops=pv_ops, tv=tv_x + tv_b, pv_int=pv_int, eq_lev=eq_levered, eq_unlev=eq_unlevered)


def per_share(eq):
    """可转债逐情景取低：债务法（6/30 股本 + 未转股面值全额扣除）vs 全部转股法（现股本）。"""
    v_conv = eq / SHARES
    v_debt = (eq - CB_RESIDUAL_FACE) / (SHARES - 0.01313101)
    return min(v_conv, v_debt), v_conv, v_debt


def irr_base(s):
    target = PRICE * SHARES
    lo, hi = 0.03, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if equity_value(s, mid)["eq_lev"] > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(oe0, r=COE, tg=0.025):
    """现价隐含：(1) 10 年所有者收益恒定增速（之后 2.5% 永续）；(2) 直接永续增速。"""
    target = PRICE * SHARES - NON_OP_ASSETS + (-NET_CASH_ADJ) * DEBT_RATE * (1 - TAX_INT) / r

    def pv(g):
        v, oe = 0.0, oe0
        for k in range(1, 11):
            oe *= (1 + g)
            v += oe / (1 + r) ** (k - 0.3)
        v += oe * (1 + tg) / (r - tg) / (1 + r) ** (10 - 0.3)
        return v
    lo, hi = -0.2, 0.5
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv(mid) < target:
            lo = mid
        else:
            hi = mid
    g10 = (lo + hi) / 2
    gp = (target * r - oe0) / (target + oe0)
    return g10, gp


def normalized_np_2026():
    """2026 正常化归母净利（报表口径，含净利息，剔除汇兑、股份支付公允价值变动、可转债利息与非经常性损益）。"""
    out = {}
    for k, s in SCEN.items():
        x_ebit = s["x_rev26"] * s["x_m"]
        b_ebit = s["b_rev"][0] * s["b_m"][0]
        net_int = -0.20                        # 2026 银行借款利息费用化约 0.5 亿、利息收入约 0.34 亿（可转债利息 H1 约 0.43 亿不再发生，剔除）
        pre = x_ebit + b_ebit + net_int
        tax = x_ebit * X_TAX + b_ebit * B_TAX[0] + net_int * X_TAX
        # 少数股东：奕瑞合肥 17.79% ×（背板 EBIT − 合肥借款利息约 0.25 亿）税后；其他非全资子公司合计约 −0.03 亿（H1 为负）
        minority = (b_ebit * (1 - B_TAX[0]) - 0.25 * (1 - B_TAX[0])) * (1 - HEFEI_PARENT) - 0.03
        out[k] = pre - tax - minority
    return out


def mixed_scen(x_key, b_key):
    """X 线取 x_key 情景、背板取 b_key 情景（概率取 x_key 的）。"""
    s = dict(SCEN[x_key])
    for k, v in SCEN[b_key].items():
        if k.startswith("b_"):
            s[k] = v
    return s


def mixed_v(x_key, b_key, r=COE):
    return per_share(equity_value(mixed_scen(x_key, b_key), r)["eq_lev"])[0]


def weighted_v(probs, b_override=None, x_override=None, r=COE):
    """按 probs 加权；b_override / x_override 把各情景的背板 / X 线替换为指定情景。"""
    tot = 0.0
    for k, p in probs.items():
        xk = x_override or k
        bk = b_override or k
        tot += p * mixed_v(xk, bk, r)
    return tot


def segment_pv(s, r=COE):
    xf, _ = xray_flows(s)
    bf, _ = backplane_flows(s)
    t_last = xf[-1][0]
    pv_x = sum(oe / (1 + r) ** t for t, oe, _ in xf) + terminal(xf[-1][2], s["x_tg"], s["x_ronic"], r, t_last)
    pv_b = sum(oe / (1 + r) ** t for t, oe, _ in bf) + terminal(bf[-1][2], s["b_tg"], s["b_ronic"], r, t_last)
    return pv_x, pv_b


def main():
    print("== 奕瑞科技 688301 独立估值（价格日 2026-10-20，现价 %.2f）==" % PRICE)
    print("有息负债合计 %.4f；视涯履约保证金 %.4f；现金类 %.4f；经营备付 %.2f" % (debt_total, SHIYA_DEPOSIT, CASH + STRUCT_DEP, OP_RESERVE))
    print("经调整净现金（无杠杆口径）net_cash_adj = %.2f 亿（<0 → 有杠杆口径）" % NET_CASH_ADJ)
    print("非经营资产 %.2f 亿；净负债税后利息现值（9%%）%.2f 亿" % (NON_OP_ASSETS, (-NET_CASH_ADJ) * DEBT_RATE * (1 - TAX_INT) / COE))
    print()
    res = {}
    for k, s in SCEN.items():
        e = equity_value(s, COE)
        v, v_conv, v_debt = per_share(e["eq_lev"])
        v_unlev = per_share(e["eq_unlev"])[0]
        res[k] = v
        print("[%s] p=%.2f  经营现值 %.1f（终值 %.1f，占 %.0f%%）  股权(有杠杆) %.1f 亿 → V=%.2f 元（转股法 %.2f／债务法 %.2f）；无杠杆口径 V=%.2f" % (
            k, s["p"], e["pv_ops"], e["tv"], 100 * e["tv"] / e["pv_ops"], e["eq_lev"], v, v_conv, v_debt, v_unlev))
    vw = sum(SCEN[k]["p"] * res[k] for k in SCEN)
    print()
    print("概率加权 V = %.2f 元；P/V = %.3f" % (vw, PRICE / vw))
    vw_ex_tsy = sum(SCEN[k]["p"] * equity_value(SCEN[k], COE)["eq_lev"] for k in SCEN) / (SHARES - TREASURY)
    vw_unlev = sum(SCEN[k]["p"] * per_share(equity_value(SCEN[k], COE)["eq_unlev"])[0] for k in SCEN)
    print("对照：无杠杆口径（全额扣经调整净负债 %.2f 亿）加权 V = %.2f 元；P/V = %.3f" % (-NET_CASH_ADJ, vw_unlev, PRICE / vw_unlev))
    print("剔除回购专户股份后 V = %.2f 元；P/V = %.3f" % (vw_ex_tsy, PRICE / vw_ex_tsy))
    for r in (0.08, 0.10):
        vr = sum(SCEN[k]["p"] * per_share(equity_value(SCEN[k], r)["eq_lev"])[0] for k in SCEN)
        print("股权成本 %.0f%%：加权 V = %.2f 元" % (100 * r, vr))
    print("基准情景隐含回报（IRR）= %.2f%%" % (100 * irr_base(SCEN["base"])))
    # 反向 DCF：以基准情景 2027 年合计所有者收益的「稳态」版本为起点（NOPAT × (1 − 30%)）
    xs = SCEN["base"]
    x_nopat27 = xs["x_rev26"] * 1.10 * xs["x_m"] * (1 - X_TAX)
    b_nopat27 = xs["b_rev"][1] * xs["b_m"][1] * (1 - B_TAX[1]) * HEFEI_PARENT
    oe0 = (x_nopat27 + b_nopat27) * (1 - 0.30)
    g10, gp = reverse_dcf(oe0)
    print("反向 DCF：起点稳态所有者收益 %.2f 亿（2027 基准 NOPAT %.2f × 70%%）→ 隐含 10 年增速 %.1f%%（之后 2.5%%），或直接永续增速 %.1f%%" % (
        oe0, x_nopat27 + b_nopat27, 100 * g10, 100 * gp))
    print()
    nn = normalized_np_2026()
    print("2026 正常化归母净利：熊 %.2f／基准 %.2f／牛 %.2f 亿" % (nn["bear"], nn["base"], nn["bull"]))
    print()
    print("基准情景逐年（亿元）：年份  X线收入  X线NOPAT  X线再投资  X线OE | 背板收入  背板NOPAT(归母)  背板再投资  背板OE")
    _, xr = xray_flows(SCEN["base"])
    _, br = backplane_flows(SCEN["base"])
    tot_prev = None
    for a, b in zip(xr, br):
        tot = a[4] + b[4]
        gtxt = "" if tot_prev is None else " 合计OE增速 %+.1f%%" % (100 * (tot / tot_prev - 1))
        print("  %d  %6.2f  %6.2f  %6.2f  %6.2f | %6.2f  %6.2f  %6.2f  %6.2f  合计OE %6.2f%s" % (
            a[0], a[1], a[2], a[3], a[4], b[1], b[2], b[3], b[4], tot, gtxt))
        tot_prev = tot
    # 再投资率与增量回报（2027-2031，X 线 + 背板合计）
    nopat = [a[2] + b[2] for a, b in zip(xr, br)]
    reinv = [a[3] + b[3] for a, b in zip(xr, br)]
    rr = sum(reinv[:5]) / sum(nopat[:5])
    x26 = SCEN["base"]["x_rev26"] * SCEN["base"]["x_m"] * (1 - X_TAX)
    b26 = SCEN["base"]["b_rev"][0] * SCEN["base"]["b_m"][0] * (1 - B_TAX[0]) * HEFEI_PARENT
    inc_ret = (nopat[4] - (x26 + b26)) / (sum(reinv[:5]) + X_COMMITTED[2026.5] + B_COMMITTED[2026.5] * HEFEI_PARENT)
    n26 = x26 + b26
    gp = []
    prev = n26
    for v in nopat[:5]:
        gp.append(v / prev - 1)
        prev = v
    print("基准归母经营 NOPAT：2026 %.2f → 2027-2031 增速 %s" % (n26, "、".join("%+.1f%%" % (100 * g) for g in gp)))
    print("基准 2027-2031 再投资率 %.0f%%；增量回报（2031 vs 2026 NOPAT 增量 ÷ 2026H2-2031 净再投资）%.1f%%" % (100 * rr, 100 * inc_ret))
    # 证伪条件触发后的 V（各情景概率不变，只替换对应分部；F4/F5 另改概率）
    P0 = {k: SCEN[k]["p"] for k in SCEN}
    print()
    print("证伪触发后的 V：")
    print("  F1 背板三情景均转熊（X 线各情景不变）V = %.2f" % weighted_v(P0, b_override="bear"))
    print("  F2 X 线三情景均转熊（背板各情景不变）V = %.2f" % weighted_v(P0, x_override="bear"))
    print("  F3 背板三情景均转牛（X 线各情景不变）V = %.2f" % weighted_v(P0, b_override="bull"))
    print("  F4 三季报弱：概率改 0.45/0.45/0.10，V = %.2f" % weighted_v({"bear": 0.45, "base": 0.45, "bull": 0.10}))
    print("  F5 关联定价恶化：背板均转熊且概率改 0.45/0.45/0.10，V = %.2f" % weighted_v({"bear": 0.45, "base": 0.45, "bull": 0.10}, b_override="bear"))
    print("  对照：概率 0.25/0.50/0.25 时 V = %.2f" % weighted_v({"bear": 0.25, "base": 0.50, "bull": 0.25}))
    for k in SCEN:
        px, pb = segment_pv(SCEN[k])
        print("  分部经营现值[%s]：X 线 %.1f 亿，背板（归母）%.1f 亿" % (k, px, pb))
    # 交叉验证：EV/EBIT
    mcap = PRICE * SHARES
    ev = mcap + debt_total + SHIYA_DEPOSIT - CASH - STRUCT_DEP + 4.6320 - NON_OP_ASSETS
    b = SCEN["base"]
    ebit26 = b["x_rev26"] * b["x_m"] + b["b_rev"][0] * b["b_m"][0]
    ebit27 = b["x_rev26"] * (1 + b["x_g"][0]) * b["x_m"] + b["b_rev"][1] * b["b_m"][1]
    print("交叉验证：市值 %.1f 亿，EV（含少数股东权益账面 4.63、减非经营资产）%.1f 亿；EV/EBIT 2026E 基准 %.1f×、2027E %.1f×" % (mcap, ev, ev / ebit26, ev / ebit27))
    # 价格分档
    print("V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵" % (
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
