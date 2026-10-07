FX=6.7046; ADS=1473.5  # million diluted ADS (5,894m diluted shares / 4)
PX=78.40
NFA=429.0   # RMB bn: cash+restricted+ST inv+other non-current (deposits/bonds)+payment receivables - ALL liabilities, 2026-06-30
WHT=15.0    # RMB bn: 10% withholding on ~150bn China-held undistributed earnings
def oe0(ebit=95.3,tax=0.21,drag=3.0,reinv=0.05):
    return (ebit*(1-tax)-drag)*(1-reinv)
def path(g_list, n_fade_from, g_term, years=10):
    # g_list: explicit growth for first len(g_list) years; then linear fade to g_term over remaining years
    gs=list(g_list)
    rem=years-len(gs)
    if rem>0:
        start=gs[-1] if n_fade_from is None else n_fade_from
        for i in range(1,rem+1):
            gs.append(start+(g_term-start)*i/rem)
    return gs
def dcf(oe_start, gs, g_term, k):
    pv=0; oe=oe_start; flows=[]
    for t,g in enumerate(gs, start=1):
        oe=oe*(1+g); flows.append(oe); pv+=oe/(1+k)**t
    tv=oe*(1+g_term)/(k-g_term); pv_tv=tv/(1+k)**len(gs)
    return pv, pv_tv, flows, tv
def cash_value(real, xp_haircut):
    return max(NFA-WHT-xp_haircut,0)*real
def per_ads(rmb_bn): return rmb_bn/FX*1000/ADS  # RMB bn -> USD/ADS
OE0=oe0()
print(f"OE0 (2026E run-rate) RMB bn {OE0:.2f} = ${OE0/FX:.2f}bn = ${per_ads(OE0):.2f}/ADS")
SC={
 'bear':dict(p=0.35, gs=path([-0.10,-0.08,-0.05,0,0],0.0,-0.01), gt=-0.01, real=0.40, xp=85.0, oe0=oe0(ebit=90.0,drag=5.0)),
 'base':dict(p=0.50, gs=path([0.04]*5,0.04,0.025), gt=0.025, real=0.60, xp=50.0, oe0=OE0),
 'bull':dict(p=0.15, gs=path([0.09]*5,0.09,0.025), gt=0.025, real=0.80, xp=0.0, oe0=oe0(ebit=97.0,drag=2.0)),
}
res={}
for name,s in SC.items():
    out={}
    for k in (0.09,0.10,0.11,0.12):
        pv,pvtv,flows,tv=dcf(s['oe0'],s['gs'],s['gt'],k)
        op=pv+pvtv; cv=cash_value(s['real'],s['xp'])
        out[k]=(op,cv,per_ads(op),per_ads(cv),per_ads(op+cv))
    res[name]=out
    print(f"\n{name}: p={s['p']} oe0={s['oe0']:.1f} growth={[round(g*100,1) for g in s['gs']]} gT={s['gt']} realization={s['real']} xp_haircut={s['xp']}")
    for k,(op,cv,a,b,c) in out.items():
        print(f"  k={k:.0%}: op RMB{op:.0f}bn ${a:.1f}/ADS + cash RMB{cv:.0f}bn ${b:.1f}/ADS = ${c:.1f}/ADS  P/V={PX/c:.2f}")
for k in (0.09,0.10,0.11,0.12):
    V=sum(SC[n]['p']*res[n][k][4] for n in SC)
    print(f"Prob-weighted V @k={k:.0%}: ${V:.1f}/ADS  P/V={PX/V:.2f}")
# terminal value share base
pv,pvtv,flows,tv=dcf(SC['base']['oe0'],SC['base']['gs'],0.025,0.10)
print('base: PV explicit',round(pv,1),'PV TV',round(pvtv,1),'TV share',round(pvtv/(pv+pvtv),3),'OE path',[round(f,1) for f in flows])
# Reverse DCF: market value of operations = price*ADS - cash value(base treatment)
mcap_rmb=PX*ADS*FX/1000
for real,xp,label in ((0.6,50,'base cash'),(1.0,0,'cash at 100% (ex-WHT)')):
    ops_mkt=mcap_rmb-cash_value(real,xp)
    # (a) constant g for 10 yrs then 2.5% terminal
    lo,hi=-0.5,0.5
    for _ in range(200):
        mid=(lo+hi)/2
        pv,pvtv,_,_=dcf(OE0,[mid]*10,0.025,0.10)
        if pv+pvtv>ops_mkt: hi=mid
        else: lo=mid
    g10=mid
    # (b) perpetual growth from OE0: V=OE0*(1+g)/(k-g)
    gp=(0.10*ops_mkt-OE0)/(ops_mkt+OE0)
    print(f"Reverse DCF [{label}]: mkt cap RMB{mcap_rmb:.0f}bn, implied ops value RMB{ops_mkt:.0f}bn = {ops_mkt/OE0:.1f}x OE0; 10y g={g10*100:.1f}% then 2.5%; perpetual g={gp*100:.1f}%")
# IRR at current price, base stream, cash at base realization counted at t0
def npv(r):
    pv,pvtv,_,_=dcf(SC['base']['oe0'],SC['base']['gs'],0.025,r)
    return pv+pvtv+cash_value(0.6,50)-mcap_rmb
lo,hi=0.04,0.40
for _ in range(200):
    mid=(lo+hi)/2
    if npv(mid)>0: lo=mid
    else: hi=mid
print(f"Base IRR at ${PX}: {mid*100:.1f}%")
# IRR alt: cash at 100% (ex WHT, ex xp haircut)
def npv2(r):
    pv,pvtv,_,_=dcf(SC['base']['oe0'],SC['base']['gs'],0.025,r)
    return pv+pvtv+cash_value(1.0,50)-mcap_rmb
lo,hi=0.04,0.60
for _ in range(200):
    mid=(lo+hi)/2
    if npv2(mid)>0: lo=mid
    else: hi=mid
print(f"Base IRR (cash at full value net of WHT and XP haircut): {mid*100:.1f}%")
print('mcap RMB bn',mcap_rmb,' NFA $/ADS',per_ads(NFA),' WHT $/ADS',per_ads(WHT))
