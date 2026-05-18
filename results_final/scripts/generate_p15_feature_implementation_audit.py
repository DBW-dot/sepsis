from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_TEXT = ROOT / "results_final" / "text"
OUT_TABLES = ROOT / "results_final" / "tables"
OUT_TEXT.mkdir(parents=True, exist_ok=True)
OUT_TABLES.mkdir(parents=True, exist_ok=True)

FEATURE_SCRIPT = ROOT / "results_final" / "clinical_implementation" / "run_p12_p10_true_training_validation.py"
SUPP_VALIDITY = ROOT / "manuscript_assets" / "tables" / "Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv"
FIG5_DATA = ROOT / "manuscript_assets" / "figures" / "data" / "Figure5_P15_Clinical_Feature_Modules_Data.csv"
METRE_TRANSPORT = ROOT / "archive" / "post_metre_reference" / "metre_transport" / "METRE_Transport_Feature_Set.csv"
METRE_PROXY_DEF = ROOT / "archive" / "post_metre_reference" / "metre_transport" / "Shared_Support_Intensity_Proxy_Definition.md"
PROXY_AUDIT = ROOT / "results_final" / "clinical_implementation" / "Proxy_Clinical_Interpretability_Audit.md"
LAB_LOOKAHEAD = ROOT / "results_final" / "clinical_implementation" / "Lab_Availability_Lookahead_Audit.md"
LAB_MISSING = ROOT / "results_final" / "clinical_implementation" / "Lab_Freshness_Missingness_Impact.csv"
TABLE3_CI = ROOT / "manuscript_assets" / "tables" / "Table3_Clinical_Implementation_TrueTraining_with_95CI.csv"
TABLE4_CI = ROOT / "manuscript_assets" / "tables" / "Table4_Lab_Freshness_Sensitivity_with_95CI.csv"
DUAL_ANCHOR = ROOT / "manuscript_assets" / "supplement" / "Supplementary_Dual_Anchor_Definition.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def extract_feature_list(name: str) -> list[str]:
    text = FEATURE_SCRIPT.read_text(encoding="utf-8")
    match = re.search(rf"{name}\s*=\s*(\[[\s\S]*?\])", text)
    if not match:
        raise RuntimeError(f"Could not find {name}")
    return ast.literal_eval(match.group(1))


P15 = extract_feature_list("P15_FEATURES")
P12 = extract_feature_list("P12_FEATURES")
P10 = extract_feature_list("P10_FEATURES")

PAPER_NAME = {
    "hr_latest_value": "heart_rate_latest_value",
    "rr_latest_value": "respiratory_rate_latest_value",
    "spo2_latest_value": "spo2_latest_value",
    "hours_since_icu_admission": "hours_since_icu_admission",
    "hours_from_anchor": "hours_from_anchor",
    "is_sepsis_on_admission": "is_sepsis_on_admission",
    "creatinine_latest_value": "creatinine_latest_value",
    "bun_latest_value": "bun_latest_value",
    "platelet_latest_value": "platelet_latest_value",
    "wbc_latest_value": "wbc_latest_value",
    "shared_support_intensity_proxy": "shared_support_intensity_proxy",
    "support_hemodynamic_component": "support_hemodynamic_component",
    "support_lactate_component": "support_lactate_component",
    "support_renal_component": "support_renal_component",
    "support_respiratory_component": "support_respiratory_component",
}

ALIASES = {
    "hr_latest_value": "heart_rate_latest_value; hr_latest_value",
    "rr_latest_value": "respiratory_rate_latest_value; rr_latest_value",
}

ZH = {
    "hours_since_icu_admission": "距 ICU 入室时间",
    "hours_from_anchor": "距脓毒症发作锚点时间",
    "is_sepsis_on_admission": "是否入室时/接近入室时发生脓毒症",
    "hr_latest_value": "最新心率",
    "rr_latest_value": "最新呼吸频率",
    "spo2_latest_value": "最新外周血氧饱和度",
    "creatinine_latest_value": "最新肌酐",
    "bun_latest_value": "最新尿素氮",
    "platelet_latest_value": "最新血小板计数",
    "wbc_latest_value": "最新白细胞计数",
    "shared_support_intensity_proxy": "共享支持强度代理总指标",
    "support_hemodynamic_component": "血流动力学支持分量",
    "support_lactate_component": "乳酸/灌注支持分量",
    "support_renal_component": "肾脏支持分量",
    "support_respiratory_component": "呼吸支持分量",
}

CATEGORY = {
    "hours_since_icu_admission": "时间锚点",
    "hours_from_anchor": "疾病阶段",
    "is_sepsis_on_admission": "疾病阶段",
    "hr_latest_value": "床旁生命体征",
    "rr_latest_value": "床旁生命体征",
    "spo2_latest_value": "床旁生命体征",
    "creatinine_latest_value": "常规实验室",
    "bun_latest_value": "常规实验室",
    "platelet_latest_value": "常规实验室",
    "wbc_latest_value": "常规实验室",
    "shared_support_intensity_proxy": "支持强度代理变量",
    "support_hemodynamic_component": "支持强度代理变量",
    "support_lactate_component": "支持强度代理变量",
    "support_renal_component": "支持强度代理变量",
    "support_respiratory_component": "支持强度代理变量",
}

