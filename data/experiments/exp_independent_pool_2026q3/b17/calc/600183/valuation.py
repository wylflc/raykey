#!/usr/bin/env python3
"""生益科技（600183）独立估值：分部加总 + 所有者收益 DCF（OI-291 b17，价格日 2026-10-21）。

口径：金额亿元，每股元。估值日 2026-10-21；资产负债表 2026-06-30（2026 中报）。
分部：① 覆铜板及其他（不含生益电子，下称“本部”）按所有者收益 DCF；② 生益电子（688183）
按同一框架独立估值后乘持股；③ 非经营资产（联瑞新材股权、联瑞转债、地产、其他联营）；
④ 本部经调整净现金；⑤ 26SYKEB 可交换债逐情景取低。
现金流：2026H2 存根（2026-12-31 折现）+ 2027–2031 年中折现 + 2031 年中终值。
景气超额：2026H2–2029 的实际利润高于正常化利润的部分单列；再投资只按正常化收入的量增计。
运行：python3 valuation.py
"""
import json

# ---------------- 快照 ----------------
PRICE = 118.99                 # 2026-10-21 收盘
SHARES = 24.29003670           # 亿股：2,429,003,670（2026-07-14 回购注销 115,560 股后；无回购专户）
MCAP = PRICE * SHARES
R0, GT = 0.09, 0.025
T_STUB = 71 / 365              # 2026-10-21 → 2026-12-31
T_YEARS = [T_STUB + 0.5 + i for i in range(5)]   # 2027..2031 年中
PROB = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ---------------- 2026 三季度推算（2026-10-17 前三季度预告，2026H1 实际） ----------------
H1_NP, H1_KF = 32.87, 29.08                  # 2026H1 归母、扣非（中报第 5 页）
NM9 = {"bear": 64.60, "base": 66.65, "bull": 68.70}   # 前三季度归母预告下限/中值/上限
Q3_NONREC = (64.60 - 61.20) - (H1_NP - H1_KF)          # 前三季度非经常 3.40 − H1 3.79 = −0.39
SE_Q3 = {"bear": 7.58, "base": 7.995, "bull": 8.41}    # 生益电子 Q3 推算（前三季度预告 18.69–19.52 − H1 11.11）
SE_STAKE_Q3 = 0.622            # Q3 平均持股（62.499% 至 09-17 定增前，之后 60.81%）
ASSOC_Q = 0.20                 # 联营投资收益/季（另按市值或账面计入，不进经营利润）

def ccl_q3(s):
    return NM9[s] - H1_NP - SE_Q3[s] * SE_STAKE_Q3 - Q3_NONREC - ASSOC_Q

# ---------------- 生益电子与可交换债 ----------------
SE_PRICE = 93.24               # 2026-10-21 收盘（腾讯行情）
SE_TOTAL = 8.60261067          # 亿股（2026-09-17 定增 2,266.98 万股登记后）
SE_HELD_0630 = 0.62499 * 8.37591234   # 中报表决权 62.499% × 06-30 股本 837,591,234 股 = 5.2348 亿股
EB_EXCH_SH = 0.00325276        # 截至 2026-08-10 已换股 325,276 股（中报第 43 页）
EB_PRICE = 96.84               # 现行换股价
SE_HELD = SE_HELD_0630 - EB_EXCH_SH
EB_FACE = 20.0 - EB_EXCH_SH * EB_PRICE      # 未换股面值 ≈ 19.685
EB_SH = EB_FACE / EB_PRICE                  # 全部换股需交付的生益电子股数（亿股）
# 生益电子 2026-06-30（东财 F10）：现金 4.0718；短借 21.4221；长借 3.3743；一年内到期 1.8176（含一年内到期租赁 0.1270）；
# 租赁负债 0.3668。2026-09-17 定增净额约 25.20。经营备付 2% × 125。租赁按框架只列示不扣。
SE_DEBT_EX_LEASE = 21.4221 + 3.3743 + (1.8176 - 0.1270)
SE_NETCASH = 4.0718 + 25.20 - SE_DEBT_EX_LEASE - 2.50

