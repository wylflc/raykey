#!/usr/bin/env python3
"""华润三九（000999）独立估值：归母穿透口径的分部所有者收益 DCF。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。全部输入写在本脚本内，来源见各常量注释
（公告文件名 + PDF 物理页；网络来源见正文与 json 的 web_facts）。

结构：归母价值 = 三九本部（不含天士力、昆药）100%
               + 天士力 28.00% + 昆药集团 29.08% + 华润圣火 49%（三九直接持有）
               + 各部分归母应占的经调整净现金与非经营资产。
"""

# ---------------------------------------------------------------- 统一快照
PRICE = 25.54            # 2026-10-21 收盘，已于 10-16 除息（每股 0.415）
SHARES = 16.6422         # 亿股，总股本；无回购专户、无库存股（2026H1_report 第 41、50 页）
COE = 0.09
VAL_T = 2026 + 294 / 365  # 价格日 2026-10-21 的年份小数
PROBS = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# 持股比例（2026H1_report 第 126 页；圣火 49% 见 2025_annual_report 第 47 页承诺表与第 267 页联营投资）
STAKE_TSL = 0.2800
STAKE_KPC = 0.2908
STAKE_SH = 0.49

# ---------------------------------------------------------------- 资产负债（2026-06-30）
# 合并口径（2026H1_report 第 48-50、89、96、109-114 页）
CONS_CASH = 32.03          # 货币资金
CONS_TRADING = 40.33       # 交易性金融资产（理财 39.99 + 股票 0.34）
CONS_CD_1Y = 7.18          # 一年内到期的大额存单（第 96 页附注 10）
CONS_CD_LT = 12.86         # 其他非流动资产中的长期银行存单（第 109-110 页）
CONS_DEBT_EX_LEASE = 12.33 + 28.48 + 2.08   # 短期借款（含票据贴现 2.18）+ 长期借款 + 一年内到期长期借款
CONS_LEASE = 2.15          # 租赁负债（含一年内到期），只列示不扣
CONS_RESTRICTED = 2.62     # 受限货币资金（第 19、122 页）
CONS_QUASI_DEBT = 0.92 + 0.19 + 0.85   # 设定受益计划、辞退福利、筹资性质其他应付款（第 113-114、121 页）
INTERIM_DIV_PAID = 6.91    # 2026 中期 10 派 4.15，10-16 除息已付（dividend_20261009_217174）

# 天士力、昆药 6-30 资产负债（东财 F10 数据中心，600535.SH / 600422.SH，2026-10-21 查询）
TSL = dict(cash=10.71, trading=22.92, cd_1y=6.53, cd_lt=2.00,   # 其他非流动资产 2.22 中约 2.0 按存单计
           debt_ex_lease=3.02 + 1.53 + 0.58, lease=0.33,
           lte=9.78, nc_fin=3.08, revenue=84.0)
KPC = dict(cash=8.72, trading=8.40, cd_1y=0.0, cd_lt=0.0,
           debt_ex_lease=8.07 + 6.90 + 1.02, lease=0.37,
           lte=0.71, nc_fin=2.76, revenue=33.0,
           div_payable_total=1.36)   # 2025 年度分红 7 月支付：应付少数股东 0.97 / 70.92%
BUFFER_RATE = 0.02         # 经营备付：营业收入的 2%
SJ_REVENUE = 185.0         # 三九本部年化营收（2026H1 合并 150.14 − 天士力 42.01 − 昆药 16.43 = 91.70，×2）


