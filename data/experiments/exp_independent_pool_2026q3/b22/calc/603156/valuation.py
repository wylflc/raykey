#!/usr/bin/env python3
"""养元饮品（603156）独立估值：OI-291 b22，价格日 2026-10-21。

口径：
- 金额单位亿元，每股元；股本 12.6028 亿股（腾讯行情口径，无回购专户股份）。
- 主业（核桃乳 + 代理天丝红牛）按所有者收益 DCF 估值，不含理财收益、公允价值变动、
  联营损益与一次性税项；投资资产（经调整净现金、长江存储股权、泉泓投资其他项目、
  中冀投资等）按非经营资产单独计价，不重复计入盈利。
- 经调整净现金为正（无杠杆口径），有息负债全额扣除。
- 长江存储（长存控股）股权按「上市后变现时的股权价值 × 持股比例 − 增值税负，再折现」计价。
输入全部写在脚本内，出处见 b22/companies/603156_养元饮品.md 的「来源」一节。
运行：python3 valuation.py
"""

PRICE = 38.88          # 2026-10-21 收盘，元
SHARES = 12.6028       # 亿股，无回购专户股份
COE = 0.09
TAX = 0.255            # 主业有效税率：25% 法定（高新资质已放弃，2026H1 报告第 83 页）+ 不可抵扣项
VAL_DATE_TO_YE2026 = 0.19   # 2026-10-21 至 2026-12-31，年
H2_SHARE = 0.42        # 2026 下半年占全年所有者收益的比例（上半年含春节旺季）
WC_FACTOR = 0.25       # 收入每变动 1 亿元，负营运资本（预收、应付票据）带来的现金变动

# ---------- 2026-06-30 资产负债表（2026H1 报告第 33-35、83、98、112-113 页）----------
CASH = 19.6465 - 0.0005          # 货币资金，扣受限保证金 0.0005
TFA = 40.3899                    # 交易性金融资产：理财 21.80、基金 15.38、其他 3.21、股票 0.0015
CUR_MATURING = 4.1952            # 一年内到期非流动资产：定期存单 1.1687 + 其他非流动金融资产 3.0265
ST_LOANS = 10.10                 # 短期借款（信用借款）
DIV_DECLARED = 6.3014            # 2026 年中期每股 0.50 元，8-21 宣派、9-23 除息
OPS_RESERVE = 3.0                # 经营备付（约 3 周现金成本）
RISK_HAIRCUT = 1.3               # R4/R5 私募与券商产品约 10.75 亿 ×10% + R2 私募约 10.7 亿 ×2%
DTL_FV = 0.638                   # 理财公允价值变动形成的递延所得税负债

NET_CASH_ADJ = (CASH + TFA + CUR_MATURING - ST_LOANS - DIV_DECLARED
                - OPS_RESERVE - RISK_HAIRCUT - DTL_FV)

# ---------- 其他非经营资产（2026H1 报告第 14-15、101-103 页）：账面值, 成本 ----------
OTHER_ASSETS = {
    # 名称: (账面值, 成本, 类别)
    "瑞浦兰钧（港股，期末收盘价）": (6.6717, 8.00, "listed"),
    "新潮传媒（分众收购预估值 83 亿）": (1.5992, 2.20, "xinchao"),
    "泉泓其他未上市项目（清微、衡川、极芯等 9 项，按成本）": (9.0444, 9.0534, "unlisted"),
    "中冀投资 32.53%（权益法，关联方）": (6.5401, 7.50, "zhongji"),
    "中冀减资款及利息（原值 2.4902，已计提 0.9217）": (1.5685, 1.5685, "zhongji_recv"),
    "联兴供热（权益法）": (0.4295, 0.4472, "lianxing"),
    "元潮创业（权益法）": (0.0811, 0.0500, "yuanchao"),
}

