#!/usr/bin/env python3
"""亚钾国际（000893）独立估值（OI-291 b09，价格日 2026-10-20）。

方法：所有者收益 DCF。经调整净现金为负，按框架以有杠杆口径为主（经调整净负债按现规模滚动、
不偿还本金，扣除税后利息永续现值），无杠杆口径（全额扣除经调整净负债）作对照。
单位：金额亿元；销量万吨；价格元/吨（集团氯化钾实现均价，不含增值税）；每股元。
输入全部写在脚本内，`python3 valuation.py` 打印正文与 json 用到的全部数字。
"""
import copy

# ------------------------------------------------------------------ 快照（brief.md）
PRICE = 36.83                       # 2026-10-20 收盘
SHARES = 9.2405                     # 总股本（腾讯口径，含回购专户），亿股
TREASURY = 0.10544029               # 回购专户 10,544,029 股，未公告注销（dividend_20260528_919599 第 1 页）
MKT_CAP = PRICE * SHARES

# ------------------------------------------------------------------ 资产负债（2026-06-30，2026H1_report 第 53-55、146-149 页）
CASH = 21.06                        # 货币资金；附注：无质押、冻结或汇回受限款项（第 129 页）
DEBT_BANK = 0.3003 + 18.1367 + 4.5036          # 短期借款 + 长期借款 + 一年内到期长期借款（含应计利息）
DEBT_HUINENG = 17.8331 + 0.2799                # 汇能集团借款 17.82 亿（长期应付款）+ 一年内到期长期应付款（主要为应计利息 0.27）
DEBT_LEASE = 0.0243 + 0.0409
DEBT = DEBT_BANK + DEBT_HUINENG + DEBT_LEASE    # 41.12，数据包有息负债 23.29 未含长期应付款
OP_RESERVE = 3.0                    # 经营备付：约 1 个月付现成本与税费
PROVISION = 0.66                    # 预计负债（美国三井大豆仲裁，第 36-37 页）视同债务
NET_CASH_ADJ = CASH - OP_RESERVE - DEBT - PROVISION      # 无杠杆口径经调整净现金
NONOP = 0.52 + 0.40                 # 溴业以外的联营企业（长投 2.74 - 亚洲溴业 2.22）+ 投资性房地产
INT_RATE = 1.4725 / 41.33           # 2026H1 利息费用 0.736 亿年化 / 期初期末平均有息负债
INT_TAX = 0.25                      # 利息抵税税率（汇能借款在母公司）

# ------------------------------------------------------------------ 经营常数
YEARS = list(range(2027, 2036))     # 显性期 2027-2035（扩产需要爬坡；json 报 2027-2031）
T0 = 2026.80                        # 估值日 2026-10-20
OTHER_REV, OTHER_MARGIN = 2.0, 0.60 # 卤水等其他收入（2026H1 1.01 亿，毛利率约 65%）
DA_PER_T = 330.0                    # 折旧摊销元/吨（2026H1 4.86 亿 / 产量 149.5 万吨 ≈ 325）
WC_RATE = 0.08                      # 收入变动占用营运资本
RONIC = 0.15                        # 终值增长的增量回报；再投资率 = g / RONIC
NET_INT_2026 = 1.45                 # 2026 年化利息费用 1.47 - 利息收入 0.03
H1_2026 = dict(sales=131.25, rev=38.22, np=13.50, oe=13.45 + 4.86 - 8.60 - 1.06 + 0.87)  # H1 所有者收益（经营口径）

