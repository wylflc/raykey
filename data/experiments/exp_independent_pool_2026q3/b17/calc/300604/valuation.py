# -*- coding: utf-8 -*-
"""长川科技（300604）独立估值 — OI-291 b17（价格日 2026-10-21）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。口径说明：
- DCF 用经济口径（研发全额费用化、不计净利息、剔除一次性项目）的归母所有者收益，
  再投资 = 增量资本强度 κ × 收入增量（营运资金 + 固定资产/无形资产 + 补强并购），
  渐退期 κ 线性过渡到终值增量回报 ROIC_T 对应的 κ_T。
- 估值时点 2026-06-30（资产负债表日），年中折现：2026H2 在 t=0.25，2027 在 t=1，…，2036 在 t=10；
  终值在 t=10 处按 Gordon 计 2037 起的现金流；经营价值再按股权成本滚到 2026-10-21。
- 经调整净现金为正（含 2026-07-09 到账的定增净额），无杠杆口径：全额扣除有息负债。
- 少数股东：各年归母比例 = 1 − mi（长川制造 33.33% 已于 2026-07-23 完成过户，不再计少数）。
"""
from datetime import date

PRICE = 202.14
SHARES_TX = 6.48935494          # 归属结果公告：归属后总股本 648,935,494 股（=腾讯 6.4894 亿）
CANCEL_PENDING = 0.01638801     # 上市公告书第 8 页：拟回购注销限制性股票 1,638,801 股（尚未办妥注销）
SHARES = SHARES_TX - CANCEL_PENDING
COE = 0.09
T_ROLL = (date(2026, 10, 21) - date(2026, 6, 30)).days / 365.0
FADE = 5

# ---------------- 经调整净现金（2026-06-30 + 期后资本事项） ----------------
BRIDGE = [
    ('货币资金（2026H1 第 53 页）', 19.932),
    ('减：受限其他货币资金（信用证保证金、在途资金，第 24 页）', -0.627),
    ('减：经营备付（约 2026E 收入的 5%）', -4.0),
    ('加：2026-07-09 定增募资净额（上市公告书第 4 页）', 30.921),
    ('加：2024 激励计划归属认购款（归属结果公告，2026-09-05 到账）', 0.528),
    ('减：已宣派 2026 中期股利（每 10 股 1 元）', -0.647),
    ('减：短期借款（第 54 页）', -7.966),
    ('减：长期借款（含一年内到期 4.415，第 55、134 页）', -21.683),
    ('减：实际控制人之一徐昕暂借款（第 131、170 页）', -1.000),
]
NET_CASH = sum(v for _, v in BRIDGE)
LEASE = 0.354                   # 租赁负债（含一年内到期）只列示不扣：起点为净利润
NON_OP = 0.798 + 0.400          # 其他权益工具投资 + 其他非流动金融资产
MI_BOOK_AFTER = 6.646 - 3.302   # 少数股东权益扣除长川制造 33.33% 后（仅列示）

# ---------------- 2026 正常化（报表口径 ↔ 经济口径） ----------------
REV_2026E = 79.0                # H1 34.61 + H2E 44.4（Q3E 约 22、Q4E 约 22.4）
NP_2026E_REPORTED = 21.5        # H1 9.64 + H2E 11.9（券商口径 20.5～22.0）
NET_CAP_AFTER_TAX = 2.8         # 2026E 资本化研发约 3.6 − 已资本化项目摊销约 0.3，按 15% 税
NET_INTEREST_AFTER_TAX = -0.13  # 定增后毛现金约 50 亿 ×1.2% − 有息负债 30.65 亿 ×2.4%

SCEN = {
    'bear': dict(p=0.25, rev0=REV_2026E * 0.80, g=[0.06, 0.09, 0.08, 0.07, 0.06], gt=0.020,
                 m0=0.195, m5=0.200, tax=[0.09, 0.09, 0.11, 0.12, 0.12, 0.12], tax_t=0.12,
                 mi=0.03, kappa=0.75, roic_t=0.12),
    'base': dict(p=0.50, rev0=REV_2026E * 0.92, g=[0.15, 0.14, 0.12, 0.10, 0.09], gt=0.025,
                 m0=0.235, m5=0.255, tax=[0.07, 0.07, 0.095, 0.105, 0.105, 0.105], tax_t=0.11,
                 mi=0.02, kappa=0.62, roic_t=0.20),
    'bull': dict(p=0.25, rev0=REV_2026E * 1.00, g=[0.25, 0.20, 0.17, 0.14, 0.12], gt=0.025,
                 m0=0.250, m5=0.280, tax=[0.06, 0.06, 0.09, 0.10, 0.10, 0.10], tax_t=0.105,
                 mi=0.015, kappa=0.55, roic_t=0.25),
}