# ---------- 长江存储（长存控股）----------
YMTC_COST = 16.0
YMTC_STAKE_PRE = 0.009808        # 0.99373%（增资公告）× 后续摊薄 0.98698（长晟 26.89%→26.54%）
YMTC_SHARES_PRE = 178.2          # 亿股：拟发 19.8～24.3 亿股 = 发行后 10%～12%，两端反推一致
YMTC_NEW_SHARES = 22.05          # 取发行区间中值
YMTC_STAKE_POST = YMTC_STAKE_PRE * YMTC_SHARES_PRE / (YMTC_SHARES_PRE + YMTC_NEW_SHARES)

SCEN = {
    "bear": dict(
        p=0.25,
        walnut=46.0, walnut_g=[-0.07] * 5, walnut_gm=0.455, gm_drift=-0.003,
        rb=11.0, rb_g=[-0.20, -0.30, -0.30, -0.10, -0.10], rb_gm=0.150,
        sell_ratio=0.130, sell_drift=0.003, admin=1.10, rd=0.38, fixed_g=0.0,
        other_income=0.15, nonop=-0.05, net_interest=0.05,
        da=1.05, capex=0.50, g_term=-0.03,
        ymtc_post_value=6000.0, ymtc_t=2.5,
        mult=dict(listed=0.80, xinchao=0.60, unlisted=0.60, zhongji=0.25,
                  zhongji_recv=0.20, lianxing=0.60, yuanchao=1.00),
        text="核桃乳季节中性收入 46 亿、毛利率 45.5%，此后每年 −7%（2016-2025 年均降幅）；"
             "天丝红牛合作收缩（2027-2031 年 −20%/−30%/−30%/−10%/−10%）；终值增长 −3%；"
             "长存控股上市延后或景气回落，变现时股权价值 6000 亿元、2.5 年后变现；中冀按账面 25%。",
    ),
    "base": dict(
        p=0.50,
        walnut=49.5, walnut_g=[-0.03] * 5, walnut_gm=0.470, gm_drift=0.0,
        rb=15.0, rb_g=[0.05, 0.0, -0.03, -0.03, -0.03], rb_gm=0.168,
        sell_ratio=0.122, sell_drift=0.0, admin=1.00, rd=0.38, fixed_g=-0.01,
        other_income=0.35, nonop=-0.03, net_interest=0.10,
        da=1.05, capex=0.55, g_term=-0.01,
        ymtc_post_value=12000.0, ymtc_t=2.0,
        mult=dict(listed=0.95, xinchao=0.90, unlisted=1.00, zhongji=0.50,
                  zhongji_recv=0.60, lianxing=0.80, yuanchao=1.00),
        text="核桃乳季节中性收入 49.5 亿（TTM 50.4 亿）、毛利率 47.0%，每年 −3%；"
             "红牛 15 亿、毛利率 16.8%，2027 年 +5% 后逐步 −3%；税率 25.5%；终值增长 −1%；"
             "长存控股上市后 2 年变现，股权价值 1.2 万亿元；中冀按账面 50%。",
    ),
    "bull": dict(
        p=0.25,
        walnut=51.5, walnut_g=[-0.005] * 5, walnut_gm=0.478, gm_drift=0.0,
        rb=17.0, rb_g=[0.08, 0.08, 0.02, 0.02, 0.02], rb_gm=0.175,
        sell_ratio=0.118, sell_drift=0.0, admin=0.95, rd=0.38, fixed_g=0.0,
        other_income=0.55, nonop=-0.02, net_interest=0.15,
        da=1.05, capex=0.60, g_term=0.01,
        ymtc_post_value=25000.0, ymtc_t=1.75,
        mult=dict(listed=1.10, xinchao=1.00, unlisted=1.60, zhongji=0.75,
                  zhongji_recv=1.00, lianxing=1.00, yuanchao=1.00),
        text="核桃乳企稳（51.5 亿、每年 −0.5%）；红牛 17 亿、毛利率 17.5% 且继续增长；终值增长 +1%；"
             "长存控股按长鑫式估值变现，1.75 年后股权价值 2.5 万亿元；未上市项目按成本 1.6 倍。",
    ),
}