SCEN = {
    "bear": dict(
        p=0.25,
        h2=dict(vol=150, price=2680, cogs=860, ts=0.070, etr=0.23, sga=2.6, proj=5.0, wc=0.0, inv=0.4),
        vol=[(2027, 280), (2028, 290)],
        price=[(2027, 2250), (2028, 2050)],
        cogs=860, ts=[(2027, 0.078), (2028, 0.085), (2029, 0.095)],
        etr=[(2027, 0.24), (2028, 0.26), (2029, 0.30)],
        sga=5.3, maint=320, proj={2027: 9.0}, inv=0.5,
        exp_vol=[], exp_capex={}, g=0.005,
    ),
    "base": dict(
        p=0.50,
        h2=dict(vol=160, price=2720, cogs=840, ts=0.070, etr=0.23, sga=2.5, proj=4.0, wc=1.0, inv=0.5),
        vol=[(2027, 300), (2028, 315), (2029, 320)],
        price=[(2027, 2550), (2028, 2420), (2029, 2350)],
        cogs=820, ts=[(2027, 0.075), (2028, 0.078), (2029, 0.085)],
        etr=[(2027, 0.235), (2028, 0.245), (2029, 0.27)],
        sga=5.0, maint=290, proj={2027: 6.0}, inv=0.9,
        # 第四个 100 万吨：2028-2030 投 36 亿，2031 年产 50 万吨、2032 年起 100 万吨
        exp_vol=[(2031, 50), (2032, 100)], exp_capex={2028: 8.0, 2029: 14.0, 2030: 14.0}, g=0.015,
    ),
    "bull": dict(
        p=0.25,
        h2=dict(vol=165, price=2780, cogs=830, ts=0.070, etr=0.22, sga=2.4, proj=3.5, wc=1.5, inv=0.6),
        vol=[(2027, 320), (2028, 335), (2029, 340)],
        price=[(2027, 2800), (2028, 2700)],
        cogs=780, ts=[(2027, 0.072), (2029, 0.075)],
        etr=[(2027, 0.22), (2029, 0.24)],
        sga=4.7, maint=265, proj={2027: 4.5}, inv=1.4,
        # 第四、第五个 100 万吨：2027-2030 投 70 亿，2030 年起分批投产，2032 年合计 200 万吨
        exp_vol=[(2030, 50), (2031, 150), (2032, 200)], exp_capex={2027: 10.0, 2028: 20.0, 2029: 22.0, 2030: 18.0}, g=0.020,
    ),
}


def step(table, year, default=0.0):
    val = default
    for y, v in table:
        if year >= y:
            val = v
    return val


def year_pl(vol, price, cogs, ts, etr, sga, other_rev=OTHER_REV):
    kcl = vol * price / 1e4
    rev = kcl + other_rev
    ebitda = kcl - vol * cogs / 1e4 + other_rev * OTHER_MARGIN - ts * rev - sga
    da = vol * DA_PER_T / 1e4
    ebit = ebitda - da
    return dict(rev=rev, ebitda=ebitda, da=da, ebit=ebit, nopat=ebit * (1 - etr))


def flows(s):
    out = []
    h = s["h2"]
    r = year_pl(h["vol"], h["price"], h["cogs"], h["ts"], h["etr"], h["sga"], other_rev=1.0)
    oe = r["nopat"] + r["da"] - h["vol"] * s["maint"] / 1e4 - h["proj"] + h["wc"] + h["inv"]
    out.append(dict(year="2026H2", dt=0.0, vol=h["vol"], capex_g=h["proj"], oe=oe, **r))
    prev_rev = H1_2026["rev"] + r["rev"]
    for y in YEARS:
        vexp = step(s["exp_vol"], y)
        vol = step(s["vol"], y) + vexp
        price = step(s["price"], y)
        sga = s["sga"] + 0.4 * vexp / 100
        r = year_pl(vol, price, s["cogs"], step(s["ts"], y), step(s["etr"], y), sga)
        capex_g = s["proj"].get(y, 0.0) + s["exp_capex"].get(y, 0.0)
        dwc = WC_RATE * (r["rev"] - prev_rev)
        core = r["nopat"] + r["da"] - vol * s["maint"] / 1e4 + s["inv"]
        out.append(dict(year=y, dt=y + 0.5 - T0, vol=vol, price=price, capex_g=capex_g, dwc=dwc,
                        oe=core - capex_g - dwc, oe_pre_growth=core, **r))
        prev_rev = r["rev"]
    return out


def debt_charge(coe):
    """有杠杆口径：经调整净负债按现规模滚动，税后利息的永续现值。"""
    return -NET_CASH_ADJ * INT_RATE * (1 - INT_TAX) / coe


def value(s, coe=0.09, levered=True, detail=False):
    fl = flows(s)
    pv = sum(f["oe"] / (1 + coe) ** f["dt"] for f in fl)
    last, g = fl[-1], s["g"]
    term_oe = last["oe_pre_growth"] * (1 + g) - g / RONIC * last["nopat"] * (1 + g)
    pv_tv = term_oe / (coe - g) / (1 + coe) ** (YEARS[-1] + 1 - T0)
    ops = pv + pv_tv
    eq = ops - debt_charge(coe) + NONOP if levered else ops + NET_CASH_ADJ + NONOP
    if detail:
        return dict(fl=fl, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / ops, ops=ops, eq=eq, v=eq / SHARES)
    return eq / SHARES


