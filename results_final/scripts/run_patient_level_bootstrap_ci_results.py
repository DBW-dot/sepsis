from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


REPO = Path(r"D:\try\github_chatgpt_share_repo")
ROOT = Path(r"D:\try")
OUT_TABLES = REPO / "results_final" / "tables"
OUT_TEXT = REPO / "results_final" / "text"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_TEXT.mkdir(parents=True, exist_ok=True)

BOOTSTRAP_MODULE_PATH = REPO / "manuscript_assets" / "audit" / "run_bootstrap_ci.py"
EXISTING_CI_PATH = REPO / "manuscript_assets" / "supplement" / "Supplementary_Table_S5_Bootstrap_CI_AllMetrics.csv"
N_RESAMPLES = 1000
SEED = 20260511


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("bootstrap_ci_core", BOOTSTRAP_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load bootstrap module from {BOOTSTRAP_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inspect_prediction_files() -> list[dict[str, Any]]:
    candidates = [
        ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet",
        ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet",
        ROOT / "step7_main_modeling" / "output" / "pred_C1_test_all.parquet",
        ROOT / "step7_main_modeling" / "output" / "pred_C1_eicu_external.parquet",
        ROOT / "step7_main_modeling" / "output" / "pred_C3_test_all.parquet",
        ROOT / "step7_main_modeling" / "output" / "pred_C3_eicu_external.parquet",
        ROOT / "post_metre_recalibration" / "pred_MT3_eicu_external.parquet",
        ROOT / "step7_main_modeling" / "output" / "Model_Ready_Test_All.parquet",
        ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet",
    ]
    rows: list[dict[str, Any]] = []
    for path in candidates:
        row: dict[str, Any] = {
            "file_path": str(path),
            "exists": path.exists(),
            "row_count": np.nan,
            "column_count": np.nan,
            "id_columns": "",
            "label_columns": "",
            "prediction_columns": "",
            "phenotype_column_present": False,
            "model_names": "",
            "notes": "",
        }
        if path.exists():
            df = pd.read_parquet(path)
            cols = list(df.columns)
            row["row_count"] = len(df)
            row["column_count"] = len(cols)
            row["id_columns"] = ",".join([c for c in ["patient_id", "subject_id", "uniquepid", "stay_id", "patientunitstayid"] if c in cols])
            row["label_columns"] = ",".join([c for c in ["event_type_24h", "true_event_type_24h", "event_indicator_death_24h"] if c in cols])
            row["prediction_columns"] = ",".join(
                [
                    c
                    for c in [
                        "predicted_prob_death_24h",
                        "prob_death_raw",
                        "predicted_prob_discharge_24h",
                        "prob_discharge_raw",
                        "predicted_prob_no_event_24h",
                        "prob_no_event_raw",
                    ]
                    if c in cols
                ]
            )
            row["phenotype_column_present"] = "phenotype_label" in cols
            if "model_name" in cols:
                row["model_names"] = ",".join(map(str, pd.Series(df["model_name"].dropna().unique()).head(10).tolist()))
            if "predicted_prob_death_24h" not in cols and "prob_death_raw" not in cols and "Model_Ready" not in path.name:
                row["notes"] = "missing_prediction_risk_column"
            elif "phenotype_label" not in cols:
                row["notes"] = "phenotype_label_missing"
            else:
                row["notes"] = "usable_for_bootstrap_or_frozen_inference"
        else:
            row["notes"] = "missing_prediction_file"
        rows.append(row)
    return rows


def ci_pair(ci: pd.DataFrame, model: str, dataset: str, scenario: str, metric: str) -> tuple[float, float]:
    row = ci[
        (ci["model_name"] == model)
        & (ci["dataset_name"] == dataset)
        & (ci["scenario"] == scenario)
        & (ci["metric_name"] == metric)
    ]
    if row.empty:
        return np.nan, np.nan
    return float(row["bootstrap_CI_lower"].iloc[0]), float(row["bootstrap_CI_upper"].iloc[0])


def make_main_results(ci: pd.DataFrame) -> pd.DataFrame:
    table2 = pd.read_csv(REPO / "manuscript_assets" / "tables" / "Table2_Main_Model_Performance.csv")
    rows: list[dict[str, Any]] = []
    for _, r in table2.iterrows():
        model = r["model_display_name"]
        row = {
            "model_name": model,
            "model_role": r["model_role"],
            "feature_count": r["feature_count"],
            "MIMIC_AUROC": r["MIMIC_AUROC"],
            "MIMIC_AUROC_95CI": fmt_ci(*ci_pair(ci, model, "mimic_internal", "primary_model", "AUROC")),
            "MIMIC_AUPRC": r["MIMIC_AUPRC"],
            "MIMIC_AUPRC_95CI": fmt_ci(*ci_pair(ci, model, "mimic_internal", "primary_model", "AUPRC")),
            "MIMIC_Brier": r["MIMIC_Brier"],
            "MIMIC_Brier_95CI": fmt_ci(*ci_pair(ci, model, "mimic_internal", "primary_model", "multiclass_Brier")),
            "eICU_AUROC": r["eICU_AUROC"],
            "eICU_AUROC_95CI": fmt_ci(*ci_pair(ci, model, "eicu_external", "primary_model", "AUROC")),
            "eICU_AUPRC": r["eICU_AUPRC"],
            "eICU_AUPRC_95CI": fmt_ci(*ci_pair(ci, model, "eicu_external", "primary_model", "AUPRC")),
            "eICU_calibration_slope": r["eICU_calibration_slope"],
            "eICU_calibration_slope_95CI": fmt_ci(
                *ci_pair(ci, model, "eicu_external", "primary_model", "calibration_slope")
            ),
            "ci_method": "patient-level cluster bootstrap; 1000 resamples; seed 20260511",
        }
        rows.append(row)
    return pd.DataFrame(rows)


def make_clinical_results(ci: pd.DataFrame) -> pd.DataFrame:
    table3 = pd.read_csv(REPO / "manuscript_assets" / "tables" / "Table3_Clinical_Implementation_TrueTraining.csv")
    rows: list[dict[str, Any]] = []
    for _, r in table3.iterrows():
        model = r["model_display_name"]
        rows.append(
            {
                "model_name": model,
                "feature_count": r["feature_count"],
                "training_status": r["training_status"],
                "eICU_AUROC": r["eICU_AUROC"],
                "eICU_AUROC_95CI": fmt_ci(*ci_pair(ci, model, "eicu_external", "primary_model", "AUROC")),
                "eICU_AUPRC": r["eICU_AUPRC"],
                "eICU_AUPRC_95CI": fmt_ci(*ci_pair(ci, model, "eicu_external", "primary_model", "AUPRC")),
                "eICU_calibration_slope": r["eICU_calibration_slope"],
                "eICU_calibration_slope_95CI": fmt_ci(
                    *ci_pair(ci, model, "eicu_external", "primary_model", "calibration_slope")
                ),
                "relative_AUPRC_drop_pct_vs_P15": r["relative_AUPRC_drop_pct_vs_P15"],
                "noninferiority_status": r["noninferiority_status"],
                "recommended_role": r["recommended_role"],
                "ci_method": "patient-level cluster bootstrap; 1000 resamples; seed 20260511",
            }
        )
    return pd.DataFrame(rows)


def fmt_ci(lower: float, upper: float) -> str:
    if not np.isfinite(lower) or not np.isfinite(upper):
        return "unavailable"
    return f"{lower:.4f}-{upper:.4f}"


def exact_metrics_from_predictions(core, df: pd.DataFrame) -> dict[str, float]:
    point = core.metric_point_estimates(df)
    return {
        "AUROC": point["AUROC"],
        "AUPRC": point["AUPRC"],
        "Brier": point["death_Brier"],
        "calibration_slope": point["calibration_slope"],
    }


def prediction_from_bundle(core, model_name: str, dataset_name: str, frame: pd.DataFrame, bundle: dict[str, Any]) -> pd.DataFrame:
    pred = core.prediction_df_from_bundle(model_name, dataset_name, frame, bundle)
    if "phenotype_label" in frame.columns:
        pred["phenotype_label"] = frame["phenotype_label"].values
    return pred


def build_prediction_sets(core) -> dict[tuple[str, str], pd.DataFrame]:
    bundles = {name: core.load_model(path) for name, path in core.FROZEN_MODEL_FILES.items()}
    frames = {
        "mimic_internal": core.add_support_proxy(pd.read_parquet(core.MODEL_READY["mimic_internal"])),
        "eicu_external": core.add_support_proxy(pd.read_parquet(core.MODEL_READY["eicu_external"])),
    }
    pred_sets: dict[tuple[str, str], pd.DataFrame] = {}
    for dataset, frame in frames.items():
        for model_name, bundle in bundles.items():
            pred_sets[(model_name, dataset)] = prediction_from_bundle(core, model_name, dataset, frame, bundle)
    existing = {
        ("M1_internal_rich_reference_model", "mimic_internal"): ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet",
        ("M1_internal_rich_reference_model", "eicu_external"): ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet",
        ("C1_dynamic_SOFA_clinical_comparator", "mimic_internal"): ROOT / "step7_main_modeling" / "output" / "pred_C1_test_all.parquet",
        ("C1_dynamic_SOFA_clinical_comparator", "eicu_external"): ROOT / "step7_main_modeling" / "output" / "pred_C1_eicu_external.parquet",
    }
    for key, path in existing.items():
        pred_sets[key] = core.load_prediction_file(key[0], key[1], path)
        raw = pd.read_parquet(path, columns=["phenotype_label"])
        pred_sets[key]["phenotype_label"] = raw["phenotype_label"].values
    return pred_sets


def phenotype_bootstrap(core, pred_sets: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (model_name, dataset_name), df in pred_sets.items():
        if "phenotype_label" not in df.columns:
            rows.append(
                {
                    "model_name": model_name,
                    "dataset_name": dataset_name,
                    "phenotype_label": "missing_prediction_file_or_missing_phenotype_label",
                    "status": "missing_prediction_file",
                }
            )
            continue
        for phenotype, part in df.groupby("phenotype_label", dropna=False):
            part = part.copy()
            if part["event_type_24h"].eq(core.DEATH_LABEL).sum() == 0:
                rows.append(
                    {
                        "model_name": model_name,
                        "dataset_name": dataset_name,
                        "phenotype_label": phenotype,
                        "status": "unavailable_single_class",
                        "row_n": len(part),
                        "death_row_n": int(part["event_type_24h"].eq(core.DEATH_LABEL).sum()),
                    }
                )
                continue
            result = core.bootstrap_ci(
                part,
                model_name=model_name,
                dataset_name=dataset_name,
                scenario=f"phenotype_{phenotype}",
                point_source="phenotype_stratified_existing_or_frozen_prediction",
            )
            exact = exact_metrics_from_predictions(core, part)
            metric_rows = pd.DataFrame(result.metric_rows)
            row = {
                "model_name": model_name,
                "dataset_name": dataset_name,
                "phenotype_label": phenotype,
                "status": "ok",
                "row_n": result.row_n,
                "cluster_n": result.cluster_n,
                "death_row_n": result.death_n,
                "cluster_id_used": result.cluster_id_used,
                "bootstrap_unit": result.cluster_level,
                "n_resamples_requested": N_RESAMPLES,
                "n_resamples_valid": result.n_resamples_valid,
                "n_resamples_skipped": result.n_resamples_skipped,
                "AUROC": exact["AUROC"],
                "AUROC_95CI": metric_ci(metric_rows, "AUROC"),
                "AUPRC": exact["AUPRC"],
                "AUPRC_95CI": metric_ci(metric_rows, "AUPRC"),
                "Brier": exact["Brier"],
                "Brier_95CI": metric_ci(metric_rows, "death_Brier"),
                "calibration_slope": exact["calibration_slope"],
                "calibration_slope_95CI": metric_ci(metric_rows, "calibration_slope"),
            }
            rows.append(row)
    return pd.DataFrame(rows)


def metric_ci(metric_rows: pd.DataFrame, metric_name: str) -> str:
    row = metric_rows[metric_rows["metric_name"] == metric_name]
    if row.empty:
        return "unavailable"
    return fmt_ci(float(row["bootstrap_CI_lower"].iloc[0]), float(row["bootstrap_CI_upper"].iloc[0]))


def validate_required_points(main_results: pd.DataFrame) -> list[str]:
    expected = {
        ("P15_clinically_parsimonious_transport_model", "eICU_AUROC"): 0.8103,
        ("P15_clinically_parsimonious_transport_model", "eICU_AUPRC"): 0.1892,
        ("P15_clinically_parsimonious_transport_model", "eICU_calibration_slope"): 1.0031,
        ("M1_internal_rich_reference_model", "eICU_AUROC"): 0.7090,
        ("M1_internal_rich_reference_model", "eICU_AUPRC"): 0.0377,
        ("M1_internal_rich_reference_model", "eICU_calibration_slope"): 0.0728,
        ("C1_dynamic_SOFA_clinical_comparator", "eICU_AUROC"): 0.7253,
        ("C1_dynamic_SOFA_clinical_comparator", "eICU_AUPRC"): 0.0669,
    }
    warnings: list[str] = []
    for (model, column), target in expected.items():
        row = main_results[main_results["model_name"] == model]
        if row.empty:
            warnings.append(f"missing_model_for_point_validation:{model}")
            continue
        value = float(row[column].iloc[0])
        if abs(value - target) > 5e-4:
            warnings.append(f"point_estimate_mismatch:{model}:{column}:observed={value}:expected={target}")
    return warnings


def exact_logistic_slope_ci_for_prediction_file(path: Path, phenotype_label: str | None = None) -> tuple[str, int, int]:
    columns = ["patient_id", "event_type_24h", "predicted_prob_death_24h", "phenotype_label"]
    df = pd.read_parquet(path, columns=columns)
    if phenotype_label is not None:
        df = df[df["phenotype_label"] == phenotype_label].copy()
    y = (df["event_type_24h"] == "ICU_DEATH").astype(int).to_numpy()
    prob = np.clip(df["predicted_prob_death_24h"].to_numpy(), 1e-6, 1 - 1e-6)
    x = np.log(prob / (1 - prob)).reshape(-1, 1)
    clusters = pd.factorize(df["patient_id"])[0]
    n_clusters = clusters.max() + 1
    rng = np.random.default_rng(SEED)
    slopes = []
    skipped = 0
    for _ in range(N_RESAMPLES):
        sampled = rng.integers(0, n_clusters, n_clusters)
        counts = np.bincount(sampled, minlength=n_clusters).astype(float)
        weights = counts[clusters]
        if np.dot(weights, y) == 0 or np.dot(weights, 1 - y) == 0:
            skipped += 1
            continue
        model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
        model.fit(x, y, sample_weight=weights)
        slopes.append(float(model.coef_[0][0]))
    lower, upper = np.percentile(np.asarray(slopes, dtype=float), [2.5, 97.5])
    return fmt_ci(float(lower), float(upper)), len(slopes), skipped


def correct_m1_external_calibration_slope_ci(main_results: pd.DataFrame, subgroup_results: pd.DataFrame) -> None:
    """Use exact logistic calibration bootstrap for M1 eICU low-slope case.

    The generic manuscript bootstrap table uses a computationally tractable
    quantile-bin approximation for calibration slope. That approximation is
    adequate for the calibrated transport models but unstable for the original
    M1 external model because its calibration slope is near zero. The point
    estimate in Table 2 was computed with exact logistic recalibration, so the
    M1 external slope CI is corrected here with the same exact method.
    """

    path = ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet"
    overall_ci, _, _ = exact_logistic_slope_ci_for_prediction_file(path)
    mask = main_results["model_name"].eq("M1_internal_rich_reference_model")
    main_results.loc[mask, "eICU_calibration_slope_95CI"] = overall_ci
    for phenotype in subgroup_results.loc[
        subgroup_results["model_name"].eq("M1_internal_rich_reference_model")
        & subgroup_results["dataset_name"].eq("eicu_external"),
        "phenotype_label",
    ].dropna().unique():
        ci, valid, skipped = exact_logistic_slope_ci_for_prediction_file(path, phenotype_label=str(phenotype))
        smask = (
            subgroup_results["model_name"].eq("M1_internal_rich_reference_model")
            & subgroup_results["dataset_name"].eq("eicu_external")
            & subgroup_results["phenotype_label"].eq(phenotype)
        )
        subgroup_results.loc[smask, "calibration_slope_95CI"] = ci
        subgroup_results.loc[smask, "n_resamples_valid"] = valid
        subgroup_results.loc[smask, "n_resamples_skipped"] = skipped


def write_summary(
    file_audit: list[dict[str, Any]],
    main_results: pd.DataFrame,
    clinical_results: pd.DataFrame,
    subgroup_results: pd.DataFrame,
    validation_warnings: list[str],
) -> None:
    p15 = main_results[main_results["model_name"] == "P15_clinically_parsimonious_transport_model"].iloc[0]
    m1 = main_results[main_results["model_name"] == "M1_internal_rich_reference_model"].iloc[0]
    c1 = main_results[main_results["model_name"] == "C1_dynamic_SOFA_clinical_comparator"].iloc[0]
    missing = [r for r in file_audit if not r["exists"] or "missing" in str(r["notes"])]
    text = f"""# Patient-level Bootstrap 95% CI Summary for Manuscript

## Scope

This analysis generates manuscript-facing 95% confidence intervals from existing prediction-level outputs and frozen model inference only. No model was retrained, no point estimate was changed, and eICU was not used for training or tuning.

## Bootstrap method

- Resampling unit: patient-level cluster when `patient_id` was available; otherwise stay-level cluster would be used.
- Row-level / patient-hour bootstrap was not used.
- Resamples requested: `{N_RESAMPLES}`.
- Random seed: `{SEED}`.
- All prediction rows belonging to a sampled patient/stay were included in each bootstrap replicate.
- Metrics: AUROC, AUPRC, death Brier score, and death-class calibration slope.
- CI: percentile 2.5% and 97.5%.

## Point-estimate validation

- P15 eICU AUROC/AUPRC/calibration slope: {p15['eICU_AUROC']:.4f}/{p15['eICU_AUPRC']:.4f}/{p15['eICU_calibration_slope']:.4f}.
- M1/70-feature reference eICU AUROC/AUPRC/calibration slope: {m1['eICU_AUROC']:.4f}/{m1['eICU_AUPRC']:.4f}/{m1['eICU_calibration_slope']:.4f}.
- Dynamic SOFA eICU AUROC/AUPRC: {c1['eICU_AUROC']:.4f}/{c1['eICU_AUPRC']:.4f}.
- Validation warnings: {validation_warnings if validation_warnings else 'none'}.

## Key P15 eICU CIs

- AUROC 95% CI: {p15['eICU_AUROC_95CI']}.
- AUPRC 95% CI: {p15['eICU_AUPRC_95CI']}.
- Calibration slope 95% CI: {p15['eICU_calibration_slope_95CI']}.

## Prediction-level file audit

"""
    for r in file_audit:
        text += (
            f"- `{r['file_path']}`: exists={r['exists']}, rows={r['row_count']}, "
            f"ids={r['id_columns']}, labels={r['label_columns']}, preds={r['prediction_columns']}, "
            f"phenotype_label={r['phenotype_column_present']}, notes={r['notes']}.\n"
        )
    text += "\n## Missing or limited prediction files\n\n"
    if missing:
        for r in missing:
            text += f"- `{r['file_path']}`: {r['notes']}.\n"
    else:
        text += "- No required M1/C1 prediction parquet was missing. P15/P12/P10 were generated by frozen-model inference from Model_Ready tables because standalone prediction parquet files were not present.\n"
    text += """

## Output files

- `results_final/tables/bootstrap_ci_main_results.csv`
- `results_final/tables/bootstrap_ci_subphenotype_results.csv`
- `results_final/tables/bootstrap_ci_clinical_implementation_models.csv`

## Guardrails

P15 remains the formal main model. P12/P10 remain clinical implementation and ultra-minimal sensitivity candidates. These CIs quantify uncertainty only; they do not alter frozen model roles or point estimates.
"""
    (OUT_TEXT / "bootstrap_ci_summary_for_manuscript.md").write_text(text, encoding="utf-8")


def main() -> None:
    core = load_bootstrap_module()
    file_audit = inspect_prediction_files()
    if not EXISTING_CI_PATH.exists():
        raise RuntimeError(f"Required existing bootstrap CI table missing: {EXISTING_CI_PATH}")
    ci = pd.read_csv(EXISTING_CI_PATH)

    main_results = make_main_results(ci)
    clinical_results = make_clinical_results(ci)

    pred_sets = build_prediction_sets(core)
    subgroup_results = phenotype_bootstrap(core, pred_sets)
    correct_m1_external_calibration_slope_ci(main_results, subgroup_results)

    validation_warnings = validate_required_points(main_results)

    main_results.to_csv(OUT_TABLES / "bootstrap_ci_main_results.csv", index=False, encoding="utf-8-sig")
    subgroup_results.to_csv(OUT_TABLES / "bootstrap_ci_subphenotype_results.csv", index=False, encoding="utf-8-sig")
    clinical_results.to_csv(
        OUT_TABLES / "bootstrap_ci_clinical_implementation_models.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(file_audit).to_csv(OUT_TABLES / "bootstrap_ci_prediction_file_audit.csv", index=False, encoding="utf-8-sig")
    write_summary(file_audit, main_results, clinical_results, subgroup_results, validation_warnings)

    print(
        json.dumps(
            {
                "main_results": str(OUT_TABLES / "bootstrap_ci_main_results.csv"),
                "subphenotype_results": str(OUT_TABLES / "bootstrap_ci_subphenotype_results.csv"),
                "clinical_results": str(OUT_TABLES / "bootstrap_ci_clinical_implementation_models.csv"),
                "summary": str(OUT_TEXT / "bootstrap_ci_summary_for_manuscript.md"),
                "validation_warnings": validation_warnings,
                "subphenotype_rows": int(len(subgroup_results)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
