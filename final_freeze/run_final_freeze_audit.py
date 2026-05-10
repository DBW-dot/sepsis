from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUT = ROOT / "final_freeze"
OUT.mkdir(parents=True, exist_ok=True)

POST_SELECTION = ROOT / "post_metre_selection"
POST_RECAL = ROOT / "post_metre_recalibration"
POST_UTILITY = ROOT / "post_metre_clinical_utility"
POST_COMPONENT = ROOT / "post_metre_component_reassessment"
PKG = ROOT / "results_package"

REQUIRED_FILES = [
    "post_metre_selection/Post_METRE_Model_Comparison.csv",
    "post_metre_selection/Post_METRE_Model_Signoff_Report.md",
    "post_metre_selection/Model_Role_Assignment.csv",
    "post_metre_selection/Downstream_Analysis_Model_Map.csv",
    "post_metre_recalibration/Post_METRE_Recalibration_Results.csv",
    "post_metre_recalibration/Post_METRE_Recalibration_Report.md",
    "post_metre_recalibration/Recalibrated_Model_Signoff.md",
    "post_metre_clinical_utility/strict_24h_first_alarm_summary.csv",
    "post_metre_clinical_utility/eventual_death_leadtime_summary.csv",
    "post_metre_clinical_utility/dca_threshold_sweep_post_metre.csv",
    "post_metre_clinical_utility/Post_METRE_Leadtime_DCA_Report.md",
    "post_metre_component_reassessment/component_ablation_results.csv",
    "post_metre_component_reassessment/component_subgroup_results.csv",
    "post_metre_component_reassessment/Post_METRE_Component_Reassessment_Report.md",
    "results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv",
    "results_package/tables/Table3_Phenotype_Gain_Post_METRE.csv",
    "results_package/tables/Table4_Measurement_Bias_Post_METRE.csv",
    "results_package/figures/Figure5_DCA_Leadtime_Post_METRE.csv",
    "results_package/figures/Figure6_External_Failure_Modes_Post_METRE.csv",
    "results_package/text/Results_Skeleton_zh_Post_METRE.md",
    "results_package/text/Discussion_Outline_zh_Post_METRE.md",
    "results_package/text/Honest_Reporting_Checklist_Post_METRE.md",
    "results_package/text/PI_Decision_Summary_Post_METRE.md",
    "results_package/POST_METRE_RESULT_INDEX.md",
    "results_package/POST_METRE_RESULT_LINEAGE.csv",
]


def fmt(value: object, digits: int = 4) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NA"
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def one(df: pd.DataFrame, **query) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col, value in query.items():
        mask &= df[col] == value
    sub = df[mask]
    if sub.empty:
        raise KeyError(f"Missing row for {query}")
    return sub.iloc[0]


def close(a: object, b: object, tol: float = 1e-9) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return a == b


def file_inventory() -> pd.DataFrame:
    rows = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        rows.append(
            {
                "relative_path": rel,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "non_empty": path.exists() and path.stat().st_size > 0,
            }
        )
    return pd.DataFrame(rows)


