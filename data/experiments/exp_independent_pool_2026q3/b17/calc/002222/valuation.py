#!/usr/bin/env python3
"""福晶科技（002222）独立估值（OI-291 b17，价格日 2026-10-21）。

方法：归母所有者收益 DCF。价值驱动式：所有者收益 = 经营归母净利 − 再投资，
再投资 = 下一年经营归母净利增量 ÷ 增量回报 RONIC。股权成本 9%（敏感性 8%／10%），终值增长 2.5%。
经调整净现金为负，按框架用有杠杆口径（净负债按现规模滚动，扣其税后利息现值，不偿还本金），
另列无杠杆口径（全额扣除）作对照。
在建工程与预付设备款（已付现、尚未形成产出）按归母份额作为「已投入产能抵扣」，
冲减 2026 下半年起的再投资，避免与净负债重复扣减。
贵金属（铂/铱坩埚）按 5-20 年计提折旧，金属本身大部分可回收：基准与乐观情景把超出
实际损耗的折旧按归母份额加回所有者收益，悲观情景不加回。

金额单位：亿元；每股价值：元/股。输入全部写在本脚本内，`python3 valuation.py` 复现正文与 json。
"""

PRICE = 50.63          # 2026-10-21 收盘，元
SHARES = 4.7025        # 亿股，含全部股份；无回购专户、无拟注销股份
COE = 0.09
TG = 0.025
TAX = 0.15             # 母公司及主要子公司高新技术企业税率

# ---- 2026-06-30 资产负债表（2026H1_report 第 28-30、87-88、104-108 页）----
CASH = 4.0693          # 货币资金 406,930,109.70 元
RESTRICTED = 0.2177    # 保函保证金 21,765,095.05 元（受限）
WMP = 0.8800           # 交易性金融资产：银行理财 88,000,000 元（2026-04 授权上限 2 亿，只买银行短期理财）
OP_RESERVE = 0.76      # 经营备付：约 1 个月 TTM 经营现金流出（2025 年 7.95 + 2026H1 5.07 − 2025H1 3.85 = 9.17 亿 ÷ 12）
DIV_PAYABLE = 0.5465   # 应付股利 54,651,303.56 元（2025 年度分红 2026-07-08 派发）
DEBT = 0.43024 + 5.629764 + 0.000463   # 短期借款 + 长期借款 + 一年内到期长期借款（均为信用借款）
LEASE = 0.5464 + 0.1566                # 租赁负债（含一年内到期）：只列示不扣（所有者收益以净利润为起点）
NON_OP = 0.5890 + 0.6669               # 其他非流动金融资产（远致富海等）+ 长期股权投资（杭州科汀 18.38%）
R_DEBT = 0.0175        # 有息负债实际平均利率：2026H1 借款利息 356.7 万 ÷ 期初期末平均借款 4.07 亿，年化

NET_CASH_ADJ = CASH - RESTRICTED + WMP - OP_RESERVE - DIV_PAYABLE - DEBT
NET_DEBT = max(0.0, -NET_CASH_ADJ)
INT_AT = NET_DEBT * R_DEBT * (1 - TAX)          # 净负债税后利息（按现规模滚动）

# 已投入、尚未形成产出的资本：在建工程 2.0494 + 预付工程设备款 1.9512 = 4.0006；
# 母公司本部 1.1551 + 1.2988 全额，子公司部分按约 55% 归母经济份额
SUNK_CREDIT = (1.1551 + 1.2988) + (4.0006 - 1.1551 - 1.2988) * 0.55

# 贵金属：原值 7.4899（2026-06-30），2026E 折旧约 0.39（H1 0.1706 + H2 约 0.22）；
# 实际损耗按原值 2.8%/年 ≈ 0.21；差额约 0.18，归母约 90% → 0.15（2026 年口径，随规模增长）
PM_ADDBACK = 0.15

YEARS = list(range(2027, 2036))   # 显式增长期 2027-2035，2036 起终值

# 2026H1 正常化归母净利（含净利息，剔除一次性）：扣非 1.6469 + 汇兑损失税后归母 0.0367
# − 联营收益 0.0048（杭州科汀列入非经营资产）= 1.6788
H1_NORM = 1.6469 + 0.0367 - 0.0048

SCEN = {
    "bear": dict(p=0.25, h2=1.42, ronic=0.12, ronic_tv=0.10, pm=0.0,
                 g=[-0.08, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]),
    "base": dict(p=0.50, h2=1.87, ronic=0.18, ronic_tv=0.15, pm=PM_ADDBACK,
                 g=[0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03]),
    "bull": dict(p=0.25, h2=2.10, ronic=0.22, ronic_tv=0.18, pm=PM_ADDBACK,
                 g=[0.35, 0.28, 0.20, 0.16, 0.13, 0.10, 0.08, 0.06, 0.04]),
}


def np_norm_2026(s):
    """2026 正常化归母净利（报表口径，含净利息）。"""
    return H1_NORM + s["h2"]


