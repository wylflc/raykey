#!/usr/bin/env python3
"""南京银行（601009）独立估值：股利折现（DDM）与剩余收益（P/B-ROE）互校。

运行：python3 valuation.py
单位：金额亿元，每股元，比率为小数。价格日 2026-10-19，估值基准日同日。
口径：普通股东口径。归母净利先扣其他权益工具（优先股股息、永续债利息）才归普通股东；
银行不做净现金调整（存款是经营负债），net_cash_adj = 0，non_operating_assets = 0。
所有输入写在本脚本内，出处见注释（文件名 + PDF 物理页）。
"""

# ---------------------------------------------------------------- 统一快照
PRICE = 12.05            # 2026-10-19 收盘，腾讯日线
SHARES = 123.6357        # 亿股，腾讯行情；与 2026H1_report 第 9 页普通股股本 12,363,567 千股一致
COE = 0.09               # 股权成本基准（框架规定），敏感性 8% / 10%
G_TERM = 0.025           # 终值增长（框架上限）

# ---------------------------------------------------------------- 已披露事实
B_H1 = 1931.53           # 2026-06-30 归属普通股东净资产，2026H1_report 第 9 页 193,153,175 千元
NP_H1_2026 = 136.50      # 2026H1 归母净利，2026H1_report 第 9 页 13,650,199 千元
NP_H1_2025 = 126.19      # 2025H1 归母净利，同上 12,619,215 千元
NP_Q3_2025 = 53.86       # 2025Q3 单季归母净利，2025_annual_report 第 17 页 5,385,651 千元
NP_Q4_2025 = 38.02       # 2025Q4 单季归母净利，同页 3,802,223 千元
NP_2025 = 218.07         # 2025 归母净利，2025_annual_report 第 16 页
COMMON_NP_2025 = 207.01  # 2025 归属普通股东净利，dividend_20260423_467997 第 2 页
B_2025 = 1813.01         # 2025-12-31 归属普通股东净资产，2026H1_report 第 9 页 181,301,002 千元
B_2024 = 1586.29         # 2024-12-31 归属普通股东净资产，同页 158,629,458 千元
PREF2_DIV_2026 = 50 * 0.0407   # 南银优2 50 亿元、票面 4.07%（2026H1_report 第 83 页），2026-08 付息并于 2026-09 全额赎回
PERP_2022_CPN = 200 * 0.0332   # 2022 永续债 200 亿元、前 5 年 3.32%（2026H1_report 第 86 页），每年 10 月付息
AT1_DIST_2026 = PREF2_DIV_2026 + PERP_2022_CPN   # 2026 年其他权益工具分配 8.675
PAYOUT_PARENT = 0.30     # 年度现金分红 = 归母净利 30%（2025 年度 65.42/218.07；股东会资料第 94 页"继续保持净利润 30%"）
INTERIM_SHARE_H1 = 0.30  # 中期分红 = 上半年归母净利 30%（2025 中期 37.86/126.19 = 30.0%）
CET1_H1 = 1944.54        # 核心一级资本净额，2026H1_report 第 38 页 194,453,724 千元
RWA_H1 = 20748.29        # 风险加权资产，同页 2,074,829,309 千元
CET1_FLOOR_PLAN = 0.08   # 资本规划（2026-2028）核心一级目标下限，股东会资料第 72 页
NPL_H1 = 127.87          # 不良贷款，2026H1_report 第 34 页 次级+可疑+损失
LLR_H1 = 391.44          # 贷款损失准备，2026H1_report 第 9 页
COVER_2025 = 3.1362      # 2025 末拨备覆盖率，2026H1_report 第 11 页
NPL_2025 = 118.40        # 2025 末不良贷款，2026H1_report 第 34 页
AC_BOOK, AC_FV = 4443.11, 4728.41   # 债权投资账面与公允价值，2026H1_report 第 209 页

