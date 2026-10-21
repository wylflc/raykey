#!/usr/bin/env python3
"""三花智控（002050）独立估值：OI-291 b11，价格日 2026-10-20。

运行：python3 valuation.py
输入全部写在本脚本内（金额单位亿元，每股为元）。出处页码见公司全文「来源」一节：
2026H1 = 2026H1_report，AR25 = 2025_annual_report（页码为 PDF 物理页）。
方法：分部（制冷空调电器零部件／汽车零部件）所有者收益 DCF，归母、无杠杆
（经调整净现金为正），机器人机电执行器按概率计期权价值，另加经调整净现金与非经营资产。
"""

# ---------------------------------------------------------------- 快照
PRICE_A = 33.03                      # A 股 2026-10-20 收盘（腾讯日线）
SHARES = 42.08013935                 # 总股本：A 37.31477535 + H 4.765364（2026H1 第 2 页）
SHARES_A, SHARES_H = 37.31477535, 4.765364
TREASURY = (8_351_021 + 5_813_422) / 1e8  # 回购专户：2025 年末 835.1 万股（AR25 第 2 页）+ 2026-07 方案截至 10-15 的 581.3 万股
PRICE_H_HKD = 22.84                  # H 股 2026-10-20 收盘（腾讯港股行情）
HKD_CNY = 0.12 / 0.13888             # 中期股息 0.12 元＝0.13888 港元的折算率（2026-09 公告口径）
COE = 0.09

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，2026H1 第 52-53、82、90、102-105、115 页）
CASH = 148.155              # 货币资金，含大额存单及定期存款 28.196
RESTRICTED = 0.857          # 保证金 0.220 + 期货保证金 0.637（流动性受限）
TFA_EX_STOCK = 2.508 + 6.291    # 交易性金融资产：结构性存款 + 现金管理理财
OCA_FIN = 4.530 + 4.650         # 其他流动资产：中信证券本金保障型收益凭证 + 国债逆回购
DERIV_NET = 0.321 - 0.163       # 衍生金融资产 − 衍生金融负债
DEBT = 13.702 + 14.476 + 9.049 + (0.771 + 1.536) + (0.433 + 0.049)
#      短期借款 + 一年内到期借款 + 长期借款 + 租赁负债（含一年内）+ 拆借款及应付利息
DIV_PAYABLE = 11.759        # 应付股利：2025 年度末期股息（已宣派，2026-07 支付）
LT_STAFF = 0.310            # 长期应付职工薪酬（类债务）
REV_TTM = 316.49
OP_RESERVE = 0.05 * REV_TTM # 经营备付：TTM 收入 5%
POST_DIST = 0.12 * 41.95537992 + 2.0795   # 06-30 后至价格日：2026 中期股息 + 2026-07 方案回购金额（截至 10-15）
NET_CASH_0630 = (CASH - RESTRICTED + TFA_EX_STOCK + OCA_FIN + DERIV_NET
                 - DEBT - DIV_PAYABLE - LT_STAFF - OP_RESERVE)
NET_CASH = NET_CASH_0630 - POST_DIST          # 价格日口径，计入 V
NON_OP = 1.415 + 0.122 + 0.425 + 0.061        # 赛力斯 H 股 + 峰岹 H 股（06-30 公允价值）+ 长期股权投资 + 投资性房地产

# ---------------------------------------------------------------- 经营假设
TAX = 0.15                  # 2025 年 15.2%，2026H1 14.1%
MINORITY = 0.017            # 少数股东损益占净利润：2025 年 1.1%，2026H1 1.8%
EQ_INCOME = 0.08            # 联营企业投资收益（年）
NET_INT_2026 = 1.30         # 2026 正常化净利息：H1 利息收入 1.33 − 利息费用 0.61，按派息回购后的现金下调
REV_H1_2026 = {"refr": 104.448, "auto": 64.551}     # 2026H1 第 13-14 页
REV_H2_2025 = {"refr": 185.847 - 103.887, "auto": 124.270 - 58.741}
CORE_EBIT_H1_2026 = 27.24   # 毛利 − 税金附加 − 三费 − 研发 + 经常性其他收益 − 减值（剔除汇兑、补助、证券投资）

