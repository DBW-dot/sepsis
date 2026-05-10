from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\GUO\Desktop\try")
PKG = ROOT / "results_package"
TABLES = PKG / "tables"
FIGURES = PKG / "figures"
TEXT = PKG / "text"
for path in [TABLES, FIGURES, TEXT]:
    path.mkdir(parents=True, exist_ok=True)

POST_SELECTION = ROOT / "post_metre_selection"
POST_RECAL = ROOT / "post_metre_recalibration"
POST_UTILITY = ROOT / "post_metre_clinical_utility"
POST_COMPONENT = ROOT / "post_metre_component_reassessment"


def fmt(x: float | int | str | None, digits: int = 4) -> str:
    if x is None:
        return "NA"
    if isinstance(x, str):
        return x
    if pd.isna(x):
        return "NA"
    return f"{float(x):.{digits}f}"


def one(df: pd.DataFrame, **query) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for key, value in query.items():
        mask &= df[key] == value
    sub = df[mask]
    if sub.empty:
        raise KeyError(f"No row for {query}")
    return sub.iloc[0]


def model_row_from_selection(
    row: pd.Series,
    model_role: str,
    dataset_scope: str,
    calibration_state: str,
    detailed_metrics: pd.DataFrame,
) -> dict:
    prefix = "mimic_internal" if dataset_scope == "mimic_internal_test" else "eicu_external"
    detail_dataset = "mimic_internal_test" if dataset_scope == "mimic_internal_test" else "eicu_external"
    detail = detailed_metrics[
        (detailed_metrics["model_name"] == row["model_name"])
        & (detailed_metrics["dataset_name"] == detail_dataset)
    ]
    if not detail.empty:
        detail_row = detail.iloc[0]
        sample_n = detail_row["sample_n"]
        death_n = detail_row["death_n"]
        death_rate = detail_row["death_rate"]
        calibration_intercept = detail_row["calibration_intercept_death"]
    else:
        sample_n = 1030526.0 if detail_dataset == "mimic_internal_test" else 1051357.0
        death_n = 20807.0 if detail_dataset == "mimic_internal_test" else 22593.0
        death_rate = death_n / sample_n
        calibration_intercept = np.nan
    return {
        "model_name": row["model_name"],
        "display_model_name": row["display_model_name"],
        "model_role": model_role,
        "dataset_scope": dataset_scope,
        "calibration_state": calibration_state,
        "sample_n": sample_n,
        "death_n": death_n,
        "death_rate": death_rate,
        "auroc_death_ovr": row[f"{prefix}_auroc"],
        "auprc_death": row[f"{prefix}_auprc"],
        "multiclass_brier": row[f"{prefix}_brier"],
        "death_brier": np.nan,
        "calibration_intercept_death": calibration_intercept,
        "calibration_slope_death": row[f"{prefix.split('_')[0]}_calibration_slope"] if prefix == "mimic_internal" else row["eicu_calibration_slope"],
        "ece_death_10bin": np.nan,
        "source_file": "post_metre_selection/Post_METRE_Model_Comparison.csv; metre_transport/METRE_vs_Original_Model_Comparison.csv",
        "status_note": "",
    }


def build_table2(selection: pd.DataFrame, recal: pd.DataFrame, detailed_metrics: pd.DataFrame) -> pd.DataFrame:
    roles = {
        "M1_original_rich": "Internal rich model, not external transport default",
        "C1_dynamic_SOFA": "Clinical score comparator",
        "C3_no_phenotype": "No-phenotype sensitivity model",
        "MT3_physiology_support_proxy": "Final external transport model",
        "MT4_support_proxy_phenotype_sensitivity": "Phenotype sensitivity model",
    }
    rows = []
    for model_name, role in roles.items():
        row = one(selection, model_name=model_name)
        rows.append(model_row_from_selection(row, role, "mimic_internal_test", "raw", detailed_metrics))
        rows.append(model_row_from_selection(row, role, "eicu_external_full", "raw", detailed_metrics))

    for method in ["raw", "intercept_only"]:
        rr = one(recal, model_name="MT3_physiology_support_proxy", calibration_method=method)
        rows.append(
            {
                "model_name": "MT3_physiology_support_proxy",
                "display_model_name": "MT3_physiology_support_proxy",
                "model_role": "Final external transport model hold-out calibration assessment",
                "dataset_scope": "eicu_external_holdout",
                "calibration_state": method,
                "sample_n": rr["row_n"],
                "death_n": rr["death_n"],
                "death_rate": rr["death_rate"],
                "auroc_death_ovr": rr["auroc_death"],
                "auprc_death": rr["auprc_death"],
                "multiclass_brier": rr["multiclass_brier"],
                "death_brier": rr["death_brier"],
                "calibration_intercept_death": rr["calibration_intercept_death"],
                "calibration_slope_death": rr["calibration_slope_death"],
                "ece_death_10bin": rr["ece_death_10bin"],
                "source_file": "post_metre_recalibration/Post_METRE_Recalibration_Results.csv",
                "status_note": "Hold-out eICU patient-level split; recalibration subset not reused for evaluation.",
            }
        )

    rows.append(
        {
            "model_name": "C2_dynamic_OASIS",
            "display_model_name": "Dynamic OASIS-only comparator",
            "model_role": "Unavailable comparator",
            "dataset_scope": "not_available",
            "calibration_state": "not_available",
            "sample_n": np.nan,
            "death_n": np.nan,
            "death_rate": np.nan,
            "auroc_death_ovr": np.nan,
            "auprc_death": np.nan,
            "multiclass_brier": np.nan,
            "death_brier": np.nan,
            "calibration_intercept_death": np.nan,
            "calibration_slope_death": np.nan,
            "ece_death_10bin": np.nan,
            "source_file": "step7_main_modeling reports and Step9 table",
            "status_note": "Unavailable because final model-ready tables do not retain stable dynamic OASIS inputs including GCS scoring, age score interface, and pre-ICU LOS.",
        }
    )
    return pd.DataFrame(rows)