# 现金流时点（距 2026-10-19 的年数）：中期股息约 11-20 派发，末期约次年 6-15 派发
T_YE2026 = 73 / 365
T_INTERIM = 32 / 365            # 2026-11-20
T_FINAL = 239 / 365             # 2027-06-15
INTERIM_FRAC = 0.58             # 年度股息中中期部分占比（2025 年 37.86/65.42 = 57.9%）
# 其他权益工具分配（仅用于把普通股东净利还原为归母净利展示；估值直接用普通股东口径）：
# 资本类债券发行计划拟发永续债 600 亿（2026、2027 各 300 亿，股东会资料第 75 页），按 2.1% 票面
# （2026 年同业永续债 1.88%-2.06%）；2022 永续债 200 亿 2027-10 首个赎回日后假设赎回。
AT1_DIST = {2027: PERP_2022_CPN + 300 * 0.021}
AT1_DIST.update({y: 600 * 0.021 for y in range(2028, 2037)})

YEARS = list(range(2027, 2037))  # 显式期 10 年，2031 年后线性收敛至终值


def fade(first5, terminal):
    """前 5 年给定，2032-2036 线性收敛到终值。"""
    last = first5[-1]
    return list(first5) + [last + (terminal - last) * k / 5 for k in range(1, 6)]


# ---------------------------------------------------------------- 三情景
# roe：归属普通股东净利 / 平均普通股东权益（宣派口径），g：普通股东权益（≈风险加权资产）增速
SCEN = {
    "bear": dict(p=0.25, h2_growth=0.00,
                 roe=fade([0.104, 0.096, 0.089, 0.084, 0.080], 0.075),
                 g=fade([0.070, 0.060, 0.055, 0.050, 0.045], G_TERM), roe_t=0.075,
                 note="下半年归母净利同比持平；息差 2027-2029 再降约 15-20bp、信用成本升至约 1.2%、债券交易收益回落、"
                      "拨备释放停止，ROE 由 2027 年 10.4% 降至 2031 年 8.0%，长期 7.5%（略低于 2026 年二季度行业 7.72%）；权益增速 7%→4.5%"),
    "base": dict(p=0.50, h2_growth=0.08,
                 roe=fade([0.115, 0.111, 0.108, 0.105, 0.102], 0.100),
                 g=fade([0.083, 0.078, 0.073, 0.068, 0.063], G_TERM), roe_t=0.100,
                 note="下半年归母净利同比 +8%（全年 +8.1%）；息差 2026 企稳、此后每年小降，信用成本约 1.0%，"
                      "覆盖率下降的利润贡献逐步消失，永续债增发使分配由 8.7 亿增至约 12.6 亿；ROE 11.5%（2027）→10.2%（2031），"
                      "长期 10%；分红率 30% 起逐步抬升"),
    "bull": dict(p=0.25, h2_growth=0.10,
                 roe=fade([0.120, 0.119, 0.117, 0.115, 0.113], 0.110),
                 g=fade([0.087, 0.084, 0.080, 0.075, 0.070], G_TERM), roe_t=0.110,
                 note="下半年归母净利同比 +10%；存款重定价红利延续、信用成本回落至约 0.9%，"
                      "ROE 约 12% 维持到 2029 年后缓降，长期 11%；权益增速 8.7%→7%"),
}


def project(s, roe_shift=0.0, b_haircut=0.0, h2_growth=None):
    """返回逐年预测：2026 年用已披露上半年 + 下半年假设，2027 起按 ROE 与权益增速推演。"""
    h2g = s["h2_growth"] if h2_growth is None else h2_growth
    np_h2 = (NP_Q3_2025 + NP_Q4_2025) * (1 + h2g)
    np_2026 = NP_H1_2026 + np_h2
    common_2026 = np_2026 - AT1_DIST_2026
    div_2026 = PAYOUT_PARENT * np_2026
    interim_2026 = INTERIM_SHARE_H1 * NP_H1_2026
    final_2026 = div_2026 - interim_2026
    b_2026 = (B_H1 + np_h2 - AT1_DIST_2026 - div_2026) * (1 - b_haircut)   # 宣派口径（扣除全年股息）
    rows = []
    b_prev = b_2026
    for i, yr in enumerate(YEARS):
        roe = s["roe"][i] + roe_shift
        g = s["g"][i]
        b = b_prev * (1 + g)
        e = roe * (b_prev + b) / 2
        d = e - (b - b_prev)
        rows.append(dict(year=yr, roe=roe, g=g, b_prev=b_prev, b=b, e=e, d=d, payout=d / e))
        b_prev = b
    roe_t = s["roe_t"] + roe_shift
    return dict(np_h2=np_h2, np_2026=np_2026, common_2026=common_2026, div_2026=div_2026,
                interim_2026=interim_2026, final_2026=final_2026, b_2026=b_2026, rows=rows, roe_t=roe_t)


