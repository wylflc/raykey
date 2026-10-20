# -*- coding: utf-8 -*-
"""恒生电子（600570）独立估值（OI-291 b05，价格日 2026-10-19）。

金额单位亿元，每股价值元/股。运行：python3 valuation.py
方法：核心软件业务所有者收益 DCF（剔除投资收益、公允价值变动与现金收益）
      + 蚂蚁基金 24.10% 股权（正常化利润 × 市盈率 × 折价）
      + 赢时胜持股（2026-10-19 收盘市值 × 折价）+ 其他长期股权投资与其他非流动金融资产（账面 × 系数）
      + 2026-06-30 经调整净现金 + 2026 年下半年自由现金流 + 在建不动产项目净值 − 少数股东对非经营净资产的份额。
经调整净现金为正，按全额扣除有息负债的口径；公司无可转债。
"""

PRICE = 20.19
SHARES = 18.96636406   # 1,896,636,406 股（dividend_20261010 第 2 页），回购专户 0 股（2026-08-25 过户至员工持股计划）
MKT_CAP = PRICE * SHARES
COE = 0.09
YEARS = [2027, 2028, 2029, 2030, 2031]
T0 = 1.2               # 2026-10-19 至 2027-12-31，年末折现（四季度集中回款）

# ---------- 2026-06-30 资产负债表（2026H1_report 第 37-39、76、100、111-112、116 页） ----------
CASH_LIKE = {
    "货币资金": 13.1990,
    "交易性金融资产（理财、货基与结构性存款为主）": 14.8765,
    "一年内到期的非流动资产（定期存单）": 2.0788,
    "其他非流动资产（定期存单）": 9.7910,
    "其他债权投资（债券）": 0.4407,
}
RESTRICTED = 0.0274            # 保函保证金
DEBT = {"短期借款": 1.7624, "一年内到期的非流动负债": 0.1487, "长期借款": 2.5986, "租赁负债": 0.1610}
DEBT_LIKE = {"长期应付款（员工持股回购义务 0.7651 + 长期资产购置款 0.0580）": 0.8231}
OP_RESERVE = 5.0               # 约一个月现金经营支出；6 月末为季节性低点
NET_CASH_ADJ = (sum(CASH_LIKE.values()) - RESTRICTED - sum(DEBT.values())
                - sum(DEBT_LIKE.values()) - OP_RESERVE)

AF_STAKE = 0.2410              # 蚂蚁（杭州）基金销售，权益法（2026H1_report 第 140 页）
AF_BOOK = 11.3643
YSS_SHARES = 7.51003080 * (0.0973 + 0.0125)   # 赢时胜总股本 7.51 亿股 × 直接 9.73% + 间接 1.25%（亿股）
YSS_PRICE = 13.44              # 赢时胜 2026-10-19 收盘（腾讯行情，2026-10-20 查）
YSS_BOOK = 5.6302
LTEI_TOTAL = 28.6425
OTHER_LTEI = LTEI_TOTAL - AF_BOOK - YSS_BOOK  # 其余 30 余家联营企业与基金
FIN_ASSETS = 2.7388 + 4.9162 + 2.8451 + 0.4510  # 其他非流动金融资产中股票、基金、信托、资管计划
UNLISTED_EQ = 10.9385                            # 其他非流动金融资产中未上市股权
DEV_PRODUCTS = 1.3966          # 存货中的开发产品（钱塘科技园拟售部分）
RE_BUDGET = 8.0 + 9.9          # 金融云产品生产基地（二期）与江苏总部预算（2026H1_report 第 104 页）
RE_REMAIN = 8.0 * (1 - 0.5966) + 9.9 * (1 - 0.2422)
MINO_EQ = 9.1374               # 少数股东权益
POST_H1_EQUITY_CASH = 2988464 * 16.74 / 1e8 + 1546527 * 11.41 / 1e8  # 7-10 月期权行权（2024 年计划，行权价 16.74）与员工持股计划认购款

