from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "parsimonious_features"
STEP7 = ROOT / "step7_main_modeling" / "output"
TRAIN_PATH = STEP7 / "Model_Ready_Train.parquet"
TEST_PATH = STEP7 / "Model_Ready_Test_All.parquet"
EXTERNAL_PATH = STEP7 / "Model_Ready_eICU_External.parquet"

TARGET_COL = "event_type_24h"
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
CLASS_ORDER = np.array([DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL], dtype=object)
RANDOM_SEED = 42


CONTEXT = [
    "hours_since_icu_admission",
    "hours_from_anchor",
    "is_sepsis_on_admission",
]

SUPPORT_PROXY = [
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
    "support_proxy_component_count",
]

MT1_PHYSIOLOGY = [
    "hr_latest_value",
    "hr_slope_6h",
    "rr_latest_value",
    "spo2_latest_value",
    "creatinine_latest_value",
    "creatinine_relative_rise_from_24h_min",
    "bun_latest_value",
    "platelet_latest_value",
    "platelet_relative_drop_24h",
    "wbc_latest_value",
    "antibiotics_active_current",
    "culture_flag_current",
]

MINIMAL_RECENCY = [
    "creatinine_hours_since_last_real_measurement",
    "platelet_hours_since_last_real_measurement",
    "wbc_hours_since_last_real_measurement",
    "fio2_hours_since_last_real_measurement",
]

F15_FEATURES = [
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

F25_FEATURES = F15_FEATURES + [
    "hr_slope_6h",
    "creatinine_relative_rise_from_24h_min",
    "platelet_relative_drop_24h",
    "antibiotics_active_current",
    "culture_flag_current",
    "support_proxy_component_count",
    "creatinine_hours_since_last_real_measurement",
    "platelet_hours_since_last_real_measurement",
    "wbc_hours_since_last_real_measurement",
    "fio2_hours_since_last_real_measurement",
]

F40_FEATURES = F25_FEATURES + [
    "map_latest_value",
    "map_deficit",
    "map_below_65_burden_24h",
    "shock_index",
    "temperature_latest_value",
    "fio2_latest_value",
    "spo2_fio2_ratio",
    "lactate_latest_value",
    "lactate_slope_6h",
    "lactate_gt2_burden_24h",
    "oliguria_burden_24h",
    "urine_output_latest_value",
    "high_fio2_burden_24h",
    "low_spo2_burden_24h",
    "bilirubin_total_latest_value",
]

MT3_FEATURES = CONTEXT + MT1_PHYSIOLOGY + SUPPORT_PROXY

FEATURE_SETS = {
    "F15_minimal_bedside_set": F15_FEATURES,
    "F25_clinical_core_set": F25_FEATURES,
    "F40_balanced_transport_set": F40_FEATURES,
    "MT3_full_transport_set": MT3_FEATURES,
}

MODEL_NAMES = {
    "F15_minimal_bedside_set": "P15_minimal_bedside_model",
    "F25_clinical_core_set": "P25_clinical_core_model",
    "F40_balanced_transport_set": "P40_balanced_transport_model",
    "MT3_full_transport_set": "MT3_full_transport_set",
}

LAB_FEATURES = {
    "creatinine_latest_value",
    "bun_latest_value",
    "platelet_latest_value",
    "wbc_latest_value",
    "lactate_latest_value",
    "bilirubin_total_latest_value",
}

ADVANCED_ENGINEERING_PATTERNS = (
    "slope",
    "burden",
    "relative",
    "proxy",
    "component",
    "hours_since_last",
    "transition",
)


@dataclass
class ModelResult:
    feature_set: str
    model_name: str
    feature_count: int
    best_c: float
    temperature: float
    validation_metrics: dict[str, float]
    internal_metrics: dict[str, float]
    external_metrics: dict[str, float]
    coefficient_importance: pd.DataFrame


def ensure_inputs() -> None:
    missing = [p for p in [TRAIN_PATH, TEST_PATH, EXTERNAL_PATH] if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required model-ready parquet(s): " + ", ".join(str(p) for p in missing))
    OUTDIR.mkdir(parents=True, exist_ok=True)


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """Recreate the frozen MT3 shared support proxy from cross-database physiology components."""
    id_cols = [c for c in ["database_source", "patient_id", "stay_id", "t_pred", "chart_hour"] if c in df.columns]
    out = df[id_cols].copy()
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

    out["support_hemodynamic_component"] = pd.concat([map_deficit_norm, map_burden_norm], axis=1).mean(axis=1)
    out["support_lactate_component"] = pd.concat([lactate_2, lactate_4], axis=1).mean(axis=1)
    out["support_renal_component"] = pd.concat([oliguria, renal_worse], axis=1).mean(axis=1)
    out["support_respiratory_component"] = pd.concat([high_fio2, low_spo2, vent_transition], axis=1).mean(axis=1)
    component_cols = [
        "support_hemodynamic_component",
        "support_lactate_component",
        "support_renal_component",
        "support_respiratory_component",
    ]
    out["support_proxy_component_count"] = out[component_cols].notna().sum(axis=1)
    out["shared_support_intensity_proxy"] = out[component_cols].mean(axis=1)
    return out


def add_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    proxy = build_support_proxy(df)
    key_cols = ["stay_id", "t_pred"]
    proxy_cols = key_cols + SUPPORT_PROXY
    return df.merge(proxy[proxy_cols], on=key_cols, how="left", validate="many_to_one")


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
    n = len(probs)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(y_binary[mask].mean()) - float(probs[mask].mean()))
    return float(ece)


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    one_hot = np.zeros_like(probs)
    class_to_pos = {label: idx for idx, label in enumerate(classes)}
    for row_idx, label in enumerate(y_true):
        one_hot[row_idx, class_to_pos[label]] = 1.0
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
        "multiclass_brier": multiclass_brier(y_true, probs, classes),
        "death_brier": float(np.mean((y_death - death_probs) ** 2)),
        "calibration_intercept_death": intercept,
        "calibration_slope_death": slope,
        "ece_death": expected_calibration_error(y_death, death_probs),
    }


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