SOURCE = {
    "hours_since_icu_admission": "ICU stay / admission 表",
    "hours_from_anchor": "Sepsis-3 电子表型规则",
    "is_sepsis_on_admission": "Sepsis-3 电子表型规则",
    "hr_latest_value": "ICU 监护仪 / 护理 flowsheet",
    "rr_latest_value": "ICU 监护仪 / 护理 flowsheet",
    "spo2_latest_value": "ICU 监护仪 / 护理 flowsheet",
    "creatinine_latest_value": "实验室系统",
    "bun_latest_value": "实验室系统",
    "platelet_latest_value": "实验室系统",
    "wbc_latest_value": "实验室系统",
    "shared_support_intensity_proxy": "医嘱系统 / 输液泵 / 呼吸机接口 / CRRT 或透析记录 / 尿量记录 / ICU 专科记录",
    "support_hemodynamic_component": "治疗支持记录 / 血压相关动态变量",
    "support_lactate_component": "实验室系统 / 灌注相关动态变量",
    "support_renal_component": "尿量记录 / CRRT 或透析记录 / 肾功能相关动态变量",
    "support_respiratory_component": "呼吸机接口 / 呼吸治疗记录 / 护理 flowsheet",
}

EXTRACT = {
    "hours_since_icu_admission": "是，基于 ICU 入室时间戳派生",
    "hours_from_anchor": "否，需要 Sepsis-3 电子表型推导 t_sepsis 后派生",
    "is_sepsis_on_admission": "否，需要 Sepsis-3 电子表型推导",
    "hr_latest_value": "是",
    "rr_latest_value": "是",
    "spo2_latest_value": "是",
    "creatinine_latest_value": "是",
    "bun_latest_value": "是",
    "platelet_latest_value": "是",
    "wbc_latest_value": "是",
    "shared_support_intensity_proxy": "否，需要字段映射和派生",
    "support_hemodynamic_component": "否，需要字段映射和派生",
    "support_lactate_component": "否，需要字段映射和派生",
    "support_renal_component": "否，需要字段映射和派生",
    "support_respiratory_component": "否，需要字段映射和派生",
}

REALTIME = {
    "hours_since_icu_admission": "固定时间戳 / 小时级派生",
    "hours_from_anchor": "固定疾病锚点 / 小时级派生",
    "is_sepsis_on_admission": "固定 cohort 标记",
    "hr_latest_value": "近实时或小时级记录",
    "rr_latest_value": "小时级或护理记录更新",
    "spo2_latest_value": "近实时或小时级记录",
    "creatinine_latest_value": "间断实验室结果",
    "bun_latest_value": "间断实验室结果",
    "platelet_latest_value": "间断实验室结果",
    "wbc_latest_value": "间断实验室结果",
    "shared_support_intensity_proxy": "依赖治疗记录更新",
    "support_hemodynamic_component": "依赖治疗记录和血压动态更新",
    "support_lactate_component": "依赖治疗记录和间断乳酸结果更新",
    "support_renal_component": "依赖尿量/肾功能/支持治疗记录更新",
    "support_respiratory_component": "依赖呼吸支持状态更新",
}

DIFFICULTY = {
    "hours_since_icu_admission": "低",
    "hours_from_anchor": "中",
    "is_sepsis_on_admission": "中",
    "hr_latest_value": "低",
    "rr_latest_value": "低到中",
    "spo2_latest_value": "低",
    "creatinine_latest_value": "低",
    "bun_latest_value": "低",
    "platelet_latest_value": "低",
    "wbc_latest_value": "低",
    "shared_support_intensity_proxy": "中到高",
    "support_hemodynamic_component": "中到高",
    "support_lactate_component": "中",
    "support_renal_component": "中到高",
    "support_respiratory_component": "中到高",
}

RISK = {
    "hours_since_icu_admission": "ADT/ICU 入室时间戳口径差异；需要本地 admission/stay 映射核对",
    "hours_from_anchor": "t_sepsis 电子表型依赖抗菌药、培养、SOFA 规则；本地实现差异可能影响校准",
    "is_sepsis_on_admission": "入室即脓毒症阈值和锚点窗口定义需本地复核",
    "hr_latest_value": "人工录入误差、监护仪/护理 flowsheet 字段差异、时间戳不一致",
    "rr_latest_value": "人工录入误差较心率更常见；护理 flowsheet 和监护仪来源可能不一致",
    "spo2_latest_value": "探头质量、吸氧/通气支持状态影响解释；跨库字段命名差异",
    "creatinine_latest_value": "结果报告时间缺失、单位/测量口径需核对、实验室非小时级更新",
    "bun_latest_value": "结果报告时间缺失、单位/测量口径需核对、实验室非小时级更新",
    "platelet_latest_value": "结果报告时间缺失、单位/测量口径需核对、实验室非小时级更新",
    "wbc_latest_value": "结果报告时间缺失、单位/测量口径需核对、实验室非小时级更新",
    "shared_support_intensity_proxy": "本地字段映射困难；支持治疗记录不完整；可能存在文档延迟；需要本地再校准",
    "support_hemodynamic_component": "MAP 缺口/低 MAP burden 来源和血压口径需核对；不能与 full VIS 混称",
    "support_lactate_component": "乳酸 freshness 依赖强；结果报告时间缺失；抽血频率影响可用性",
    "support_renal_component": "尿量、肾功能恶化、CRRT/透析记录字段可能不稳定；需要本地映射",
    "support_respiratory_component": "FiO2、SpO2、通气状态和呼吸支持升级记录跨系统差异明显",
}