def net_cash_parts():
    """返回各部分（100% 口径）经调整净现金与归母应占合计。"""
    cons_gross = CONS_CASH + CONS_TRADING + CONS_CD_1Y + CONS_CD_LT
    tsl_gross = TSL["cash"] + TSL["trading"] + TSL["cd_1y"] + TSL["cd_lt"]
    kpc_gross = KPC["cash"] + KPC["trading"] + KPC["cd_1y"] + KPC["cd_lt"]
    sj_gross = cons_gross - tsl_gross - kpc_gross
    sj_debt = CONS_DEBT_EX_LEASE - TSL["debt_ex_lease"] - KPC["debt_ex_lease"]
    # 受限资金按货币资金比例分摊
    sj_cash = CONS_CASH - TSL["cash"] - KPC["cash"]
    r_tsl = CONS_RESTRICTED * TSL["cash"] / CONS_CASH
    r_kpc = CONS_RESTRICTED * KPC["cash"] / CONS_CASH
    r_sj = CONS_RESTRICTED - r_tsl - r_kpc
    div_to_sj = KPC["div_payable_total"] * STAKE_KPC
    sj = (sj_gross - sj_debt - r_sj - INTERIM_DIV_PAID + div_to_sj
          - BUFFER_RATE * SJ_REVENUE - CONS_QUASI_DEBT)
    tsl = tsl_gross - TSL["debt_ex_lease"] - r_tsl - BUFFER_RATE * TSL["revenue"]
    kpc = (kpc_gross - KPC["debt_ex_lease"] - r_kpc - KPC["div_payable_total"]
           - BUFFER_RATE * KPC["revenue"])
    parent = sj + STAKE_TSL * tsl + STAKE_KPC * kpc
    cons_adj = (cons_gross - CONS_DEBT_EX_LEASE - CONS_RESTRICTED - INTERIM_DIV_PAID
                - KPC["div_payable_total"] * (1 - STAKE_KPC)
                - BUFFER_RATE * (SJ_REVENUE + TSL["revenue"] + KPC["revenue"]) - CONS_QUASI_DEBT)
    return dict(cons_gross=cons_gross, sj_gross=sj_gross, sj_debt=sj_debt, sj_cash_mon=sj_cash,
                sj=sj, tsl=tsl, kpc=kpc, parent=parent, cons_adj=cons_adj,
                # 数据包口径：有息负债 45.09 = 短期借款 12.33 + 长期借款 28.48 + 一年内到期非流动负债 3.20 + 租赁负债 1.07
                naive=CONS_CASH + CONS_TRADING - 45.09)


def lookthrough():
    """穿透拆分：归母净利 = 本部 + 28%×天士力归母 + 29.08%×昆药归母 + 49%×圣火 − 购买价分摊摊销。
    合并数：2025_annual_report 第 10-11 页；2026H1_report 第 7 页；单季见数据包第五节。
    天士力、昆药自身数：东财 F10（2026-10-21 查询）；天士力 2026H1 另见 IR_20260904_027049 第 4 页。
    圣火 49% 权益法收益：2025 0.755（2025_annual_report 第 267 页），2026H1 −0.066（2026H1_report 第 160 页），
    2025H1 未披露，按全年一半左右取 0.37。购买价分摊归母影响：2026H1 0.25（第 126-127 页合并层面净利与
    子公司自身净利之差 × 持股），2025 全年取 0.4、2025H1 取 0.1（估计）。"""
    rows = {
        # 期间: (归母, 扣非, 天士力归母, 天士力扣非, 昆药归母, 昆药扣非, 昆药持股, 圣火49%, PPA, 合并营收, 天士力营收, 昆药营收)
        "2025": (34.21, 31.34, 11.05 - 3.14, 7.91 - 2.36, 3.50, 1.07, 0.2805, 0.755, 0.40,
                 316.03, 82.36 - 20.55, 65.75),
        "2025H1": (18.15, 16.98, 7.75 - 3.14, 6.40 - 2.36, 1.98, 1.51, 0.2805, 0.37, 0.10,
                   148.10, 42.88 - 20.55, 33.51),
        "2026H1": (16.71, 15.97, 8.93, 8.70, -3.64, -3.90, 0.2908, -0.066, 0.25,
                   150.14, 42.01, 16.43),
        "2025Q3": (5.38, 4.89, 9.84 - 7.75, 8.29 - 6.40, 2.69 - 1.98, 1.17 - 1.51, 0.2805, 0.19, 0.10,
                   71.76, 63.11 - 42.88, 47.51 - 33.51),
    }
    out = {}
    for k, (np_, kf, tnp, tkf, knp, kkf, ks, sh, ppa, rev, trev, krev) in rows.items():
        sj_np = np_ - STAKE_TSL * tnp - ks * knp - sh + ppa
        sj_kf = kf - STAKE_TSL * tkf - ks * kkf - sh + ppa
        out[k] = dict(sj_np=sj_np, sj_kf=sj_kf, sj_rev=rev - trev - krev,
                      tsl=STAKE_TSL * tnp, kpc=ks * knp, sh=sh, ppa=ppa)
    return out


