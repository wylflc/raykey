#!/usr/bin/env python3
"""农业银行（601288）独立估值：剩余收益（P/B–ROE）与股利折现（DDM）互校。

OI-291 池内独立审计 b03，价格日 2026-10-19。用法：python3 valuation.py
单位：金额亿元，股本亿股，每股元。输入全部写在本脚本内，出处见注释
（“H1”= 2026H1_report，“AR”= 2025_annual_report，页码为 PDF 物理页）。

口径：
- 估值对象是普通股东。归母净利先扣其他权益工具（永续债利息与优先股股息）才归普通股东。
- 银行不做净现金调整：客户存款与同业负债是经营负债，现金与债券是经营资产。
- 定向增发（≤1,600 亿元，财政部 1,300 亿元）按 2026 年末完成计入：权益 +1,600，
  股数按假设发行价折算；增发资金先替代付息负债，按 1.6% 税前利息节省计入利润。
- 2026-10-21 除息的中期股息 0.1297 元只属于现有股份，在价格日计入每股价值（现价含息）。
- 年度股息按年末支付处理（期末股息实际次年年中支付，影响很小）；RI 与 DDM 用同一套假设，
  两者相等用来核对净盈余关系，独立的交叉验证见静态 P/B、历史 P/B、同业与股息率。
"""

import math

# ---------------------------------------------------------------- 市场与股本
PRICE = 7.49                 # A 股 2026-10-19 收盘（腾讯日线），含 2026 中期股息
N_OLD = 3499.8303            # A 3,192.4421 + H 307.3882 亿股（H1 第 88 页）
DPS_INTERIM = 0.1297         # 2026 中期股息，股权登记 10-20、除息 10-21（dividend_20261014 第 1 页）
INTERIM_TOTAL = 453.93       # 合计 453.93 亿元（dividend_20260829 第 1 页）
H_PRICE_HKD = 6.74           # H 股 2026-10-16 收盘（10-19 港股重阳节休市），仅作参考
T0_TO_YE = 73 / 365          # 价格日到 2026-12-31

# ---------------------------------------------------------------- 定向增发
RAISE = 1600.0               # 募资上限（holders_20260907 第 2 页；募集说明书第 48 页）
P_ISSUE = 7.20               # 假设发行价：近 20 日收盘均价 7.02 与现价除息后 7.36 之间
FUND_SAVING = 0.016          # 增发资金替代付息负债的税前利息节省率

# ---------------------------------------------------------------- 2026 上半年实际
B_H1 = 33280.14 - 4700.00    # 普通股权益 = 归母权益 - 其他权益工具（H1 第 10、32 页）
PARENT_H1_2026 = 1463.81     # 归母净利（H1 第 10 页）
ORD_H1_2026 = 1395.60        # 普通股东净利，已扣其他权益工具股息 68.21（H1 第 196 页）
DIST_H1_2026 = 68.21
# 2026 下半年其他权益工具派息：2021/22/23/24/25 年各期永续债按票面 + 农行优1（H1 第 93、176-178 页）
DIST_H2_2026 = 400 * 0.0376 + 300 * 0.0317 + 400 * 0.0321 + 400 * 0.0229 + 400 * 0.0227 + 16.48
PARENT_2025 = 2910.41        # AR 第 10 页
PARENT_H1_2025 = 1395.10     # F10 单季合计，AR 第 11 页季度表
PARENT_H2_2025 = PARENT_2025 - PARENT_H1_2025
ORD_2025 = 2739.56           # AR 第 294 页（扣其他权益工具 170.85）
PAYOUT_PARENT = 0.30         # 2025 年 30.00%，2026 中期 31.0%（dividend_20260331 第 2 页；H1 第 94 页）