YEARS = [2026, 2027, 2028, 2029, 2030, 2031]


def core_path(s):
    """返回 2026N 至 2031 年主业逐年数据。"""
    out = []
    walnut, rb = s["walnut"], s["rb"]
    gm, sell = s["walnut_gm"], s["sell_ratio"]
    admin, rd, oth = s["admin"], s["rd"], s["other_income"]
    da = s["da"]
    prev_rev = None
    for i, y in enumerate(YEARS):
        if i > 0:
            walnut *= 1 + s["walnut_g"][i - 1]
            rb *= 1 + s["rb_g"][i - 1]
            gm += s["gm_drift"]
            sell += s["sell_drift"]
            admin *= 1 + s["fixed_g"]
            rd *= 1 + s["fixed_g"]
            oth = max(oth - 0.01, 0.0)
            da = max(da - 0.05, s["capex"])
        other_rev = 0.10
        rev = walnut + rb + other_rev
        gp = walnut * gm + rb * s["rb_gm"] + other_rev * 0.60
        surcharge = 0.0075 * rev
        selling = sell * walnut + 0.025 * rb
        ebit = gp - surcharge - selling - admin - rd
        pretax = ebit + oth + s["nonop"]
        nopat = pretax * (1 - TAX)
        np_norm = (pretax + s["net_interest"]) * (1 - TAX)   # 登记口径：含财务费用行净利息
        wc_cf = 0.0 if prev_rev is None else WC_FACTOR * (rev - prev_rev)
        oe = nopat + da - s["capex"] + wc_cf
        out.append(dict(year=y, walnut=walnut, rb=rb, rev=rev, gp=gp, ebit=ebit,
                        pretax=pretax, nopat=nopat, np_norm=np_norm, oe=oe, da=da,
                        capex=s["capex"], wc_cf=wc_cf))
        prev_rev = rev
    return out


def core_value(s, r, path=None):
    path = path or core_path(s)
    pv = H2_SHARE * path[0]["oe"] / (1 + r) ** VAL_DATE_TO_YE2026
    for k, row in enumerate(path[1:], start=1):
        t = VAL_DATE_TO_YE2026 + k - 0.5
        pv += row["oe"] / (1 + r) ** t
    last = path[-1]
    g = s["g_term"]
    oe_term = last["nopat"] * (1 + g) + WC_FACTOR * g * last["rev"]   # 终值期折旧 = 资本开支
    tv = oe_term / (r - g)
    pv_tv = tv / (1 + r) ** (VAL_DATE_TO_YE2026 + 5)
    return pv + pv_tv, pv_tv


def after_tax(value, cost):
    return value - 0.25 * max(0.0, value - cost)


def ymtc_value(s, r):
    gross = s["ymtc_post_value"] * YMTC_STAKE_POST
    net = after_tax(gross, YMTC_COST)
    return net / (1 + r) ** s["ymtc_t"], gross, net


def other_assets_value(s):
    total = 0.0
    for name, (book, cost, cat) in OTHER_ASSETS.items():
        total += after_tax(book * s["mult"][cat], cost)
    return total


def value_per_share(s, r=COE):
    core, pv_tv = core_value(s, r)
    ymtc, _, _ = ymtc_value(s, r)
    oth = other_assets_value(s)
    equity = core + NET_CASH_ADJ + oth + ymtc
    return equity / SHARES, dict(core=core, pv_tv=pv_tv, net_cash=NET_CASH_ADJ,
                                 other=oth, ymtc=ymtc, equity=equity)


def weighted(r=COE):
    return sum(SCEN[k]["p"] * value_per_share(SCEN[k], r)[0] for k in SCEN)