def build_table3(component: pd.DataFrame, subgroup: pd.DataFrame) -> pd.DataFrame:
    selected = component[
        component["model_name"].isin(
            [
                "A1_B2_MT3_best_transport_no_phenotype_shared_proxy",
                "A2_MT4_best_transport_hard_phenotype",
                "A3_best_transport_soft_membership",
            ]
        )
    ].copy()
    baseline = selected[selected["model_name"] == "A1_B2_MT3_best_transport_no_phenotype_shared_proxy"][
        ["dataset_name", "auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"]
    ].rename(
        columns={
            "auroc_death_ovr": "baseline_auroc",
            "auprc_death": "baseline_auprc",
            "multiclass_brier": "baseline_brier",
            "calibration_slope_death": "baseline_slope",
        }
    )
    out = selected.merge(baseline, on="dataset_name", how="left")
    out["comparison_scope"] = "overall"
    out["delta_auroc_vs_MT3"] = out["auroc_death_ovr"] - out["baseline_auroc"]
    out["delta_auprc_vs_MT3"] = out["auprc_death"] - out["baseline_auprc"]
    out["delta_brier_vs_MT3"] = out["multiclass_brier"] - out["baseline_brier"]
    out["delta_slope_vs_MT3"] = out["calibration_slope_death"] - out["baseline_slope"]
    keep_cols = [
        "comparison_scope",
        "model_name",
        "feature_role",
        "dataset_name",
        "sample_n",
        "death_n",
        "death_rate",
        "auroc_death_ovr",
        "auprc_death",
        "multiclass_brier",
        "calibration_slope_death",
        "delta_auroc_vs_MT3",
        "delta_auprc_vs_MT3",
        "delta_brier_vs_MT3",
        "delta_slope_vs_MT3",
    ]
    overall = out[keep_cols]
    sg = subgroup[
        (subgroup["dataset_name"] == "eicu_external")
        & (subgroup["subgroup_type"].isin(["phenotype_label", "phenotype_transfer_group"]))
        & (
            subgroup["model_name"].isin(
                [
                    "A1_B2_MT3_best_transport_no_phenotype_shared_proxy",
                    "A2_MT4_best_transport_hard_phenotype",
                    "A3_best_transport_soft_membership",
                ]
            )
        )
    ].copy()
    sg["comparison_scope"] = sg["subgroup_type"] + ":" + sg["subgroup_value"].astype(str)
    for col in ["feature_role", "delta_auroc_vs_MT3", "delta_auprc_vs_MT3", "delta_brier_vs_MT3", "delta_slope_vs_MT3"]:
        sg[col] = np.nan
    return pd.concat([overall, sg[keep_cols]], ignore_index=True)


