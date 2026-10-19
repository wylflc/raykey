#!/usr/bin/env python3
"""增长信息的价值：g0 换成不同来源时，年度截面 P/V 对其后回报的排序力（描述统计）。

样本：回测宇宙（时点护城河）内、候选侧历史带年报行（status = ok、growth 路径）。
评估日：年报带可得日之后的首个月末交易日（答案卷 opportunity_trap_labels_v1.csv 的月末行），
取当日逐日状态的现价、V 与 P/V，以及答案卷的其后 3／5 年含分红年化回报 f3／f5。

g0 变体（其余输入与带相同，同一引擎重算企业价值，按少数股东份额折入 V）：
- 现行：带上的 g0；
- 零增长、常数 5%：所有公司同一个 g0；
- 先知：其后 5 年归母净利年化增速（两年均值端点），夹 [0, 25%]——只作上界，事后才知道；
- 有限预测力：按「与先知相关系数 ρ」生成预测。校准型 = 按 ρ 收缩到均值（贝叶斯最优）；
  过度自信型 = 不收缩、方差与先知相同。各 200 次随机抽取取中位。

读数：年内百分位秩的合并相关 corr(−ln P/V, f)、对零增长的差（按公司整簇重抽）；最便宜五分之一减最贵五分之一的 f 均值差（逐年中位）。
用法：python3 growth_value_oracle.py <仓库根目录> <输出目录> <growth_rows.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R, GT = 0.10, 0.03


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    rows_path = Path(sys.argv[3]).resolve()
    sys.path.insert(0, str(root / "scripts"))
    from intrinsic_value import intrinsic_value, ValuationError  # noqa: E402

    keep = ["security_code", "report_date", "available_at", "nopat_ps", "roic0", "g0", "ev_ps",
            "intrinsic_value", "minority_share", "maintenance_ratio", "roe_terminal", "r", "g_terminal"]
    bands = []
    with (root / "data/processed/roic_bands.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["report_date"].endswith("-12-31") and r["status"] == "ok" and r["roic_path"] == "growth":
                bands.append({k: r[k] for k in keep})
    b = pd.DataFrame(bands)
    for c in keep[3:]:
        b[c] = pd.to_numeric(b[c], errors="coerce")
    g = pd.read_csv(rows_path, dtype={"security_code": str})
    g = g[["security_code", "report_date", "moat", "real_np5_avg2", "real_np5", "real_rev5", "year"]]
    b = b.merge(g, on=["security_code", "report_date"], how="inner")
    b = b[b["moat"]].copy()

    labels = pd.read_csv(root / "data/backtest/opportunity_trap_labels_v1.csv", dtype={"code": str},
                         usecols=["code", "date", "f3", "f5"])
    labels = labels.sort_values(["code", "date"])
    lab_by_code = {c: d for c, d in labels.groupby("code")}
    ev_date, f3, f5 = [], [], []
    for code, avail in zip(b["security_code"], b["available_at"]):
        d = lab_by_code.get(code)
        if d is None:
            ev_date.append(None); f3.append(np.nan); f5.append(np.nan); continue
        hit = d[d["date"] >= avail]
        if hit.empty or hit["date"].iloc[0] > (pd.Timestamp(avail) + pd.Timedelta(days=45)).strftime("%Y-%m-%d"):
            ev_date.append(None); f3.append(np.nan); f5.append(np.nan); continue
        ev_date.append(hit["date"].iloc[0]); f3.append(hit["f3"].iloc[0]); f5.append(hit["f5"].iloc[0])
    b["eval_date"], b["f3"], b["f5"] = ev_date, f3, f5
    b = b[b["eval_date"].notna()].copy()

    want = {f"{c},{d}" for c, d in zip(b["security_code"], b["eval_date"])}
    state = {}
    with (root / "data/processed/a_share_daily_states_adopted.csv").open(encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split(",")
        ix = {k: header.index(k) for k in ("close", "band_report_date", "intrinsic_value", "valuation_ratio")}
        for line in f:
            key = line[:17]
            if key in want:
                p = line.rstrip("\n").split(",")
                state[key] = (p[ix["close"]], p[ix["band_report_date"]], p[ix["intrinsic_value"]], p[ix["valuation_ratio"]])
    sv = [state.get(f"{c},{d}") for c, d in zip(b["security_code"], b["eval_date"])]
    b["state_band"] = [s[1] if s else None for s in sv]
    b["close"] = [float(s[0]) if s and s[0] else np.nan for s in sv]
    b["v_state"] = [float(s[2]) if s and s[2] else np.nan for s in sv]
    b["pv"] = [float(s[3]) if s and s[3] else np.nan for s in sv]
    # 只保留评估日仍由该年报带生效的行（否则 P/V 用的是别的带）
    b = b[(b["state_band"] == b["report_date"]) & (b["pv"] > 0) & (b["v_state"] > 0) & b["f3"].notna()].copy()

    def ev(row, g0: float) -> float:
        try:
            return intrinsic_value(row.nopat_ps, row.roic0, g0, row.r, roe_terminal=row.roe_terminal,
                                   g_terminal=row.g_terminal, n=10, roe_lam=0.12, horizon=50,
                                   maintenance_ratio=row.maintenance_ratio if np.isfinite(row.maintenance_ratio) else 0.0
                                   ).intrinsic_value
        except ValuationError:
            return np.nan

    b["ev_check"] = [ev(r, r.g0) for r in b.itertuples()]
    rel = (b["ev_check"] / b["ev_ps"] - 1).abs()
    lines = [f"样本：回测宇宙内年报带 {len(b)} 行，{b['security_code'].nunique()} 家，{b['year'].min()}–{b['year'].max()}",
             f"引擎复现带上 EV：相对差中位 {rel.median():.2e}，最大 {rel.max():.2e}（>1e-3 的 {int((rel > 1e-3).sum())} 行剔除）"]
    b = b[rel <= 1e-3].copy()

    def pv_for(g0s: np.ndarray) -> np.ndarray:
        ev_new = np.array([ev(r, float(gg)) for r, gg in zip(b.itertuples(), g0s)])
        mm = b["minority_share"].fillna(0).clip(0, 0.95).to_numpy()
        v_band_new = b["intrinsic_value"].to_numpy() + (ev_new - b["ev_ps"].to_numpy()) * (1 - mm)
        ratio = v_band_new / b["intrinsic_value"].to_numpy()
        out = b["pv"].to_numpy() / ratio
        out[~(v_band_new > 0)] = np.nan
        return out

    def score(pv: np.ndarray, fcol: str) -> tuple[float, float, int]:
        d = pd.DataFrame({"year": b["year"].to_numpy(), "x": -np.log(pv), "f": b[fcol].to_numpy()}).dropna()
        rhos, spreads = [], []
        for _, gg in d.groupby("year"):
            if len(gg) < 15:
                continue
            rhos.append(gg["x"].rank().corr(gg["f"].rank()))
            q = gg["x"].rank(pct=True)
            spreads.append(gg.loc[q > 0.8, "f"].mean() - gg.loc[q <= 0.2, "f"].mean())
        return float(np.median(rhos)), float(np.median(spreads)), len(rhos)

    oracle = b["real_np5_avg2"].clip(-0.2, 0.4)
    have_o = oracle.notna() & b["f5"].notna()
    lines.append(f"同一样本：有先知增速且有 f5 的行 {int(have_o.sum())}，{b.loc[have_o, 'security_code'].nunique()} 家"
                 f"（缺失多为其后亏损或数据不足，另报其后回报：缺失行 f3 中位 {b.loc[~have_o, 'f3'].median():+.3f}，"
                 f"保留行 {b.loc[have_o, 'f3'].median():+.3f}）")
    b = b[have_o].copy()
    m = b["minority_share"].fillna(0).clip(0, 0.95)
    oracle = oracle[have_o]
    mu, sd = float(oracle.mean()), float(oracle.std())
    years = b["year"].to_numpy()
    codes = b["security_code"].to_numpy()

    def pct_rank_by_year(x: np.ndarray) -> np.ndarray:
        return pd.Series(x).groupby(years).rank(pct=True).to_numpy()

    def metrics(pv: np.ndarray, fcol: str, idx: np.ndarray | None = None) -> tuple[float, float]:
        x = -np.log(pv)
        f = b[fcol].to_numpy()
        if idx is not None:
            x, f, yrs = x[idx], f[idx], years[idx]
        else:
            yrs = years
        d = pd.DataFrame({"y": yrs, "x": x, "f": f}).dropna()
        rx = d.groupby("y")["x"].rank(pct=True)
        rf = d.groupby("y")["f"].rank(pct=True)
        pooled = float(np.corrcoef(rx, rf)[0, 1])
        top = d[rx > 0.8].groupby("y")["f"].mean()
        bot = d[rx <= 0.2].groupby("y")["f"].mean()
        spread = float((top - bot).dropna().median())
        return pooled, spread

    variants = {
        "现行 g0": b["g0"].to_numpy(),
        "零增长": np.zeros(len(b)),
        "常数 5%": np.full(len(b), 0.05),
        "先知（夹 [0, 25%]）": oracle.clip(0, 0.25).to_numpy(),
        "先知收缩一半": (mu + 0.5 * (oracle - mu)).clip(0, 0.25).to_numpy(),
    }
    pvs = {k: pv_for(v) for k, v in variants.items()}
    uniq = np.unique(codes)
    rng = np.random.default_rng(20261019)
    boot_idx = []
    for _ in range(500):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        boot_idx.append(np.concatenate([np.flatnonzero(codes == c) for c in pick]))
    res = []
    for name, pv in pvs.items():
        for fcol in ("f3", "f5"):
            rho, spr = metrics(pv, fcol)
            diffs = [metrics(pv, fcol, ix)[0] - metrics(pvs["零增长"], fcol, ix)[0] for ix in boot_idx[:300]]
            lo, hi = np.percentile(diffs, [5, 95])
            res.append({"variant": name, "target": fcol, "pooled_rank_corr": rho, "q5_spread_median": spr,
                        "diff_vs_zero": rho - metrics(pvs["零增长"], fcol)[0], "diff_p05": lo, "diff_p95": hi})

    z_o = ((oracle - mu) / sd).to_numpy()
    for rho in (0.2, 0.4, 0.6):
        for kind in ("校准型", "过度自信型"):
            acc = {"f3": [], "f5": []}
            spr_acc = {"f3": [], "f5": []}
            for _ in range(200):
                eps = rng.standard_normal(len(b))
                sig = rho * z_o + np.sqrt(1 - rho ** 2) * eps
                scale = rho * sd if kind == "校准型" else sd
                fc = np.clip(mu + scale * sig, 0, 0.25)
                pv = pv_for(fc)
                for fcol in ("f3", "f5"):
                    r_, s_ = metrics(pv, fcol)
                    acc[fcol].append(r_); spr_acc[fcol].append(s_)
            for fcol in ("f3", "f5"):
                zero = metrics(pvs["零增长"], fcol)[0]
                res.append({"variant": f"预测力 ρ={rho}（{kind}）", "target": fcol,
                            "pooled_rank_corr": float(np.median(acc[fcol])),
                            "q5_spread_median": float(np.median(spr_acc[fcol])),
                            "diff_vs_zero": float(np.median(acc[fcol])) - zero,
                            "diff_p05": float(np.percentile(acc[fcol], 5)) - zero,
                            "diff_p95": float(np.percentile(acc[fcol], 95)) - zero})
    t = pd.DataFrame(res)
    t.to_csv(out_dir / "growth_value_oracle.csv", index=False, float_format="%.4f")
    lines.append("")
    lines.append("读数：年内百分位秩的合并相关 corr(−ln P/V, 其后回报)；对零增长的差（确定性变体给按公司整簇重抽 300 次的 5%～95% 区间，")
    lines.append("模拟变体给 200 次抽取的 5%～95% 区间）；便宜五分之一 − 贵五分之一的年化回报差（逐年中位）")
    lines.append("变体                         目标  秩相关   对零增长的差 [区间]          五分位差")
    for r in t.itertuples():
        lines.append(f"{r.variant:<28} {r.target}   {r.pooled_rank_corr:+.3f}   {r.diff_vs_zero:+.3f} [{r.diff_p05:+.3f}, {r.diff_p95:+.3f}]   {r.q5_spread_median:+.3f}")
    lines.append("")
    lines.append(f"先知增速均值 {mu:.3f}、标准差 {sd:.3f}；现行 g0 与先知的年内秩相关"
                 f" {np.corrcoef(pct_rank_by_year(b['g0'].to_numpy()), pct_rank_by_year(oracle.to_numpy()))[0, 1]:+.3f}")
    (out_dir / "growth_value_oracle.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
