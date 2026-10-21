#!/usr/bin/env python3
"""688271 联影医疗 独立估值（OI-291 b11，深度版）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，来源见注释与正文。
价格日 2026-10-20，现价 110.00 元，总股本 8.2416 亿股（含回购专户 675.83 万股）。
联网输入（见正文来源）：2026 年 1-8 月公司中标额 +28.8%、Q3 影像招采 +20.64%（众成数科，二手转引），
乙类大型设备集采 2026 年底前落地（2026-07 三部门通知），9-30 美元中间价 6.7351。
最新定期报告 2026 中报（2026-08-20），三季报预约 2026-10-29。
"""

PRICE = 110.00
SHARES = 8.2416                 # 亿股，腾讯行情口径，含回购专户
TREASURY = 0.06758348           # 亿股，2026H1_report 第 2 页：截至 2026-07-31 回购专户 6,758,348 股
SHARES_EX_TREASURY = SHARES - TREASURY
COE = 0.09
TERMINAL_G = 0.025
VAL_YEAR = 2026 + (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 20) / 365.0   # 2026-10-20

# ---------- 一、经调整净现金（2026-06-30，2026H1_report 第 126-128、172、212、217-218、232 页） ----------
CASH = 72.32                    # 货币资金（含受限保证金 0.518、定期存款应收利息 0.205）
TRADING_FA = 17.17              # 交易性金融资产（结构性存款与理财）
RESTRICTED = 0.518              # 保函、信用证等保证金（第 70、232 页）
OPERATING_RESERVE = 10.0        # 经营备付：约 3 周经营现金流出（2026H1 经营流出 79.68 亿 / 26 周 × 3 ≈ 9.2）
INTEREST_DEBT = 15.25 + 0.59 + 2.32   # 短期借款（含票据贴现 2.90）+ 一年内到期非流动负债 + 租赁负债
DIVIDEND_PAYABLE = 1.476        # 应付股利：2025 年度末期 0.18 元/股，2026-07-20 已除息派发
INTERIM_DIVIDEND = 1.0626       # 2026 中期 0.13 元/股，2026-08-20 宣派、09-09 除息（dividend_20260820_156761）
NET_CASH_ADJ = (CASH + TRADING_FA - RESTRICTED - OPERATING_RESERVE
                - INTEREST_DEBT - DIVIDEND_PAYABLE - INTERIM_DIVIDEND)
NON_OPERATING = 1.86 + 1.31     # 长期股权投资 + 其他非流动金融资产（按账面）
# 其他非流动负债 14.32 = 预收产品服务款（第 218 页附注 52），属经营性负债，不作类债务；
# 递延收益 4.75 = 政府补助（第 217-218 页），不作类债务；关联方存款：无（无财务公司）。

# ---------- 二、2026 年正常化归母净利（剔除汇兑、非经常性损益；含税后净利息） ----------
NET_INTEREST_AFTER_TAX = 0.9    # 2026H1 利息收入 0.42 + 理财收益 0.36 − 利息支出 0.155，全年约 1.0，税后约 0.9


def normalized_2026(rev, gm, sell, ga, rd, other_inc, credit_imp, tax_rate=0.12, minority=0.15):
    """经营口径 2026 年归母净利（不含净利息）。rev 亿元，其余为占收入比例或金额。"""
    taxes_surcharge = 0.006 * rev
    misc = 0.25                 # 权益法亏损、手续费、营业外经常性部分
    op = rev * (gm - sell - ga - rd) - taxes_surcharge + other_inc - credit_imp - misc
    return op * (1 - tax_rate) + minority


SCEN_2026 = {
    # 收入：H1 实际 70.52；H2 2025 基数 77.84。bear H2 +5%，base +12.5%，bull +20%
    "bear": dict(rev=70.52 + 77.84 * 1.05, gm=0.463, sell=0.158, ga=0.047, rd=0.148, other_inc=4.3, credit_imp=2.6),
    "base": dict(rev=70.52 + 77.84 * 1.125, gm=0.468, sell=0.154, ga=0.045, rd=0.145, other_inc=4.4, credit_imp=2.3),
    "bull": dict(rev=70.52 + 77.84 * 1.20, gm=0.471, sell=0.151, ga=0.044, rd=0.143, other_inc=4.6, credit_imp=2.1),
}

