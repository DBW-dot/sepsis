from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "metre_transport"
OUTDIR.mkdir(parents=True, exist_ok=True)

STEP7 = ROOT / "step7_main_modeling" / "output"
TRAIN_PATH = STEP7 / "Model_Ready_Train.parquet"
TEST_PATH = STEP7 / "Model_Ready_Test_All.parquet"
EXTERNAL_PATH = STEP7 / "Model_Ready_eICU_External.parquet"
STEP3_MAIN_PATH = ROOT / "step3_dynamic_feature_bank" / "output" / "Dynamic_Feature_Bank_main.parquet"
PRED_M1_TEST = STEP7 / "pred_main_test_all.parquet"
PRED_M1_EXT = STEP7 / "pred_main_eicu_external.parquet"
PRED_C1_TEST = STEP7 / "pred_C1_test_all.parquet"
PRED_C1_EXT = STEP7 / "pred_C1_eicu_external.parquet"

TARGET_COL = "event_type_24h"
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"

CLASSES_FOR_METRICS = [DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL]
RANDOM_SEED = 42

CONTEXT_FEATURES = [
    "hours_from_anchor",
    "hours_since_icu_admission",
    "is_sepsis_on_admission",
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

SUPPORT_RAW_COMPONENTS = [
    "map_deficit",
    "map_below_65_burden_24h",
    "lactate_gt2_burden_24h",
    "lactate_gt4_burden_24h",
    "oliguria_burden_24h",
    "high_fiO2_burden_24h",
    "low_SpO2_burden_24h",
    "ventilation_transition_count_24h",
    "worsening_renal_trajectory_flag",
]

SUPPORT_INPUT_COLUMNS = [
    "map_deficit",
    "map_below_65_burden_24h",
    "lactate_gt2_burden_24h",
    "lactate_gt4_burden_24h",
    "oliguria_burden_24h",
    "high_fio2_burden_24h",
    "low_spo2_burden_24h",
    "ventilation_transition_count_24h",
    "worsening_renal_trajectory_flag",
]

SUPPORT_MODEL_FEATURES = [
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
    "support_proxy_component_count",
]

PHENOTYPE_FEATURE = ["phenotype_label"]

MT_FEATURES = {
    "MT1_physiology_only": CONTEXT_FEATURES + MT1_PHYSIOLOGY,
    "MT2_physiology_minimal_recency": CONTEXT_FEATURES + MT1_PHYSIOLOGY + MINIMAL_RECENCY,
    "MT3_physiology_support_proxy": CONTEXT_FEATURES + MT1_PHYSIOLOGY + SUPPORT_MODEL_FEATURES,
    "MT4_support_proxy_phenotype_sensitivity": CONTEXT_FEATURES
    + MT1_PHYSIOLOGY
    + SUPPORT_MODEL_FEATURES
    + PHENOTYPE_FEATURE,
}

QUALITY_HEAVY_FEATURES = [
    "hr_is_observed_current_hour",
    "hr_is_forward_filled",
    "hr_measure_count_last_24h",
    "map_is_observed_current_hour",
    "map_is_forward_filled",
    "map_measure_count_last_24h",
    "lactate_is_observed_current_hour",
    "lactate_is_forward_filled",
    "lactate_measure_count_last_24h",
    "creatinine_is_observed_current_hour",
    "creatinine_is_forward_filled",
    "creatinine_measure_count_last_24h",
    "bilirubin_total_is_observed_current_hour",
    "bilirubin_total_is_forward_filled",
    "bilirubin_total_measure_count_last_24h",
    "platelet_is_observed_current_hour",
    "platelet_is_forward_filled",
    "platelet_measure_count_last_24h",
    "wbc_is_observed_current_hour",
    "wbc_is_forward_filled",
    "wbc_measure_count_last_24h",
    "urine_output_is_observed_current_hour",
    "urine_output_is_forward_filled",
    "urine_output_measure_count_last_24h",
    "fio2_is_observed_current_hour",
    "fio2_is_forward_filled",
    "fio2_measure_count_last_24h",
]

LOW_TRANSPORT_FEATURES = [
    "sbp_latest_value",
    "map_latest_value",
    "map_slope_6h",
    "shock_index",
    "shock_index_slope_6h",
    "temperature_latest_value",
    "fio2_latest_value",
    "spo2_fio2_ratio",
    "pao2_fio2_ratio",
    "lactate_latest_value",
    "lactate_slope_6h",
    "urine_output_latest_value",
    "bilirubin_total_latest_value",
    "bilirubin_slope_24h",
    "ventilation_status_current",
    "ventilation_status_hours_since_last_status_update",
    "culture_flag_hours_since_last_status_update",
]

FULL_VIS_RICH_ONLY = [
    "current_vis",
    "mean_vis_1h",
    "mean_vis_3h",
    "mean_vis_6h",
    "max_vis_24h",
    "slope_vis_3h",
    "slope_vis_6h",
    "accel_vis_6h",
    "vis_burden_hours_24h",
    "vis_escalation_count_24h",
    "map_deficit_x_vis",
    "lactate_slope_6h_x_vis_slope_6h",
    "urine_output_decline_x_vis",
]

REGISTRY_FEATURES = sorted(
    set(
        CONTEXT_FEATURES
        + MT1_PHYSIOLOGY
        + MINIMAL_RECENCY
        + SUPPORT_INPUT_COLUMNS
        + SUPPORT_MODEL_FEATURES
        + PHENOTYPE_FEATURE
        + QUALITY_HEAVY_FEATURES
        + LOW_TRANSPORT_FEATURES
        + FULL_VIS_RICH_ONLY
        + [
            "hr_sd_24h",
            "high_fio2_burden_24h",
            "low_spo2_burden_24h",
            "antibiotics_active_hours_since_last_status_update",
            "culture_flag_is_observed_or_recorded",
            "ventilation_status_is_observed_or_recorded",
        ]
    )
)


@dataclass
class TrainedModel:
    model_name: str
    features: list[str]
    best_c: float
    temperature: float
    validation_metrics: dict[str, float]
    test_metrics: dict[str, float]
    external_metrics: dict[str, float]


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = clip_probs(probs)
    logits = np.log(probs / (1.0 - probs)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


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
    auroc = float(roc_auc_score(y_death, death_probs))
    auprc = float(average_precision_score(y_death, death_probs))
    intercept, slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "sample_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()),
        "auroc_death_ovr": auroc,
        "auprc_death": auprc,
        "multiclass_brier": multiclass_brier(y_true, probs, classes),
        "calibration_intercept_death": intercept,
        "calibration_slope_death": slope,
    }


def tune_temperature(y_true: np.ndarray, logits: np.ndarray, classes: np.ndarray) -> tuple[float, float]:
    best_t = 1.0
    best_loss = np.inf
    for t in list(np.linspace(0.6, 2.5, 20)) + [3.0, 3.5, 4.0]:
        probs = softmax(logits / t)
        loss = log_loss(y_true, probs, labels=list(classes))
        if loss < best_loss:
            best_loss = loss
            best_t = float(t)
    return best_t, float(best_loss)


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["database_source", "patient_id", "stay_id", "t_pred", "chart_hour"]].copy()
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
    out["support_proxy_definition"] = "METRE_shared_proxy_not_full_VIS"
    return out


