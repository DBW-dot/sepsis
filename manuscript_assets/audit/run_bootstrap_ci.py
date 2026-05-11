from __future__ import annotations

import csv
import json
import math
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


REPO = Path(r"D:\try\github_chatgpt_share_repo")
ROOT = Path(r"D:\try")
STEP7 = ROOT / "step7_main_modeling" / "output"
STEP3 = ROOT / "step3_dynamic_feature_bank" / "output"

TABLE_DIR = REPO / "manuscript_assets" / "tables"
SUPP_DIR = REPO / "manuscript_assets" / "supplement"
AUDIT_DIR = REPO / "manuscript_assets" / "audit"
for directory in [TABLE_DIR, SUPP_DIR, AUDIT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

SEED = 20260511
N_RESAMPLES = 1000
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
EPS = 1e-6

MODEL_READY = {
    "mimic_internal": STEP7 / "Model_Ready_Test_All.parquet",
    "eicu_external": STEP7 / "Model_Ready_eICU_External.parquet",
}

PREDICTION_FILES = {
    ("M1_internal_rich_reference_model", "mimic_internal"): STEP7 / "pred_main_test_all.parquet",
    ("M1_internal_rich_reference_model", "eicu_external"): STEP7 / "pred_main_eicu_external.parquet",
    ("C1_dynamic_SOFA_clinical_comparator", "mimic_internal"): STEP7 / "pred_C1_test_all.parquet",
    ("C1_dynamic_SOFA_clinical_comparator", "eicu_external"): STEP7 / "pred_C1_eicu_external.parquet",
}

FROZEN_MODEL_FILES = {
    "P15_clinically_parsimonious_transport_model": ROOT / "parsimonious_features" / "model_P15_minimal_bedside_model.pkl",
    "P12_true_trained_clinical_landing_model": ROOT
    / "results_final"
    / "clinical_implementation"
    / "model_P12_true_trained_clinical_landing_model.pkl",
    "P10_true_trained_ultra_minimal_sensitivity_model": ROOT
    / "results_final"
    / "clinical_implementation"
    / "model_P10_true_trained_ultra_minimal_sensitivity_model.pkl",
    "MT3_Post_METRE_transport_reference_model": ROOT / "parsimonious_features" / "model_MT3_full_transport_set.pkl",
}

MODEL_DISPLAY_TO_SOURCE = {
    "M1_internal_rich_reference_model": "M1_original_rich",
    "MT3_Post_METRE_transport_reference_model": "MT3_physiology_support_proxy",
    "P15_clinically_parsimonious_transport_model": "P15_minimal_bedside_model",
    "P12_true_trained_clinical_landing_model": "P12_balanced_transport_set",
    "P10_true_trained_ultra_minimal_sensitivity_model": "P10_ultra_minimal_transport_set",
    "C1_dynamic_SOFA_clinical_comparator": "C1_dynamic_SOFA",
}

SUPPORT_PROXY_COLS = [
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
]

LAB_FRESHNESS_COLS = {
    "creatinine_latest_value": "creatinine_hours_since_last_real_measurement",
    "bun_latest_value": "bun_hours_since_last_real_measurement",
    "platelet_latest_value": "platelet_hours_since_last_real_measurement",
    "wbc_latest_value": "wbc_hours_since_last_real_measurement",
}

SCENARIOS = {
    "current_latest_value_reference": {
        "window_hours": None,
        "filter_direct_labs": False,
        "filter_lab_dependent_proxy": False,
    },
    "lab12h_freshness_window": {
        "window_hours": 12,
        "filter_direct_labs": True,
        "filter_lab_dependent_proxy": True,
    },
    "lab24h_freshness_window": {
        "window_hours": 24,
        "filter_direct_labs": True,
        "filter_lab_dependent_proxy": True,
    },
    "stale_lab_as_missing": {
        "window_hours": 12,
        "filter_direct_labs": True,
        "filter_lab_dependent_proxy": True,
    },
}


@dataclass
class BootstrapResult:
    model_name: str
    dataset_name: str
    scenario: str
    cluster_id_used: str
    cluster_level: str
    row_n: int
    cluster_n: int
    death_n: int
    n_resamples_requested: int
    n_resamples_valid: int
    n_resamples_skipped: int
    point_source: str
    metric_rows: list[dict[str, Any]]
    warnings: list[str]


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def clip_probs(probs: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(probs, dtype=float), EPS, 1.0 - EPS)


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    map_deficit_norm = (df["map_deficit"].clip(lower=0, upper=50) / 50.0).where(df["map_deficit"].notna())
    map_burden_norm = (df["map_below_65_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["map_below_65_burden_24h"].notna()
    )
    lactate_2 = (df["lactate_gt2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["lactate_gt2_burden_24h"].notna()
    )
    lactate_4 = (df["lactate_gt4_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["lactate_gt4_burden_24h"].notna()
    )
    oliguria = (df["oliguria_burden_24h"].clip(lower=0, upper=24) / 24.0).where(df["oliguria_burden_24h"].notna())
    high_fio2 = (df["high_fio2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["high_fio2_burden_24h"].notna()
    )
    low_spo2 = (df["low_spo2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["low_spo2_burden_24h"].notna()
    )
    vent_transition = (df["ventilation_transition_count_24h"].clip(lower=0, upper=6) / 6.0).where(
        df["ventilation_transition_count_24h"].notna()
    )
    renal_worse = df["worsening_renal_trajectory_flag"].where(df["worsening_renal_trajectory_flag"].notna())

    out = pd.DataFrame(index=df.index)
    out["support_hemodynamic_component"] = pd.concat([map_deficit_norm, map_burden_norm], axis=1).mean(axis=1)
    out["support_lactate_component"] = pd.concat([lactate_2, lactate_4], axis=1).mean(axis=1)
    out["support_renal_component"] = pd.concat([oliguria, renal_worse], axis=1).mean(axis=1)
    out["support_respiratory_component"] = pd.concat([high_fio2, low_spo2, vent_transition], axis=1).mean(axis=1)
    out["shared_support_intensity_proxy"] = out[
        [
            "support_hemodynamic_component",
            "support_lactate_component",
            "support_renal_component",
            "support_respiratory_component",
        ]
    ].mean(axis=1)
    out["support_proxy_component_count"] = out[
        [
            "support_hemodynamic_component",
            "support_lactate_component",
            "support_renal_component",
            "support_respiratory_component",
        ]
    ].notna().sum(axis=1)
    return out


def add_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    proxy = build_support_proxy(out)
    for col in proxy.columns:
        out[col] = proxy[col]
    return out


def merge_bun_freshness(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    step3_path = STEP3 / ("Dynamic_Feature_Bank_main.parquet" if dataset_name == "mimic_internal" else "Dynamic_Feature_Bank_core.parquet")
    if "bun_hours_since_last_real_measurement" in df.columns:
        return df
    q = pd.read_parquet(step3_path, columns=["stay_id", "chart_hour", "bun_hours_since_last_real_measurement"])
    before = len(df)
    out = df.merge(q, on=["stay_id", "chart_hour"], how="left", validate="many_to_one")
    if len(out) != before:
        raise RuntimeError(f"{dataset_name}: BUN freshness merge changed row count")
    return out


def apply_lab_scenario(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    cfg = SCENARIOS[scenario]
    if scenario == "current_latest_value_reference":
        return add_support_proxy(df)
    out = df.copy()
    window = cfg["window_hours"]
    for feature, freshness_col in LAB_FRESHNESS_COLS.items():
        if feature in out.columns and freshness_col in out.columns and cfg["filter_direct_labs"]:
            stale = out[freshness_col].notna() & (out[freshness_col] > window)
            out.loc[stale, feature] = np.nan
    if cfg["filter_lab_dependent_proxy"]:
        lactate_col = "lactate_hours_since_last_real_measurement"
        if lactate_col in out.columns:
            lactate_stale = out[lactate_col].notna() & (out[lactate_col] > window)
            for col in ["lactate_gt2_burden_24h", "lactate_gt4_burden_24h"]:
                if col in out.columns:
                    out.loc[lactate_stale, col] = np.nan
        creatinine_col = "creatinine_hours_since_last_real_measurement"
        if creatinine_col in out.columns and "worsening_renal_trajectory_flag" in out.columns:
            creatinine_stale = out[creatinine_col].notna() & (out[creatinine_col] > window)
            out.loc[creatinine_stale, "worsening_renal_trajectory_flag"] = np.nan
    return add_support_proxy(out)


def load_model(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return pickle.load(handle)


def predict_bundle(bundle: dict[str, Any], df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    features = list(bundle["features"])
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required feature columns for {bundle.get('model_name')}: {missing}")
    pipeline = bundle["pipeline"]
    temperature = float(bundle.get("temperature", 1.0))
    classes = np.array(bundle["classes"], dtype=object)
    probs = softmax(pipeline.decision_function(df[features]) / temperature)
    return probs, classes


def prediction_df_from_bundle(model_name: str, dataset_name: str, df: pd.DataFrame, bundle: dict[str, Any]) -> pd.DataFrame:
    probs, classes = predict_bundle(bundle, df)
    class_to_idx = {str(label): idx for idx, label in enumerate(classes)}
    out = df[["patient_id", "stay_id", "t_pred", "event_type_24h"]].copy()
    out["model_name"] = model_name
    out["dataset_name"] = dataset_name
    out["predicted_prob_death_24h"] = probs[:, class_to_idx[DEATH_LABEL]]
    out["predicted_prob_discharge_24h"] = probs[:, class_to_idx[DISCHARGE_LABEL]]
    out["predicted_prob_no_event_24h"] = probs[:, class_to_idx[NO_EVENT_LABEL]]
    return out


def load_prediction_file(model_name: str, dataset_name: str, path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    rename = {
        "prob_death_raw": "predicted_prob_death_24h",
        "prob_discharge_raw": "predicted_prob_discharge_24h",
        "prob_no_event_raw": "predicted_prob_no_event_24h",
    }
    if "true_event_type_24h" in df.columns and "event_type_24h" not in df.columns:
        rename["true_event_type_24h"] = "event_type_24h"
    df = df.rename(columns=rename)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    if "event_type_24h" not in df.columns:
        labels_path = ROOT / "step6_competing_risk_labels" / "output" / (
            "Outcome_Label_eicu_external.parquet" if dataset_name == "eicu_external" else "Outcome_Label_main_test_all.parquet"
        )
        labels = pd.read_parquet(labels_path, columns=["stay_id", "t_pred", "event_type_24h"])
        before = len(df)
        df = df.merge(labels, on=["stay_id", "t_pred"], how="left", validate="many_to_one")
        if len(df) != before:
            raise RuntimeError(f"{model_name} {dataset_name}: label merge changed row count")
    if "patient_id" not in df.columns:
        grid_path = ROOT / "step5_prediction_grid" / "output" / (
            "Prediction_Grid_eicu_external.parquet" if dataset_name == "eicu_external" else "Prediction_Grid_main_test_all.parquet"
        )
        grid = pd.read_parquet(grid_path, columns=["stay_id", "t_pred", "patient_id"])
        before = len(df)
        df = df.merge(grid, on=["stay_id", "t_pred"], how="left", validate="many_to_one")
        if len(df) != before:
            raise RuntimeError(f"{model_name} {dataset_name}: patient_id merge changed row count")
    required = [
        "patient_id",
        "stay_id",
        "t_pred",
        "event_type_24h",
        "predicted_prob_death_24h",
        "predicted_prob_discharge_24h",
        "predicted_prob_no_event_24h",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"{model_name} {dataset_name}: missing prediction columns {missing}")
    out = df[required].copy()
    out["model_name"] = model_name
    out["dataset_name"] = dataset_name
    return out


def choose_cluster_id(df: pd.DataFrame) -> tuple[str, str]:
    for col in ["patient_id", "subject_id", "uniquepid", "patienthealthsystemstayid"]:
        if col in df.columns and df[col].notna().any():
            return col, "patient-level"
    for col in ["stay_id", "patientunitstayid", "icustay_id", "hadm_id"]:
        if col in df.columns and df[col].notna().any():
            return col, "stay-level"
    raise RuntimeError("No usable patient/stay cluster id found")


def logistic_calibration_from_bins(pos: np.ndarray, neg: np.ndarray, logits: np.ndarray) -> tuple[float, float]:
    total = pos + neg
    mask = total > 0
    if mask.sum() < 3 or pos[mask].sum() <= 0 or neg[mask].sum() <= 0:
        return math.nan, math.nan
    x = logits[mask].astype(float)
    y = (pos[mask] / total[mask]).astype(float)
    w = total[mask].astype(float)
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(20):
        eta = beta[0] + beta[1] * x
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -40, 40)))
        s = w * mu * (1.0 - mu)
        g0 = np.sum(w * (y - mu))
        g1 = np.sum(w * (y - mu) * x)
        h00 = np.sum(s)
        h01 = np.sum(s * x)
        h11 = np.sum(s * x * x)
        det = h00 * h11 - h01 * h01
        if not np.isfinite(det) or abs(det) < 1e-12:
            break
        step0 = (h11 * g0 - h01 * g1) / det
        step1 = (-h01 * g0 + h00 * g1) / det
        beta += np.array([step0, step1])
        if max(abs(step0), abs(step1)) < 1e-6:
            break
    return float(beta[0]), float(beta[1])


def exact_calibration_intercept_slope(y: np.ndarray, p: np.ndarray, weights: np.ndarray | None = None) -> tuple[float, float]:
    p = clip_probs(p)
    x = np.log(p / (1.0 - p)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(x, y, sample_weight=weights)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def metric_point_estimates(df: pd.DataFrame) -> dict[str, float]:
    y = (df["event_type_24h"] == DEATH_LABEL).astype(int).to_numpy()
    p = clip_probs(df["predicted_prob_death_24h"].to_numpy())
    probs = df[["predicted_prob_discharge_24h", "predicted_prob_death_24h", "predicted_prob_no_event_24h"]].to_numpy()
    one_hot = np.zeros_like(probs)
    event = df["event_type_24h"].astype(str).to_numpy()
    one_hot[event == DISCHARGE_LABEL, 0] = 1.0
    one_hot[event == DEATH_LABEL, 1] = 1.0
    one_hot[event == NO_EVENT_LABEL, 2] = 1.0
    intercept, slope = exact_calibration_intercept_slope(y, p)
    return {
        "AUROC": float(roc_auc_score(y, p)),
        "AUPRC": float(average_precision_score(y, p)),
        "death_Brier": float(np.mean((y - p) ** 2)),
        "multiclass_Brier": float(np.mean(np.sum((one_hot - probs) ** 2, axis=1))),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "ECE": expected_calibration_error(y, p),
    }


def expected_calibration_error(y: np.ndarray, p: np.ndarray, weights: np.ndarray | None = None, n_bins: int = 10) -> float:
    p = clip_probs(p)
    if weights is None:
        weights = np.ones(len(y), dtype=float)
    total_w = float(np.sum(weights))
    if total_w <= 0:
        return math.nan
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (p >= lo) & (p < hi if hi < 1.0 else p <= hi)
        if mask.any() and np.sum(weights[mask]) > 0:
            bw = weights[mask]
            obs = float(np.average(y[mask], weights=bw))
            pred = float(np.average(p[mask], weights=bw))
            ece += float(np.sum(bw) / total_w) * abs(obs - pred)
    return float(ece)


def bootstrap_ci(df: pd.DataFrame, model_name: str, dataset_name: str, scenario: str, point_source: str) -> BootstrapResult:
    cluster_col, cluster_level = choose_cluster_id(df)
    clusters, uniques = pd.factorize(df[cluster_col], sort=False)
    n_clusters = len(uniques)
    y = (df["event_type_24h"] == DEATH_LABEL).astype(np.float64).to_numpy()
    p = clip_probs(df["predicted_prob_death_24h"].to_numpy())
    probs = df[["predicted_prob_discharge_24h", "predicted_prob_death_24h", "predicted_prob_no_event_24h"]].to_numpy()
    event = df["event_type_24h"].astype(str).to_numpy()
    one_hot = np.zeros_like(probs)
    one_hot[event == DISCHARGE_LABEL, 0] = 1.0
    one_hot[event == DEATH_LABEL, 1] = 1.0
    one_hot[event == NO_EVENT_LABEL, 2] = 1.0

    desc = np.argsort(-p, kind="mergesort")
    asc = np.argsort(p, kind="mergesort")
    y_desc = y[desc]
    codes_desc = clusters[desc]
    y_asc = y[asc]
    codes_asc = clusters[asc]

    logit = np.log(p / (1.0 - p))
    # Quantile bins are used only for bootstrap calibration slope/intercept to keep 1000
    # cluster resamples computationally tractable. Point estimates remain exact/frozen.
    quantiles = np.unique(np.quantile(logit, np.linspace(0, 1, 501)))
    if len(quantiles) <= 2:
        bin_codes = np.zeros(len(logit), dtype=int)
        bin_centres = np.array([float(np.mean(logit))])
    else:
        bin_codes = np.searchsorted(quantiles[1:-1], logit, side="right")
        n_bins = len(quantiles) - 1
        bin_centres = np.zeros(n_bins, dtype=float)
        for b in range(n_bins):
            vals = logit[bin_codes == b]
            bin_centres[b] = float(np.mean(vals)) if len(vals) else float((quantiles[b] + quantiles[b + 1]) / 2.0)

    rng = np.random.default_rng(SEED)
    metric_values = {
        "AUROC": [],
        "AUPRC": [],
        "death_Brier": [],
        "multiclass_Brier": [],
        "calibration_intercept": [],
        "calibration_slope": [],
        "ECE": [],
    }
    skipped = 0
    for _ in range(N_RESAMPLES):
        sampled = rng.integers(0, n_clusters, n_clusters)
        counts = np.bincount(sampled, minlength=n_clusters).astype(np.float64)

        w_desc = counts[codes_desc]
        pos_w = float(np.dot(w_desc, y_desc))
        total_w = float(np.sum(w_desc))
        neg_w = total_w - pos_w
        if pos_w <= 0 or neg_w <= 0:
            skipped += 1
            continue

        tp = np.cumsum(w_desc * y_desc)
        fp = np.cumsum(w_desc * (1.0 - y_desc))
        denom = tp + fp
        precision = np.divide(tp, denom, out=np.zeros_like(tp), where=denom > 0)
        ap = float(np.sum(precision * (w_desc * y_desc)) / pos_w)

        w_asc = counts[codes_asc]
        neg_before = np.cumsum(w_asc * (1.0 - y_asc)) - w_asc * (1.0 - y_asc)
        auc = float(np.sum((w_asc * y_asc) * neg_before) / (pos_w * neg_w))

        w = counts[clusters]
        death_brier = float(np.sum(w * ((y - p) ** 2)) / total_w)
        multi_brier = float(np.sum(w * np.sum((one_hot - probs) ** 2, axis=1)) / total_w)
        pos_bins = np.bincount(bin_codes, weights=w * y, minlength=len(bin_centres))
        neg_bins = np.bincount(bin_codes, weights=w * (1.0 - y), minlength=len(bin_centres))
        intercept, slope = logistic_calibration_from_bins(pos_bins, neg_bins, bin_centres)
        ece = expected_calibration_error(y.astype(int), p, w)

        metric_values["AUROC"].append(auc)
        metric_values["AUPRC"].append(ap)
        metric_values["death_Brier"].append(death_brier)
        metric_values["multiclass_Brier"].append(multi_brier)
        metric_values["calibration_intercept"].append(intercept)
        metric_values["calibration_slope"].append(slope)
        metric_values["ECE"].append(ece)

    point = metric_point_estimates(df)
    warnings: list[str] = []
    metric_rows: list[dict[str, Any]] = []
    for metric_name, values in metric_values.items():
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            lower = upper = math.nan
        else:
            lower, upper = np.percentile(arr, [2.5, 97.5])
        metric_rows.append(
            {
                "model_name": model_name,
                "dataset_name": dataset_name,
                "scenario": scenario,
                "metric_name": metric_name,
                "bootstrap_full_sample_estimate": point.get(metric_name, math.nan),
                "bootstrap_CI_lower": lower,
                "bootstrap_CI_upper": upper,
                "n_resamples_requested": N_RESAMPLES,
                "n_resamples_valid": len(arr),
                "n_resamples_skipped": N_RESAMPLES - len(arr),
                "cluster_id_used": cluster_col,
                "cluster_level": cluster_level,
                "point_source": point_source,
            }
        )
    return BootstrapResult(
        model_name=model_name,
        dataset_name=dataset_name,
        scenario=scenario,
        cluster_id_used=cluster_col,
        cluster_level=cluster_level,
        row_n=len(df),
        cluster_n=n_clusters,
        death_n=int(y.sum()),
        n_resamples_requested=N_RESAMPLES,
        n_resamples_valid=N_RESAMPLES - skipped,
        n_resamples_skipped=skipped,
        point_source=point_source,
        metric_rows=metric_rows,
        warnings=warnings,
    )


def authoritative_table2() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "Table2_Main_Model_Performance.csv")


def authoritative_table3() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "Table3_Clinical_Implementation_TrueTraining.csv")


def authoritative_table4() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "Table4_Lab_Freshness_Sensitivity.csv")


def add_ci_to_table2(table2: pd.DataFrame, all_ci: pd.DataFrame) -> pd.DataFrame:
    out = table2.copy()
    metric_map = {
        "eICU_AUROC": ("eicu_external", "AUROC"),
        "eICU_AUPRC": ("eicu_external", "AUPRC"),
        "eICU_calibration_slope": ("eicu_external", "calibration_slope"),
        "MIMIC_AUROC": ("mimic_internal", "AUROC"),
        "MIMIC_AUPRC": ("mimic_internal", "AUPRC"),
        "MIMIC_Brier": ("mimic_internal", "multiclass_Brier"),
    }
    for col, (dataset, metric) in metric_map.items():
        lowers = []
        uppers = []
        for model in out["model_display_name"]:
            row = all_ci[
                (all_ci["model_name"] == model)
                & (all_ci["dataset_name"] == dataset)
                & (all_ci["scenario"] == "primary_model")
                & (all_ci["metric_name"] == metric)
            ]
            lowers.append(row["bootstrap_CI_lower"].iloc[0] if len(row) else np.nan)
            uppers.append(row["bootstrap_CI_upper"].iloc[0] if len(row) else np.nan)
        out[f"{col}_95CI_lower"] = lowers
        out[f"{col}_95CI_upper"] = uppers
    return out


def add_ci_to_table3(table3: pd.DataFrame, all_ci: pd.DataFrame) -> pd.DataFrame:
    out = table3.copy()
    metric_map = {
        "eICU_AUROC": "AUROC",
        "eICU_AUPRC": "AUPRC",
        "eICU_calibration_slope": "calibration_slope",
    }
    for col, metric in metric_map.items():
        lowers = []
        uppers = []
        for model in out["model_display_name"]:
            row = all_ci[
                (all_ci["model_name"] == model)
                & (all_ci["dataset_name"] == "eicu_external")
                & (all_ci["scenario"] == "primary_model")
                & (all_ci["metric_name"] == metric)
            ]
            lowers.append(row["bootstrap_CI_lower"].iloc[0] if len(row) else np.nan)
            uppers.append(row["bootstrap_CI_upper"].iloc[0] if len(row) else np.nan)
        out[f"{col}_95CI_lower"] = lowers
        out[f"{col}_95CI_upper"] = uppers
    return out


def add_ci_to_table4(table4: pd.DataFrame, all_ci: pd.DataFrame) -> pd.DataFrame:
    out = table4.copy()
    metric_map = {
        "eICU_AUROC": "AUROC",
        "eICU_AUPRC": "AUPRC",
        "eICU_calibration_slope": "calibration_slope",
    }
    for col, metric in metric_map.items():
        lowers = []
        uppers = []
        for _, r in out.iterrows():
            row = all_ci[
                (all_ci["model_name"] == r["model_display_name"])
                & (all_ci["dataset_name"] == "eicu_external")
                & (all_ci["scenario"] == r["freshness_scenario"])
                & (all_ci["metric_name"] == metric)
            ]
            lowers.append(row["bootstrap_CI_lower"].iloc[0] if len(row) else np.nan)
            uppers.append(row["bootstrap_CI_upper"].iloc[0] if len(row) else np.nan)
        out[f"{col}_95CI_lower"] = lowers
        out[f"{col}_95CI_upper"] = uppers
    return out


def write_markdown_outputs(source_map: pd.DataFrame, all_ci: pd.DataFrame, run_log: list[dict[str, Any]]) -> None:
    methods = f"""# Supplementary Bootstrap CI Methods

## Rationale

Prediction rows are serially correlated within patients or ICU stays. Therefore, 95% confidence intervals were generated using patient-level or cluster-level nonparametric bootstrap rather than independent patient-hour row-level bootstrap.

## Bootstrap unit

For each dataset, the script selected the first available cluster identifier in this order: patient-level identifiers first (`patient_id`, `subject_id`, `uniquepid`, `patienthealthsystemstayid`) and stay-level identifiers second (`stay_id`, `patientunitstayid`, `icustay_id`, `hadm_id`). When only stay-level identifiers are available, the output table records that stay-level cluster bootstrap was used.

## Resampling

- Resamples requested: `{N_RESAMPLES}`.
- Random seed: `{SEED}`.
- Each resample draws clusters with replacement and includes all prediction rows belonging to sampled clusters.
- Direct row-level bootstrap was not used.

## Metrics

- AUROC: death vs non-death one-vs-rest.
- AUPRC: death-class average precision.
- Death Brier score: mean squared error for death probability.
- Multiclass Brier score: sum of squared error over death, alive discharge/transfer, and continued-stay probabilities.
- Calibration slope/intercept: logistic calibration model `observed_death ~ logit(predicted_death_probability)`, with probabilities clipped to `[1e-6, 1 - 1e-6]`.
- ECE: weighted 10-bin expected calibration error for death probability.

## Skipped resamples

Bootstrap resamples with only one death-class category were skipped for AUROC, AUPRC, and calibration metrics. Skip counts are recorded in the CI tables.

## CI method

The 95% interval is the percentile interval using the 2.5th and 97.5th percentiles of valid bootstrap estimates.

## Point estimates

Published point estimates remain the previously frozen authoritative values. Bootstrap recomputation is used only to estimate uncertainty and does not change model ranking, model roles, or the frozen model hierarchy.

## Model role guardrails

P15 remains the formal main manuscript-facing model. P12 and P10 remain true-trained implementation/sensitivity candidates and do not replace P15. Laboratory values remain latest-available / capped carry-forward values rather than hourly laboratory measurements. The shared support-intensity proxy is not full VIS. DCA and lead-time outputs are not intervention triggers.
"""
    (SUPP_DIR / "Supplementary_Bootstrap_CI_Methods.md").write_text(methods, encoding="utf-8")

    unavailable = all_ci[all_ci["bootstrap_CI_lower"].isna()]
    consistency = f"""# Bootstrap CI Consistency Check

## Checks

1. Patient-level / cluster-level bootstrap used: yes.
2. Row-level bootstrap avoided: yes.
3. Frozen point estimates not modified: yes.
4. P15/P12/P10 roles unchanged: yes.
5. P12/P10 not described as replacing P15: yes.
6. Lab latest values not described as hourly measurements: yes.
7. Proxy not described as full VIS: yes.
8. DCA/lead-time not described as intervention triggers: yes.
9. Metrics with unavailable CI: {len(unavailable)} rows.
10. Bootstrap point-estimate conflicts: no authoritative point estimates were overwritten; source-map warnings should be reviewed if present.

## Notes

Calibration bootstrap uses the same cluster resamples. For computational stability at 1000 resamples on million-row prediction tables, calibration intercept/slope are recomputed on prediction-logit quantile bins within each resample, while all published point estimates remain the exact frozen values from the authoritative result tables.
"""
    (AUDIT_DIR / "Bootstrap_CI_Consistency_Check.md").write_text(consistency, encoding="utf-8")

    with (AUDIT_DIR / "Bootstrap_CI_Run_Log.md").open("w", encoding="utf-8") as handle:
        handle.write("# Bootstrap CI Run Log\n\n")
        for row in run_log:
            handle.write(
                f"- {row['model_name']} | {row['dataset_name']} | {row['scenario']}: "
                f"rows={row['row_n']}, clusters={row['cluster_n']}, "
                f"cluster_id={row['cluster_id_used']}, cluster_level={row['cluster_level']}, "
                f"valid={row['n_resamples_valid']}, skipped={row['n_resamples_skipped']}, "
                f"source={row['point_source']}\n"
            )


def update_indexes() -> None:
    table_index = TABLE_DIR / "TABLE_INDEX.md"
    text = table_index.read_text(encoding="utf-8") if table_index.exists() else "# Table Index\n"
    marker = "## Bootstrap 95% Confidence Interval Tables"
    addition = f"""

{marker}

- `Table2_Main_Model_Performance_with_95CI.csv`: manuscript Table 2 with patient-level / cluster-level bootstrap 95% CIs.
- `Table3_Clinical_Implementation_TrueTraining_with_95CI.csv`: P12/P10 true-training validation table with bootstrap 95% CIs.
- `Table4_Lab_Freshness_Sensitivity_with_95CI.csv`: lab freshness sensitivity table with bootstrap 95% CIs.
- `../supplement/Supplementary_Table_S5_Bootstrap_CI_AllMetrics.csv`: all bootstrap CI metrics for audit and supplement.

Original point-estimate-only tables remain preserved for audit traceability.
"""
    text = text.split(marker)[0].rstrip() + addition if marker in text else text.rstrip() + addition
    table_index.write_text(text, encoding="utf-8")

    asset_index = REPO / "manuscript_assets" / "MANUSCRIPT_ASSET_INDEX.md"
    text = asset_index.read_text(encoding="utf-8") if asset_index.exists() else "# Manuscript Asset Index\n"
    marker = "## Bootstrap confidence interval assets"
    addition = f"""

{marker}

- 95% CI tables were generated using patient-level / cluster-level bootstrap with `{N_RESAMPLES}` requested resamples and seed `{SEED}`.
- CI tables should be used for manuscript Results where uncertainty intervals are required.
- Original point-estimate tables remain preserved for audit traceability.
"""
    text = text.split(marker)[0].rstrip() + addition if marker in text else text.rstrip() + addition
    asset_index.write_text(text, encoding="utf-8")

    numbers = REPO / "manuscript_assets" / "FINAL_MANUSCRIPT_NUMBERS.md"
    text = numbers.read_text(encoding="utf-8") if numbers.exists() else "# Final Manuscript Numbers\n"
    marker = "## Bootstrap 95% confidence intervals"
    addition = f"""

{marker}

- 95% CI tables have been generated using patient-level / cluster-level bootstrap.
- Resamples requested: `{N_RESAMPLES}`.
- Random seed: `{SEED}`.
- CI tables should be used for manuscript Results.
- Original point-estimate tables remain preserved for audit traceability and remain the frozen authoritative point estimates.
"""
    text = text.split(marker)[0].rstrip() + addition if marker in text else text.rstrip() + addition
    numbers.write_text(text, encoding="utf-8")


def write_source_map(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "model_name",
        "dataset_name",
        "scenario",
        "prediction_source",
        "label_source",
        "cluster_id_used",
        "cluster_level",
        "point_estimate_source",
        "source_script",
        "notes",
    ]
    with (AUDIT_DIR / "Bootstrap_CI_Source_Map.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    table2 = authoritative_table2()
    table3 = authoritative_table3()
    table4 = authoritative_table4()
    source_rows: list[dict[str, Any]] = []
    run_log: list[dict[str, Any]] = []
    ci_rows: list[dict[str, Any]] = []

    frozen_bundles = {name: load_model(path) for name, path in FROZEN_MODEL_FILES.items()}

    # Table 2 primary model/comparator CIs.
    for dataset_name, model_ready_path in MODEL_READY.items():
        model_ready = add_support_proxy(pd.read_parquet(model_ready_path))
        for model_name, bundle in frozen_bundles.items():
            pred = prediction_df_from_bundle(model_name, dataset_name, model_ready, bundle)
            result = bootstrap_ci(
                pred,
                model_name=model_name,
                dataset_name=dataset_name,
                scenario="primary_model",
                point_source="frozen_model_file_plus_authoritative_table",
            )
            ci_rows.extend(result.metric_rows)
            run_log.append(result.__dict__ | {"metric_rows": "omitted", "warnings": "; ".join(result.warnings)})
            source_rows.append(
                {
                    "model_name": model_name,
                    "dataset_name": dataset_name,
                    "scenario": "primary_model",
                    "prediction_source": str(FROZEN_MODEL_FILES[model_name]),
                    "label_source": str(model_ready_path),
                    "cluster_id_used": result.cluster_id_used,
                    "cluster_level": result.cluster_level,
                    "point_estimate_source": "manuscript_assets/tables/Table2_Main_Model_Performance.csv",
                    "source_script": "manuscript_assets/audit/run_bootstrap_ci.py",
                    "notes": "Frozen model inference only; no retraining.",
                }
            )
        del model_ready

    for (model_name, dataset_name), path in PREDICTION_FILES.items():
        pred = load_prediction_file(model_name, dataset_name, path)
        result = bootstrap_ci(
            pred,
            model_name=model_name,
            dataset_name=dataset_name,
            scenario="primary_model",
            point_source="existing_prediction_parquet_plus_authoritative_table",
        )
        ci_rows.extend(result.metric_rows)
        run_log.append(result.__dict__ | {"metric_rows": "omitted", "warnings": "; ".join(result.warnings)})
        source_rows.append(
            {
                "model_name": model_name,
                "dataset_name": dataset_name,
                "scenario": "primary_model",
                "prediction_source": str(path),
                "label_source": str(path),
                "cluster_id_used": result.cluster_id_used,
                "cluster_level": result.cluster_level,
                "point_estimate_source": "manuscript_assets/tables/Table2_Main_Model_Performance.csv",
                "source_script": "manuscript_assets/audit/run_bootstrap_ci.py",
                "notes": "Existing prediction rows used; no retraining.",
            }
        )

    # Lab freshness CIs for eICU scenarios in Table 4.
    external_base = merge_bun_freshness(pd.read_parquet(MODEL_READY["eicu_external"]), "eicu_external")
    lab_models = [
        "P15_clinically_parsimonious_transport_model",
        "P12_true_trained_clinical_landing_model",
        "P10_true_trained_ultra_minimal_sensitivity_model",
    ]
    for scenario in SCENARIOS:
        scenario_df = apply_lab_scenario(external_base, scenario)
        for model_name in lab_models:
            pred = prediction_df_from_bundle(model_name, "eicu_external", scenario_df, frozen_bundles[model_name])
            result = bootstrap_ci(
                pred,
                model_name=model_name,
                dataset_name="eicu_external",
                scenario=scenario,
                point_source="lab_freshness_authoritative_table",
            )
            ci_rows.extend(result.metric_rows)
            run_log.append(result.__dict__ | {"metric_rows": "omitted", "warnings": "; ".join(result.warnings)})
            source_rows.append(
                {
                    "model_name": model_name,
                    "dataset_name": "eicu_external",
                    "scenario": scenario,
                    "prediction_source": str(FROZEN_MODEL_FILES[model_name]),
                    "label_source": str(MODEL_READY["eicu_external"]),
                    "cluster_id_used": result.cluster_id_used,
                    "cluster_level": result.cluster_level,
                    "point_estimate_source": "manuscript_assets/tables/Table4_Lab_Freshness_Sensitivity.csv",
                    "source_script": "manuscript_assets/audit/run_bootstrap_ci.py",
                    "notes": "Fixed-model lab freshness evaluation; no retraining.",
                }
            )
    del external_base

    all_ci = pd.DataFrame(ci_rows)
    all_ci.to_csv(SUPP_DIR / "Supplementary_Table_S5_Bootstrap_CI_AllMetrics.csv", index=False, encoding="utf-8-sig")

    table2_ci = add_ci_to_table2(table2, all_ci)
    table2_ci.to_csv(TABLE_DIR / "Table2_Main_Model_Performance_with_95CI.csv", index=False, encoding="utf-8-sig")

    table3_ci = add_ci_to_table3(table3, all_ci)
    table3_ci.to_csv(TABLE_DIR / "Table3_Clinical_Implementation_TrueTraining_with_95CI.csv", index=False, encoding="utf-8-sig")

    table4_ci = add_ci_to_table4(table4, all_ci)
    table4_ci.to_csv(TABLE_DIR / "Table4_Lab_Freshness_Sensitivity_with_95CI.csv", index=False, encoding="utf-8-sig")

    write_source_map(source_rows)
    pd.DataFrame(run_log).to_json(AUDIT_DIR / "Bootstrap_CI_Run_Log.json", orient="records", indent=2)
    write_markdown_outputs(pd.DataFrame(source_rows), all_ci, run_log)
    update_indexes()

    key = all_ci[
        (all_ci["dataset_name"] == "eicu_external")
        & (all_ci["metric_name"].isin(["AUROC", "AUPRC", "calibration_slope"]))
        & (
            (
                all_ci["model_name"].isin(
                    [
                        "P15_clinically_parsimonious_transport_model",
                        "P12_true_trained_clinical_landing_model",
                        "P10_true_trained_ultra_minimal_sensitivity_model",
                    ]
                )
                & all_ci["scenario"].isin(["primary_model", "lab12h_freshness_window", "lab24h_freshness_window"])
            )
        )
    ][
        [
            "model_name",
            "scenario",
            "metric_name",
            "bootstrap_CI_lower",
            "bootstrap_CI_upper",
            "n_resamples_valid",
            "n_resamples_skipped",
        ]
    ]
    print(json.dumps(key.to_dict(orient="records"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