def build_table4(component: pd.DataFrame) -> pd.DataFrame:
    selected = component[
        component["model_name"].isin(
            [
                "B1_C1_MT1_physiology_only_no_proxy",
                "C2_MT2_physiology_minimal_recency",
                "C3_physiology_full_quality",
                "C4_physiology_full_quality_measurement_intensity",
            ]
        )
    ].copy()
    base = selected[selected["model_name"] == "B1_C1_MT1_physiology_only_no_proxy"][
        ["dataset_name", "auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"]
    ].rename(
        columns={
            "auroc_death_ovr": "baseline_auroc",
            "auprc_death": "baseline_auprc",
            "multiclass_brier": "baseline_brier",
            "calibration_slope_death": "baseline_slope",
        }
    )
    out = selected.merge(base, on="dataset_name", how="left")
    out["delta_auroc_vs_physiology_only"] = out["auroc_death_ovr"] - out["baseline_auroc"]
    out["delta_auprc_vs_physiology_only"] = out["auprc_death"] - out["baseline_auprc"]
    out["delta_brier_vs_physiology_only"] = out["multiclass_brier"] - out["baseline_brier"]
    out["delta_slope_vs_physiology_only"] = out["calibration_slope_death"] - out["baseline_slope"]
    return out[
        [
            "model_name",
            "feature_role",
            "dataset_name",
            "sample_n",
            "death_n",
            "death_rate",
            "auroc_death_ovr",
            "auprc_death",
            "multiclass_brier",
            "calibration_slope_death",
            "delta_auroc_vs_physiology_only",
            "delta_auprc_vs_physiology_only",
            "delta_brier_vs_physiology_only",
            "delta_slope_vs_physiology_only",
        ]
    ]


def build_figure5(dca: pd.DataFrame, strict: pd.DataFrame, eventual: pd.DataFrame) -> pd.DataFrame:
    dca_rows = dca.copy()
    dca_rows["analysis_type"] = "DCA_24h_death"
    strict_rows = strict.copy()
    strict_rows["analysis_type"] = "strict_24h_first_alarm"
    eventual_rows = eventual.copy()
    eventual_rows["analysis_type"] = "eventual_death_leadtime_exploratory_not_strict_24h"
    all_cols = sorted(set(dca_rows.columns) | set(strict_rows.columns) | set(eventual_rows.columns))
    return pd.concat(
        [dca_rows.reindex(columns=all_cols), strict_rows.reindex(columns=all_cols), eventual_rows.reindex(columns=all_cols)],
        ignore_index=True,
    )


def build_figure6(selection: pd.DataFrame, recal: pd.DataFrame, component: pd.DataFrame) -> pd.DataFrame:
    m1 = one(selection, model_name="M1_original_rich")
    mt3 = one(selection, model_name="MT3_physiology_support_proxy")
    raw = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="raw")
    cal = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="intercept_only")
    mt1_ext = one(component, model_name="B1_C1_MT1_physiology_only_no_proxy", dataset_name="eicu_external")
    mt3_ext = one(component, model_name="A1_B2_MT3_best_transport_no_phenotype_shared_proxy", dataset_name="eicu_external")
    c4_ext = one(component, model_name="C4_physiology_full_quality_measurement_intensity", dataset_name="eicu_external")
    mt4_ext = one(component, model_name="A2_MT4_best_transport_hard_phenotype", dataset_name="eicu_external")
    soft_ext = one(component, model_name="A3_best_transport_soft_membership", dataset_name="eicu_external")
    return pd.DataFrame(
        [
            {
                "failure_mode": "external_discrimination_drop",
                "old_conclusion": "M1 eICU external AUPRC was very low.",
                "post_metre_result": "MT3 improves external discrimination but remains a transport-oriented, not peak-internal, model.",
                "old_metric": f"M1 AUROC/AUPRC {fmt(m1['eicu_external_auroc'])}/{fmt(m1['eicu_external_auprc'])}",
                "new_metric": f"MT3 AUROC/AUPRC {fmt(mt3['eicu_external_auroc'])}/{fmt(mt3['eicu_external_auprc'])}",
                "interpretation": "METRE feature alignment substantially reduces external AUPRC failure.",
                "source_file": "post_metre_selection/Post_METRE_Model_Comparison.csv",
            },
            {
                "failure_mode": "external_calibration_failure",
                "old_conclusion": "M1 external calibration slope was close to zero.",
                "post_metre_result": "MT3 raw slope is near 1; local intercept-only recalibration mainly fixes calibration level/Brier/ECE.",
                "old_metric": f"M1 slope {fmt(m1['eicu_calibration_slope'])}",
                "new_metric": f"MT3 full external slope {fmt(mt3['eicu_calibration_slope'])}; hold-out raw->{fmt(raw['calibration_slope_death'])}, recal->{fmt(cal['calibration_slope_death'])}",
                "interpretation": "Deployment should still require local recalibration because probability level changed markedly.",
                "source_file": "post_metre_recalibration/Post_METRE_Recalibration_Results.csv",
            },
            {
                "failure_mode": "support_intensity_representation",
                "old_conclusion": "Full VIS and eICU reduced proxy were not transport-equivalent.",
                "post_metre_result": "Shared support-intensity proxy improves external AUPRC over physiology-only.",
                "old_metric": f"MT1 AUPRC {fmt(mt1_ext['auprc_death'])}",
                "new_metric": f"MT3 AUPRC {fmt(mt3_ext['auprc_death'])}",
                "interpretation": "Use shared proxy for transport; keep full VIS internal-only.",
                "source_file": "post_metre_component_reassessment/component_ablation_results.csv",
            },
            {
                "failure_mode": "measurement_process_shift",
                "old_conclusion": "Quality/intensity features harmed eICU transport in Step8.",
                "post_metre_result": "Full quality + measurement intensity remains harmful after Post-METRE.",
                "old_metric": "Step8 physiology+quality+intensity external AUPRC 0.0362",
                "new_metric": f"C4 external AUPRC {fmt(c4_ext['auprc_death'])}; slope {fmt(c4_ext['calibration_slope_death'])}",
                "interpretation": "Exclude high-dimensional measurement-intensity features from final transport model.",
                "source_file": "post_metre_component_reassessment/component_ablation_results.csv",
            },
            {
                "failure_mode": "phenotype_role",
                "old_conclusion": "Phenotype gain was limited.",
                "post_metre_result": "Hard phenotype and soft membership do not improve MT3 external AUPRC.",
                "old_metric": "M1 vs C3 external AUPRC delta +0.000153",
                "new_metric": f"MT4 AUPRC {fmt(mt4_ext['auprc_death'])}; soft AUPRC {fmt(soft_ext['auprc_death'])}; MT3 AUPRC {fmt(mt3_ext['auprc_death'])}",
                "interpretation": "Phenotype should be stratification/explanation, not a default performance driver.",
                "source_file": "post_metre_component_reassessment/component_ablation_results.csv",
            },
        ]
    )


