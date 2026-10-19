#!/usr/bin/env python3
"""模型 g0 对其后实际增长的预测力（描述统计，不改任何生产产物）。

输入（只读）：
- data/processed/roic_bands.csv：候选侧历史带，取年报行（report_date = 12-31）、status = ok、roic_path = growth。
- data/raw/financials/<年>-12-31.csv：年报归母净利与营业总收入。
- data/processed/pit_attention/panel_moat_bank_v6b.csv：回测宇宙（时点护城河名单）。

对每个年报带行（第 t 年），计算其后 h 年（3、5）归母净利与营收的年化增速，
与带上的 g0、g_trailing 及按营收算的过去五年增速对照：逐年截面秩相关、分档中位、
收缩斜率与绝对误差。实际值只用于事后评分，不回写任何带。

用法：python3 growth_predictability.py <仓库根目录> <输出目录> <逐行明细目录（可再生，放 data/scratch）>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

G_T = 0.03
FADE_N = 10


def load_bands(path: Path) -> pd.DataFrame:
    keep = ["security_code", "security_name", "report_date", "available_at", "status", "roic_path",
            "g0", "g_trailing", "roic0", "incremental_roic", "reinvestment_rate", "roic_g_source",
            "growth_trust", "peak_weight", "trough_weight"]
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["report_date"].endswith("-12-31"):
                continue
            if r["status"] != "ok" or r["roic_path"] != "growth":
                continue
            rows.append({k: r[k] for k in keep})
    df = pd.DataFrame(rows)
    for c in ["g0", "g_trailing", "roic0", "incremental_roic", "reinvestment_rate",
              "growth_trust", "peak_weight", "trough_weight"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["year"] = df["report_date"].str[:4].astype(int)
    return df


def load_panel(root: Path, years: range) -> pd.DataFrame:
    parts = []
    for y in years:
        fn = root / "data/raw/financials" / f"{y}-12-31.csv"
        if not fn.exists():
            continue
        d = pd.read_csv(fn, dtype={"security_code": str},
                        usecols=["security_code", "parent_netprofit", "total_operate_income"])
        d["year"] = y
        parts.append(d)
    p = pd.concat(parts, ignore_index=True)
    p = p.drop_duplicates(["security_code", "year"], keep="last")
    return p


def load_moat(root: Path) -> pd.DataFrame:
    m = pd.read_csv(root / "data/processed/pit_attention/panel_moat_bank_v6b.csv", dtype={"security_code": str})
    return m[["security_code", "effective_from", "effective_to"]]


def in_moat(df: pd.DataFrame, moat: pd.DataFrame) -> pd.Series:
    merged = df[["security_code", "available_at"]].reset_index().merge(moat, on="security_code", how="left")
    hit = (merged["effective_from"] <= merged["available_at"]) & (merged["available_at"] <= merged["effective_to"])
    return hit.groupby(merged["index"]).any().reindex(df.index, fill_value=False)


def cagr(a: pd.Series, b: pd.Series, h: int) -> pd.Series:
    """a → b 的 h 年年化；a ≤ 0 记缺失；b ≤ 0 记 −100%（排序用，误差统计另行排除）。"""
    out = pd.Series(np.nan, index=a.index)
    ok = (a > 0) & b.notna()
    pos = ok & (b > 0)
    out[pos] = (b[pos] / a[pos]) ** (1.0 / h) - 1
    out[ok & (b <= 0)] = -1.0
    return out


def implied_avg_growth(g0: pd.Series, h: int) -> pd.Series:
    """生产引擎增速 10 年线性 fade：第 k 年 g0 + (g_T − g0)·k/10，取前 h 年的平均。"""
    return g0 + (G_T - g0) * (h + 1) / (2 * FADE_N)


def spearman_by_year(df: pd.DataFrame, x: str, y: str, min_n: int = 30) -> pd.DataFrame:
    out = []
    for yr, g in df.groupby("year"):
        g = g[[x, y]].dropna()
        if len(g) < min_n:
            continue
        rho = g[x].rank().corr(g[y].rank())
        out.append({"year": yr, "n": len(g), "rho": rho})
    return pd.DataFrame(out)


def demeaned_slope(df: pd.DataFrame, x: str, y: str, clip: tuple[float, float]) -> tuple[float, float, int]:
    """逐年去均值后，实际增速（截尾）对预测值的回归斜率与 R²。"""
    g = df[[x, y, "year"]].dropna()
    g = g[g[y] > -1]
    g = g.assign(yc=g[y].clip(*clip), xc=g[x].clip(-0.3, 0.6))
    g["yd"] = g["yc"] - g.groupby("year")["yc"].transform("mean")
    g["xd"] = g["xc"] - g.groupby("year")["xc"].transform("mean")
    if g["xd"].var() == 0 or len(g) < 30:
        return float("nan"), float("nan"), len(g)
    b = (g["xd"] * g["yd"]).sum() / (g["xd"] ** 2).sum()
    r2 = np.corrcoef(g["xd"], g["yd"])[0, 1] ** 2
    return b, r2, len(g)


def bucket(g0: float, rr: float, inc: float) -> str:
    if g0 == 0:
        if not np.isfinite(rr) or rr <= 0:
            return "0｜再投资率 ≤ 0"
        if not np.isfinite(inc) or inc <= 0:
            return "0｜增量回报 ≤ 0"
        return "0｜其他"
    if g0 < 0.03:
        return "(0, 3%)"
    if g0 < 0.06:
        return "[3%, 6%)"
    if g0 < 0.10:
        return "[6%, 10%)"
    if g0 < 0.15:
        return "[10%, 15%)"
    return "[15%, 25%]"


ORDER = ["0｜再投资率 ≤ 0", "0｜增量回报 ≤ 0", "0｜其他", "(0, 3%)", "[3%, 6%)", "[6%, 10%)", "[10%, 15%)", "[15%, 25%]"]


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_dir = Path(sys.argv[3]).resolve()
    rows_dir.mkdir(parents=True, exist_ok=True)

    bands = load_bands(root / "data/processed/roic_bands.csv")
    panel = load_panel(root, range(1998, 2026))
    moat = load_moat(root)

    np_ = panel.pivot(index="security_code", columns="year", values="parent_netprofit")
    rev = panel.pivot(index="security_code", columns="year", values="total_operate_income")

    def lookup(tbl: pd.DataFrame, codes: pd.Series, years: pd.Series) -> pd.Series:
        vals = []
        for c, y in zip(codes, years):
            try:
                vals.append(tbl.at[c, y])
            except KeyError:
                vals.append(np.nan)
        return pd.Series(vals, index=codes.index, dtype=float)

    df = bands.copy()
    df["np_t"] = lookup(np_, df["security_code"], df["year"])
    df["rev_t"] = lookup(rev, df["security_code"], df["year"])
    df["rev_t5"] = lookup(rev, df["security_code"], df["year"] - 5)
    df["np_tm1"] = lookup(np_, df["security_code"], df["year"] - 1)
    df["rev_trailing5"] = cagr(df["rev_t5"], df["rev_t"], 5).where(lambda s: s > -1)
    for h in (3, 5):
        df[f"np_t{h}"] = lookup(np_, df["security_code"], df["year"] + h)
        df[f"np_t{h}m1"] = lookup(np_, df["security_code"], df["year"] + h - 1)
        df[f"rev_t{h}"] = lookup(rev, df["security_code"], df["year"] + h)
        df[f"real_np{h}"] = cagr(df["np_t"], df[f"np_t{h}"], h)
        df[f"real_rev{h}"] = cagr(df["rev_t"], df[f"rev_t{h}"], h)
        start2 = (df["np_t"] + df["np_tm1"]) / 2
        end2 = (df[f"np_t{h}"] + df[f"np_t{h}m1"]) / 2
        df[f"real_np{h}_avg2"] = cagr(start2, end2, h)
        df[f"impl{h}"] = implied_avg_growth(df["g0"], h)
    df["moat"] = in_moat(df, moat)
    df["bucket"] = [bucket(a, b, c) for a, b, c in zip(df["g0"], df["reinvestment_rate"], df["incremental_roic"])]
    df.to_csv(rows_dir / "growth_rows.csv", index=False, float_format="%.6f")

    lines: list[str] = []
    w = lines.append
    w("模型 g0 对其后实际增长的预测力（候选侧历史带，年报行，status=ok，路径 growth）")
    w(f"带行 {len(df)}，年份 {df['year'].min()}–{df['year'].max()}；回测宇宙内 {int(df['moat'].sum())} 行")
    w("")

    subsets = {
        "全部有带公司（多为曾进观察范围者，含幸存者偏差）": df,
        "回测宇宙（时点护城河）": df[df["moat"]],
        "ROIC0 ≥ 15%": df[df["roic0"] >= 0.15],
    }
    sum_rows = []
    for name, sub in subsets.items():
        for h, last in ((5, 2020), (3, 2022)):
            s = sub[(sub["year"] >= 2008) & (sub["year"] <= last)]
            w(f"== {name}｜其后 {h} 年（第 t 年 2008–{last}）==")
            w(f"  行数 {len(s)}；有实际值 {int(s[f'real_np{h}'].notna().sum())}；其后亏损占比 {np.mean(s[f'real_np{h}'] == -1):.1%}")
            for x, label in (("g0", "g0（现行，资本腿）"), ("g_trailing", "过去五年 NOPAT 增速"), ("rev_trailing5", "过去五年营收增速")):
                for y, ylab in ((f"real_np{h}", "归母净利"), (f"real_np{h}_avg2", "归母净利（两年均值端点）"), (f"real_rev{h}", "营收")):
                    t = spearman_by_year(s, x, y, min_n=30 if name.startswith("全部") else 15)
                    if t.empty:
                        continue
                    b, r2, n = demeaned_slope(s, x if x != "g0" else f"impl{h}", y, (-0.5, 0.6))
                    w(f"  {label:<16} → {ylab:<14} 逐年秩相关中位 {t['rho'].median():+.3f}"
                      f"（{(t['rho'] > 0).sum()}/{len(t)} 年为正，区间 {t['rho'].min():+.2f}～{t['rho'].max():+.2f}）"
                      f"；去年均值斜率 {b:+.2f}，R² {r2:.3f}，n {n}")
                    sum_rows.append({"subset": name, "h": h, "predictor": x, "target": y, "rho_median": t["rho"].median(),
                                     "years_pos": int((t["rho"] > 0).sum()), "years": len(t), "rho_min": t["rho"].min(),
                                     "rho_max": t["rho"].max(), "slope": b, "r2": r2, "n": n})
            # 误差：模型隐含 h 年平均增速 vs 常数
            e = s[[f"impl{h}", f"real_np{h}", "g_trailing"]].dropna()
            e = e[e[f"real_np{h}"] > -1]
            yv = e[f"real_np{h}"].clip(-0.5, 0.6)
            w(f"  绝对误差中位（实际归母净利增速截尾 [−50%, 60%]，排除其后亏损，n {len(e)}）：")
            w(f"    模型隐含 {np.median(np.abs(e[f'impl{h}'] - yv)):.3f}；常数 0 {np.median(np.abs(yv)):.3f}；"
              f"常数 5% {np.median(np.abs(0.05 - yv)):.3f}；常数 8% {np.median(np.abs(0.08 - yv)):.3f}；"
              f"过去增速 {np.median(np.abs(e['g_trailing'].clip(-0.3, 0.6) - yv)):.3f}")
            w(f"    实际增速分布：P25 {yv.quantile(0.25):+.3f}，中位 {yv.median():+.3f}，P75 {yv.quantile(0.75):+.3f}")
            w("")
    pd.DataFrame(sum_rows).to_csv(out_dir / "rank_corr_summary.csv", index=False, float_format="%.4f")

    # 分档：其后 5 年（2008–2020）
    btab = []
    for name, sub in subsets.items():
        s = sub[(sub["year"] >= 2008) & (sub["year"] <= 2020)]
        w(f"== 分档（{name}，其后 5 年）==")
        w("  档位                 行数   g0中位  实际净利增速中位 [P25, P75]   实际营收增速中位   5年后净利低于当年")
        for bk in ORDER:
            g = s[s["bucket"] == bk]
            gg = g[g["real_np5"].notna()]
            if len(gg) < 10:
                continue
            q = gg["real_np5"]
            drop = np.mean(gg["np_t5"] < gg["np_t"])
            w(f"  {bk:<18} {len(gg):>6}  {g['g0'].median():6.3f}   {q.median():+.3f} [{q.quantile(.25):+.3f}, {q.quantile(.75):+.3f}]"
              f"        {gg['real_rev5'].median():+.3f}            {drop:.1%}")
            btab.append({"subset": name, "bucket": bk, "n": len(gg), "g0_median": g["g0"].median(),
                         "real_np5_median": q.median(), "real_np5_p25": q.quantile(.25), "real_np5_p75": q.quantile(.75),
                         "real_rev5_median": gg["real_rev5"].median(), "np_lower_after5": drop})
        w("")
    pd.DataFrame(btab).to_csv(out_dir / "bucket_table.csv", index=False, float_format="%.4f")

    (out_dir / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