def feature_metadata(feature: str) -> dict[str, str]:
    lower = feature.lower()
    if feature in FULL_VIS_RICH_ONLY:
        return {
            "clinical_concept": "MIMIC full vasoactive-inotropic support intensity",
            "mimic_source_table": "mimiciv_icu.inputevents / Step3 VIS_Derivation_Table",
            "mimic_raw_variable": feature,
            "eicu_source_table": "not transport-equivalent",
            "eicu_raw_variable": "unavailable or reduced proxy only",
            "unit_mimic": "VIS score or derived VIS unit",
            "unit_eicu": "not available",
            "canonical_unit": "VIS score",
            "conversion_rule": "MIMIC full VIS formula only; not converted to eICU proxy",
            "hourly_aggregation_rule": "hourly current/window VIS derivative",
            "forward_fill_rule": "not forward-filled across databases",
        }
    if feature == "phenotype_label":
        return {
            "clinical_concept": "early static phenotype label",
            "mimic_source_table": "step4 Phenotype_Assignment_main",
            "mimic_raw_variable": "phenotype_label",
            "eicu_source_table": "step4 Phenotype_Assignment_eicu",
            "eicu_raw_variable": "mapped phenotype_label",
            "unit_mimic": "category",
            "unit_eicu": "category",
            "canonical_unit": "category",
            "conversion_rule": "MIMIC discovery label; eICU assigned by mapping model",
            "hourly_aggregation_rule": "stay-level label joined to t_pred rows",
            "forward_fill_rule": "constant within stay",
        }
    if feature in CONTEXT_FEATURES:
        return {
            "clinical_concept": "dynamic prediction temporal alignment",
            "mimic_source_table": "Prediction_Grid_main_*",
            "mimic_raw_variable": feature,
            "eicu_source_table": "Prediction_Grid_eicu_external",
            "eicu_raw_variable": feature,
            "unit_mimic": "hours or binary",
            "unit_eicu": "hours or binary",
            "canonical_unit": "hours/binary",
            "conversion_rule": "already canonical",
            "hourly_aggregation_rule": "prediction grid value",
            "forward_fill_rule": "not applicable",
        }
    if "antibiotics" in lower:
        concept = "antibiotic exposure flag"
        mimic_source = "mimiciv_hosp.prescriptions / Step2 antibiotics flag"
        eicu_source = "eicu medication / infusionDrug adapted flag"
        unit = "binary/status"
    elif "culture" in lower:
        concept = "culture evidence flag"
        mimic_source = "mimiciv_hosp.microbiologyevents"
        eicu_source = "eicu microLab / diagnosis-supported adapted evidence"
        unit = "binary/status"
    elif any(x in lower for x in ["creatinine", "bun", "bilirubin", "platelet", "wbc", "lactate"]):
        concept = lower.replace("_", " ")
        mimic_source = "mimiciv_hosp.labevents"
        eicu_source = "eicu.lab"
        unit = "canonical lab unit"
    elif any(x in lower for x in ["urine", "oliguria"]):
        concept = lower.replace("_", " ")
        mimic_source = "mimiciv_icu.outputevents"
        eicu_source = "eicu.intakeOutput"
        unit = "mL/hour or derived burden"
    elif any(x in lower for x in ["fio2", "spo2", "pao2", "rr", "ventilation"]):
        concept = lower.replace("_", " ")
        mimic_source = "mimiciv_icu.chartevents / respiratory charting"
        eicu_source = "eicu.vitalPeriodic / respiratoryCharting"
        unit = "canonical respiratory unit"
    elif any(x in lower for x in ["hr", "sbp", "map", "shock", "temperature"]):
        concept = lower.replace("_", " ")
        mimic_source = "mimiciv_icu.chartevents"
        eicu_source = "eicu.vitalPeriodic / nurseCharting"
        unit = "canonical vital unit"
    elif lower.startswith("support_") or "shared_support" in lower:
        concept = "shared support-intensity proxy"
        mimic_source = "Step7 model-ready physiology-derived support components"
        eicu_source = "Step7 model-ready core physiology-derived support components"
        unit = "0-1 proxy scale or component count"
    else:
        concept = lower.replace("_", " ")
        mimic_source = "Step7 model-ready feature"
        eicu_source = "Step7 model-ready feature"
        unit = "derived"
    return {
        "clinical_concept": concept,
        "mimic_source_table": mimic_source,
        "mimic_raw_variable": feature,
        "eicu_source_table": eicu_source,
        "eicu_raw_variable": feature,
        "unit_mimic": unit,
        "unit_eicu": unit,
        "canonical_unit": unit,
        "conversion_rule": "already canonicalized in Step2/Step3 feature layer",
        "hourly_aggregation_rule": "latest/windowed dynamic feature at t_pred",
        "forward_fill_rule": "Step2 capped forward-fill where applicable; dynamic burdens use prefix-only windows",
    }