# 资产负债起点（2026 年末估计）
ASSETS_H1 = 510588.73        # H1 第 10 页
RWA_H1 = 262816.08           # H1 第 74 页
ASSETS_YE26 = 528000.0       # 2026 年末总资产估计（上半年 +4.7%，下半年按 +3.4%）
RWA_YE26 = RWA_H1 * ASSETS_YE26 / ASSETS_H1
CET1_DEDUCT = 200.0          # 核心一级资本扣除项约 203.65 亿（H1 第 270 页附注）
IEA_RATIO = 0.9756           # 生息资产/总资产（H1 第 17 页平均余额 49,125.6/50,354.6）
LOAN_RATIO = 0.5645          # 贷款总额/总资产（H1 第 10 页）
FEES_2026 = 851.0            # 手续费净收入 2026E：上半年 469.59 + 下半年 381
OPEX_2026 = 2673.0           # 业务及管理费 2026E：上半年 1,082.03 + 下半年 1,591
OTHER_COST_RATIO = 0.027     # 税金及附加、其他业务成本、营业外净额占营收（2025 年 193/7,253）
PPOP_2026 = 8075.0 - OPEX_2026 - 215.0   # 2026E 拨备前利润（营收 8,075 估计）
EXCESS_GAIN_2026 = 172.7     # 投资收益+公允价值 2026E 约 700.7，高于 2025 年 528.1 的部分
AVG_LOANS_2026 = (271348.34 + 2 * 288247.60 + LOAN_RATIO * ASSETS_YE26) / 4

# 其他权益工具派息与少数股东损益路径（2027-2031）
DIST = [145.0, 148.0, 151.0, 154.0, 157.0]
MINORITY = [35.0, 36.0, 37.0, 38.0, 39.0]
PAYOUT_ORD = 0.315           # 普通股东口径分红率，约等于归母口径 30%
G_TERMINAL = 0.025           # 终值增长（框架上限）
COE = 0.09
YEARS = list(range(2027, 2032))

SCENARIOS = {
    "bear": dict(p=0.25, g_h2=0.010,
                 asset_g=[0.065, 0.06, 0.055, 0.05, 0.05],
                 nim=[0.0124, 0.0122, 0.0120, 0.0119, 0.0118],
                 fee_g=[0.02] * 5, other_nonii=[620.0] * 5, opex_g=[0.045] * 5,
                 credit_cost=[0.0060, 0.0060, 0.0060, 0.0058, 0.0058],
                 etr=[0.145] * 5, roe_lr=0.073, gain_nonrec=1.0,
                 text="净息差 2027 年 1.24% 降到 2031 年 1.18%；信用成本 0.60%（个人经营贷、县域与地产不良上行）；"
                      "税率 14.5%；非息收入不增长；长期 ROE 7.3%"),
    "base": dict(p=0.50, g_h2=0.045,
                 asset_g=[0.07, 0.065, 0.06, 0.06, 0.055],
                 nim=[0.0127, 0.0125, 0.0124, 0.0123, 0.0122],
                 fee_g=[0.03, 0.04, 0.04, 0.04, 0.04],
                 other_nonii=[650.0, 670.0, 690.0, 710.0, 730.0], opex_g=[0.04] * 5,
                 credit_cost=[0.0055] * 5, etr=[0.135] * 5, roe_lr=0.087, gain_nonrec=0.75,
                 text="净息差 2027 年 1.27% 缓降到 2031 年 1.22%；资产增速 7% 降到 5.5%；信用成本 0.55%；"
                      "税率 13.5%；归母分红率 30%；长期 ROE 8.7%"),
    "bull": dict(p=0.25, g_h2=0.060,
                 asset_g=[0.07, 0.07, 0.065, 0.06, 0.06],
                 nim=[0.0128] * 5, fee_g=[0.035] * 5,
                 other_nonii=[660.0, 673.0, 687.0, 700.0, 714.0], opex_g=[0.038] * 5,
                 credit_cost=[0.0050] * 5, etr=[0.13] * 5, roe_lr=0.096, gain_nonrec=0.5,
                 text="存款成本继续下行使净息差稳在 1.28%；信用成本 0.50%；税率 13%；手续费恢复增长；长期 ROE 9.6%"),
}


def start_2026(s, p_issue=P_ISSUE, raise_amt=RAISE):
    """2026 年下半年估计与年末起点（含增发）。"""
    parent26 = PARENT_H1_2026 + PARENT_H2_2025 * (1 + s["g_h2"])
    ord26 = parent26 - DIST_H1_2026 - DIST_H2_2026
    ord_h2 = ord26 - ORD_H1_2026
    b_pre = B_H1 + ord_h2 - INTERIM_TOTAL               # 已扣中期股息，未扣期末股息
    final_div = PAYOUT_PARENT * parent26 - INTERIM_TOTAL  # 2026 期末股息（新股参与）
    b_cum = b_pre + raise_amt                             # 年末含增发、含待派期末股息
    n_post = N_OLD + (raise_amt / p_issue if raise_amt else 0.0)
    return dict(parent26=parent26, ord26=ord26, b_pre=b_pre, final_div=final_div,
                b_cum=b_cum, b0=b_cum - final_div, n_post=n_post)