def np_op_2026(s):
    """2026 经营归母净利 = 正常化归母净利 + 净负债税后利息 + 贵金属折旧加回。"""
    return np_norm_2026(s) + INT_AT + s["pm"]


def flows(s, g_list=None, ronic=None, ronic_tv=None):
    """所有者收益流。2026H2 记在 t=0；2027 起记在年中（t = 年份 − 2026 − 0.31）；
    显式期最后一年之后进入终值，终值在显式期末（t = 最后年份 − 2026 + 0.19）。"""
    g_list = s["g"] if g_list is None else g_list
    ronic = s["ronic"] if ronic is None else ronic
    ronic_tv = s["ronic_tv"] if ronic_tv is None else ronic_tv
    nps = [np_op_2026(s)]
    for g in g_list:
        nps.append(nps[-1] * (1 + g))
    nps.append(nps[-1] * (1 + TG))           # 终值首年
    last = 2026 + len(g_list)
    credit = SUNK_CREDIT
    rows = []
    h1_part = H1_NORM + INT_AT / 2 + s["pm"] / 2
    for i in range(len(nps) - 1):
        y = 2026 + i
        r = ronic if y < last else ronic_tv
        reinv = max(0.0, (nps[i + 1] - nps[i]) / r)
        if i == 0:
            npv, reinv = nps[0] - h1_part, reinv / 2
            t = 0.0
        else:
            npv, t = nps[i], y - 2026 - 0.31
        use = min(credit, reinv)
        credit -= use
        rows.append(dict(year=y, np=npv, reinv=reinv, net=reinv - use, oe=npv - (reinv - use), t=t,
                         rate=reinv / npv if npv else 0.0))
    oe_tv = nps[-1] * (1 - TG / ronic_tv)
    return rows, oe_tv, last - 2026 + 0.19


def value(s, coe=COE, levered=True, **kw):
    rows, oe_tv, t_tv = flows(s, **kw)
    pv = sum(r["oe"] / (1 + coe) ** r["t"] for r in rows)
    pv_tv = oe_tv / (coe - TG) / (1 + coe) ** t_tv
    debt_adj = -INT_AT / coe if levered else NET_CASH_ADJ
    eq = pv + pv_tv + debt_adj + NON_OP
    return dict(eq=eq, v=eq / SHARES, pv=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv))


def weighted(coe=COE, levered=True, probs=None):
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    return sum(probs[k] * value(SCEN[k], coe, levered)["v"] for k in SCEN)


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


def implied_irr():
    """基准情景所有者收益流（含终值与净负债口径）使每股现值等于现价的折现率。"""
    return solve(lambda r: value(SCEN["base"], coe=r)["v"], 0.03, 0.20, PRICE)


def implied_np_growth_10y():
    """反向 DCF（再投资约束）：基准 RONIC 18%，2027-2036 十年恒定增速 g，其后 2.5%（RONIC 15%）。"""
    return solve(lambda g: value(SCEN["base"], g_list=[g] * 10)["v"], 0.0, 0.60, PRICE)


def implied_oe_growth_10y():
    """反向 DCF（所有者收益口径）：以基准稳态所有者收益 = 2026 经营归母净利 × (1 − 2.5%/15%) 为起点，
    10 年恒定增速 g、其后 2.5%，不另扣增长再投资。"""
    oe0 = np_op_2026(SCEN["base"]) * (1 - TG / SCEN["base"]["ronic_tv"])
    target = PRICE * SHARES + INT_AT / COE - NON_OP

    def pv(g):
        tot = sum(oe0 * (1 + g) ** k / (1 + COE) ** (k - 0.31) for k in range(1, 11))
        tot += oe0 * (1 + g) ** 10 * (1 + TG) / (COE - TG) / (1 + COE) ** 10.19
        return tot
    return solve(pv, 0.0, 0.60, target)


def implied_perpetual_g():
    """反向 DCF（永续）：基准 2026 经营归母净利起步、RONIC 18% 的永续增长模型隐含增速。"""
    np0 = np_op_2026(SCEN["base"])
    target = PRICE * SHARES + INT_AT / COE - NON_OP
    return solve(lambda g: np0 * (1 + g) * (1 - g / SCEN["base"]["ronic"]) / (COE - g), 0.0, 0.0899, target)