def value(pr, r):
    """返回 (DDM 每股, 剩余收益每股)。"""
    df = lambda t: (1 + r) ** (-t)
    # 2026 年股息（中期 2026-11、末期 2027-06），两法共用
    pv26 = (pr["interim_2026"] * df(T_INTERIM) + pr["final_2026"] * df(T_FINAL))
    # DDM：t 年股息 58% 于当年 11 月、42% 于次年 6 月派发
    pv_div = 0.0
    for row in pr["rows"]:
        k = row["year"] - 2026
        pv_div += row["d"] * (INTERIM_FRAC * df(k + T_INTERIM) + (1 - INTERIM_FRAC) * df(k + T_FINAL))
    b_n = pr["rows"][-1]["b"]
    roe_t = pr["roe_t"]
    d_next = b_n * (roe_t * (1 + G_TERM / 2) - G_TERM)          # 2037 年股息
    lag = INTERIM_FRAC * (T_INTERIM - T_YE2026) + (1 - INTERIM_FRAC) * (T_FINAL - T_YE2026)
    tv_ddm = d_next / (r - G_TERM) * (1 + r) ** (-lag)           # 2036 年末价值
    n = len(YEARS)
    ddm = pv26 + pv_div + tv_ddm * df(T_YE2026 + n)
    # 剩余收益：V = B_2026 + Σ(E_t - r·B_{t-1}) 折现 + 终值剩余收益
    pv_ri = 0.0
    for row in pr["rows"]:
        k = row["year"] - 2026
        pv_ri += (row["e"] - r * row["b_prev"]) * (1 + r) ** (-k)
    tv_ri = b_n * (roe_t * (1 + G_TERM / 2) - r) / (r - G_TERM)
    ri = pv26 + (pr["b_2026"] + pv_ri + tv_ri * (1 + r) ** (-n)) * df(T_YE2026)
    return ddm / SHARES, ri / SHARES


def v_of(pr, r):
    ddm, ri = value(pr, r)
    return ddm          # 主值取 DDM（分红现金流时点真实）；剩余收益作互校


def tv_share(pr, r):
    """DDM 中 2036 年末终值现值占 V 的比例。"""
    b_n = pr["rows"][-1]["b"]
    d_next = b_n * (pr["roe_t"] * (1 + G_TERM / 2) - G_TERM)
    lag = INTERIM_FRAC * (T_INTERIM - T_YE2026) + (1 - INTERIM_FRAC) * (T_FINAL - T_YE2026)
    tv = d_next / (r - G_TERM) * (1 + r) ** (-lag) * (1 + r) ** (-(T_YE2026 + len(YEARS)))
    return tv / SHARES / v_of(pr, r)


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


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


# ---------------------------------------------------------------- ROE 拆解与信用（仅展示，不进入 V）
# 2025：2025_annual_report 第 16、23、26-28 页；H1 2026：2026H1_report 第 9、17、21-23、34、37 页（上半年数 ×2 年化）
DUPONT = {
    "2025": dict(assets=(25914.00, 30218.20), nii=349.02, fee=42.82, inv=159.05, oth=4.53, ga=144.79,
                 tax_s=7.63, oth_cost=2.32, imp=139.28, nonop=-0.78, tax=40.05, minority=2.50,
                 at1=11.06, ceq=(1586.29, 1813.01), k=1),
    "2026H1年化": dict(assets=(30218.20, 32373.24), nii=219.35, fee=22.83, inv=72.77, oth=1.01, ga=71.71,
                     tax_s=4.03, oth_cost=1.07, imp=74.42, nonop=-0.32, tax=26.98, minority=0.93,
                     at1=AT1_DIST_2026 / 2, ceq=(1813.01, 1931.53), k=2),
}
CREDIT = {
    # 不良（期初、期末）、核销及转销、收回已核销、摊余成本贷款减值计提、贷款（期初、期末）、年化倍数
    "2025": dict(npl=(103.87, 118.40), wo=142.45, rec=26.63, prov=140.46, loans=(12563.98, 14243.56), k=1),
    "2026H1": dict(npl=(118.40, 127.87), wo=72.51, rec=16.47, prov=77.10, loans=(14243.56, 15677.91), k=2),
}