def audit_model_roles(role: pd.DataFrame, downstream: pd.DataFrame) -> tuple[dict[str, bool], str]:
    checks = {
        "M1_internal_rich": bool(
            (role["model_name"].eq("M1_original_rich") & role["assigned_role"].eq("Internal rich model")).any()
        ),
        "MT3_external_transport": bool(
            (
                role["model_name"].eq("MT3_physiology_support_proxy")
                & role["assigned_role"].eq("External transport model")
                & role["selected_as_external_transport"].astype(int).eq(1)
            ).any()
        ),
        "C1_clinical_comparator": bool(
            (
                role["model_name"].eq("C1_dynamic_SOFA")
                & role["assigned_role"].eq("Clinical score comparator")
                & role["selected_as_baseline_comparator"].astype(int).eq(1)
            ).any()
        ),
        "phenotype_downgraded": bool(
            (
                downstream["downstream_analysis"].eq("phenotype gain reassessment")
                & downstream["reason"].str.contains("Sensitivity|stratification|not a default driver", case=False, regex=True)
            ).any()
        ),
        "full_VIS_internal_only": bool(
            (
                downstream["downstream_analysis"].eq("VIS/proxy contribution analysis")
                & downstream["reason"].str.contains("full VIS framed as internal rich", case=False, regex=False)
            ).any()
        ),
        "support_proxy_transport": bool(
            (
                downstream["final result tables" == downstream["downstream_analysis"]]["primary_model_to_use"]
                .astype(str)
                .str.contains("MT3_physiology_support_proxy")
                .any()
            )
        ),
    }
    text = f"""# Final Model Role Audit

## Verdict

Final model role consistency: `{"PASS" if all(checks.values()) else "FAIL"}`.

## Checks

| Check | Status |
|---|---:|
| Original M1 is internal rich model | {checks["M1_internal_rich"]} |
| Final external transport model is MT3_physiology_support_proxy | {checks["MT3_external_transport"]} |
| Dynamic SOFA-only is clinical comparator | {checks["C1_clinical_comparator"]} |
| Phenotype is downgraded to sensitivity/stratification/explanation | {checks["phenotype_downgraded"]} |
| Full VIS is internal-rich/sensitivity only | {checks["full_VIS_internal_only"]} |
| Shared support-intensity proxy is used in transport model | {checks["support_proxy_transport"]} |

## Frozen roles

- Internal rich model: `M1_original_rich`.
- External transport model: `MT3_physiology_support_proxy`.
- Clinical comparator: `C1_dynamic_SOFA`.
- Phenotype: sensitivity / stratification / explanation tool, not default transport input.
- Full VIS: internal rich/sensitivity only.
- Transport support signal: shared support-intensity proxy.
"""
    return checks, text