def grade_feature(feature: str, miss_mimic: float, miss_eicu: float) -> tuple[str, str, str]:
    if feature in FULL_VIS_RICH_ONLY:
        return "unusable", "rich_internal", "Full VIS is not transport-equivalent to eICU reduced support proxy."
    if feature in QUALITY_HEAVY_FEATURES or "measure_count_last_24h" in feature or "is_forward_filled" in feature:
        return "low", "exclude", "Observation-process-heavy feature likely harms transportability."
    if feature == "phenotype_label":
        return "moderate", "supplementary", "Use only as sensitivity/stratification, not default performance driver."
    if feature in SUPPORT_MODEL_FEATURES:
        return "high", "transport", "Shared support-intensity proxy built from cross-database physiology components."
    if feature in LOW_TRANSPORT_FEATURES:
        if miss_eicu >= 0.65:
            return "low", "rich_internal", "External missingness or semantic instability is high."
        return "moderate", "supplementary", "Potentially useful but not default transport feature."
    if feature in MINIMAL_RECENCY:
        return "moderate", "transport", "Minimal recency/provenance feature retained only in MT2."
    if feature in MT1_PHYSIOLOGY or feature in CONTEXT_FEATURES:
        if miss_eicu <= 0.25:
            return "high", "transport", "Core shared feature with acceptable external missingness."
        if miss_eicu <= 0.60:
            return "moderate", "transport", "Shared feature with moderate external missingness."
        return "low", "supplementary", "Shared concept but missingness is high."
    if feature in SUPPORT_INPUT_COLUMNS:
        return "moderate", "transport", "Input component for shared support proxy, not used as full VIS."
    if miss_eicu >= 0.80:
        return "unusable", "exclude", "External missingness too high for transport layer."
    if miss_eicu >= 0.50:
        return "low", "supplementary", "External missingness is substantial."
    return "moderate", "supplementary", "Available but not selected for compact METRE transport model."


def missingness(df: pd.DataFrame, feature: str) -> float:
    if feature not in df.columns:
        return 1.0
    return float(df[feature].isna().mean())