def main():
    mcap = PRICE * SHARES
    print(f"现价 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股（无回购专户）；市值 {mcap:.2f} 亿元")
    print(f"经调整净现金（无杠杆口径）{NET_CASH_ADJ:.2f} 亿 = 货币资金 {CASH:.2f} − 受限 {RESTRICTED:.2f} + 理财 {WMP:.2f}"
          f" − 经营备付 {OP_RESERVE:.2f} − 应付股利 {DIV_PAYABLE:.2f} − 有息负债 {DEBT:.2f}；租赁负债 {LEASE:.2f} 只列示")
    print(f"净负债税后利息 {INT_AT:.3f} 亿/年（利率 {R_DEBT:.2%}），现值 {INT_AT/COE:.2f} 亿；非经营资产 {NON_OP:.2f} 亿；"
          f"已投入产能抵扣 {SUNK_CREDIT:.2f} 亿；贵金属折旧加回（基准/乐观）{PM_ADDBACK:.2f} 亿/年")
    print()
    res = {}
    for k, s in SCEN.items():
        rows, oe_tv, t_tv = flows(s)
        vl, vu = value(s), value(s, levered=False)
        v8, v10 = value(s, 0.08)["v"], value(s, 0.10)["v"]
        res[k] = vl["v"]
        print(f"[{k}] p={s['p']:.2f}  2026 正常化归母净利 {np_norm_2026(s):.2f} 亿（H1 {H1_NORM:.2f} + H2 {s['h2']:.2f}）；"
              f"经营口径 {np_op_2026(s):.2f}")
        for r in rows:
            lab = "2026H2" if r["year"] == 2026 else str(r["year"])
            print(f"   {lab}: 经营归母净利 {r['np']:6.2f}  再投资 {r['reinv']:5.2f}（率 {r['rate']:4.0%}）"
                  f"  抵扣后 {r['net']:5.2f}  所有者收益 {r['oe']:6.2f}")
        print(f"   终值首年所有者收益 {oe_tv:.2f}（再投资率 {TG/s['ronic_tv']:.1%}），终值折现 t={t_tv:.2f}")
        print(f"   增长 2027-2035: {', '.join(f'{x:+.0%}' for x in s['g'])}；终值 {TG:.1%}；"
              f"RONIC {s['ronic']:.0%}（终值 {s['ronic_tv']:.0%}）")
        print(f"   V(有杠杆) {vl['v']:.2f} 元  V(无杠杆全额扣债) {vu['v']:.2f} 元  终值占比 {vl['tv_share']:.0%}"
              f"  V@8% {v8:.2f}  V@10% {v10:.2f}")
        print()
    vw, vwu = weighted(), weighted(levered=False)
    print(f"加权 V（有杠杆）{vw:.2f} 元，P/V {PRICE/vw:.2f}；加权 V（无杠杆）{vwu:.2f} 元，P/V {PRICE/vwu:.2f}")
    print(f"加权 V @8% {weighted(0.08):.2f} 元（P/V {PRICE/weighted(0.08):.2f}）；"
          f"@10% {weighted(0.10):.2f} 元（P/V {PRICE/weighted(0.10):.2f}）")
    print(f"现价隐含回报（基准流）{implied_irr():.2%}")
    print(f"反向 DCF：所有者收益 10 年恒定增速 {implied_oe_growth_10y():.1%}（起点 "
          f"{np_op_2026(SCEN['base'])*(1-TG/0.15):.2f} 亿，不另扣增长再投资）；"
          f"按 RONIC 18% 再投资时归母净利 10 年增速 {implied_np_growth_10y():.1%}；永续增速 {implied_perpetual_g():.2%}")
    print(f"分档价格（V 不变）：明显低估 ≤ {0.75*vw:.2f}；温和低估 ≤ {0.90*vw:.2f}；大致合理 ≤ {1.10*vw:.2f}；偏贵 > {1.10*vw:.2f}")
    print()
    # 证伪情景
    v_r12 = value(SCEN["base"], ronic=0.12, ronic_tv=0.10)["v"]
    v_shift = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    v_up = weighted(probs={"bear": 0.10, "base": 0.40, "bull": 0.50})
    print(f"证伪对照：基准增长但 RONIC 12% → V {v_r12:.2f}；权重移向悲观（50/40/10）→ V {v_shift:.2f}；"
          f"权重移向乐观（10/40/50）→ V {v_up:.2f}；悲观 V {res['bear']:.2f}；乐观 V {res['bull']:.2f}")
    # 交叉验证
    np_ttm, eq_parent = 3.311, 18.968
    print()
    print(f"交叉验证：PE(TTM) {mcap/np_ttm:.1f}x；PE(2026 基准正常化) {mcap/np_norm_2026(SCEN['base']):.1f}x；"
          f"PB {mcap/eq_parent:.2f}x；股息率 {0.20/PRICE:.2%}（无回购）")
    # 营业利润 TTM（2025 3.449 + 2026H1 2.389 − 2025H1 1.611）+ 利息费用 TTM（0.032 + 0.046 − 0.013）
    # − 投资收益与公允价值变动 TTM（0.046 + 0.135 − 0.042）
    ebit_ttm = 3.449 + 2.389 - 1.611 + 0.065 - 0.139
    ev = mcap - NET_CASH_ADJ + 1.785 - NON_OP
    print(f"EV（含少数股东权益账面 1.78）{ev:.1f} 亿；EV/EBIT(TTM {ebit_ttm:.2f}) {ev/ebit_ttm:.1f}x")
    nb = np_norm_2026(SCEN["base"])
    print(f"历史年末 PE 中位约 50x × 2026 基准正常化 {nb:.2f} 亿 = 每股 {50*nb/SHARES:.1f} 元；"
          f"PB 中位约 7.6x × 归母权益 {eq_parent:.2f} = 每股 {7.6*eq_parent/SHARES:.1f} 元")


if __name__ == "__main__":
    main()