def build(s):
    """返回 2026..2036 的收入、经济口径归母净利、再投资、所有者收益。"""
    gs = list(s['g'])
    for k in range(1, FADE + 1):
        gs.append(gs[4] + (s['gt'] - gs[4]) * k / FADE)
    n = len(gs) + 1                                  # 11 年：2026..2036
    rev = [s['rev0']]
    for g in gs:
        rev.append(rev[-1] * (1 + g))
    m = [s['m0'] + (s['m5'] - s['m0']) * min(i, 5) / 5 for i in range(n)]
    tax = [s['tax'][i] if i <= 5 else s['tax_t'] for i in range(n)]
    np_ = [rev[i] * m[i] * (1 - tax[i]) * (1 - s['mi']) for i in range(n)]
    nopat_m_t = s['m5'] * (1 - s['tax_t'])
    kappa_t = nopat_m_t / s['roic_t']
    reinv = []
    for i in range(n):
        if i < n - 1:
            k = i - 4                                # i=5 起为渐退期第 1 年
            kap = s['kappa'] if k <= 0 else s['kappa'] + (kappa_t - s['kappa']) * k / FADE
            reinv.append(kap * (rev[i + 1] - rev[i]) * (1 - s['mi']))
        else:
            reinv.append(np_[i] * (1 + s['gt']) * s['gt'] / s['roic_t'])
    oe = [np_[i] - reinv[i] for i in range(n)]
    return dict(g=gs, rev=rev, m=m, tax=tax, np=np_, reinv=reinv, oe=oe, kappa_t=kappa_t)


def value(s, r=COE, growth_override=None):
    s = dict(s)
    if growth_override is not None:
        s['g'] = growth_override[:5]
    b = build(s)
    if growth_override is not None:              # 反向 DCF：10 年统一增速
        b['g'] = growth_override
        rev = [s['rev0']]
        for g in growth_override:
            rev.append(rev[-1] * (1 + g))
        n = len(rev)
        m = [s['m0'] + (s['m5'] - s['m0']) * min(i, 5) / 5 for i in range(n)]
        tax = [s['tax'][i] if i <= 5 else s['tax_t'] for i in range(n)]
        np_ = [rev[i] * m[i] * (1 - tax[i]) * (1 - s['mi']) for i in range(n)]
        reinv = [s['kappa'] * (rev[i + 1] - rev[i]) * (1 - s['mi']) for i in range(n - 1)]
        reinv.append(np_[-1] * (1 + s['gt']) * s['gt'] / s['roic_t'])
        b.update(rev=rev, np=np_, reinv=reinv, oe=[np_[i] - reinv[i] for i in range(n)])
    pv = 0.0
    for i, oe in enumerate(b['oe']):
        cf, t = (0.5 * oe, 0.25) if i == 0 else (oe, float(i))
        pv += cf / (1 + r) ** t
    np_next = b['np'][-1] * (1 + s['gt'])
    tv = np_next * (1 - s['gt'] / s['roic_t']) / (r - s['gt'])
    pv_tv = tv / (1 + r) ** (len(b['oe']) - 1)
    ops = (pv + pv_tv) * (1 + r) ** T_ROLL
    eq = ops + NET_CASH + NON_OP
    return dict(v=eq / SHARES, eq=eq, ops=ops, pv=pv, pv_tv=pv_tv, b=b)