def project(s, r=COE, p_issue=P_ISSUE, raise_amt=RAISE, roe_const=None,
            nim_shift=0.0, cc_shift=0.0, payout=PAYOUT_ORD, roe_lr=None):
    """驱动因素预测 2027-2031，2032-2036 线性收敛到长期 ROE 与稳态分红率，2037 起 g=2.5%。"""
    st = start_2026(s, p_issue, raise_amt)
    lr = s["roe_lr"] if roe_lr is None else roe_lr
    if roe_const is not None:
        lr = roe_const
    b = st["b0"]
    assets, fees, opex = ASSETS_YE26, FEES_2026, OPEX_2026
    rwa = RWA_YE26
    rows, books, ords, divs = [], [b], [], []
    for i, yr in enumerate(YEARS):
        a1 = assets * (1 + s["asset_g"][i])
        avg_a = (assets + a1) / 2
        nii = IEA_RATIO * avg_a * (s["nim"][i] + nim_shift) + raise_amt * FUND_SAVING
        fees *= 1 + s["fee_g"][i]
        opex *= 1 + s["opex_g"][i]
        rev = nii + fees + s["other_nonii"][i]
        credit = (s["credit_cost"][i] + cc_shift) * LOAN_RATIO * avg_a
        pbt = rev - opex - OTHER_COST_RATIO * rev - credit
        parent = pbt * (1 - s["etr"][i]) - MINORITY[i]
        ordn = parent - DIST[i]
        if roe_const is not None:
            ordn = roe_const * b
            parent = ordn + DIST[i]
        d = payout * ordn
        b1 = b + ordn - d
        rwa *= 1 + s["asset_g"][i]
        rows.append(dict(year=yr, nim=s["nim"][i] + nim_shift, nii=nii, rev=rev, opex=opex, ci=opex / rev,
                         credit=credit, pbt=pbt, etr=s["etr"][i], parent=parent, ord=ordn,
                         roe_b=ordn / b, roe_avg=ordn / ((b + b1) / 2), div=d, cet1=(b1 - CET1_DEDUCT) / rwa))
        ords.append(ordn)
        divs.append(d)
        b = b1
        books.append(b)
        assets = a1
    roe31 = rows[-1]["roe_b"]
    p_lr = 1 - G_TERMINAL / lr
    for j in range(1, 6):
        roe = roe31 + (lr - roe31) * j / 5
        p = payout + (p_lr - payout) * j / 5
        ordn = roe * b
        d = p * ordn
        ords.append(ordn)
        divs.append(d)
        b = b + ordn - d
        books.append(b)
    # 剩余收益法：V(2026 年末，含期末股息) = 含息账面 + Σ RI 现值 + 终值
    pv_ri = sum((ords[k] - r * books[k]) / (1 + r) ** (k + 1) for k in range(10))
    tv_ri = (lr - r) * books[10] / (r - G_TERMINAL) / (1 + r) ** 10
    v_ri = st["b_cum"] + pv_ri + tv_ri
    # 股利折现法：同一股利流
    pv_div = st["final_div"] + sum(divs[k] / (1 + r) ** (k + 1) for k in range(10))
    tv_ddm = (lr - G_TERMINAL) * books[10] / (r - G_TERMINAL) / (1 + r) ** 10
    v_ddm = pv_div + tv_ddm
    disc = (1 + r) ** T0_TO_YE
    per_ri = DPS_INTERIM + v_ri / st["n_post"] / disc
    per_ddm = DPS_INTERIM + v_ddm / st["n_post"] / disc
    return dict(st=st, rows=rows, books=books, ords=ords, divs=divs, lr=lr, p_lr=p_lr,
                pv_ri=pv_ri, tv_ri=tv_ri, v_ri=v_ri, pv_div=pv_div, tv_ddm=tv_ddm, v_ddm=v_ddm,
                per_ri=per_ri, per_ddm=per_ddm, v=per_ri)