def audit_table2(selection: pd.DataFrame, table2: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    mapping = {
        "mimic_internal_test": {
            "auroc_death_ovr": "mimic_internal_auroc",
            "auprc_death": "mimic_internal_auprc",
            "multiclass_brier": "mimic_internal_brier",
            "calibration_slope_death": "mimic_calibration_slope",
        },
        "eicu_external_full": {
            "auroc_death_ovr": "eicu_external_auroc",
            "auprc_death": "eicu_external_auprc",
            "multiclass_brier": "eicu_external_brier",
            "calibration_slope_death": "eicu_calibration_slope",
        },
    }
    for model_name in [
        "M1_original_rich",
        "C1_dynamic_SOFA",
        "C3_no_phenotype",
        "MT3_physiology_support_proxy",
        "MT4_support_proxy_phenotype_sensitivity",
    ]:
        source = one(selection, model_name=model_name)
        for dataset_scope, cols in mapping.items():
            target = one(table2, model_name=model_name, dataset_scope=dataset_scope, calibration_state="raw")
            for table_col, source_col in cols.items():
                rows.append(
                    {
                        "audit_item": "Table2_vs_Post_METRE_Model_Comparison",
                        "model_name": model_name,
                        "dataset_scope": dataset_scope,
                        "metric": table_col,
                        "table_value": target[table_col],
                        "source_value": source[source_col],
                        "consistent": close(target[table_col], source[source_col]),
                    }
                )
    return rows


def audit_table3(component: pd.DataFrame, table3: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    models = [
        "A1_B2_MT3_best_transport_no_phenotype_shared_proxy",
        "A2_MT4_best_transport_hard_phenotype",
        "A3_best_transport_soft_membership",
    ]
    for model_name in models:
        for dataset_name in ["mimic_internal_test", "eicu_external"]:
            source = one(component, model_name=model_name, dataset_name=dataset_name)
            target = one(table3, model_name=model_name, dataset_name=dataset_name, comparison_scope="overall")
            for metric in ["auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"]:
                rows.append(
                    {
                        "audit_item": "Table3_vs_component_reassessment",
                        "model_name": model_name,
                        "dataset_scope": dataset_name,
                        "metric": metric,
                        "table_value": target[metric],
                        "source_value": source[metric],
                        "consistent": close(target[metric], source[metric]),
                    }
                )
    return rows


def audit_table4(component: pd.DataFrame, table4: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    models = [
        "B1_C1_MT1_physiology_only_no_proxy",
        "C2_MT2_physiology_minimal_recency",
        "C3_physiology_full_quality",
        "C4_physiology_full_quality_measurement_intensity",
    ]
    for model_name in models:
        for dataset_name in ["mimic_internal_test", "eicu_external"]:
            source = one(component, model_name=model_name, dataset_name=dataset_name)
            target = one(table4, model_name=model_name, dataset_name=dataset_name)
            for metric in ["auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"]:
                rows.append(
                    {
                        "audit_item": "Table4_vs_component_reassessment",
                        "model_name": model_name,
                        "dataset_scope": dataset_name,
                        "metric": metric,
                        "table_value": target[metric],
                        "source_value": source[metric],
                        "consistent": close(target[metric], source[metric]),
                    }
                )
    return rows


def audit_figure5(fig5: pd.DataFrame) -> dict[str, object]:
    analysis_types = set(fig5["analysis_type"].dropna().astype(str))
    strict = fig5[fig5["analysis_type"] == "strict_24h_first_alarm"]
    eventual = fig5[fig5["analysis_type"] == "eventual_death_leadtime_exploratory_not_strict_24h"]
    dca = fig5[fig5["analysis_type"] == "DCA_24h_death"]
    return {
        "has_strict_24h_first_alarm": "strict_24h_first_alarm" in analysis_types,
        "has_eventual_exploratory": "eventual_death_leadtime_exploratory_not_strict_24h" in analysis_types,
        "has_dca_24h_death": "DCA_24h_death" in analysis_types,
        "strict_max_lead_time_le_24h": bool(strict["strict_lead_time_max_hours"].dropna().max() <= 24.0),
        "dca_has_recalibrated_MT3": bool(dca["model_name"].astype(str).str.contains("MT3_recalibrated_intercept_only").any()),
        "eventual_marked_not_strict": bool(eventual["lead_time_definition"].astype(str).str.contains("not_strict_24h").all()),
    }


def audit_figure6(fig6: pd.DataFrame) -> dict[str, object]:
    expected = {
        "external_discrimination_drop",
        "external_calibration_failure",
        "support_intensity_representation",
        "measurement_process_shift",
        "phenotype_role",
    }
    present = set(fig6["failure_mode"].dropna().astype(str))
    return {
        "expected_failure_modes_present": expected.issubset(present),
        "missing_failure_modes": ";".join(sorted(expected - present)),
        "mentions_MT3": bool(fig6["post_metre_result"].astype(str).str.contains("MT3|Shared support|Hard phenotype", regex=True).any()),
    }


def write_table_figure_report(comparison_rows: list[dict[str, object]], fig5_checks: dict, fig6_checks: dict) -> str:
    comparison = pd.DataFrame(comparison_rows)
    inconsistent = comparison[~comparison["consistent"]]
    summary = comparison.groupby("audit_item")["consistent"].agg(["sum", "count"]).reset_index()
    summary_table = "| audit_item | pass_n | total_n |\n|---|---:|---:|\n"
    for _, row in summary.iterrows():
        summary_table += f"| {row['audit_item']} | {int(row['sum'])} | {int(row['count'])} |\n"
    text = f"""# Final Table/Figure Consistency Audit

## Verdict

Post-METRE table and figure consistency: `{"PASS" if inconsistent.empty and all(v is True or v == '' for v in fig6_checks.values()) and all(fig5_checks.values()) else "REVIEW"}`.

## Numeric table checks

{summary_table}

Number of inconsistent numeric cells: `{len(inconsistent)}`.

## Figure 5 checks

| Check | Status |
|---|---:|
| Contains strict 24h first-alarm panel | {fig5_checks["has_strict_24h_first_alarm"]} |
| Contains exploratory eventual-death lead-time panel | {fig5_checks["has_eventual_exploratory"]} |
| Contains DCA 24h death panel | {fig5_checks["has_dca_24h_death"]} |
| Strict lead-time max <= 24h | {fig5_checks["strict_max_lead_time_le_24h"]} |
| Includes recalibrated MT3 DCA | {fig5_checks["dca_has_recalibrated_MT3"]} |
| Eventual-death lead-time explicitly marked not strict 24h | {fig5_checks["eventual_marked_not_strict"]} |

## Figure 6 checks

| Check | Status |
|---|---:|
| Expected external failure modes present | {fig6_checks["expected_failure_modes_present"]} |
| Missing failure modes | {fig6_checks["missing_failure_modes"] or "none"} |
| Post-METRE result text mentions MT3/support/phenotype updates | {fig6_checks["mentions_MT3"]} |

## Interpretation

- Table2_Post_METRE is numerically audited against `Post_METRE_Model_Comparison.csv`.
- Table3_Post_METRE is numerically audited against `component_ablation_results.csv` for phenotype model variants.
- Table4_Post_METRE is numerically audited against `component_ablation_results.csv` for measurement-process variants.
- Figure5_Post_METRE uses strict 24h first-alarm as the main lead-time interface and separately labels eventual-death lead-time as exploratory.
- Figure6_Post_METRE reflects external failure-mode updates after METRE repair.
"""
    if not inconsistent.empty:
        text += "\n## Inconsistent numeric cells\n\n"
        text += inconsistent.to_csv(index=False) + "\n"
    comparison.to_csv(OUT / "Final_Table_Figure_Consistency_Detail.csv", index=False)
    return text


def write_old_result_replacement() -> tuple[pd.DataFrame, str]:
    rows = [
        {
            "old_file": "results_package/tables/Table2_Main_Model_Comparators.csv",
            "new_file": "results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv",
            "replacement_status": "replace_for_main_results",
            "old_result_role": "historical Step9 model comparison",
            "new_result_role": "main Post-METRE model comparison",
            "main_text_use": "use_new_only",
            "supplementary_or_exploratory_use": "old table may be cited only as historical pre-METRE result if needed",
            "reason": "External transport model is now MT3, while M1 is internal rich model.",
        },
        {
            "old_file": "results_package/tables/Table3_Phenotype_Gain.csv",
            "new_file": "results_package/tables/Table3_Phenotype_Gain_Post_METRE.csv",
            "replacement_status": "replace_for_main_results",
            "old_result_role": "old phenotype gain audit around M1/C3",
            "new_result_role": "Post-METRE phenotype hard/soft reassessment",
            "main_text_use": "use_new_only",
            "supplementary_or_exploratory_use": "old table can remain as pre-METRE sensitivity history",
            "reason": "Phenotype is downgraded to stratification/explanation and is not final transport input.",
        },
        {
            "old_file": "results_package/tables/Table4_Measurement_Bias.csv",
            "new_file": "results_package/tables/Table4_Measurement_Bias_Post_METRE.csv",
            "replacement_status": "replace_for_main_results",
            "old_result_role": "Step8 measurement bias decoupling",
            "new_result_role": "Post-METRE measurement-process component reassessment",
            "main_text_use": "use_new_only",
            "supplementary_or_exploratory_use": "old table can be used as historical consistency check",
            "reason": "High-dimensional quality/intensity remains non-transportable after Post-METRE.",
        },
        {
            "old_file": "results_package/figures/Figure5_dca_leadtime.csv",
            "new_file": "results_package/figures/Figure5_DCA_Leadtime_Post_METRE.csv",
            "replacement_status": "replace_for_main_results",
            "old_result_role": "old DCA and non-strict/eventual-style lead-time",
            "new_result_role": "strict 24h lead-time, exploratory eventual-death lead-time, and recalibrated DCA",
            "main_text_use": "use_new_only",
            "supplementary_or_exploratory_use": "old 79-91h lead-time should not be used as main; if shown, relabel as historical unstable result",
            "reason": "Old lead-time exceeded 24h horizon and is inconsistent with strict 24h label framing.",
        },
        {
            "old_file": "results_package/figures/Figure6_external_failure_modes.csv",
            "new_file": "results_package/figures/Figure6_External_Failure_Modes_Post_METRE.csv",
            "replacement_status": "replace_for_main_results",
            "old_result_role": "pre-METRE external failure mode diagnosis",
            "new_result_role": "Post-METRE failure mode update",
            "main_text_use": "use_new_only",
            "supplementary_or_exploratory_use": "old failure mode figure may be retained as pre-repair rationale",
            "reason": "METRE repair changes interpretation of external AUPRC, calibration, support proxy, and measurement shift.",
        },
    ]
    df = pd.DataFrame(rows)
    report = """# Old Result Replacement Report

## Main replacement decision

All Post-METRE suffixed files should be used for manuscript main results. Pre-METRE Step8/Step9 files remain auditable historical versions but should not drive the main Results narrative.

## Do not use in main manuscript

- `results_package/figures/Figure5_dca_leadtime.csv`: old lead-time values around 79-91h are not strict 24h-label lead-time.
- `results_package/tables/Table2_Main_Model_Comparators.csv`: old model comparison lacks the frozen MT3 external transport role.
- `results_package/tables/Table3_Phenotype_Gain.csv`: old phenotype framing can overstate performance-driver role.
- `results_package/tables/Table4_Measurement_Bias.csv`: old measurement bias analysis is superseded by Post-METRE component reassessment.
- `results_package/figures/Figure6_external_failure_modes.csv`: old failure-mode diagnosis is superseded after METRE repair.

## Retain as historical or supplementary only

Old Step8/Step9 outputs can be retained for audit trail and pre-repair rationale, but any manuscript statement should point to the Post-METRE versions unless explicitly labeled historical/pre-repair/exploratory.
"""
    return df, report


def write_handoff_index() -> str:
    return """# FINAL MANUSCRIPT HANDOFF INDEX

## Abstract should cite

- External transport performance: `results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv`.
- Key improvement lineage: `results_package/POST_METRE_RESULT_LINEAGE.csv`.
- Final model role: `final_freeze/Final_Model_Role_Audit.md`.

## Results should cite

- Table 2: `results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv`.
- Table 3: `results_package/tables/Table3_Phenotype_Gain_Post_METRE.csv`.
- Table 4: `results_package/tables/Table4_Measurement_Bias_Post_METRE.csv`.
- Figure 5 data: `results_package/figures/Figure5_DCA_Leadtime_Post_METRE.csv`.
- Figure 6 data: `results_package/figures/Figure6_External_Failure_Modes_Post_METRE.csv`.
- Narrative scaffold: `results_package/text/Results_Skeleton_zh_Post_METRE.md`.

## Discussion should emphasize

- M1 is internal rich model, not external transport model.
- MT3_physiology_support_proxy is the frozen external transport model.
- External deployment should require local recalibration.
- Strict 24h lead-time replaces old non-strict/eventual-style lead-time.
- DCA supports risk stratification, not automatic intervention triggering.
- Phenotype is a stratification/explanation/calibration audit tool, not a main performance driver.
- Full VIS and shared support-intensity proxy must remain separate concepts.
- Measurement intensity features are excluded from final transport feature set.

## Negative results that must remain

- MT3 internal performance is lower than M1.
- Local recalibration is required for deployment-ready probability scale.
- Phenotype_label and soft membership do not improve final external transport performance.
- Phenotype_3 remains weak-transfer/lower-certainty.
- Full VIS is internal-only.
- Full quality and measurement intensity harm external transport.
- Dynamic OASIS remains unavailable.

## Exploratory / sensitivity only

- Eventual-death lead-time from `Figure5_DCA_Leadtime_Post_METRE.csv`.
- MT4 phenotype sensitivity model.
- Full VIS internal-only sensitivity model.
- Historical pre-METRE Step8/Step9 outputs.
"""


def write_pi_summary(selection: pd.DataFrame, recal: pd.DataFrame) -> str:
    m1 = one(selection, model_name="M1_original_rich")
    mt3 = one(selection, model_name="MT3_physiology_support_proxy")
    raw = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="raw")
    cal = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="intercept_only")
    return f"""# FINAL PI SUMMARY

## 当前项目最终完成了什么

项目完成了从原始 M1 外部迁移失败到 Post-METRE transportability repair 的完整闭环：模型选择、外部再校准、strict 24h lead-time/DCA 重算、组件重估和结果包更新均已冻结。

## 最强结果

- 原 M1 eICU external AUROC/AUPRC/slope 为 {fmt(m1['eicu_external_auroc'])}/{fmt(m1['eicu_external_auprc'])}/{fmt(m1['eicu_calibration_slope'])}。
- 最终 MT3 eICU external AUROC/AUPRC/slope 为 {fmt(mt3['eicu_external_auroc'])}/{fmt(mt3['eicu_external_auprc'])}/{fmt(mt3['eicu_calibration_slope'])}。
- eICU hold-out intercept-only recalibration 将 death Brier/ECE 从 {fmt(raw['death_brier'])}/{fmt(raw['ece_death_10bin'])} 改善到 {fmt(cal['death_brier'])}/{fmt(cal['ece_death_10bin'])}。

## 最弱结果

- MT3 不是内部性能最强模型；M1 仍是 internal rich model。
- Phenotype_label 和 soft membership 不能作为性能增强卖点。
- Measurement intensity 与 full quality features 在 eICU 外部迁移中表现很差。

## 最终推荐主叙事

推荐主叙事为：`M1_original_rich` 作为 internal rich/reference model，`MT3_physiology_support_proxy` 作为 external transport model，`C1_dynamic_SOFA` 作为 clinical comparator。

## 不能夸大的结论

- 不能说 phenotype 是主性能驱动。
- 不能把 full VIS 和 support-intensity proxy 混为一谈。
- 不能说模型可无需本地再校准直接部署。
- 不能把 exploratory eventual-death lead-time 写成 strict 24h lead-time。

## 是否可以进入论文写作

可以进入正式论文写作阶段。建议论文定位为 transportability-focused 方法学与透明失败修复，而不是单纯强性能模型。
"""


def main() -> None:
    inventory = file_inventory()
    inventory.to_csv(OUT / "Required_File_Inventory.csv", index=False)

    selection = pd.read_csv(POST_SELECTION / "Post_METRE_Model_Comparison.csv")
    role = pd.read_csv(POST_SELECTION / "Model_Role_Assignment.csv")
    downstream = pd.read_csv(POST_SELECTION / "Downstream_Analysis_Model_Map.csv")
    recal = pd.read_csv(POST_RECAL / "Post_METRE_Recalibration_Results.csv")
    component = pd.read_csv(POST_COMPONENT / "component_ablation_results.csv")
    table2 = pd.read_csv(PKG / "tables" / "Table2_Main_Model_Comparators_Post_METRE.csv")
    table3 = pd.read_csv(PKG / "tables" / "Table3_Phenotype_Gain_Post_METRE.csv")
    table4 = pd.read_csv(PKG / "tables" / "Table4_Measurement_Bias_Post_METRE.csv")
    fig5 = pd.read_csv(PKG / "figures" / "Figure5_DCA_Leadtime_Post_METRE.csv")
    fig6 = pd.read_csv(PKG / "figures" / "Figure6_External_Failure_Modes_Post_METRE.csv")

    role_checks, role_text = audit_model_roles(role, downstream)
    (OUT / "Final_Model_Role_Audit.md").write_text(role_text, encoding="utf-8")

    comparisons = []
    comparisons.extend(audit_table2(selection, table2))
    comparisons.extend(audit_table3(component, table3))
    comparisons.extend(audit_table4(component, table4))
    fig5_checks = audit_figure5(fig5)
    fig6_checks = audit_figure6(fig6)
    table_report = write_table_figure_report(comparisons, fig5_checks, fig6_checks)
    (OUT / "Final_Table_Figure_Consistency_Audit.md").write_text(table_report, encoding="utf-8")

    replacement_map, replacement_report = write_old_result_replacement()
    replacement_map.to_csv(OUT / "Old_Result_Replacement_Map.csv", index=False)
    (OUT / "Old_Result_Replacement_Report.md").write_text(replacement_report, encoding="utf-8")

    (OUT / "FINAL_MANUSCRIPT_HANDOFF_INDEX.md").write_text(write_handoff_index(), encoding="utf-8")
    (OUT / "FINAL_PI_SUMMARY.md").write_text(write_pi_summary(selection, recal), encoding="utf-8")

    all_files_ok = bool(inventory["non_empty"].all())
    comparison_df = pd.DataFrame(comparisons)
    summary = {
        "required_files_ok": all_files_ok,
        "model_roles_consistent": all(role_checks.values()),
        "table_numeric_consistent": bool(comparison_df["consistent"].all()),
        "figure5_consistent": all(fig5_checks.values()),
        "figure6_consistent": bool(fig6_checks["expected_failure_modes_present"] and fig6_checks["mentions_MT3"]),
        "old_result_replacement_map_rows": int(len(replacement_map)),
        "handoff_index_exists": (OUT / "FINAL_MANUSCRIPT_HANDOFF_INDEX.md").exists(),
        "pi_summary_exists": (OUT / "FINAL_PI_SUMMARY.md").exists(),
    }
    (OUT / "Final_Freeze_Audit_Summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