SUPPORT = {
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
}

SUPPORT_DETAIL = {
    "shared_support_intensity_proxy": ("Step7 model-ready physiology-derived support components / composite", "Step7 model-ready core physiology-derived support components / composite", "是，四个 proxy 分量平均"),
    "support_hemodynamic_component": ("map_deficit + map_below_65_burden_24h", "map_deficit + map_below_65_burden_24h", "是，MAP deficit 与低 MAP burden 合成"),
    "support_lactate_component": ("lactate_gt2_burden_24h + lactate_gt4_burden_24h", "lactate_gt2_burden_24h + lactate_gt4_burden_24h", "是，乳酸 burden 合成"),
    "support_renal_component": ("oliguria_burden_24h + worsening_renal_trajectory_flag", "oliguria_burden_24h + worsening_renal_trajectory_flag", "是，少尿 burden 与肾功能恶化标记合成"),
    "support_respiratory_component": ("high_fio2_burden_24h + low_spo2_burden_24h + ventilation_transition_count_24h", "high_fio2_burden_24h + low_spo2_burden_24h + ventilation_transition_count_24h", "是，呼吸支持/氧合 burden 合成"),
}


def evidence_for(feature: str) -> str:
    parts = [rel(SUPP_VALIDITY), rel(FIG5_DATA), rel(FEATURE_SCRIPT)]
    if feature in {"hours_from_anchor", "is_sepsis_on_admission"}:
        parts.append(rel(DUAL_ANCHOR))
    if feature in SUPPORT:
        parts.extend([rel(METRE_PROXY_DEF), rel(PROXY_AUDIT)])
    if feature in {"creatinine_latest_value", "bun_latest_value", "platelet_latest_value", "wbc_latest_value"}:
        parts.append(rel(LAB_LOOKAHEAD))
    return "; ".join(parts)