def weighted(vals, probs=None):
    probs = probs or {k: SCENARIOS[k]["p"] for k in SCENARIOS}
    return sum(probs[k] * vals[k] for k in vals)


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def irr_per_share(res, price=PRICE):
    """现有股份的股利流（含价格日中期股息与终值）使现值等于现价的折现率。"""
    n = res["st"]["n_post"]
    flows = [(0.0, DPS_INTERIM), (T0_TO_YE, res["st"]["final_div"] / n)]
    flows += [(T0_TO_YE + k + 1, res["divs"][k] / n) for k in range(10)]
    b_end, lr = res["books"][10], res["lr"]

    def pv(x):
        tv = (lr - G_TERMINAL) * b_end / (x - G_TERMINAL) / n
        return sum(c / (1 + x) ** t for t, c in flows) + tv / (1 + x) ** (T0_TO_YE + 10) - price
    return bisect(pv, G_TERMINAL + 0.002, 0.30)


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def normalized_2026(s):
    """2026 年正常化归母净利：剔除高于 2025 年水平的投资收益（按情景的非经常比例），
    信用成本与税率换成该情景的常态值。"""
    ppop = PPOP_2026 - EXCESS_GAIN_2026 * s["gain_nonrec"]
    pbt = ppop - s["credit_cost"][0] * AVG_LOANS_2026
    return pbt * (1 - s["etr"][0]) - MINORITY[0]


