#!/usr/bin/env python3
"""券商远期预测的修正幅度：同一目标年（2026 财年）EPS，早期预测与最新预测对照。

研报存档 2026-08 抓取，`predict_this_year_eps` 一律指 2026 财年（与发布年无关；2024、2025、2026 年文件分别只有
1、2、3 个预测字段有值，与此一致）。对每家公司取：
- 早期：2024-01-01～2024-06-30 发布的 2026 财年 EPS，按机构取最后一份、再取中位（≥3 家机构）；
- 中期：2025-01-01～2025-06-30 发布的同一字段；
- 最新：2026-04-01 起发布的同一字段（年报与一季报后，≥3 家机构；存档止于 2026-08-09），作为 2026 财年实际的近似。
剔除 2023→2025 年报股数（归母净利 ÷ 基本 EPS）变动超过 5% 的公司，避免送转与增发改变每股口径。
用法：python3 analyst_bias.py <仓库根目录>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(sys.argv[1]).resolve()
pool = set(pd.read_csv(root / "data/processed/a_share_pool_model_bands_adopted.csv", dtype={"security_code": str})["security_code"])


def med(year: int, lo: str, hi: str, min_orgs: int) -> pd.Series:
    rep = pd.read_csv(root / f"data/raw/research_reports/reports_{year}.csv", dtype={"security_code": str},
                      usecols=["publish_date", "security_code", "org_code", "predict_this_year_eps"])
    d = rep[(rep["publish_date"] >= lo) & (rep["publish_date"] <= hi) & rep["predict_this_year_eps"].notna()]
    d = d.sort_values("publish_date").drop_duplicates(["security_code", "org_code"], keep="last")
    g = d.groupby("security_code").agg(eps=("predict_this_year_eps", "median"), n=("org_code", "nunique"))
    return g.loc[g["n"] >= min_orgs, "eps"]


def shares(year: int) -> pd.Series:
    a = pd.read_csv(root / f"data/raw/financials/{year}-12-31.csv", dtype={"security_code": str},
                    usecols=["security_code", "parent_netprofit", "basic_eps"]).drop_duplicates("security_code", keep="last")
    a = a[(a["basic_eps"].abs() > 0.01)]
    return (a["parent_netprofit"] / a["basic_eps"]).set_axis(a["security_code"])


early = med(2024, "2024-01-01", "2024-06-30", 3)
mid = med(2025, "2025-01-01", "2025-06-30", 3)
late = med(2026, "2026-04-01", "2026-12-31", 3)
sh = (shares(2025) / shares(2023)).dropna()
stable = set(sh[(sh - 1).abs() <= 0.05].index)
for label, a in (("2024 上半年 → 2026 年 4～8 月（提前约 2 年）", early), ("2025 上半年 → 2026 年 4～8 月（提前约 1 年）", mid)):
    j = pd.concat([a.rename("a"), late.rename("b")], axis=1, join="inner")
    j = j[j.index.isin(stable) & (j["a"] > 0) & (j["b"] > 0)]
    for name, sub in (("全部", j), ("当前池成员", j[j.index.isin(pool)])):
        r = sub["a"] / sub["b"] - 1
        print(f"{label}｜{name}：公司 {len(sub)}；早期预测高于最新 {np.mean(r > 0):.0%}；早期 ÷ 最新 − 1 中位 {r.median():+.1%}"
              f"（P25 {r.quantile(.25):+.1%}，P75 {r.quantile(.75):+.1%}）")