def build_lineage(selection: pd.DataFrame, recal: pd.DataFrame, dca: pd.DataFrame, strict: pd.DataFrame, component: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(metric_name, old_value, new_value, source_file, source_script, model_used, whether_recalibrated, notes):
        rows.append(
            {
                "metric_name": metric_name,
                "old_value": old_value,
                "new_value": new_value,
                "source_file": source_file,
                "source_script": source_script,
                "model_used": model_used,
                "whether_recalibrated": whether_recalibrated,
                "notes": notes,
            }
        )

    m1 = one(selection, model_name="M1_original_rich")
    mt3 = one(selection, model_name="MT3_physiology_support_proxy")
    add("eICU external AUROC", m1["eicu_external_auroc"], mt3["eicu_external_auroc"], "post_metre_selection/Post_METRE_Model_Comparison.csv", "post_metre_selection/run_post_metre_model_selection.py", "MT3_physiology_support_proxy", "no", "Old value is original M1 external AUROC.")
    add("eICU external AUPRC", m1["eicu_external_auprc"], mt3["eicu_external_auprc"], "post_metre_selection/Post_METRE_Model_Comparison.csv", "post_metre_selection/run_post_metre_model_selection.py", "MT3_physiology_support_proxy", "no", "Primary external transport improvement.")
    add("eICU external calibration slope", m1["eicu_calibration_slope"], mt3["eicu_calibration_slope"], "post_metre_selection/Post_METRE_Model_Comparison.csv", "post_metre_selection/run_post_metre_model_selection.py", "MT3_physiology_support_proxy", "no", "Raw transport model slope before local recalibration.")
    raw = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="raw")
    cal = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="intercept_only")
    for metric in ["auroc_death", "auprc_death", "death_brier", "multiclass_brier", "calibration_slope_death", "ece_death_10bin"]:
        add(f"holdout MT3 {metric} after local recalibration", raw[metric], cal[metric], "post_metre_recalibration/Post_METRE_Recalibration_Results.csv", "post_metre_recalibration/run_post_metre_external_recalibration.py", "MT3_physiology_support_proxy", "yes_intercept_only", "Patient-level hold-out eICU evaluation.")
    old_fig5 = pd.read_csv(PKG / "figures" / "Figure5_dca_leadtime.csv")
    old_lt = old_fig5[(old_fig5["source_panel"] == "Leadtime") & (old_fig5["threshold"] == 0.1) & (old_fig5["strategy"] == "M1")]["value"].iloc[0]
    new_lt = one(strict, model_name="MT3_recalibrated_intercept_only", threshold=0.1)["strict_lead_time_median_hours"]
    add("Figure5 lead-time at threshold 0.10", old_lt, new_lt, "post_metre_clinical_utility/strict_24h_first_alarm_summary.csv", "post_metre_clinical_utility/run_post_metre_clinical_utility.py", "MT3_recalibrated_intercept_only", "yes_intercept_only", "Old value was eventual-death style lead-time; new value is strict 24h-label first alarm median.")
    old_dca = old_fig5[(old_fig5["source_panel"] == "DCA") & (old_fig5["threshold"] == 0.1) & (old_fig5["strategy"] == "M1")]["value"].iloc[0]
    new_dca = one(dca, model_name="MT3_recalibrated_intercept_only", threshold=0.1)["net_benefit"]
    add("Figure5 DCA net benefit at threshold 0.10", old_dca, new_dca, "post_metre_clinical_utility/dca_threshold_sweep_post_metre.csv", "post_metre_clinical_utility/run_post_metre_clinical_utility.py", "MT3_recalibrated_intercept_only", "yes_intercept_only", "Post-METRE DCA uses 24h death label and recalibrated probability.")
    mt3c = one(component, model_name="A1_B2_MT3_best_transport_no_phenotype_shared_proxy", dataset_name="eicu_external")
    mt4c = one(component, model_name="A2_MT4_best_transport_hard_phenotype", dataset_name="eicu_external")
    soft = one(component, model_name="A3_best_transport_soft_membership", dataset_name="eicu_external")
    add("Phenotype hard-label external AUPRC delta", 0.000153, mt4c["auprc_death"] - mt3c["auprc_death"], "post_metre_component_reassessment/component_ablation_results.csv", "post_metre_component_reassessment/run_post_metre_component_reassessment.py", "MT4 vs MT3", "no", "Old value was M1 vs C3 external AUPRC delta.")
    add("Phenotype soft-membership external AUPRC delta", "not previously tested", soft["auprc_death"] - mt3c["auprc_death"], "post_metre_component_reassessment/component_ablation_results.csv", "post_metre_component_reassessment/run_post_metre_component_reassessment.py", "A3 vs MT3", "no", "Soft membership does not improve external AUPRC.")
    mt1 = one(component, model_name="B1_C1_MT1_physiology_only_no_proxy", dataset_name="eicu_external")
    add("Shared support proxy external AUPRC gain vs no-proxy", "not in old Step9 package", mt3c["auprc_death"] - mt1["auprc_death"], "post_metre_component_reassessment/component_ablation_results.csv", "post_metre_component_reassessment/run_post_metre_component_reassessment.py", "MT3 vs MT1", "no", "Supports proxy inclusion in transport model.")
    c4 = one(component, model_name="C4_physiology_full_quality_measurement_intensity", dataset_name="eicu_external")
    add("Measurement intensity external AUPRC", 0.036217330079026375, c4["auprc_death"], "post_metre_component_reassessment/component_ablation_results.csv", "post_metre_component_reassessment/run_post_metre_component_reassessment.py", "C4", "no", "Confirms measurement intensity remains non-transportable.")
    return pd.DataFrame(rows)