def write_source_availability() -> pd.DataFrame:
    rows = []
    for feature in P15:
        rows.append(
            {
                "特征类别": CATEGORY[feature],
                "具体变量": ZH[feature],
                "英文变量名": PAPER_NAME[feature],
                "主要临床来源": SOURCE[feature],
                "是否可直接抽取": EXTRACT[feature],
                "实时性": REALTIME[feature],
                "部署难度": DIFFICULTY[feature],
                "主要风险点": RISK[feature],
                "证据来源文件": evidence_for(feature),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT_TABLES / "P15_feature_source_availability_deployment_table.csv", index=False, encoding="utf-8-sig")
    return df


def write_mapping_audit() -> pd.DataFrame:
    metre = pd.read_csv(METRE_TRANSPORT)
    by_raw = {row["mimic_raw_variable"]: row for _, row in metre.iterrows()}
    rows = []
    for feature in P15:
        if feature in SUPPORT:
            mimic, eicu, merge = SUPPORT_DETAIL[feature]
            rows.append(
                {
                    "P15 变量": PAPER_NAME[feature],
                    "MIMIC-IV 来源字段 / itemid / 表": mimic + "；未在当前项目文件中找到原始 itemid，需要作者核对",
                    "eICU 来源字段 / 表": eicu + "；未在当前项目文件中找到原始字段名细节，需要作者核对",
                    "是否需要单位转换": "使用 0-1 proxy scale；底层变量已在 Step2/Step3 层 canonicalized，具体单位换算未在主路径完整列出",
                    "是否需要字段合并": merge,
                    "是否存在 fallback": "未在当前项目文件中找到数据库特异性 fallback 细节；proxy 用 shared transport representation 避免 full VIS 等价假设",
                    "映射稳定性判断": "high/transport（概念级，来自 METRE transport registry）；本地字段级部署仍需核对",
                    "证据文件路径": "; ".join([rel(FEATURE_SCRIPT), rel(METRE_TRANSPORT), rel(METRE_PROXY_DEF)]),
                    "备注": "禁止写成 full VIS；底层原始字段和单位需作者结合原始特征工程代码核对。",
                }
            )
            continue
        if feature in by_raw:
            row = by_raw[feature]
            rows.append(
                {
                    "P15 变量": PAPER_NAME[feature],
                    "MIMIC-IV 来源字段 / itemid / 表": f"{row['mimic_source_table']} / {row['mimic_raw_variable']}；未在当前项目文件中找到 itemid",
                    "eICU 来源字段 / 表": f"{row['eicu_source_table']} / {row['eicu_raw_variable']}",
                    "是否需要单位转换": f"{row['conversion_rule']}；具体单位未在当前最终文件中完整展开",
                    "是否需要字段合并": "否，概念级变量已在 Step2/Step3 层 canonicalized",
                    "是否存在 fallback": "prediction grid 字段作为双库统一接口" if feature.startswith("hours_") or feature == "is_sepsis_on_admission" else "未在当前项目文件中找到数据库特异性 fallback 细节",
                    "映射稳定性判断": row["transportability_grade"],
                    "证据文件路径": rel(METRE_TRANSPORT),
                    "备注": "未在当前项目文件中找到原始 itemid；仅确认到表/概念级映射。",
                }
            )
        else:
            rows.append(
                {
                    "P15 变量": PAPER_NAME[feature],
                    "MIMIC-IV 来源字段 / itemid / 表": "未在当前项目文件中找到直接证据，需要作者根据原始特征工程代码进一步核对。",
                    "eICU 来源字段 / 表": "未在当前项目文件中找到直接证据，需要作者根据原始特征工程代码进一步核对。",
                    "是否需要单位转换": "未确认",
                    "是否需要字段合并": "未确认",
                    "是否存在 fallback": "未确认",
                    "映射稳定性判断": "未确认",
                    "证据文件路径": rel(FEATURE_SCRIPT),
                    "备注": "feature list confirmed, source mapping not confirmed.",
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUT_TABLES / "P15_feature_mapping_audit.csv", index=False, encoding="utf-8-sig")
    return df


def write_missingness_audit() -> pd.DataFrame:
    metre = pd.read_csv(METRE_TRANSPORT)
    lab_missing = pd.read_csv(LAB_MISSING)
    current = lab_missing[lab_missing["scenario"].eq("current_latest_value_reference")]
    lab_map = {
        (row["dataset_name"], row["feature_name"]): float(row["baseline_missing_rate"])
        for _, row in current.iterrows()
    }
    metre_map = {
        row["mimic_raw_variable"]: (
            float(row["missingness_mimic"]),
            float(row["missingness_eicu"]),
            rel(METRE_TRANSPORT),
        )
        for _, row in metre.iterrows()
    }
    rows = []
    for feature in P15:
        if ("mimic_internal", feature) in lab_map or ("eicu_external", feature) in lab_map:
            mimic_missing = lab_map.get(("mimic_internal", feature))
            eicu_missing = lab_map.get(("eicu_external", feature))
            source = rel(LAB_MISSING)
            note = "current_latest_value_reference baseline_missing_rate；lab/proxy freshness 审计来源。"
        elif feature in metre_map:
            mimic_missing, eicu_missing, source = metre_map[feature]
            note = "METRE transport registry 中的 model-ready missingness；主文不建议逐项展开，适合补充材料。"
        else:
            mimic_missing = None
            eicu_missing = None
            source = rel(FEATURE_SCRIPT)
            note = "未在当前项目文件中找到直接缺失率证据，需要作者根据模型 ready table 核对。"
        diff = None if mimic_missing is None or eicu_missing is None else eicu_missing - mimic_missing
        rows.append(
            {
                "P15 变量": PAPER_NAME[feature],
                "MIMIC-IV 缺失率": "未确认" if mimic_missing is None else f"{mimic_missing:.6f}",
                "eICU 缺失率": "未确认" if eicu_missing is None else f"{eicu_missing:.6f}",
                "缺失率差异": "未确认" if diff is None else f"{diff:.6f}",
                "是否可用于主文": "建议补充材料逐项列出；主文可概述可获得性和 freshness 结论",
                "证据文件路径": source,
                "备注": note,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT_TABLES / "P15_feature_missingness_audit.csv", index=False, encoding="utf-8-sig")
    return df


def perf_row(model: str) -> dict:
    table3 = pd.read_csv(TABLE3_CI)
    return table3[table3["model_display_name"].eq(model)].iloc[0].to_dict()


def table4_value(model: str, scenario: str, metric: str) -> float:
    table4 = pd.read_csv(TABLE4_CI)
    row = table4[(table4["model_display_name"].eq(model)) & (table4["freshness_scenario"].eq(scenario))].iloc[0]
    return float(row[metric])


def write_text_outputs() -> None:
    p12_deleted = [feature for feature in P15 if feature not in set(P12)]
    p10_deleted = [feature for feature in P15 if feature not in set(P10)]
    p12_perf = perf_row("P12_true_trained_clinical_landing_model")
    p10_perf = perf_row("P10_true_trained_ultra_minimal_sensitivity_model")

    p15_feature_lines = [
        "| 序号 | 论文推荐变量名 | 内部变量名 | 中文推荐名称 | 类别 | aliases | 证据 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for idx, feature in enumerate(P15, 1):
        aliases = ALIASES.get(feature, feature)
        p15_feature_lines.append(
            f"| {idx} | `{PAPER_NAME[feature]}` | `{feature}` | {ZH[feature]} | {CATEGORY[feature]} | {aliases} | {rel(FEATURE_SCRIPT)}; {rel(SUPP_VALIDITY)} |"
        )

    proxy_lines = [
        "| proxy 变量 | 精确定义/项目内定义 | 临床解释 | 部署风险 | 是否可用于主文 | 是否建议仅放补充材料 | 证据文件路径 |",
        "|---|---|---|---|---|---|---|",
        f"| `shared_support_intensity_proxy` | 四个可用分量的平均值 | 总体支持强度负荷 | 字段映射、治疗文档延迟、本地再校准 | 主文可用，但必须定义清楚 | 否，可放主文方法和补充表 | {rel(METRE_PROXY_DEF)}; {rel(FEATURE_SCRIPT)}; {rel(PROXY_AUDIT)} |",
        f"| `support_hemodynamic_component` | normalized map_deficit 与 map_below_65_burden_24h 的均值 | 循环支持/低血压负荷 | 血压来源、MAP 口径、与 VIS 混称风险 | 可用于主文特征表 | 可在补充材料给公式 | {rel(METRE_PROXY_DEF)}; {rel(FEATURE_SCRIPT)} |",
        f"| `support_lactate_component` | normalized lactate_gt2_burden_24h 与 lactate_gt4_burden_24h 的均值 | 乳酸/灌注负荷 | 乳酸结果 freshness 和报告时间 | 可用于主文特征表 | 建议补充解释 freshness | {rel(METRE_PROXY_DEF)}; {rel(LAB_MISSING)} |",
        f"| `support_renal_component` | normalized oliguria_burden_24h 与 worsening_renal_trajectory_flag 的均值 | 肾脏支持/恶化负荷 | 尿量、CRRT/透析、肌酐 freshness 映射 | 可用于主文特征表 | 建议补充字段映射 | {rel(METRE_PROXY_DEF)}; {rel(LAB_MISSING)} |",
        f"| `support_respiratory_component` | normalized high_fio2_burden_24h、low_spo2_burden_24h、ventilation_transition_count_24h 的均值 | 呼吸支持/氧合恶化负荷 | FiO2、通气状态和呼吸治疗记录映射 | 可用于主文特征表 | 建议补充字段映射 | {rel(METRE_PROXY_DEF)}; {rel(FEATURE_SCRIPT)} |",
    ]

    p12_deleted_lines = "\n".join([f"- `{feature}` ({CATEGORY[feature]}): 牺牲 {ZH[feature]} 相关信息。" for feature in p12_deleted])
    p10_deleted_lines = "\n".join([f"- `{feature}` ({CATEGORY[feature]}): 牺牲 {ZH[feature]} 相关信息。" for feature in p10_deleted])

    results_para = (
        "在冻结的 P15 主模型基础上，P12 和 P10 作为低负担实现候选进行了真实训练验证，而不是仅保留模拟敏感性估计。"
        f"P12 保留 12 个变量，相对 P15 删除 {', '.join(p12_deleted)}，eICU 外部 AUROC/AUPRC/校准斜率为 "
        f"{p12_perf['eICU_AUROC']:.4f}/{p12_perf['eICU_AUPRC']:.4f}/{p12_perf['eICU_calibration_slope']:.4f} "
        f"（95% CI: AUROC {p12_perf['eICU_AUROC_95CI_lower']:.4f}-{p12_perf['eICU_AUROC_95CI_upper']:.4f}; "
        f"AUPRC {p12_perf['eICU_AUPRC_95CI_lower']:.4f}-{p12_perf['eICU_AUPRC_95CI_upper']:.4f}; "
        f"校准斜率 {p12_perf['eICU_calibration_slope_95CI_lower']:.4f}-{p12_perf['eICU_calibration_slope_95CI_upper']:.4f}）。"
        f"P10 保留 10 个变量，相对 P15 删除 {', '.join(p10_deleted)}，eICU 外部 AUROC/AUPRC/校准斜率为 "
        f"{p10_perf['eICU_AUROC']:.4f}/{p10_perf['eICU_AUPRC']:.4f}/{p10_perf['eICU_calibration_slope']:.4f} "
        f"（95% CI: AUROC {p10_perf['eICU_AUROC_95CI_lower']:.4f}-{p10_perf['eICU_AUROC_95CI_upper']:.4f}; "
        f"AUPRC {p10_perf['eICU_AUPRC_95CI_lower']:.4f}-{p10_perf['eICU_AUPRC_95CI_upper']:.4f}; "
        f"校准斜率 {p10_perf['eICU_calibration_slope_95CI_lower']:.4f}-{p10_perf['eICU_calibration_slope_95CI_upper']:.4f}）。"
        "这些结果支持 P12/P10 作为低负担部署候选或敏感性模型进行补充展示，但不改变 P15 作为正式主模型的冻结定位；P15 保留完整支持强度代理分量，仍提供最完整的临床语义覆盖。"
    )

    audit_md = f"""# P15 特征集临床来源、可获得性与部署难度审计

## 证据边界

本文件仅使用当前项目中的代码、CSV、Markdown 和审计文件。未在当前项目文件中找到的 itemid、原始字段、具体单位换算和 result availability time 均标注为需要作者核对。未重新训练模型，未修改任何冻结点估计，未使用 eICU 调参。

主要证据文件：

- `{rel(FEATURE_SCRIPT)}`：P15/P12/P10 true-training 特征清单和 support proxy 构造代码。
- `{rel(SUPP_VALIDITY)}`：P15 特征临床有效性和可实施性审计。
- `{rel(METRE_TRANSPORT)}`：跨库概念级映射、缺失率和 transportability grade；该文件位于 archive，但用于审计追踪。
- `{rel(METRE_PROXY_DEF)}`：shared support-intensity proxy 定义；明确不是 full VIS。
- `{rel(LAB_MISSING)}` 与 `{rel(LAB_LOOKAHEAD)}`：实验室 freshness、missingness 和 look-ahead 审计。
- `{rel(TABLE3_CI)}`：P12/P10 true-training 结果及 95% CI。

## 任务 1：P15 最终 15 个特征

{chr(10).join(p15_feature_lines)}

结论：P15 最终变量数为 {len(P15)}。用户特别列出的 time since ICU admission、time since sepsis onset、is sepsis on admission、heart rate、respiratory rate、SpO2、creatinine、BUN、platelet、WBC、shared support-intensity proxy 及四个支持强度分量均属于 P15。内部训练脚本使用 `hr_latest_value` 和 `rr_latest_value`；论文推荐使用更可读的 `heart_rate_latest_value` 和 `respiratory_rate_latest_value`，并在补充表中保留 alias。

## 任务 2：临床来源、可获得性与部署难度

已生成表：`{rel(OUT_TABLES / 'P15_feature_source_availability_deployment_table.csv')}`。

概括：7 个生命体征/常规实验室变量可直接从监护或实验室系统抽取；`hours_since_icu_admission` 可从 ICU 入室时间戳派生；`hours_from_anchor` 和 `is_sepsis_on_admission` 需要 Sepsis-3 电子表型推导；5 个支持强度 proxy 变量需要本地字段映射和派生。

## 任务 3：MIMIC-IV 与 eICU 字段映射

已生成表：`{rel(OUT_TABLES / 'P15_feature_mapping_audit.csv')}`。

### 已确认字段映射

当前项目可确认到概念级表/字段映射。例如 HR 来自 MIMIC `mimiciv_icu.chartevents` 和 eICU `vitalPeriodic / nurseCharting`，实验室变量来自 MIMIC `mimiciv_hosp.labevents` 和 eICU `lab`，时间锚点来自 prediction grid。

### 未确认字段映射

当前最终文件未找到完整原始 itemid 级映射，也未找到完整数据库字段 fallback 细节。支持强度 proxy 的底层变量已确认为动态特征名，但原始设备/医嘱/呼吸机/CRRT 字段级映射仍需作者核对。

### 需要作者核对字段映射

- MIMIC-IV chartevents/labevents 的 itemid 级定义。
- eICU vitalPeriodic、nurseCharting、respiratoryCharting、lab、intakeOutput、infusionDrug 或其他治疗支持字段的本地字段名。
- proxy 底层 MAP、FiO2、SpO2、ventilation transition、urine output、worsening renal trajectory 和 lactate burden 的构造代码与单位口径。

## 任务 4：缺失率审计

已生成表：`{rel(OUT_TABLES / 'P15_feature_missingness_audit.csv')}`。

当前可确认所有 15 个 P15 变量均有 model-ready 或 METRE registry 层面的缺失率证据。建议逐项缺失率放补充材料；主文只概述 P15 变量可获得性较高，并重点报告 lab freshness sensitivity。

## 任务 5：单位转换、时间对齐和 look-ahead

- `METRE_Transport_Feature_Set.csv` 将 P15 生命体征和实验室变量标记为 already canonicalized in Step2/Step3 feature layer。
- 当前最终主路径未找到完整 Canonical Unit Dictionary 或 itemid 级单位转换表；不能在论文中编造具体单位换算公式。
- 支持强度 proxy 使用 0-1 proxy scale 或 component score 表达，不是 full VIS，也不是药物剂量单位。
- Step2/Step3 层使用 capped forward-fill where applicable；动态 burden 使用 prefix-only windows。
- 实验室 latest_value 是 latest-available / capped carry-forward，不是每小时真实实验室测量。
- 未找到 linear interpolation、MICE 或将 missingness mask 纳入 P15 的证据；不能声称 P15 使用这些机制。
- `Lab_Availability_Lookahead_Audit.md` 说明 model-ready 层未找到 explicit result availability/store time；可用 freshness 字段基于 chart/sample-time derived quality indicators。
- 审计未引入 t_pred 之后的实验室值；但不能证明所有真实报告延迟风险已完全消除。

P15 current latest_value reference eICU AUROC/AUPRC/calibration slope: {table4_value('P15_clinically_parsimonious_transport_model', 'current_latest_value_reference', 'eICU_AUROC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'current_latest_value_reference', 'eICU_AUPRC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'current_latest_value_reference', 'eICU_calibration_slope'):.4f}。

P15 12h freshness eICU AUROC/AUPRC/calibration slope: {table4_value('P15_clinically_parsimonious_transport_model', 'lab12h_freshness_window', 'eICU_AUROC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'lab12h_freshness_window', 'eICU_AUPRC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'lab12h_freshness_window', 'eICU_calibration_slope'):.4f}，状态为 borderline acceptable，不应写成 fully noninferior。

P15 24h freshness eICU AUROC/AUPRC/calibration slope: {table4_value('P15_clinically_parsimonious_transport_model', 'lab24h_freshness_window', 'eICU_AUROC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'lab24h_freshness_window', 'eICU_AUPRC'):.4f} / {table4_value('P15_clinically_parsimonious_transport_model', 'lab24h_freshness_window', 'eICU_calibration_slope'):.4f}，状态为 largely stable。

## 任务 6：支持强度代理变量定义

{chr(10).join(proxy_lines)}

结论：shared support-intensity proxy 是跨数据库支持强度负荷代理变量，明确不是 full VIS。MIMIC full VIS 只可作为 internal-rich/sensitivity 背景，不是 eICU external transport 输入。

## 任务 7：P12/P10 删除变量和性能

### P12 相对 P15 删除

{p12_deleted_lines}

### P10 相对 P15 删除

{p10_deleted_lines}

### 可直接插入 Results 的中文段落

{results_para}

## 未确认信息清单

- 未在当前项目文件中找到完整 itemid 级字段映射表。
- 未在当前项目文件中找到完整 Canonical Unit Dictionary 或所有变量具体单位换算公式。
- 未在 model-ready 层找到 result availability/store time；当前只确认使用 chart/sample-time freshness 近似。
- 支持强度 proxy 底层原始设备字段、医嘱字段、CRRT/透析字段和呼吸机接口字段需作者按原始特征工程代码进一步核对。
"""
    (OUT_TEXT / "P15_feature_implementation_audit.md").write_text(audit_md, encoding="utf-8")

    methods = """# 2.X P15 特征集的临床来源与实施可行性

P15_clinically_parsimonious_transport_model 的设计目标不是最大化高维特征数量或内部 AUC，而是在双锚点动态预测框架下保留一组临床语义清楚、跨数据库可迁移且可由结构化 EHR 自动抽取或派生的变量。最终 P15 特征集包含 15 个变量，分为时间锚点、疾病阶段、床旁生命体征、常规实验室指标和支持强度代理变量五类。时间相关变量包括距 ICU 入室时间、距 t_sepsis 疾病锚点时间以及是否入室时或接近入室时已发生脓毒症。t_ICU 可由 ICU stay/admission 时间戳获得；t_sepsis 和 is_sepsis_on_admission 需要根据已锁定的 Sepsis-3 电子表型规则推导，因此在本地部署时必须复核感染证据、SOFA 变化和锚点定义。

生命体征变量包括心率、呼吸频率和 SpO2，项目文件将其归为 bedside monitor 或护理 flowsheet 来源，通常可近实时或小时级记录。常规实验室变量包括肌酐、BUN、血小板计数和 WBC，来源为实验室系统。需要强调的是，模型中的 laboratory latest_value 不是假设每小时真实测量，而是 latest-available / capped carry-forward 值；项目已完成 12h 和 24h freshness sensitivity，以评估实验室结果时效性对部署真实性的影响。由于当前模型 ready 层未保留完整 result availability/store time，相关审计使用 chart/sample time 作为保守近似；这一限制应在方法学和局限性中同时说明。

支持强度代理变量包括 shared_support_intensity_proxy 及其 hemodynamic、lactate/perfusion、renal 和 respiratory 分量。该 proxy 表示跨数据库可共享的支持强度负荷，而不是 full VIS，也不是单纯药物剂量评分。根据项目中的 proxy 定义，血流动力学分量由 MAP deficit 和 MAP below 65 burden 构成，乳酸/灌注分量由 lactate >2 和 >4 burden 构成，肾脏分量由 oliguria burden 和 renal trajectory worsening 构成，呼吸分量由 high FiO2 burden、low SpO2 burden 和 ventilation transition count 构成。上述变量需要本地医嘱、治疗支持、尿量、呼吸支持和实验室字段映射，因此部署难度高于生命体征和常规实验室变量。

P12 和 P10 是在冻结主流程下真实训练验证的低负担候选模型。P12 删除部分支持强度分量但保留 WBC、shared_support_intensity_proxy 和 support_lactate_component；P10 进一步删除 WBC 和所有 proxy 分量，仅保留 shared_support_intensity_proxy。二者可用于数据条件较弱或临床实施负担讨论，但不能直接替代 P15，除非后续由作者重新冻结模型层级并完成相应验证。
"""
    discussion = """# 6.X P15 特征集的临床实施边界

P15 的优势不只是变量数量较少，而是保留变量具有清晰的临床语义和可追溯的 EHR 来源。与高维模型相比，P15 有意减少 observation-process-heavy 特征和数据库特异性记录习惯的影响，从而降低模型学习测量密度、文档风格或数据源特异性偏差的风险。生命体征和常规实验室变量在 ICU 场景中可获得性较高，临床医生也容易理解其方向性含义；这使 P15 更适合作为 implementation-oriented prototype，而不是只在单一数据库内部表现较强的高维模型。

真正的部署难点主要有两类。第一，t_sepsis 不是床旁直接字段，而是 Sepsis-3 电子表型锚点，需要本地重建 suspected infection、SOFA 变化和时间配对逻辑。第二，shared support-intensity proxy 及其分量依赖本地治疗支持记录、尿量、呼吸支持、血压负荷和实验室 freshness 的稳定映射。该 proxy 不能解释为 full VIS，也不能等同于药物剂量评分；它更适合作为跨数据库支持负荷表达。若目标医院结构化 EHR 不完整，可在补充分析中考虑 P12/P10 或进行本地再校准，但这不改变 P15 作为正式主模型的定位。

此外，phenotype 分层更适合用于模型审计、校准线索和异质性描述，不应过度解释为治疗分型或因果亚型。DCA 和 lead-time 结果也应仅作为补充临床效用估计，而不是自动干预触发器。P15 的合理定位是需要本地字段映射、实验室时效性审计和前瞻性验证的 EHR 动态风险模型。
"""
    limitations = """# Limitations 补充段落

本研究尚未完成前瞻性部署验证，因此 P15 的实际临床运行性能仍需在目标医院 EHR 环境中进一步评估。P15 虽然是 clinically parsimonious transport model，但其落地仍依赖本地结构化 EHR 的完整程度：t_sepsis 需要由本地 Sepsis-3 电子表型规则推导，支持强度代理变量可能来自医嘱、输液泵、呼吸机接口、护理 flowsheet、尿量和 CRRT/透析记录。上述字段在不同医院系统中的命名、时间戳、更新频率和完整性可能不一致，并可能影响模型校准。实验室 latest_value 变量为 latest-available / capped carry-forward 值，不代表每小时真实测量；由于 result availability time 在当前模型 ready 层不完整，本研究使用 chart/sample time 作为保守近似，这不能完全替代真实报告可用时间。正式部署前需要完成变量映射审计、缺失率评估、单位一致性检查、实验室 freshness 评估和本地再校准，并应避免将 shared support-intensity proxy 解释为 full VIS 或直接治疗建议。
"""
    checklist = """# P15 作者投稿前核对清单

- [ ] 核对每个支持强度代理变量的精确定义，尤其是 MAP deficit、MAP below 65 burden、lactate burden、oliguria burden、renal trajectory worsening、FiO2/SpO2 burden 和 ventilation transition count。
- [ ] 核对 MIMIC-IV 与 eICU 的字段映射表；当前项目文件确认到概念级表/字段，未找到完整 itemid 级映射。
- [ ] 核对各 P15 特征在 MIMIC-IV 和 eICU 中的最终缺失率；当前输出已整理 model-ready/registry 缺失率，但若主文逐项报告，建议作者重新从最终 model-ready 表复核。
- [ ] 核对单位转换规则；当前文件说明已 canonicalized，但未完整展开具体单位换算。
- [ ] 核对实验室前向携带最大窗口和 freshness 规则；当前结果显示 12h borderline acceptable、24h largely stable。
- [ ] 核对 t_sepsis 电子表型规则，包括 suspected infection、SOFA 变化和入室即脓毒症定义。
- [ ] 核对 P12/P10 删除变量清单是否与 true-training 脚本一致。
- [ ] 确认所有支持强度代理变量只使用 t_pred 及之前的信息，未引入预测时点后的治疗状态或实验室结果。
- [ ] 判断目标医院是否需要本地再校准，特别是在支持治疗文档和实验室报告时间不同的系统中。
- [ ] 决定表 X 放主文还是补充材料；建议主文概述来源和部署边界，逐项字段映射/缺失率放补充表。
"""
    (OUT_TEXT / "P15_methods_insert_zh.md").write_text(methods, encoding="utf-8")
    (OUT_TEXT / "P15_results_insert_zh.md").write_text("# Results 插入段落：P12/P10 低负担实现验证\n\n" + results_para + "\n", encoding="utf-8")
    (OUT_TEXT / "P15_discussion_insert_zh.md").write_text(discussion, encoding="utf-8")
    (OUT_TEXT / "P15_limitations_insert_zh.md").write_text(limitations, encoding="utf-8")
    (OUT_TEXT / "P15_author_checklist_before_submission.md").write_text(checklist, encoding="utf-8")


def main() -> None:
    source_df = write_source_availability()
    mapping_df = write_mapping_audit()
    missing_df = write_missingness_audit()
    write_text_outputs()
    direct_count = int(source_df["是否可直接抽取"].str.startswith("是").sum())
    phenotype_count = int(source_df["是否可直接抽取"].str.contains("电子表型").sum())
    mapping_count = int(source_df["是否可直接抽取"].str.contains("字段映射").sum())
    confirmed_missingness_count = int((missing_df["MIMIC-IV 缺失率"] != "未确认").sum())
    unresolved_itemid_count = int(mapping_df["备注"].str.contains("itemid|原始字段|单位需作者", regex=True).sum())
    outputs = [
        OUT_TEXT / "P15_feature_implementation_audit.md",
        OUT_TABLES / "P15_feature_source_availability_deployment_table.csv",
        OUT_TABLES / "P15_feature_mapping_audit.csv",
        OUT_TABLES / "P15_feature_missingness_audit.csv",
        OUT_TEXT / "P15_methods_insert_zh.md",
        OUT_TEXT / "P15_results_insert_zh.md",
        OUT_TEXT / "P15_discussion_insert_zh.md",
        OUT_TEXT / "P15_limitations_insert_zh.md",
        OUT_TEXT / "P15_author_checklist_before_submission.md",
    ]
    print(json.dumps({
        "p15_feature_count": len(P15),
        "direct_extractable_count": direct_count,
        "requires_e_phenotype_count": phenotype_count,
        "requires_local_mapping_count": mapping_count,
        "confirmed_missingness_count": confirmed_missingness_count,
        "unresolved_exact_itemid_or_unit_count": unresolved_itemid_count,
        "outputs": [rel(path) for path in outputs],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
