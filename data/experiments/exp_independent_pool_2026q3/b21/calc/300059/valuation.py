#!/usr/bin/env python3
"""300059 东方财富：独立估值计算（OI-291 b21，价格日 2026-10-21）。

方法：金融企业口径的剩余收益模型（RI）。
  1) 驱动因子模型把 2026 年归母净利按多年中枢正常化（A 股成交额、两融、客户资金、
     天天基金非货保有、自营收益率、佣金收益率）；
  2) 以 2026 年末预计归母权益为期初账面，2027-2031 年显式期（ROE 线性收敛到终值 ROE，
     权益按业务增速增长，派息 = 净利 − 权益增量），2032 年起按终值增长；
  3) 熊／基准／牛三情景概率加权；另做分部加总、同业 PB、隐含回报与反向推算。
金额单位亿元，每股价值元/股。所有输入写在本文件内，`python3 valuation.py` 直接复现正文与 json。
"""
from datetime import date

# ---------------------------------------------------------------- 快照与账面
PRICE = 17.90                  # 2026-10-21 收盘（brief.md）
SHARES = 158.2220              # 亿股，总股本（无回购专户、无拟注销股份；预留限制性股票 95.30 万股待归属，可忽略）
MKT_CAP = PRICE * SHARES       # 2,832.2 亿元
COE = 0.09
B_H1 = 984.06                  # 2026-06-30 归母权益（2026H1_report 第 42 页）
NP_H1 = 80.64                  # 2026H1 归母净利（2026H1_report 第 7 页）
Q3E = 36.5                     # 2026Q3 估计（A 股成交额 147.9 万亿、两融季末 2.61 万亿，见正文）
Q4E = 29.0                     # 2026Q4 估计（日均成交额按 1.75 万亿）
NP_2026E = NP_H1 + Q3E + Q4E   # 2026 年报告口径估计
B0 = B_H1 + Q3E + Q4E          # 2026-12-31 预计归母权益（下半年无分红）
STUB = (date(2026, 12, 31) - date(2026, 10, 21)).days / 365.0
PARENT_NET_CASH = 16.26 + 18.43 - 1.40   # 母公司货币资金+交易性金融资产−短期借款（2026H1_report 第 42-43 页）

# ---------------------------------------------------------------- 校准（报告原文）
CAL = {
    # 项目: (2025 年, 2026H1)
    "A股成交额(万亿)": (420.0, 317.5),                      # 2025_annual_report 第 9 页；2026H1_report 第 10 页
    "代理买卖证券净收入": (102.469 - 29.274, 63.735 - 18.995),  # 2025AR 第 139 页；H1 第 109 页
    "席位租赁+代销金融产品": (1.213 + 2.830, 1.358 + 1.978),
    "期货经纪净收入": (9.378, 5.645),
    "其他手续费(投行/资管/基金管理/投顾/其他)": (0.272 + 1.342 + 0.914 + 1.802 + 0.054,
                                         0.599 + 1.073 + 1.008 + 2.859 + 0.288),
    "利息净收入": (34.355, 22.710),
    "其中融资融券利息收入": (36.306, 22.612),
    "金融电子商务服务(天天基金)": (31.820, 20.846),
    "金融数据服务等": (2.403 + 1.099, 1.950),
    "投资收益+公允价值变动": (26.503 - 2.806, 10.322 + 2.887),
    "其他收益(政府补助为主)": (4.238, 4.040),
}
NONMONEY_AUM = {"2025-12-31": 7701.33, "2026-06-30": 10120.0}   # 亿元
INV_BOOK = {"2024-12-31": 952.6, "2025-12-31": 1230.7, "2026-06-30": 1421.8}  # 交易性+其他债权+其他权益+债权投资（F10）


