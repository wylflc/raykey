# 增长率假设评估（2026-10-19，描述统计）

用户 2026-10-19 问：模型是否应按每家公司选择适合的增长率，是否不必一切以回测为基准。本目录只做描述统计，不改任何生产产物。结论见[报告](../../../docs/reports/growth_assumption_review_2026-10-19.zh.md)，日志见回测日志 §12.343。

## 复现

在仓库根目录运行（交互会话，单进程，各约 10 秒至 1.5 分钟）：

```bash
D=data/experiments/exp_growth_assumption_20261019
S=data/scratch/experiments/exp_growth_assumption_20261019
PYTHONDONTWRITEBYTECODE=1 python3 $D/tools/growth_predictability.py . $D $S
PYTHONDONTWRITEBYTECODE=1 python3 $D/tools/growth_value_oracle.py . $D $S/growth_rows.csv
PYTHONDONTWRITEBYTECODE=1 python3 $D/tools/engine_sensitivity.py . > $D/engine_sensitivity.txt
PYTHONDONTWRITEBYTECODE=1 python3 $D/tools/analyst_bias.py . > $D/analyst_bias.txt
PYTHONDONTWRITEBYTECODE=1 python3 $D/tools/pool_g0_floor.py . > $D/pool_g0_floor.txt
```

## 输入（只读）

- `data/processed/roic_bands.csv`（10-14 版）：候选侧历史带，取年报行、`status = ok`、`roic_path = growth`。
- `data/raw/financials/<年>-12-31.csv`：年报归母净利、营业总收入、基本 EPS。
- `data/processed/pit_attention/panel_moat_bank_v6b.csv`：回测宇宙；带的可得日落在在册区间内记为宇宙内。
- `data/backtest/opportunity_trap_labels_v1.csv`：月末其后 3／5 年含分红年化回报 `f3`／`f5`。
- `data/processed/a_share_daily_states_adopted.csv`：评估日的现价、V 与 `P/V`。
- `data/raw/research_reports/reports_2024～2026.csv`：券商 EPS 预测。存档 2026-08-09 抓取，`predict_this_year_eps` 一律指 2026 财年，与发布年无关（2024、2025、2026 年文件分别只有 1、2、3 个预测字段有值）。
- `data/processed/a_share_pool_model_bands_adopted.csv`、`daily_buy_candidates.csv`（10-16 扫描）。

## 输出

| 文件 | 内容 |
| --- | --- |
| `summary.txt`、`rank_corr_summary.csv`、`bucket_table.csv` | g0、过去五年 NOPAT 增速、过去五年营收增速对其后 3／5 年实际增速的逐年秩相关、去年均值斜率、绝对误差与分档 |
| `growth_value_oracle.txt`、`.csv` | 回测宇宙内 g0 换成零增长、常数、先知与模拟预测力后，`P/V` 对其后回报的年内秩相关；对零增长的差按公司整簇重抽 300 次 |
| `engine_sensitivity.txt` | 生产引擎 EV ÷ NOPAT 随 g0、ROIC0、r、λ 的变化；海康威视分解 |
| `analyst_bias.txt` | 同一目标年（2026）EPS 预测：2024 上半年、2025 上半年对 2026 年 4～8 月的修正 |
| `pool_g0_floor.txt`、`.csv` | 当前池 g0 = 0 成员改 3%／5%／8% 后的 V 与 `P/V` |

逐行明细 `growth_rows.csv`（约 1.5 MB）放 `data/scratch/experiments/exp_growth_assumption_20261019/`，可由第一条命令重建。

## 口径说明

- 实际增速：归母净利、营收总额的 h 年年化；起点 ≤ 0 记缺失，终点 ≤ 0 记 −100%（只用于排序，误差统计剔除）。「两年均值端点」= 起点取 t−1、t 两年均值，终点取 t+h−1、t+h 两年均值。
- 模型隐含 h 年平均增速：第 k 年增速 `g0 + (3% − g0)·k/10` 的前 h 年平均。
- 先知检验的 V：同一引擎按带上输入重算企业价值（复现带上 EV 的相对差中位 5e-5），差额按少数股东份额折入 V，未重算股权桥；`P/V` 按 V 的比例折算。
- 模拟预测力：预测 = 均值 + 缩放 × (ρ × 先知标准分 + √(1−ρ²) × 噪声)，校准型缩放 ρ × 标准差，过度自信型缩放 1 × 标准差，夹 [0, 25%]，各 200 次。
- 池内重算剔除按带上输入复现不了 EV 的 2 只（北新建材、华鲁恒升）。买入线未按 §12.1 重解，读数只表示相对变化。