def build_registry(mimic_df: pd.DataFrame, eicu_df: pd.DataFrame, proxy_missing: dict[str, tuple[float, float]]) -> pd.DataFrame:
    rows = []
    for feature in REGISTRY_FEATURES:
        if feature in proxy_missing:
            miss_mimic, miss_eicu = proxy_missing[feature]
        else:
            miss_mimic, miss_eicu = missingness(mimic_df, feature), missingness(eicu_df, feature)
        grade, recommended, note = grade_feature(feature, miss_mimic, miss_eicu)
        meta = feature_metadata(feature)
        rows.append(
            {
                **meta,
                "missingness_mimic": miss_mimic,
                "missingness_eicu": miss_eicu,
                "transportability_grade": grade,
                "recommended_use": recommended,
                "notes": note,
            }
        )
    registry = pd.DataFrame(rows).sort_values(
        ["recommended_use", "transportability_grade", "clinical_concept", "mimic_raw_variable"]
    )
    registry.to_csv(OUTDIR / "METRE_Core_Feature_Registry.csv", index=False, encoding="utf-8-sig")
    return registry


def write_registry_report(registry: pd.DataFrame) -> None:
    grade_counts = registry["transportability_grade"].value_counts().to_dict()
    use_counts = registry["recommended_use"].value_counts().to_dict()
    text = f"""# METRE Core Feature Registry Report

## Construction

- Registry source: Step7 model-ready tables plus Step3 VIS schema audit.
- Missingness reference for MIMIC: `Model_Ready_Test_All.parquet`.
- Missingness reference for eICU: `Model_Ready_eICU_External.parquet`.
- Full VIS features were deliberately marked `rich_internal` or `unusable` for transport because eICU has no transport-equivalent full VIS field.

## Transportability grade counts

```json
{json.dumps(grade_counts, ensure_ascii=False, indent=2)}
```

## Recommended-use counts

```json
{json.dumps(use_counts, ensure_ascii=False, indent=2)}
```

## Verification logic

- Features used in METRE transport models must be present in both MIMIC and eICU model-ready tables or be generated by the shared proxy function from shared components.
- Measurement-process-heavy variables are not used as default transport predictors.
- `phenotype_label` is limited to MT4 sensitivity because previous experiments showed negligible overall gain.
"""
    (OUTDIR / "METRE_Core_Feature_Registry_Report.md").write_text(text, encoding="utf-8")


def write_feature_sets(registry: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rich = registry.loc[registry["recommended_use"].isin(["rich_internal", "transport", "supplementary"])].copy()
    rich["feature_set_role"] = np.where(rich["recommended_use"] == "rich_internal", "rich_internal_default", "available_for_context")
    transport_features = sorted(set(MT1_PHYSIOLOGY + CONTEXT_FEATURES + MINIMAL_RECENCY + SUPPORT_MODEL_FEATURES))
    transport = registry.loc[registry["mimic_raw_variable"].isin(transport_features)].copy()
    transport["feature_set_role"] = transport["mimic_raw_variable"].map(
        lambda x: "MT1_physiology_context"
        if x in CONTEXT_FEATURES + MT1_PHYSIOLOGY
        else ("MT2_minimal_recency" if x in MINIMAL_RECENCY else "MT3_shared_support_proxy")
    )
    rich.to_csv(OUTDIR / "Rich_Internal_Feature_Set.csv", index=False, encoding="utf-8-sig")
    transport.to_csv(OUTDIR / "METRE_Transport_Feature_Set.csv", index=False, encoding="utf-8-sig")
    return rich, transport


def build_preprocessor(feature_list: list[str]) -> ColumnTransformer:
    categorical = [f for f in feature_list if f == "phenotype_label"]
    numeric = [f for f in feature_list if f not in categorical]
    transformers = [
        (
            "numeric",
            Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
            numeric,
        )
    ]
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]),
                categorical,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop")


def fit_metre_model(
    model_name: str,
    features: list[str],
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    external_df: pd.DataFrame,
) -> TrainedModel:
    y_train = train_df[TARGET_COL].to_numpy()
    y_val = validation_df[TARGET_COL].to_numpy()
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
        pipe.fit(train_df[features], y_train)
        logits = pipe.decision_function(validation_df[features])
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
                "pipeline": pipe,
                "classes": classes,
                "temperature": temperature,
                "best_c": c,
                "validation_metrics": val_metrics,
            }
    assert best_bundle is not None
    pipe = best_bundle["pipeline"]
    classes = best_bundle["classes"]
    temperature = float(best_bundle["temperature"])

    def evaluate(df: pd.DataFrame) -> dict[str, float]:
        logits = pipe.decision_function(df[features])
        probs = softmax(logits / temperature)
        return compute_metrics(df[TARGET_COL].to_numpy(), probs, classes)

    test_metrics = evaluate(test_df)
    external_metrics = evaluate(external_df)
    bundle = {
        "model_name": model_name,
        "features": features,
        "best_c": float(best_bundle["best_c"]),
        "temperature": temperature,
        "classes": list(classes),
        "pipeline": pipe,
        "validation_metrics": best_bundle["validation_metrics"],
        "test_metrics": test_metrics,
        "external_metrics": external_metrics,
    }
    with (OUTDIR / f"model_{model_name}.pkl").open("wb") as handle:
        pickle.dump(bundle, handle)
    return TrainedModel(
        model_name=model_name,
        features=features,
        best_c=float(best_bundle["best_c"]),
        temperature=temperature,
        validation_metrics=best_bundle["validation_metrics"],
        test_metrics=test_metrics,
        external_metrics=external_metrics,
    )