def non_operating_parent():
    """非经营资产（归母应占）：长期股权投资与其他非流动金融资产按账面折价。"""
    sj_lte = 14.70 - TSL["lte"] - KPC["lte"]          # 合并长期股权投资 14.70
    sj_fin = 6.24 - TSL["nc_fin"] - KPC["nc_fin"]     # 合并其他非流动金融资产 6.24
    sj = 0.6 * sj_lte + 0.8 * sj_fin
    tsl = 0.5 * (TSL["lte"] + TSL["nc_fin"])
    kpc = 0.6 * (KPC["lte"] + KPC["nc_fin"])
    return dict(sj=sj, tsl=tsl, kpc=kpc, parent=sj + STAKE_TSL * tsl + STAKE_KPC * kpc)


# ---------------------------------------------------------------- 情景
# 各部分 2026 正常化归母净利、2026 下半年预计净利、2027-2031 逐年增速（或逐年净利）、终值增速。
# 三九本部：2025 本部扣非约 29.1、2026H1 本部扣非约 14.98（同比 −1.1%），见 lookthrough() 输出。
# 天士力：2026H1 归母 8.93、扣非 8.70（IR_20260904_027049 第 4 页；东财 F10）。
# 昆药：2026H1 归母 −3.64、扣非 −3.90；2025 归母 3.50、扣非 1.07（东财 F10）。
RONIC = 0.20
SCEN = {
    "bear": dict(
        sj_norm=28.0, sj_h2=13.6, sj_g=[-0.03, -0.02, -0.01, 0.0, 0.0], sj_gt=0.005, sj_reinv=0.05,
        tsl_norm=9.5, tsl_h2=2.8, tsl_g=[0.0, 0.0, 0.0, 0.0, 0.0], tsl_gt=0.005,
        kpc_norm=-4.0, kpc_h2=-2.4, kpc_np=[-3.0, -1.5, -0.5, 0.0, 0.5], kpc_gt=0.0,
        sh_norm=0.0, sh_h2=0.1, sh_np=[0.3, 0.3, 0.3, 0.3, 0.3], sh_gt=0.0,
        floor_kpc=0.0),
    "base": dict(
        sj_norm=29.4, sj_h2=14.4, sj_g=[0.01, 0.02, 0.02, 0.02, 0.02], sj_gt=0.02, sj_reinv=0.10,
        tsl_norm=11.3, tsl_h2=3.6, tsl_g=[0.04, 0.04, 0.04, 0.04, 0.04], tsl_gt=0.02,
        kpc_norm=-2.0, kpc_h2=-1.4, kpc_np=[-1.0, 0.8, 1.5, 2.0, 2.3], kpc_gt=0.015,
        sh_norm=0.3, sh_h2=0.4, sh_np=[0.6, 0.9, 1.0, 1.05, 1.1], sh_gt=0.01,
        floor_kpc=None),
    "bull": dict(
        sj_norm=30.5, sj_h2=15.0, sj_g=[0.04, 0.04, 0.035, 0.03, 0.03], sj_gt=0.025, sj_reinv=0.15,
        tsl_norm=12.8, tsl_h2=4.2, tsl_g=[0.07, 0.07, 0.07, 0.07, 0.07], tsl_gt=0.025,
        kpc_norm=-1.0, kpc_h2=-0.9, kpc_np=[0.5, 2.5, 3.2, 3.6, 3.9], kpc_gt=0.02,
        sh_norm=0.5, sh_h2=0.6, sh_np=[1.0, 1.4, 1.5, 1.6, 1.65], sh_gt=0.02,
        floor_kpc=None),
}
PPA_AFTER_TAX_PARENT = 0.4   # 天士力、昆药购买价分摊摊销的归母税后影响（非现金，只进报表口径净利）
YEARS = [2027, 2028, 2029, 2030, 2031]