def predict_proba_with_temperature(pipe: Pipeline, df: pd.DataFrame, features: list[str], temperature: float) -> np.ndarray:
    logits = pipe.decision_function(df[features])
    return softmax(logits / temperature)


def coefficient_importance(pipe: Pipeline, features: list[str], model_name: str) -> pd.DataFrame:
    clf = pipe.named_steps["classifier"]
    classes = clf.classes_
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    coef = np.asarray(clf.coef_[death_idx], dtype=float)
    out = pd.DataFrame(
        {
            "model_name": model_name,
            "feature": features,
            "death_class_coefficient": coef,
            "abs_death_class_coefficient": np.abs(coef),
        }
    )
    out["importance_rank"] = out["abs_death_class_coefficient"].rank(method="dense", ascending=False).astype(int)
    return out.sort_values(["importance_rank", "feature"])


def fit_model(
    feature_set: str,
    model_name: str,
    features: list[str],
    train_inner: pd.DataFrame,
    validation: pd.DataFrame,
    internal: pd.DataFrame,
    external: pd.DataFrame,
) -> ModelResult:
    y_train = train_inner[TARGET_COL].to_numpy()
    y_val = validation[TARGET_COL].to_numpy()
    best_bundle = None
    best_score = None
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
    temperature = float(best_bundle["temperature"])
    internal_probs = predict_proba_with_temperature(pipe, internal, features, temperature)
    external_probs = predict_proba_with_temperature(pipe, external, features, temperature)
    internal_metrics = compute_metrics(internal[TARGET_COL].to_numpy(), internal_probs, classes)
    external_metrics = compute_metrics(external[TARGET_COL].to_numpy(), external_probs, classes)
    importance = coefficient_importance(pipe, features, model_name)

    with (OUTDIR / f"model_{model_name}.pkl").open("wb") as handle:
        pickle.dump(
            {
                "feature_set": feature_set,
                "model_name": model_name,
                "features": features,
                "best_c": float(best_bundle["best_c"]),
                "temperature": temperature,
                "classes": list(classes),
                "pipeline": pipe,
                "validation_metrics": best_bundle["validation_metrics"],
                "internal_metrics": internal_metrics,
                "external_metrics": external_metrics,
            },
            handle,
        )

    return ModelResult(
        feature_set=feature_set,
        model_name=model_name,
        feature_count=len(features),
        best_c=float(best_bundle["best_c"]),
        temperature=temperature,
        validation_metrics=best_bundle["validation_metrics"],
        internal_metrics=internal_metrics,
        external_metrics=external_metrics,
        coefficient_importance=importance,
    )