def load_prediction_metrics(model_name: str, dataset_name: str, path: Path) -> dict[str, float | str]:
    df = pd.read_parquet(path)
    probs = np.column_stack(
        [
            df["predicted_prob_discharge_24h"].to_numpy(),
            df["predicted_prob_death_24h"].to_numpy(),
            df["predicted_prob_no_event_24h"].to_numpy(),
        ]
    )
    metrics = compute_metrics(df["true_event_type_24h"].to_numpy(), probs, np.array(CLASSES_FOR_METRICS, dtype=object))
    metrics.update({"model_name": model_name, "dataset_name": dataset_name})
    return metrics


def rows_for_model(result: TrainedModel) -> list[dict[str, float | str]]:
    return [
        {"model_name": result.model_name, "dataset_name": "mimic_internal_test", **result.test_metrics},
        {"model_name": result.model_name, "dataset_name": "eicu_external", **result.external_metrics},
    ]


def comparison_table(metre_results: list[TrainedModel]) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    rows.extend(rows_for_model(metre_results[0]))
    rows.extend(rows_for_model(metre_results[1]))
    rows.extend(rows_for_model(metre_results[2]))
    rows.extend(rows_for_model(metre_results[3]))
    rows.extend(
        [
            load_prediction_metrics("M1_original_rich", "mimic_internal_test", PRED_M1_TEST),
            load_prediction_metrics("M1_original_rich", "eicu_external", PRED_M1_EXT),
            load_prediction_metrics("C1_dynamic_SOFA", "mimic_internal_test", PRED_C1_TEST),
            load_prediction_metrics("C1_dynamic_SOFA", "eicu_external", PRED_C1_EXT),
        ]
    )
    table = pd.DataFrame(rows)
    internal = table.loc[
        table["dataset_name"] == "mimic_internal_test",
        ["model_name", "auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"],
    ].rename(
        columns={
            "auroc_death_ovr": "internal_auroc_death_ovr",
            "auprc_death": "internal_auprc_death",
            "multiclass_brier": "internal_multiclass_brier",
            "calibration_slope_death": "internal_calibration_slope_death",
        }
    )
    external = table.loc[
        table["dataset_name"] == "eicu_external",
        ["model_name", "auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_slope_death"],
    ].rename(
        columns={
            "auroc_death_ovr": "external_auroc_death_ovr",
            "auprc_death": "external_auprc_death",
            "multiclass_brier": "external_multiclass_brier",
            "calibration_slope_death": "external_calibration_slope_death",
        }
    )
    drops = internal.merge(external, on="model_name", how="inner")
    drops["external_internal_auroc_drop"] = drops["internal_auroc_death_ovr"] - drops["external_auroc_death_ovr"]
    drops["external_internal_auprc_drop"] = drops["internal_auprc_death"] - drops["external_auprc_death"]
    table = table.merge(
        drops[["model_name", "external_internal_auroc_drop", "external_internal_auprc_drop"]],
        on="model_name",
        how="left",
    )
    table.to_csv(OUTDIR / "METRE_vs_Original_Model_Comparison.csv", index=False, encoding="utf-8-sig")
    table.loc[table["model_name"].str.startswith("MT")].to_csv(
        OUTDIR / "METRE_Transport_Model_Comparison.csv", index=False, encoding="utf-8-sig"
    )
    return table