# ---------- 三、情景参数（2027-2036 显性期，之后 2.5% 永续） ----------
SCENARIOS = {
    "bear": dict(
        p=0.25,
        growth=[0.07, 0.05, 0.07, 0.07, 0.06, 0.055, 0.05, 0.045, 0.04, 0.035],
        margin=[0.095, 0.095, 0.100, 0.105, 0.110, 0.110, 0.115, 0.115, 0.115, 0.115],
        cap_per_rev=1 / 1.2,     # 每 1 元新增收入所需经营资本（含营运资本与长期资产）
        terminal_ronic=0.11,
        h2_2026_fcf=4.0,        # 2026H2 自由现金流（H2 经营现金流约 13 − 资本开支约 9）
    ),
    "base": dict(
        p=0.50,
        growth=[0.15, 0.13, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04],   # 2027 +15%：2026 年 1-8 月公司中标额 +28.8%（众成数科，二手转引）
        margin=[0.118, 0.123, 0.129, 0.135, 0.140, 0.144, 0.147, 0.150, 0.150, 0.150],
        cap_per_rev=1 / 1.6,
        terminal_ronic=0.15,
        h2_2026_fcf=12.0,       # H2 经营现金流约 21 − 资本开支约 9（2025H2 为 26.30 − 10.16）
    ),
    "bull": dict(
        p=0.25,
        growth=[0.20, 0.18, 0.16, 0.14, 0.12, 0.11, 0.10, 0.08, 0.06, 0.04],   # 2028 收入约 232，介于 2026 激励触发值 215 与目标值 239 之间
        margin=[0.132, 0.142, 0.152, 0.160, 0.168, 0.173, 0.177, 0.180, 0.180, 0.180],
        cap_per_rev=1 / 2.0,
        terminal_ronic=0.20,
        h2_2026_fcf=17.0,
    ),
}


def run(name, coe=COE, shares=SHARES, overrides=None, verbose=False):
    s = dict(SCENARIOS[name])
    if overrides:
        s.update(overrides)
    base26 = SCEN_2026[name]
    rev = base26["rev"]
    np26_op = normalized_2026(**base26)
    years = list(range(2027, 2037))
    pv_explicit = 0.0
    rows = []
    reinv_sum = 0.0
    np_prev = np26_op
    for i, y in enumerate(years):
        rev_new = rev * (1 + s["growth"][i])
        np_y = rev_new * s["margin"][i]
        reinv = (rev_new - rev) * s["cap_per_rev"]
        oe = np_y - reinv
        t = (y + 0.5) - VAL_YEAR
        pv = oe / (1 + coe) ** t
        pv_explicit += pv
        reinv_sum += reinv
        rows.append((y, rev_new, np_y, reinv, oe, t, pv))
        rev = rev_new
        np_prev = np_y
    np_term = np_prev * (1 + TERMINAL_G)
    oe_term = np_term * (1 - TERMINAL_G / s["terminal_ronic"])
    t_last = rows[-1][5]
    tv = oe_term / (coe - TERMINAL_G)
    pv_tv = tv / (1 + coe) ** t_last
    pv_h2 = s["h2_2026_fcf"] / (1 + coe) ** 0.1
    equity = pv_explicit + pv_tv + pv_h2 + NET_CASH_ADJ + NON_OPERATING
    v = equity / shares
    reinv_5y = sum(r[3] for r in rows[:5])
    out = dict(name=name, v=v, equity=equity, pv_explicit=pv_explicit, pv_tv=pv_tv, pv_h2=pv_h2,
               tv_share=pv_tv / (pv_explicit + pv_tv + pv_h2), np26_op=np26_op, rows=rows,
               reinv_rate_5y=reinv_5y / sum(r[2] for r in rows[:5]),
               incr_return_5y=((rows[4][2] - np26_op) / reinv_5y) if reinv_5y > 1e-9 else float("nan"),
               rev26=base26["rev"])
    if verbose:
        print(f"\n[{name}] 2026 收入 {base26['rev']:.1f}，2026 经营口径归母净利 {np26_op:.2f}，"
              f"含净利息 {np26_op + NET_INTEREST_AFTER_TAX:.2f}")
        print("  年份   收入    归母净利  再投资   所有者收益  折现年数  现值")
        for (y, r_, n_, ri, oe, t, pv) in rows:
            print(f"  {y}  {r_:7.1f}  {n_:7.2f}  {ri:7.2f}  {oe:8.2f}   {t:5.2f}  {pv:7.2f}")
        print(f"  终值：归母净利 {np_term:.2f}，所有者收益 {oe_term:.2f}，TV {tv:.1f}，现值 {pv_tv:.1f}"
              f"（占经营价值 {out['tv_share']:.1%}）")
        print(f"  显性期现值 {pv_explicit:.1f} + 2026H2 FCF 现值 {pv_h2:.1f} + 经调整净现金 {NET_CASH_ADJ:.2f}"
              f" + 非经营资产 {NON_OPERATING:.2f} = 股权价值 {equity:.1f}")
        print(f"  前 5 年再投资率 {out['reinv_rate_5y']:.1%}，增量回报（2031 归母净利 − 2026）/ 5 年再投资"
              f" {out['incr_return_5y']:.1%}")
        print(f"  每股价值 {v:.2f} 元（含回购专户股本 {shares}）")
    return out