# ---------- 核心软件业务成本结构参数（2025_annual_report 第 91-92、176-180 页） ----------
OTHER_INC = 0.031              # 经常性其他收益（软件增值税即征即退 1.68 亿等）占收入
SURTAX = 0.0065                # 税金及附加（不含土地增值税）占收入
CAP_INT = 0.15                 # 增量收入所需增量投入资本（应收、合同履约成本、设备，扣合同负债）

SCEN = {
    "bear": dict(p=0.25, rev26=52.0, norm_rev26=53.0, growth=[0.02, 0.01, 0.02, 0.02, 0.02],
                 gm26=0.695, gm=0.700, opex26=32.3, opex_g=0.01, imp=0.025, tax=0.10, mino=0.08,
                 g=0.020, ronic=0.20, h2fcf=12.5,
                 af_np=9.0, af_pe=11.0, af_disc=0.35, yss_hc=0.25, oltei=0.50, fin=0.90, uneq=0.50,
                 devp=0.60, re_frac=0.40, mino_bs=0.70, assoc_other=-0.15, net_int=0.50),
    "base": dict(p=0.50, rev26=54.5, norm_rev26=57.0, growth=[0.09, 0.06, 0.05, 0.04, 0.04],
                 gm26=0.705, gm=0.710, opex26=32.7, opex_g=0.043, imp=0.018, tax=0.06, mino=0.065,
                 g=0.025, ronic=0.25, h2fcf=15.0,
                 af_np=14.5, af_pe=14.0, af_disc=0.25, yss_hc=0.15, oltei=0.60, fin=0.95, uneq=0.65,
                 devp=0.70, re_frac=0.55, mino_bs=0.50, assoc_other=-0.05, net_int=0.63),
    "bull": dict(p=0.25, rev26=56.5, norm_rev26=59.0, growth=[0.11, 0.09, 0.07, 0.06, 0.05],
                 gm26=0.710, gm=0.720, opex26=32.9, opex_g=0.060, imp=0.013, tax=0.05, mino=0.055,
                 g=0.025, ronic=0.30, h2fcf=17.0,
                 af_np=20.0, af_pe=16.0, af_disc=0.20, yss_hc=0.10, oltei=0.75, fin=1.00, uneq=0.80,
                 devp=0.85, re_frac=0.70, mino_bs=0.40, assoc_other=0.05, net_int=0.70),
}


def margin_factor(gm, imp):
    return gm - SURTAX + OTHER_INC - imp


def core_path(s):
    """返回 2026-2031 收入、核心 EBIT、核心归母净利与 2027-2031 所有者收益。"""
    rev = [s["rev26"]]
    for gr in s["growth"]:
        rev.append(rev[-1] * (1 + gr))
    opex = [s["opex26"] * (1 + s["opex_g"]) ** i for i in range(6)]
    gm = [s["gm26"]] + [s["gm"]] * 5
    ebit = [rev[i] * margin_factor(gm[i], s["imp"]) - opex[i] for i in range(6)]
    np_ = [e * (1 - s["tax"]) * (1 - s["mino"]) for e in ebit]
    oe = [np_[i] - CAP_INT * (rev[i] - rev[i - 1]) for i in range(1, 6)]
    return rev, opex, ebit, np_, oe


def non_core(s):
    return {
        "蚂蚁基金 24.10%": s["af_np"] * s["af_pe"] * AF_STAKE * (1 - s["af_disc"]),
        "赢时胜 10.98%": YSS_SHARES * YSS_PRICE * (1 - s["yss_hc"]),
        "其他联营企业": OTHER_LTEI * s["oltei"],
        "其他非流动金融资产": FIN_ASSETS * s["fin"] + UNLISTED_EQ * s["uneq"],
        "开发产品": DEV_PRODUCTS * s["devp"],
        "在建不动产项目净值": s["re_frac"] * RE_BUDGET * 0.85 - RE_REMAIN * 0.90,
        "少数股东对非经营净资产份额": -MINO_EQ * s["mino_bs"],
        "经调整净现金（6月末）": NET_CASH_ADJ,
        "7-10 月期权行权与员工持股认购款": POST_H1_EQUITY_CASH,
    }