# ---------------- 本部经调整净现金（2026-06-30，不含生益电子、不含可交换债） ----------------
CASH, TFA = 19.9726, 26.3126   # 合并货币资金、交易性金融资产（理财 20.02、联瑞转债 5.79、股票 0.41 等）
CASH_LIKE = CASH + TFA
DEBT_CONS = dict(st=30.4728, lt=8.5622, cur=4.9839 - 0.1270)   # 合并短借、长借、一年内到期（不含租赁）
NC = dict(
    cash_like_ex_se=CASH_LIKE - 4.0718,
    less_lrcb_fv=-5.7855,       # 联瑞转债 06-30 公允价值，另按现价计入
    less_restricted=-0.1293,    # 受限货币资金（中报第 13 页）
    less_op_reserve=-5.30,      # 经营备付 2% × 本部正常化收入 262.5
    less_debt=-(sum(DEBT_CONS.values()) - SE_DEBT_EX_LEASE),      # 本部短借+长借+一年内到期
)
NET_CASH = sum(NC.values())
# 合并口径对照：06-30 与计入生益电子 09-17 定增后的备考
NET_CASH_CONS = CASH_LIKE - 5.7855 - 0.1293 - 5.30 - 2.50 - sum(DEBT_CONS.values())
NET_CASH_CONS_PF = NET_CASH_CONS + 25.20

# ---------------- 非经营资产 ----------------
LR_SH, LR_PRICE, LR_BOOK = 0.561730 * 1.3, 102.20, 4.1637   # 联瑞新材 5,617.3 万股 ×1.3（10 转 3，10-16 除权）
LR_MKT = LR_SH * LR_PRICE
LRCB = 0.01616660 * 278.72                  # 联瑞转债 1,616,660 张 × 278.72 元（10-21 收盘），假定仍持有
LRCB_AT = LRCB - 0.15 * (LRCB - 1.61666)
RE_INV, LAND_COMP = 7.516 + 3.129, 2.180    # 地产开发成本+开发产品（净额）；万江老厂区收储补偿（含税）
NONOP = {
    "bear": dict(lianrui=LR_MKT - 0.25 * (LR_MKT - LR_BOOK), lrcb=LRCB_AT, realestate=RE_INV * 0.4 + LAND_COMP * 0.75,
                 inv_property=1.37, other_assoc=4.176 * 0.6, other_fin=0.10),
    "base": dict(lianrui=LR_MKT, lrcb=LRCB_AT, realestate=RE_INV * 0.6 + LAND_COMP * 0.75,
                 inv_property=1.37, other_assoc=4.176 * 0.8, other_fin=0.10),
    "bull": dict(lianrui=LR_MKT, lrcb=LRCB_AT, realestate=RE_INV * 0.8 + LAND_COMP * 0.75,
                 inv_property=1.37, other_assoc=4.176 * 1.0, other_fin=0.10),
}

# ---------------- 情景参数 ----------------
# rev26：2026 正常化收入；m：正常化净利率；k：每 1 元新增收入所需净投入（固定资产+营运资本）；
# g：2027–2031 正常化收入增速；ronic_t：终值期增量回报；other：废弃资源综合利用归母净利；
# act：实际利润（含景气超额），None 为回到正常化；vol26：2026 量增（用于 2026H2 再投资）
CCL = {
    "bear": dict(rev26=230.0, m=0.100, k=0.80, g=[0.06, 0.06, 0.05, 0.05, 0.04], ronic_t=0.11, other=0.2, vol26=0.12,
                 act={"2026H2": ccl_q3("bear") + 22.0, 2027: 50.0, 2028: "trough", 2029: None}),
    "base": dict(rev26=262.5, m=0.130, k=0.75, g=[0.09, 0.09, 0.08, 0.07, 0.06], ronic_t=0.14, other=0.3, vol26=0.12,
                 act={"2026H2": ccl_q3("base") + 29.0, 2027: 85.0, 2028: 55.0, 2029: None}),
    "bull": dict(rev26=290.0, m=0.165, k=0.70, g=[0.13, 0.12, 0.11, 0.10, 0.08], ronic_t=0.18, other=0.4, vol26=0.12,
                 act={"2026H2": ccl_q3("bull") + 34.0, 2027: 115.0, 2028: 95.0, 2029: 75.0}),
}
SE = {
    "bear": dict(rev26=115.0, m=0.10, k=0.80, g=[0.06, 0.05, 0.04, 0.03, 0.03], ronic_t=0.11, other=0.0, vol26=0.25,
                 act={"2026H2": SE_Q3["bear"] + 7.0, 2027: 18.0, 2028: None, 2029: None}),
    "base": dict(rev26=125.0, m=0.15, k=0.75, g=[0.14, 0.12, 0.10, 0.08, 0.06], ronic_t=0.15, other=0.0, vol26=0.25,
                 act={"2026H2": SE_Q3["base"] + 8.5, 2027: 30.0, 2028: 28.0, 2029: None}),
    "bull": dict(rev26=140.0, m=0.18, k=0.70, g=[0.20, 0.17, 0.14, 0.10, 0.08], ronic_t=0.18, other=0.0, vol26=0.25,
                 act={"2026H2": SE_Q3["bull"] + 9.5, 2027: 38.0, 2028: 44.0, 2029: 44.0}),
}
TROUGH = 0.85   # 熊市 2028 年跌价去库存：利润为正常化的 85%