YEARS = list(range(2027, 2036))   # 显性期 2027-2035；2026 只计 H2

SCEN = {
    "bear": dict(
        p=0.25, g_tv=0.020, ronic=0.13, ronic_tv=0.12,
        h2_2026={"refr": -0.03, "auto": 0.06},
        g={"refr": [0.02, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.025, 0.025],
           "auto": [0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.025, 0.025, 0.02]},
        m_h2_2026={"refr": 0.140, "auto": 0.150},
        m={"refr": [0.135, 0.130] + [0.130] * 7, "auto": [0.145, 0.140] + [0.140] * 7},
        fx_h2_2026=-1.0, fx=[-1.5, -1.0, -0.5] + [0.0] * 6,
        floor_h2_2026=8.0, floor={2027: 13.0, 2028: 12.0},
        robot_p=0.0, robot_scale=1.0,
        norm_m={"refr": 0.130, "auto": 0.140}, norm_fx=-2.0,
        text="制冷 2026 年 −1%，此后 2%～3%；汽零 2026 年 +7.8%，此后 3%～4%；核心营业利润率回落到 13.4%（分部 13%/14%）；汇兑拖累至 2029 年；增量回报 13%，终值增长 2%；机器人不计",
    ),
    "base": dict(
        p=0.50, g_tv=0.025, ronic=0.18, ronic_tv=0.15,
        h2_2026={"refr": 0.01, "auto": 0.09},
        g={"refr": [0.06, 0.07, 0.07, 0.06, 0.055, 0.05, 0.045, 0.04, 0.035],
           "auto": [0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035]},
        m_h2_2026={"refr": 0.148, "auto": 0.160},
        m={"refr": [0.150, 0.149, 0.148] + [0.147] * 6, "auto": [0.160, 0.158, 0.156] + [0.155] * 6},
        fx_h2_2026=-0.5, fx=[-0.5] + [0.0] * 8,
        floor_h2_2026=8.0, floor={2027: 15.0, 2028: 14.0},
        robot_p=0.35, robot_scale=1.0,
        norm_m={"refr": 0.147, "auto": 0.155}, norm_fx=-1.0,
        text="制冷 2026 年 +0.7%，2027-2029 年 6%～7%（液冷、储能、家空修复），2035 年降到 3.5%；汽零 2026 年 +9.4%，2027 年 10% 逐年降到 3.5%；核心营业利润率由 2027 年 15.4% 收敛到 15.0%（分部 14.7%/15.5%）；增量回报 18%，终值 2.5%／15%；机器人按 35% 成功概率计",
    ),
    "bull": dict(
        p=0.25, g_tv=0.025, ronic=0.22, ronic_tv=0.18,
        h2_2026={"refr": 0.04, "auto": 0.11},
        g={"refr": [0.10, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04],
           "auto": [0.13, 0.12, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05, 0.045]},
        m_h2_2026={"refr": 0.153, "auto": 0.165},
        m={"refr": [0.155] * 9, "auto": [0.165] * 9},
        fx_h2_2026=0.0, fx=[0.0] * 9,
        floor_h2_2026=8.0, floor={2027: 15.0, 2028: 14.0},
        robot_p=0.80, robot_scale=1.5,
        norm_m={"refr": 0.155, "auto": 0.165}, norm_fx=0.0,
        text="制冷 2027-2028 年 10%（液冷高增长、家空强修复），2035 年 4%；汽零 2027 年 13% 降到 4.5%；核心营业利润率 16%（分部 15.5%/16.5%）；增量回报 22%，终值 2.5%／18%；机器人成功概率 80%、规模 1.5 倍",
    ),
}