def value(s, r, af_override=None):
    rev, opex, ebit, np_, oe = core_path(s)
    pv_oe = sum(oe[i] / (1 + r) ** (T0 + i) for i in range(5))
    g = s["g"]
    oe_term = np_[-1] * (1 + g) * (1 - g / s["ronic"])
    tv = oe_term / (r - g)
    pv_tv = tv / (1 + r) ** (T0 + 4)
    pv_h2 = s["h2fcf"] / (1 + r) ** 0.1
    nc = non_core(s)
    if af_override is not None:
        nc["蚂蚁基金 24.10%"] = af_override
    eq = pv_oe + pv_tv + pv_h2 + sum(nc.values())
    return dict(eq=eq, ps=eq / SHARES, pv_oe=pv_oe, pv_tv=pv_tv, pv_h2=pv_h2, nc=nc,
                rev=rev, opex=opex, ebit=ebit, np=np_, oe=oe, tv=tv)


def weighted(r, probs=None, mods=None):
    tot = 0.0
    for k, s in SCEN.items():
        ss = dict(s)
        if mods and k in mods:
            ss.update(mods[k])
        p = probs[k] if probs else s["p"]
        tot += p * value(ss, r)["ps"]
    return tot


def solve(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def normalized_np_2026(s):
    """2026 年正常化归母净利：正常验收节奏下的核心软件 + 蚂蚁基金正常化份额 + 其他联营 + 税后净利息。"""
    core_ebit = s["norm_rev26"] * margin_factor(s["gm"], s["imp"]) - s["opex26"]
    core = core_ebit * (1 - s["tax"]) * (1 - s["mino"])
    af = s["af_np"] * AF_STAKE
    return core + af + s["assoc_other"] + s["net_int"], core, core_ebit, af


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print(f"市值 {MKT_CAP:.2f} 亿；现金类合计 {sum(CASH_LIKE.values()):.2f}；有息负债 {sum(DEBT.values()):.2f}；"
          f"经调整净现金 {NET_CASH_ADJ:.2f}")
    print(f"赢时胜持股 {YSS_SHARES:.4f} 亿股，市值 {YSS_SHARES * YSS_PRICE:.2f} 亿；其他联营账面 {OTHER_LTEI:.2f}；"
          f"在建项目剩余投入 {RE_REMAIN:.2f}")
    res = {}
    for k, s in SCEN.items():
        v = value(s, COE)
        res[k] = v
        core = v["pv_oe"] + v["pv_tv"]
        print(f"\n[{k}] p={s['p']:.2f}  V={v['ps']:.2f} 元/股  股权价值 {v['eq']:.1f} 亿")
        print(f"  核心 DCF {core:.1f}（显性期 {v['pv_oe']:.1f} + 终值现值 {v['pv_tv']:.1f}；终值占核心 {v['pv_tv'] / core:.0%}，"
              f"占全部 {v['pv_tv'] / v['eq']:.0%}）；下半年 FCF 现值 {v['pv_h2']:.1f}")
        for kk, vv in v["nc"].items():
            print(f"  {kk}: {vv:.2f}")
        print("  收入 2026-2031:", [round(x, 1) for x in v["rev"]])
        print("  期间费用:", [round(x, 1) for x in v["opex"]])
        print("  核心 EBIT:", [round(x, 2) for x in v["ebit"]],
              "利润率:", [f"{v['ebit'][i] / v['rev'][i]:.1%}" for i in range(6)])
        print("  核心归母净利:", [round(x, 2) for x in v["np"]])
        print("  所有者收益 2027-2031:", [round(x, 2) for x in v["oe"]],
              "增速:", [f"{v['oe'][i] / v['oe'][i - 1] - 1:.1%}" for i in range(1, 5)])
        g = s["g"]
        print(f"  终值：2032 所有者收益 {v['np'][-1] * (1 + g) * (1 - g / s['ronic']):.2f}，永续增长 {g:.1%}，"
              f"再投资率 {g / s['ronic']:.0%}（RONIC {s['ronic']:.0%}）")
        n, core_n, ebit_n, af_n = normalized_np_2026(s)
        print(f"  2026 正常化归母净利 {n:.2f}（核心 {core_n:.2f}，EBIT {ebit_n:.2f}，蚂蚁基金 {af_n:.2f}，"
              f"其他联营 {s['assoc_other']:.2f}，净利息 {s['net_int']:.2f}）")

    vw = sum(SCEN[k]["p"] * res[k]["ps"] for k in SCEN)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv:.2f}（{band(pv)}）")
    print(f"V 不变时各档价格：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}：加权 V = {weighted(r):.2f}；基准 V = {value(SCEN['base'], r)['ps']:.2f}")
    print(f"参考：股权成本 7% 加权 V = {weighted(0.07):.2f}；牛市情景 7% V = {value(SCEN['bull'], 0.07)['ps']:.2f}")

    # 现价隐含回报：基准情景现金流（非经营项目按本文估值固定）
    base = SCEN["base"]
    irr = solve(lambda r: value(base, r)["eq"] - MKT_CAP, 0.03, 0.12)
    print(f"现价隐含回报（基准现金流）= {irr:.2%}")

    # 反向 DCF：扣除基准非经营项目后，现价隐含的核心所有者收益
    vb = res["base"]
    noncore_b = sum(vb["nc"].values()) + vb["pv_h2"]
    core_implied = MKT_CAP - noncore_b
    oe27 = vb["oe"][0]

    def core_pv(g10, r=COE, gt=0.025):
        tot, oe = 0.0, oe27
        for i in range(10):
            if i > 0:
                oe *= (1 + g10)
            tot += oe / (1 + r) ** (T0 + i)
        tv = oe * (1 + gt) / (r - gt)
        return tot + tv / (1 + r) ** (T0 + 9)

    g10 = solve(lambda x: core_pv(x) - core_implied, -0.05, 0.40)
    g_perp = COE - oe27 / core_implied
    print(f"反向 DCF：现价隐含核心价值 {core_implied:.1f} 亿（基准核心 DCF {vb['pv_oe'] + vb['pv_tv']:.1f}）；"
          f"自 2027 所有者收益 {oe27:.2f} 起，隐含 2028-2036 年增速 {g10:.1%}（其后 2.5%）；"
          f"或隐含永续增速 {g_perp:.1%}")
    print(f"  2036 年隐含所有者收益 {oe27 * (1 + g10) ** 9:.1f} 亿")

    # 交叉验证
    ebit25 = 8.18
    ev_core = MKT_CAP - noncore_b
    print(f"交叉：现价对应核心 EV/2025 核心 EBIT {ev_core / ebit25:.1f}×，对 2027 基准核心 EBIT "
          f"{ev_core / vb['ebit'][1]:.1f}×；基准核心 DCF/2027 核心净利 "
          f"{(vb['pv_oe'] + vb['pv_tv']) / vb['np'][1]:.1f}×")
    print(f"  蚂蚁基金账面 {AF_BOOK:.2f} 亿 vs 三情景估值 "
          + "/".join(f"{res[k]['nc']['蚂蚁基金 24.10%']:.1f}" for k in SCEN))
    print(f"  股息：近 12 个月每股 0.20 元 + 10-22 派 0.05 元，合 {0.25 / PRICE:.2%}")

    # 证伪条件触发后的 V
    f1 = res["bull"]["ps"]
    f2 = res["bear"]["ps"]
    f3 = weighted(COE, mods={"base": dict(af_np=20.0, af_disc=0.20), "bear": dict(af_np=14.5, af_disc=0.25),
                              "bull": dict(af_np=24.0)})
    f4 = weighted(COE, probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f5 = weighted(COE, probs={"bear": 0.10, "base": 0.50, "bull": 0.40})
    print(f"证伪 V：F1 牛市路径 {f1:.2f}；F2 熊市路径 {f2:.2f}；F3 蚂蚁基金上调 {f3:.2f}；"
          f"F4 概率转向熊 {f4:.2f}；F5 概率转向牛 {f5:.2f}")
