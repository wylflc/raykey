#!/usr/bin/env python3
"""生产引擎下企业价值对 g0 的敏感度：EV ÷ 每股 NOPAT 随 g0、ROIC0 的变化。

参数同 §6.5.1：r = 10%，g_T = 3%，增速 10 年线性 fade，回报指数衰减 λ = 0.12、50 年，
ROIC_T = min(r + 2pp, ROIC0)。用法：python3 engine_sensitivity.py <仓库根目录>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "scripts"))
from intrinsic_value import intrinsic_value  # noqa: E402

R, GT = 0.10, 0.03
G0S = [0.0, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25]
print("EV ÷ NOPAT（倍）；括号内为相对 g0 = 0 的变化")
print("ROIC0   " + "  ".join(f"g0={g:>4.0%}" for g in G0S))
for roic0 in (0.12, 0.15, 0.20, 0.30, 0.50):
    roic_t = min(R + 0.02, roic0)
    vals = []
    for g in G0S:
        res = intrinsic_value(1.0, roic0, g, R, roe_terminal=roic_t, g_terminal=GT, n=10,
                              roe_lam=0.12, horizon=50)
        vals.append(res.intrinsic_value)
    base = vals[0]
    print(f"{roic0:>5.0%}   " + "  ".join(f"{v:5.1f}({v / base - 1:+4.0%})" for v in vals))
print()
print("g0 每 +1pp 的 EV 变化（ROIC0 = 20%，在 g0 附近差分）")
for g in (0.0, 0.05, 0.10, 0.15):
    a = intrinsic_value(1.0, 0.20, g, R, roe_terminal=0.12, g_terminal=GT, n=10, roe_lam=0.12, horizon=50).intrinsic_value
    b = intrinsic_value(1.0, 0.20, g + 0.01, R, roe_terminal=0.12, g_terminal=GT, n=10, roe_lam=0.12, horizon=50).intrinsic_value
    print(f"  g0 {g:.0%} → {g + 0.01:.0%}：EV {b / a - 1:+.1%}")
print()
print("同一公司 r 改 ±1pp 的 EV 变化（ROIC0 = 20%，g0 = 5%）")
for r in (0.09, 0.10, 0.11):
    v = intrinsic_value(1.0, 0.20, 0.05, r, roe_terminal=min(r + 0.02, 0.20), g_terminal=GT, n=10, roe_lam=0.12, horizon=50).intrinsic_value
    print(f"  r {r:.0%}：EV/NOPAT {v:.2f}")

print()
print("回报衰减速度 λ 的影响（ROIC0 = 30%，g0 = 5%；λ 越小护城河越久）")
for lam in (0.03, 0.06, 0.12, 0.24):
    v = intrinsic_value(1.0, 0.30, 0.05, R, roe_terminal=0.12, g_terminal=GT, n=10, roe_lam=lam, horizon=50).intrinsic_value
    print(f"  λ {lam:.2f}：EV/NOPAT {v:.2f}")
print()
print("海康威视（生产带 2026-06-30：每股 NOPAT 2.0296，ROIC0 25.02%，每股净负债 −1.9963，V 20.30）")
NOPAT, ROIC0, ND = 2.0296, 0.2502, -1.9963
for label, g, r, lam in (("现行 g0 0、r 10%、λ 0.12", 0.0, 0.10, 0.12), ("g0 5%", 0.05, 0.10, 0.12),
                         ("g0 8%", 0.08, 0.10, 0.12), ("r 9%", 0.0, 0.09, 0.12), ("λ 0.06", 0.0, 0.10, 0.06),
                         ("g0 5% + r 9%", 0.05, 0.09, 0.12), ("g0 5% + r 9% + λ 0.06", 0.05, 0.09, 0.06)):
    ev = intrinsic_value(NOPAT, ROIC0, g, r, roe_terminal=min(r + 0.02, ROIC0), g_terminal=GT, n=10,
                         roe_lam=lam, horizon=50).intrinsic_value
    print(f"  {label:<24} EV {ev:6.2f}  V≈{ev - ND:6.2f}（少数股东扣减按带上近似，未随 EV 重算）")
