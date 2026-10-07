# VIPS independent valuation - reproducible calculations (RMB bn unless noted)
FX = 6.7046          # USD/CNY, ECB 2026-10-06
PRICE = 12.75        # USD/ADS, 2026-10-06 close
ADS = 475.5          # m ADS (95.1m ordinary shares x5, 2026-06-30)
MCAP = PRICE * ADS * FX / 1000  # RMB bn
OPT_ADS, OPT_K = 26.66, 66.85 / 5   # founders' vested options (5.333m shares) strike US$/ADS

# ---- balance sheet 2026-06-30 (Q2 release) ----
cash, sti, htm, restricted = 29.246, 3.618, 0.806, 0.605
st_loans = 10.968
wht_payable = 1.56          # historical-dividend WHT, to be paid in Q3 2026 (CFO)
shanshan_cash_sbc = 1.70    # cash-settled Shan Shan awards liability (1.628 at 2025-12-31), est.
nci_loans = 0.16            # loans from NCI shareholders (0.1595 at 2025-12-31)
fin_net = cash + sti + htm - st_loans
net_after_quasi = fin_net - wht_payable - shanshan_cash_sbc - nci_loans
reit2_mkt = 0.49 * 1999.9968 * 3.841 / 1000       # 508603 close 2026-09-30
other_inv = (7.616 - 0.49 * 7.696) + 4.981        # equity-method ex REIT2 + other investments
NCI = 3.6                                          # book 3.345 + REIT1 outside units at market

def realization(k, years=5, cash_yield=0.015, wht=0.10):
    # cash distributed evenly over `years`, earning cash_yield meanwhile, then 10% WHT
    return (1 - wht) * sum(((1 + cash_yield) / (1 + k)) ** t for t in range(1, years + 1)) / years

def nonop(k, float_reserve, rf, reit_f, inv_f):
    adj_cash = net_after_quasi - float_reserve
    return adj_cash * rf + reit2_mkt * reit_f + other_inv * inv_f - NCI, adj_cash

def oe_path(oe1, g_early, g_late):
    path = [oe1]
    for g in g_early: path.append(path[-1] * (1 + g))
    for g in g_late: path.append(path[-1] * (1 + g))
    return path  # 10 years

def dcf(path, k, g_term):
    pv = sum(cf / (1 + k) ** t for t, cf in enumerate(path, 1))
    tv = path[-1] * (1 + g_term) / (k - g_term)
    return pv + tv / (1 + k) ** len(path)

def per_ads(equity_rmb):
    v = equity_rmb / FX / ADS * 1000
    dil = max(0.0, v - OPT_K) * OPT_ADS / (ADS + OPT_ADS)
    return v - dil

SC = {
 'bear': dict(oe1=5.08, ge=[-0.124]*4, gl=[-0.03]*5, gt=-0.03, fr=8.0, rf=0.50, reit=0.70, inv=0.35, p=0.35),
 'base': dict(oe1=5.70, ge=[-0.04, -0.04, -0.02, -0.02], gl=[0.0]*5, gt=0.0, fr=5.5, rf=None, reit=0.80, inv=0.50, p=0.50),
 'bull': dict(oe1=6.00, ge=[0.03]*4, gl=[0.02]*5, gt=0.02, fr=4.0, rf=0.80, reit=0.90, inv=0.60, p=0.15),
}

def scenario(name, k=0.10):
    s = SC[name]
    path = oe_path(s['oe1'], s['ge'], s['gl'])
    core = dcf(path, k, s['gt'])
    rf = s['rf'] if s['rf'] is not None else realization(k)
    no, adj_cash = nonop(k, s['fr'], rf, s['reit'], s['inv'])
    return dict(path=path, core=core, nonop=no, adj_cash=adj_cash, rf=rf, eq=core + no, v=per_ads(core + no))

print(f"MCAP RMB {MCAP:.2f}bn = US${PRICE*ADS/1000:.3f}bn")
print(f"fin_net {fin_net:.2f}  net_after_quasi {net_after_quasi:.2f}  REIT2 mkt {reit2_mkt:.3f}  other_inv {other_inv:.3f}")
for k in (0.09, 0.10, 0.11, 0.12):
    res = {n: scenario(n, k) for n in SC}
    V = sum(SC[n]['p'] * res[n]['v'] for n in SC)
    line = '  '.join(f"{n}: core {res[n]['core']:.2f} nonop {res[n]['nonop']:.2f} rf {res[n]['rf']:.3f} V ${res[n]['v']:.2f}" for n in SC)
    print(f"k={k:.0%}  {line}  | weighted V ${V:.2f}  P/V {PRICE/V:.3f}")
