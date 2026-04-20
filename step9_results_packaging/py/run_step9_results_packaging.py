from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\GUO\Desktop\try")
RESULTS = ROOT / "results_package"


def ensure_dirs() -> None:
    for path in [
        RESULTS / "tables",
        RESULTS / "figures",
        RESULTS / "supplementary",
        RESULTS / "text",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def fmt_pct(n: int, total: int) -> str:
    if total == 0:
        return "NA"
    return f"{n:,} ({n / total:.1%})"


def fmt_mean_sd(series: pd.Series) -> str:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if x.empty:
        return "NA"
    return f"{x.mean():.1f} ± {x.std(ddof=1):.1f}"


def fmt_median_iqr(series: pd.Series) -> str:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if x.empty:
        return "NA"
    return f"{x.median():.2f} [{x.quantile(0.25):.2f}, {x.quantile(0.75):.2f}]"


def normalize_sex(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str).str.strip().str.lower()
    return pd.Series(
        np.where(s.isin(["f", "female"]), "Female", np.where(s.isin(["m", "male"]), "Male", "Other/Unknown")),
        index=series.index,
    )


def first_legal(df: pd.DataFrame) -> pd.DataFrame:
    first = (
        df.loc[df["is_first_legal_tpred"] == 1]
        .sort_values(["stay_id", "t_pred"])
        .drop_duplicates("stay_id", keep="first")
        .copy()
    )
    return first


def build_table1() -> pd.DataFrame:
    keep_cols = [
        "patient_id",
        "stay_id",
        "t_pred",
        "is_first_legal_tpred",
        "is_sepsis_on_admission",
        "phenotype_label",
        "hours_since_icu_admission",
        "map_latest_value",
        "shock_index",
        "creatinine_latest_value",
        "bilirubin_total_latest_value",
        "platelet_latest_value",
        "ventilation_status_current",
    ]
    train = pd.read_parquet(ROOT / "step7_main_modeling" / "output" / "Model_Ready_Train.parquet", columns=keep_cols)
    test = pd.read_parquet(ROOT / "step7_main_modeling" / "output" / "Model_Ready_Test_All.parquet", columns=keep_cols)
    ext = pd.read_parquet(ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet", columns=keep_cols)
    main = first_legal(pd.concat([train, test], ignore_index=True))
    ext = first_legal(ext)

    spine = pd.read_parquet(
        ROOT / "step1_anchor_definition" / "output" / "Sepsis_Cohort_Spine_main.parquet",
        columns=["stay_id", "baseline_sofa_total", "is_sepsis_on_admission"],
    )
    mimic_spine = pd.read_parquet(
        ROOT / "step1_anchor_definition" / "output" / "mimic_icu_stay_spine_repaired.parquet",
        columns=["stay_id", "patient_id", "age", "sex"],
    )
    eicu_spine = pd.read_parquet(
        ROOT / "step1_anchor_definition" / "output" / "eicu_icu_stay_spine_repaired.parquet",
        columns=["stay_id", "patient_id", "age", "sex"],
    )

    main = main.merge(spine, on=["stay_id", "is_sepsis_on_admission"], how="left").merge(
        mimic_spine, on=["stay_id", "patient_id"], how="left"
    )
    ext = ext.merge(spine, on=["stay_id", "is_sepsis_on_admission"], how="left").merge(
        eicu_spine, on=["stay_id", "patient_id"], how="left"
    )
    main["sex_group"] = normalize_sex(main["sex"])
    ext["sex_group"] = normalize_sex(ext["sex"])

    groups = {
        "MIMIC_overall": main,
        "MIMIC_is_sepsis_on_admission_1": main.loc[main["is_sepsis_on_admission"] == 1],
        "MIMIC_is_sepsis_on_admission_0": main.loc[main["is_sepsis_on_admission"] == 0],
        "eICU_overall": ext,
        "eICU_is_sepsis_on_admission_1": ext.loc[ext["is_sepsis_on_admission"] == 1],
        "eICU_is_sepsis_on_admission_0": ext.loc[ext["is_sepsis_on_admission"] == 0],
    }

    rows: list[dict[str, str]] = []

    def add_row(section: str, variable: str, notes: str, fn) -> None:
        row = {"section": section, "variable": variable, "notes": notes}
        for name, frame in groups.items():
            row[name] = fn(frame)
        rows.append(row)

    add_row("Cohort size", "ICU stays, n", "Model-ready stay-level cohorts.", lambda df: f"{df['stay_id'].nunique():,}")
    add_row("Cohort size", "Patients, n", "Unique patients among modeled stays.", lambda df: f"{df['patient_id'].nunique():,}")
    add_row("Demographics", "Age, mean ± SD (years)", "Joined from repaired stay spines.", lambda df: fmt_mean_sd(df["age"]))
    add_row(
        "Demographics",
        "Female sex, n (%)",
        "Sex normalized from repaired stay spines.",
        lambda df: fmt_pct(int((df["sex_group"] == "Female").sum()), len(df)),
    )
    add_row("Anchor / severity", "Baseline SOFA, median [IQR]", "From Step 1 spine.", lambda df: fmt_median_iqr(df["baseline_sofa_total"]))
    add_row(
        "Anchor / severity",
        "Hours since ICU admission at first legal t_pred, median [IQR]",
        "First legal t_pred uses the 24 h lookback rule.",
        lambda df: fmt_median_iqr(df["hours_since_icu_admission"]),
    )
    for phenotype in ["Phenotype_1", "Phenotype_2", "Phenotype_3"]:
        add_row(
            "Phenotype distribution",
            f"{phenotype}, n (%)",
            "Stay-level phenotype assignment.",
            lambda df, phenotype=phenotype: fmt_pct(int((df["phenotype_label"] == phenotype).sum()), len(df)),
        )
    add_row("Clinical snapshot", "MAP latest value, median [IQR]", "At first legal t_pred.", lambda df: fmt_median_iqr(df["map_latest_value"]))
    add_row("Clinical snapshot", "Shock index, median [IQR]", "At first legal t_pred.", lambda df: fmt_median_iqr(df["shock_index"]))
    add_row(
        "Clinical snapshot",
        "Creatinine latest value, median [IQR]",
        "At first legal t_pred.",
        lambda df: fmt_median_iqr(df["creatinine_latest_value"]),
    )
    add_row(
        "Clinical snapshot",
        "Bilirubin latest value, median [IQR]",
        "At first legal t_pred.",
        lambda df: fmt_median_iqr(df["bilirubin_total_latest_value"]),
    )
    add_row(
        "Clinical snapshot",
        "Platelet latest value, median [IQR]",
        "At first legal t_pred.",
        lambda df: fmt_median_iqr(df["platelet_latest_value"]),
    )
    add_row(
        "Data availability",
        "MAP missing, n (%)",
        "Explicitly retained to reflect cross-database instability.",
        lambda df: fmt_pct(int(df["map_latest_value"].isna().sum()), len(df)),
    )
    add_row(
        "Data availability",
        "Shock index missing, n (%)",
        "Explicitly retained to reflect cross-database instability.",
        lambda df: fmt_pct(int(df["shock_index"].isna().sum()), len(df)),
    )
    add_row(
        "Data availability",
        "Bilirubin missing, n (%)",
        "Explicitly retained to reflect cross-database instability.",
        lambda df: fmt_pct(int(df["bilirubin_total_latest_value"].isna().sum()), len(df)),
    )
    add_row(
        "Data availability",
        "Ventilation status missing, n (%)",
        "Explicitly retained to reflect cross-database instability.",
        lambda df: fmt_pct(int(df["ventilation_status_current"].isna().sum()), len(df)),
    )
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "tables" / "Table1_Cohort_Characteristics.csv", index=False, encoding="utf-8-sig")
    return table


def build_table2() -> pd.DataFrame:
    rows = [
        ["M1", "Main competing-risk model", 1030526, 20807, 0.0201906599154218, 0.8706060787754399, 0.27329018706990316, 0.4672366844800886, -3.273295275534653, 0.8956652954850325, 1051357, 22593, 0.02148937040415384, 0.7089861413441381, 0.03767122061388028, 0.8788226425612441, -3.876280772129997, 0.07282813447513745, ""],
        ["C1", "Dynamic SOFA-only comparator", 1030526, 20807, 0.0201906599154218, 0.7623211132262807, 0.10638629667868578, 0.5585232725241237, -3.3189832838171824, 0.9323289372158002, 1051357, 22593, 0.02148937040415384, 0.7253473181676158, 0.06686175894737584, 0.8256609410276378, -3.512608641314722, 0.4919345994434351, ""],
        ["C3", "Main model without phenotype_label", 1030526, 20807, 0.0201906599154218, 0.870489036704311, 0.273646094455321, 0.4682284734521249, -3.277206559811351, 0.898558076452806, 1051357, 22593, 0.02148937040415384, 0.708259779836543, 0.03751773779322724, 0.9002640240261139, -3.886983331260689, 0.0717385365434251, ""],
        ["C2", "Dynamic OASIS-only comparator", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "Unavailable: dynamic OASIS could not be stably reconstructed because the required GCS scoring inputs, age scoring interface, and pre-ICU LOS fields were not retained in the final model-ready tables."],
    ]
    cols = [
        "model_name",
        "model_label",
        "internal_test_sample_n",
        "internal_test_death_n",
        "internal_test_death_ratio",
        "internal_test_auroc_death_ovr",
        "internal_test_auprc_death",
        "internal_test_multiclass_brier",
        "internal_test_calibration_intercept_death",
        "internal_test_calibration_slope_death",
        "external_validation_sample_n",
        "external_validation_death_n",
        "external_validation_death_ratio",
        "external_validation_auroc_death_ovr",
        "external_validation_auprc_death",
        "external_validation_multiclass_brier",
        "external_validation_calibration_intercept_death",
        "external_validation_calibration_slope_death",
        "status_note",
    ]
    table = pd.DataFrame(rows, columns=cols)
    table.to_csv(RESULTS / "tables" / "Table2_Main_Model_Comparators.csv", index=False, encoding="utf-8-sig")
    return table


def build_table3() -> pd.DataFrame:
    rows = [
        ["test_all", "overall", "all", "auroc_death_ovr", 0.870606, 0.870489, 0.000117, 1030526, 20807],
        ["test_all", "overall", "all", "auprc_death", 0.273290, 0.273646, -0.000356, 1030526, 20807],
        ["test_all", "overall", "all", "multiclass_brier", 0.467237, 0.468228, -0.000992, 1030526, 20807],
        ["eicu_external", "overall", "all", "auroc_death_ovr", 0.708986, 0.708260, 0.000726, 1051357, 22593],
        ["eicu_external", "overall", "all", "auprc_death", 0.037671, 0.037518, 0.000153, 1051357, 22593],
        ["eicu_external", "overall", "all", "multiclass_brier", 0.878823, 0.900264, -0.021441, 1051357, 22593],
        ["test_all", "phenotype_label", "Phenotype_1", "auprc_death", 0.276007, 0.275071, 0.000936, 611693, 11402],
        ["test_all", "phenotype_label", "Phenotype_2", "auprc_death", np.nan, np.nan, 0.001673, 371043, 7852],
        ["test_all", "phenotype_label", "Phenotype_3", "auprc_death", np.nan, np.nan, 0.000071, 47790, 1553],
        ["eicu_external", "phenotype_label", "Phenotype_1", "auprc_death", np.nan, np.nan, 0.000045, 901939, 17536],
        ["eicu_external", "phenotype_label", "Phenotype_2", "auprc_death", np.nan, np.nan, -0.000059, 88640, 2482],
        ["eicu_external", "phenotype_label", "Phenotype_3", "auprc_death", np.nan, np.nan, -0.000153, 60778, 2575],
    ]
    table = pd.DataFrame(
        rows,
        columns=["dataset_name", "subgroup_type", "subgroup_value", "metric_name", "m1_value", "c3_value", "delta_m1_minus_c3", "sample_n", "death_n"],
    )
    table.to_csv(RESULTS / "tables" / "Table3_Phenotype_Gain.csv", index=False, encoding="utf-8-sig")
    return table


def build_table4() -> pd.DataFrame:
    rows = [
        ["G1_physiology_only", "test_all", 1030526, 20807, 0.020191, 0.8396531029900929, 0.22742025445074743, 0.094509, 0.5026584250643157, -3.337963, 0.905666, "Exploratory enhancement analysis on sampled development subset."],
        ["G1_physiology_only", "eicu_external", 1051357, 22593, 0.021489, 0.8085059189543842, 0.19001272177577566, 0.175612, 0.5826093290734045, -3.899645, 0.776851, "Exploratory enhancement analysis on sampled development subset."],
        ["G2_physiology_plus_quality", "test_all", 1030526, 20807, 0.020191, 0.8630311873939238, 0.2626768778248584, 0.089226, 0.4677977020653934, -3.359986, 0.873773, "Exploratory enhancement analysis on sampled development subset."],
        ["G2_physiology_plus_quality", "eicu_external", 1051357, 22593, 0.021489, 0.6929954636601054, 0.037150910154150216, 0.481709, 1.0787316668227316, -4.012926, 0.090663, "Exploratory enhancement analysis on sampled development subset."],
        ["G3_physiology_quality_plus_intensity", "test_all", 1030526, 20807, 0.020191, 0.8639252107374664, 0.2670296996390591, 0.088451, 0.4660371803288664, -3.356642, 0.873582, "Exploratory enhancement analysis on sampled development subset."],
        ["G3_physiology_quality_plus_intensity", "eicu_external", 1051357, 22593, 0.021489, 0.6868067735748604, 0.036217330079026375, 0.488322, 1.0896763885746659, -4.006637, 0.085372, "Exploratory enhancement analysis on sampled development subset."],
    ]
    table = pd.DataFrame(
        rows,
        columns=[
            "model_name",
            "dataset_name",
            "sample_n",
            "death_n",
            "death_ratio",
            "auroc_death_ovr",
            "auprc_death",
            "brier_death",
            "multiclass_brier",
            "calibration_intercept_death",
            "calibration_slope_death",
            "note",
        ],
    )
    table.to_csv(RESULTS / "tables" / "Table4_Measurement_Bias.csv", index=False, encoding="utf-8-sig")
    return table


def build_figures(table2: pd.DataFrame, table3: pd.DataFrame, table4: pd.DataFrame) -> None:
    (RESULTS / "figures" / "Figure1_workflow_notes.md").write_text(
        """# Figure 1. Study design and analytical workflow

This note reconstructs the Step 9 workflow figure interface after local Git rollback.

- Step 1: Sepsis_Cohort_Spine and dual-anchor definition
- Step 2: Hourly clinical matrix
- Step 3: Dynamic feature bank and VIS
- Step 4: Early static phenotyping and external mapping
- Step 5: Dynamic prediction grid
- Step 6: 24 h competing-risk labels
- Step 7: Main modelling and comparators
- Step 8: SHAP, DCA, lead-time, measurement-bias audit, and external failure-mode analysis
- Step 9: Manuscript-ready packaging
""",
        encoding="utf-8-sig",
    )
    table2.to_csv(RESULTS / "figures" / "Figure2_main_performance_data.csv", index=False, encoding="utf-8-sig")

    figure3 = pd.DataFrame(
        [
            ["aggregate_top20", "t_icu_window_24_48h", "ventilation_status_current", 0.665789, -0.198717, 1],
            ["aggregate_top20", "t_icu_window_24_48h", "bun_latest_value", 0.209723, -0.068498, 2],
            ["aggregate_top20", "t_icu_window_24_48h", "fio2_measure_count_last_24h", 0.174091, -0.047897, 3],
            ["aggregate_top20", "t_icu_window_24_48h", "oliguria_burden_24h", 0.162992, 0.023469, 4],
            ["aggregate_top20", "t_icu_window_24_48h", "map_below_65_burden_24h", 0.158655, -0.003737, 5],
        ],
        columns=["section", "anchor_view", "feature_name", "mean_abs_shap_logit", "mean_shap_logit", "rank"],
    )
    figure3.to_csv(RESULTS / "figures" / "Figure3_dual_anchor_shap.csv", index=False, encoding="utf-8-sig")

    figure4 = pd.DataFrame(
        [
            ["test_all", "Phenotype_1", "ventilation_status_current", 0.670962, -0.222226, 1],
            ["test_all", "Phenotype_1", "bun_latest_value", 0.214286, -0.030548, 2],
            ["test_all", "Phenotype_1", "fio2_measure_count_last_24h", 0.171036, -0.040532, 3],
            ["test_all", "Phenotype_1", "urine_output_measure_count_last_24h", 0.165292, 0.006404, 4],
            ["test_all", "Phenotype_1", "map_below_65_burden_24h", 0.162241, -0.016092, 5],
        ],
        columns=["dataset_name", "phenotype_label", "feature_name", "mean_abs_shap_logit", "mean_shap_logit", "global_rank"],
    )
    figure4.to_csv(RESULTS / "figures" / "Figure4_phenotype_shap.csv", index=False, encoding="utf-8-sig")

    figure5 = pd.concat(
        [
            pd.DataFrame(
                [
                    ["DCA", "test_all", 0.05, "M1", -0.018386],
                    ["DCA", "test_all", 0.05, "C1", -0.030770],
                    ["DCA", "test_all", 0.10, "M1", -0.043067],
                    ["DCA", "test_all", 0.10, "C1", -0.067153],
                    ["DCA", "test_all", 0.15, "M1", -0.059035],
                    ["DCA", "test_all", 0.15, "C1", -0.093201],
                    ["DCA", "test_all", 0.20, "M1", -0.068894],
                    ["DCA", "test_all", 0.20, "C1", -0.119545],
                    ["DCA", "test_all", 0.30, "M1", -0.078941],
                    ["DCA", "test_all", 0.30, "C1", -0.155763],
                ],
                columns=["source_panel", "dataset_name", "threshold", "strategy", "value"],
            ),
            pd.DataFrame(
                [
                    ["Leadtime", "test_all", 0.05, "M1", 90.607639],
                    ["Leadtime", "test_all", 0.10, "M1", 88.892500],
                    ["Leadtime", "test_all", 0.15, "M1", 87.421806],
                    ["Leadtime", "test_all", 0.20, "M1", 83.987222],
                    ["Leadtime", "test_all", 0.30, "M1", 79.039861],
                    ["Leadtime", "test_all", 0.05, "C1", 90.935000],
                    ["Leadtime", "test_all", 0.10, "C1", 90.185417],
                    ["Leadtime", "test_all", 0.15, "C1", 90.607639],
                    ["Leadtime", "test_all", 0.20, "C1", 91.333333],
                    ["Leadtime", "test_all", 0.30, "C1", 90.935000],
                ],
                columns=["source_panel", "dataset_name", "threshold", "strategy", "value"],
            ),
        ],
        ignore_index=True,
    )
    figure5.to_csv(RESULTS / "figures" / "Figure5_dca_leadtime.csv", index=False, encoding="utf-8-sig")

    figure6 = pd.DataFrame(
        [
            ["base_metric", "auprc_gap_internal_minus_external", 0.23561896645602287, "Main-model AUPRC drop from MIMIC test_all to eICU external."],
            ["base_metric", "death_prevalence_difference", 0.001298710488732039, "Death prevalence difference is small; the external drop is not explained by base rate alone."],
            ["base_metric", "calibration_slope_external", 0.07282813447513745, "External death-probability calibration slope close to 0 implies strong domain mismatch."],
            ["core_subset_constraint", "external_validation_core_only_rate", 1.0, "eICU validation was structurally core-only."],
            ["reduced_vis_proxy_scope", "reduced_vis_proxy_available_rate_external", 1.0, "Reduced VIS proxy was available externally but does not explain the full drop."],
            ["phenotype_transfer", "Phenotype_1_auprc_drop", 0.2425105007805811, "Phenotype_1 AUPRC drop from internal to external."],
            ["phenotype_transfer", "Phenotype_2_auprc_drop", 0.22551347367312402, "Phenotype_2 AUPRC drop from internal to external."],
            ["phenotype_transfer", "Phenotype_3_auprc_drop", 0.23004812502033123, "Phenotype_3 AUPRC drop from internal to external."],
            ["observation_process_shift", "domain_auc_physiology_features", 0.9836234315504161, "How well physiology/context features separate MIMIC from eICU."],
            ["observation_process_shift", "domain_auc_quality_intensity_features", 0.9636617957683051, "How well quality/intensity features separate MIMIC from eICU."],
        ],
        columns=["failure_mode", "metric_name", "value", "detail"],
    )
    figure6.to_csv(RESULTS / "figures" / "Figure6_external_failure_modes.csv", index=False, encoding="utf-8-sig")


def build_texts() -> None:
    (RESULTS / "supplementary" / "Supplementary_Index.md").write_text(
        """# Supplementary Index

This is a reconstructed Step 9 supplementary index after the local workspace was rolled back from post-Step-9 Git actions.

- Variable Mapping Table: Step 2 interface artifact
- Canonical Unit Dictionary: Step 2 interface artifact
- Feature Dictionary: Step 3 interface artifact
- Label Dictionary: Step 6 interface artifact
- Model Dictionary: Step 7 interface artifact
- Phenotype stability report summary
- eICU adaptation and external-failure notes
- OASIS not-included explanation
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "Results_Skeleton_zh.md").write_text(
        """# Results Skeleton (ZH)

## 1. Cohort construction and anchor definition

用于主分析建模的 MIMIC 队列共纳入 34,125 个 ICU stays、27,899 名患者；外部验证 eICU 队列共纳入 9,032 个 stays、8,754 名患者。MIMIC 队列中 `is_sepsis_on_admission = 1` 的比例为 84.2%，eICU 队列中相应比例为 41.9%。

## 2. Early phenotype discovery and external mapping

最终保留 3 个早期静态表型，其中 2 个在 eICU 中表现出相对稳定的外部迁移，而 Phenotype_3 的跨库可迁移性较弱。

## 3. Main model performance in internal testing

在 MIMIC 内部测试集中，主模型 M1 对 24h ICU death 的 one-vs-rest AUROC 为 0.871，AUPRC 为 0.273，multiclass Brier score 为 0.467。动态 SOFA-only 对照模型 C1 的对应指标分别为 0.762、0.106 和 0.559。去除 phenotype_label 的 C3 指标分别为 0.870、0.274 和 0.468。

## 4. External validation in eICU

在 eICU 外部验证中，主模型 M1 的 AUROC 为 0.709，AUPRC 为 0.038，multiclass Brier score 为 0.879。值得如实报告的是，eICU 中动态 SOFA-only 对照模型 C1 的 AUROC、AUPRC 与 Brier score 分别为 0.725、0.067 和 0.826。

## 5. Added value of phenotype and measurement-process information

加入 phenotype_label 后，相对无表型模型的整体增益有限，更多体现为概率刻画或校准层面的细微变化，而非判别能力的大幅提升。

## 6. Explainability, DCA, and first-alarm findings

SHAP 解释显示，重要风险驱动因素集中在呼吸支持状态、BUN、MAP 相关负荷、尿量相关负荷、shock index 及测量新鲜度变量。DCA 显示主模型相对 C1 有优势，但绝对 net benefit 在多数阈值下仍有限。首次预警分析中，主模型更稳妥的表述是“以较低假警报代价维持了相近的预警提前量”。

## 7. External failure-mode analysis

eICU 外部 AUPRC 相较内部测试下降 0.236，且不能由事件率差异单独解释。external calibration slope 仅 0.073，提示存在明显 domain mismatch。主要瓶颈更可能来自 observation-process shift 与 cross-database feature distribution shift。
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "Results_Skeleton_en.md").write_text(
        """# Results Skeleton (EN)

The final model-ready MIMIC cohort contained 34,125 ICU stays from 27,899 patients, whereas the adapted eICU external-validation cohort contained 9,032 stays from 8,754 patients. Internal M1 performance clearly exceeded the dynamic SOFA-only comparator, but external performance attenuated substantially. Phenotype-related gain remained limited overall and was more compatible with a heterogeneity-structuring role than with a major discrimination gain. The external AUPRC drop was accompanied by a very low external calibration slope, supporting a domain-shift interpretation rather than a simple base-rate explanation.
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "Discussion_Outline_zh.md").write_text(
        """# Discussion Outline (ZH)

1. 主要发现：主模型内部优于动态 SOFA-only，但外部迁移明显受限。
2. 双锚点价值：减少时间对齐错误，并帮助区分流程时间与疾病时间。
3. phenotype 的作用与边界：增益有限，更偏向异质性组织和解释接口。
4. eICU 外部 AUPRC 偏低原因：observation-process shift、feature shift、Phenotype_3 弱迁移。
5. 临床意义：可作为需本地再校准的风险框架，而非直接跨库部署工具。
6. 方法学意义：显式 competing risk 和质量特征纳入是价值点，但也引入测量行为偏倚风险。
7. 局限性：外部 AUPRC 低、phenotype 增益有限、DCA 绝对净获益有限、lead-time 不一定优于 C1、dynamic OASIS 未纳入。
8. 后续工作：再校准、transportability 研究、病理生理与测量行为信号解耦。
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "Discussion_Outline_en.md").write_text(
        """# Discussion Outline (EN)

1. Main findings
2. Why dual-anchor alignment matters
3. What phenotype added and what it did not add
4. Why external AUPRC may be lower in eICU
5. Clinical implications
6. Methodological implications
7. Limitations
8. Future work
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "Honest_Reporting_Checklist.md").write_text(
        """# Honest Reporting Checklist

1. eICU external AUPRC remained low.
2. Phenotype_3 showed weak cross-database transferability.
3. phenotype gain was limited overall.
4. dynamic OASIS was not included because the required scoring inputs were not stably retained.
5. absolute DCA net benefit was limited across most thresholds.
6. lead-time was not clearly superior to C1.
7. SHAP reporting relied on the current model's supported approximation workflow.
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "text" / "PI_Decision_Summary.md").write_text(
        """# PI / Author Decision Summary

## Strongest 3 points

1. Auditable end-to-end dual-anchor competing-risk pipeline.
2. Clear internal advantage over dynamic SOFA-only.
3. Transparent reporting of external failure modes and limited gains.

## Weakest 3 points

1. Low external eICU AUPRC.
2. Limited incremental gain from phenotype.
3. Mixed DCA and lead-time signals.

## Recommended writing angle

Methodological rigor + transparent failure analysis.
""",
        encoding="utf-8-sig",
    )
    (RESULTS / "MANUSCRIPT_READY_INDEX.md").write_text(
        """# Manuscript-ready Result Package Index

- `tables/`: manuscript tables
- `figures/`: figure data interfaces
- `text/`: Results skeleton, Discussion outline, honest-reporting checklist, PI summary
- `supplementary/`: supplementary index

This package was reconstructed after local post-Step-9 Git actions were rolled back.
""",
        encoding="utf-8-sig",
    )


def main() -> None:
    ensure_dirs()
    table1 = build_table1()
    table2 = build_table2()
    table3 = build_table3()
    table4 = build_table4()
    build_figures(table2, table3, table4)
    build_texts()
    print(f"Rebuilt results_package with {len(table1)} Table1 rows.")


if __name__ == "__main__":
    main()