# 机器人机电执行器「成功」情形（未披露收入；2026H1 第 13 页「批量交付与产线爬坡」）
ROBOT_REV = [10, 25, 45, 70, 90, 105, 115, 122, 128]   # 2027-2035，亿元
ROBOT_NM, ROBOT_RR_EARLY, ROBOT_RR_LATE = 0.09, 0.40, 0.20   # 净利率；2031 年前／后再投资率
ROBOT_G_TV, ROBOT_RONIC_TV = 0.025, 0.15


def t_mid(year):
    """价格日 2026-10-20 至该年年中的年数（年中惯例）；2026H2 记 0.1。"""
    return 0.1 if year == 2026 else (year - 2026) - 0.3


def segment_path(s, seg):
    """返回 [(年份, 收入, 核心 EBIT)]，2026 年只含 H2。"""
    rev = REV_H2_2025[seg] * (1 + s["h2_2026"][seg])
    out = [(2026, rev, rev * s["m_h2_2026"][seg])]
    full = REV_H1_2026[seg] + rev
    for i, y in enumerate(YEARS):
        full *= 1 + s["g"][seg][i]
        out.append((y, full, full * s["m"][seg][i]))
    return out


def full_year_rev_2026(s, seg):
    return REV_H1_2026[seg] + REV_H2_2025[seg] * (1 + s["h2_2026"][seg])


def seg_growth(s, seg, i):
    """分部第 i 年（YEARS 下标）收入增速，用于再投资（投资先于增长）；i = len(YEARS) 时取终值增长。"""
    return s["g_tv"] if i >= len(YEARS) else s["g"][seg][i]


def dcf(s, k=COE, detail=False):
    keep = (1 - TAX) * (1 - MINORITY)
    seg_pv, rows = {}, []
    paths = {seg: segment_path(s, seg) for seg in ("refr", "auto")}
    nopat_tot = [paths["refr"][j][2] * keep + paths["auto"][j][2] * keep for j in range(len(YEARS) + 1)]
    for seg in ("refr", "auto"):
        pv = 0.0
        for j, (y, rev, ebit) in enumerate(paths[seg]):
            nopat = ebit * keep
            share = nopat / nopat_tot[j]
            if y == 2026:   # 半年：NOPAT 已是 H2，再投资按 H2 NOPAT × 次年增速 / 增量回报，下限为承诺资本开支
                reinv = max(s["floor_h2_2026"] * share, nopat * seg_growth(s, seg, 0) / s["ronic"])
            else:
                i = YEARS.index(y)
                ronic = s["ronic_tv"] if i + 1 >= len(YEARS) else s["ronic"]
                floor = s["floor"].get(y, 0.0) * share
                reinv = max(floor, nopat * seg_growth(s, seg, i + 1) / ronic)
            oe = nopat - reinv
            pv += oe / (1 + k) ** t_mid(y)
            if detail:
                rows.append((seg, y, rev, ebit, nopat, reinv, oe))
        y_last, rev_last, ebit_last = paths[seg][-1]
        nopat_tv = ebit_last * keep * (1 + s["g_tv"])
        oe_tv = nopat_tv * (1 - s["g_tv"] / s["ronic_tv"])
        tv = oe_tv / (k - s["g_tv"])
        pv_tv = tv / (1 + k) ** t_mid(y_last)
        seg_pv[seg] = (pv, pv_tv)
    # 汇兑拖累（公司项，税后）
    fx_pv = s["fx_h2_2026"] * (1 - TAX) / (1 + k) ** t_mid(2026)
    fx_pv += sum(f * (1 - TAX) / (1 + k) ** t_mid(y) for f, y in zip(s["fx"], YEARS))
    robot = robot_option(s, k)
    eq_pv = EQ_INCOME / k
    total = sum(a + b for a, b in seg_pv.values()) + fx_pv + robot + eq_pv + NET_CASH + NON_OP
    res = dict(seg_pv=seg_pv, fx_pv=fx_pv, robot=robot, eq_pv=eq_pv, total=total,
               v=total / SHARES, v_ex_treasury=total / (SHARES - TREASURY))
    if detail:
        res["rows"] = rows
    return res


