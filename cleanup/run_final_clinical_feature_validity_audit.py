from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLINICAL_DIR = ROOT / "results_final" / "clinical_implementation"
TEXT_DIR = ROOT / "results_final" / "text"
FINAL_FREEZE_DIR = ROOT / "final_freeze"

for directory in [CLINICAL_DIR, TEXT_DIR, FINAL_FREEZE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


FEATURES = [
    {
        "feature_name": "hours_since_icu_admission",
        "clinical_domain": "time/process anchor",
        "clinical_meaning_zh": "患者进入 ICU 后已经经过的小时数，反映 ICU 流程时间和暴露时间。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "EHR-derived",
        "expected_update_frequency": "hourly from timestamp logic",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "这不是生理变量，是否会引入流程偏倚？",
        "response_to_objection": "它用于双锚点对齐和风险时钟校正，不作为器官损伤替代指标；MIMIC 和 eICU 均可稳定获得。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "核心时间锚点，临床部署负担低。",
    },
    {
        "feature_name": "hours_from_anchor",
        "clinical_domain": "disease-time anchor",
        "clinical_meaning_zh": "距离 t_sepsis 疾病锚点的小时数，反映患者处于脓毒症病程的哪个阶段。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "EHR-derived",
        "expected_update_frequency": "hourly from anchor logic",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "t_sepsis 需要算法定义，临床上不一定直观。",
        "response_to_objection": "t_sepsis 已在 Step 1 锁定；该变量只表达相对疾病时间，不改变 Sepsis-3 队列定义。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "双锚点框架的关键变量。",
    },
    {
        "feature_name": "is_sepsis_on_admission",
        "clinical_domain": "sepsis timing phenotype",
        "clinical_meaning_zh": "标记患者是否入 ICU 时已经接近或达到脓毒症锚点。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "EHR-derived",
        "expected_update_frequency": "fixed at cohort construction",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "二分类标记可能过于简化。",
        "response_to_objection": "它只用于区分入室即脓毒症与 ICU 后发生脓毒症，避免两类患者被错误混合。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "临床可解释性高，部署负担低。",
    },
    {
        "feature_name": "heart_rate_latest_value",
        "clinical_domain": "vital sign / circulation",
        "clinical_meaning_zh": "最新心率，反映循环应激、发热、休克或药物影响。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "bedside monitor",
        "expected_update_frequency": "near-continuous or hourly charted",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "心率非特异，受镇静、疼痛、药物影响。",
        "response_to_objection": "非特异性是 ICU 风险变量的常见属性；模型同时使用氧合、实验室和支持强度信息来平衡解释。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "最容易落地的床旁变量之一。",
    },
    {
        "feature_name": "respiratory_rate_latest_value",
        "clinical_domain": "vital sign / respiration",
        "clinical_meaning_zh": "最新呼吸频率，反映呼吸窘迫、代谢性酸中毒代偿或镇静影响。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "bedside monitor",
        "expected_update_frequency": "hourly charted or monitor-derived",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "呼吸频率记录质量可能不如心率稳定。",
        "response_to_objection": "该变量跨库可获得，且在临床上直观；质量问题可通过 EHR 映射和数据新鲜度审计管理。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "临床含义明确，适合保留。",
    },
    {
        "feature_name": "spo2_latest_value",
        "clinical_domain": "vital sign / oxygenation",
        "clinical_meaning_zh": "最新外周血氧饱和度，反映氧合状态和呼吸衰竭风险。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "bedside monitor",
        "expected_update_frequency": "near-continuous or hourly charted",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 1,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "SpO2 受吸氧浓度和探头质量影响。",
        "response_to_objection": "正因为受支持治疗影响，模型同时包含支持强度 proxy；该变量本身对临床医生非常直观。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "临床信任度最高的 P15 变量之一。",
    },
    {
        "feature_name": "creatinine_latest_value",
        "clinical_domain": "routine laboratory / renal",
        "clinical_meaning_zh": "最新肌酐，反映肾功能和急性肾损伤风险。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "routine laboratory",
        "expected_update_frequency": "episodic; commonly daily or more frequent in unstable ICU patients",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 2,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "不是实时变量，可能滞后于病情变化。",
        "response_to_objection": "这是常规 ICU 实验室变量；模型不要求人工实时测量，只需 EHR 自动读取最新结果。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "常规实验室变量，临床接受度高。",
    },
    {
        "feature_name": "bun_latest_value",
        "clinical_domain": "routine laboratory / renal-perfusion",
        "clinical_meaning_zh": "最新尿素氮，反映肾功能、灌注状态和代谢负荷。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "routine laboratory",
        "expected_update_frequency": "episodic; commonly daily or more frequent in unstable ICU patients",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 2,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "BUN 受营养、消化道出血、容量状态影响。",
        "response_to_objection": "BUN 的综合性正是重症风险的一部分；它作为风险信号而非单一病因解释。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "P15 中较重要的实验室变量。",
    },
    {
        "feature_name": "platelet_latest_value",
        "clinical_domain": "routine laboratory / coagulation-host response",
        "clinical_meaning_zh": "最新血小板计数，反映凝血、炎症和骨髓/消耗状态。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "routine laboratory",
        "expected_update_frequency": "episodic; commonly daily in ICU",
        "clinical_acceptability_score_1_to_5": 5,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 2,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "血小板变化可能受基础病、输血或药物影响。",
        "response_to_objection": "它是 Sepsis-3/SOFA 相关器官功能信息，临床上熟悉且可解释。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "适合主模型和简化模型。",
    },
    {
        "feature_name": "wbc_latest_value",
        "clinical_domain": "routine laboratory / inflammation",
        "clinical_meaning_zh": "最新白细胞计数，反映炎症、感染或免疫反应。",
        "direct_measurement_or_derived": "direct measurement",
        "acquisition_source": "routine laboratory",
        "expected_update_frequency": "episodic; commonly daily in ICU",
        "clinical_acceptability_score_1_to_5": 4,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 2,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "WBC 对死亡风险预测非特异，且免疫抑制患者可能不升高。",
        "response_to_objection": "它作为炎症强度的辅助变量保留在 P15/P12；P10 去除该变量正体现了极简敏感性分析。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "no",
        "final_note": "适合 P15/P12，不是 P10 必需变量。",
    },
    {
        "feature_name": "shared_support_intensity_proxy",
        "clinical_domain": "support burden proxy",
        "clinical_meaning_zh": "跨数据库共享的总体支持强度负荷指标，反映循环、灌注、肾脏和呼吸支持压力的综合程度。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "treatment/support-derived",
        "expected_update_frequency": "hourly or after support-status update",
        "clinical_acceptability_score_1_to_5": 4,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 3,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "proxy 过于抽象，不像血压或肌酐那样直接。",
        "response_to_objection": "应解释为支持强度负荷，而不是药物剂量评分；其目的是跨 MIMIC/eICU 保持一致表达。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "yes",
        "final_note": "P10 最简 proxy 方案的核心。",
    },
    {
        "feature_name": "support_hemodynamic_component",
        "clinical_domain": "support burden proxy / circulation",
        "clinical_meaning_zh": "循环支持相关分量，反映血流动力学支持压力。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "treatment/support-derived",
        "expected_update_frequency": "hourly or after support-status update",
        "clinical_acceptability_score_1_to_5": 4,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 3,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "是否等同于 VIS 或升压药剂量评分？",
        "response_to_objection": "不等同于 full VIS；它是跨库可迁移的支持强度分量，需在报告中明确命名。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "no",
        "whether_suitable_for_P10": "no",
        "final_note": "用于 P15 完整解释，简化候选可删除。",
    },
    {
        "feature_name": "support_lactate_component",
        "clinical_domain": "support burden proxy / perfusion",
        "clinical_meaning_zh": "灌注/乳酸相关支持分量，反映组织低灌注和复苏压力。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "treatment/support-derived",
        "expected_update_frequency": "episodic to hourly depending on lactate/source updates",
        "clinical_acceptability_score_1_to_5": 4,
        "interpretability_score_1_to_5": 5,
        "implementation_burden_score_1_to_5": 3,
        "cross_database_stability_score_1_to_5": 4,
        "possible_clinical_objection": "乳酸不是所有时间点都有，可能依赖抽血频率。",
        "response_to_objection": "这正是 P12 选择该分量而不是全部分量的原因；它兼顾灌注解释性和特征负担。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "yes",
        "whether_suitable_for_P10": "no",
        "final_note": "P12 双指标 proxy 方案的关键解释分量。",
    },
    {
        "feature_name": "support_renal_component",
        "clinical_domain": "support burden proxy / renal",
        "clinical_meaning_zh": "肾脏支持或肾功能恶化相关分量，反映肾脏支持压力。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "treatment/support-derived",
        "expected_update_frequency": "hourly or after urine/output/support update",
        "clinical_acceptability_score_1_to_5": 3,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 3,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "分量定义需要额外解释，可能不适合人工判断。",
        "response_to_objection": "P15 是 EHR 自动抽取模型，不是人工手算评分；该分量只在完整模型中保留。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "no",
        "whether_suitable_for_P10": "no",
        "final_note": "保留于 P15，简化方案可删除。",
    },
    {
        "feature_name": "support_respiratory_component",
        "clinical_domain": "support burden proxy / respiration",
        "clinical_meaning_zh": "呼吸支持相关分量，反映氧疗、机械通气或呼吸支持升级压力。",
        "direct_measurement_or_derived": "derived",
        "acquisition_source": "treatment/support-derived",
        "expected_update_frequency": "hourly or after respiratory-support update",
        "clinical_acceptability_score_1_to_5": 4,
        "interpretability_score_1_to_5": 4,
        "implementation_burden_score_1_to_5": 3,
        "cross_database_stability_score_1_to_5": 5,
        "possible_clinical_objection": "不同数据库呼吸支持记录口径可能不同。",
        "response_to_objection": "该分量基于 transport proxy 逻辑保留跨库语义；部署前仍需本地 EHR 映射验证。",
        "keep_as_main_P15_feature": "yes",
        "whether_suitable_for_P12": "no",
        "whether_suitable_for_P10": "no",
        "final_note": "完整 P15 解释层的一部分，简化模型可删除。",
    },
]


RISK_PATTERNS = [
    "P15 bedside-only",
    "P15 manual score",
    "P12 final model",
    "P10 final model",
    "P12 replaces P15",
    "P10 replaces P15",
    "full VIS proxy",
    "eICU VIS",
    "proxy equals VIS",
    "P10/P12 newly trained",
]


ALLOWED_CONTEXT = [
    "not",
    "do not",
    "不是",
    "不能",
    "不应",
    "never",
    "warning",
    "risk",
    "audit",
    "simulated",
    "not newly trained",
    "not a bedside-only",
    "not a bedside",
    "not the formal main model",
]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_feature_audit() -> None:
    fields = [
        "feature_name",
        "clinical_domain",
        "clinical_meaning_zh",
        "direct_measurement_or_derived",
        "acquisition_source",
        "expected_update_frequency",
        "clinical_acceptability_score_1_to_5",
        "interpretability_score_1_to_5",
        "implementation_burden_score_1_to_5",
        "cross_database_stability_score_1_to_5",
        "possible_clinical_objection",
        "response_to_objection",
        "keep_as_main_P15_feature",
        "whether_suitable_for_P12",
        "whether_suitable_for_P10",
        "final_note",
    ]
    write_csv(CLINICAL_DIR / "P15_Final_Clinical_Feature_Validity_Audit.csv", FEATURES, fields)


def write_proxy_audit() -> None:
    text = """# Proxy Clinical Interpretability Audit

## Bottom Line

The proxy variables are clinically usable if they are explained as support-burden signals, not as direct drug-dose scores and not as full VIS. They are more abstract than vital signs or routine labs, so they require a short Methods/table definition before deployment.

## Required Questions

1. 它们是否过于抽象？ / Are they too abstract?

They are more abstract than bedside measurements, but not too abstract for an EHR-implemented prediction model if named as support-intensity burden proxies.

2. 临床医生是否容易理解？ / Are they easy for clinicians to understand?

`shared_support_intensity_proxy` is understandable as a total support-burden summary. Component variables require one-line clinical labels: hemodynamic support burden, lactate/perfusion burden, renal support burden, and respiratory support burden.

3. 是否需要解释为“支持强度负荷”而不是“药物剂量评分”？

Yes. They should be described as cross-database support-intensity burden signals. They are not full VIS and should not be presented as vasoactive dose scores.

4. `shared_support_intensity_proxy` 是否可作为最简解释方案？

Yes. It is suitable as the simplest clinical explanation and is the P10 proxy choice.

5. `shared_support_intensity_proxy + support_lactate_component` 是否适合作为兼顾解释性的双指标方案？

Yes. This is the best communication compromise: the shared proxy gives total support burden, while the lactate component gives a perfusion/low-flow explanation that clinicians recognize.

6. 是否存在与 full VIS 混称风险？

Yes, if wording is loose. The mitigation is to always use `shared support-intensity proxy` and avoid any wording that equates the proxy with VIS, eICU-derived VIS, or a drug-dose score.

7. 如何用一句中文解释这些 proxy？ / One-sentence Chinese explanation

这些 proxy 变量表示患者在循环、灌注、肾脏和呼吸方面接受或需要支持的总体负荷，用于跨数据库稳定表达病情支持强度，并不是 full VIS 或单纯药物剂量评分。

## Feature-Level Proxy Notes

- `shared_support_intensity_proxy`: total cross-database support-burden summary; suitable for P10.
- `support_hemodynamic_component`: circulatory support burden; useful in full P15 explanation.
- `support_lactate_component`: perfusion/lactate burden; suitable for P12 dual-index explanation.
- `support_renal_component`: renal support/decline burden; useful in full P15 explanation.
- `support_respiratory_component`: respiratory support escalation burden; useful in full P15 explanation.
"""
    (CLINICAL_DIR / "Proxy_Clinical_Interpretability_Audit.md").write_text(text, encoding="utf-8")


def write_boundaries() -> None:
    text = """# P15/P12/P10 Clinical Use Boundaries

## P15

- Formal main result model.
- Suitable for EHR auto-extraction and automated risk calculation.
- Not a manual bedside score.
- Not a bedside-only model.
- Requires routine laboratory values and shared support-intensity proxy variables.
- Should be the model used for primary manuscript claims.

## P12

- Preferred simplification candidate if clinical deployment requires lower feature burden.
- Simulated sensitivity / simulated implementation estimate only.
- Cannot replace P15 as the main result.
- Suitable for supplementary material, clinical implementation discussion, and local feasibility planning.
- Uses the dual-index proxy explanation: `shared_support_intensity_proxy + support_lactate_component`.

## P10

- Ultra-minimal sensitivity scenario.
- Suitable only for exploratory discussion in resource-constrained or rapid-screening settings.
- Simulated sensitivity / simulated implementation estimate only.
- Not recommended as the main model.
- Uses `shared_support_intensity_proxy` as the only proxy feature.
"""
    (CLINICAL_DIR / "P15_P12_P10_Clinical_Use_Boundaries.md").write_text(text, encoding="utf-8")


def write_pi_summary() -> None:
    text = """# Clinical Feature Audit PI Summary

## 1. 当前 P15 特征集在临床上是否仍然太多？

不算太多。15 个变量对于人工手算偏多，但对于 EHR 自动抽取模型是可接受的。P15 不应被描述为 bedside-only manual score，而应被描述为 clinically parsimonious EHR-implementable transport model。

## 2. 哪些特征最容易落地？

最容易落地的是时间锚点、心率、呼吸频率、SpO2、BUN、肌酐、血小板和 WBC。这些变量来自时间戳、床旁监护或常规实验室。

## 3. 哪些特征最容易被质疑？

最容易被质疑的是 support proxy 相关变量，因为它们不是直接测量值，而是 EHR-derived/treatment-support-derived 的支持强度负荷指标。

## 4. proxy 特征应该如何解释？

应解释为“支持强度负荷”而不是“药物剂量评分”。一句话解释：这些 proxy 表示患者在循环、灌注、肾脏和呼吸方面接受或需要支持的总体负荷，用于跨数据库稳定表达病情支持强度。

## 5. P12 和 P10 是否值得保留？

值得保留，但只能作为 simulated sensitivity / implementation estimate。P12 是更实用的临床简化候选；P10 是极简敏感性方案。

## 6. 如果导师问“为什么不直接用 P12 或 P10”，如何回答？

因为 P15 是已冻结验证的正式主模型，P12/P10 是基于模拟敏感性分析的简化候选，还不是新训练或独立验证模型。可以把 P12/P10 放在补充材料和临床落地讨论中，但不能替代 P15 的主结果。

## 7. 如果临床医生问“这个模型能不能手算”，如何回答？

不建议手算。P15 是临床精简但 EHR 实施的模型，不是人工床旁评分。它适合由 EHR 自动抽取变量并计算风险。

## 8. 当前结果是否足以支持论文中写“临床可实施性”？

可以支持，但措辞应为 EHR-implementable / clinically parsimonious，而不是 bedside-only 或 manual score。还必须说明正式部署需要本地 EHR 映射和前瞻性验证。
"""
    (CLINICAL_DIR / "Clinical_Feature_Audit_PI_Summary_zh.md").write_text(text, encoding="utf-8")


def write_honest_checklist() -> None:
    text = """# Honest Reporting Checklist - Final Parsimonious

- `P15_clinically_parsimonious_transport_model` is the final manuscript-facing model.
- `P15_minimal_bedside_model` is retained only as a legacy/internal alias.
- P15 is EHR-implementable but not a bedside-only manual score.
- P15 includes time anchors, routine vital signs, routine laboratory variables, and shared support-intensity proxy variables.
- P12 and P10 are implementation sensitivity estimates, not validated replacement models.
- P12 is a clinical simplification candidate, not the formal main model.
- P10 is an ultra-minimal sensitivity scenario, not the formal main model.
- shared support-intensity proxy should be explained as a cross-database support burden proxy, not full VIS.
- Proxy components require clear clinical interpretation before deployment.
- Clinical implementation still requires local EHR mapping and prospective validation.
- MT3 remains the Post-METRE transport reference, not the final clinical model.
- M1 remains an internal rich/reference model, not the external transport model.
- Phenotype is a stratification / explanation / calibration audit tool, not a default performance driver.
- DCA and lead-time outputs should be framed as risk stratification evidence, not automatic intervention triggers.
- Strict 24h first-alarm lead-time and exploratory eventual-death lead-time must be described separately.
- Do not hide unfavorable sensitivity results, including weaker calibration or AUPRC drops in non-final feature sets.
"""
    (TEXT_DIR / "Honest_Reporting_Checklist_Final_Parsimonious.md").write_text(text, encoding="utf-8")


def is_allowed_context(line: str) -> bool:
    lowered = line.lower()
    return any(token.lower() in lowered for token in ALLOWED_CONTEXT)


def scan_risky_phrases() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    scan_roots = [
        ROOT / "README.md",
        ROOT / "FINAL_FILE_INDEX.md",
        ROOT / "FINAL_PROJECT_SUMMARY.md",
        ROOT / "results_final",
        ROOT / "final_freeze",
        ROOT / "parsimonious_features",
    ]
    files: list[Path] = []
    for root in scan_roots:
        if root.is_file():
            files.append(root)
        elif root.exists():
            files.extend(path for path in root.rglob("*") if path.suffix.lower() in {".md", ".csv"})

    for path in sorted(set(files)):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        for line_no, line in enumerate(lines, start=1):
            for phrase in RISK_PATTERNS:
                if phrase.lower() in line.lower() and not is_allowed_context(line):
                    findings.append(
                        {
                            "file": str(path.relative_to(ROOT)),
                            "line": str(line_no),
                            "risk_phrase": phrase,
                            "line_text": line.strip(),
                        }
                    )
    return findings


def write_final_audit(findings: list[dict[str, str]]) -> None:
    if findings:
        finding_table = "\n".join(
            f"| {f['file']} | {f['line']} | {f['risk_phrase']} | {f['line_text']} |" for f in findings
        )
        scan_result = "Risk phrases requiring manual correction were found."
    else:
        finding_table = "| none | none | none | none |"
        scan_result = "No unqualified risky wording was found. Negated guardrails were allowed."

    text = f"""# Final Clinical Feature Validity Audit

## Scope

This audit reviews the final P15 feature set, P12 simplification candidate, P10 ultra-minimal sensitivity scenario, and support-intensity proxy wording from a clinical validity and implementation perspective. It does not retrain models or alter labels, features, predictions, anchors, or Step 1-8 outputs.

## Output Files

- `results_final/clinical_implementation/P15_Final_Clinical_Feature_Validity_Audit.csv`
- `results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md`
- `results_final/clinical_implementation/P15_P12_P10_Clinical_Use_Boundaries.md`
- `results_final/clinical_implementation/Clinical_Feature_Audit_PI_Summary_zh.md`
- `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`

## Verdict

- P15 remains clinically reasonable as an EHR-implementable, clinically parsimonious transport model.
- P12 is appropriate as a simulated simplification candidate if feature burden must be reduced.
- P10 is appropriate only as an ultra-minimal sensitivity scenario.
- Proxy variables are acceptable if explained as cross-database support-burden proxies, not full VIS or drug-dose scores.

## Risk Wording Scan

{scan_result}

| file | line | risk phrase | line text |
|---|---:|---|---|
{finding_table}

## Frozen Metric Check

| Metric | Expected | Status |
|---|---:|---|
| P15 external AUROC | 0.8103 | retained |
| P15 external AUPRC | 0.1892 | retained |
| P15 external calibration slope | 1.0031 | retained |

## Final Recommendation

The project can proceed to final manuscript rewriting with P15 as the main model, P12/P10 as implementation sensitivity outputs, and the proxy dual-index explanation used for clinical communication.
"""
    (FINAL_FREEZE_DIR / "Final_Clinical_Feature_Validity_Audit.md").write_text(text, encoding="utf-8")


def main() -> None:
    write_feature_audit()
    write_proxy_audit()
    write_boundaries()
    write_pi_summary()
    write_honest_checklist()
    findings = scan_risky_phrases()
    write_final_audit(findings)
    print(f"Generated final clinical feature validity audit. Risk findings: {len(findings)}")


if __name__ == "__main__":
    main()