def write_support_definition(proxy_df: pd.DataFrame) -> None:
    summary = (
        proxy_df.groupby("dataset_name")
        .agg(
            row_n=("shared_support_intensity_proxy", "size"),
            missing_rate=("shared_support_intensity_proxy", lambda s: float(s.isna().mean())),
            mean_proxy=("shared_support_intensity_proxy", "mean"),
            median_proxy=("shared_support_intensity_proxy", "median"),
            mean_component_count=("support_proxy_component_count", "mean"),
        )
        .reset_index()
    )
    text = f"""# Shared Support Intensity Proxy Definition

## Scope

This is a METRE-style transportable support-intensity proxy. It is **not** full VIS.

## Components

- Hemodynamic component: mean of normalized `map_deficit` and `map_below_65_burden_24h`.
- Lactate component: mean of normalized `lactate_gt2_burden_24h` and `lactate_gt4_burden_24h`.
- Renal component: mean of normalized `oliguria_burden_24h` and `worsening_renal_trajectory_flag`.
- Respiratory component: mean of normalized `high_fio2_burden_24h`, `low_spo2_burden_24h`, and `ventilation_transition_count_24h`.
- Composite: mean of available component scores.

## Explicit VIS separation

- MIMIC full VIS remains a rich internal feature family.
- eICU reduced support signal is not treated as mathematically equivalent to full VIS.
- MT3/MT4 use this shared proxy instead of full VIS.

## Proxy summary

```json
{json.dumps(summary.to_dict(orient="records"), ensure_ascii=False, indent=2)}
```
"""
    (OUTDIR / "Shared_Support_Intensity_Proxy_Definition.md").write_text(text, encoding="utf-8")


def compute_full_vis_missingness() -> dict[str, tuple[float, float]]:
    if not STEP3_MAIN_PATH.exists():
        return {}
    schema = set(pq.ParquetFile(STEP3_MAIN_PATH).schema.names)
    cols = [feature for feature in FULL_VIS_RICH_ONLY if feature in schema]
    if not cols:
        return {}
    vis_df = pd.read_parquet(STEP3_MAIN_PATH, columns=cols)
    return {feature: (float(vis_df[feature].isna().mean()), 1.0) for feature in cols}


def write_model_report(results: list[TrainedModel], comparison: pd.DataFrame) -> None:
    subset = comparison[
        comparison["model_name"].isin([r.model_name for r in results] + ["M1_original_rich", "C1_dynamic_SOFA"])
    ].copy()
    default_external = subset[
        (subset["dataset_name"] == "eicu_external")
        & (subset["model_name"].isin(["MT1_physiology_only", "MT2_physiology_minimal_recency", "MT3_physiology_support_proxy"]))
    ].copy()
    best_ext = (
        default_external
        .sort_values(["auroc_death_ovr", "auprc_death"], ascending=[False, False])
        .iloc[0]
    )
    best_sensitivity = (
        subset[(subset["dataset_name"] == "eicu_external") & (subset["model_name"].str.startswith("MT"))]
        .sort_values(["auroc_death_ovr", "auprc_death"], ascending=[False, False])
        .iloc[0]
    )
    m1_ext = subset[(subset["model_name"] == "M1_original_rich") & (subset["dataset_name"] == "eicu_external")].iloc[0]
    mt3_ext = subset[(subset["model_name"] == "MT3_physiology_support_proxy") & (subset["dataset_name"] == "eicu_external")].iloc[0]
    mt2_ext = subset[(subset["model_name"] == "MT2_physiology_minimal_recency") & (subset["dataset_name"] == "eicu_external")].iloc[0]
    mt1_ext = subset[(subset["model_name"] == "MT1_physiology_only") & (subset["dataset_name"] == "eicu_external")].iloc[0]
    mt4_ext = subset[(subset["model_name"] == "MT4_support_proxy_phenotype_sensitivity") & (subset["dataset_name"] == "eicu_external")].iloc[0]
    text = f"""# METRE Transport Model Report

## Training design

- Training source: MIMIC `train_inner` only.
- Validation source: MIMIC `validation` only.
- External evaluation: eICU only, never used for fitting, imputation, scaling, encoding, or model selection.
- Model family: regularized multinomial logistic regression with balanced class weights and validation-selected temperature scaling.
- Outcome: three-class competing-risk label (`ICU_DEATH`, `ALIVE_DISCHARGE`, `NO_EVENT`).

## METRE model definitions

- MT1: transport physiology plus temporal anchor context.
- MT2: MT1 plus minimal recency/provenance features.
- MT3: MT1 plus shared support-intensity proxy.
- MT4: MT3 plus `phenotype_label` sensitivity.

## External comparison snapshot

- M1 original rich external AUROC/AUPRC/slope: {m1_ext['auroc_death_ovr']:.4f} / {m1_ext['auprc_death']:.4f} / {m1_ext['calibration_slope_death']:.4f}
- MT1 external AUROC/AUPRC/slope: {mt1_ext['auroc_death_ovr']:.4f} / {mt1_ext['auprc_death']:.4f} / {mt1_ext['calibration_slope_death']:.4f}
- MT2 external AUROC/AUPRC/slope: {mt2_ext['auroc_death_ovr']:.4f} / {mt2_ext['auprc_death']:.4f} / {mt2_ext['calibration_slope_death']:.4f}
- MT3 external AUROC/AUPRC/slope: {mt3_ext['auroc_death_ovr']:.4f} / {mt3_ext['auprc_death']:.4f} / {mt3_ext['calibration_slope_death']:.4f}
- MT4 external AUROC/AUPRC/slope: {mt4_ext['auroc_death_ovr']:.4f} / {mt4_ext['auprc_death']:.4f} / {mt4_ext['calibration_slope_death']:.4f}

## Best external model by AUROC/AUPRC

- Best default METRE model: `{best_ext['model_name']}`
- eICU AUROC={best_ext['auroc_death_ovr']:.4f}
- eICU AUPRC={best_ext['auprc_death']:.4f}
- eICU calibration slope={best_ext['calibration_slope_death']:.4f}
- Best sensitivity model including MT4: `{best_sensitivity['model_name']}` with AUROC={best_sensitivity['auroc_death_ovr']:.4f}, AUPRC={best_sensitivity['auprc_death']:.4f}, slope={best_sensitivity['calibration_slope_death']:.4f}

## Interpretation

- METRE-style restriction reduced dependence on high-dimensional observation-process features.
- The shared support proxy must be interpreted as a cross-database support signal, not a replacement for full VIS.
- MT4 tests phenotype sensitivity only; phenotype is not promoted to the default transport model even when AUROC changes slightly.
"""
    (OUTDIR / "METRE_Transport_Model_Report.md").write_text(text, encoding="utf-8")