def robot_npv_success(k=COE, scale=1.0):
    pv = 0.0
    np_last = 0.0
    for i, (y, r) in enumerate(zip(YEARS, ROBOT_REV)):
        np_ = r * scale * ROBOT_NM
        rr = ROBOT_RR_EARLY if y <= 2031 else ROBOT_RR_LATE
        pv += np_ * (1 - rr) / (1 + k) ** t_mid(y)
        np_last = np_
    oe_tv = np_last * (1 + ROBOT_G_TV) * (1 - ROBOT_G_TV / ROBOT_RONIC_TV)
    pv += oe_tv / (k - ROBOT_G_TV) / (1 + k) ** t_mid(YEARS[-1])
    return pv


def robot_option(s, k=COE):
    return s["robot_p"] * robot_npv_success(k, s["robot_scale"])


def normalized_np_2026(s):
    """2026 年正常化归母净利：分部收入 × 中枢利润率 + 净利息 + 正常化汇兑 + 联营收益，扣税与少数股东。"""
    ebit = sum(full_year_rev_2026(s, seg) * s["norm_m"][seg] for seg in ("refr", "auto"))
    pretax = ebit + NET_INT_2026 + s["norm_fx"] + EQ_INCOME
    return pretax * (1 - TAX) * (1 - MINORITY), ebit


def weighted(k=COE, scen=SCEN):
    return sum(s["p"] * dcf(s, k)["v"] for s in scen.values())


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


def implied_irr(price=PRICE_A):
    base = SCEN["base"]
    return solve(lambda r: dcf(base, r)["v"], 0.03, 0.20, price)


def reverse_dcf_10y(ronic=0.18, ronic_tv=0.15):
    """现价隐含：2027-2036 年 NOPAT 年增速 g（再投资 = g/ronic），此后 2.5%（增量回报 ronic_tv），9% 折现；
    起点为基准 2026 年中枢 NOPAT（不含净利息），不计机器人期权。"""
    base = SCEN["base"]
    keep = (1 - TAX) * (1 - MINORITY)
    nopat0 = normalized_np_2026(base)[1] * keep + base["norm_fx"] * (1 - TAX) * (1 - MINORITY)
    target = PRICE_A * SHARES - NET_CASH - NON_OP - EQ_INCOME / COE

    def value(g):
        pv, n = 0.0, nopat0
        for i in range(10):
            n *= 1 + g
            pv += n * (1 - g / ronic) / (1 + COE) ** (i + 0.7)
        oe_tv = n * 1.025 * (1 - 0.025 / ronic_tv)
        pv += oe_tv / (COE - 0.025) / (1 + COE) ** 9.7
        return pv
    hi = ronic * 0.999
    g10 = solve(value, 0.0, hi, target) if value(hi) >= target else None   # None：任何增速都达不到现价
    if g10 is None:
        g10 = -max(value(x / 1000) for x in range(int(hi * 1000)))          # 负数＝可达到的最大经营价值（亿）

    def gordon(g):
        return nopat0 * (1 + g) * (1 - g / ronic_tv) / (COE - g)
    g_perp = solve(gordon, 0.0, 0.0899, target)
    return g10, g_perp, nopat0, target