def calibration():
    out = {}
    t25, t26 = CAL["A股成交额(万亿)"]
    b25, b26 = CAL["代理买卖证券净收入"]
    out["佣金净收入/万亿成交额 2025"] = b25 / t25
    out["佣金净收入/万亿成交额 2026H1"] = b26 / t26
    out["天天基金收入/平均非货保有 2026H1(年化)"] = 2 * CAL["金融电子商务服务(天天基金)"][1] / (
        (NONMONEY_AUM["2025-12-31"] + NONMONEY_AUM["2026-06-30"]) / 2)
    out["自营收益率 2025"] = CAL["投资收益+公允价值变动"][0] / ((INV_BOOK["2024-12-31"] + INV_BOOK["2025-12-31"]) / 2)
    out["自营收益率 2026H1(年化)"] = 2 * CAL["投资收益+公允价值变动"][1] / (
        (INV_BOOK["2025-12-31"] + INV_BOOK["2026-06-30"]) / 2)
    m_avg_h1 = (808.5 + 2 * 812.7 + 964.5) / 4      # F10 融出资金 2025-12、2026-03、2026-06
    out["两融利息收益率 2026H1(年化)"] = 2 * CAL["其中融资融券利息收入"][1] / m_avg_h1
    return out


# ---------------------------------------------------------------- 驱动因子与情景
TRADING_DAYS = 242
SCEN = {
    "bear": dict(p=0.25, T=1.20, y_b=0.128, brk_other=4.5, fut=8.0, fee_other=6.5,
                 M_em=620, a_m=0.036, C=1100, b_c=0.0060, c_nii=-3.0,
                 AUM=7000, f_rate=0.0038, data=3.0, inv_book=1100, inv_y=0.0145, subsidy=1.7,
                 F=32.0, v=0.09, tax=0.145,
                 g=[0.02, 0.02, 0.02, 0.02, 0.02], g_T=0.02, fade=0.001),
    "base": dict(p=0.50, T=1.65, y_b=0.141, brk_other=6.0, fut=9.5, fee_other=9.0,
                 M_em=800, a_m=0.038, C=1500, b_c=0.0070, c_nii=-2.5,
                 AUM=9000, f_rate=0.0044, data=3.5, inv_book=1300, inv_y=0.0175, subsidy=3.2,
                 F=33.4, v=0.09, tax=0.145,
                 g=[0.05, 0.045, 0.04, 0.035, 0.03], g_T=0.025, fade=0.008),
    "bull": dict(p=0.25, T=2.30, y_b=0.150, brk_other=7.0, fut=11.0, fee_other=11.5,
                 M_em=950, a_m=0.039, C=1900, b_c=0.0075, c_nii=-2.0,
                 AUM=11000, f_rate=0.0046, data=4.0, inv_book=1450, inv_y=0.0195, subsidy=4.5,
                 F=34.5, v=0.09, tax=0.145,
                 g=[0.08, 0.07, 0.06, 0.05, 0.04], g_T=0.025, fade=0.015),
}
LABEL = {"bear": "熊", "base": "基准", "bull": "牛"}


def normalized_np(s):
    """2026 年正常化归母净利（报表口径，含净利息，政府补助按情景比例计入）。"""
    lines = {
        "经纪佣金(代理买卖净)": s["T"] * TRADING_DAYS * s["y_b"],
        "席位租赁+代销": s["brk_other"],
        "期货经纪": s["fut"],
        "其他手续费": s["fee_other"],
        "利息净收入": s["M_em"] * s["a_m"] + s["C"] * s["b_c"] + s["c_nii"],
        "基金销售(天天)": s["AUM"] * s["f_rate"],
        "金融数据等": s["data"],
        "自营投资收益": s["inv_book"] * s["inv_y"],
        "其他收益(补助)": s["subsidy"],
    }
    rev = sum(lines.values())
    cost = s["F"] + s["v"] * rev
    pbt = rev - cost
    np_ = pbt * (1 - s["tax"])
    return dict(lines=lines, rev=rev, cost=cost, pbt=pbt, np=np_)