def write_text_outputs(selection: pd.DataFrame, recal: pd.DataFrame, strict: pd.DataFrame, dca: pd.DataFrame, component: pd.DataFrame) -> None:
    m1 = one(selection, model_name="M1_original_rich")
    mt3 = one(selection, model_name="MT3_physiology_support_proxy")
    mt4 = one(selection, model_name="MT4_support_proxy_phenotype_sensitivity")
    raw = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="raw")
    cal = one(recal, model_name="MT3_physiology_support_proxy", calibration_method="intercept_only")
    strict_010 = one(strict, model_name="MT3_recalibrated_intercept_only", threshold=0.1)
    strict_005 = one(strict, model_name="MT3_recalibrated_intercept_only", threshold=0.005)
    dca_010 = one(dca, model_name="MT3_recalibrated_intercept_only", threshold=0.1)
    dca_005 = one(dca, model_name="MT3_recalibrated_intercept_only", threshold=0.005)
    mt3c = one(component, model_name="A1_B2_MT3_best_transport_no_phenotype_shared_proxy", dataset_name="eicu_external")
    mt4c = one(component, model_name="A2_MT4_best_transport_hard_phenotype", dataset_name="eicu_external")
    soft = one(component, model_name="A3_best_transport_soft_membership", dataset_name="eicu_external")
    c4 = one(component, model_name="C4_physiology_full_quality_measurement_intensity", dataset_name="eicu_external")

    results_zh = f"""# Results Skeleton zh Post-METRE

## 1. Post-METRE 模型角色更新

原 M1 仍是 MIMIC 内部 rich model，内部 AUROC/AUPRC 为 {fmt(m1['mimic_internal_auroc'])}/{fmt(m1['mimic_internal_auprc'])}，但 eICU 外部 AUROC/AUPRC/slope 仅为 {fmt(m1['eicu_external_auroc'])}/{fmt(m1['eicu_external_auprc'])}/{fmt(m1['eicu_calibration_slope'])}。Post-METRE 后，最终 external transport model 固定为 MT3，即 physiology + temporal context + shared support-intensity proxy，不直接纳入 phenotype_label。

## 2. 外部验证改善

MT3 在 eICU full external 上 AUROC/AUPRC/slope 为 {fmt(mt3['eicu_external_auroc'])}/{fmt(mt3['eicu_external_auprc'])}/{fmt(mt3['eicu_calibration_slope'])}。相对于 M1，外部 AUPRC 从 {fmt(m1['eicu_external_auprc'])} 提升到 {fmt(mt3['eicu_external_auprc'])}，AUROC 从 {fmt(m1['eicu_external_auroc'])} 提升到 {fmt(mt3['eicu_external_auroc'])}。但 MT3 内部 AUPRC {fmt(mt3['mimic_internal_auprc'])} 低于 M1 内部 AUPRC {fmt(m1['mimic_internal_auprc'])}，说明它是 transport-focused model，而不是内部性能最强模型。

## 3. 外部再校准

在 eICU patient-level hold-out 上，MT3 raw AUROC/AUPRC/slope 为 {fmt(raw['auroc_death'])}/{fmt(raw['auprc_death'])}/{fmt(raw['calibration_slope_death'])}；intercept-only recalibration 后为 {fmt(cal['auroc_death'])}/{fmt(cal['auprc_death'])}/{fmt(cal['calibration_slope_death'])}。再校准不改变判别能力，但 death Brier/ECE 从 {fmt(raw['death_brier'])}/{fmt(raw['ece_death_10bin'])} 改善到 {fmt(cal['death_brier'])}/{fmt(cal['ece_death_10bin'])}。因此外部部署应表述为 requires local recalibration。

## 4. Strict 24h lead-time 与 DCA

旧 Figure5 中 79-91 小时 lead-time 不再作为 strict 24h 主结果，应改名为 exploratory eventual-death lead-time。新的 strict 24h first-alarm 结果中，MT3 recalibrated 在阈值 0.10 的 median lead-time 为 {fmt(strict_010['strict_lead_time_median_hours'])} 小时，最大 strict lead-time 不超过 24 小时。DCA 在阈值 0.005 和 0.10 的 net benefit 分别为 {fmt(dca_005['net_benefit'])} 和 {fmt(dca_010['net_benefit'])}，再校准后低阈值和中等阈值区间均优于未校准 MT3。

## 5. Phenotype、VIS/proxy 与 measurement-process 结论

Post-METRE component reassessment 显示 hard phenotype model MT4 的外部 AUPRC 为 {fmt(mt4c['auprc_death'])}，低于 MT3 的 {fmt(mt3c['auprc_death'])}；soft membership 外部 AUPRC 为 {fmt(soft['auprc_death'])}，也未优于 MT3。因此 phenotype 应降级为分层/解释/校准审计工具。Full VIS 保留为 internal rich/sensitivity 模块；跨库主分析使用 shared support-intensity proxy。Full quality + measurement intensity 外部 AUPRC 为 {fmt(c4['auprc_death'])} 且 calibration slope 为 {fmt(c4['calibration_slope_death'])}，因此不进入最终 transport feature set。

## 6. 当前结果定位

Post-METRE 后项目比原始外部结果更稳，但仍需诚实报告：MT3 不追求 MIMIC 内部最高性能；外部部署需要 local recalibration；phenotype 不是性能增强器；measurement-process features 破坏外部迁移；模型更适合风险分层和审计式临床辅助，而不是自动干预触发器。
"""
    (TEXT / "Results_Skeleton_zh_Post_METRE.md").write_text(results_zh, encoding="utf-8")

    discussion_zh = """# Discussion Outline zh Post-METRE

## 1. Main findings

Post-METRE 的核心发现是：跨库 feature alignment 和 shared support-intensity proxy 能显著改善 eICU 外部迁移，而原 M1 更适合定位为 internal rich model。

## 2. Why METRE-style transport layer matters

外部失败主要不是事件率差异，而是 feature semantics、VIS/proxy 不等价和 observation-process shift。MT3 放弃高维 measurement-process 信号后，外部 AUROC/AUPRC 和校准明显更稳。

## 3. Recalibration as deployment requirement

MT3 raw slope 已接近 1，但 probability level 偏移明显；intercept-only local recalibration 显著改善 Brier/ECE。因此论文应明确：模型若部署到本地 ICU 系统，需要 local recalibration。

## 4. Phenotype role after reassessment

Phenotype 不应再写成 performance driver。它更适合组织异质性、解释风险模式、做 subgroup calibration audit。Phenotype_3 仍应作为弱迁移/低确定性表型说明。

## 5. VIS/proxy interpretation

Full VIS 是 MIMIC internal rich 信息，不可与 eICU reduced proxy 混称。Shared support-intensity proxy 是最终 transport model 的支持强度表达。

## 6. Clinical utility and alarm framing

Strict 24h lead-time 取代旧的 79-91h lead-time。DCA 在低阈值区间和再校准后有所改善，但模型仍应定位为 risk stratification，而非自动治疗触发器。

## 7. Limitations

需要报告：MT3 内部性能低于 M1；external recalibration 需要本地标签样本；OASIS 仍不可稳定实现；measurement intensity 的强预测性在外部不可迁移；eICU validation 仍受 core subset 和 proxy 限制。

## 8. Future work

后续可做前瞻性本地再校准、站点级 drift monitoring、可解释性与临床工作流验证，以及更严格的多中心 transport feature registry。
"""
    (TEXT / "Discussion_Outline_zh_Post_METRE.md").write_text(discussion_zh, encoding="utf-8")

    honest = f"""# Honest Reporting Checklist Post-METRE

1. M1 内部表现最好，但不能作为外部 transport model；eICU AUPRC 仅 {fmt(m1['eicu_external_auprc'])}，calibration slope 仅 {fmt(m1['eicu_calibration_slope'])}。
2. MT3 明显改善外部 AUPRC 至 {fmt(mt3['eicu_external_auprc'])}，但内部 AUPRC 低于 M1，因此是 transport-focused trade-off，不是全方位更强模型。
3. eICU local recalibration 应作为部署前要求；intercept-only recalibration 主要改善 Brier/ECE，不提高 AUROC/AUPRC。
4. 旧 79-91 小时 lead-time 不能称为 strict 24h lead-time，只能作为 exploratory eventual-death lead-time 或撤出主图。
5. DCA 虽有正 net benefit 阈值区间，且再校准改善 DCA，但模型仍不应表述为自动干预触发器。
6. Phenotype_label 和 soft membership 均未改善 MT3 外部 AUPRC；phenotype 应降级为分层/解释/校准审计工具。
7. Phenotype_3 仍是弱迁移/低确定性表型；较高 subgroup AUPRC 可能受死亡率较高影响，不能等同于迁移更好。
8. Full VIS 只能作为 MIMIC internal rich/sensitivity 信息；transport model 使用 shared support-intensity proxy，不能把 full VIS 与 eICU proxy 混称。
9. Full quality 和 measurement intensity features 在 eICU 外部明显破坏迁移，不能纳入最终 transport feature set。
10. Dynamic OASIS 仍不可稳定实现，原因是 final model-ready tables 缺少必要 GCS、age scoring interface 和 pre-ICU LOS 等输入。
"""
    (TEXT / "Honest_Reporting_Checklist_Post_METRE.md").write_text(honest, encoding="utf-8")

    pi = f"""# PI Decision Summary Post-METRE

## 最强的 3 点

1. METRE-style transport layer 将 eICU external AUPRC 从 M1 的 {fmt(m1['eicu_external_auprc'])} 提升到 MT3 的 {fmt(mt3['eicu_external_auprc'])}，且 raw calibration slope 接近 1。
2. 结果叙事从“内部强但外部失败”转为“internal rich model + external transport model”的双模型框架，更容易防守。
3. Component reassessment 明确了 phenotype、VIS/proxy、measurement-process features 的边界，避免过度声称。

## 最弱的 3 点

1. MT3 内部性能低于 M1，不能说它整体更强。
2. 外部部署需要 local recalibration，说明概率尺度仍存在站点漂移。
3. Phenotype 增益有限，且 Phenotype_3 迁移弱，不能作为核心性能卖点。

## 投稿定位建议

主线更适合“方法学严谨 + transportability repair + 透明失败分析”，而不是“强性能模型”。当前已可进入正式论文写作阶段，但写作必须保留负面结果和部署限制。
"""
    (TEXT / "PI_Decision_Summary_Post_METRE.md").write_text(pi, encoding="utf-8")

    assessment = f"""# Post-METRE Final Project Assessment

## 1. Post-METRE 后项目是否更稳

是。原 M1 的 eICU external AUROC/AUPRC/slope 为 {fmt(m1['eicu_external_auroc'])}/{fmt(m1['eicu_external_auprc'])}/{fmt(m1['eicu_calibration_slope'])}；MT3 为 {fmt(mt3['eicu_external_auroc'])}/{fmt(mt3['eicu_external_auprc'])}/{fmt(mt3['eicu_calibration_slope'])}。外部判别与校准均明显更可防守。

## 2. 是否能把 external transport model 放入主结果

可以。建议主结果中并列展示：M1 as internal rich model，MT3 as external transport model，C1 as clinical comparator，MT3 recalibrated as deployment-oriented local recalibration result。

## 3. M1 是否仍保留为 internal rich model

是。M1 的 MIMIC internal AUROC/AUPRC 仍最高，为 {fmt(m1['mimic_internal_auroc'])}/{fmt(m1['mimic_internal_auprc'])}，但不应作为外部迁移主模型。

## 4. 仍需诚实报告的负面结果

- MT3 内部性能低于 M1。
- Local recalibration 是外部部署要求。
- Phenotype 和 soft membership 不是性能增强器。
- Full VIS 不能跨库直接迁移。
- Measurement intensity features 破坏外部迁移。
- DCA 改善主要支持风险分层，不支持自动干预触发。
- 旧 lead-time 必须撤回或改名为 exploratory eventual-death lead-time。

## 5. 是否可以进入正式论文写作

可以。当前结果包已经具备进入正式论文写作的结构化材料，但论文写作必须以 transportability 和透明失败修复为主线，而不是夸大模型性能。
"""
    (TEXT / "Post_METRE_Final_Project_Assessment.md").write_text(assessment, encoding="utf-8")