def main():
    print("== 三花智控（002050）独立估值，价格日 2026-10-20 ==")
    mcap_a = PRICE_A * SHARES
    price_h_cny = PRICE_H_HKD * HKD_CNY
    mcap_mix = PRICE_A * SHARES_A + price_h_cny * SHARES_H
    print(f"A 股价×总股本 {mcap_a:,.1f} 亿；H 股 {PRICE_H_HKD} 港元≈{price_h_cny:.2f} 元（A 股的 {price_h_cny / PRICE_A:.0%}），"
          f"A+H 分别计价市值 {mcap_mix:,.1f} 亿")
    print(f"经调整净现金：06-30 {NET_CASH_0630:.2f} 亿 − 期后派息回购 {POST_DIST:.2f} = {NET_CASH:.2f} 亿；"
          f"有息负债 {DEBT:.2f}，经营备付 {OP_RESERVE:.2f}；非经营资产 {NON_OP:.2f}")
    print("-- 2026 年正常化归母净利（含净利息，剔除一次性）")
    for name, s in SCEN.items():
        npn, ebit = normalized_np_2026(s)
        rev = sum(full_year_rev_2026(s, g) for g in ("refr", "auto"))
        print(f"  {name}: 收入 {rev:.1f}，核心 EBIT {ebit:.2f}（{ebit / rev:.1%}），归母 {npn:.2f} 亿")
    print("-- 三情景（9%）")
    res = {}
    for name, s in SCEN.items():
        r = dcf(s, COE)
        res[name] = r
        sp = r["seg_pv"]
        print(f"  {name}: V {r['v']:.2f} 元（剔除回购专户 {r['v_ex_treasury']:.2f}）p={s['p']}；"
              f"制冷 {sum(sp['refr']):.1f}（终值 {sp['refr'][1]:.1f}）汽零 {sum(sp['auto']):.1f}（终值 {sp['auto'][1]:.1f}）"
              f" 汇兑 {r['fx_pv']:.1f} 机器人 {r['robot']:.1f} 联营 {r['eq_pv']:.1f} 净现金 {NET_CASH:.1f} 非经营 {NON_OP:.1f}"
              f" 合计 {r['total']:.1f} 亿；终值占比 {(sp['refr'][1] + sp['auto'][1]) / r['total']:.0%}")
    vw = weighted()
    vw_ex = sum(s["p"] * res[n]["v_ex_treasury"] for n, s in SCEN.items())
    print(f"加权 V {vw:.2f} 元，P/V {PRICE_A / vw:.2f}；剔除回购专户 V {vw_ex:.2f}，P/V {PRICE_A / vw_ex:.2f}")
    print(f"H 股对照：{price_h_cny:.2f} 元 / V = {price_h_cny / vw:.2f}")
    print(f"股权成本 8%：加权 V {weighted(0.08):.2f}；10%：加权 V {weighted(0.10):.2f}")
    for name, s in SCEN.items():
        print(f"  {name}: 8% {dcf(s, 0.08)['v']:.2f}  10% {dcf(s, 0.10)['v']:.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准现金流）{irr:.2%}；按 H 股价 {price_h_cny:.2f} 元为 {implied_irr(price_h_cny):.2%}")
    g10, gp, nopat0, target = reverse_dcf_10y()
    g10b, gpb, _, _ = reverse_dcf_10y(0.25, 0.18)
    g10c, _, _, _ = reverse_dcf_10y(0.30, 0.18)
    head = (f"反向 DCF：现价经营价值 {target:.1f} 亿（扣净现金、非经营资产与联营），起点 NOPAT {nopat0:.2f} 亿；")
    part18 = (f"增量回报 18% 时任何 10 年增速都达不到（最高 {-g10:.0f} 亿）" if g10 < 0 else f"增量回报 18% 时 10 年年增 {g10:.1%}")
    print(head + part18 + f"；增量回报 25% 时 2027-2036 年 NOPAT 年增 {g10b:.1%}，30% 时 {g10c:.1%}（终值 2.5%、增量回报 18%）；"
          f"一步永续：增长 {gp:.2%}（增量回报 15%）或 {gpb:.2%}（18%）")
    rs = robot_npv_success()
    print(f"机器人成功情形 NPV {rs:.1f} 亿（{rs / SHARES:.2f} 元/股）；现价与加权 V 之差 {(PRICE_A - vw) * SHARES:.0f} 亿"
          f" ＝ 成功情形 NPV 的 {(PRICE_A - vw) * SHARES / rs:.1f} 倍（须确定实现）")
    exp_robot = sum(sc["p"] * res[n]["robot"] for n, sc in SCEN.items())
    v_norobot = vw - exp_robot / SHARES
    need = PRICE_A / 1.10
    print(f"  不计机器人的加权 V {v_norobot:.2f}；P/V 回到 1.10 需 V ≥ {need:.2f}，即在已计入期望值之外再加 "
          f"{(need - vw) * SHARES / rs:.1f} 个成功情形；现价对应确定实现的 {(PRICE_A - v_norobot) * SHARES / rs:.1f} 个成功情形")
    import copy
    s1, s2 = copy.deepcopy(SCEN["base"]), copy.deepcopy(SCEN["base"])
    for seg in ("refr", "auto"):
        s1["m"][seg] = [x + 0.01 for x in s1["m"][seg]]
        s1["m_h2_2026"][seg] += 0.01
        s2["g"][seg] = [x + 0.01 for x in s2["g"][seg]]
    print(f"  基准敏感性：利润率 +1 个百分点 V {dcf(s1)['v']:.2f}；2027-2035 年增速各 +1 个百分点 V {dcf(s2)['v']:.2f}")
    for name in SCEN:
        r = res[name]
        print(f"  {name} 每股：制冷 {sum(r['seg_pv']['refr']) / SHARES:.2f} 汽零 {sum(r['seg_pv']['auto']) / SHARES:.2f}"
              f" 机器人 {r['robot'] / SHARES:.2f} 净现金 {NET_CASH / SHARES:.2f} 其他 {(r['fx_pv'] + r['eq_pv'] + NON_OP) / SHARES:.2f}")
    print("-- 基准增长路径（全年，归母 NOPAT 与所有者收益）")
    b = dcf(SCEN["base"], COE, detail=True)
    keep = (1 - TAX) * (1 - MINORITY)
    agg = {}
    for seg, y, rev, ebit, nopat, reinv, oe in b["rows"]:
        a = agg.setdefault(y, [0, 0, 0, 0, 0])
        a[0] += rev; a[1] += ebit; a[2] += nopat; a[3] += reinv; a[4] += oe
    h1_nopat = CORE_EBIT_H1_2026 * keep
    rev26 = sum(REV_H1_2026.values()) + agg[2026][0]
    nopat26 = h1_nopat + agg[2026][2]
    oe26 = nopat26 - 2 * agg[2026][3]
    prev_oe, prev_n = oe26, nopat26
    ebit26 = CORE_EBIT_H1_2026 + agg[2026][1]
    print(f"  2026 全年：收入 {rev26:.1f} 核心EBIT {ebit26:.2f}（{ebit26 / rev26:.1%}）NOPAT {nopat26:.2f} 再投资 {2 * agg[2026][3]:.2f}"
          f" 所有者收益 {oe26:.2f}（H1 按实际核心 EBIT，H2 按情景；全年再投资按 H2 的两倍）")
    print(f"  2026 对照：剔除 H1 汇兑与证券浮亏的归母约 {(ebit26 + NET_INT_2026 - 0.5 + EQ_INCOME) * keep:.1f} 亿；"
          f"报告口径约 {20.44 + (agg[2026][1] + NET_INT_2026 / 2 - 0.5 + EQ_INCOME / 2) * keep:.1f} 亿（H1 20.44）")
    for y in YEARS:
        rev, ebit, nopat, reinv, oe = agg[y]
        print(f"  {y}: 收入 {rev:.1f} 核心EBIT {ebit:.2f}（{ebit / rev:.1%}）NOPAT {nopat:.2f}（{nopat / prev_n - 1:+.1%}）"
              f" 再投资 {reinv:.2f}（{reinv / nopat:.0%}）所有者收益 {oe:.2f}（{oe / prev_oe - 1:+.1%}）")
        prev_oe, prev_n = oe, nopat
    print("-- 三情景增长路径（2027-2031 与终值；收入增速／核心 EBIT 率／NOPAT 增速／所有者收益）")
    for name, sc in SCEN.items():
        r = dcf(sc, COE, detail=True)
        ag = {}
        for seg, y, rev, ebit, nopat, reinv, oe in r["rows"]:
            a = ag.setdefault(y, [0, 0, 0, 0, 0])
            a[0] += rev; a[1] += ebit; a[2] += nopat; a[3] += reinv; a[4] += oe
        rev_prev = sum(full_year_rev_2026(sc, g) for g in ("refr", "auto"))
        n_prev = CORE_EBIT_H1_2026 * keep + ag[2026][2]
        cells = []
        for y in YEARS[:5]:
            rev, ebit, nopat, reinv, oe = ag[y]
            cells.append(f"{y} {rev / rev_prev - 1:+.1%}/{ebit / rev:.1%}/{nopat / n_prev - 1:+.1%}/{oe:.1f}")
            rev_prev, n_prev = rev, nopat
        print(f"  {name}: " + "；".join(cells) + f"；终值增长 {sc['g_tv']:.1%}、终值增量回报 {sc['ronic_tv']:.0%}")
    print("-- 交叉验证")
    print(f"  市值/2026 基准正常化归母 {mcap_a / normalized_np_2026(SCEN['base'])[0]:.1f}×；"
          f"EV/2026 基准核心 EBIT {(mcap_a - NET_CASH - NON_OP) / normalized_np_2026(SCEN['base'])[1]:.1f}×")
    print(f"  加权 V 对应 2026 基准正常化 PE {vw * SHARES / normalized_np_2026(SCEN['base'])[0]:.1f}×，PB {vw * SHARES / 325.02:.2f}×")
    print("-- 证伪条件触发后的 V")
    fals = falsifier_values()
    for k_, v_ in fals.items():
        print(f"  {k_}: {v_:.2f}")
    print("-- V 不变时各档价格：≤{:.2f} 明显低估；{:.2f}～{:.2f} 温和低估；{:.2f}～{:.2f} 大致合理；>{:.2f} 偏贵".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


def falsifier_values():
    import copy
    out = {}
    # F1 2026 年报核心营业利润率 < 14%：权重移向熊市 0.5/0.4/0.1
    sc = copy.deepcopy(SCEN)
    sc["bear"]["p"], sc["base"]["p"], sc["bull"]["p"] = 0.5, 0.4, 0.1
    out["F1 利润率跌破 14%（权重 0.5/0.4/0.1）"] = weighted(COE, sc)
    # F2 汽零 2027H1 增速 < 3%：基准的汽零路径换成熊市路径
    sc = copy.deepcopy(SCEN)
    for n in sc:
        if n != "bear":
            sc[n]["g"]["auto"] = SCEN["bear"]["g"]["auto"]
            sc[n]["m"]["auto"] = [x - 0.005 for x in sc[n]["m"]["auto"]]
    out["F2 汽零增速 < 3%（基准与牛市换熊市汽零路径）"] = weighted(COE, sc)
    # F3 制冷 2027 年增速 < 2%（液冷储能不足以抵消家空）：基准与牛市换熊市制冷路径
    sc = copy.deepcopy(SCEN)
    for n in sc:
        if n != "bear":
            sc[n]["g"]["refr"] = SCEN["bear"]["g"]["refr"]
    out["F3 制冷增速 < 2%（换熊市制冷路径）"] = weighted(COE, sc)
    # F4 机器人执行器 2027 年披露收入 ≥ 20 亿：三情景机器人成功概率取 0.9、基准规模 1.2
    sc = copy.deepcopy(SCEN)
    for n in sc:
        sc[n]["robot_p"] = 0.9
        sc[n]["robot_scale"] = max(sc[n]["robot_scale"], 1.2)
    out["F4 机器人收入 ≥ 20 亿（成功概率 0.9）"] = weighted(COE, sc)
    # F5 2027 年收入增速 ≥ 12% 且核心利润率 ≥ 16%：权重 0.1/0.4/0.5
    sc = copy.deepcopy(SCEN)
    sc["bear"]["p"], sc["base"]["p"], sc["bull"]["p"] = 0.1, 0.4, 0.5
    out["F5 收入 ≥ +12% 且利润率 ≥ 16%（权重 0.1/0.4/0.5）"] = weighted(COE, sc)
    return out


if __name__ == "__main__":
    main()