def verify_features(frames: Iterable[pd.DataFrame]) -> None:
    required = sorted(set(sum(FEATURE_SETS.values(), [])) | {TARGET_COL, "internal_split"})
    problems = []
    for feature in required:
        if feature == "internal_split":
            continue
        if any(feature not in df.columns for df in frames):
            problems.append(feature)
    if problems:
        raise ValueError("Feature(s) missing from at least one required table: " + ", ".join(problems))


def feature_set_csv(feature_set: str, features: list[str], train_df: pd.DataFrame, external_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in features:
        rows.append(
            {
                "feature_set": feature_set,
                "feature": feature,
                "feature_order": len(rows) + 1,
                "mimic_missing_rate": float(train_df[feature].isna().mean()),
                "eicu_missing_rate": float(external_df[feature].isna().mean()),
                "clinical_domain": clinical_domain(feature),
                "clinical_interpretability": interpretability_grade(feature),
            }
        )
    return pd.DataFrame(rows)


def clinical_domain(feature: str) -> str:
    lower = feature.lower()
    if feature in CONTEXT:
        return "time_anchor"
    if "support" in lower:
        return "support_intensity_proxy"
    if any(x in lower for x in ["hr", "map", "shock", "temperature"]):
        return "circulation_vitals"
    if any(x in lower for x in ["rr", "spo2", "fio2", "ventilation", "pao2"]):
        return "respiration"
    if any(x in lower for x in ["creatinine", "bun", "urine", "oliguria", "renal"]):
        return "renal"
    if any(x in lower for x in ["platelet", "wbc", "bilirubin", "lactate"]):
        return "lab_organ_function"
    if any(x in lower for x in ["antibiotic", "culture"]):
        return "infection_evidence"
    return "other"


def interpretability_grade(feature: str) -> str:
    lower = feature.lower()
    if any(pattern in lower for pattern in ["measure_count", "is_forward_filled", "phenotype", "vis"]):
        return "not_allowed_for_parsimonious_transport"
    if any(pattern in lower for pattern in ADVANCED_ENGINEERING_PATTERNS):
        return "derived_but_clinically_named"
    return "direct_or_bedside"


def feature_counts_for_clinical_use(features: list[str]) -> dict[str, int | bool]:
    required_labs = len([f for f in features if f in LAB_FEATURES or "lactate" in f or "bilirubin" in f])
    requires_advanced = any(
        ("hours_since_last" in f or "relative" in f or "slope" in f or "burden" in f or "transition" in f)
        for f in features
    )
    return {
        "feature_count": len(features),
        "required_labs_count": required_labs,
        "bedside_only_possible_flag": bool(required_labs == 0),
        "requires_advanced_drug_dose_flag": False,
        "requires_complex_engineering_flag": bool(requires_advanced),
    }


def result_rows(results: list[ModelResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        clinical_counts = feature_counts_for_clinical_use(FEATURE_SETS[result.feature_set])
        for dataset_name, metrics in [
            ("mimic_internal", result.internal_metrics),
            ("eicu_external", result.external_metrics),
        ]:
            rows.append(
                {
                    "feature_set": result.feature_set,
                    "model_name": result.model_name,
                    "dataset_name": dataset_name,
                    "best_c": result.best_c,
                    "temperature": result.temperature,
                    **clinical_counts,
                    **metrics,
                }
            )
    table = pd.DataFrame(rows)
    internal = table.loc[
        table["dataset_name"] == "mimic_internal",
        ["model_name", "auroc_death_ovr", "auprc_death"],
    ].rename(columns={"auroc_death_ovr": "internal_auroc", "auprc_death": "internal_auprc"})
    external = table.loc[
        table["dataset_name"] == "eicu_external",
        ["model_name", "auroc_death_ovr", "auprc_death"],
    ].rename(columns={"auroc_death_ovr": "external_auroc", "auprc_death": "external_auprc"})
    drops = internal.merge(external, on="model_name")
    drops["internal_external_auroc_drop"] = drops["internal_auroc"] - drops["external_auroc"]
    drops["internal_external_auprc_drop"] = drops["internal_auprc"] - drops["external_auprc"]
    drops["external_internal_auroc_ratio"] = drops["external_auroc"] / drops["internal_auroc"]
    drops["external_internal_auprc_ratio"] = drops["external_auprc"] / drops["internal_auprc"]
    return table.merge(
        drops[
            [
                "model_name",
                "internal_external_auroc_drop",
                "internal_external_auprc_drop",
                "external_internal_auroc_ratio",
                "external_internal_auprc_ratio",
            ]
        ],
        on="model_name",
        how="left",
    )


def noninferiority(comparison: pd.DataFrame) -> pd.DataFrame:
    external = comparison[comparison["dataset_name"] == "eicu_external"].copy()
    mt3 = external.loc[external["feature_set"] == "MT3_full_transport_set"].iloc[0]
    rows = []
    for _, row in external.iterrows():
        auroc_drop = float(mt3["auroc_death_ovr"] - row["auroc_death_ovr"])
        auprc_drop_abs = float(mt3["auprc_death"] - row["auprc_death"])
        auprc_drop_pct = float(auprc_drop_abs / mt3["auprc_death"]) if mt3["auprc_death"] else np.nan
        slope = float(row["calibration_slope_death"])
        if auprc_drop_pct <= 0.10:
            auprc_status = "acceptable"
        elif auprc_drop_pct <= 0.20:
            auprc_status = "borderline_acceptable"
        else:
            auprc_status = "not_recommended"
        if auroc_drop <= 0.03:
            auroc_status = "acceptable"
        elif auroc_drop <= 0.05:
            auroc_status = "borderline_acceptable"
        else:
            auroc_status = "not_recommended"
        if 0.8 <= slope <= 1.2:
            slope_status = "ideal"
        elif 0.6 <= slope < 0.8:
            slope_status = "acceptable_recalibration_needed"
        else:
            slope_status = "not_recommended"
        overall = "acceptable"
        if "not_recommended" in [auprc_status, auroc_status, slope_status]:
            overall = "not_recommended"
        elif "borderline_acceptable" in [auprc_status, auroc_status] or "acceptable_recalibration_needed" == slope_status:
            overall = "borderline_acceptable"
        rows.append(
            {
                "feature_set": row["feature_set"],
                "model_name": row["model_name"],
                "feature_count": int(row["feature_count"]),
                "external_auroc": row["auroc_death_ovr"],
                "external_auprc": row["auprc_death"],
                "external_calibration_slope": slope,
                "mt3_external_auroc": mt3["auroc_death_ovr"],
                "mt3_external_auprc": mt3["auprc_death"],
                "auroc_drop_vs_mt3": auroc_drop,
                "auprc_drop_vs_mt3_abs": auprc_drop_abs,
                "auprc_drop_vs_mt3_pct": auprc_drop_pct,
                "auroc_status": auroc_status,
                "auprc_status": auprc_status,
                "calibration_slope_status": slope_status,
                "overall_acceptability": overall,
            }
        )
    return pd.DataFrame(rows)


def build_rationale(
    feature_tables: dict[str, pd.DataFrame],
    comparison: pd.DataFrame,
    importance: pd.DataFrame,
) -> pd.DataFrame:
    union_features = sorted(set().union(*[set(df["feature"]) for df in feature_tables.values()]))
    external = comparison[comparison["dataset_name"] == "eicu_external"].copy()
    rows = []
    for feature in union_features:
        included_sets = [name for name, df in feature_tables.items() if feature in set(df["feature"])]
        miss_mimic = float(np.nanmean([df.loc[df["feature"] == feature, "mimic_missing_rate"].iloc[0] for df in feature_tables.values() if feature in set(df["feature"])]))
        miss_eicu = float(np.nanmean([df.loc[df["feature"] == feature, "eicu_missing_rate"].iloc[0] for df in feature_tables.values() if feature in set(df["feature"])]))
        imp_rows = importance[importance["feature"] == feature]
        if imp_rows.empty:
            imp_reason = "not in fitted candidate models"
        else:
            best_rank = int(imp_rows["importance_rank"].min())
            best_model = str(imp_rows.sort_values("importance_rank").iloc[0]["model_name"])
            imp_reason = f"regularized death-class coefficient rank {best_rank} in {best_model}; used as auxiliary only"
        domain = clinical_domain(feature)
        rows.append(
            {
                "feature": feature,
                "included_feature_sets": ";".join(included_sets),
                "mimic_missing_rate": miss_mimic,
                "eicu_missing_rate": miss_eicu,
                "clinical_reason": clinical_reason(feature, domain),
                "transportability_reason": transportability_reason(feature, miss_mimic, miss_eicu),
                "model_importance_reason": imp_reason,
                "final_decision": final_decision(feature, included_sets, external),
            }
        )
    return pd.DataFrame(rows)


def clinical_reason(feature: str, domain: str) -> str:
    if domain == "time_anchor":
        return "captures ICU/sepsis timing without changing the existing dual-anchor label framework"
    if domain == "support_intensity_proxy":
        return "summarizes clinically interpretable circulatory, lactate, renal, and respiratory support burden without full VIS"
    if domain == "circulation_vitals":
        return "bedside hemodynamic or perfusion marker familiar to ICU clinicians"
    if domain == "respiration":
        return "respiratory status/support marker relevant to acute deterioration"
    if domain == "renal":
        return "renal function or urine-output marker linked to organ dysfunction"
    if domain == "lab_organ_function":
        return "routine laboratory or organ-function marker with direct clinical interpretation"
    if domain == "infection_evidence":
        return "limited infection-context marker already present in the competing-risk feature layer"
    return "clinically named transport candidate"


def transportability_reason(feature: str, mimic_missing: float, eicu_missing: float) -> str:
    if eicu_missing < 0.25 and mimic_missing < 0.25:
        return "available with low missingness in both MIMIC and eICU"
    if eicu_missing < 0.60:
        return "available in both databases with moderate missingness; retained only when clinically justified"
    return "high external missingness; only retained if needed for balanced transport comparison"


def final_decision(feature: str, included_sets: list[str], external: pd.DataFrame) -> str:
    if "F15_minimal_bedside_set" in included_sets:
        return "retain in minimal/core/balanced candidate"
    if "F25_clinical_core_set" in included_sets:
        return "retain in clinical core candidate"
    if "F40_balanced_transport_set" in included_sets:
        return "retain in balanced candidate only"
    if "MT3_full_transport_set" in included_sets:
        return "retain only as MT3 reference"
    return "not retained"


def write_reports(
    feature_tables: dict[str, pd.DataFrame],
    comparison: pd.DataFrame,
    assessment: pd.DataFrame,
    rationale: pd.DataFrame,
) -> None:
    for feature_set, table in feature_tables.items():
        if feature_set.startswith("F15"):
            table.to_csv(OUTDIR / "F15_minimal_bedside_set.csv", index=False, encoding="utf-8-sig")
        elif feature_set.startswith("F25"):
            table.to_csv(OUTDIR / "F25_clinical_core_set.csv", index=False, encoding="utf-8-sig")
        elif feature_set.startswith("F40"):
            table.to_csv(OUTDIR / "F40_balanced_transport_set.csv", index=False, encoding="utf-8-sig")

    comparison.to_csv(OUTDIR / "Parsimonious_Model_Comparison.csv", index=False, encoding="utf-8-sig")
    assessment.to_csv(OUTDIR / "Noninferiority_Assessment.csv", index=False, encoding="utf-8-sig")
    rationale.to_csv(OUTDIR / "Feature_Retention_Rationale.csv", index=False, encoding="utf-8-sig")

    external = comparison[comparison["dataset_name"] == "eicu_external"].copy()
    rec = choose_recommendation(assessment)
    rec_row = external[external["feature_set"] == rec["recommended_feature_set"]].iloc[0]
    mt3_row = external[external["feature_set"] == "MT3_full_transport_set"].iloc[0]

    (OUTDIR / "Feature_Retention_Report.md").write_text(
        "# Feature Retention Report\n\n"
        "This audit combines clinical interpretability, MIMIC/eICU availability, and regularized model coefficient ranks. "
        "Coefficient ranks were used only as supporting evidence, not as a mechanical feature selector.\n\n"
        f"- Candidate feature count: F15={len(F15_FEATURES)}, F25={len(F25_FEATURES)}, F40={len(F40_FEATURES)}, MT3={len(MT3_FEATURES)}.\n"
        "- Excluded by design: phenotype label, measurement-intensity variables, full VIS, and non-transportable high-dimensional derivatives.\n"
        "- Existing cohort, dual-anchor logic, Sepsis-3 suspected infection layer, and 24h competing-risk label were not modified.\n",
        encoding="utf-8",
    )

    comparison_md = [
        "# Parsimonious Model Report",
        "",
        "Training source: MIMIC train_inner only. Validation tuning: MIMIC validation only. External validation: eICU only.",
        "All models output three competing-risk classes and use the same labels and split as the existing MT3 repair workflow.",
        "",
        "| feature_set | n | eICU AUROC | eICU AUPRC | eICU slope | status vs MT3 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for _, row in assessment.sort_values("feature_count").iterrows():
        comparison_md.append(
            f"| {row['feature_set']} | {int(row['feature_count'])} | {row['external_auroc']:.4f} | "
            f"{row['external_auprc']:.4f} | {row['external_calibration_slope']:.4f} | {row['overall_acceptability']} |"
        )
    (OUTDIR / "Parsimonious_Model_Report.md").write_text("\n".join(comparison_md) + "\n", encoding="utf-8")

    (OUTDIR / "Final_Parsimonious_Model_Recommendation.md").write_text(
        "# Final Parsimonious Model Recommendation\n\n"
        f"- Recommended clinical landing model: `{rec['recommended_model_name']}`.\n"
        f"- Recommended feature set: `{rec['recommended_feature_set']}` ({int(rec_row['feature_count'])} features).\n"
        f"- eICU AUROC/AUPRC/slope: {rec_row['auroc_death_ovr']:.4f} / {rec_row['auprc_death']:.4f} / {rec_row['calibration_slope_death']:.4f}.\n"
        f"- MT3 reference eICU AUROC/AUPRC/slope: {mt3_row['auroc_death_ovr']:.4f} / {mt3_row['auprc_death']:.4f} / {mt3_row['calibration_slope_death']:.4f}.\n"
        f"- AUPRC drop vs MT3: {rec['auprc_drop_vs_mt3_pct']:.2%}.\n"
        f"- Main-text replacement recommendation: {rec['replace_mt3_as_main']}.\n"
        f"- Reason: {rec['reason']}.\n\n"
        "MT3 should remain as the performance upper-bound reference unless the selected parsimonious model is accepted as the main clinical model.\n",
        encoding="utf-8",
    )

    (OUTDIR / "Manuscript_Update_Notes.md").write_text(
        "# Manuscript Update Notes\n\n"
        "- Do not rewrite the cohort, anchor, or label methods.\n"
        "- Add a clinical parsimony experiment that compares F15, F25, F40, and MT3 under the same MIMIC-training/eICU-external-validation design.\n"
        f"- The recommended parsimonious model is `{rec['recommended_model_name']}` with {int(rec_row['feature_count'])} features.\n"
        "- Use feature-count reduction and retained bedside/core organ-function variables to answer clinical implementability concerns.\n"
        "- Keep phenotype as stratification/interpretation only and keep MT3 as a performance upper-bound reference if parsimony costs are material.\n",
        encoding="utf-8",
    )


def choose_recommendation(assessment: pd.DataFrame) -> dict[str, object]:
    candidates = assessment[assessment["feature_set"] != "MT3_full_transport_set"].copy()
    acceptable = candidates[candidates["overall_acceptability"].isin(["acceptable", "borderline_acceptable"])].copy()
    if not acceptable.empty:
        acceptable["rank_status"] = acceptable["overall_acceptability"].map({"acceptable": 0, "borderline_acceptable": 1})
        chosen = acceptable.sort_values(["rank_status", "feature_count", "auprc_drop_vs_mt3_pct"]).iloc[0]
        replace = bool(chosen["overall_acceptability"] == "acceptable")
        reason = (
            "accepted by noninferiority thresholds with the smallest feature count"
            if replace
            else "borderline acceptable; suitable for clinical sensitivity rather than direct replacement"
        )
    else:
        chosen = assessment[assessment["feature_set"] == "MT3_full_transport_set"].iloc[0]
        replace = False
        reason = "all parsimonious candidates exceeded predefined external performance or calibration loss thresholds"
    return {
        "recommended_feature_set": chosen["feature_set"],
        "recommended_model_name": chosen["model_name"],
        "feature_count": int(chosen["feature_count"]),
        "auprc_drop_vs_mt3_pct": float(chosen["auprc_drop_vs_mt3_pct"]),
        "replace_mt3_as_main": replace,
        "reason": reason,
    }


def main() -> None:
    ensure_inputs()
    train_all = pd.read_parquet(TRAIN_PATH)
    internal = pd.read_parquet(TEST_PATH)
    external = pd.read_parquet(EXTERNAL_PATH)
    train_all = add_support_proxy(train_all)
    internal = add_support_proxy(internal)
    external = add_support_proxy(external)
    verify_features([train_all, internal, external])

    train_inner = train_all.loc[train_all["internal_split"] == "train_inner"].copy()
    validation = train_all.loc[train_all["internal_split"] == "validation"].copy()

    feature_tables = {
        feature_set: feature_set_csv(feature_set, features, train_inner, external)
        for feature_set, features in FEATURE_SETS.items()
    }

    results: list[ModelResult] = []
    for feature_set, features in FEATURE_SETS.items():
        model_name = MODEL_NAMES[feature_set]
        print(f"[{datetime.now().isoformat(timespec='seconds')}] Training {model_name} ({len(features)} features)")
        result = fit_model(feature_set, model_name, features, train_inner, validation, internal, external)
        results.append(result)
        print(
            f"  eICU AUROC={result.external_metrics['auroc_death_ovr']:.4f}, "
            f"AUPRC={result.external_metrics['auprc_death']:.4f}, "
            f"slope={result.external_metrics['calibration_slope_death']:.4f}"
        )

    importance = pd.concat([r.coefficient_importance.assign(feature_set=r.feature_set) for r in results], ignore_index=True)
    importance.to_csv(OUTDIR / "Parsimonious_Model_Coefficient_Importance.csv", index=False, encoding="utf-8-sig")

    comparison = result_rows(results)
    assessment = noninferiority(comparison)
    rationale = build_rationale(feature_tables, comparison, importance)
    write_reports(feature_tables, comparison, assessment, rationale)

    recommendation = choose_recommendation(assessment)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "train_rows": int(len(train_inner)),
        "validation_rows": int(len(validation)),
        "mimic_internal_rows": int(len(internal)),
        "eicu_external_rows": int(len(external)),
        "trained_models": [r.model_name for r in results],
        "recommendation": recommendation,
        "forbidden_changes": {
            "modified_step1_to_6": False,
            "used_eicu_for_training": False,
            "used_phenotype_default_input": False,
            "used_measurement_intensity": False,
            "used_full_vis_external_transport": False,
        },
    }
    (OUTDIR / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nRecommendation")
    print(json.dumps(recommendation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