def ri_value(s, r=COE, B=B0, np26=None, detail=False, payout_override=None, r_inc=None):
    """剩余收益估值，返回 2026-10-21 每股价值。
    默认路径：归母净利按 g（2027-2031 逐年增速，2027 年相对正常化 2026 年）增长；
    ROE 自 2027 年读数（= 2027 净利 / 2026 年末权益）线性下滑 fade 到 2031 年并作为终值 ROE；
    期初权益 B_{t-1} = 净利_t / ROE_t（t ≥ 2），可分配额 = 净利 − 权益增量；2032 年起净利与权益按 g_T 增长。
    低派息变体（payout_override、r_inc）：在默认路径上叠加多留存的资本，多留存部分按 r_inc 的税后
    增量回报计息，终值期继续按 g_T 增长、按 r_inc 计息。"""
    if np26 is None:
        np26 = normalized_np(s)["np"]
    g = s["g"]
    nps = []
    x = np26
    for gt in g:
        x *= 1 + gt
        nps.append(x)
    np6 = nps[-1] * (1 + s["g_T"])
    roe1 = nps[0] / B
    roe_T = roe1 - s["fade"]
    roes = [roe1 + (roe_T - roe1) * i / 4.0 for i in range(5)]
    bd_open = [B] + [nps[t] / roes[t] for t in range(1, 5)]      # 默认路径各年期初权益
    bd_end5 = np6 / roe_T                                         # 2031 年末权益
    rows = []
    b = B
    extra = 0.0
    pv = 0.0
    np_prev = np26
    for t in range(5):
        bd_next = bd_open[t + 1] if t < 4 else bd_end5
        if payout_override is None:
            np_t = nps[t]
            b_next = bd_next
        else:
            np_t = nps[t] + r_inc * extra
            b_next = b + np_t * (1 - payout_override)
        div_t = np_t - (b_next - b)
        ri_t = np_t - r * b
        pv += ri_t / (1 + r) ** (t + 1)
        rows.append(dict(year=2027 + t, np=np_t, b_open=b, roe=np_t / b, div=div_t, ri=ri_t,
                         g_np=np_t / np_prev - 1, payout=div_t / np_t))
        np_prev = np_t
        b = b_next
        extra = b - bd_next
    tv = ((roe_T - r) * bd_end5 + ((r_inc - r) * extra if payout_override is not None else 0.0)) / (r - s["g_T"])
    pv_tv = tv / (1 + r) ** 5
    v_end = B + pv + pv_tv
    v_now = v_end / (1 + r) ** STUB
    ps = v_now / SHARES
    if detail:
        reinvest = (bd_end5 - B) / sum(nps)                       # 2027-2031 累计再投资率
        inc_ret = (nps[-1] - nps[0]) / (bd_open[4] - B)            # 增量回报 = 净利增量 / 期初权益增量
        return dict(ps=ps, v_now=v_now, v_end=v_end, pv_ri=pv, pv_tv=pv_tv, rows=rows, roe1=roe1,
                    roe_T=roe_T, b5=b, tv_share=pv_tv / v_end, reinvest=reinvest, inc_ret=inc_ret)
    return ps


def ddm_check(s, r=COE):
    """股利折现复核（与 RI 应一致）。"""
    d = ri_value(s, r=r, detail=True)
    pv = sum(row["div"] / (1 + r) ** (i + 1) for i, row in enumerate(d["rows"]))
    b5 = d["b5"]
    div6 = d["roe_T"] * b5 - s["g_T"] * b5
    tv = div6 / (r - s["g_T"])
    v_end = pv + tv / (1 + r) ** 5
    return v_end / (1 + r) ** STUB / SHARES


def weighted(r=COE, scen=SCEN, weights=None):
    w = weights or {k: v["p"] for k, v in scen.items()}
    return sum(w[k] * ri_value(scen[k], r=r) for k in scen)


def implied_irr(s):
    """基准情景股利流（含终值）使现值等于现价的折现率。"""
    d = ri_value(s, detail=True)
    divs = [row["div"] for row in d["rows"]]
    b5 = d["b5"]
    div6 = d["roe_T"] * b5 - s["g_T"] * b5

    def pv(i):
        v = sum(x / (1 + i) ** (k + 1) for k, x in enumerate(divs))
        v += div6 / (i - s["g_T"]) / (1 + i) ** 5
        return v / (1 + i) ** STUB
    lo, hi = s["g_T"] + 0.0005, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv(mid) > MKT_CAP:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse():
    pb_adj = MKT_CAP * (1 + COE) ** STUB / B0         # 折到 2026 年末的市值 / 年末权益
    g = 0.025
    roe_implied = g + pb_adj * (COE - g)              # 稳态 P/B = (ROE−g)/(r−g)
    out = {"P/B(2026年末权益)": pb_adj, "隐含稳态ROE(g=2.5%)": roe_implied}
    for name, roe in [("TTM ROE 14.8%", 145.82 / B_H1), ("牛市 2027 ROE", None)]:
        if roe is None:
            roe = ri_value(SCEN["bull"], detail=True)["roe1"]
        # (roe − g)/(r − g) = pb  =>  g = (pb*r − roe)/(pb − 1)
        g_imp = (pb_adj * COE - roe) / (pb_adj - 1)
        out[f"隐含永续增长({name}={roe:.1%})"] = g_imp
    # 基准 ROE 下能达到的最高价值（g→ROE−0.1pp 的极限）检查
    return out