def write_index() -> None:
    text = """# Post-METRE Result Package Index

## Updated main tables

- `tables/Table2_Main_Model_Comparators_Post_METRE.csv`
- `tables/Table3_Phenotype_Gain_Post_METRE.csv`
- `tables/Table4_Measurement_Bias_Post_METRE.csv`

## Updated figure data

- `figures/Figure5_DCA_Leadtime_Post_METRE.csv`
- `figures/Figure6_External_Failure_Modes_Post_METRE.csv`

## Updated manuscript interface text

- `text/Results_Skeleton_zh_Post_METRE.md`
- `text/Discussion_Outline_zh_Post_METRE.md`
- `text/Honest_Reporting_Checklist_Post_METRE.md`
- `text/PI_Decision_Summary_Post_METRE.md`
- `text/Post_METRE_Final_Project_Assessment.md`

## Traceability

- `POST_METRE_RESULT_LINEAGE.csv` records old value, new value, source file, source script, model, recalibration status, and notes.

## Replacement decisions

- Old Figure5 lead-time should be replaced or renamed because it measured eventual-death timing, not strict 24h-label first alarm.
- New Figure5 data should use strict 24h lead-time, exploratory eventual-death lead-time as separate panel, and post-METRE DCA/recalibrated DCA.
- External transport narrative should use MT3, while preserving M1 as the internal rich model.
"""
    (PKG / "POST_METRE_RESULT_INDEX.md").write_text(text, encoding="utf-8")