def dcf(p, r=R0, act_override=None):
    """返回 dict：pv 合计、各期明细。p 为情景参数。"""
    act = dict(p["act"])
    if act_override:
        act.update(act_override)
    rev, m, k, other = p["rev26"], p["m"], p["k"], p["other"]
    np26 = rev * m + other
    rows = []
    # 2026H2 存根
    re26 = 0.5 * k * (rev - rev / (1 + p["vol26"]))
    np_h2 = act["2026H2"]
    oe = np_h2 - re26
    pv = oe / (1 + r) ** T_STUB
    rows.append(("2026H2", np26 / 2, np_h2, re26, oe, pv))
    revs = [rev]
    for i, g in enumerate(p["g"]):
        yr = 2027 + i
        prev = revs[-1]
        cur = prev * (1 + g)
        revs.append(cur)
        np_norm = cur * m + other
        a = act.get(yr)
        if a is None:
            np_act = np_norm
        elif a == "trough":
            np_act = np_norm * TROUGH
        else:
            np_act = a
        reinv = k * (cur - prev)
        oe = np_act - reinv
        pvi = oe / (1 + r) ** T_YEARS[i]
        pv += pvi
        rows.append((yr, np_norm, np_act, reinv, oe, pvi))
    np32 = revs[-1] * (1 + GT) * m + other
    oe32 = (np32 - other) * (1 - GT / p["ronic_t"]) + other
    tv = oe32 / (r - GT)
    pv_tv = tv / (1 + r) ** T_YEARS[-1]
    pv += pv_tv
    return dict(pv=pv, rows=rows, np26=np26, tv=tv, pv_tv=pv_tv, revs=revs, oe32=oe32)


def norm_only(p, r=R0):
    """不含景气超额的纯正常化 DCF（用于拆分超额利润的现值）。"""
    act = {"2026H2": (p["rev26"] * p["m"] + p["other"]) / 2, 2027: None, 2028: None, 2029: None}
    return dcf(dict(p, act=act), r)


def se_value(s, r=R0, p_override=None, act_override=None):
    p = dict(SE[s])
    if p_override:
        p.update(p_override)
    d = dcf(p, r, act_override)
    eq = d["pv"] + SE_NETCASH
    return eq, eq / SE_TOTAL, d


def company_value(s, r=R0, ccl_override=None, ccl_act=None, se_s=None, se_act=None, se_mkt=False):
    p = dict(CCL[s])
    if ccl_override:
        p.update(ccl_override)
    d = dcf(p, r, ccl_act)
    se_eq, se_ps, _ = se_value(se_s or s, r, act_override=se_act)
    if se_mkt:
        se_ps = SE_PRICE
    stake = SE_HELD * se_ps
    nonop = sum(NONOP[s].values())
    v_debt = d["pv"] + stake + nonop + NET_CASH - EB_FACE            # 可交换债按面值全额扣除
    v_exch = d["pv"] + (SE_HELD - EB_SH) * se_ps + nonop + NET_CASH  # 全部换股：少持 EB_SH 股，不扣债
    v = min(v_debt, v_exch)
    return dict(ccl=d["pv"], stake=stake, se_ps=se_ps, nonop=nonop, v_debt=v_debt / SHARES,
                v_exch=v_exch / SHARES, v_ps=v / SHARES, total=v, ccl_d=d)


def weighted(r=R0, **kw):
    return sum(PROB[s] * company_value(s, r, **kw)["v_ps"] for s in PROB)


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