def reinv(g, ronic=RONIC, floor=0.05):
    return max(floor, g / ronic) if g > 0 else floor


def disc(t, r):
    """把发生在年份小数 t 的现金流折到价格日。"""
    return 1.0 / (1 + r) ** max(0.0, t - VAL_T)


def pv_growth_stream(base_np, h2_np, gs, gt, r, reinv_floor=0.05, ronic=RONIC, fixed_reinv=None):
    """按增速路径：2026 下半年 + 2027-2031 + 终值。所有者收益 = 净利 × (1 − 再投资率)。
    fixed_reinv 给定时各年与终值统一用该再投资率（本部按情景长期增速 ÷ 增量回报设定）。"""
    rv = (lambda g: fixed_reinv) if fixed_reinv is not None else (lambda g: reinv(g, ronic, reinv_floor))
    pv = h2_np * (1 - rv(max(gs[0], 0))) * disc(2026.9, r)
    np_t = base_np
    oe_list = []
    for y, g in zip(YEARS, gs):
        np_t *= (1 + g)
        oe = np_t * (1 - rv(g))
        oe_list.append(oe)
        pv += oe * disc(y + 0.5, r)
    oe_t1 = np_t * (1 + gt) * (1 - rv(gt))
    tv = oe_t1 / (r - gt)
    pv_tv = tv * disc(2032.0, r)
    return pv + pv_tv, pv_tv, oe_list


def pv_np_path(h2_np, nps, gt, r, ronic=0.15):
    """按逐年净利路径（亏损期所有者收益 = 净利；终值扣再投资）。"""
    pv = h2_np * disc(2026.9, r)
    for y, n in zip(YEARS, nps):
        pv += n * disc(y + 0.5, r)
    n_t1 = nps[-1] * (1 + gt)
    rr = gt / ronic if gt > 0 else 0.0
    tv = n_t1 * (1 - rr) / (r - gt) if n_t1 > 0 else 0.0
    return pv + tv * disc(2032.0, r)


def scenario_value(name, r=COE):
    s = SCEN[name]
    nc = net_cash_parts()
    no = non_operating_parent()
    sj_op, sj_tv, sj_oe = pv_growth_stream(s["sj_norm"], s["sj_h2"], s["sj_g"], s["sj_gt"], r,
                                           fixed_reinv=s["sj_reinv"])
    tsl_op, _, tsl_oe = pv_growth_stream(s["tsl_norm"], s["tsl_h2"], s["tsl_g"], s["tsl_gt"], r)
    kpc_op = pv_np_path(s["kpc_h2"], s["kpc_np"], s["kpc_gt"], r)
    sh_op = pv_np_path(s["sh_h2"], s["sh_np"], s["sh_gt"], r)
    sj_total = sj_op + nc["sj"] + no["sj"]
    tsl_eq = tsl_op + nc["tsl"] + no["tsl"]
    kpc_eq = kpc_op + nc["kpc"] + no["kpc"]
    if s["floor_kpc"] is not None:
        kpc_eq = max(kpc_eq, s["floor_kpc"])
    parent = sj_total + STAKE_TSL * tsl_eq + STAKE_KPC * kpc_eq + STAKE_SH * sh_op
    norm_np = (s["sj_norm"] + STAKE_TSL * s["tsl_norm"] + STAKE_KPC * s["kpc_norm"]
               + STAKE_SH * s["sh_norm"] - PPA_AFTER_TAX_PARENT)
    # 归母所有者收益路径（2027-2031）
    kpc_np = s["kpc_np"]
    oe_parent = [sj_oe[i] + STAKE_TSL * tsl_oe[i] + STAKE_KPC * kpc_np[i] + STAKE_SH * s["sh_np"][i]
                 for i in range(5)]
    return dict(v=parent / SHARES, equity=parent, sj_op=sj_op, sj_tv=sj_tv, sj_total=sj_total,
                tsl_eq=tsl_eq, kpc_eq=kpc_eq, sh_op=sh_op, norm_np=norm_np, oe_parent=oe_parent,
                tv_share=(sj_tv) / parent)


