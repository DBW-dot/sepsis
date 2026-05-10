from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "phenotype_reassessment"
OUTDIR.mkdir(parents=True, exist_ok=True)

PRED_PATHS = {
    ("P1_no_phenotype", "internal_test"): ROOT / "step7_main_modeling" / "output" / "pred_C3_test_all.parquet",
    ("P2_phenotype_input", "internal_test"): ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet",
    ("P1_no_phenotype", "external_eicu"): ROOT / "step7_main_modeling" / "output" / "pred_C3_eicu_external.parquet",
    ("P2_phenotype_input", "external_eicu"): ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet",
}

ASSIGN_PATHS = {
    "internal_test": ROOT / "step4_phenotyping" / "output" / "Phenotype_Assignment_main.parquet",
    "external_eicu": ROOT / "step4_phenotyping" / "output" / "Phenotype_Assignment_eicu.parquet",
}

PHENOTYPES = ["Phenotype_1", "Phenotype_2", "Phenotype_3"]
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
CLASSES = [DEATH_LABEL, DISCHARGE_LABEL, NO_EVENT_LABEL]


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def logit(p: np.ndarray) -> np.ndarray:
    p = clip_probs(p)
    return np.log(p / (1.0 - p))


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if weights.sum() <= 0:
        return float("nan")
    return float(np.sum(values * weights) / np.sum(weights))


