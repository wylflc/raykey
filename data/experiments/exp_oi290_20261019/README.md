# OI-290 g0 = 0 下限改基准增速（2026-10-19）

[预登记](preregister.md)写于建带之前。结论见[报告](../../../docs/reports/oi290_g0_floor_2026-10-19.zh.md)，日志见回测日志 §12.344。

## 复现

研究开关 `scripts/build_historical_valuation_bands.py --g0-none-fill {off,f3,f5,fr}`（缺省 off，测试 `scripts/test_g0_none_fill.py`）。

| 步骤 | 命令 | 作业 |
| --- | --- | --- |
| 四臂两侧建带、银行保险覆盖、持仓侧状态 | `sbatch --account=tes21035 scripts/slurm/oi290_arms.sbatch`（`build.py`） | 28292838，33 分钟，32 核，峰值 30.9 GB |
| 月末观测、读数 1～7、买入线对齐与第 13 款 | `sbatch --account=tes21035 scripts/slurm/oi290_readings.sbatch`（`collect.py`、`readings.py`、`post.py`） | 28293415，16 分钟 |
| 回测参考读数（全样本与去赢家 A） | `sbatch --account=tes21035 scripts/slurm/oi290_sweep.sbatch` | 28293416，6 分钟，64 核；出表一步因命令写错在交互会话补跑 |

产物：
- 逐日状态与月末观测在 `data/scratch/experiments/exp_oi290_20261019/`，可再生，14 天未改动即被清理；
- 读数在本目录：`readings.json`／`readings.txt`、`align.json`、`opportunity_trap.md`／`.json`、`sweep.txt`／`sweep_report.txt`、`run_manifest.json`。

## 核对

- `C` 的 `roic_bands.csv`、`roic_bands_b2.csv`、三份逐日状态与 `data/processed/` 生产文件逐字节相同。
- 受影响以外的月份四臂 `P/V` 完全相同（`readings.json` 的 `unaffected_identical`）。
- 开关改动的带行全部是资本腿失效行：growth 路径 3,808 行，加「薄权益」拒绝行 326 行。
- 冒烟测试用 12 家小样本跑通全部脚本（`OI290_DIR`／`OI290_OUT` 指向 scratch 的 `smoke/`）。
