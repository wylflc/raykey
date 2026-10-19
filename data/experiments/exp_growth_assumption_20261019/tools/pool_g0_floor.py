#!/usr/bin/env python3
"""当前池：g0 = 0 的 growth 路径成员若改用一个基准 g0，P/V 怎么变（描述，不改生产）。

读 10-16 扫描的 daily_buy_candidates.csv（model_pv）与候选侧生产带；同一引擎按带上输入重算企业价值，
按少数股东份额折入 V，P/V 按 V 的比例折算。用法：python3 pool_g0_floor.py <仓库根目录>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "scripts"))
from intrinsic_value import intrinsic_value  # noqa: E402

BUY = 1.0034
bands = pd.read_csv(root / "data/processed/a_share_pool_model_bands_adopted.csv", dtype={"security_code": str})
cand = pd.read_csv(root / "data/processed/daily_buy_candidates.csv", dtype={"security_code": str})[["security_code", "trade_date", "model_pv"]]
d = bands.merge(cand, on="security_code", how="inner")
d = d[(d["status"] == "ok") & (d["roic_path"] == "growth") & d["model_pv"].notna()]
print(f"扫描日 {d['trade_date'].iloc[0]}；growth 路径池成员 {len(d)}，g0 = 0 的 {int((d['g0'] == 0).sum())}；买入线 {BUY}")
z = d[d["g0"] == 0].copy()


def ev(r, g):
    mr = r.maintenance_ratio if np.isfinite(r.maintenance_ratio) else 0.0
    return intrinsic_value(r.nopat_ps, r.roic0, g, r.r, roe_terminal=r.roe_terminal, g_terminal=r.g_terminal,
                           n=10, roe_lam=0.12, horizon=50, maintenance_ratio=mr).intrinsic_value


chk = np.array([ev(r, 0.0) for r in z.itertuples()]) / z["ev_ps"].to_numpy() - 1
bad = np.abs(chk) > 1e-3
flags = z[["forecast_overlay", "research_overlay", "growth_cap_note"]].notna().any(axis=1).to_numpy()
print(f"引擎按带上输入复现 EV：{int((~bad).sum())} 只误差 ≤ 1e-3；{int(bad.sum())} 只对不上（其中带预告／研究数／上限标记的 {int((bad & flags).sum())} 只），只读不算："
      + "、".join(f"{n}（{c:+.0%}）" for n, c, b in zip(z["security_name"], chk, bad) if b))
z = z[~bad].copy()
m = z["minority_share"].fillna(0).clip(0, 0.95).to_numpy()
v_raw = (z["ev_ps"] - z["net_debt_ps"]).to_numpy()
rows = []
for g in (0.03, 0.05, 0.08):
    ev_new = np.array([ev(r, g) for r in z.itertuples()])
    ratio = (v_raw + (ev_new - z["ev_ps"].to_numpy()) * (1 - m)) / v_raw
    pv_new = z["model_pv"].to_numpy() / ratio
    enter = (z["model_pv"].to_numpy() > BUY) & (pv_new <= BUY)
    print(f"g0 改 {g:.0%}：V 中位 {np.median(ratio) - 1:+.1%}（P10 {np.percentile(ratio, 10) - 1:+.1%}，P90 {np.percentile(ratio, 90) - 1:+.1%}）；"
          f"原在买入区 {int((z['model_pv'] <= BUY).sum())} 只，新进买入区 {int(enter.sum())} 只："
          + "、".join(f"{n}（{a:.3f}→{b:.3f}）" for n, a, b, e in zip(z["security_name"], z["model_pv"], pv_new, enter) if e))
    rows.append(pd.DataFrame({"security_code": z["security_code"], "security_name": z["security_name"], "g0_alt": g,
                              "model_pv": z["model_pv"], "pv_alt": pv_new, "v_ratio": ratio}))
out = pd.concat(rows)
out.to_csv(root / "data/experiments/exp_growth_assumption_20261019/pool_g0_floor.csv", index=False, float_format="%.4f")
print("g0 = 0 成员 P/V 分布：", np.round(np.percentile(z["model_pv"], [10, 25, 50, 75, 90]), 3))