def dupont():
    print("== ROE 拆解（占平均总资产） ==")
    print(" 期间        净利息  手续费  投资类  营收    费用    信用减值  税前   所得税率  ROA(归母)  杠杆   普通股东ROE")
    for name, d in DUPONT.items():
        k = d["k"]
        avg_a = sum(d["assets"]) / 2
        rev = d["nii"] + d["fee"] + d["inv"] + d["oth"]
        ppop = rev - d["ga"] - d["tax_s"] - d["oth_cost"]
        pretax = ppop - d["imp"] + d["nonop"]
        np_ = pretax - d["tax"]
        parent = np_ - d["minority"]
        common = parent - d["at1"]
        avg_e = sum(d["ceq"]) / 2
        f = lambda x: x * k / avg_a * 100
        print(" %-10s %5.2f%%  %5.2f%%  %5.2f%%  %5.2f%%  %5.2f%%  %5.2f%%   %5.2f%%  %5.1f%%   %5.2f%%    %5.2f  %5.2f%%"
              % (name, f(d["nii"]), f(d["fee"]), f(d["inv"]), f(rev), f(d["ga"]), f(d["imp"]), f(pretax),
                 d["tax"] / pretax * 100, f(parent), avg_a / avg_e, common * k / avg_e * 100))
        print("            成本收入比 %.1f%%；拨备前利润 %.1f 亿（占资产 %.2f%%）" % (d["ga"] / rev * 100, ppop, f(ppop)))
    print(" 注：上半年年化未扣季节性，2025 年四季度单季归母仅 38.0 亿，全年 ROE 以 2026E 11.97% 为准")
    print()
    print("== 不良生成与信用成本 ==")
    for name, c in CREDIT.items():
        k = c["k"]
        avg_l = sum(c["loans"]) / 2
        gen = (c["npl"][1] - c["npl"][0] + c["wo"]) * k / avg_l
        nco = (c["wo"] - c["rec"]) * k / avg_l
        cc = c["prov"] * k / avg_l
        print(" %-7s 不良生成率 %.2f%%  净核销率 %.2f%%  贷款信用成本 %.2f%%  期末不良率 %.2f%%"
              % (name, gen * 100, nco * 100, cc * 100, c["npl"][1] / c["loans"][1] * 100))
    print()