def main():
    out = {}
    print("=== 快照 ===")
    print(f"现价 {PRICE}  总股本 {SHARES:.4f} 亿股  市值 {MCAP:.2f} 亿")
    print(f"Q3 推算：归母 {NM9['base'] - H1_NP:.2f}（{NM9['bear'] - H1_NP:.2f}–{NM9['bull'] - H1_NP:.2f}），"
          f"Q3 非经常 {Q3_NONREC:.2f}；本部 Q3 经常性 {ccl_q3('base'):.2f}（{ccl_q3('bear'):.2f}–{ccl_q3('bull'):.2f}）")
    print(f"生益电子：持股 {SE_HELD:.4f} 亿股 / {SE_TOTAL:.4f}（{SE_HELD / SE_TOTAL:.2%}），市值口径 {SE_HELD * SE_PRICE:.1f} 亿；"
          f"经调整净现金 {SE_NETCASH:.2f}")
    print(f"可交换债：未换股面值 {EB_FACE:.3f} 亿，全部换股需交付 {EB_SH * 1e4:.0f} 万股生益电子")
    print("本部经调整净现金：" + "，".join(f"{k} {v:.2f}" for k, v in NC.items()) + f" → {NET_CASH:.2f}")
    print(f"合并口径经调整净现金（不含可交换债）：06-30 {NET_CASH_CONS:.2f}；计入生益电子定增后备考 {NET_CASH_CONS_PF:.2f}")
    print(f"联瑞新材 {LR_SH * 1e4:.1f} 万股 × {LR_PRICE} = {LR_MKT:.2f}；联瑞转债 {LRCB:.2f}（税后 {LRCB_AT:.2f}）")

    print("\n=== 三情景（9%） ===")
    res = {}
    for s in PROB:
        cv = company_value(s)
        res[s] = cv
        d = cv["ccl_d"]
        se_eq, se_ps, sd = se_value(s)
        nn = norm_only(CCL[s])
        print(f"\n[{s}] 本部 DCF {cv['ccl']:.1f}（正常化部分 {nn['pv']:.1f}，景气超额 {cv['ccl'] - nn['pv']:.1f}；"
              f"终值现值 {d['pv_tv']:.1f}，占本部 {d['pv_tv'] / cv['ccl']:.0%}）")
        print("  年份  正常化净利  实际净利  再投资  所有者收益  现值")
        for row in d["rows"]:
            print("  {}  {:8.2f}  {:8.2f}  {:6.2f}  {:8.2f}  {:7.2f}".format(*row))
        print(f"  终值：2032 所有者收益 {d['oe32']:.2f}，TV {d['tv']:.1f}，现值 {d['pv_tv']:.1f}")
        print(f"  生益电子 100% 独立价值 {se_eq:.1f} 亿（{se_ps:.2f} 元/股，市价 P/V {SE_PRICE / se_ps:.2f}）；"
              f"持股价值 {cv['stake']:.1f}")
        print(f"  非经营资产 {cv['nonop']:.1f}：" + "，".join(f"{k} {v:.2f}" for k, v in NONOP[s].items()))
        print(f"  可交换债取低：按债务 {cv['v_debt']:.2f} 元 / 全部换股 {cv['v_exch']:.2f} 元 → 取 {cv['v_ps']:.2f} 元")
        out[s] = round(cv["v_ps"], 2)

    vw = weighted()
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv:.2f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：V = {v8:.2f}（P/V {PRICE / v8:.2f}）；10%：V = {v10:.2f}（P/V {PRICE / v10:.2f}）")

    # 市值口径交叉核对：生益电子按 93.24 元计入（等价于合并口径扣除按市值计的少数股东权益）
    vm = {s: company_value(s, se_mkt=True)["v_ps"] for s in PROB}
    vmw = sum(PROB[s] * vm[s] for s in PROB)
    print("生益电子按市值计入：" + "，".join(f"{s} {vm[s]:.2f}" for s in PROB) + f"；加权 {vmw:.2f}（P/V {PRICE / vmw:.2f}）")
    mi_mkt = (SE_TOTAL - SE_HELD) * SE_PRICE
    print(f"  （少数股东按市值 {mi_mkt:.1f} 亿，账面 24.24 亿）")

    # 隐含回报：基准情景现金流使每股价值等于现价的折现率
    irr = solve(lambda r: company_value("base", r)["v_ps"], 0.0255, 0.09, PRICE)
    print(f"现价隐含回报（基准现金流）：{irr:.2%}")

    # 反向 DCF
    base = company_value("base")
    ops_target = MCAP - base["nonop"] - NET_CASH + EB_FACE         # 经营部分（本部 + 生益电子持股）须值多少
    stake_frac = SE_HELD / SE_TOTAL
    pc, ps = CCL["base"], SE["base"]
    oe0_norm = (pc["rev26"] * pc["m"] + pc["other"]) * (1 - 0.08 / (pc["m"] / pc["k"])) + \
        stake_frac * ps["rev26"] * ps["m"] * (1 - 0.12 / (ps["m"] / ps["k"]))
    np26e = NM9["base"] + 29.0 + 8.5 * stake_frac + ASSOC_Q   # 前三季度中值 + Q4（本部 29 + 生益电子 8.5×持股 + 联营）
    oe0_act = np26e * 0.65

    def pv_growth(oe0, g, years=10, r=R0):
        tot, oe = 0.0, oe0
        for t in range(1, years + 1):
            oe *= (1 + g)
            tot += oe / (1 + r) ** t
        return tot + oe * (1 + GT) / (r - GT) / (1 + r) ** years

    g_norm = solve(lambda g: pv_growth(oe0_norm, g), 0.0, 0.8, ops_target)
    g_act = solve(lambda g: pv_growth(oe0_act, g), -0.2, 0.8, ops_target)
    g_perp = (R0 * ops_target - oe0_act) / (ops_target + oe0_act)
    print(f"反向 DCF：经营部分须值 {ops_target:.0f} 亿；以正常化所有者收益 {oe0_norm:.1f} 亿起步，"
          f"隐含 10 年年增 {g_norm:.1%}；以 2026E 实际水平（归母 {np26e:.1f} 亿 × 65% = {oe0_act:.1f} 亿）起步，"
          f"隐含 10 年年增 {g_act:.1%}，或永续增长 {g_perp:.1%}")

    # 2026 正常化归母净利（含净利息与联营投资收益，剔除一次性；生益电子按定增后持股 60.81%）
    nnp = {}
    for s in PROB:
        c, e = CCL[s], SE[s]
        nnp[s] = c["rev26"] * c["m"] + c["other"] + stake_frac * e["rev26"] * e["m"] + 0.85
    print("2026 正常化归母净利：" + "，".join(f"{s} {nnp[s]:.1f}" for s in PROB) + f"（2026E 实际约 {np26e:.1f}）")

    # 增长路径（基准，正常化归母净利与所有者收益）
    dc, ds = norm_only(CCL["base"]), norm_only(SE["base"])
    np_path = [nnp["base"]] + [dc["rows"][i][1] + stake_frac * ds["rows"][i][1] + 0.85 for i in range(1, 6)]
    gpath = [np_path[i] / np_path[i - 1] - 1 for i in range(1, 6)]
    oe_path = [dc["rows"][i][4] + stake_frac * ds["rows"][i][4] + 0.85 for i in range(1, 6)]
    reinv = sum(dc["rows"][i][3] + stake_frac * ds["rows"][i][3] for i in range(1, 6)) / sum(np_path[1:])
    roic_ccl = CCL["base"]["m"] / CCL["base"]["k"]
    roic_se = SE["base"]["m"] / SE["base"]["k"]
    re_c = sum(dc["rows"][i][3] for i in range(1, 6))
    re_s = stake_frac * sum(ds["rows"][i][3] for i in range(1, 6))
    roic_w = (roic_ccl * re_c + roic_se * re_s) / (re_c + re_s)
    print("基准正常化归母净利 2026–2031：" + "，".join(f"{x:.1f}" for x in np_path) +
          "；增速 " + "，".join(f"{g:.1%}" for g in gpath))
    print("基准正常化所有者收益（归母）2027–2031：" + "，".join(f"{x:.1f}" for x in oe_path) +
          f"；平均再投资率 {reinv:.0%}；增量回报 本部 {roic_ccl:.1%}、生益电子 {roic_se:.1%}、加权 {roic_w:.1%}")
    for s in PROB:
        rc, rs = company_value(s)["ccl_d"]["rows"], se_value(s)[2]["rows"]
        path = [(rc[i][0], rc[i][2] + (SE_STAKE_Q3 if i == 0 else stake_frac) * rs[i][2] + (0.42 if i == 0 else 0.85))
                for i in range(0, 4)]
        print(f"  [{s}] 实际归母净利路径（含景气超额）：" +
              "，".join(f"{y} {v:.1f}" for y, v in path) + f"（2026 全年 ≈ {H1_NP - 3.79 + path[0][1]:.1f}，扣除 H1 非经常）")

    # 证伪条件触发后的 V（加权口径：只改相应假设）
    def wv(**kw):
        return sum(PROB[s] * company_value(s, **kw)["v_ps"] for s in PROB)
    f1 = sum(PROB[s] * company_value(s, ccl_act={2027: min(CCL[s]["act"][2027], 55.0), 2028: None, 2029: None},
                                     se_act={2027: min(SE[s]["act"][2027], 24.0), 2028: None, 2029: None})["v_ps"]
             for s in PROB)
    f2 = company_value("base", ccl_override=dict(m=0.165, k=0.70, ronic_t=0.18, rev26=262.5))["v_ps"]
    f3 = company_value("base", ccl_act={2027: 115.0, 2028: 95.0, 2029: 70.0}, se_act={2027: 38.0, 2028: 40.0})["v_ps"]
    f4 = sum(PROB[s] * company_value(s, se_s="bear")["v_ps"] for s in PROB)
    f5 = company_value("base", ccl_override=dict(m=0.165, k=0.70, ronic_t=0.18, rev26=262.5),
                       ccl_act={2027: 115.0, 2028: 95.0, 2029: 70.0}, se_s="bull")["v_ps"]
    f5m = company_value("base", ccl_override=dict(m=0.165, k=0.70, ronic_t=0.18, rev26=262.5),
                        ccl_act={2027: 115.0, 2028: 95.0, 2029: 70.0}, se_mkt=True)["v_ps"]
    print(f"证伪触发后 V：F1 景气提前结束 {f1:.2f}；F2 正常化净利率 16.5% 获证实 {f2:.2f}；"
          f"F3 景气延续至 2028 {f3:.2f}；F4 生益电子落入熊市 {f4:.2f}；"
          f"F2+F3 同时成立且生益电子取牛市 {f5:.2f}（生益电子按市值 {f5m:.2f}）")

    # 分档价格（V 不变）
    print(f"分档价格：≤{0.75 * vw:.1f} 明显低估；{0.75 * vw:.1f}–{0.90 * vw:.1f} 温和低估；"
          f"{0.90 * vw:.1f}–{1.10 * vw:.1f} 大致合理；>{1.10 * vw:.1f} 偏贵")

    # 交叉验证
    np_ttm, eq = 51.94, 185.02
    ev = MCAP + 63.41 - CASH_LIKE + (SE_TOTAL - SE_HELD) * SE_PRICE + 1.34 - LR_MKT - LRCB - 12.0
    ebit26e, ebit_norm = 125.0, 61.6
    print(f"交叉：PE(TTM) {MCAP / np_ttm:.1f}，PE(2026E) {MCAP / np26e:.1f}，PE(正常化基准) {MCAP / nnp['base']:.1f}；"
          f"PB {MCAP / eq:.2f}；EV {ev:.0f}，EV/EBIT(2026E≈{ebit26e:.0f}) {ev / ebit26e:.1f}，"
          f"EV/EBIT(正常化≈{ebit_norm}) {ev / ebit_norm:.1f}；股息率 {0.80 / PRICE:.2%}（2025 全年 1.20 元：{1.20 / PRICE:.2%}）")

    summary = dict(v=out, v_weighted=round(vw, 2), pv=round(pv, 2), v8=round(v8, 2), v10=round(v10, 2),
                   irr=round(irr, 4), v_mkt_se=round(vmw, 2), nnp={k: round(v, 1) for k, v in nnp.items()},
                   net_cash=round(NET_CASH, 2), nonop_base=round(sum(NONOP["base"].values()), 1),
                   g_path=[round(g, 3) for g in gpath], reinv=round(reinv, 3), roic_w=round(roic_w, 3),
                   falsifiers=[round(f1, 2), round(f2, 2), round(f3, 2), round(f4, 2), round(f5, 2), round(f5m, 2)],
                   g_norm=round(g_norm, 3), g_act=round(g_act, 3), g_perp=round(g_perp, 3))
    print("\nSUMMARY " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