def weighted(r=COE, probs=None):
    probs = probs or {k: s['p'] for k, s in SCEN.items()}
    return sum(probs[k] * value(SCEN[k], r)['v'] for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def normalized_np_2026(s):
    b = build(s)
    econ = b['np'][0]
    return econ, econ + NET_CAP_AFTER_TAX + NET_INTEREST_AFTER_TAX


if __name__ == '__main__':
    print(f'估值股本 {SHARES:.4f} 亿股（腾讯 {SHARES_TX:.4f} − 拟注销 {CANCEL_PENDING:.4f}）；滚动 {T_ROLL:.3f} 年')
    print('经调整净现金（无杠杆口径）：')
    for name, v in BRIDGE:
        print(f'   {v:8.3f}  {name}')
    print(f'   = {NET_CASH:.2f} 亿；非经营资产 {NON_OP:.2f}；租赁负债 {LEASE:.2f}（只列示）；'
          f'扣长川制造后少数股东权益账面 {MI_BOOK_AFTER:.2f}')

    print('\n2026 正常化归母净利（经济口径 / 报表口径，含净利息、剔除一次性）：')
    for k, s in SCEN.items():
        e, rpt = normalized_np_2026(s)
        print(f'   {k}: 经济 {e:.2f}  报表 {rpt:.2f}  （正常化收入 {s["rev0"]:.1f}）')
    e_b, r_b = normalized_np_2026(SCEN['base'])
    print(f'   参照：2026E 报表归母约 {NP_2026E_REPORTED:.1f}，基准正常化差额 {r_b - NP_2026E_REPORTED:+.2f}')

    res = {k: value(s) for k, s in SCEN.items()}
    vw = weighted()
    print('\n三情景：')
    for k, s in SCEN.items():
        d = res[k]
        tvs = d['pv_tv'] / (d['pv'] + d['pv_tv'])
        print(f'   {k}: V = {d["v"]:.2f} 元（p={s["p"]:.2f}；股权 {d["eq"]:.1f} 亿；终值占经营价值 {tvs:.1%}；'
              f'κ={s["kappa"]:.2f}→κ_T={d["b"]["kappa_t"]:.2f}）')
        b = d['b']
        print('      年份   收入   经济归母   再投资   所有者收益   收入增速')
        for i in range(len(b['rev'])):
            g = b['g'][i - 1] if i > 0 else float('nan')
            print(f'      {2026 + i}  {b["rev"][i]:7.1f}  {b["np"][i]:7.2f}  {b["reinv"][i]:7.2f}  '
                  f'{b["oe"][i]:7.2f}   {g:6.1%}')
    print(f'\n加权 V = {vw:.2f} 元；P/V = {PRICE / vw:.2f}')
    for r in (0.08, 0.10):
        print(f'   股权成本 {r:.0%}: 加权 V = {weighted(r):.2f} 元（熊 {value(SCEN["bear"], r)["v"]:.2f} / '
              f'基准 {value(SCEN["base"], r)["v"]:.2f} / 牛 {value(SCEN["bull"], r)["v"]:.2f}）')

    irr = solve(lambda r: value(SCEN['base'], r)['v'], 0.03, 0.09, PRICE)
    print(f'现价隐含回报（基准情景现金流）：{irr:.2%}')
    irr_bull = solve(lambda r: value(SCEN['bull'], r)['v'], 0.03, 0.09, PRICE)
    print(f'   牛市情景现金流下的隐含回报：{irr_bull:.2%}')

    g_rev = solve(lambda g: value(SCEN['base'], COE, [g] * 10)['v'], 0.05, 0.60, PRICE)
    d_rev = value(SCEN['base'], COE, [g_rev] * 10)
    print(f'反向 DCF：基准利润率与资本强度下，现价隐含 2027–2036 收入年增 {g_rev:.1%}，'
          f'2036 收入 {d_rev["b"]["rev"][-1]:.0f} 亿、经济归母 {d_rev["b"]["np"][-1]:.0f} 亿')
    oe27 = res['base']['b']['oe'][1]
    ev_ops = PRICE * SHARES - NET_CASH - NON_OP
    g_perp = COE - oe27 / (ev_ops / (1 + COE) ** T_ROLL)
    print(f'   以 2027 基准所有者收益 {oe27:.1f} 亿计的现价隐含永续增速 {g_perp:.1%}')

    # 增长路径（基准，所有者收益）
    b = res['base']['b']
    oe_g = [b['oe'][i] / b['oe'][i - 1] - 1 for i in range(1, 6)]
    rr = sum(b['reinv'][1:6]) / sum(b['np'][1:6])
    roic_inc = SCEN['base']['m5'] * (1 - SCEN['base']['tax'][5]) * (1 - SCEN['base']['mi']) / SCEN['base']['kappa']
    print('基准所有者收益增速 2027–2031：', ' '.join(f'{x:.1%}' for x in oe_g),
          f'；再投资率 {rr:.1%}；增量回报 {roic_inc:.1%}')

    # 交叉验证
    bvps = (56.30 + 30.921 + 0.528 - 0.647 - (4.629 - 3.302)) / SHARES
    print(f'\n交叉验证：调整后每股归母净资产 {bvps:.2f} 元，现价 PB {PRICE / bvps:.1f}×，加权 V 对应 PB {vw / bvps:.1f}×')
    print(f'   现价 / 2026 基准正常化归母（报表） = {PRICE * SHARES / r_b:.1f}×；加权 V 对应 {vw * SHARES / r_b:.1f}×')
    ev_mkt = PRICE * SHARES - NET_CASH - NON_OP + MI_BOOK_AFTER
    ebit26 = 22.0
    print(f'   EV/EBIT(2026E 约 {ebit26:.0f} 亿)：现价 {ev_mkt / ebit26:.0f}×；加权 V {(vw * SHARES - NET_CASH - NON_OP + MI_BOOK_AFTER) / ebit26:.0f}×')
    print(f'   股息+回购收益率：每股年股息约 0.20 元 → {0.20 / PRICE:.2%}；提议回购 0.5～1.0 亿 → '
          f'{0.5 / (PRICE * SHARES):.2%}～{1.0 / (PRICE * SHARES):.2%}')

    # H 股：不超过发行后总股本 15%（超额配售前），另有 15% 超额配售
    print('\nH 股影响（未完成，按现有股本估值；以下为情景测算，发行费 3%）：')
    for share_pct, label in ((0.15, '15%'), (0.15 * 1.15 / (1 + 0.15 * 0.15), '含超额配售约 16.9%')):
        nh = SHARES * share_pct / (1 - share_pct)
        for disc in (0.0, 0.20, 0.40):
            ph = PRICE * (1 - disc) * 0.97
            v_new = (vw * SHARES + nh * ph) / (SHARES + nh)
            print(f'   {label}：新增 {nh:.3f} 亿股，H 股价较 A 股折让 {disc:.0%} → 加权 V {v_new:.2f} 元'
                  f'（每股收益摊薄 {nh / (SHARES + nh):.1%}）')

    # 证伪条件触发后的独立 V
    print('\n证伪触发后的 V：')
    cases = {
        'F1 2026Q3 收入<19 亿或归母<5.0 亿': {'bear': 0.45, 'base': 0.45, 'bull': 0.10},
        'F2 2026 年报存货>55 亿且经营现金流<6 亿': {'bear': 0.50, 'base': 0.50, 'bull': 0.00},
        'F3 2027H1 收入同比为负（<34.6 亿）': {'bear': 0.60, 'base': 0.40, 'bull': 0.00},
        'F4 2027 归母≥35 亿且经营现金流/净利≥70%': {'bear': 0.00, 'base': 0.50, 'bull': 0.50},
        'F5 关键零部件或第一大客户受新出口管制': {'bear': 1.00, 'base': 0.00, 'bull': 0.00},
    }
    for name, pr in cases.items():
        print(f'   {name}: V = {weighted(COE, pr):.2f} 元')
    # 基准情景单项敏感性（其余输入不变）
    print('\n基准 V 单项敏感性：')
    sens = {
        '不做周期折扣（2026 收入 79 即趋势）': dict(rev0=REV_2026E),
        '增量资本强度 κ 0.62→0.50': dict(kappa=0.50),
        '终值增量回报 20%→30%': dict(roic_t=0.30),
        '2031 起经济口径税前利润率 25.5%→28%': dict(m5=0.28),
        '2027–2031 收入增速各 +5 个百分点': dict(g=[x + 0.05 for x in SCEN['base']['g']]),
    }
    for name, upd in sens.items():
        s2 = dict(SCEN['base']); s2.update(upd)
        print(f'   {name}: {value(s2)["v"]:.2f} 元')
    s_all = dict(SCEN['base']); s_all.update(rev0=REV_2026E, kappa=0.50, roic_t=0.30, m5=0.28,
                                             g=[x + 0.05 for x in SCEN['base']['g']])
    print(f'   以上五项同时取乐观值: {value(s_all)["v"]:.2f} 元')
    # 近端周期高点：2026H2–2027 按一致预期（2027 报表归母约 32 亿、收入约 105 亿）兑现、2028 回到基准趋势
    b0 = res['base']['b']
    kap = SCEN['base']['kappa']
    h2_excess = (11.9 - 1.45) - 0.5 * b0['np'][0]          # 2026H2E 经济口径归母 − 基准正常化半年
    y27_excess = (32.0 - 3.0) - b0['np'][1]                 # 2027 一致预期折经济口径 − 基准趋势
    wc_tied = kap * (105.0 - b0['rev'][1])                  # 超额收入占用的资本，2028 回到趋势时释放
    pv_hump = (h2_excess / (1 + COE) ** 0.25 + y27_excess / (1 + COE) ** 1
               - wc_tied / (1 + COE) ** 0.5 + wc_tied / (1 + COE) ** 2) * (1 + COE) ** T_ROLL
    print(f'   近端周期高点按一致预期兑现（2027 归母约 32 亿）后 2028 回到趋势：基准 V {value(SCEN["base"])["v"]:.2f}'
          f' → {(res["base"]["eq"] + pv_hump) / SHARES:.2f} 元（增量现金流现值 {pv_hump:.1f} 亿）')

    print('\n分档价格（V 不变）：≤0.75 明显低估 ≤ {:.2f}；0.75～0.90 温和低估 ≤ {:.2f}；0.90～1.10 大致合理 ≤ {:.2f}；>1.10 偏贵'
          .format(vw * 0.75, vw * 0.90, vw * 1.10))