def weighted(r=COE):
    return sum(PROBS[k] * scenario_value(k, r)["v"] for k in PROBS)


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def implied_irr():
    """基准情景所有者收益流（含终值、净现金与非经营资产）使现值等于现价的折现率。"""
    return bisect(lambda r: scenario_value("base", r)["v"] - PRICE, 0.05, 0.20)


def reverse_dcf():
    """现价隐含：(a) 三九本部永续增速（天士力、昆药、圣火按基准）；
    (b) 归母所有者收益 10 年增速（2027-2036，之后 2% 永续，9% 折现）。"""
    base = scenario_value("base")
    others = base["equity"] - base["sj_total"]
    nc = net_cash_parts()
    no = non_operating_parent()
    target_sj = PRICE * SHARES - others - nc["sj"] - no["sj"]
    s = SCEN["base"]

    def f_perp(g):
        val, _, _ = pv_growth_stream(s["sj_norm"], s["sj_h2"], [g] * 5, g, COE,
                                     fixed_reinv=max(0.05, g / RONIC))
        return val - target_sj
    g_perp = bisect(f_perp, -0.05, 0.06)

    oe0 = base["oe_parent"][0] / (1 + 0.01)   # 2026 年化归母所有者收益近似
    ncp = nc["parent"] + no["parent"]

    def f10(g):
        pv, oe = 0.0, oe0
        for i in range(10):
            oe *= (1 + g)
            pv += oe * disc(2027 + i + 0.5, COE)
        tv = oe * 1.02 / (COE - 0.02)
        pv += tv * disc(2037.0, COE)
        return (pv + ncp) / SHARES - PRICE
    g10 = bisect(f10, -0.10, 0.10)
    return g_perp, g10, oe0