def main():
    print("=== 农业银行 601288 独立估值（价格日 2026-10-19，现价 %.2f 元，股权成本 %.0f%%）===" % (PRICE, COE * 100))
    print(f"现有股本 {N_OLD:.4f} 亿股；增发 {RAISE:.0f} 亿元 @ {P_ISSUE:.2f} 元 = {RAISE / P_ISSUE:.2f} 亿股，"
          f"增发后 {N_OLD + RAISE / P_ISSUE:.2f} 亿股")
    print(f"2026 上半年普通股权益 {B_H1:.2f} 亿元，每股 {B_H1 / N_OLD:.3f} 元；"
          f"下半年其他权益工具派息估计 {DIST_H2_2026:.2f} 亿元")

    res = {k: project(s) for k, s in SCENARIOS.items()}

    print("\n--- 2026 年桥接与 2026 年正常化归母净利 ---")
    for k, s in SCENARIOS.items():
        st = res[k]["st"]
        cet1_pre = (st["b_pre"] - st["final_div"] - CET1_DEDUCT) / RWA_YE26
        cet1_post = (st["b0"] - CET1_DEDUCT) / RWA_YE26
        print(f"{k}: 下半年归母同比 {s['g_h2']:+.1%} → 2026E 归母 {st['parent26']:.0f}（{st['parent26'] / PARENT_2025 - 1:+.1%}），"
              f"普通股东 {st['ord26']:.0f}；年末普通股权益 增发前 {st['b_pre']:.0f} / 含增发 {st['b_cum']:.0f}；"
              f"期末股息 {st['final_div']:.1f}；核心一级 增发前 {cet1_pre:.2%} / 增发后 {cet1_post:.2%}；"
              f"正常化归母 {normalized_2026(s):.0f}")

    for k in SCENARIOS:
        r_ = res[k]
        n = r_["st"]["n_post"]
        print(f"\n--- {k} 情景：{SCENARIOS[k]['text']} ---")
        print("年份  净息差  利息净收入  营收    成本收入比 信用减值  税前    归母净利(增速)    普通股东净利(增速)  ROE期初 ROE平均  每股股息 核心一级")
        prev_parent, prev_ord = r_["st"]["parent26"], r_["st"]["ord26"]
        for row in r_["rows"]:
            print(f"{row['year']}  {row['nim']:.2%}  {row['nii']:8.0f}  {row['rev']:7.0f}  {row['ci']:6.1%}  {row['credit']:7.0f}  "
                  f"{row['pbt']:6.0f}  {row['parent']:6.0f}({row['parent'] / prev_parent - 1:+5.1%})  "
                  f"{row['ord']:6.0f}({row['ord'] / prev_ord - 1:+5.1%})  {row['roe_b']:.2%}  {row['roe_avg']:.2%}  "
                  f"{row['div'] / n:.4f}  {row['cet1']:.2%}")
            prev_parent, prev_ord = row["parent"], row["ord"]
        print(f"2032-2036 ROE 由 {r_['rows'][-1]['roe_b']:.2%} 线性收敛到长期 {r_['lr']:.2%}，分红率由 31.5% 升到稳态 {r_['p_lr']:.1%}")
        print(f"RI：含息账面 {r_['st']['b_cum']:.0f} + RI 现值 {r_['pv_ri']:.0f} + 终值 {r_['tv_ri']:.0f} = {r_['v_ri']:.0f} 亿元"
              f"（年末 P/B {r_['v_ri'] / r_['st']['b_cum']:.3f}）")
        print(f"DDM：股利现值 {r_['pv_div']:.0f} + 终值 {r_['tv_ddm']:.0f} = {r_['v_ddm']:.0f} 亿元（终值占 {r_['tv_ddm'] / r_['v_ddm']:.1%}）；"
              f"差异 {r_['v_ddm'] - r_['v_ri']:+.3f}")
        print(f"每股 V（含 0.1297 元中期股息）：RI {r_['per_ri']:.3f} / DDM {r_['per_ddm']:.3f} 元")

    vals = {k: res[k]["v"] for k in SCENARIOS}
    vw = weighted(vals)
    pv = PRICE / vw
    print("\n=== 三情景与加权 ===")
    for k in SCENARIOS:
        print(f"{k}: V = {vals[k]:.2f} 元，概率 {SCENARIOS[k]['p']:.0%}")
    print(f"加权 V = {vw:.2f} 元；P/V = {pv:.3f} → {verdict(pv)}")
    print(f"V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}–{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}–{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n=== 股权成本敏感性（同一 ROE 路径）===")
    sens = {}
    for r in (0.08, 0.10):
        v_r = {k: project(s, r=r)["v"] for k, s in SCENARIOS.items()}
        sens[r] = weighted(v_r)
        print(f"r = {r:.0%}：" + "，".join(f"{k} {v_r[k]:.2f}" for k in v_r) + f"；加权 {sens[r]:.2f} 元；P/V {PRICE / sens[r]:.3f}")

    irr_base = irr_per_share(res["base"])
    print("\n=== 现价隐含回报与反向估值 ===")
    print(f"基准情景股利流（含终值）使现值等于现价的折现率：{irr_base:.2%}")
    for k in ("bear", "bull"):
        print(f"  {k} 情景隐含回报：{irr_per_share(res[k]):.2%}")
    x_star = bisect(lambda x: project(SCENARIOS["base"], roe_const=x)["v"] - PRICE, 0.04, 0.15)
    chk = project(SCENARIOS["base"], roe_const=x_star)
    print(f"现价隐含的 2027 年起恒定 ROE（期初普通股权益口径，g=2.5%，r=9%）：{x_star:.2%}，"
          f"折合平均权益口径约 {chk['rows'][0]['roe_avg']:.2%}")
    st = res["base"]["st"]
    bvps_ye = st["b_cum"] / st["n_post"]
    implied_pb = (PRICE - DPS_INTERIM) * (1 + COE) ** T0_TO_YE / bvps_ye
    print(f"增发后 2026 年末含息每股账面 {bvps_ye:.3f} 元；现价（除息并折到年末）对应 P/B {implied_pb:.3f}")

    print("\n=== 静态 P/B–ROE 核对：P/B = (ROE - g)/(r - g) ===")
    for k, s in SCENARIOS.items():
        pb = (s["roe_lr"] - G_TERMINAL) / (COE - G_TERMINAL)
        v_static = DPS_INTERIM + bvps_ye * pb / (1 + COE) ** T0_TO_YE
        print(f"{k}: 长期 ROE {s['roe_lr']:.1%} → P/B {pb:.3f} → 每股 {v_static:.2f} 元（含过渡期超额回报的完整模型 {vals[k]:.2f}）")

    print("\n=== 历史与同业交叉验证 ===")
    hist = {2013: (2.48, 2.60), 2014: (3.71, 3.05), 2015: (3.23, 3.48), 2016: (3.10, 3.81), 2017: (3.83, 4.15),
            2018: (3.60, 4.54), 2019: (3.69, 5.00), 2020: (3.14, 5.39), 2021: (2.94, 5.87), 2022: (2.91, 6.37),
            2023: (3.64, 6.88), 2024: (5.34, 7.40), 2025: (7.68, 7.91)}
    pbs = {y: c / b for y, (c, b) in hist.items()}
    srt = sorted(pbs.values())
    print("年末 P/B：" + "，".join(f"{y} {v:.2f}" for y, v in pbs.items()))
    print(f"2013-2025 区间 {srt[0]:.2f}–{srt[-1]:.2f}，中位数 {srt[len(srt) // 2]:.2f}；现价/2026H1 每股净资产 8.17 = {PRICE / 8.17:.2f}")
    ttm_ord = ORD_2025 - (PARENT_H1_2025 - 92.07) + ORD_H1_2026
    print(f"TTM 普通股东净利 {ttm_ord:.0f} 亿元，TTM 普通股 EPS {ttm_ord / N_OLD:.3f}，PE {PRICE / (ttm_ord / N_OLD):.1f}")
    print(f"过去 12 个月除息合计 0.2495 元，股息率 {0.2495 / PRICE:.2%}；2026 年每股股息（中期 0.1297 + 期末 "
          f"{st['final_div'] / st['n_post']:.4f}）= {DPS_INTERIM + st['final_div'] / st['n_post']:.4f} 元")
    print("同业（数据包腾讯字段）：工商银行 PB 0.77、PE(TTM) 8.19、股息率 3.61%；建设银行 PB 0.85、PE 8.74、3.36%；"
          "农业银行 PB 0.92、PE 8.80、3.33%；东财行业平均 PB 0.61")

    print("\n=== 敏感性（相对加权 V %.2f）===" % vw)
    for pi in (6.50, 8.00):
        v_p = weighted({k: project(s, p_issue=pi)["v"] for k, s in SCENARIOS.items()})
        print(f"增发价 {pi:.2f} 元：加权 V {v_p:.2f}")
    v_np = weighted({k: project(s, raise_amt=0.0)["v"] for k, s in SCENARIOS.items()})
    print(f"不计增发（同样增长、股本不变，仅作对照）：加权 V {v_np:.2f}")
    for lab, kw in (("净息差各年 -5bp", dict(nim_shift=-0.0005)), ("净息差各年 +5bp", dict(nim_shift=0.0005)),
                    ("信用成本各年 +10bp", dict(cc_shift=0.0010)), ("信用成本各年 -10bp", dict(cc_shift=-0.0010)),
                    ("普通股分红率 25%", dict(payout=0.25))):
        v_s = weighted({k: project(s, **kw)["v"] for k, s in SCENARIOS.items()})
        print(f"{lab}：加权 V {v_s:.2f}")

    print("\n=== 证伪条件触发后的独立 V ===")
    f1 = weighted(vals, {"bear": 0.5, "base": 0.5, "bull": 0.0})
    print(f"F1 三季报（10-31）前三季度归母同比 < +2% 或净息差 < 1.25%：概率改为 50/50/0 → V {f1:.2f}")
    f2 = project(SCENARIOS["base"], cc_shift=0.0010)["v"] * 0.6 + vals["bear"] * 0.4
    print(f"F2 2026 年报（2027-03-31）不良率 ≥ 1.32% 或个人经营贷不良率 ≥ 2.3%：基准信用成本 +10bp 占 60%、悲观 40% → V {f2:.2f}")
    f3 = weighted({k: project(s, nim_shift=-0.0005)["v"] for k, s in SCENARIOS.items()})
    print(f"F3 2027 中报（2027-08-31）上半年净息差 < 1.22%：各情景净息差 -5bp → V {f3:.2f}")
    f4 = weighted({"bear": vals["bear"], "base": project(SCENARIOS["base"], payout=0.25)["v"], "bull": vals["bull"]},
                  {"bear": 0.4, "base": 0.45, "bull": 0.15})
    print(f"F4 2026 年度现金分红 < 归母净利 30% 或增发后核心一级 < 10.5%：分红率 25%、概率 40/45/15 → V {f4:.2f}")

    print("\n=== 登记用摘要 ===")
    base_rows = res["base"]["rows"]
    prev = res["base"]["st"]["ord26"]
    growth = []
    for row in base_rows:
        growth.append(row["ord"] / prev - 1)
        prev = row["ord"]
    print("v_bear/base/bull:", [round(vals[k], 2) for k in ("bear", "base", "bull")],
          "v_weighted:", round(vw, 2), "pv:", round(pv, 3),
          "v_at_coe_8:", round(sens[0.08], 2), "v_at_coe_10:", round(sens[0.10], 2), "implied_irr:", round(irr_base, 4))
    print("normalized_parent_np_2026:", {k: round(normalized_2026(s)) for k, s in SCENARIOS.items()})
    print("基准普通股东净利增速 2027-2031:", [round(g, 4) for g in growth],
          "；再投资率", 1 - PAYOUT_ORD, "；平均 ROE(期初)", round(sum(r['roe_b'] for r in base_rows) / 5, 4))
    print(f"H 股 {H_PRICE_HKD} 港元（10-16），按 0.90–0.92 港元兑人民币约 {H_PRICE_HKD * 0.90:.2f}–{H_PRICE_HKD * 0.92:.2f} 元；"
          f"H 股价/加权 V ≈ {H_PRICE_HKD * 0.91 / vw:.2f}（同日 A 股 7.24）")


if __name__ == "__main__":
    main()