def weighted(coe=0.09, levered=True, scen=None, probs=None):
    scen = scen or SCEN
    probs = probs or {n: scen[n]["p"] for n in scen}
    return sum(probs[n] * value(scen[n], coe, levered) for n in scen)


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if fm * flo <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def normalized_np_2026(s):
    """2026 年规模（全年销量）× 长期正常化价格与成本，2026 年税制，含净利息，剔除一次性。"""
    vol = H1_2026["sales"] + s["h2"]["vol"]
    price = s["price"][-1][1]
    r = year_pl(vol, price, s["cogs"], 0.070, s["h2"]["etr"], s["sga"])
    return (r["ebit"] - NET_INT_2026) * (1 - s["h2"]["etr"]) + s["inv"] - 0.03   # 少数股东约 0.03


def q3_fy2026_estimate():
    """基准：三季度销量 75 万吨、实现价 2750；四季度 85 万吨、2700（与 2026H2 基准一致）。"""
    res = {}
    for q, vol, price in (("Q3", 75, 2750), ("Q4", 85, 2700)):
        r = year_pl(vol, price, 840, 0.070, 0.23, 1.25, other_rev=0.5)
        np_ = (r["ebit"] - NET_INT_2026 / 4) * (1 - 0.23) + 0.25
        res[q] = (r["rev"], np_)
    return res


def variant(**changes):
    sc = copy.deepcopy(SCEN)
    for n, ch in changes.items():
        for k, v in ch.items():
            sc[n][k] = v
    return sc