def solve(f, lo, hi, target, n=200):
    """二分求解 f(x) = target（f 单调）。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 养元饮品 603156 独立估值（价格日 2026-10-21，现价 %.2f 元，股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("经调整净现金（无杠杆口径）%.2f 亿元 = 货币资金 %.2f + 交易性金融资产 %.2f + 一年内到期 %.2f"
          " − 短期借款 %.2f − 已宣派股利 %.2f − 经营备付 %.1f − 风险折价 %.1f − 递延税负债 %.2f"
          % (NET_CASH_ADJ, CASH, TFA, CUR_MATURING, ST_LOANS, DIV_DECLARED, OPS_RESERVE,
             RISK_HAIRCUT, DTL_FV))
    print("长存控股持股：发行前 %.4f%%，发行后约 %.4f%%（发行前 %.1f 亿股 + 新发 %.2f 亿股）"
          % (YMTC_STAKE_PRE * 100, YMTC_STAKE_POST * 100, YMTC_SHARES_PRE, YMTC_NEW_SHARES))
    print()
    res = {}
    for k, s in SCEN.items():
        path = core_path(s)
        v, d = value_per_share(s)
        res[k] = (v, d, path)
        _, gross, net = ymtc_value(s, COE)
        print("[%s] p=%.2f  V = %.2f 元/股" % (k, s["p"], v))
        print("   假设：" + s["text"])
        print("   主业 %.1f 亿（终值现值 %.1f，占主业 %.0f%%）| 净现金 %.1f | 其他投资 %.1f | 长存股权 %.1f"
              "（变现时 %.0f 亿元×%.3f%% = %.1f，税后 %.1f，折现 %.1f 年）| 股权合计 %.1f 亿"
              % (d["core"], d["pv_tv"], 100 * d["pv_tv"] / d["core"], d["net_cash"], d["other"],
                 d["ymtc"], s["ymtc_post_value"], YMTC_STAKE_POST * 100, gross, net, s["ymtc_t"],
                 d["equity"]))
        print("   每股：主业 %.2f | 净现金 %.2f | 其他投资 %.2f | 长存 %.2f"
              % (d["core"] / SHARES, d["net_cash"] / SHARES, d["other"] / SHARES, d["ymtc"] / SHARES))
        print("   年份  核桃乳  红牛   收入   主业EBIT 税后经营利润 正常化归母 所有者收益")
        for row in path:
            print("   %d %6.2f %6.2f %6.2f %7.2f %8.2f %9.2f %9.2f"
                  % (row["year"], row["walnut"], row["rb"], row["rev"], row["ebit"],
                     row["nopat"], row["np_norm"], row["oe"]))
        g_oe = [path[i]["oe"] / path[i - 1]["oe"] - 1 for i in range(1, len(path))]
        print("   所有者收益增速 2027-2031：" + "、".join("%.1f%%" % (100 * g) for g in g_oe)
              + "；终值增长 %.1f%%" % (100 * s["g_term"]))
        print()

    vw = weighted()
    pv = PRICE / vw
    print("概率加权 V = %.2f 元/股；P/V = %.3f → %s" % (vw, pv, band(pv)))
    print("（无回购专户股份，剔除口径与上同）")
    v8, v10 = weighted(0.08), weighted(0.10)
    print("股权成本敏感性：8%% → V = %.2f（P/V %.2f）；10%% → V = %.2f（P/V %.2f）"
          % (v8, PRICE / v8, v10, PRICE / v10))
    for k in SCEN:
        print("   %s：8%% %.2f / 9%% %.2f / 10%% %.2f"
              % (k, value_per_share(SCEN[k], 0.08)[0], value_per_share(SCEN[k], 0.09)[0],
                 value_per_share(SCEN[k], 0.10)[0]))
    print("V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    # 正常化归母净利 2026（登记口径）
    print("2026 正常化归母净利（含财务费用行净利息，不含理财、公允价值、联营与一次性税项）："
          "熊 %.2f / 基准 %.2f / 牛 %.2f 亿元"
          % tuple(res[k][2][0]["np_norm"] for k in ("bear", "base", "bull")))

    # 现价隐含回报：基准情景（主业所有者收益流 + 终值 + 净现金 + 其他投资 + 长存变现）
    base = SCEN["base"]
    # 折现率须高于各情景终值增长（牛市 +1%），下限取 1.5%
    irr = solve(lambda r: value_per_share(base, r)[0], 0.015, 0.5, PRICE)
    print("现价隐含回报（基准情景现金流）= %.2f%%" % (100 * irr))
    irr_w = solve(lambda r: weighted(r), 0.015, 0.5, PRICE)
    print("现价隐含回报（三情景概率加权）= %.2f%%" % (100 * irr_w))

    # 反向 DCF：扣除基准情景非经营资产后，现价隐含的主业价值
    vb, db, pb = res["base"]
    nonop_ps = (db["net_cash"] + db["other"] + db["ymtc"]) / SHARES
    implied_core = (PRICE - nonop_ps) * SHARES
    oe26h2 = H2_SHARE * pb[0]["oe"] / (1 + COE) ** VAL_DATE_TO_YE2026
    oe27 = pb[1]["oe"]

    def core_perp(g):   # 2027 年起所有者收益按 g 永续增长（年中折现）
        return oe26h2 + oe27 * (1 + COE) ** (1 - VAL_DATE_TO_YE2026 - 0.5) / (COE - g)

    g_perp = solve(core_perp, -0.5, COE - 1e-4, implied_core)

    def core_10y(g):
        pv = oe26h2
        oe = oe27
        for k in range(10):
            t = VAL_DATE_TO_YE2026 + k + 0.5
            pv += oe / (1 + COE) ** t
            oe_last = oe
            oe *= 1 + g
        tv = oe_last * 1.025 / (COE - 0.025)
        return pv + tv / (1 + COE) ** (VAL_DATE_TO_YE2026 + 10)

    g10 = solve(core_10y, -0.5, 0.5, implied_core)
    print("反向 DCF：扣除基准非经营资产 %.2f 元/股后，现价隐含主业价值 %.1f 亿元（%.1f 倍 2027 所有者收益），"
          "对应 10 年所有者收益增速 %.1f%%（其后 2.5%%），或永续增速约 %.1f%%"
          % (nonop_ps, implied_core, implied_core / oe27, 100 * g10, 100 * g_perp))
    # 现价隐含的长存估值：主业、净现金、其他投资按基准，长存为未知数
    rest = (db["core"] + db["net_cash"] + db["other"]) / SHARES
    need_net_pv = (PRICE - rest) * SHARES
    need_net = need_net_pv * (1 + COE) ** base["ymtc_t"]
    gross_needed = (need_net - 0.25 * YMTC_COST) / 0.75
    print("现价隐含长存估值：主业等按基准时，需长存股权税后现值 %.1f 亿元，即 %.0f 年后变现时长存控股"
          "股权价值约 %.2f 万亿元" % (need_net_pv, base["ymtc_t"], gross_needed / YMTC_STAKE_POST / 1e4))

    # 交叉验证
    ttm_np, ttm_dnp, bvps = 13.70, 13.61, 87.77 / SHARES
    print("交叉验证：PE(TTM) %.1f；PB %.2f；TTM 股息率 %.2f%%；"
          % (PRICE * SHARES / ttm_np, PRICE / bvps, 100 * 1.50 / PRICE))
    ev_base = PRICE * SHARES - db["net_cash"] - db["other"] - db["ymtc"]
    print("   基准非经营资产下 EV/主业 EBIT(2026N) = %.1f 倍；主业价值/EBIT = %.1f 倍"
          % (ev_base / pb[0]["ebit"], db["core"] / pb[0]["ebit"]))
    ex_ymtc = (db["core"] + db["net_cash"] + db["other"]) / SHARES
    print("   不含长存股权的基准每股价值 %.2f 元；长存股权占基准 V 的 %.0f%%"
          % (ex_ymtc, 100 * db["ymtc"] / db["equity"]))

    # 增长路径与再投资（基准）
    g_oe = [pb[i]["oe"] / pb[i - 1]["oe"] - 1 for i in range(1, len(pb))]
    reinv = [(r_["capex"] - r_["da"] - r_["wc_cf"]) / r_["nopat"] for r_ in pb[1:]]
    print("基准所有者收益增速 2027-2031：" + ", ".join("%.4f" % g for g in g_oe)
          + "；再投资率（资本开支−折旧+营运资本占用）/税后经营利润 平均 %.3f" % (sum(reinv) / len(reinv)))
    print("杠杆口径判断：经调整净现金 %.2f 亿元 > 0，按无杠杆口径全额扣除有息负债" % NET_CASH_ADJ)
    vw_ex = sum(SCEN[k]["p"] * (value_per_share(SCEN[k])[1]["equity"]
                                - value_per_share(SCEN[k])[1]["ymtc"]) for k in SCEN) / SHARES
    print("概率加权不含长存的每股价值 %.2f 元；概率加权长存股权 %.2f 元/股" % (vw_ex, vw - vw_ex))
    print("长存敏感度：变现时长存控股股权价值每变动 1 万亿元，基准 V 变动 %.2f 元/股"
          % ((after_tax(2e4 * YMTC_STAKE_POST, YMTC_COST) - after_tax(1e4 * YMTC_STAKE_POST, YMTC_COST))
             / (1 + COE) ** base["ymtc_t"] / SHARES))
    rest0 = (db["core"] + db["net_cash"] + db["other"]) / SHARES
    gross_now = ((PRICE - rest0) * SHARES - 0.25 * YMTC_COST) / 0.75
    print("若即时变现、不折现：现价隐含长存控股股权价值 %.2f 万亿元" % (gross_now / YMTC_STAKE_POST / 1e4))

    # 非经营资产（基准与概率加权）
    nonop_b = db["other"] + db["ymtc"]
    nonop_w = sum(SCEN[k]["p"] * (value_per_share(SCEN[k])[1]["other"]
                                  + value_per_share(SCEN[k])[1]["ymtc"]) for k in SCEN)
    print("非经营资产（不含净现金）：基准 %.2f 亿元（其他投资 %.2f + 长存 %.2f）；概率加权 %.2f 亿元"
          % (nonop_b, db["other"], db["ymtc"], nonop_w))

    # 证伪条件触发后的 V（其余按基准）
    print("证伪条件触发后的 V：")
    def v_with(**kw):
        s = dict(SCEN["base"])
        s.update(kw)
        return value_per_share(s)[0]
    print("   F1 长存控股 2027-06-30 前未获注册或终止审核（6000 亿、3 年变现）：%.2f"
          % v_with(ymtc_post_value=6000.0, ymtc_t=3.0))
    print("   F2 长存上市后 60 个交易日平均市值 ≥ 4 万亿元（按 4 万亿、1.5 年变现折算）：%.2f"
          % v_with(ymtc_post_value=40000.0, ymtc_t=1.5))
    print("   F3 2026 年核桃乳收入 < 46 亿或 2027H1 < 24 亿（主业按熊市、长存按基准）：%.2f"
          % v_with(walnut=46.0, walnut_g=[-0.07] * 5, walnut_gm=0.455, gm_drift=-0.003,
                   sell_ratio=0.130, sell_drift=0.003, g_term=-0.03))
    print("   F4 天丝终止或大幅收缩养元经销（2027H1 功能饮料收入 < 4 亿）：%.2f"
          % v_with(rb=11.0, rb_g=[-0.40, -0.50, -0.50, -0.20, -0.20]))
    print("   F5 中冀减资款 2027-04-30 前仍未回收且再计提（中冀股权与债权按 0）：%.2f"
          % (v_with() - (after_tax(6.5401 * 0.5, 7.5) + 1.5685 * 0.6) / SHARES))


if __name__ == "__main__":
    main()