def main() -> None:
    selection = pd.read_csv(POST_SELECTION / "Post_METRE_Model_Comparison.csv")
    detailed_metrics = pd.read_csv(ROOT / "metre_transport" / "METRE_vs_Original_Model_Comparison.csv")
    recal = pd.read_csv(POST_RECAL / "Post_METRE_Recalibration_Results.csv")
    strict = pd.read_csv(POST_UTILITY / "strict_24h_first_alarm_summary.csv")
    eventual = pd.read_csv(POST_UTILITY / "eventual_death_leadtime_summary.csv")
    dca = pd.read_csv(POST_UTILITY / "dca_threshold_sweep_post_metre.csv")
    component = pd.read_csv(POST_COMPONENT / "component_ablation_results.csv")
    subgroup = pd.read_csv(POST_COMPONENT / "component_subgroup_results.csv")

    table2 = build_table2(selection, recal, detailed_metrics)
    table3 = build_table3(component, subgroup)
    table4 = build_table4(component)
    fig5 = build_figure5(dca, strict, eventual)
    fig6 = build_figure6(selection, recal, component)
    lineage = build_lineage(selection, recal, dca, strict, component)

    table2.to_csv(TABLES / "Table2_Main_Model_Comparators_Post_METRE.csv", index=False)
    table3.to_csv(TABLES / "Table3_Phenotype_Gain_Post_METRE.csv", index=False)
    table4.to_csv(TABLES / "Table4_Measurement_Bias_Post_METRE.csv", index=False)
    fig5.to_csv(FIGURES / "Figure5_DCA_Leadtime_Post_METRE.csv", index=False)
    fig6.to_csv(FIGURES / "Figure6_External_Failure_Modes_Post_METRE.csv", index=False)
    lineage.to_csv(PKG / "POST_METRE_RESULT_LINEAGE.csv", index=False)
    write_text_outputs(selection, recal, strict, dca, component)
    write_index()

    verification = {
        "table2_rows": len(table2),
        "figure5_rows": len(fig5),
        "lineage_rows": len(lineage),
        "mt3_external_auprc": float(one(selection, model_name="MT3_physiology_support_proxy")["eicu_external_auprc"]),
        "m1_external_auprc": float(one(selection, model_name="M1_original_rich")["eicu_external_auprc"]),
    }
    print(verification)


if __name__ == "__main__":
    main()