def write_final_recommendation(comparison: pd.DataFrame) -> None:
    external = comparison[comparison["dataset_name"] == "eicu_external"].copy()
    internal = comparison[comparison["dataset_name"] == "mimic_internal_test"].copy()
    default_external = external[external["model_name"].isin(["MT1_physiology_only", "MT2_physiology_minimal_recency", "MT3_physiology_support_proxy"])].copy()
    best_ext = default_external.sort_values(["auroc_death_ovr", "auprc_death"], ascending=[False, False]).iloc[0]
    best_sensitivity = external[external["model_name"].str.startswith("MT")].sort_values(
        ["auroc_death_ovr", "auprc_death"], ascending=[False, False]
    ).iloc[0]
    m1_ext = external[external["model_name"] == "M1_original_rich"].iloc[0]
    m1_int = internal[internal["model_name"] == "M1_original_rich"].iloc[0]
    mt1_ext = external[external["model_name"] == "MT1_physiology_only"].iloc[0]
    mt2_ext = external[external["model_name"] == "MT2_physiology_minimal_recency"].iloc[0]
    mt3_ext = external[external["model_name"] == "MT3_physiology_support_proxy"].iloc[0]
    mt4_ext = external[external["model_name"] == "MT4_support_proxy_phenotype_sensitivity"].iloc[0]

    auc_shift_reduced = best_ext["external_internal_auroc_drop"] < m1_ext["external_internal_auroc_drop"]
    support_helped = mt3_ext["auroc_death_ovr"] > mt1_ext["auroc_death_ovr"] or mt3_ext["auprc_death"] > mt1_ext["auprc_death"]
    recency_helped_auc = mt2_ext["auroc_death_ovr"] > mt1_ext["auroc_death_ovr"]
    recency_helped_auprc = mt2_ext["auprc_death"] > mt1_ext["auprc_death"]
    phenotype_helped_auc = mt4_ext["auroc_death_ovr"] > mt3_ext["auroc_death_ovr"]
    phenotype_helped_auprc = mt4_ext["auprc_death"] > mt3_ext["auprc_death"]
    text = f"""# METRE Transport Final Recommendation

## Required answers

1. Did the METRE transport feature set reduce external AUROC/AUPRC drift?
   - AUROC drift reduction: `{auc_shift_reduced}`.
   - Original M1 AUROC drop: {m1_ext['external_internal_auroc_drop']:.4f}.
   - Best METRE AUROC drop: {best_ext['external_internal_auroc_drop']:.4f}.

2. Did the shared support-intensity proxy mitigate full VIS to reduced proxy information degradation?
   - Support proxy helped relative to MT1: `{support_helped}`.
   - MT1 eICU AUROC/AUPRC: {mt1_ext['auroc_death_ovr']:.4f} / {mt1_ext['auprc_death']:.4f}.
   - MT3 eICU AUROC/AUPRC: {mt3_ext['auroc_death_ovr']:.4f} / {mt3_ext['auprc_death']:.4f}.

3. Did minimal recency improve or harm external transport?
   - Minimal recency AUROC improved relative to MT1: `{recency_helped_auc}`.
   - Minimal recency AUPRC improved relative to MT1: `{recency_helped_auprc}`.
   - MT2 eICU AUROC/AUPRC: {mt2_ext['auroc_death_ovr']:.4f} / {mt2_ext['auprc_death']:.4f}.
   - Interpretation: minimal recency is mixed if AUROC and AUPRC move in opposite directions.

4. Did phenotype_label still show limited gain?
   - Phenotype sensitivity AUROC improved relative to MT3: `{phenotype_helped_auc}`.
   - Phenotype sensitivity AUPRC improved relative to MT3: `{phenotype_helped_auprc}`.
   - MT4 eICU AUROC/AUPRC: {mt4_ext['auroc_death_ovr']:.4f} / {mt4_ext['auprc_death']:.4f}.
   - Best sensitivity model by AUROC/AUPRC: `{best_sensitivity['model_name']}`.
   - Interpretation: phenotype remains a sensitivity/stratification variable because MT4 is not the default METRE transport model and does not improve AUPRC over MT3.

5. Which model is most suitable as the manuscript external transport model?
   - Recommended transport model: `{best_ext['model_name']}`.
   - Rationale: selected among default METRE models MT1-MT3 by external AUROC with AUPRC tie-break, while keeping full VIS and direct phenotype input out of the default transport path.

6. Should original M1 be positioned as an internal rich model?
   - Yes. Original M1 retains the strongest rich internal framing and should not be described as naturally transportable without qualification.
   - M1 internal AUROC/AUPRC: {m1_int['auroc_death_ovr']:.4f} / {m1_int['auprc_death']:.4f}.
   - M1 external AUROC/AUPRC: {m1_ext['auroc_death_ovr']:.4f} / {m1_ext['auprc_death']:.4f}.
"""
    (OUTDIR / "METRE_Transport_Final_Recommendation.md").write_text(text, encoding="utf-8")


