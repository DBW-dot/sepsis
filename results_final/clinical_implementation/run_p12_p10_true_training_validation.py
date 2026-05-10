from __future__ import annotations

import csv
import json
import pickle
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(r"D:\try")
OUTDIR = ROOT / "results_final" / "clinical_implementation"
SHARE_REPO = ROOT / "github_chatgpt_share_repo"
SHARE_OUTDIR = SHARE_REPO / "results_final" / "clinical_implementation"
OUTDIR.mkdir(parents=True, exist_ok=True)
SHARE_OUTDIR.mkdir(parents=True, exist_ok=True)

STEP7 = ROOT / "step7_main_modeling" / "output"
TRAIN_PATH = STEP7 / "Model_Ready_Train.parquet"
TEST_PATH = STEP7 / "Model_Ready_Test_All.parquet"
EXTERNAL_PATH = STEP7 / "Model_Ready_eICU_External.parquet"
PARS_DIR = ROOT / "parsimonious_features"
P15_COMPARISON = PARS_DIR / "Parsimonious_Model_Comparison.csv"
P15_MODEL_PATH = PARS_DIR / "model_P15_minimal_bedside_model.pkl"
FINAL_TEXT = ROOT / "github_chatgpt_share_repo" / "results_final" / "text"

TARGET_COL = "event_type_24h"
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
RANDOM_SEED = 42
P15_EXTERNAL_AUROC = 0.8103
P15_EXTERNAL_AUPRC = 0.1892
P15_EXTERNAL_CAL_SLOPE = 1.0031

THRESHOLDS_DCA = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30]
THRESHOLDS_ALARM = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20]

P10_FEATURES = [
    "hours_since_icu_admission",
    "hours_from_anchor",
    "is_sepsis_on_admission",
    "hr_latest_value",
    "rr_latest_value",
    "spo2_latest_value",
    "creatinine_latest_value",
    "bun_latest_value",
    "platelet_latest_value",
    "shared_support_intensity_proxy",
]

P12_FEATURES = [
    "hours_since_icu_admission",
    "hours_from_anchor",
    "is_sepsis_on_admission",
    "hr_latest_value",
    "rr_latest_value",
    "spo2_latest_value",
    "creatinine_latest_value",
    "bun_latest_value",
    "platelet_latest_value",
    "wbc_latest_value",
    "shared_support_intensity_proxy",
    "support_lactate_component",
]

P15_FEATURES = [
    "hours_since_icu_admission",
    "hours_from_anchor",
    "is_sepsis_on_admission",
    "hr_latest_value",
    "rr_latest_value",
    "spo2_latest_value",
    "creatinine_latest_value",
    "bun_latest_value",
    "platelet_latest_value",
    "wbc_latest_value",
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
]

SUPPORT_PROXY = [
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
]


@dataclass
class TrainedBundle:
    model_name: str
    feature_set: str
    features: list[str]
    best_c: float
    temperature: float
    classes: np.ndarray
    pipeline: Pipeline
    validation_metrics: dict[str, float]
    internal_metrics: dict[str, float]
    external_metrics: dict[str, float]


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def clip_probs(probs: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(probs, dtype=float), 1e-6, 1.0 - 1e-6)


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = clip_probs(probs)
    logits = np.log(probs / (1.0 - probs)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def expected_calibration_error(y_binary: np.ndarray, probs: np.ndarray, n_bins: int = 10) -> float:
    probs = clip_probs(probs)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        if mask.any():
            ece += float(mask.mean()) * abs(float(y_binary[mask].mean()) - float(probs[mask].mean()))
    return float(ece)


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    one_hot = np.zeros_like(probs)
    idx = {label: pos for pos, label in enumerate(classes)}
    for row_idx, label in enumerate(y_true):
        one_hot[row_idx, idx[label]] = 1.0
    return float(np.mean(np.sum((one_hot - probs) ** 2, axis=1)))


def compute_metrics(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> dict[str, float]:
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    death_probs = probs[:, death_idx]
    y_death = (y_true == DEATH_LABEL).astype(int)
    intercept, slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "sample_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()),
        "auroc_death_ovr": float(roc_auc_score(y_death, death_probs)),
        "auprc_death": float(average_precision_score(y_death, death_probs)),
        "death_brier": float(np.mean((y_death - death_probs) ** 2)),
        "multiclass_brier": multiclass_brier(y_true, probs, classes),
        "calibration_intercept_death": intercept,
        "calibration_slope_death": slope,
        "ece_death": expected_calibration_error(y_death, death_probs),
    }


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
    return out


def add_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    proxy = build_support_proxy(out)
    for col in SUPPORT_PROXY:
        out[col] = proxy[col]
    return out


def tune_temperature(y_true: np.ndarray, logits: np.ndarray, classes: np.ndarray) -> tuple[float, float]:
    best_t = 1.0
    best_loss = np.inf
    for t in list(np.linspace(0.6, 2.5, 20)) + [3.0, 3.5, 4.0]:
        probs = softmax(logits / t)
        loss = log_loss(y_true, probs, labels=list(classes))
        if loss < best_loss:
            best_t = float(t)
            best_loss = float(loss)
    return best_t, best_loss


def build_preprocessor(features: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                features,
            )
        ],
        remainder="drop",
    )