def main():
    print("南京银行（601009）独立估值  价格日 2026-10-19  现价 %.2f 元  总股本 %.4f 亿股" % (PRICE, SHARES))
    print("市值 %.1f 亿元；2026-06-30 普通股每股净资产 %.2f 元，P/B %.3f" % (PRICE * SHARES, B_H1 / SHARES, PRICE / (B_H1 / SHARES)))
    print()
    dupont()
    # ---------------- 2026 年估计与正常化
    print("== 2026 年估计（上半年已披露 + 下半年假设） ==")
    cover_release_h1 = COVER_2025 * NPL_H1 - LLR_H1
    print("上半年拨备覆盖率由 313.62%% 降至 306.11%%：维持年初覆盖率需多计提 %.1f 亿元（税前）" % cover_release_h1)
    for k, s in SCEN.items():
        pr = project(s)
        print("%-4s 下半年 %.2f  全年归母 %.2f（同比 %+.1f%%）  普通股东净利 %.2f  年度股息 %.2f（每股 %.3f，中期 %.3f）  年末宣派口径 BVPS %.2f"
              % (k, pr["np_h2"], pr["np_2026"], (pr["np_2026"] / NP_2025 - 1) * 100, pr["common_2026"],
                 pr["div_2026"], pr["div_2026"] / SHARES, pr["interim_2026"] / SHARES, pr["b_2026"] / SHARES))
    base26 = project(SCEN["base"])
    b26_cash = base26["b_2026"] + base26["final_2026"]
    roe26 = base26["common_2026"] / ((B_2025 + b26_cash) / 2)
    print("基准 2026E 普通股东 ROE（平均权益）%.2f%%；2025 年 %.2f%%" % (roe26 * 100, COMMON_NP_2025 / ((B_2024 + B_2025) / 2) * 100))
    cover_release_fy = 2 * (COVER_2025 * NPL_H1 - LLR_H1) * 0.75   # 全年按上半年两倍、税率 25% 折税后
    norm = {"bear": project(SCEN["bear"])["np_2026"] - cover_release_fy,
            "base": base26["np_2026"],
            "bull": project(SCEN["bull"])["np_2026"]}
    print("2026 正常化归母净利：熊 %.1f（再扣覆盖率下降贡献税后约 %.1f）  基准 %.1f  牛 %.1f"
          % (norm["bear"], cover_release_fy, norm["base"], norm["bull"]))
    print()
    # ---------------- 逐年路径
    for k in ("bear", "base", "bull"):
        pr = project(SCEN[k])
        print("== %s 情景路径（普通股东口径，亿元） ==" % k)
        prev_e = pr["common_2026"]
        print(" 年份   ROE    权益增速  普通股东净利  同比    股息   分红率  年末权益  BVPS   DPS")
        for row in pr["rows"]:
            print(" %d  %5.2f%%  %5.2f%%   %8.1f   %+5.1f%%  %6.1f  %5.1f%%  %7.1f  %5.2f  %5.3f"
                  % (row["year"], row["roe"] * 100, row["g"] * 100, row["e"], (row["e"] / prev_e - 1) * 100,
                     row["d"], row["payout"] * 100, row["b"], row["b"] / SHARES, row["d"] / SHARES))
            prev_e = row["e"]
        par = [row["e"] + AT1_DIST[row["year"]] for row in pr["rows"][:5]]
        prev_p = pr["np_2026"]
        gp = []
        for x in par:
            gp.append("%.1f（%+.1f%%）" % (x, (x / prev_p - 1) * 100))
            prev_p = x
        print(" 还原归母净利 2027-2031：" + "，".join(gp))
        print(" 终值：ROE %.1f%%，增长 %.1f%%，稳态分红率 %.0f%%，终值 P/B %.3f"
              % (pr["roe_t"] * 100, G_TERM * 100, (1 - G_TERM / (pr["roe_t"] * (1 + G_TERM / 2))) * 100,
                 (pr["roe_t"] * (1 + G_TERM / 2) - G_TERM) / (COE - G_TERM)))
        print()
    # ---------------- 估值
    print("== 三情景 V（元/股） ==")
    print(" 情景  概率   DDM@9%   剩余收益@9%  差异   DDM@8%   DDM@10%")
    res = {}
    for k, s in SCEN.items():
        pr = project(s)
        d9, r9 = value(pr, COE)
        d8, _ = value(pr, 0.08)
        d10, _ = value(pr, 0.10)
        res[k] = dict(v=d9, ri=r9, v8=d8, v10=d10)
        print(" %-4s  %.2f   %6.2f    %6.2f     %+.1f%%  %6.2f   %6.2f" % (k, s["p"], d9, r9, (r9 / d9 - 1) * 100, d8, d10))
    vw = sum(SCEN[k]["p"] * res[k]["v"] for k in SCEN)
    vw8 = sum(SCEN[k]["p"] * res[k]["v8"] for k in SCEN)
    vw10 = sum(SCEN[k]["p"] * res[k]["v10"] for k in SCEN)
    pv = PRICE / vw
    print(" 加权 V = %.2f 元；P/V = %.3f（%s）" % (vw, pv, tier(pv)))
    print(" 股权成本 8%%：加权 V = %.2f；10%%：加权 V = %.2f" % (vw8, vw10))
    print(" 终值（2036 年末）现值占 V：熊 %.0f%%  基准 %.0f%%  牛 %.0f%%"
          % tuple(tv_share(project(SCEN[k]), COE) * 100 for k in ("bear", "base", "bull")))
    for lo_pv, name in ((0.75, "明显低估上沿"), (0.90, "温和低估上沿"), (1.10, "大致合理上沿")):
        print("   V 不变时 %s 价格 = %.2f 元" % (name, lo_pv * vw))
    print()
    # ---------------- 现价隐含回报与反向估值
    irr = solve(lambda r: v_of(project(SCEN["base"]), r), 0.03, 0.40, PRICE)
    print("== 现价隐含回报 ==")
    print(" 基准情景分红流（含终值）使现值等于现价的折现率 = %.2f%%" % (irr * 100))
    shift = solve(lambda d: v_of(project(SCEN["base"], roe_shift=d), COE), -0.06, 0.03, PRICE)
    print(" 反向：股权成本 9%% 下，基准 ROE 路径整体平移 %+.2fpp 才与现价相等 → 隐含 2027 年 ROE %.1f%%、长期 ROE %.1f%%"
          % (shift * 100, (SCEN["base"]["roe"][0] + shift) * 100, (SCEN["base"]["roe_t"] + shift) * 100))
    pb_now = PRICE / (B_H1 / SHARES)
    print(" 稳态公式：P/B %.3f = (ROE-g)/(r-g) → 隐含永续 ROE = %.2f%%（g 2.5%%，r 9%%）" % (pb_now, (G_TERM + pb_now * (COE - G_TERM)) * 100))
    impl_r = G_TERM + (roe26 - G_TERM) / pb_now
    print(" 稳态公式：若 ROE 永续维持 2026E %.2f%%，现价隐含股权成本 = %.2f%%" % (roe26 * 100, impl_r * 100))
    print()
    # ---------------- 交叉验证
    print("== 交叉验证 ==")
    dps_ttm = 0.3062 + 0.22295
    print(" 股息率：过去 12 个月 %.3f 元 → %.2f%%；2026E 每股 %.3f 元 → %.2f%%；无回购"
          % (dps_ttm, dps_ttm / PRICE * 100, base26["div_2026"] / SHARES, base26["div_2026"] / SHARES / PRICE * 100))
    print(" 2026E 市盈率 %.2f 倍（归母）；2026E 普通股东每股收益 %.3f 元"
          % (PRICE * SHARES / base26["np_2026"], base26["common_2026"] / SHARES))
    pb_ss = lambda roe: (roe * (1 + G_TERM / 2) - G_TERM) / (COE - G_TERM)
    print(" 单阶段 P/B-ROE：ROE 8%%/10%%/11%% → 合理 P/B %.2f/%.2f/%.2f → 以 6 月末 BVPS 计 %.2f/%.2f/%.2f 元"
          % (pb_ss(0.08), pb_ss(0.10), pb_ss(0.11), pb_ss(0.08) * B_H1 / SHARES, pb_ss(0.10) * B_H1 / SHARES, pb_ss(0.11) * B_H1 / SHARES))
    naive = (base26["div_2026"] / SHARES) * (1 + G_TERM) / (COE - G_TERM)
    print(" 朴素股利模型（分红率永远 30%%、股息永续增 2.5%%）= %.2f 元：等于假设留存利润永不产生回报，只作下限参照" % naive)
    print()
    # ---------------- 资本约束
    print("== 资本约束（基准） ==")
    cet1_26 = CET1_H1 + (b26_cash - B_H1)
    rwa_26 = RWA_H1 * 1.04
    print(" 2026 末核心一级资本约 %.0f 亿，RWA 约 %.0f 亿（下半年 +4%%）→ CET1 %.2f%%；规划下限 %.0f%%"
          % (cet1_26, rwa_26, cet1_26 / rwa_26 * 100, CET1_FLOOR_PLAN * 100))
    cet1, rwa = cet1_26, rwa_26
    rows = base26["rows"]
    out = []
    for row in rows[:5]:
        cet1 += row["b"] - row["b_prev"]
        rwa *= 1.10
        out.append("%d %.2f%%" % (row["year"], cet1 / rwa * 100))
    print(" 若 RWA 每年增 10%（2025 年为 14.4%）而分红按基准：CET1 " + "，".join(out))
    roe27 = rows[0]["roe"]
    print(" 2027 年 ROE %.1f%% 时，分红率 30%% 可支撑的内生增速约 %.1f%%" % (roe27 * 100, roe27 * 0.70 / (1 - roe27 * 0.70 / 2) * 100))
    print()
    # ---------------- 拨备与隐含价值（不计入 V）
    excess150 = (LLR_H1 / NPL_H1 - 1.50) * NPL_H1
    print("== 不计入 V 的缓冲 ==")
    print(" 拨备覆盖率 306.11%%，超出 150%% 的准备金 %.0f 亿元（税前），税后约 %.0f 亿元，每股 %.2f 元"
          % (excess150, excess150 * 0.75, excess150 * 0.75 / SHARES))
    print(" 债权投资浮盈 %.0f 亿元（公允价值 %.0f − 账面 %.0f，税前），税后每股 %.2f 元"
          % (AC_FV - AC_BOOK, AC_FV, AC_BOOK, (AC_FV - AC_BOOK) * 0.75 / SHARES))
    print()
    # ---------------- 证伪情景
    print("== 证伪条件触发后的 V（元/股，按原概率加权，股权成本 9%） ==")
    fal = {
        "F1 前三季归母净利同比 < +5%（下半年按持平、ROE 路径 -0.4pp）":
            dict(bear=dict(h2_growth=0.0, roe_shift=-0.004), base=dict(h2_growth=0.0, roe_shift=-0.004), bull=dict(h2_growth=0.0, roe_shift=-0.004)),
        "F2 2026 年报净息差 < 1.72% 或信用减值/平均贷款 > 1.15%（ROE 路径 -0.8pp）":
            dict(bear=dict(roe_shift=-0.008), base=dict(roe_shift=-0.008), bull=dict(roe_shift=-0.008)),
        "F3 2027 中报不良率 > 0.95% 或拨备覆盖率 < 260%（ROE -1.0pp 且净资产 -3%）":
            dict(bear=dict(roe_shift=-0.010, b_haircut=0.03), base=dict(roe_shift=-0.010, b_haircut=0.03), bull=dict(roe_shift=-0.010, b_haircut=0.03)),
        "F4 CET1 < 8.5% 或低于每股净资产增发普通股（净资产 -2%、ROE -0.3pp）":
            dict(bear=dict(b_haircut=0.02, roe_shift=-0.003), base=dict(b_haircut=0.02, roe_shift=-0.003), bull=dict(b_haircut=0.02, roe_shift=-0.003)),
        "F5 2027 年加权 ROE < 10.5%（全路径按熊市）":
            None,
    }
    fal_v = {}
    for name, kw in fal.items():
        if kw is None:
            v = v_of(project(SCEN["bear"]), COE)
        else:
            v = sum(SCEN[k]["p"] * v_of(project(SCEN[k], **kw[k]), COE) for k in SCEN)
        fal_v[name] = v
        print(" %s → V %.2f，P/V %.2f" % (name, v, PRICE / v))
    print()
    # ---------------- json 用增长路径
    rows = base26["rows"]
    gr, prev = [], base26["common_2026"]
    for row in rows[:5]:
        gr.append(row["e"] / prev - 1)
        prev = row["e"]
    reinv = 1 - sum(r_["payout"] for r_ in rows[:5]) / 5
    incr = sum(r_["roe"] for r_ in rows[:5]) / 5
    print("== json 摘要 ==")
    print(" scenarios v: bear %.2f base %.2f bull %.2f；v_weighted %.2f；pv %.3f；v8 %.2f；v10 %.2f；irr %.4f"
          % (res["bear"]["v"], res["base"]["v"], res["bull"]["v"], vw, pv, vw8, vw10, irr))
    print(" growth_path 2027-2031：" + "，".join("%.3f" % x for x in gr) + "；再投资率 %.2f；增量回报 %.3f" % (reinv, incr))
    print(" normalized_parent_np_2026：bear %.1f base %.1f bull %.1f" % (norm["bear"], norm["base"], norm["bull"]))
    print(" falsifiers v：" + "，".join("%.2f" % v for v in fal_v.values()))


if __name__ == "__main__":
    main()