def weighted(coe=COE, shares=SHARES, overrides_by=None):
    tot = 0.0
    vs = {}
    for k in ("bear", "base", "bull"):
        ov = (overrides_by or {}).get(k)
        r = run(k, coe=coe, shares=shares, overrides=ov)
        vs[k] = r["v"]
        tot += SCENARIOS[k]["p"] * r["v"]
    return tot, vs


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


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("=== 688271 联影医疗 独立估值（价格日 2026-10-20，现价 %.2f 元）===" % PRICE)
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} 亿元（现金类 {CASH + TRADING_FA:.2f} − 受限 {RESTRICTED} − 经营备付 "
          f"{OPERATING_RESERVE} − 有息负债 {INTEREST_DEBT:.2f} − 应付及中期股利 {DIVIDEND_PAYABLE + INTERIM_DIVIDEND:.2f}）；"
          f"非经营资产 {NON_OPERATING:.2f}")
    print("经调整净现金为正 → 无杠杆口径；无可转债。")
    print("\n2026 年正常化归母净利（含税后净利息 %.1f）：" % NET_INTEREST_AFTER_TAX)
    for k in ("bear", "base", "bull"):
        n = normalized_2026(**SCEN_2026[k])
        print(f"  {k}: 收入 {SCEN_2026[k]['rev']:.1f}，经营口径 {n:.2f}，含净利息 {n + NET_INTEREST_AFTER_TAX:.2f}")

    res = {k: run(k, verbose=True) for k in ("bear", "base", "bull")}
    vw, vs = weighted()
    pv = PRICE / vw
    print("\n=== 三情景与加权（股权成本 9%）===")
    for k in ("bear", "base", "bull"):
        print(f"  {k}: V = {vs[k]:.2f} 元，概率 {SCENARIOS[k]['p']:.2f}")
    print(f"  加权 V = {vw:.2f} 元；P/V = {pv:.3f} → {verdict(pv)}")

    vw_ex, vs_ex = weighted(shares=SHARES_EX_TREASURY)
    print(f"  剔除回购专户股份（{SHARES_EX_TREASURY:.4f} 亿股）：加权 V = {vw_ex:.2f} 元，P/V = {PRICE / vw_ex:.3f}")

    for c in (0.08, 0.10):
        v_c, vs_c = weighted(coe=c)
        print(f"  股权成本 {c:.0%}：bear {vs_c['bear']:.2f} / base {vs_c['base']:.2f} / bull {vs_c['bull']:.2f}，"
              f"加权 V = {v_c:.2f} 元，P/V = {PRICE / v_c:.3f}")

    irr = solve(lambda r: run("base", coe=r)["v"], 0.03, 0.20, PRICE)
    print(f"\n现价隐含回报（基准情景现金流，含终值与净现金）= {irr:.2%}")
    irr_w = solve(lambda r: weighted(coe=r)[0], 0.03, 0.20, PRICE)
    print(f"（参考：三情景加权现金流的隐含回报 = {irr_w:.2%}）")

    # 反向 DCF (a)：基准利润率、资本强度与终值不变，2027-2036 统一收入增速
    def v_uniform_g(g):
        return run("base", overrides=dict(growth=[g] * 10))["v"]
    g_impl = solve(v_uniform_g, 0.0, 0.40, PRICE)
    print(f"反向 DCF (a)：基准利润率路径与资本强度下，现价隐含 2027-2036 年收入年均增速 {g_impl:.1%}")
    # 反向 DCF (b)：基准增长路径与资本强度不变，统一抬升利润率
    def v_margin_shift(dm):
        m = [x + dm for x in SCENARIOS["base"]["margin"]]
        return run("base", overrides=dict(margin=m))["v"]
    dm_impl = solve(v_margin_shift, 0.0, 0.30, PRICE)
    print(f"反向 DCF (b)：基准增长路径下，需净利率比基准高 {dm_impl * 100:.1f} 个百分点（终局约 "
          f"{(0.15 + dm_impl):.1%}）")
    # 反向 DCF (c)：以基准 2027 所有者收益为起点，10 年所有者收益复合增速
    oe27 = res["base"]["rows"][0][4]
    ev_target = PRICE * SHARES - NET_CASH_ADJ - NON_OPERATING - res["base"]["pv_h2"]

    def ev_oe_growth(g):
        pv = 0.0
        oe = oe27
        for i in range(10):
            t = (2027 + i + 0.5) - VAL_YEAR
            pv += oe / (1 + COE) ** t
            last_t = t
            last = oe
            oe *= (1 + g)
        tv = last * (1 + TERMINAL_G) / (COE - TERMINAL_G)
        return pv + tv / (1 + COE) ** last_t
    g_oe = solve(ev_oe_growth, 0.0, 0.60, ev_target)
    print(f"反向 DCF (c)：以基准 2027 年所有者收益 {oe27:.2f} 亿为起点，现价隐含 10 年所有者收益复合增速 {g_oe:.1%}"
          f"（之后 2.5%）")

    # 敏感性：基准情景的资本强度与终局净利率
    print("\n基准情景敏感性（股权成本 9%）：")
    for sc in (1.2, 1.4, 1.8, 2.2):
        print(f"  销售/资本 {sc:.1f}：base V = {run('base', overrides=dict(cap_per_rev=1 / sc))['v']:.2f}")
    for dm in (-0.02, 0.02, 0.04):
        m = [x + dm * (i + 1) / 10 for i, x in enumerate(SCENARIOS["base"]["margin"])]
        print(f"  终局净利率 {0.15 + dm:.0%}（2027-2036 线性过渡）：base V = {run('base', overrides=dict(margin=m))['v']:.2f}")

    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NON_OPERATING
    n26b = normalized_2026(**SCEN_2026["base"])
    pretax_op_26 = (n26b - 0.15) / 0.88
    print(f"\n交叉验证：市值 {mcap:.1f}，EV {ev:.1f}；EV/2026E 经营税前利润 {ev / pretax_op_26:.1f}×；"
          f"市值/2026E 正常化归母 {mcap / (n26b + NET_INTEREST_AFTER_TAX):.1f}×；PB 4.12×")

    # 证伪条件触发后的独立 V
    print("\n=== 证伪条件触发后的独立 V ===")
    f1 = res["bear"]["v"]
    print(f"F1 2026Q3 单季营收同比 < 5%（< 29.85 亿）或 2026 全年营收 < 152 亿：按 bear 50%/base 50% 重配 → "
          f"{0.5 * vs['bear'] + 0.5 * vs['base']:.2f}")
    f2_ov = {k: dict(cap_per_rev=1 / 1.0) for k in ("bear", "base", "bull")}
    f2_ov["bear"] = dict(cap_per_rev=1 / 0.9)
    v_f2, _ = weighted(overrides_by=f2_ov)
    print(f"F2 2026 年末账龄 1 年以上应收占比 > 30% 且 2026 年经营现金流 < 归母净利 70%：销售/资本降至 1.0（bear 0.9）→ {v_f2:.2f}")
    v_f3 = 0.25 * vs["base"] + 0.75 * vs["bull"]
    print(f"F3 2027 年营收 ≥ 186 亿（2026 激励 2027 触发值）且扣非归母净利率 ≥ 13.5%：bull 75%/base 25% → {v_f3:.2f}")
    f4_ov = {k: dict(margin=[m - 0.015 for m in SCENARIOS[k]["margin"]]) for k in ("bear", "base", "bull")}
    v_f4, _ = weighted(overrides_by=f4_ov)
    print(f"F4 乙类集采中 PET/CT 或放疗中标价降幅 ≥ 30% 且 2027H1 毛利率 < 45%：各情景净利率 −1.5 个百分点 → {v_f4:.2f}")
    f5_ov = {k: dict(cap_per_rev=1 / 2.2) for k in ("bear", "base", "bull")}
    _, vs_f5 = weighted(overrides_by=f5_ov)
    v_f5 = 0.15 * vs_f5["bear"] + 0.50 * vs_f5["base"] + 0.35 * vs_f5["bull"]
    print(f"F5 2026-2027 两年经营现金流合计 ≥ 归母净利合计 × 1.2 且 2027 年末（应收+存货）/营收 ≤ 65%："
          f"销售/资本升至 2.2、概率改为 15/50/35 → {v_f5:.2f}")
    for c in (0.09, 0.08):
        _, vs_c35 = weighted(coe=c, overrides_by=f5_ov)
        print(f"F3 与 F5 同时触发（bull 75%/base 25%，销售/资本 2.2），股权成本 {c:.0%}："
              f"{0.75 * vs_c35['bull'] + 0.25 * vs_c35['base']:.2f}")
    f1_v = 0.5 * vs["bear"] + 0.5 * vs["base"]
    print("\n价格档位（V 不变）：明显低估 ≤ %.2f；温和低估 ≤ %.2f；大致合理 ≤ %.2f；偏贵 > %.2f" %
          (0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    return dict(vw=vw, vs=vs, pv=pv, irr=irr, g_impl=g_impl, dm_impl=dm_impl, g_oe=g_oe,
                f=[f1_v, v_f2, v_f3, v_f4, v_f5])


def summary(out):
    vs = out["vs"]
    v8, _ = weighted(coe=0.08)
    v10, _ = weighted(coe=0.10)
    b = run("base")
    print("\n=== 登记摘要（与 688271.json 一致）===")
    print(f"scenarios v: bear {vs['bear']:.2f} / base {vs['base']:.2f} / bull {vs['bull']:.2f}；"
          f"v_weighted {out['vw']:.2f}；pv {out['pv']:.3f}；v_at_coe_8 {v8:.2f}；v_at_coe_10 {v10:.2f}；"
          f"implied_irr {out['irr']:.4f}")
    print("normalized_parent_np_2026_yi: " + " / ".join(
        f"{k} {normalized_2026(**SCEN_2026[k]) + NET_INTEREST_AFTER_TAX:.2f}" for k in ("bear", "base", "bull")))
    print(f"net_cash_adj_yi {NET_CASH_ADJ:.2f}；non_operating_assets_yi {NON_OPERATING:.2f}；"
          f"base reinvestment_rate {b['reinv_rate_5y']:.3f}；incremental_return {b['incr_return_5y']:.3f}")
    print("falsifiers v_if_triggered: " + " / ".join(f"F{i + 1} {v:.2f}" for i, v in enumerate(out["f"])))


if __name__ == "__main__":
    summary(main())