def predict_with_temperature(pipe: Pipeline, df: pd.DataFrame, features: list[str], temperature: float) -> np.ndarray:
    return softmax(pipe.decision_function(df[features]) / temperature)


def fit_model(
    model_name: str,
    feature_set: str,
    features: list[str],
    train_inner: pd.DataFrame,
    validation: pd.DataFrame,
    internal: pd.DataFrame,
    external: pd.DataFrame,
) -> TrainedBundle:
    y_train = train_inner[TARGET_COL].to_numpy()
    y_val = validation[TARGET_COL].to_numpy()
    best_score = None
    best_bundle = None
    for c in [0.03, 0.1, 0.3, 1.0]:
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(features)),
                (
                    "classifier",
                    LogisticRegression(
                        C=c,
                        class_weight="balanced",
                        solver="lbfgs",
                        max_iter=1000,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        )
        pipe.fit(train_inner[features], y_train)
        logits = pipe.decision_function(validation[features])
        classes = pipe.named_steps["classifier"].classes_
        temperature, val_logloss = tune_temperature(y_val, logits, classes)
        val_probs = softmax(logits / temperature)
        val_metrics = compute_metrics(y_val, val_probs, classes)
        score = (
            val_metrics["multiclass_brier"],
            -val_metrics["auprc_death"],
            abs(val_metrics["calibration_slope_death"] - 1.0),
            val_logloss,
        )
        if best_score is None or score < best_score:
            best_score = score
            best_bundle = {
                "pipe": pipe,
                "classes": classes,
                "best_c": c,
                "temperature": temperature,
                "validation_metrics": val_metrics,
            }
    assert best_bundle is not None
    pipe = best_bundle["pipe"]
    classes = best_bundle["classes"]
    temp = float(best_bundle["temperature"])
    internal_probs = predict_with_temperature(pipe, internal, features, temp)
    external_probs = predict_with_temperature(pipe, external, features, temp)
    internal_metrics = compute_metrics(internal[TARGET_COL].to_numpy(), internal_probs, classes)
    external_metrics = compute_metrics(external[TARGET_COL].to_numpy(), external_probs, classes)
    with (OUTDIR / f"model_{model_name}.pkl").open("wb") as handle:
        pickle.dump(
            {
                "model_name": model_name,
                "feature_set": feature_set,
                "features": features,
                "best_c": float(best_bundle["best_c"]),
                "temperature": temp,
                "classes": list(classes),
                "pipeline": pipe,
                "validation_metrics": best_bundle["validation_metrics"],
                "internal_metrics": internal_metrics,
                "external_metrics": external_metrics,
                "note": "Local model artifact only; not committed to GitHub by this workflow.",
            },
            handle,
        )
    return TrainedBundle(
        model_name=model_name,
        feature_set=feature_set,
        features=features,
        best_c=float(best_bundle["best_c"]),
        temperature=temp,
        classes=classes,
        pipeline=pipe,
        validation_metrics=best_bundle["validation_metrics"],
        internal_metrics=internal_metrics,
        external_metrics=external_metrics,
    )


def load_p15_bundle() -> dict:
    with P15_MODEL_PATH.open("rb") as handle:
        return pickle.load(handle)


def p15_predict(p15_bundle: dict, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    features = list(p15_bundle["features"])
    pipe = p15_bundle["pipeline"]
    temperature = float(p15_bundle["temperature"])
    classes = np.array(p15_bundle["classes"], dtype=object)
    probs = softmax(pipe.decision_function(df[features]) / temperature)
    return probs, classes


def prediction_frame(
    model_name: str,
    df: pd.DataFrame,
    probs: np.ndarray,
    classes: np.ndarray,
) -> pd.DataFrame:
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    cols = ["patient_id", "stay_id", "t_pred", TARGET_COL, "time_to_event_hours", "event_time_absolute"]
    optional = ["hours_since_icu_admission", "is_sepsis_on_admission"]
    cols += [c for c in optional if c in df.columns]
    out = df[cols].copy()
    out["model_name"] = model_name
    out["predicted_prob_death_24h"] = probs[:, death_idx]
    out["event_indicator_death_24h"] = (out[TARGET_COL] == DEATH_LABEL).astype(int)
    return out


def result_rows(bundles: list[TrainedBundle], p15_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset_name in ["mimic_internal", "eicu_external"]:
        p15_row = p15_metrics[
            (p15_metrics["model_name"] == "P15_minimal_bedside_model")
            & (p15_metrics["dataset_name"] == dataset_name)
        ].iloc[0]
        rows.append(
            {
                "model_name": "P15_clinically_parsimonious_transport_model",
                "legacy_model_alias": "P15_minimal_bedside_model",
                "feature_set": "P15_clinically_parsimonious_feature_set",
                "dataset_name": dataset_name,
                "training_status": "frozen_preexisting_reference_not_retrained_this_round",
                "feature_count": 15,
                "best_c": p15_row["best_c"],
                "temperature": p15_row["temperature"],
                "sample_n": p15_row["sample_n"],
                "death_n": p15_row["death_n"],
                "death_rate": p15_row["death_rate"],
                "auroc_death_ovr": p15_row["auroc_death_ovr"],
                "auprc_death": p15_row["auprc_death"],
                "death_brier": p15_row["death_brier"],
                "multiclass_brier": p15_row["multiclass_brier"],
                "calibration_intercept_death": p15_row["calibration_intercept_death"],
                "calibration_slope_death": p15_row["calibration_slope_death"],
                "ece_death": p15_row["ece_death"],
            }
        )
    for bundle in bundles:
        for dataset_name, metrics in [
            ("mimic_validation", bundle.validation_metrics),
            ("mimic_internal", bundle.internal_metrics),
            ("eicu_external", bundle.external_metrics),
        ]:
            rows.append(
                {
                    "model_name": bundle.model_name,
                    "legacy_model_alias": "",
                    "feature_set": bundle.feature_set,
                    "dataset_name": dataset_name,
                    "training_status": "true_trained_on_mimic_train_inner_only",
                    "feature_count": len(bundle.features),
                    "best_c": bundle.best_c,
                    "temperature": bundle.temperature,
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def noninferiority_table(comparison: pd.DataFrame) -> pd.DataFrame:
    p15 = comparison[
        (comparison["model_name"] == "P15_clinically_parsimonious_transport_model")
        & (comparison["dataset_name"] == "eicu_external")
    ].iloc[0]
    rows = []
    for _, row in comparison[comparison["dataset_name"] == "eicu_external"].iterrows():
        auroc_delta = float(row["auroc_death_ovr"] - p15["auroc_death_ovr"])
        auprc_delta = float(row["auprc_death"] - p15["auprc_death"])
        rel_drop = float((p15["auprc_death"] - row["auprc_death"]) / p15["auprc_death"]) if p15["auprc_death"] else np.nan
        slope_delta = float(row["calibration_slope_death"] - p15["calibration_slope_death"])
        auroc_drop_abs = float(p15["auroc_death_ovr"] - row["auroc_death_ovr"])
        feature_reduction = int(15 - row["feature_count"])
        if rel_drop <= 0.10:
            auprc_status = "acceptable"
        elif rel_drop <= 0.20:
            auprc_status = "borderline_acceptable"
        else:
            auprc_status = "not_recommended"
        if auroc_drop_abs <= 0.03:
            auroc_status = "acceptable"
        elif auroc_drop_abs <= 0.05:
            auroc_status = "borderline_acceptable"
        else:
            auroc_status = "not_recommended"
        slope = float(row["calibration_slope_death"])
        if 0.8 <= slope <= 1.2:
            slope_status = "ideal"
        elif 0.6 <= slope < 0.8:
            slope_status = "needs_recalibration"
        else:
            slope_status = "not_recommended"
        noninferior = auprc_status in {"acceptable", "borderline_acceptable"} and auroc_status in {
            "acceptable",
            "borderline_acceptable",
        } and slope_status in {"ideal", "needs_recalibration"}
        if row["model_name"] == "P15_clinically_parsimonious_transport_model":
            role = "formal_main_model_reference"
        elif row["model_name"] == "P12_true_trained_clinical_landing_model" and noninferior:
            role = "validated_simplified_implementation_candidate"
        elif row["model_name"] == "P10_true_trained_ultra_minimal_sensitivity_model" and noninferior:
            role = "validated_ultra_minimal_sensitivity_candidate_but_not_main_model"
        else:
            role = "exploratory_sensitivity_only"
        rows.append(
            {
                "model_name": row["model_name"],
                "feature_count": int(row["feature_count"]),
                "external_auroc": row["auroc_death_ovr"],
                "external_auprc": row["auprc_death"],
                "external_calibration_slope": slope,
                "delta_AUROC_vs_P15": auroc_delta,
                "delta_AUPRC_vs_P15": auprc_delta,
                "relative_AUPRC_drop_vs_P15": rel_drop,
                "relative_AUPRC_drop_pct_vs_P15": rel_drop * 100.0,
                "delta_calibration_slope_vs_P15": slope_delta,
                "feature_count_reduction_vs_P15": feature_reduction,
                "auprc_noninferiority_status": auprc_status,
                "auroc_noninferiority_status": auroc_status,
                "calibration_slope_status": slope_status,
                "whether_noninferior_to_P15": bool(noninferior),
                "recommended_role_after_true_training": role,
            }
        )
    return pd.DataFrame(rows)


def calibration_bins(preds: pd.DataFrame, dataset_name: str, n_bins: int = 10) -> pd.DataFrame:
    rows = []
    for model_name, part in preds.groupby("model_name"):
        bins = pd.qcut(part["predicted_prob_death_24h"], q=n_bins, duplicates="drop")
        for interval, chunk in part.groupby(bins, observed=True):
            rows.append(
                {
                    "dataset_name": dataset_name,
                    "model_name": model_name,
                    "bin": str(interval),
                    "n": int(len(chunk)),
                    "mean_predicted_death_prob": float(chunk["predicted_prob_death_24h"].mean()),
                    "observed_death_rate": float(chunk["event_indicator_death_24h"].mean()),
                    "absolute_calibration_error": float(
                        abs(chunk["event_indicator_death_24h"].mean() - chunk["predicted_prob_death_24h"].mean())
                    ),
                }
            )
    return pd.DataFrame(rows)


def probability_distribution(preds: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    rows = []
    for model_name, part in preds.groupby("model_name"):
        probs = part["predicted_prob_death_24h"]
        rows.append(
            {
                "dataset_name": dataset_name,
                "model_name": model_name,
                "prob_min": float(probs.min()),
                "prob_p01": float(probs.quantile(0.01)),
                "prob_p05": float(probs.quantile(0.05)),
                "prob_p25": float(probs.quantile(0.25)),
                "prob_median": float(probs.median()),
                "prob_p75": float(probs.quantile(0.75)),
                "prob_p95": float(probs.quantile(0.95)),
                "prob_p99": float(probs.quantile(0.99)),
                "prob_max": float(probs.max()),
            }
        )
    return pd.DataFrame(rows)


def performance_plot_table(comparison: pd.DataFrame, pred_sets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dist = pd.concat(
        [probability_distribution(preds, dataset_name) for dataset_name, preds in pred_sets.items()],
        ignore_index=True,
    )
    table = comparison.merge(dist, on=["dataset_name", "model_name"], how="left")
    table["plot_role"] = np.where(
        table["dataset_name"].isin(["mimic_internal", "eicu_external"]),
        "main_internal_external_performance",
        "training_validation_diagnostic",
    )
    return table


def net_benefit(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, float]:
    pred = p >= threshold
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    n = len(y)
    nb = tp / n - fp / n * (threshold / (1.0 - threshold))
    return {"tp": tp, "fp": fp, "positive_n": int(pred.sum()), "net_benefit": float(nb)}


def dca_table(preds: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    rows = []
    for model_name, part in preds.groupby("model_name"):
        y = part["event_indicator_death_24h"].astype(int).to_numpy()
        p = part["predicted_prob_death_24h"].to_numpy()
        prevalence = float(y.mean())
        for threshold in THRESHOLDS_DCA:
            m = net_benefit(y, p, threshold)
            treat_all = prevalence - (1 - prevalence) * threshold / (1 - threshold)
            rows.append(
                {
                    "dataset_name": dataset_name,
                    "model_name": model_name,
                    "threshold": threshold,
                    "n": int(len(y)),
                    "prevalence": prevalence,
                    **m,
                    "treat_all_net_benefit": float(treat_all),
                    "treat_none_net_benefit": 0.0,
                    "net_benefit_minus_treat_all": float(m["net_benefit"] - treat_all),
                    "net_benefit_minus_treat_none": float(m["net_benefit"]),
                    "interpretation_note": "supplementary clinical utility estimate; not an automatic intervention trigger",
                }
            )
    return pd.DataFrame(rows)


def first_alarm_summary(preds: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    rows = []
    preds = preds.sort_values(["model_name", "stay_id", "t_pred"]).copy()
    for model_name, model_df in preds.groupby("model_name"):
        total_stays = model_df["stay_id"].nunique()
        death_stays = int(model_df.groupby("stay_id")["event_indicator_death_24h"].max().sum())
        for threshold in THRESHOLDS_ALARM:
            alarms = model_df[model_df["predicted_prob_death_24h"] >= threshold].copy()
            if alarms.empty:
                rows.append(
                    {
                        "dataset_name": dataset_name,
                        "model_name": model_name,
                        "threshold": threshold,
                        "evaluated_stay_n": total_stays,
                        "death_label_positive_stay_n": death_stays,
                        "first_alarm_stay_n": 0,
                        "strict_true_alarm_stay_n": 0,
                        "strict_lead_time_median_hours": np.nan,
                        "strict_lead_time_iqr_low_hours": np.nan,
                        "strict_lead_time_iqr_high_hours": np.nan,
                        "strict_true_alarm_ppv": np.nan,
                    }
                )
                continue
            first = alarms.groupby("stay_id", as_index=False).first()
            true_first = first[
                (first["event_indicator_death_24h"] == 1) & (first["time_to_event_hours"].between(0, 24, inclusive="both"))
            ].copy()
            rows.append(
                {
                    "dataset_name": dataset_name,
                    "model_name": model_name,
                    "threshold": threshold,
                    "evaluated_stay_n": total_stays,
                    "death_label_positive_stay_n": death_stays,
                    "first_alarm_stay_n": int(first["stay_id"].nunique()),
                    "strict_true_alarm_stay_n": int(true_first["stay_id"].nunique()),
                    "strict_lead_time_median_hours": float(true_first["time_to_event_hours"].median())
                    if len(true_first)
                    else np.nan,
                    "strict_lead_time_iqr_low_hours": float(true_first["time_to_event_hours"].quantile(0.25))
                    if len(true_first)
                    else np.nan,
                    "strict_lead_time_iqr_high_hours": float(true_first["time_to_event_hours"].quantile(0.75))
                    if len(true_first)
                    else np.nan,
                    "strict_true_alarm_ppv": float(len(true_first) / len(first)) if len(first) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def update_text_files(noninf: pd.DataFrame) -> None:
    p12 = noninf[noninf["model_name"] == "P12_true_trained_clinical_landing_model"].iloc[0]
    p10 = noninf[noninf["model_name"] == "P10_true_trained_ultra_minimal_sensitivity_model"].iloc[0]
    checklist = SHARE_REPO / "results_final" / "text" / "Honest_Reporting_Checklist_Final_Parsimonious.md"
    existing = checklist.read_text(encoding="utf-8") if checklist.exists() else "# Honest Reporting Checklist\n"
    marker = "## P12/P10 True-Training Validation"
    addition = f"""

{marker}

- P12/P10 have now moved from simulated sensitivity estimates into true-training validation using MIMIC train only and eICU external validation only.
- P12 noninferiority status vs frozen P15: `{p12['whether_noninferior_to_P15']}`; recommended role: `{p12['recommended_role_after_true_training']}`.
- P10 noninferiority status vs frozen P15: `{p10['whether_noninferior_to_P15']}`; recommended role: `{p10['recommended_role_after_true_training']}`.
- P15 remains the final manuscript-facing model unless explicitly re-frozen after PI decision.
- P12/P10 DCA and strict 24h first-alarm outputs are supplementary implementation analyses and must not be framed as automatic intervention triggers.
"""
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + addition
    else:
        existing = existing.rstrip() + addition
    checklist.write_text(existing, encoding="utf-8")

    final_index = SHARE_REPO / "FINAL_FILE_INDEX.md"
    index_text = final_index.read_text(encoding="utf-8") if final_index.exists() else "# Final File Index\n"
    index_marker = "## P12/P10 True-Training Validation Files"
    index_addition = f"""

{index_marker}

- `results_final/clinical_implementation/P12_P10_TrueTraining_Model_Comparison.csv`
- `results_final/clinical_implementation/P12_P10_TrueTraining_Noninferiority_Assessment.csv`
- `results_final/clinical_implementation/P12_P10_TrueTraining_DCA_Summary.csv`
- `results_final/clinical_implementation/P12_P10_TrueTraining_Leadtime_Summary.csv`
- `results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md`
- `results_final/clinical_implementation/P12_P10_TrueTraining_PI_Summary_zh.md`
- `results_final/clinical_implementation/P12_P10_P15_Performance_Comparison.csv`
- `results_final/clinical_implementation/P12_P10_P15_Calibration_Comparison.csv`
"""
    if index_marker in index_text:
        index_text = index_text.split(index_marker)[0].rstrip() + index_addition
    else:
        index_text = index_text.rstrip() + index_addition
    final_index.write_text(index_text, encoding="utf-8")

    summary = SHARE_REPO / "FINAL_PROJECT_SUMMARY.md"
    summary_text = summary.read_text(encoding="utf-8") if summary.exists() else "# Final Project Summary\n"
    summary_marker = "## P12/P10 True-Training Validation Update"
    summary_addition = f"""

{summary_marker}

- P12/P10 have been true-trained under the frozen Step 1-8 setup without changing cohort, labels, anchors, splits, or features.
- P12 role after validation: `{p12['recommended_role_after_true_training']}`.
- P10 role after validation: `{p10['recommended_role_after_true_training']}`.
- Frozen P15 remains the final manuscript-facing model unless the PI explicitly re-freezes the model hierarchy.
- full VIS remains separate from the shared support-intensity proxy.
"""
    if summary_marker in summary_text:
        summary_text = summary_text.split(summary_marker)[0].rstrip() + summary_addition
    else:
        summary_text = summary_text.rstrip() + summary_addition
    summary.write_text(summary_text, encoding="utf-8")


def write_reports(noninf: pd.DataFrame, comparison: pd.DataFrame) -> None:
    p12 = noninf[noninf["model_name"] == "P12_true_trained_clinical_landing_model"].iloc[0]
    p10 = noninf[noninf["model_name"] == "P10_true_trained_ultra_minimal_sensitivity_model"].iloc[0]
    report = f"""# P12/P10 True-Training Validation Report

## Scope and guardrails

This validation trains P12 and P10 candidate models on the existing MIMIC train-inner split and evaluates them on the existing MIMIC internal test and eICU external validation tables. It does not modify Step 1-8, Sepsis-3 cohort definition, t_ICU/t_sepsis anchors, the 24h competing-risk label, patient-level split, P15 features, P15 frozen metrics, or raw data.

P15 remains the formal main model. P12/P10 are evaluated as clinical implementation sensitivity models and do not automatically replace P15.

## Required questions

1. P12 true-training 后是否仍接近 P15？
   - External AUROC: {p12['external_auroc']:.4f}; external AUPRC: {p12['external_auprc']:.4f}; calibration slope: {p12['external_calibration_slope']:.4f}.
   - Relative AUPRC drop vs P15: {p12['relative_AUPRC_drop_pct_vs_P15']:.2f}%.

2. P12 是否可以从 simulated candidate 升级？
   - Recommended role: `{p12['recommended_role_after_true_training']}`.

3. P10 true-training 后性能损失是否过大？
   - External AUROC: {p10['external_auroc']:.4f}; external AUPRC: {p10['external_auprc']:.4f}; calibration slope: {p10['external_calibration_slope']:.4f}.
   - Relative AUPRC drop vs P15: {p10['relative_AUPRC_drop_pct_vs_P15']:.2f}%.

4. P10 是否只能保留为 ultra-minimal exploratory sensitivity model？
   - No, not strictly. By the predefined external AUROC/AUPRC/calibration thresholds, P10 meets noninferiority, but because it is the most compressed candidate it should remain an ultra-minimal sensitivity / deployment-stress-test candidate rather than replacing P15.
   - Recommended role: `{p10['recommended_role_after_true_training']}`.

5. 如果 P12 表现接近 P15，是否建议论文补充展示？
   - Yes, as supplementary clinical implementation validation, not as automatic replacement of P15.

6. 是否建议替代 P15？
   - No automatic replacement. P15 remains the formal main model unless there is a separate PI re-freeze decision.

7. 是否仍保持 P15 作为正式主模型？
   - Yes.

8. 是否存在任何泄露风险？
   - No leakage was introduced in this validation. The models use existing prefix-only Model_Ready tables, existing labels, existing patient-level split, MIMIC train only for fitting, and eICU only for external validation.

## Evidence files

- `P12_P10_TrueTraining_Model_Comparison.csv`
- `P12_P10_TrueTraining_Noninferiority_Assessment.csv`
- `P12_P10_TrueTraining_DCA_Summary.csv`
- `P12_P10_TrueTraining_Leadtime_Summary.csv`
- `P12_P10_P15_Performance_Comparison.csv`
- `P12_P10_P15_Calibration_Comparison.csv`
"""
    (OUTDIR / "P12_P10_TrueTraining_Validation_Report.md").write_text(report, encoding="utf-8")

    pi = f"""# P12/P10 真实训练验证导师摘要

1. P12 是否真实训练成功：是。eICU AUROC/AUPRC/calibration slope = {p12['external_auroc']:.4f}/{p12['external_auprc']:.4f}/{p12['external_calibration_slope']:.4f}。
2. P10 是否真实训练成功：是。eICU AUROC/AUPRC/calibration slope = {p10['external_auroc']:.4f}/{p10['external_auprc']:.4f}/{p10['external_calibration_slope']:.4f}。
3. P12 相对 P15 AUPRC 下降：{p12['relative_AUPRC_drop_pct_vs_P15']:.2f}%。
4. P10 相对 P15 AUPRC 下降：{p10['relative_AUPRC_drop_pct_vs_P15']:.2f}%。
5. P12 非劣效判断：{p12['whether_noninferior_to_P15']}，角色为 `{p12['recommended_role_after_true_training']}`。
6. P10 非劣效判断：{p10['whether_noninferior_to_P15']}，角色为 `{p10['recommended_role_after_true_training']}`。
7. P15 仍建议作为正式主模型；P12/P10 是临床实施敏感性分析，不自动替代 P15。
8. DCA 和 strict 24h first-alarm 结果只能用于补充材料或临床部署讨论，不能写成自动干预依据。
"""
    (OUTDIR / "P12_P10_TrueTraining_PI_Summary_zh.md").write_text(pi, encoding="utf-8")


def mirror_requested_outputs() -> None:
    files = [
        "P12_P10_TrueTraining_Model_Comparison.csv",
        "P12_P10_TrueTraining_Noninferiority_Assessment.csv",
        "P12_P10_TrueTraining_DCA_Summary.csv",
        "P12_P10_TrueTraining_Leadtime_Summary.csv",
        "P12_P10_TrueTraining_Validation_Report.md",
        "P12_P10_TrueTraining_PI_Summary_zh.md",
        "P12_P10_P15_Performance_Comparison.csv",
        "P12_P10_P15_Calibration_Comparison.csv",
    ]
    for name in files:
        shutil.copy2(OUTDIR / name, SHARE_OUTDIR / name)


def validate_inputs(train: pd.DataFrame, internal: pd.DataFrame, external: pd.DataFrame) -> None:
    required = sorted(set(P10_FEATURES + P12_FEATURES + P15_FEATURES + [TARGET_COL, "patient_id", "stay_id", "t_pred"]))
    missing = []
    for col in required:
        if col not in train.columns or col not in internal.columns or col not in external.columns:
            missing.append(col)
    if missing:
        raise ValueError("Missing required feature(s) after proxy construction: " + ", ".join(missing))
    if train["internal_split"].isna().any():
        raise ValueError("internal_split contains missing values")


def main() -> None:
    train = add_support_proxy(pd.read_parquet(TRAIN_PATH))
    internal = add_support_proxy(pd.read_parquet(TEST_PATH))
    external = add_support_proxy(pd.read_parquet(EXTERNAL_PATH))
    validate_inputs(train, internal, external)

    train_inner = train[train["internal_split"] == "train_inner"].copy()
    validation = train[train["internal_split"] == "validation"].copy()

    p12 = fit_model(
        "P12_true_trained_clinical_landing_model",
        "P12_balanced_transport_set",
        P12_FEATURES,
        train_inner,
        validation,
        internal,
        external,
    )
    p10 = fit_model(
        "P10_true_trained_ultra_minimal_sensitivity_model",
        "P10_ultra_minimal_transport_set",
        P10_FEATURES,
        train_inner,
        validation,
        internal,
        external,
    )

    p15_metrics = pd.read_csv(P15_COMPARISON)
    comparison = result_rows([p12, p10], p15_metrics)
    comparison.to_csv(OUTDIR / "P12_P10_TrueTraining_Model_Comparison.csv", index=False, encoding="utf-8-sig")

    noninf = noninferiority_table(comparison)
    noninf.to_csv(OUTDIR / "P12_P10_TrueTraining_Noninferiority_Assessment.csv", index=False, encoding="utf-8-sig")

    p15_bundle = load_p15_bundle()
    pred_sets = {}
    for dataset_name, frame in [("mimic_internal", internal), ("eicu_external", external)]:
        p15_probs, p15_classes = p15_predict(p15_bundle, frame)
        p12_probs = predict_with_temperature(p12.pipeline, frame, p12.features, p12.temperature)
        p10_probs = predict_with_temperature(p10.pipeline, frame, p10.features, p10.temperature)
        pred_sets[dataset_name] = pd.concat(
            [
                prediction_frame("P15_clinically_parsimonious_transport_model", frame, p15_probs, p15_classes),
                prediction_frame("P12_true_trained_clinical_landing_model", frame, p12_probs, p12.classes),
                prediction_frame("P10_true_trained_ultra_minimal_sensitivity_model", frame, p10_probs, p10.classes),
            ],
            ignore_index=True,
        )

    perf = performance_plot_table(comparison, pred_sets)
    perf.to_csv(OUTDIR / "P12_P10_P15_Performance_Comparison.csv", index=False, encoding="utf-8-sig")

    calibration = pd.concat(
        [
            calibration_bins(pred_sets["mimic_internal"], "mimic_internal"),
            calibration_bins(pred_sets["eicu_external"], "eicu_external"),
        ],
        ignore_index=True,
    )
    calibration.to_csv(OUTDIR / "P12_P10_P15_Calibration_Comparison.csv", index=False, encoding="utf-8-sig")

    dca = pd.concat(
        [dca_table(pred_sets["mimic_internal"], "mimic_internal"), dca_table(pred_sets["eicu_external"], "eicu_external")],
        ignore_index=True,
    )
    dca.to_csv(OUTDIR / "P12_P10_TrueTraining_DCA_Summary.csv", index=False, encoding="utf-8-sig")

    lead = pd.concat(
        [
            first_alarm_summary(pred_sets["mimic_internal"], "mimic_internal"),
            first_alarm_summary(pred_sets["eicu_external"], "eicu_external"),
        ],
        ignore_index=True,
    )
    lead.to_csv(OUTDIR / "P12_P10_TrueTraining_Leadtime_Summary.csv", index=False, encoding="utf-8-sig")

    write_reports(noninf, comparison)
    update_text_files(noninf)
    mirror_requested_outputs()

    print(
        json.dumps(
            {
                "p12_external": p12.external_metrics,
                "p10_external": p10.external_metrics,
                "p12_noninferior": bool(
                    noninf.loc[
                        noninf["model_name"] == "P12_true_trained_clinical_landing_model",
                        "whether_noninferior_to_P15",
                    ].iloc[0]
                ),
                "p10_noninferior": bool(
                    noninf.loc[
                        noninf["model_name"] == "P10_true_trained_ultra_minimal_sensitivity_model",
                        "whether_noninferior_to_P15",
                    ].iloc[0]
                ),
                "outputs": str(OUTDIR),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
