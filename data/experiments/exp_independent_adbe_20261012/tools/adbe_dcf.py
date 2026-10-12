# ADBE owner-earnings DCF, independent re-check of 2026-10-12. $bn unless noted.
# Price date 2026-10-09 (US close). Based on exp_independent_us3_20261007/tools/adbe_dcf.py;
# changes: price/date, Q4 stub, post-balance-sheet cash uses in net debt, a fourth (stress)
# scenario, new probabilities, reverse-DCF block.
PRICE = 242.27
SHARES = 0.3892            # bn, 10-Q cover, 2026-09-18
MCAP = PRICE * SHARES
REV26 = 26.60              # FY26 guidance midpoint
OE26 = 7.43                # FY26E GAAP net income ex one-offs (27.9% of revenue)
Q4STUB = 1.85              # Q4 GAAP EPS guide 4.675 x 0.389 = 1.82, plus after-tax acquisition costs
ND_REP = 6.40 - 5.64       # debt face (notes 6.15 + CP 0.25) less cash and ST investments, 2026-08-28
OPCASH = 1.5               # operating cash reserve
TOPAZ = 0.34               # Topaz Labs cash consideration, closed 2026-09-23 (after balance-sheet date)
BUYBACK_GAP = 0.47         # buybacks 08-29..09-18: (391.0 - 389.2)m shares x ~262 USD average close
ADJ_ND = ND_REP + OPCASH + TOPAZ + BUYBACK_GAP
ADJ_ND_OLD = ND_REP + OPCASH                    # 10-07 review basis
T0 = 49 / 365              # 2026-10-09 -> FY26 year-end 2026-11-27


def scen(growth, margin, gT):
    rev = REV26
    fl = []
    for k, (g, m) in enumerate(zip(growth, margin), start=1):
        rev *= 1 + g
        fl.append((T0 + k - 0.5, rev * m, rev, g, m))
    return fl, gT


def value(sc, r, nd=None, stub=None, t0=None):
    fl, gT = sc
    nd = ADJ_ND if nd is None else nd
    stub = Q4STUB if stub is None else stub
    pv = stub / (1 + r) ** (T0 / 2) + sum(cf / (1 + r) ** t for t, cf, *_ in fl)
    tv = fl[-1][1] * (1 + gT) / (r - gT) / (1 + r) ** (T0 + len(fl))
    return (pv + tv - nd) / SHARES, tv / (pv + tv)


def solve(f, lo, hi):
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


S = {
    # clone-and-commoditization shock: worse than bear (see report section 5)
    'stress': scen([.03, -.035, -.07, -.07, -.06, -.05, -.04, -.04, -.03, -.03],
                   [.25, .22, .19, .17, .16, .15, .15, .15, .15, .15], -.03),
    # bear/base/bull paths unchanged from the 10-07 review
    'bear': scen([.06, .01, -.02, -.03, -.03, -.03, -.03, -.03, -.03, -.03],
                 [.26, .245, .23, .22, .215, .21, .21, .21, .21, .21], -.02),
    'base': scen([.075, .07, .065, .06, .055, .05, .045, .04, .035, .03],
                 [.275, .275, .28, .28, .28, .28, .28, .28, .28, .28], .02),
    'bull': scen([.09, .10, .10, .09, .08, .07, .06, .05, .04, .03],
                 [.28, .29, .30, .305, .31, .31, .31, .31, .31, .31], .025),
}
PR = {'stress': .05, 'bear': .37, 'base': .45, 'bull': .13}
PR_OLD = {'stress': 0, 'bear': .35, 'base': .50, 'bull': .15}
assert abs(sum(PR.values()) - 1) < 1e-9


def wv(pr, r=.09, **kw):
    return sum(p * value(S[n], r, **kw)[0] for n, p in pr.items())


print('inputs: price %.2f  shares %.4fbn  mcap %.2fbn  adj net debt %.2fbn (%.2f USD/share)  T0 %.3f'
      % (PRICE, SHARES, MCAP, ADJ_ND, ADJ_ND / SHARES, T0))
print('\n== scenarios ==')
for n, sc in S.items():
    fl, gT = sc
    print('%-6s p=%2.0f%% | rev FY27 %.1f FY31 %.1f FY36 %.1f | OE FY27 %.2f FY31 %.2f FY36 %.2f | gT %+.1f%%'
          % (n, PR[n] * 100, fl[0][2], fl[4][2], fl[9][2], fl[0][1], fl[4][1], fl[9][1], gT * 100))
    print('       V@8%% %.0f  V@9%% %.0f (TV %.0f%%)  V@10%% %.0f | price vs V@9%%: %+.0f%% | P/V %.2f'
          % (value(sc, .08)[0], value(sc, .09)[0], 100 * value(sc, .09)[1], value(sc, .10)[0],
             100 * (value(sc, .09)[0] / PRICE - 1), PRICE / value(sc, .09)[0]))

print('\n== probability-weighted V and P/V ==')
for r in (.08, .09, .10):
    V = wv(PR, r)
    print('r=%.0f%%: V=%.1f  P/V=%.3f' % (r * 100, V, PRICE / V))