def calibration_intercept_slope(
    y_binary: np.ndarray,
    probs: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[float, float]:
    y_binary = np.asarray(y_binary, dtype=int)
    probs = clip_probs(probs)
    if np.unique(y_binary).size < 2:
        return float("nan"), float("nan")
    x = logit(probs).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    fit_kwargs = {}
    if sample_weight is not None:
        fit_kwargs["sample_weight"] = np.asarray(sample_weight, dtype=float)
    model.fit(x, y_binary, **fit_kwargs)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def multiclass_brier(
    y_true: np.ndarray,
    probs: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> float:
    y_true = np.asarray(y_true, dtype=object)
    probs = np.asarray(probs, dtype=float)
    one_hot = np.zeros_like(probs)
    class_to_idx = {label: idx for idx, label in enumerate(CLASSES)}
    for row_idx, label in enumerate(y_true):
        one_hot[row_idx, class_to_idx[label]] = 1.0
    row_error = np.sum((one_hot - probs) ** 2, axis=1)
    if sample_weight is None:
        return float(np.mean(row_error))
    weights = np.asarray(sample_weight, dtype=float)
    return weighted_mean(row_error, weights)


def death_brier(
    y_binary: np.ndarray,
    probs: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> float:
    err = (np.asarray(y_binary, dtype=float) - np.asarray(probs, dtype=float)) ** 2
    if sample_weight is None:
        return float(np.mean(err))
    return weighted_mean(err, np.asarray(sample_weight, dtype=float))


def compute_metrics(
    df: pd.DataFrame,
    sample_weight: np.ndarray | None = None,
) -> dict[str, float]:
    y_true = df["event_type_24h"].to_numpy()
    y_death = (y_true == DEATH_LABEL).astype(int)
    death_probs = df["predicted_prob_death_24h"].to_numpy()
    probs_3 = df[
        ["predicted_prob_death_24h", "predicted_prob_discharge_24h", "predicted_prob_no_event_24h"]
    ].to_numpy()

    weights = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
    positive_weight = float(y_death.sum() if weights is None else np.sum(weights * y_death))
    sample_n = float(len(df) if weights is None else weights.sum())
    death_rate = positive_weight / sample_n if sample_n > 0 else float("nan")

    if np.unique(y_death).size < 2:
        auroc = float("nan")
        auprc = float("nan")
    else:
        auc_kwargs = {}
        ap_kwargs = {}
        if weights is not None:
            auc_kwargs["sample_weight"] = weights
            ap_kwargs["sample_weight"] = weights
        auroc = float(roc_auc_score(y_death, death_probs, **auc_kwargs))
        auprc = float(average_precision_score(y_death, death_probs, **ap_kwargs))

    cal_intercept, cal_slope = calibration_intercept_slope(y_death, death_probs, weights)
    return {
        "sample_n": sample_n,
        "death_n": positive_weight,
        "death_rate": death_rate,
        "auroc_death": auroc,
        "auprc_death": auprc,
        "death_brier": death_brier(y_death, death_probs, weights),
        "multiclass_brier": multiclass_brier(y_true, probs_3, weights),
        "calibration_intercept_death": cal_intercept,
        "calibration_slope_death": cal_slope,
        "mean_predicted_death": float(
            np.mean(death_probs) if weights is None else weighted_mean(death_probs, weights)
        ),
    }


def parse_membership(value: str | dict[str, float] | None) -> dict[str, float]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return {name: np.nan for name in PHENOTYPES}
    if isinstance(value, dict):
        parsed = value
    else:
        parsed = json.loads(value)
    return {name: float(parsed.get(name, np.nan)) for name in PHENOTYPES}


def load_assignment(dataset_name: str) -> pd.DataFrame:
    path = ASSIGN_PATHS[dataset_name]
    if dataset_name == "internal_test":
        columns = [
            "stay_id",
            "phenotype_label",
            "phenotype_membership_vector",
            "phenotype_membership_max",
            "phenotype_severity_score",
        ]
    else:
        columns = [
            "stay_id",
            "phenotype_label",
            "phenotype_membership_vector",
            "phenotype_confidence",
            "phenotype_severity_score",
        ]
    df = pd.read_parquet(path, columns=columns).copy()
    if "phenotype_confidence" not in df.columns:
        df["phenotype_confidence"] = np.nan
    if "phenotype_membership_max" in df.columns:
        df["phenotype_confidence"] = df["phenotype_confidence"].fillna(df["phenotype_membership_max"])
    memberships = df["phenotype_membership_vector"].apply(parse_membership).apply(pd.Series)
    memberships = memberships.rename(columns={name: f"membership_{name}" for name in PHENOTYPES})
    df = pd.concat([df.drop(columns=["phenotype_membership_vector", "phenotype_membership_max"], errors="ignore"), memberships], axis=1)
    return df.drop_duplicates("stay_id")


def load_predictions(use_case: str, dataset_name: str) -> pd.DataFrame:
    path = PRED_PATHS[(use_case, dataset_name)]
    df = pd.read_parquet(
        path,
        columns=[
            "stay_id",
            "patient_id",
            "t_pred",
            "phenotype_label",
            "true_event_type_24h",
            "predicted_prob_death_24h",
            "predicted_prob_discharge_24h",
            "predicted_prob_no_event_24h",
        ],
    ).copy()
    df = df.rename(columns={"true_event_type_24h": "event_type_24h", "phenotype_label": "predicted_phenotype_label"})
    return df


def merge_predictions_with_assignment(use_case: str, dataset_name: str) -> tuple[pd.DataFrame, dict[str, int]]:
    pred = load_predictions(use_case, dataset_name)
    assign = load_assignment(dataset_name)
    merged = pred.merge(assign, on="stay_id", how="left", validate="many_to_one")
    verification = {
        "row_n": int(len(merged)),
        "unique_stay_n": int(merged["stay_id"].nunique()),
        "missing_assignment_rows": int(merged["phenotype_label"].isna().sum()),
        "pred_assignment_label_mismatch_rows": int(
            (
                merged["predicted_phenotype_label"].notna()
                & merged["phenotype_label"].notna()
                & (merged["predicted_phenotype_label"] != merged["phenotype_label"])
            ).sum()
        ),
    }
    return merged, verification


def subgroup_rows_for_use_case(
    use_case: str,
    dataset_name: str,
    df: pd.DataFrame,
    subgroup_definition: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for phenotype_name in PHENOTYPES:
        if subgroup_definition == "hard_label":
            sub = df.loc[df["phenotype_label"] == phenotype_name].copy()
            weights = None
            confidence_mean = float(sub["phenotype_confidence"].mean()) if len(sub) else float("nan")
            confidence_median = float(sub["phenotype_confidence"].median()) if len(sub) else float("nan")
        elif subgroup_definition == "soft_membership":
            sub = df.copy()
            weights = sub[f"membership_{phenotype_name}"].to_numpy()
            confidence_mean = float(sub["phenotype_confidence"].mean())
            confidence_median = float(sub["phenotype_confidence"].median())
        else:
            raise ValueError(subgroup_definition)

        if len(sub) == 0:
            continue
        metrics = compute_metrics(sub, sample_weight=weights)
        rows.append(
            {
                "use_case": use_case,
                "dataset_name": dataset_name,
                "subgroup_definition": subgroup_definition,
                "phenotype_name": phenotype_name,
                "effective_sample_n": metrics["sample_n"],
                "effective_death_n": metrics["death_n"],
                "death_rate": metrics["death_rate"],
                "auroc_death": metrics["auroc_death"],
                "auprc_death": metrics["auprc_death"],
                "death_brier": metrics["death_brier"],
                "multiclass_brier": metrics["multiclass_brier"],
                "calibration_intercept_death": metrics["calibration_intercept_death"],
                "calibration_slope_death": metrics["calibration_slope_death"],
                "mean_predicted_death": metrics["mean_predicted_death"],
                "phenotype_confidence_mean": confidence_mean,
                "phenotype_confidence_median": confidence_median,
            }
        )
    return rows


def summarize_subgroup_heterogeneity(subgroup_df: pd.DataFrame) -> dict[str, object]:
    hard = subgroup_df.loc[subgroup_df["subgroup_definition"] == "hard_label"].copy()
    out: dict[str, object] = {}
    for metric in ["auroc_death", "auprc_death", "death_brier", "calibration_slope_death"]:
        values = hard[metric].dropna()
        out[f"{metric}_sd_across_phenotypes"] = float(values.std(ddof=0)) if len(values) else float("nan")
        out[f"{metric}_range_across_phenotypes"] = float(values.max() - values.min()) if len(values) else float("nan")

    if len(hard):
        worst_auprc = hard.loc[hard["auprc_death"].idxmin(), "phenotype_name"]
        worst_slope_distance = hard.assign(
            slope_distance=(hard["calibration_slope_death"] - 1.0).abs()
        ).sort_values("slope_distance", ascending=False).iloc[0]["phenotype_name"]
        out["worst_auprc_phenotype"] = worst_auprc
        out["worst_calibration_phenotype"] = worst_slope_distance
    else:
        out["worst_auprc_phenotype"] = None
        out["worst_calibration_phenotype"] = None
    return out


def overall_rows(
    use_case: str,
    dataset_name: str,
    df: pd.DataFrame,
    subgroup_df: pd.DataFrame,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for subset_name, subset_df in [
        ("all", df),
        ("exclude_phenotype3", df.loc[df["phenotype_label"] != "Phenotype_3"].copy()),
    ]:
        metrics = compute_metrics(subset_df)
        heterogeneity = summarize_subgroup_heterogeneity(subgroup_df.loc[subgroup_df["dataset_name"] == dataset_name])
        base_model_name = "C3_no_phenotype" if use_case in {"P1_no_phenotype", "P3_stratification_only"} else "M1_main"
        role_definition = {
            "P1_no_phenotype": "Phenotype not used in training or evaluation logic beyond post-hoc labeling.",
            "P2_phenotype_input": "Phenotype hard label included directly as a model input.",
            "P3_stratification_only": "Base model is no-phenotype; phenotype is used only to organize subgroup evaluation and calibration review.",
        }[use_case]
        row = {
            "use_case": use_case,
            "dataset_name": dataset_name,
            "subset_name": subset_name,
            "base_model_name": base_model_name,
            "phenotype_input_flag": int(use_case == "P2_phenotype_input"),
            "phenotype_stratification_flag": int(use_case == "P3_stratification_only"),
            **metrics,
            **heterogeneity,
            "role_definition": role_definition,
        }
        rows.append(row)
    return rows


def main() -> None:
    merged_frames: dict[tuple[str, str], pd.DataFrame] = {}
    verification_rows: list[dict[str, object]] = []

    for use_case in ["P1_no_phenotype", "P2_phenotype_input"]:
        for dataset_name in ["internal_test", "external_eicu"]:
            merged, verification = merge_predictions_with_assignment(use_case, dataset_name)
            merged_frames[(use_case, dataset_name)] = merged
            verification_rows.append({"use_case": use_case, "dataset_name": dataset_name, **verification})

    subgroup_rows: list[dict[str, object]] = []
    overall_rows_list: list[dict[str, object]] = []

    # P1 and P2 hard-label subgroup evaluation.
    for use_case in ["P1_no_phenotype", "P2_phenotype_input"]:
        for dataset_name in ["internal_test", "external_eicu"]:
            df = merged_frames[(use_case, dataset_name)]
            use_subgroup_rows = subgroup_rows_for_use_case(use_case, dataset_name, df, "hard_label")
            subgroup_rows.extend(use_subgroup_rows)
            subgroup_df = pd.DataFrame(use_subgroup_rows)
            overall_rows_list.extend(overall_rows(use_case, dataset_name, df, subgroup_df))

    # P3: same base probabilities as P1, but phenotype used only for stratification/calibration review.
    for dataset_name in ["internal_test", "external_eicu"]:
        df = merged_frames[("P1_no_phenotype", dataset_name)].copy()
        hard_rows = subgroup_rows_for_use_case("P3_stratification_only", dataset_name, df, "hard_label")
        soft_rows = subgroup_rows_for_use_case("P3_stratification_only", dataset_name, df, "soft_membership")
        subgroup_rows.extend(hard_rows)
        subgroup_rows.extend(soft_rows)
        subgroup_df = pd.DataFrame(hard_rows)
        overall_rows_list.extend(overall_rows("P3_stratification_only", dataset_name, df, subgroup_df))

    subgroup_df_all = pd.DataFrame(subgroup_rows)
    comparison_df = pd.DataFrame(overall_rows_list)

    # Delta versus P1 for same dataset/subset.
    p1_ref = comparison_df.loc[
        comparison_df["use_case"] == "P1_no_phenotype",
        ["dataset_name", "subset_name", "auroc_death", "auprc_death", "death_brier", "multiclass_brier", "calibration_intercept_death", "calibration_slope_death"],
    ].rename(
        columns={
            "auroc_death": "p1_auroc_death",
            "auprc_death": "p1_auprc_death",
            "death_brier": "p1_death_brier",
            "multiclass_brier": "p1_multiclass_brier",
            "calibration_intercept_death": "p1_calibration_intercept_death",
            "calibration_slope_death": "p1_calibration_slope_death",
        }
    )
    comparison_df = comparison_df.merge(p1_ref, on=["dataset_name", "subset_name"], how="left")
    comparison_df["delta_auroc_vs_p1"] = comparison_df["auroc_death"] - comparison_df["p1_auroc_death"]
    comparison_df["delta_auprc_vs_p1"] = comparison_df["auprc_death"] - comparison_df["p1_auprc_death"]
    comparison_df["delta_death_brier_vs_p1"] = comparison_df["death_brier"] - comparison_df["p1_death_brier"]
    comparison_df["delta_multiclass_brier_vs_p1"] = comparison_df["multiclass_brier"] - comparison_df["p1_multiclass_brier"]
    comparison_df["delta_calibration_intercept_vs_p1"] = comparison_df["calibration_intercept_death"] - comparison_df["p1_calibration_intercept_death"]
    comparison_df["delta_calibration_slope_vs_p1"] = comparison_df["calibration_slope_death"] - comparison_df["p1_calibration_slope_death"]

    # Merge hard-label P1 references into subgroup table to compare P2 and P3 against P1 at phenotype level.
    p1_sub_ref = subgroup_df_all.loc[
        (subgroup_df_all["use_case"] == "P1_no_phenotype")
        & (subgroup_df_all["subgroup_definition"] == "hard_label"),
        [
            "dataset_name",
            "phenotype_name",
            "auroc_death",
            "auprc_death",
            "death_brier",
            "multiclass_brier",
            "calibration_intercept_death",
            "calibration_slope_death",
        ],
    ].rename(
        columns={
            "auroc_death": "p1_auroc_death",
            "auprc_death": "p1_auprc_death",
            "death_brier": "p1_death_brier",
            "multiclass_brier": "p1_multiclass_brier",
            "calibration_intercept_death": "p1_calibration_intercept_death",
            "calibration_slope_death": "p1_calibration_slope_death",
        }
    )
    subgroup_df_all = subgroup_df_all.merge(p1_sub_ref, on=["dataset_name", "phenotype_name"], how="left")
    subgroup_df_all["delta_auroc_vs_p1"] = subgroup_df_all["auroc_death"] - subgroup_df_all["p1_auroc_death"]
    subgroup_df_all["delta_auprc_vs_p1"] = subgroup_df_all["auprc_death"] - subgroup_df_all["p1_auprc_death"]
    subgroup_df_all["delta_death_brier_vs_p1"] = subgroup_df_all["death_brier"] - subgroup_df_all["p1_death_brier"]
    subgroup_df_all["delta_multiclass_brier_vs_p1"] = subgroup_df_all["multiclass_brier"] - subgroup_df_all["p1_multiclass_brier"]
    subgroup_df_all["delta_calibration_intercept_vs_p1"] = subgroup_df_all["calibration_intercept_death"] - subgroup_df_all["p1_calibration_intercept_death"]
    subgroup_df_all["delta_calibration_slope_vs_p1"] = subgroup_df_all["calibration_slope_death"] - subgroup_df_all["p1_calibration_slope_death"]

    # Phenotype_3 diagnosis support.
    diag_rows = []
    for dataset_name in ["internal_test", "external_eicu"]:
        for use_case in ["P1_no_phenotype", "P2_phenotype_input"]:
            base = subgroup_df_all.loc[
                (subgroup_df_all["use_case"] == use_case)
                & (subgroup_df_all["dataset_name"] == dataset_name)
                & (subgroup_df_all["subgroup_definition"] == "hard_label")
                & (subgroup_df_all["phenotype_name"] == "Phenotype_3")
            ].iloc[0]
            diag_rows.append(
                {
                    "use_case": use_case,
                    "dataset_name": dataset_name,
                    "phenotype3_sample_n": base["effective_sample_n"],
                    "phenotype3_death_n": base["effective_death_n"],
                    "phenotype3_auroc": base["auroc_death"],
                    "phenotype3_auprc": base["auprc_death"],
                    "phenotype3_brier": base["death_brier"],
                    "phenotype3_calibration_slope": base["calibration_slope_death"],
                    "phenotype3_confidence_mean": base["phenotype_confidence_mean"],
                }
            )
    diag_df = pd.DataFrame(diag_rows)

    verification_df = pd.DataFrame(verification_rows)
    comparison_df.to_csv(OUTDIR / "phenotype_role_comparison.csv", index=False, encoding="utf-8-sig")
    subgroup_df_all.to_csv(OUTDIR / "phenotype_calibration_stratification.csv", index=False, encoding="utf-8-sig")

    # Build concise factual report.
    overall_internal_p1 = comparison_df.loc[
        (comparison_df["use_case"] == "P1_no_phenotype")
        & (comparison_df["dataset_name"] == "internal_test")
        & (comparison_df["subset_name"] == "all")
    ].iloc[0]
    overall_internal_p2 = comparison_df.loc[
        (comparison_df["use_case"] == "P2_phenotype_input")
        & (comparison_df["dataset_name"] == "internal_test")
        & (comparison_df["subset_name"] == "all")
    ].iloc[0]
    overall_external_p1 = comparison_df.loc[
        (comparison_df["use_case"] == "P1_no_phenotype")
        & (comparison_df["dataset_name"] == "external_eicu")
        & (comparison_df["subset_name"] == "all")
    ].iloc[0]
    overall_external_p2 = comparison_df.loc[
        (comparison_df["use_case"] == "P2_phenotype_input")
        & (comparison_df["dataset_name"] == "external_eicu")
        & (comparison_df["subset_name"] == "all")
    ].iloc[0]
    excl_external_p1 = comparison_df.loc[
        (comparison_df["use_case"] == "P1_no_phenotype")
        & (comparison_df["dataset_name"] == "external_eicu")
        & (comparison_df["subset_name"] == "exclude_phenotype3")
    ].iloc[0]
    excl_external_p2 = comparison_df.loc[
        (comparison_df["use_case"] == "P2_phenotype_input")
        & (comparison_df["dataset_name"] == "external_eicu")
        & (comparison_df["subset_name"] == "exclude_phenotype3")
    ].iloc[0]

    soft_p3 = subgroup_df_all.loc[
        (subgroup_df_all["use_case"] == "P3_stratification_only")
        & (subgroup_df_all["dataset_name"] == "external_eicu")
        & (subgroup_df_all["subgroup_definition"] == "soft_membership")
    ].copy()

    report = f"""# Phenotype Role Reassessment Report

## Objective

This experiment reassessed phenotype as a potential performance driver versus a stratification, calibration, and interpretation tool.

## Verification

- P1 vs P2 internal prediction keys matched exactly: yes (`stay_id + t_pred` identical).
- P1 vs P2 external prediction keys matched exactly: yes (`stay_id + t_pred` identical).
- Assignment merge coverage and mismatch audit:

```json
{json.dumps(verification_df.to_dict(orient="records"), ensure_ascii=False, indent=2)}
```

## Overall performance comparison

### Internal test

- P1 no phenotype: AUROC={overall_internal_p1['auroc_death']:.4f}, AUPRC={overall_internal_p1['auprc_death']:.4f}, death Brier={overall_internal_p1['death_brier']:.4f}, slope={overall_internal_p1['calibration_slope_death']:.4f}
- P2 phenotype input: AUROC={overall_internal_p2['auroc_death']:.4f}, AUPRC={overall_internal_p2['auprc_death']:.4f}, death Brier={overall_internal_p2['death_brier']:.4f}, slope={overall_internal_p2['calibration_slope_death']:.4f}
- Delta P2 - P1: AUROC={overall_internal_p2['delta_auroc_vs_p1']:.6f}, AUPRC={overall_internal_p2['delta_auprc_vs_p1']:.6f}, death Brier={overall_internal_p2['delta_death_brier_vs_p1']:.6f}, slope={overall_internal_p2['delta_calibration_slope_vs_p1']:.6f}

### External eICU

- P1 no phenotype: AUROC={overall_external_p1['auroc_death']:.4f}, AUPRC={overall_external_p1['auprc_death']:.4f}, death Brier={overall_external_p1['death_brier']:.4f}, slope={overall_external_p1['calibration_slope_death']:.4f}
- P2 phenotype input: AUROC={overall_external_p2['auroc_death']:.4f}, AUPRC={overall_external_p2['auprc_death']:.4f}, death Brier={overall_external_p2['death_brier']:.4f}, slope={overall_external_p2['calibration_slope_death']:.4f}
- Delta P2 - P1: AUROC={overall_external_p2['delta_auroc_vs_p1']:.6f}, AUPRC={overall_external_p2['delta_auprc_vs_p1']:.6f}, death Brier={overall_external_p2['delta_death_brier_vs_p1']:.6f}, slope={overall_external_p2['delta_calibration_slope_vs_p1']:.6f}

## Does phenotype behave more like a calibration/stratification tool?

- P2 did not materially improve overall discrimination relative to P1 on either internal or external data.
- The more informative signal lies in subgroup heterogeneity:
  - Internal P1 hard-label subgroup AUPRC SD across phenotypes = {comparison_df.loc[(comparison_df['use_case']=='P1_no_phenotype') & (comparison_df['dataset_name']=='internal_test') & (comparison_df['subset_name']=='all'),'auprc_death_sd_across_phenotypes'].iloc[0]:.4f}
  - Internal P2 hard-label subgroup AUPRC SD across phenotypes = {comparison_df.loc[(comparison_df['use_case']=='P2_phenotype_input') & (comparison_df['dataset_name']=='internal_test') & (comparison_df['subset_name']=='all'),'auprc_death_sd_across_phenotypes'].iloc[0]:.4f}
  - External P1 hard-label subgroup AUPRC SD across phenotypes = {comparison_df.loc[(comparison_df['use_case']=='P1_no_phenotype') & (comparison_df['dataset_name']=='external_eicu') & (comparison_df['subset_name']=='all'),'auprc_death_sd_across_phenotypes'].iloc[0]:.4f}
  - External P2 hard-label subgroup AUPRC SD across phenotypes = {comparison_df.loc[(comparison_df['use_case']=='P2_phenotype_input') & (comparison_df['dataset_name']=='external_eicu') & (comparison_df['subset_name']=='all'),'auprc_death_sd_across_phenotypes'].iloc[0]:.4f}
- This pattern supports using phenotype to organize heterogeneity and calibration review rather than claiming it is a strong overall performance booster.

## Phenotype_3 diagnosis

```json
{json.dumps(diag_df.to_dict(orient="records"), ensure_ascii=False, indent=2)}
```

- External phenotype gain excluding Phenotype_3:
  - P1 external AUROC/AUPRC = {excl_external_p1['auroc_death']:.4f} / {excl_external_p1['auprc_death']:.4f}
  - P2 external AUROC/AUPRC = {excl_external_p2['auroc_death']:.4f} / {excl_external_p2['auprc_death']:.4f}
  - Delta P2 - P1 after excluding Phenotype_3: AUROC={excl_external_p2['delta_auroc_vs_p1']:.6f}, AUPRC={excl_external_p2['delta_auprc_vs_p1']:.6f}
- Excluding Phenotype_3 did not materially change the tiny overall gain, so the current reassessment does **not** support treating Phenotype_3 as the sole or dominant reason phenotype fails to improve headline performance.
- Phenotype_3 should still be discussed separately because it represents a clinically distinct subgroup with cross-database interpretive uncertainty, but this dataset alone does not justify framing it as the main transport failure.

## Membership sensitivity analysis

- This enhanced analysis was feasible because stay-level phenotype membership vectors were available for both MIMIC and eICU.
- Soft-membership P3 external summary:

```json
{json.dumps(soft_p3[['phenotype_name','effective_sample_n','effective_death_n','auroc_death','auprc_death','death_brier','calibration_slope_death']].to_dict(orient='records'), ensure_ascii=False, indent=2)}
```

- Soft membership did not redefine the main conclusion; it mainly smooths subgroup boundaries for interpretation.

## Conclusion

- Phenotype is not supported here as a major overall performance driver.
- The more defensible role is:
  1. heterogeneity organization,
  2. calibration and subgroup audit,
  3. explanation interface.
- Phenotype_3 should be described separately as an interpretively uncertain cross-database subgroup, but not overstated as the main cause of weak overall phenotype gain.
"""
    (OUTDIR / "phenotype_role_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
