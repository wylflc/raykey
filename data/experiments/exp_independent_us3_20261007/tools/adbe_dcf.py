# Final ADBE owner-earnings DCF. $bn unless noted. Valuation date 2026-10-06.
PRICE=238.12; SHARES=0.3892; MCAP=PRICE*SHARES
REV26=26.60; OE26=7.43; Q4STUB=1.88
ND_REP=6.40-5.64; OPCASH=1.5; ADJ_ND=ND_REP+OPCASH; T0=0.14
def scen(growth, margin, gT):
    rev=REV26; fl=[]
    for k,(g,m) in enumerate(zip(growth,margin),start=1):
        rev*=1+g; fl.append((T0+k-0.5, rev*m, rev, g, m))
    return fl, gT
def value(sc,r):
    fl,gT=sc; tT=T0+len(fl)
    pv=Q4STUB/(1+r)**(T0/2)+sum(cf/(1+r)**t for t,cf,*_ in fl)
    tv=fl[-1][1]*(1+gT)/(r-gT)/(1+r)**tT
    return (pv+tv-ADJ_ND)/SHARES, tv/(pv+tv)
S={
 'bear':scen([.06,.01,-.02,-.03,-.03,-.03,-.03,-.03,-.03,-.03],[.26,.245,.23,.22,.215,.21,.21,.21,.21,.21],-.02),
 'base':scen([.075,.07,.065,.06,.055,.05,.045,.04,.035,.03],[.275,.275,.28,.28,.28,.28,.28,.28,.28,.28],.02),
 'bull':scen([.09,.10,.10,.09,.08,.07,.06,.05,.04,.03],[.28,.29,.30,.305,.31,.31,.31,.31,.31,.31],.025),
}
PR={'bear':.35,'base':.50,'bull':.15}
for n,sc in S.items():
    fl,gT=sc
    print('%s: rev FY27 %.1f FY31 %.1f FY36 %.1f | OE FY27 %.2f FY31 %.2f FY36 %.2f | gT %.1f%%'%(n,fl[0][2],fl[4][2],fl[9][2],fl[0][1],fl[4][1],fl[9][1],gT*100))
    print('    V@8%% %.0f  V@9%% %.0f (TV %.0f%%)  V@10%% %.0f'%(value(sc,.08)[0],value(sc,.09)[0],100*value(sc,.09)[1],value(sc,.10)[0]))
for r in (.08,.09,.10):
    V=sum(PR[n]*value(S[n],r)[0] for n in S)
    print('weighted r=%.0f%%: V=%.1f  P/V=%.3f'%(r*100,V,PRICE/V))
for pr in [(.30,.50,.20),(.35,.50,.15),(.40,.45,.15),(.45,.45,.10)]:
    V=sum(p*value(S[n],.09)[0] for p,n in zip(pr,['bear','base','bull']))
    print('probs bear/base/bull %s -> V %.0f P/V %.2f'%(pr,V,PRICE/V))
def solve(f,lo,hi):
    for _ in range(200):
        mid=(lo+hi)/2
        if f(lo)*f(mid)<=0: hi=mid
        else: lo=mid
    return (lo+hi)/2
for n in S: print('IRR %s %.2f%%'%(n, 100*solve(lambda r: value(S[n],r)[0]-PRICE,S[n][1]+.001,.4)))
# probability-weighted IRR: rate at which weighted value equals price
print('IRR prob-weighted %.2f%%'%(100*solve(lambda r: sum(PR[n]*value(S[n],r)[0] for n in S)-PRICE,.026,.4)))