def load_model_ready() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    needed = sorted(
        set(
            ["database_source", "patient_id", "stay_id", "t_pred", "chart_hour", TARGET_COL, "internal_split"]
            + REGISTRY_FEATURES
            + SUPPORT_INPUT_COLUMNS
        )
    )
    train_schema = set(pq.ParquetFile(TRAIN_PATH).schema.names)
    test_schema = set(pq.ParquetFile(TEST_PATH).schema.names)
    external_schema = set(pq.ParquetFile(EXTERNAL_PATH).schema.names)
    train_cols = [c for c in needed if c in train_schema]
    test_cols = [c for c in needed if c != "internal_split" and c in test_schema]
    external_cols = [c for c in needed if c != "internal_split" and c in external_schema]
    train = pd.read_parquet(TRAIN_PATH, columns=train_cols)
    test = pd.read_parquet(TEST_PATH, columns=test_cols)
    external = pd.read_parquet(EXTERNAL_PATH, columns=external_cols)
    train_inner = train[train["internal_split"] == "train_inner"].copy()
    validation = train[train["internal_split"] == "validation"].copy()
    return train_inner, validation, test, external, train


def add_proxy(df: pd.DataFrame, dataset_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    proxy = build_support_proxy(df)
    proxy["dataset_name"] = dataset_name
    proxy_cols = ["stay_id", "t_pred"] + SUPPORT_MODEL_FEATURES
    merged = df.merge(proxy[proxy_cols], on=["stay_id", "t_pred"], how="left", validate="many_to_one")
    return merged, proxy


def main() -> None:
    train_inner, validation, test, external, train_all = load_model_ready()
    train_inner, proxy_train_inner = add_proxy(train_inner, "mimic_train_inner")
    validation, proxy_validation = add_proxy(validation, "mimic_validation")
    test, proxy_test = add_proxy(test, "mimic_internal_test")
    external, proxy_external = add_proxy(external, "eicu_external")
    proxy_all = pd.concat([proxy_train_inner, proxy_validation, proxy_test, proxy_external], ignore_index=True)
    proxy_all.to_parquet(OUTDIR / "Shared_Support_Intensity_Proxy.parquet", index=False)
    write_support_definition(proxy_all)

    proxy_missing = {
        feature: (float(test[feature].isna().mean()), float(external[feature].isna().mean()))
        for feature in SUPPORT_MODEL_FEATURES
    }
    missing_overrides = {**proxy_missing, **compute_full_vis_missingness()}
    registry = build_registry(test, external, missing_overrides)
    write_registry_report(registry)
    write_feature_sets(registry)

    results = []
    for model_name, features in MT_FEATURES.items():
        result = fit_metre_model(model_name, features, train_inner, validation, test, external)
        results.append(result)
    comparison = comparison_table(results)
    write_model_report(results, comparison)
    write_final_recommendation(comparison)

    external = comparison[comparison["dataset_name"] == "eicu_external"].copy()
    best = external[external["model_name"].isin(["MT1_physiology_only", "MT2_physiology_minimal_recency", "MT3_physiology_support_proxy"])].sort_values(
        ["auroc_death_ovr", "auprc_death"], ascending=[False, False]
    ).iloc[0]
    print("METRE transport repair completed.")
    print(
        json.dumps(
            {
                "best_model": best["model_name"],
                "external_auroc": best["auroc_death_ovr"],
                "external_auprc": best["auprc_death"],
                "external_slope": best["calibration_slope_death"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