def main():
    print(f"市值 {MKT_CAP:.2f} 亿；有息负债 {DEBT:.2f}（银行 {DEBT_BANK:.2f}、汇能 {DEBT_HUINENG:.2f}、租赁 {DEBT_LEASE:.2f}）")
    print(f"经调整净现金（无杠杆口径）{NET_CASH_ADJ:.2f} 亿 = 现金 {CASH} - 备付 {OP_RESERVE} - 有息负债 {DEBT:.2f} - 预计负债 {PROVISION}")
    print(f"非经营资产 {NONOP:.2f}；有息负债平均利率 {INT_RATE:.4f}；净负债税后利息永续现值 @8/9/10%："
          f"{debt_charge(0.08):.2f} / {debt_charge(0.09):.2f} / {debt_charge(0.10):.2f}")
    print()
    for n, s in SCEN.items():
        d = value(s, 0.09, True, detail=True)
        print(f"[{n}] p={s['p']:.2f}  V(有杠杆)={d['v']:.2f}  V(无杠杆)={value(s, 0.09, False):.2f}  "
              f"剔除回购股 V={d['eq']/(SHARES-TREASURY):.2f}  终值占比 {d['tv_share']:.1%}  "
              f"经营现值 {d['ops']:.1f}（显性 {d['pv_explicit']:.1f} + 终值 {d['pv_tv']:.1f}）  @8% {value(s,0.08):.2f}  @10% {value(s,0.10):.2f}")
        for f in d["fl"]:
            if f["year"] == "2026H2" or f["year"] <= 2032:
                print(f"    {f['year']}: 销量 {f['vol']:.0f}  收入 {f['rev']:.2f}  EBITDA {f['ebitda']:.2f}  NOPAT {f['nopat']:.2f}  "
                      f"项目+扩产资本开支 {f['capex_g']:.1f}  所有者收益 {f['oe']:.2f}")
    vw = weighted()
    vu = weighted(levered=False)
    vx = vw * SHARES / (SHARES - TREASURY)
    print()
    print(f"加权 V（有杠杆，9%）= {vw:.2f}；P/V = {PRICE/vw:.3f}")
    print(f"加权 V（无杠杆，9%）= {vu:.2f}；P/V = {PRICE/vu:.3f}")
    print(f"剔除回购专户股份：加权 V = {vx:.2f}；P/V = {PRICE/vx:.3f}")
    print(f"加权 V @8% = {weighted(0.08):.2f}；@10% = {weighted(0.10):.2f}")
    alt = weighted(probs={"bear": 0.30, "base": 0.50, "bull": 0.20})
    print(f"概率改为 30/50/20 的加权 V = {alt:.2f}；P/V = {PRICE/alt:.3f}")
    irr = solve(lambda k: value(SCEN['base'], k) * SHARES, 0.03, 0.30, MKT_CAP)
    irr_u = solve(lambda k: value(SCEN['base'], k, False) * SHARES, 0.03, 0.30, MKT_CAP)
    print(f"现价隐含回报（基准情景，有杠杆）= {irr:.4f}；无杠杆 = {irr_u:.4f}")

    # 反向 DCF：以基准 2029 年稳态核心所有者收益（扣维护、不含扩产）为起点
    need = MKT_CAP + debt_charge(0.09) - NONOP
    base_fl = flows(SCEN["base"])
    oe0 = [f for f in base_fl if f["year"] == 2029][0]["oe_pre_growth"]
    g_perp = 0.09 - oe0 / need
    def pv10(g):
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= (1 + g)
            pv += oe / 1.09 ** t
        return pv + oe * 1.015 / (0.09 - 0.015) / 1.09 ** 10
    g10 = solve(pv10, -0.10, 0.20, need)
    print(f"反向 DCF：市值对应经营所有者收益现值 {need:.1f} 亿；基准稳态核心所有者收益 {oe0:.2f} 亿 → 隐含永续增速 {g_perp:.4f}；"
          f"10 年增速（其后 1.5%）{g10:.4f}")
    # 换一种表述：保持基准其他假设，现价隐含的长期实现价（2029 年起）
    def v_at_lr_price(p):
        sc = variant(base=dict(price=[(2027, 2550), (2028, 2420), (2029, p)]))
        return value(sc["base"])
    p_imp = solve(v_at_lr_price, 1500, 4000, PRICE)
    print(f"现价隐含基准长期实现价 {p_imp:.0f} 元/吨（基准 2350，高 {p_imp/2350-1:.1%}，约合 CFR {p_imp/7.10/0.98:.0f} 美元/吨）")

    nn = {n: normalized_np_2026(s) for n, s in SCEN.items()}
    print("2026 正常化归母净利：" + "  ".join(f"{n} {v:.2f}" for n, v in nn.items()))

    # 增长路径（基准）
    oes = {f["year"]: f["oe"] for f in base_fl}
    oe2026 = H1_2026["oe"] + oes["2026H2"]
    prev = oe2026
    grow = []
    for y in range(2027, 2032):
        grow.append(oes[y] / prev - 1)
        prev = oes[y]
    print(f"基准所有者收益：2026 {oe2026:.2f}（H1 实际 {H1_2026['oe']:.2f} + H2 估计 {oes['2026H2']:.2f}）  " +
          "  ".join(f"{y} {oes[y]:.2f}" for y in range(2027, 2033)))
    print("基准所有者收益增速 2027-2031：" + "  ".join(f"{g:+.3f}" for g in grow))
    core = {f["year"]: f.get("oe_pre_growth") for f in base_fl}
    print("基准核心所有者收益（扣维护、不扣扩产）：" + "  ".join(f"{y} {core[y]:.2f}" for y in range(2027, 2033)))
    capex_exp = sum(SCEN["base"]["exp_capex"].values())
    no_exp = variant(base=dict(exp_vol=[], exp_capex={}))
    fl_ne = {f["year"]: f for f in flows(no_exp["base"])}
    inc_oe = core[2033] - fl_ne[2033]["oe_pre_growth"]
    nopat_27_31 = sum(f["nopat"] for f in base_fl if f["year"] != "2026H2" and 2027 <= f["year"] <= 2031)
    capex_27_31 = sum(f["capex_g"] for f in base_fl if f["year"] != "2026H2" and 2027 <= f["year"] <= 2031)
    print(f"基准扩产：资本开支 {capex_exp:.0f} 亿，满产增量所有者收益 {inc_oe:.2f} 亿/年 → 增量回报 {inc_oe/capex_exp:.3f}；"
          f"2027-2031 再投资率（项目+扩产资本开支/NOPAT）{capex_27_31/nopat_27_31:.3f}")
    v_ne = value(no_exp["base"])
    print(f"基准不含第四个百万吨：V = {v_ne:.2f}（扩产贡献 {value(SCEN['base'])-v_ne:.2f} 元/股）")

    # 交叉验证
    ev = MKT_CAP - NET_CASH_ADJ - NONOP
    ss = [f for f in base_fl if f["year"] == 2029][0]
    np_ss = (ss["ebit"] - NET_INT_2026) * (1 - 0.27) + SCEN["base"]["inv"]
    print(f"EV = {ev:.1f} 亿；基准 2029 稳态 EBIT {ss['ebit']:.2f} → EV/EBIT {ev/ss['ebit']:.1f}；稳态归母净利 {np_ss:.2f} → PE {MKT_CAP/np_ss:.1f}")
    print(f"PE(2026 正常化基准) = {MKT_CAP/nn['base']:.1f}；股息率 {0.11/PRICE:.4f}")
    est = q3_fy2026_estimate()
    fy = H1_2026["np"] + est["Q3"][1] + est["Q4"][1]
    print(f"2026Q3 估计：收入 {est['Q3'][0]:.2f}，归母净利 {est['Q3'][1]:.2f}；Q4 估计 {est['Q4'][1]:.2f}；2026 全年报告口径 ≈ {fy:.1f}")

    # 证伪条件触发后的独立 V
    f1 = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f2 = weighted(scen=variant(
        base=dict(vol=[(2027, 280), (2028, 295), (2029, 300)], exp_vol=[(2032, 50), (2033, 100)],
                  exp_capex={2029: 8.0, 2030: 14.0, 2031: 14.0}),
        bull=dict(vol=[(2027, 300), (2028, 315), (2029, 320)], exp_vol=[(2031, 50), (2032, 150), (2033, 200)],
                  exp_capex={2028: 10.0, 2029: 20.0, 2030: 22.0, 2031: 18.0})))
    f3 = weighted(scen=variant(
        bear=dict(ts=[(2027, 0.078), (2028, 0.085), (2029, 0.097)], etr=[(2027, 0.24), (2028, 0.26), (2029, 0.31)]),
        base=dict(ts=[(2027, 0.075), (2028, 0.080), (2029, 0.097)], etr=[(2027, 0.235), (2028, 0.25), (2029, 0.30)]),
        bull=dict(ts=[(2027, 0.072), (2028, 0.075), (2029, 0.090)], etr=[(2027, 0.22), (2028, 0.24), (2029, 0.28)])))
    # F3b：在 F3 之上，新《矿产法》把资源税率由 5% 提到 7%（约占集团收入 +1.5 个百分点），2028 年起
    f3b = weighted(scen=variant(
        bear=dict(ts=[(2027, 0.078), (2028, 0.100), (2029, 0.112)], etr=[(2027, 0.24), (2028, 0.26), (2029, 0.31)]),
        base=dict(ts=[(2027, 0.075), (2028, 0.095), (2029, 0.112)], etr=[(2027, 0.235), (2028, 0.25), (2029, 0.30)]),
        bull=dict(ts=[(2027, 0.072), (2028, 0.090), (2029, 0.105)], etr=[(2027, 0.22), (2028, 0.24), (2029, 0.28)])))
    # F4：2027 年底前未获第四、第五个百万吨批复：基准不扩产，牛市只扩一个（推迟一年）
    f4 = weighted(scen=variant(base=dict(exp_vol=[], exp_capex={}),
                               bull=dict(exp_vol=[(2031, 50), (2032, 100)], exp_capex={2028: 8.0, 2029: 14.0, 2030: 14.0})))
    # F5：资本配置失误：基准 36 亿投出却无钾肥增量（如转投非钾业务零回报），牛市只成一个
    f5 = weighted(scen=variant(base=dict(exp_vol=[], exp_capex={2028: 8.0, 2029: 14.0, 2030: 14.0}),
                               bull=dict(exp_vol=[(2030, 50), (2031, 100)])))
    print(f"证伪 F1 价格（权重改为 50/40/10）V = {f1:.2f}")
    print(f"证伪 F2 产量（核心产量 -20 万吨、扩产推迟一年）V = {f2:.2f}")
    print(f"证伪 F3 老挝优惠到期不续（2029 起出口关税全部 7%、利润税 35%）V = {f3:.2f}；叠加资源税 5%→7% V = {f3b:.2f}")
    print(f"证伪 F4 2027 年底前未获第四/第五个百万吨批复 V = {f4:.2f}")
    print(f"证伪 F5 资本配置失误（36 亿投出无钾肥增量）V = {f5:.2f}")
    print(f"V 不变时各档价格：≤0.75 明显低估 {0.75*vw:.2f}；0.90 {0.90*vw:.2f}；1.10 {1.10*vw:.2f}")
    # 正文用：长期价格折合东南亚标准氯化钾 CFR（汇率 7.10、实现价/CFR 约 0.98）
    for n, s in SCEN.items():
        lp = s["price"][-1][1]
        print(f"    {n} 长期实现价 {lp} 元/吨 ≈ CFR {lp/7.10/0.98:.0f} 美元/吨")
    pw = sum(SCEN[n]["p"] * SCEN[n]["price"][-1][1] for n in SCEN)
    print(f"    概率加权长期实现价 {pw:.0f} 元/吨 ≈ CFR {pw/7.10/0.98:.0f} 美元/吨")
    print(f"    基准 2029 稳态：收入 {ss['rev']:.2f}、EBITDA {ss['ebitda']:.2f}（{ss['ebitda']/ss['rev']:.1%}）、"
          f"EBIT {ss['ebit']:.2f}（{ss['ebit']/ss['rev']:.1%}）、NOPAT {ss['nopat']:.2f}、核心所有者收益 {ss['oe_pre_growth']:.2f}")


if __name__ == "__main__":
    main()