def main():
    nc = net_cash_parts()
    no = non_operating_parent()
    lt = lookthrough()
    print("== 穿透拆分（亿元）：本部 = 归母 − 天士力/昆药/圣火归母应占 + 购买价分摊")
    for k, d in lt.items():
        print(f"  {k}: 本部归母 {d['sj_np']:.2f}，本部扣非 {d['sj_kf']:.2f}，本部营收 {d['sj_rev']:.2f}"
              f" | 天士力应占 {d['tsl']:.2f}，昆药应占 {d['kpc']:.2f}，圣火 {d['sh']:.2f}，PPA {d['ppa']:.2f}")
    print(f"  本部 2026H1 同比：归母 {lt['2026H1']['sj_np']/lt['2025H1']['sj_np']-1:+.1%}，"
          f"扣非 {lt['2026H1']['sj_kf']/lt['2025H1']['sj_kf']-1:+.1%}，营收 {lt['2026H1']['sj_rev']/lt['2025H1']['sj_rev']-1:+.1%}")
    # 本部单季营收（合并 − 天士力 − 昆药；天士力 2025Q1 未并表）
    q_rev = {"2025Q1": 68.54 - 16.08, "2026Q1": 81.30 - 21.65 - 8.36,
             "2025Q2": 79.57 - (42.88 - 20.55) - (33.51 - 16.08),
             "2026Q2": 68.84 - (42.01 - 21.65) - (16.43 - 8.36)}
    print(f"  本部单季营收：Q1 {q_rev['2025Q1']:.2f}→{q_rev['2026Q1']:.2f}（{q_rev['2026Q1']/q_rev['2025Q1']-1:+.1%}），"
          f"Q2 {q_rev['2025Q2']:.2f}→{q_rev['2026Q2']:.2f}（{q_rev['2026Q2']/q_rev['2025Q2']-1:+.1%}）")
    # 2026Q3 估计（基准）：本部归母约为 2025Q3 的 99%，天士力 Q3 归母 2.3、营收 20.0，昆药 Q3 归母 −0.8、营收 8.0，
    # 圣火 Q3 净利 0.15，购买价分摊 0.12；本部营收 37.5（与 2025Q3 持平）。
    q3_sj = lt["2025Q3"]["sj_np"] * 0.99
    q3 = q3_sj + STAKE_TSL * 2.3 + STAKE_KPC * (-0.8) + STAKE_SH * 0.15 - 0.12
    q3_rev = 37.5 + 20.0 + 8.0
    print(f"  2026Q3 估计：归母 {q3:.2f}（2025Q3 5.38，{q3/5.38-1:+.0%}），营收 {q3_rev:.1f}（2025Q3 71.76，"
          f"{q3_rev/71.76-1:+.0%}），本部归母 {q3_sj:.2f}；前三季度归母 {16.71+q3:.2f}（2025 同期 23.53）")
    print("== 经调整净现金（亿元）")
    print(f"  合并现金类+存单 {nc['cons_gross']:.2f}；数据包口径 现金类−有息负债(含租赁) {nc['naive']:.2f}")
    print(f"  合并经调整净现金（100%） {nc['cons_adj']:.2f}")
    print(f"  三九本部 {nc['sj']:.2f}（现金类+存单 {nc['sj_gross']:.2f}，有息负债 {nc['sj_debt']:.2f}）"
          f"；天士力 100% {nc['tsl']:.2f}；昆药 100% {nc['kpc']:.2f}")
    print(f"  归母应占经调整净现金 net_cash_adj_yi = {nc['parent']:.2f}")
    print(f"  归母应占非经营资产 = {no['parent']:.2f}（本部 {no['sj']:.2f}，天士力 100% {no['tsl']:.2f}，昆药 100% {no['kpc']:.2f}）")
    print("== 三情景（9%）")
    res = {}
    for k in ("bear", "base", "bull"):
        r = scenario_value(k)
        res[k] = r
        print(f"  {k}: V={r['v']:.2f} 元  归母价值 {r['equity']:.1f} 亿 | 本部经营 {r['sj_op']:.1f} "
              f"本部合计 {r['sj_total']:.1f} 天士力100% {r['tsl_eq']:.1f} 昆药100% {r['kpc_eq']:.1f} "
              f"圣火100% {r['sh_op']:.1f} | 2026正常化归母净利 {r['norm_np']:.2f} | 本部终值占比 {r['tv_share']:.0%}")
        print("     归母所有者收益 2027-2031: " + ", ".join(f"{x:.2f}" for x in r["oe_parent"]))
    vw = weighted()
    pv = PRICE / vw
    tier = ("明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else
            "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高")
    print(f"== 加权 V = {vw:.2f} 元；P/V = {pv:.3f}（{tier}）")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"== 股权成本 8%: 加权 V = {v8:.2f}（熊 {scenario_value('bear',0.08)['v']:.2f} / 基 "
          f"{scenario_value('base',0.08)['v']:.2f} / 牛 {scenario_value('bull',0.08)['v']:.2f}）")
    print(f"== 股权成本 10%: 加权 V = {v10:.2f}（熊 {scenario_value('bear',0.10)['v']:.2f} / 基 "
          f"{scenario_value('base',0.10)['v']:.2f} / 牛 {scenario_value('bull',0.10)['v']:.2f}）")
    irr = implied_irr()
    irr_w = bisect(lambda r: weighted(r) - PRICE, 0.05, 0.20)
    print(f"== 现价隐含回报（基准情景）= {irr:.2%}；按三情景加权 V 求解 = {irr_w:.2%}")
    g_perp, g10, oe0 = reverse_dcf()
    print(f"== 反向 DCF：本部永续增速 {g_perp:.2%}；归母所有者收益 10 年增速 {g10:.2%}（起点 {oe0:.2f} 亿，之后 2%）")
    print("== 分档价格（V 不变）："
          f"≤{0.75*vw:.2f} 明显低估；{0.75*vw:.2f}～{0.90*vw:.2f} 温和低估；"
          f"{0.90*vw:.2f}～{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵")
    # 证伪触发后的 V：把对应部分换成熊市假设，其余按加权
    print("== 证伪触发后的独立 V")
    for label, swap in (("本部转熊（本部全部取熊）", ("sj",)),
                        ("天士力转熊", ("tsl",)),
                        ("昆药与圣火转熊", ("kpc", "sh")),
                        ("本部与昆药同时转熊", ("sj", "kpc", "sh"))):
        vv = 0.0
        for k, p in PROBS.items():
            saved = dict(SCEN[k])
            for part in swap:
                for key in list(SCEN[k].keys()):
                    if key.startswith(part + "_"):
                        SCEN[k][key] = SCEN["bear"][key]
                if part == "kpc":
                    SCEN[k]["floor_kpc"] = SCEN["bear"]["floor_kpc"]
            vv += p * scenario_value(k)["v"]
            SCEN[k] = saved
        print(f"  {label}: V = {vv:.2f}")
    # 资本配置：新增 ≥50 亿元、收益率约 5% 的并购，按 (1 − 5%/9%) 计价值折损
    loss = 50 * (1 - 0.05 / COE)
    print(f"  新增 50 亿元低回报并购（收益率 5%）: 价值折损 {loss:.1f} 亿 → V = {weighted() - loss / SHARES:.2f}")
    # 基准路径：归母净利与所有者收益
    b = SCEN["base"]
    sj, tsl = b["sj_norm"], b["tsl_norm"]
    oe_prev = (b["sj_norm"] * (1 - b["sj_reinv"]) + STAKE_TSL * b["tsl_norm"] * (1 - reinv(b["tsl_g"][0]))
               + STAKE_KPC * b["kpc_norm"] + STAKE_SH * b["sh_norm"])
    print(f"== 基准路径（2026 正常化归母所有者收益 {oe_prev:.2f}）")
    oe_b = scenario_value("base")["oe_parent"]
    for i, y in enumerate(YEARS):
        sj *= 1 + b["sj_g"][i]
        tsl *= 1 + b["tsl_g"][i]
        npp = sj + STAKE_TSL * tsl + STAKE_KPC * b["kpc_np"][i] + STAKE_SH * b["sh_np"][i] - PPA_AFTER_TAX_PARENT
        g_oe = oe_b[i] / (oe_b[i - 1] if i else oe_prev) - 1
        print(f"  {y}: 归母净利 {npp:.2f}，归母所有者收益 {oe_b[i]:.2f}（{g_oe:+.1%}），本部再投资率 {b['sj_reinv']:.0%}")
    # 交叉验证
    print("== 交叉验证")
    mv_tsl, mv_kpc = 207.81, 65.86   # 2026-10-21 腾讯行情总市值
    print(f"  上市子公司按市值：天士力 28% = {STAKE_TSL*mv_tsl:.1f} 亿，昆药 29.08% = {STAKE_KPC*mv_kpc:.1f} 亿；"
          f"三九总市值 {PRICE*SHARES:.1f} 亿 → 隐含本部+圣火+非经营 {PRICE*SHARES-STAKE_TSL*mv_tsl-STAKE_KPC*mv_kpc:.1f} 亿")
    sotp_mkt = (res['base']['sj_total'] + STAKE_TSL * mv_tsl + STAKE_KPC * mv_kpc
                + STAKE_SH * res['base']['sh_op'])
    print(f"  分部加总（本部按基准 DCF、子公司按市值）= {sotp_mkt:.1f} 亿 → {sotp_mkt/SHARES:.2f} 元")
    print(f"  股息率（过去 12 个月 1.005 元）= {1.005/PRICE:.2%}；2025 年度分红率 "
          f"{(0.45+0.59)*SHARES/34.21:.1%}")
    print(f"  PE(TTM 归母 32.77) = {PRICE*SHARES/32.77:.1f}×；PE(基准 2026 正常化) = "
          f"{PRICE*SHARES/res['base']['norm_np']:.1f}×；PB = {PRICE*SHARES/228.32:.2f}×")
    ev = PRICE * SHARES + 0.72 * mv_tsl + 0.7092 * mv_kpc + 6.55 + CONS_DEBT_EX_LEASE - nc['cons_gross']
    ebit_ttm = 8.05 + 14.26 + 15.99 + 9.00 + (0.13 + 0.15 + 0.15 + 0.12)  # 近四季营业利润 + 财务费用（净利息）
    print(f"  合并 EV（少数股东按市值）= {ev:.1f} 亿；EV/EBIT(TTM≈{ebit_ttm:.1f}) = {ev/ebit_ttm:.1f}×")


if __name__ == "__main__":
    main()