def value_const_roe(roe, g10, r=COE, gT=0.025, B=B0, years=10):
    """ROE 恒定、权益前 years 年按 g10 增长、此后按 gT 增长时的每股价值（反向推算用）。"""
    pv = 0.0
    b = B
    for t in range(1, years + 1):
        np_t = roe * b
        b_next = b * (1 + g10)
        pv += (np_t - (b_next - b)) / (1 + r) ** t
        b = b_next
    pv += b * (roe - gT) / (r - gT) / (1 + r) ** years
    return pv / (1 + r) ** STUB / SHARES


def implied_g10(roe):
    """现价隐含的 10 年净利（=权益）增速；无解返回 None。"""
    lo, hi = -0.05, 0.40
    if value_const_roe(roe, hi) < PRICE:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if value_const_roe(roe, mid) < PRICE:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def tax_expiry_delta(s, r=COE, sec_share=0.75, new_rate=0.25):
    """东方财富证券西部大开发 15% 税率 2030-12-31 到期不续：2031 年起证券子公司（约占税前 75%）按 25% 计税，
    权益路径不变、少分派，返回每股价值变化。"""
    d = ri_value(s, r=r, detail=True)
    k = 1 - sec_share * (new_rate - 0.15) / (1 - s["tax"])
    np31 = d["rows"][-1]["np"]
    np32 = np31 * (1 + s["g_T"])
    dv_end = (k - 1) * (np31 / (1 + r) ** 5 + np32 / (r - s["g_T"]) / (1 + r) ** 5)
    return dv_end / (1 + r) ** STUB / SHARES


def turnover_sensitivity():
    """基准情景：只改日均成交额，或成交额与两融、客户资金、保有按比例联动。"""
    out = []
    base = SCEN["base"]
    for T in (1.30, 1.65, 2.00, 2.30):
        only = dict(base, T=T)
        k = T / base["T"]
        co = dict(base, T=T, M_em=base["M_em"] * (0.5 + 0.5 * k), C=base["C"] * k,
                  AUM=base["AUM"] * (0.6 + 0.4 * k))
        out.append((T, normalized_np(only)["np"], ri_value(only), normalized_np(co)["np"], ri_value(co)))
    return out


def sotp(r=COE):
    """分部加总（基准）：证券子公司按正常化 ROE 的合理 PB，平台业务按 PE，母公司现金按账面。"""
    eq_sec_2026e = 806.36 + 0.55 * (Q3E + Q4E)        # 东方财富证券 2026-06-30 净资产 806.36（H1 第 17 页）+ 下半年约 55% 利润留存
    np_base = normalized_np(SCEN["base"])["np"]
    platform_np = 30.0                                 # 平台（基金销售+数据+母公司）正常化净利：2025 年 32.07、2026H1 年化 41.5，按保有中枢与降费取 30
    sec_np = np_base - platform_np
    sec_roe = sec_np / eq_sec_2026e
    pb_sec = (sec_roe - 0.025) / (r - 0.025)
    v_sec = eq_sec_2026e * pb_sec
    pe_platform = 15.0
    v_plat = platform_np * pe_platform
    v_cash = PARENT_NET_CASH
    v_end = v_sec + v_plat + v_cash
    return dict(eq_sec=eq_sec_2026e, sec_np=sec_np, sec_roe=sec_roe, pb_sec=pb_sec, v_sec=v_sec,
                v_plat=v_plat, v_cash=v_cash, ps=v_end / (1 + r) ** STUB / SHARES,
                ps_peer_pb=(eq_sec_2026e * 1.09 + v_plat + v_cash) / (1 + r) ** STUB / SHARES)


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def variant(chg):
    """chg: {(情景, 参数): 新值}，返回改动后的情景表副本。"""
    sc = {k: dict(v) for k, v in SCEN.items()}
    for (scn, key), val in chg.items():
        sc[scn][key] = val
    return sc


