"""决策日志：第一批修正落地行与 OI-264 门槛重装行（v4.232，须在重发扫描之前写入；已写的 run_id 不重写）。"""
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_decision_log import append_decision_log, DEFAULT_DECISION_LOG, WORKFLOW_VERSION  # noqa: E402

ROWS = [
    ('OI-260-264-20261006-land', 'mechanism_repair', 'valuation_caliber', 'adopted',
     'v4.232 第一批修正落地：OI-260 派息率按财年全部现金分红（含中期，预案公告日起计）；OI-262 推股数与重述前 BPS 用普通股权益（股本不是股数时按面板 BPS 反推）、'
     '年度分配期末入账按 |x| 更小解释（多笔取最优组合）、公告前已派分红经营账面按派后计与年报行期后除息补扣（含 OI-261 应付股利）；OI-264 只纠负税率（首轮「低于中位 10pp」'
     '方案误改神火、顺丰、鼎龙，用户同日改判）；OI-243 回测单票上限按信号日净资产。六臂重建（作业 27654484）：CONTROL 逐字节复现七份正式状态；09-30 池内 42 只 V 变化'
     '（华荣 −5.8%、P/V 0.974→1.034 出买入区；平安带值 −4.1%；盐湖 +4.5%，补税后谷底守卫 0.85→1；爱玛 +2.8%）；招行／成都年报行 BPS 回到 43.43／20.84，中国海油股数 751.8→475.3 亿。'
     '原线合格面 16.873%（在册 16.916%），容差内保留 1.0034、在册合格面不改写。14 起点参考读数 NEW 对 CONTROL 标劣化：主读数全／A／U −0.37／−0.01／−0.01，复利 −0.44／−0.22／−0.22'
     '（只估值四项复利 −0.35，只改上限分母 +0.33）；CONTROL 14/14 复现在册 BASE；BASE 按 NEW 重登。',
     'data/experiments/exp_oi260_264_land_20261006/build_check.json;data/experiments/exp_oi260_264_land_20261006/current_changes.md;'
     'data/experiments/exp_oi260_264_land_20261006/align.txt;data/experiments/exp_oi260_264_land_20261006/readings.md;data/experiments/exp_oi260_264_land_20261006/user_ruling.json',
     'workflow_rule:2026-10-06:ALL:batch1_ruled'),
    ('OI-264-20261006-reinstall', 'mechanism_repair', 'valuation_caliber', 'adopted',
     'v4.232 重装（用户 2026-10-06 裁定加门槛后重装）：首轮安装的 OI-264「凡负即纠、前三年无可比按法定 25%」误改牧原（09-30 V 28.20→14.52，−48.5%），'
     '改为实际税率低于 −5% 才纠、按前三年非负观测税率中位、前三年无非负观测的不改。重建（作业 27657977）CONTROL 逐字节等于首轮安装前正式状态；'
     '修正后 09-30 池内 V 与首轮只差牧原（复原 28.15）、豪威 37.71→36.83、安集 92.11→94.67、乐鑫 69.87→66.31，对改前仍 33 只 V 变化、买入区 27→26（华荣出）；'
     '原线合格面 16.882%（−0.034pp）容差内保留 1.0034；14 起点读数与首轮相同（只差浮点末位），CONTROL 28/28 复现 HEAD 在册 BASE，BASE 按修正后 NEW 重登。'
     '其余各项（OI-260、OI-262、OI-261 应付股利、OI-243）不变；首轮读数与安装凭据留 v1_negative_all/。',
     'data/experiments/exp_oi260_264_land_20261006/build_check.json;data/experiments/exp_oi260_264_land_20261006/current_changes.md;'
     'data/experiments/exp_oi260_264_land_20261006/align.txt;data/experiments/exp_oi260_264_land_20261006/readings.md;'
     'data/experiments/exp_oi260_264_land_20261006/user_ruling.json;data/experiments/exp_oi260_264_land_20261006/registration.json;'
     'data/experiments/exp_oi260_264_land_20261006/v1_negative_all/build_check.json',
     'mechanism_repair:2026-09-30:ALL:33aa3daf'),
]


def main():
    done = {r['run_id'] for r in csv.DictReader(open(DEFAULT_DECISION_LOG, encoding='utf-8'))}
    rows = [dict(logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage=stage, run_id=run_id, as_of='2026-09-30',
                 security_code='ALL', decision_type=kind, decision_result=result, summary_reason=reason, input_files=inputs,
                 output_file='data/experiments/exp_oi260_264_land_20261006/publication.json', operator_or_script='exp_oi260_264_land_20261006/log.py',
                 workflow_version=WORKFLOW_VERSION, supersedes_decision_id=supersedes)
            for run_id, stage, kind, result, reason, inputs, supersedes in ROWS if run_id not in done]
    if rows:
        append_decision_log(DEFAULT_DECISION_LOG, rows)
    print('decision log rows appended', len(rows), WORKFLOW_VERSION)


if __name__ == '__main__':
    main()