print('base-case terminal growth 1.5/2.0/2.5%%: %s'
      % ' / '.join('%.0f' % value((S['base'][0], g), .09)[0] for g in (.015, .02, .025)))

print('\n== bridge from the 10-07 review (V 304.4 at 238.12) ==')
v_old_inputs = sum(PR_OLD[n] * value(S[n], .09, nd=ADJ_ND_OLD, stub=1.88)[0] for n in PR_OLD if PR_OLD[n])
v_new_tech = wv({k: v for k, v in PR_OLD.items() if v})
v_new = wv(PR)
print('old probabilities, old net debt/stub, new date: %.1f' % v_old_inputs)
print('old probabilities, new net debt/stub          : %.1f  (technical %+.1f)' % (v_new_tech, v_new_tech - v_old_inputs))
print('new probabilities incl. stress                : %.1f  (probabilities %+.1f)' % (v_new, v_new - v_new_tech))
print('P/V at old V 304.4 and new price: %.3f' % (PRICE / 304.4))

print('\n== probability sensitivity (stress/bear/base/bull, r=9%) ==')
for pr in [(0, .35, .50, .15), (.05, .35, .47, .13), (.05, .37, .45, .13), (.05, .40, .42, .13),
           (.10, .35, .42, .13), (.10, .40, .40, .10), (.05, .45, .40, .10), (.15, .37, .38, .10),
           (.20, .35, .35, .10), (0, .30, .50, .20)]:
    V = sum(p * value(S[n], .09)[0] for p, n in zip(pr, ['stress', 'bear', 'base', 'bull']))
    print('%s -> V %.0f  P/V %.2f' % ('/'.join('%.0f' % (100 * p) for p in pr), V, PRICE / V))
vs, vb, vm, vu = (value(S[n], .09)[0] for n in ('stress', 'bear', 'base', 'bull'))
for target in (0.75, 0.90, 1.00, 1.10):
    # hold stress 5% and bull 13%; bear absorbs from base
    need = PRICE / target
    pb = (0.05 * vs + 0.13 * vu + 0.82 * vm - need) / (vm - vb)
    print('P/V = %.2f needs bear probability %.0f%% (stress 5%%, bull 13%% fixed; adverse total %.0f%%)'
          % (target, 100 * pb, 100 * pb + 5))

print('\n== implied IRR at %.2f ==' % PRICE)
for n in S:
    print('IRR %-6s %.2f%%' % (n, 100 * solve(lambda r: value(S[n], r)[0] - PRICE, max(S[n][1], -0.05) + .0015, .4)))
print('IRR prob-weighted %.2f%%' % (100 * solve(lambda r: wv(PR, r) - PRICE, .026, .4)))

print('\n== reverse DCF at %.2f (r=9%%) ==' % PRICE)
r = .09
ev = MCAP + ADJ_ND
stub_pv = Q4STUB / (1 + r) ** (T0 / 2)
oe27 = S['base'][0][0][1]
# growing perpetuity from FY27E base OE, mid-year convention
g_imp = solve(lambda g: stub_pv + oe27 * (1 + r) ** (0.5 - T0) / (r - g) - ev, -.5, .0899)
print('mcap %.2f + adj net debt %.2f = %.2f; FY27E base OE %.2f -> implied perpetual growth %.2f%%'
      % (MCAP, ADJ_ND, ev, oe27, 100 * g_imp))


def flat_path(c, gT):
    fl = [(T0 + k - 0.5, OE26 * (1 + c) ** k) for k in range(1, 11)]
    pv = stub_pv + sum(cf / (1 + r) ** t for t, cf in fl)
    return pv + fl[-1][1] * (1 + gT) / (r - gT) / (1 + r) ** (T0 + 10) - ev


for gT in (.025, 0.0):
    print('implied 10y OE CAGR from FY26 %.2f, terminal %.1f%%: %.2f%%'
          % (OE26, 100 * gT, 100 * solve(lambda c: flat_path(c, gT), -.3, .3)))
stag = scen([.04, .035, .03, .025, .02, .015, .01, .01, .01, .01], [.26] * 10, 0.0)
print('stagnation path (rev +4%%..+1%%, OE margin 26%%, terminal 0%%): V %.0f' % value(stag, r)[0])
w = (vm - PRICE) / (vm - vb)
print('two-state mix of bear %.0f and base %.0f that equals price: bear weight %.0f%%' % (vb, vm, 100 * w))
print('our adverse weight (stress+bear): %.0f%%' % (100 * (PR['stress'] + PR['bear'])))

print('\n== cross-checks at %.2f ==' % PRICE)
print('FY26E OE yield %.1f%%; GAAP PE on FY26E EPS 18.145: %.1f; non-GAAP PE on 24.475: %.1f'
      % (100 * OE26 / MCAP, PRICE / 18.145, PRICE / 24.475))
print('TTM FCF-SBC 8.52 yield %.1f%%; TTM buyback 9.30 yield %.1f%%' % (100 * 8.52 / MCAP, 100 * 9.30 / MCAP))