def main():
    print("== 校准（报告原文）==")
    for k, v in calibration().items():
        print(f"  {k}: {v:.4f}")
    print(f"  2026E 归母净利（报告口径估计）= {NP_2026E:.2f}；2026 年末归母权益 B0 = {B0:.2f}；市值 {MKT_CAP:.1f}")
    print(f"  母公司层面现金类净额（金融企业口径 net_cash_adj）= {PARENT_NET_CASH:.2f}")

    print("\n== 2026 年正常化归母净利（驱动因子）==")
    norm = {}
    for k, s in SCEN.items():
        n = normalized_np(s)
        norm[k] = n["np"]
        ln = "；".join(f"{a} {b:.1f}" for a, b in n["lines"].items())
        print(f"  {LABEL[k]}: 日均成交 {s['T']:.2f} 万亿 → 收入 {n['rev']:.1f}（{ln}）；"
              f"成本 {n['cost']:.1f}；税前 {n['pbt']:.1f}；归母净利 {n['np']:.1f}")
    wnp = sum(SCEN[k]["p"] * norm[k] for k in SCEN)
    print(f"  概率加权正常化归母净利 {wnp:.1f}")

    print("\n== 敏感度（基准，税后归母净利，亿元）==")
    s = SCEN["base"]
    k_after = (1 - s["v"]) * (1 - s["tax"])
    print(f"  A股日均成交额 +0.1 万亿（仅佣金直接效应）: {0.1 * TRADING_DAYS * s['y_b'] * k_after:+.2f}")
    print(f"  公司融出资金 +100 亿: {100 * s['a_m'] * k_after:+.2f}；全市场融资 +1,000 亿（份额 3.2%）: {32 * s['a_m'] * k_after:+.2f}")
    print(f"  客户资金 +100 亿: {100 * s['b_c'] * k_after:+.2f}")
    print(f"  天天基金非货保有 +1,000 亿: {1000 * s['f_rate'] * k_after:+.2f}；费率 −5bp: {-s['AUM'] * 0.0005 * k_after:+.2f}")
    print(f"  自营收益率 +10bp: {s['inv_book'] * 0.001 * k_after:+.2f}")
    print(f"  佣金收益率 −5%: {-0.05 * s['T'] * TRADING_DAYS * s['y_b'] * k_after:+.2f}")

    print("\n== 剩余收益估值（2026-10-21 每股）==")
    res = {}
    for k, sc in SCEN.items():
        d = ri_value(sc, detail=True)
        res[k] = d
        v8, v10 = ri_value(sc, r=0.08), ri_value(sc, r=0.10)
        print(f"  {LABEL[k]}(p={sc['p']:.2f}): V={d['ps']:.2f}（8%: {v8:.2f}；10%: {v10:.2f}）；"
              f"2027 ROE {d['roe1']:.2%}→终值 {d['roe_T']:.2%}；终值现值占 V {d['tv_share']:.1%}；DDM 复核 {ddm_check(sc):.2f}")
        for row in d["rows"]:
            print(f"     {row['year']}: 归母净利 {row['np']:.1f}（{row['g_np']:+.1%}）期初权益 {row['b_open']:.0f} "
                  f"ROE {row['roe']:.2%} 可分配 {row['div']:.1f}（派息率 {row['payout']:.0%}）RI {row['ri']:.1f}")
        print(f"     再投资率（2027-31 累计）{d['reinvest']:.0%}；增量回报 {d['inc_ret']:.1%}")
    vw = weighted()
    v8w, v10w = weighted(0.08), weighted(0.10)
    pv = PRICE / vw
    print(f"\n  加权 V = {vw:.2f}；P/V = {pv:.2f}（{tier(pv)}）；8%: {v8w:.2f}；10%: {v10w:.2f}")
    print(f"  分档价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}–{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}–{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")
    print(f"  按有回购专户股份剔除口径：无回购专户，V 相同")

    print("\n== 隐含回报与反向推算 ==")
    print(f"  基准情景隐含回报（IRR）= {implied_irr(SCEN['base']):.2%}")
    for k, v in reverse().items():
        print(f"  {k}: {v:.2%}" if "ROE" in k or "增长" in k else f"  {k}: {v:.2f}")
    for nm, roe in [("基准 2027 ROE", res["base"]["roe1"]), ("TTM ROE", 145.82 / B_H1), ("牛市 2027 ROE", res["bull"]["roe1"])]:
        g10 = implied_g10(roe)
        txt = "无解（增速再高也达不到现价）" if g10 is None else f"{g10:.1%}"
        print(f"  ROE 恒定 {roe:.1%} 时现价隐含 10 年增速：{txt}；g=10% 时 V = {value_const_roe(roe, 0.10):.2f}")
    print("  日均成交额敏感度（基准；只改成交额 → 联动两融/客户资金/保有）：")
    for T, n1, v1, n2, v2 in turnover_sensitivity():
        print(f"     {T:.2f} 万亿：正常化归母 {n1:.1f}、V {v1:.2f} → 联动 {n2:.1f}、V {v2:.2f}")
    base_d = res["base"]
    yld = base_d["rows"][0]["div"] / MKT_CAP
    print(f"  基准 2027 年可分配额 {base_d['rows'][0]['div']:.1f} 亿，对现市值收益率 {yld:.2%}；"
          f"现实股息率 0.56%（2025 年度每股 0.10 元）")

    print("\n== 交叉验证 ==")
    sp = sotp()
    print(f"  分部加总：证券权益 {sp['eq_sec']:.0f}、正常化净利 {sp['sec_np']:.1f}、ROE {sp['sec_roe']:.2%}、"
          f"合理PB {sp['pb_sec']:.2f} → {sp['v_sec']:.0f}；平台 30×15 = {sp['v_plat']:.0f}；母公司现金 {sp['v_cash']:.0f}"
          f" → 每股 {sp['ps']:.2f}；证券按行业 PB 1.09 → 每股 {sp['ps_peer_pb']:.2f}")
    for pe in (20, 27):
        print(f"  正常化净利 × 历史 PE {pe}x → 每股 {wnp * pe / SHARES:.2f}")
    print(f"  现价对应 PE(2026E 报告口径) {MKT_CAP / NP_2026E:.1f}x；PE(正常化加权) {MKT_CAP / wnp:.1f}x；"
          f"PB(2026-06-30) {MKT_CAP / B_H1:.2f}x")

    print("\n== 证伪条件触发后的 V ==")
    f1 = weighted(weights={"bear": 0.10, "base": 0.40, "bull": 0.50})
    f2 = weighted(weights={"bear": 0.50, "base": 0.40, "bull": 0.10})
    sc3 = variant({("base", "y_b"): 0.125, ("bull", "y_b"): 0.135, ("bear", "y_b"): 0.115})
    f3 = weighted(scen=sc3)
    sc4 = variant({("base", "f_rate"): 0.0040, ("base", "AUM"): 8500,
                   ("bull", "f_rate"): 0.0042, ("bear", "f_rate"): 0.0034})
    f4 = weighted(scen=sc4)
    low = ri_value(SCEN["base"], payout_override=0.13, r_inc=0.04)
    f5 = 0.25 * ri_value(SCEN["bear"]) + 0.5 * low + 0.25 * ri_value(SCEN["bull"])
    print(f"  F1 牛市权重升至 50%（2027 归母≥170 且 ROE≥15%）：V = {f1:.2f}")
    print(f"  F2 熊市权重升至 50%（2027 日均成交<1.3 万亿且归母<95）：V = {f2:.2f}")
    print(f"  F3 佣金收益率再降（2026 年代理买卖净收入/成交额 < 0.130）：V = {f3:.2f}")
    print(f"  F4 基金销售降费落地（2026 金融电子商务收入 < 38 亿）：V = {f4:.2f}")
    print(f"  F5 低派息留存（派息 13%、留存增量税后回报 4%）基准 V = {low:.2f} → 加权 V = {f5:.2f}")
    dtax = sum(SCEN[k]["p"] * tax_expiry_delta(SCEN[k]) for k in SCEN)
    print(f"  税率风险：2031 年起证券子公司按 25% 计税 → 加权 V 变化 {dtax:+.2f}（V = {vw + dtax:.2f}）")


if __name__ == "__main__":
    main()