b = scenario('base')
print('base OE path', [round(x, 3) for x in b['path']], 'adj_cash', round(b['adj_cash'], 2))
print('base nonop per ADS $', round(b['nonop'] / FX / ADS * 1000, 2), ' OE1 per ADS $', round(5.70 / FX / ADS * 1000, 3))

# ---- reverse DCF at 10% ----
core_mkt = MCAP - b['nonop']
print(f"market-implied core value {core_mkt:.2f}bn -> P/OE1 {core_mkt/5.70:.2f}x; implied perpetual g = {0.10 - 5.70/core_mkt:.2%}")
lo, hi = -0.5, 0.2
for _ in range(200):
    mid = (lo + hi) / 2
    path = [5.70 * (1 + mid) ** t for t in range(10)]
    if dcf(path, 0.10, 0.0) > core_mkt: hi = mid
    else: lo = mid
print(f"implied 10y OE CAGR (terminal g=0 after y10): {mid:.2%}")

# ---- IRR on base path, nonop fixed at base value ----
lo, hi = 0.05, 0.60
for _ in range(200):
    r = (lo + hi) / 2
    val = dcf(b['path'], r, 0.0) + b['nonop']
    if val > MCAP: lo = r
    else: hi = r
print(f"base-case implied IRR: {r:.2%}")
# IRR if non-operating assets get zero credit
lo, hi = 0.05, 0.60
for _ in range(200):
    r2 = (lo + hi) / 2
    if dcf(b['path'], r2, 0.0) > MCAP: lo = r2
    else: hi = r2
print(f"IRR with zero credit for net cash/investments: {r2:.2%}")

# ---- cross checks ----
ttm_ngni = 1501.489 + 2858.031 + 2305.623 + 392.213
ttm_sbc = 346.352 + 336.254 + 220.645 + 486.514
print(f"TTM non-GAAP NI {ttm_ngni/1000:.3f}bn, +WHT one-off -> {(ttm_ngni+1560)/1000:.3f}; TTM SBC {ttm_sbc/1000:.3f}; GAAP ex one-offs {(ttm_ngni+1560-ttm_sbc)/1000:.3f}")
ttm_fcf = 7.201751
print(f"TTM FCF-SBC {ttm_fcf - ttm_sbc/1000:.3f}; ex after-tax interest (0.56) {ttm_fcf - ttm_sbc/1000 - 0.56:.3f}; x0.9 {0.9*(ttm_fcf - ttm_sbc/1000 - 0.56):.3f}; +REIT tax 1.63 x0.9 {0.9*(ttm_fcf - ttm_sbc/1000 - 0.56 + 1.63):.3f}")
ret = {2023: (5.107, 0, 9.510), 2024: (3.866, 1.685, 9.033), 2025: (4.941, 1.795, 8.745)}
for y, (bb, dv, ng) in ret.items(): print(y, f"returns {bb+dv:.3f}bn = {100*(bb+dv)/ng:.1f}% of non-GAAP NI")
print('3y', f"{100*sum(a+b_ for a, b_, _ in ret.values())/sum(n for *_, n in ret.values()):.1f}%")
target26 = 0.75 * 8.745
print(f"2026 target >= RMB {target26:.2f}bn = US${target26/FX:.3f}bn; H2 needed ~US${target26/FX-0.40:.3f}bn = {100*(target26/FX-0.40)/(PRICE*ADS/1000):.1f}% of mcap")
ev_simple = MCAP - (fin_net - wht_payable) - (7.616 + 4.981) + 3.345
print(f"EV simple {ev_simple:.2f}bn -> EV/EBIT(TTM 8.179) {ev_simple/8.179:.2f}x")
ev_adj = MCAP - (net_after_quasi - 5.5) - (reit2_mkt*0.8 + other_inv*0.5) + NCI
print(f"EV adjusted {ev_adj:.2f}bn -> EV/EBIT {ev_adj/8.179:.2f}x; EV/core EBIT 2027E 7.6 {ev_adj/7.6:.2f}x")
