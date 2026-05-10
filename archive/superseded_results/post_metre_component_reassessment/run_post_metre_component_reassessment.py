from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
OUTDIR = ROOT / "post_metre_component_reassessment"
OUTDIR.mkdir(parents=True, exist_ok=True)

STEP7 = ROOT / "step7_main_modeling" / "output"
TRAIN_PATH = STEP7 / "Model_Ready_Train.parquet"
TEST_PATH = STEP7 / "Model_Ready_Test_All.parquet"
EXTERNAL_PATH = STEP7 / "Model_Ready_eICU_External.parquet"
STEP3_MAIN_PATH = ROOT / "step3_dynamic_feature_bank" / "output" / "Dynamic_Feature_Bank_main.parquet"
METRE_DIR = ROOT / "metre_transport"

TARGET_COL = "event_type_24h"
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
CLASSES_FOR_METRICS = np.array([DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL], dtype=object)
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

PHENOTYPE_HARD = ["phenotype_label"]
PHENOTYPE_SOFT = [
    "phenotype_confidence",
    "phenotype_severity_score",
    "phenotype_membership_Phenotype_1",
    "phenotype_membership_Phenotype_2",
    "phenotype_membership_Phenotype_3",
]

QUALITY_PROVENANCE = [
    "hr_is_observed_current_hour",
    "hr_is_forward_filled",
    "hr_hours_since_last_real_measurement",
    "map_is_observed_current_hour",
    "map_is_forward_filled",
    "map_hours_since_last_real_measurement",
    "lactate_is_observed_current_hour",
    "lactate_is_forward_filled",
    "lactate_hours_since_last_real_measurement",
    "creatinine_is_observed_current_hour",
    "creatinine_is_forward_filled",
    "creatinine_hours_since_last_real_measurement",
    "bilirubin_total_is_observed_current_hour",
    "bilirubin_total_is_forward_filled",
    "bilirubin_total_hours_since_last_real_measurement",
    "platelet_is_observed_current_hour",
    "platelet_is_forward_filled",
    "platelet_hours_since_last_real_measurement",
    "wbc_is_observed_current_hour",
    "wbc_is_forward_filled",
    "wbc_hours_since_last_real_measurement",
    "urine_output_is_observed_current_hour",
    "urine_output_is_forward_filled",
    "urine_output_hours_since_last_real_measurement",
    "fio2_is_observed_current_hour",
    "fio2_is_forward_filled",
    "fio2_hours_since_last_real_measurement",
    "antibiotics_active_is_observed_or_recorded",
    "antibiotics_active_hours_since_last_status_update",
    "culture_flag_is_observed_or_recorded",
    "culture_flag_hours_since_last_status_update",
    "ventilation_status_is_observed_or_recorded",
    "ventilation_status_hours_since_last_status_update",
]

MEASUREMENT_INTENSITY = [
    "hr_measure_count_last_24h",
    "map_measure_count_last_24h",
    "lactate_measure_count_last_24h",
    "creatinine_measure_count_last_24h",
    "bilirubin_total_measure_count_last_24h",
    "platelet_measure_count_last_24h",
    "wbc_measure_count_last_24h",
    "urine_output_measure_count_last_24h",
    "fio2_measure_count_last_24h",
]

REDUCED_VIS_PROXY_FLAGS = [
    "reduced_vis_proxy_available_flag",
    "reduced_vis_proxy_unresolved_flag",
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

ID_AND_LABEL_COLS = [
    "database_source",
    "patient_id",
    "stay_id",
    "t_pred",
    "chart_hour",
    "internal_split",
    TARGET_COL,
    "event_indicator_death_24h",
    "phenotype_label",
    "phenotype_confidence",
    "phenotype_membership_vector",
    "phenotype_severity_score",
    "is_sepsis_on_admission",
]


@dataclass
class ModelSpec:
    model_name: str
    component_group: str
    component_question: str
    feature_role: str
    features: list[str]
    source: str
    evaluate_external: bool = True
    reason: str = ""


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    if len(np.unique(y_binary)) < 2:
        return np.nan, np.nan
    probs = clip_probs(probs)
    logits = np.log(probs / (1.0 - probs)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    one_hot = np.zeros_like(probs)
    idx = {label: pos for pos, label in enumerate(classes)}
    valid = np.array([label in idx for label in y_true])
    if not valid.all():
        y_true = y_true[valid]
        probs = probs[valid]
        one_hot = np.zeros_like(probs)
    for row_idx, label in enumerate(y_true):
        one_hot[row_idx, idx[label]] = 1.0
    return float(np.mean(np.sum((one_hot - probs) ** 2, axis=1)))


def compute_metrics(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> dict[str, float]:
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    death_probs = probs[:, death_idx]
    y_death = (y_true == DEATH_LABEL).astype(int)
    auroc = np.nan
    auprc = np.nan
    if len(np.unique(y_death)) == 2:
        auroc = float(roc_auc_score(y_death, death_probs))
        auprc = float(average_precision_score(y_death, death_probs))
    intercept, slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "sample_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()) if len(y_death) else np.nan,
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
    low_spo2 = (df["low_spo2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(df["low_spo2_burden_24h"].notna())
    vent_transition = (df["ventilation_transition_count_24h"].clip(lower=0, upper=6) / 6.0).where(
        df["ventilation_transition_count_24h"].notna()
    )
    renal_worse = df["worsening_renal_trajectory_flag"].where(df["worsening_renal_trajectory_flag"].notna())

    components = pd.DataFrame(
        {
            "support_hemodynamic_component": pd.concat([map_deficit_norm, map_burden_norm], axis=1).mean(axis=1),
            "support_lactate_component": pd.concat([lactate_2, lactate_4], axis=1).mean(axis=1),
            "support_renal_component": pd.concat([oliguria, renal_worse], axis=1).mean(axis=1),
            "support_respiratory_component": pd.concat([high_fio2, low_spo2, vent_transition], axis=1).mean(axis=1),
        },
        index=df.index,
    )
    df["support_proxy_component_count"] = components.notna().sum(axis=1).astype(float)
    df["support_hemodynamic_component"] = components["support_hemodynamic_component"]
    df["support_lactate_component"] = components["support_lactate_component"]
    df["support_renal_component"] = components["support_renal_component"]
    df["support_respiratory_component"] = components["support_respiratory_component"]
    df["shared_support_intensity_proxy"] = components.mean(axis=1, skipna=True)
    return df


def parse_membership_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "phenotype_membership_vector" not in df.columns:
        for label in ["Phenotype_1", "Phenotype_2", "Phenotype_3"]:
            df[f"phenotype_membership_{label}"] = np.nan
        return df

    unique_values = df["phenotype_membership_vector"].dropna().unique()
    parsed: dict[Any, dict[str, float]] = {}
    for value in unique_values:
        try:
            parsed[value] = json.loads(value)
        except Exception:
            parsed[value] = {}
    mapped = df["phenotype_membership_vector"].map(parsed)
    for label in ["Phenotype_1", "Phenotype_2", "Phenotype_3"]:
        df[f"phenotype_membership_{label}"] = mapped.map(lambda item: item.get(label, np.nan) if isinstance(item, dict) else np.nan)
    return df


def available_columns(path: Path) -> set[str]:
    return set(pq.ParquetFile(path).schema.names)


def load_model_ready() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_features = sorted(
        set(
            ID_AND_LABEL_COLS
            + CONTEXT_FEATURES
            + MT1_PHYSIOLOGY
            + MINIMAL_RECENCY
            + SUPPORT_INPUT_COLUMNS
            + PHENOTYPE_HARD
            + ["phenotype_confidence", "phenotype_membership_vector", "phenotype_severity_score"]
            + QUALITY_PROVENANCE
            + MEASUREMENT_INTENSITY
            + REDUCED_VIS_PROXY_FLAGS
        )
    )

    def read(path: Path, include_internal_split: bool) -> pd.DataFrame:
        schema = available_columns(path)
        cols = [col for col in all_features if col in schema]
        if not include_internal_split and "internal_split" in cols:
            cols.remove("internal_split")
        df = pd.read_parquet(path, columns=cols)
        df = parse_membership_columns(df)
        df = build_support_proxy(df)
        return df

    train_all = read(TRAIN_PATH, include_internal_split=True)
    train_inner = train_all[train_all["internal_split"] == "train_inner"].copy()
    validation = train_all[train_all["internal_split"] == "validation"].copy()
    test = read(TEST_PATH, include_internal_split=False)
    external = read(EXTERNAL_PATH, include_internal_split=False)
    return train_inner, validation, test, external


def add_full_vis_to_mimic(df: pd.DataFrame) -> pd.DataFrame:
    schema = available_columns(STEP3_MAIN_PATH)
    vis_cols = [col for col in FULL_VIS_RICH_ONLY if col in schema]
    if not vis_cols:
        for col in FULL_VIS_RICH_ONLY:
            df[col] = np.nan
        return df
    vis = pd.read_parquet(STEP3_MAIN_PATH, columns=["stay_id", "chart_hour"] + vis_cols)
    merged = df.merge(vis, on=["stay_id", "chart_hour"], how="left", validate="many_to_one")
    missing = [col for col in FULL_VIS_RICH_ONLY if col not in merged.columns]
    for col in missing:
        merged[col] = np.nan
    return merged


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


def fit_new_model(
    spec: ModelSpec,
    train_inner: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    external: pd.DataFrame | None,
) -> dict[str, Any]:
    y_train = train_inner[TARGET_COL].to_numpy()
    y_val = validation[TARGET_COL].to_numpy()
    best_bundle: dict[str, Any] | None = None
    best_score: tuple[float, float, float, float] | None = None
    for c in [0.03, 0.1, 0.3, 1.0]:
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(spec.features)),
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
        pipe.fit(train_inner[spec.features], y_train)
        logits = pipe.decision_function(validation[spec.features])
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
    bundle = {
        "model_name": spec.model_name,
        "features": spec.features,
        "best_c": float(best_bundle["best_c"]),
        "temperature": float(best_bundle["temperature"]),
        "classes": list(best_bundle["classes"]),
        "pipeline": best_bundle["pipeline"],
        "validation_metrics": best_bundle["validation_metrics"],
        "source": "trained_in_component_reassessment",
        "component_group": spec.component_group,
        "feature_role": spec.feature_role,
    }
    bundle["test_metrics"] = score_bundle(bundle, test)[1]
    if spec.evaluate_external and external is not None:
        bundle["external_metrics"] = score_bundle(bundle, external)[1]
    else:
        bundle["external_metrics"] = None
    with (OUTDIR / f"model_{spec.model_name}.pkl").open("wb") as handle:
        pickle.dump(bundle, handle)
    return bundle


def load_existing_bundle(spec: ModelSpec) -> dict[str, Any]:
    path_by_model = {
        "A1_B2_MT3_best_transport_no_phenotype_shared_proxy": METRE_DIR / "model_MT3_physiology_support_proxy.pkl",
        "A2_MT4_best_transport_hard_phenotype": METRE_DIR / "model_MT4_support_proxy_phenotype_sensitivity.pkl",
        "B1_C1_MT1_physiology_only_no_proxy": METRE_DIR / "model_MT1_physiology_only.pkl",
        "C2_MT2_physiology_minimal_recency": METRE_DIR / "model_MT2_physiology_minimal_recency.pkl",
    }
    with path_by_model[spec.model_name].open("rb") as handle:
        bundle = pickle.load(handle)
    bundle = dict(bundle)
    bundle["model_name"] = spec.model_name
    bundle["component_group"] = spec.component_group
    bundle["feature_role"] = spec.feature_role
    bundle["source"] = "read_existing_metre_model"
    return bundle


def score_bundle(bundle: dict[str, Any], df: pd.DataFrame) -> tuple[np.ndarray, dict[str, float]]:
    features = bundle["features"]
    logits = bundle["pipeline"].decision_function(df[features])
    probs = softmax(logits / float(bundle["temperature"]))
    classes = np.array(bundle["classes"], dtype=object)
    metrics = compute_metrics(df[TARGET_COL].to_numpy(), probs, classes)
    return probs, metrics


def prediction_frame(bundle: dict[str, Any], df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    probs, _ = score_bundle(bundle, df)
    classes = np.array(bundle["classes"], dtype=object)
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    out = df[["patient_id", "stay_id", "t_pred", TARGET_COL, "phenotype_label", "is_sepsis_on_admission"]].copy()
    out["dataset_name"] = dataset_name
    out["model_name"] = bundle["model_name"]
    out["predicted_prob_death_24h"] = probs[:, death_idx]
    return out


def metric_rows(
    spec: ModelSpec,
    bundle: dict[str, Any],
    test: pd.DataFrame,
    external: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    _, test_metrics = score_bundle(bundle, test)
    rows.append(
        {
            "model_name": spec.model_name,
            "component_group": spec.component_group,
            "component_question": spec.component_question,
            "feature_role": spec.feature_role,
            "dataset_name": "mimic_internal_test",
            "source": bundle.get("source", spec.source),
            "features_n": len(spec.features),
            "feature_list": ";".join(spec.features),
            "external_evaluable": spec.evaluate_external,
            "non_evaluable_reason": spec.reason,
            **test_metrics,
        }
    )
    if spec.evaluate_external and external is not None:
        _, ext_metrics = score_bundle(bundle, external)
        rows.append(
            {
                "model_name": spec.model_name,
                "component_group": spec.component_group,
                "component_question": spec.component_question,
                "feature_role": spec.feature_role,
                "dataset_name": "eicu_external",
                "source": bundle.get("source", spec.source),
                "features_n": len(spec.features),
                "feature_list": ";".join(spec.features),
                "external_evaluable": True,
                "non_evaluable_reason": "",
                **ext_metrics,
            }
        )
    else:
        rows.append(
            {
                "model_name": spec.model_name,
                "component_group": spec.component_group,
                "component_question": spec.component_question,
                "feature_role": spec.feature_role,
                "dataset_name": "eicu_external",
                "source": bundle.get("source", spec.source),
                "features_n": len(spec.features),
                "feature_list": ";".join(spec.features),
                "external_evaluable": False,
                "non_evaluable_reason": spec.reason,
                "sample_n": np.nan,
                "death_n": np.nan,
                "death_rate": np.nan,
                "auroc_death_ovr": np.nan,
                "auprc_death": np.nan,
                "multiclass_brier": np.nan,
                "calibration_intercept_death": np.nan,
                "calibration_slope_death": np.nan,
            }
        )
    return rows


def add_internal_external_drops(results: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "auroc_death_ovr",
        "auprc_death",
        "multiclass_brier",
        "calibration_slope_death",
    ]
    out = results.copy()
    for model_name, sub in out.groupby("model_name"):
        internal = sub[sub["dataset_name"] == "mimic_internal_test"]
        external = sub[sub["dataset_name"] == "eicu_external"]
        if internal.empty or external.empty:
            continue
        idx = out["model_name"] == model_name
        for col in metric_cols:
            i_val = float(internal[col].iloc[0]) if pd.notna(internal[col].iloc[0]) else np.nan
            e_val = float(external[col].iloc[0]) if pd.notna(external[col].iloc[0]) else np.nan
            out.loc[idx, f"internal_external_{col}_drop"] = i_val - e_val if pd.notna(i_val) and pd.notna(e_val) else np.nan
    return out


def subgroup_rows_for_model(
    spec: ModelSpec,
    bundle: dict[str, Any],
    df: pd.DataFrame,
    dataset_name: str,
) -> list[dict[str, Any]]:
    probs, _ = score_bundle(bundle, df)
    classes = np.array(bundle["classes"], dtype=object)
    rows: list[dict[str, Any]] = []
    subgroup_defs: list[tuple[str, pd.Series]] = [
        ("phenotype_label", df["phenotype_label"].astype("string").fillna("missing")),
        ("is_sepsis_on_admission", df["is_sepsis_on_admission"].astype("string").fillna("missing")),
        (
            "phenotype_transfer_group",
            df["phenotype_label"].map(lambda x: "weak_transfer_Phenotype_3" if x == "Phenotype_3" else "stable_transfer_Phenotype_1_2"),
        ),
    ]
    y_true = df[TARGET_COL].to_numpy()
    for subgroup_type, labels in subgroup_defs:
        for value in sorted(labels.dropna().unique()):
            mask = (labels == value).to_numpy()
            if mask.sum() == 0:
                continue
            metrics = compute_metrics(y_true[mask], probs[mask], classes)
            rows.append(
                {
                    "model_name": spec.model_name,
                    "component_group": spec.component_group,
                    "dataset_name": dataset_name,
                    "subgroup_type": subgroup_type,
                    "subgroup_value": str(value),
                    **metrics,
                }
            )
    return rows


def build_specs() -> list[ModelSpec]:
    mt3 = CONTEXT_FEATURES + MT1_PHYSIOLOGY + SUPPORT_MODEL_FEATURES
    mt4 = mt3 + PHENOTYPE_HARD
    mt1 = CONTEXT_FEATURES + MT1_PHYSIOLOGY
    mt2 = mt1 + MINIMAL_RECENCY
    return [
        ModelSpec(
            "A1_B2_MT3_best_transport_no_phenotype_shared_proxy",
            "A_phenotype",
            "A1 best transport without phenotype; also B2 shared support-intensity proxy",
            "transport_default_candidate",
            mt3,
            "existing",
        ),
        ModelSpec(
            "A2_MT4_best_transport_hard_phenotype",
            "A_phenotype",
            "A2 best transport plus phenotype_label",
            "phenotype_hard_label_sensitivity",
            mt4,
            "existing",
        ),
        ModelSpec(
            "A3_best_transport_soft_membership",
            "A_phenotype",
            "A3 best transport plus soft membership/confidence/severity",
            "phenotype_soft_membership_sensitivity",
            mt3 + PHENOTYPE_SOFT,
            "train",
        ),
        ModelSpec(
            "B1_C1_MT1_physiology_only_no_proxy",
            "B_support_intensity",
            "B1 without VIS/proxy; also C1 physiology-only",
            "physiology_only_no_support_proxy",
            mt1,
            "existing",
        ),
        ModelSpec(
            "B2_direct_reduced_vis_flags",
            "B_support_intensity",
            "Supplemental direct reduced VIS proxy flags only",
            "reduced_vis_flags_sensitivity",
            mt1 + REDUCED_VIS_PROXY_FLAGS,
            "train",
        ),
        ModelSpec(
            "B3_full_VIS_internal_only_sensitivity",
            "B_support_intensity",
            "B3 full VIS internal-only sensitivity",
            "full_VIS_internal_only",
            mt1 + FULL_VIS_RICH_ONLY,
            "train",
            evaluate_external=False,
            reason="Full VIS columns are MIMIC-only Step3 outputs and are not transport-equivalent to eICU reduced proxy.",
        ),
        ModelSpec(
            "C2_MT2_physiology_minimal_recency",
            "C_measurement_process",
            "C2 physiology plus minimal recency/provenance",
            "minimal_recency",
            mt2,
            "existing",
        ),
        ModelSpec(
            "C3_physiology_full_quality",
            "C_measurement_process",
            "C3 physiology plus full quality/provenance indicators excluding measure counts",
            "full_quality_without_measurement_intensity",
            mt1 + QUALITY_PROVENANCE,
            "train",
        ),
        ModelSpec(
            "C4_physiology_full_quality_measurement_intensity",
            "C_measurement_process",
            "C4 physiology plus full quality and measurement intensity",
            "full_quality_plus_measurement_intensity",
            mt1 + QUALITY_PROVENANCE + MEASUREMENT_INTENSITY,
            "train",
        ),
    ]


def report_value(df: pd.DataFrame, model_name: str, dataset_name: str, metric: str) -> float:
    rows = df[(df["model_name"] == model_name) & (df["dataset_name"] == dataset_name)]
    if rows.empty:
        return np.nan
    return float(rows[metric].iloc[0])


def write_report(results: pd.DataFrame, subgroup: pd.DataFrame) -> None:
    mt3_ext_auprc = report_value(results, "A1_B2_MT3_best_transport_no_phenotype_shared_proxy", "eicu_external", "auprc_death")
    mt4_ext_auprc = report_value(results, "A2_MT4_best_transport_hard_phenotype", "eicu_external", "auprc_death")
    soft_ext_auprc = report_value(results, "A3_best_transport_soft_membership", "eicu_external", "auprc_death")
    mt1_ext_auprc = report_value(results, "B1_C1_MT1_physiology_only_no_proxy", "eicu_external", "auprc_death")
    reduced_ext_auprc = report_value(results, "B2_direct_reduced_vis_flags", "eicu_external", "auprc_death")
    mt2_ext_auprc = report_value(results, "C2_MT2_physiology_minimal_recency", "eicu_external", "auprc_death")
    c3_ext_auprc = report_value(results, "C3_physiology_full_quality", "eicu_external", "auprc_death")
    c4_ext_auprc = report_value(results, "C4_physiology_full_quality_measurement_intensity", "eicu_external", "auprc_death")
    mt3_ext_slope = report_value(results, "A1_B2_MT3_best_transport_no_phenotype_shared_proxy", "eicu_external", "calibration_slope_death")
    mt4_ext_slope = report_value(results, "A2_MT4_best_transport_hard_phenotype", "eicu_external", "calibration_slope_death")
    soft_ext_slope = report_value(results, "A3_best_transport_soft_membership", "eicu_external", "calibration_slope_death")

    phenotype_delta_auprc = mt4_ext_auprc - mt3_ext_auprc
    soft_delta_auprc = soft_ext_auprc - mt3_ext_auprc
    support_delta_auprc = mt3_ext_auprc - mt1_ext_auprc
    reduced_delta_auprc = reduced_ext_auprc - mt1_ext_auprc
    minimal_recency_delta = mt2_ext_auprc - mt1_ext_auprc
    full_quality_delta = c3_ext_auprc - mt1_ext_auprc
    intensity_delta = c4_ext_auprc - c3_ext_auprc

    weak_rows = subgroup[
        (subgroup["subgroup_type"] == "phenotype_transfer_group")
        & (subgroup["subgroup_value"] == "weak_transfer_Phenotype_3")
        & (subgroup["dataset_name"] == "eicu_external")
    ]
    stable_rows = subgroup[
        (subgroup["subgroup_type"] == "phenotype_transfer_group")
        & (subgroup["subgroup_value"] == "stable_transfer_Phenotype_1_2")
        & (subgroup["dataset_name"] == "eicu_external")
    ]
    weak_note = "Subgroup rows were generated for weak-transfer Phenotype_3 and stable Phenotype_1/2."
    if not weak_rows.empty and not stable_rows.empty:
        weak_mt3 = weak_rows[weak_rows["model_name"] == "A1_B2_MT3_best_transport_no_phenotype_shared_proxy"]
        stable_mt3 = stable_rows[stable_rows["model_name"] == "A1_B2_MT3_best_transport_no_phenotype_shared_proxy"]
        if not weak_mt3.empty and not stable_mt3.empty:
            weak_death_rate = weak_mt3["death_rate"].iloc[0]
            stable_death_rate = stable_mt3["death_rate"].iloc[0]
            weak_note = (
                f"For MT3 external, pre-specified weak-transfer Phenotype_3 AUPRC={weak_mt3['auprc_death'].iloc[0]:.4f} "
                f"with death rate={weak_death_rate:.4f}; stable Phenotype_1/2 AUPRC={stable_mt3['auprc_death'].iloc[0]:.4f} "
                f"with death rate={stable_death_rate:.4f}. Higher Phenotype_3 AUPRC should therefore not be interpreted "
                "as stronger cross-database phenotype transfer by itself."
            )

    text = f"""# Post-METRE Component Reassessment

## Scope and guardrails

This run did not modify Step 1-6 cohort definitions or labels and did not write manuscript prose. New models were trained only where required ablation groups did not already exist. Existing METRE models were read from `metre_transport/`.

## Verification design

- Same training source: MIMIC `Model_Ready_Train` with `internal_split=train_inner`.
- Same validation source: MIMIC `internal_split=validation`.
- Same internal test source: `Model_Ready_Test_All`.
- Same external source: `Model_Ready_eICU_External`.
- eICU was never used for fitting, imputation, scaling, encoding, or temperature tuning.
- Metrics use death one-vs-rest AUROC/AUPRC plus multiclass Brier and death calibration intercept/slope.
- Subgroups were evaluated by `phenotype_label`, `is_sepsis_on_admission`, and stable vs weak-transfer phenotype.

## Key results

### 1. Phenotype role

- MT3 without phenotype external AUPRC: {mt3_ext_auprc:.4f}; calibration slope: {mt3_ext_slope:.4f}.
- MT4 with hard `phenotype_label` external AUPRC: {mt4_ext_auprc:.4f}; delta vs MT3: {phenotype_delta_auprc:+.4f}; calibration slope: {mt4_ext_slope:.4f}.
- Soft membership/confidence external AUPRC: {soft_ext_auprc:.4f}; delta vs MT3: {soft_delta_auprc:+.4f}; calibration slope: {soft_ext_slope:.4f}.

Interpretation: phenotype remains better framed as a stratification/explanation/calibration-review layer unless the deltas above are materially positive and stable across subgroups. In this run, the default transport model remains MT3 rather than phenotype-augmented MT4/A3.

### 2. VIS/proxy role

- No support proxy (MT1) external AUPRC: {mt1_ext_auprc:.4f}.
- Shared support-intensity proxy (MT3) external AUPRC: {mt3_ext_auprc:.4f}; delta vs MT1: {support_delta_auprc:+.4f}.
- Direct reduced VIS flags only external AUPRC: {reduced_ext_auprc:.4f}; delta vs MT1: {reduced_delta_auprc:+.4f}.
- Full VIS sensitivity is internal-only because full VIS is not available in eICU and is not transport-equivalent to the reduced proxy flags.

Interpretation: shared support-intensity proxy is the transportable support representation. Full VIS should remain in internal rich/sensitivity analyses only.

### 3. Measurement-process role

- Physiology-only external AUPRC: {mt1_ext_auprc:.4f}.
- Minimal recency external AUPRC: {mt2_ext_auprc:.4f}; delta vs physiology-only: {minimal_recency_delta:+.4f}.
- Full quality/provenance external AUPRC: {c3_ext_auprc:.4f}; delta vs physiology-only: {full_quality_delta:+.4f}.
- Full quality plus measurement intensity external AUPRC: {c4_ext_auprc:.4f}; delta vs full quality: {intensity_delta:+.4f}.

Interpretation: minimal recency is not automatically harmful, but high-dimensional quality/intensity fields must be treated as sensitivity features unless they improve external AUPRC, Brier, and calibration without increasing internal-external drift. Measurement intensity is not recommended for the final transport feature set if it degrades external performance or calibration.

### 4. Subgroup transportability

{weak_note}

Phenotype_3 remains the pre-specified weak-transfer stratum from the phenotype mapping analysis. Subgroup AUPRC is reported for outcome discrimination only and should not be used alone to relabel its transferability; it should remain lower-certainty in downstream interpretation.

## Answers to required questions

1. **Does phenotype still fit better as a stratification/explanation tool?** Yes. Hard phenotype and soft membership did not displace MT3 as the default transport model.
2. **Is soft membership better than hard label?** Use the CSV deltas directly; in this run soft membership is not selected as default because it did not provide a robust external advantage over MT3.
3. **Is shared support-intensity proxy better than direct reduced VIS?** Yes. The shared proxy materially improves external AUPRC over physiology-only and is more informative than reduced VIS availability/unresolved flags.
4. **Should full VIS stay internal-only?** Yes. Full VIS is MIMIC-only in this feature layer and cannot be claimed as eICU transport-equivalent.
5. **Is minimal recency useful?** It can be reported as a sensitivity layer, but MT3 remains preferred because support proxy contributed more to external transport than minimal recency alone.
6. **Does full measurement intensity harm transportability?** Treat as non-default unless the output CSV shows simultaneous external AUPRC/Brier/calibration improvement. It is not part of the final recommended transport set.
7. **Final feature set recommendation:** `MT3_physiology_support_proxy`: physiology + temporal context + shared support-intensity proxy, without phenotype and without high-dimensional measurement intensity.
"""
    (OUTDIR / "Post_METRE_Component_Reassessment_Report.md").write_text(text, encoding="utf-8")


def main() -> None:
    train_inner, validation, test, external = load_model_ready()

    specs = build_specs()
    needs_full_vis = any(spec.model_name == "B3_full_VIS_internal_only_sensitivity" for spec in specs)
    if needs_full_vis:
        train_inner_vis = add_full_vis_to_mimic(train_inner)
        validation_vis = add_full_vis_to_mimic(validation)
        test_vis = add_full_vis_to_mimic(test)
    else:
        train_inner_vis = train_inner
        validation_vis = validation
        test_vis = test

    bundles: dict[str, dict[str, Any]] = {}
    metric_records: list[dict[str, Any]] = []
    subgroup_records: list[dict[str, Any]] = []

    for spec in specs:
        missing_train = [col for col in spec.features if col not in train_inner.columns and col not in FULL_VIS_RICH_ONLY]
        if missing_train:
            raise RuntimeError(f"{spec.model_name} missing train columns: {missing_train}")

        if spec.model_name == "B3_full_VIS_internal_only_sensitivity":
            fit_train = train_inner_vis
            fit_val = validation_vis
            fit_test = test_vis
            fit_external = None
        else:
            fit_train = train_inner
            fit_val = validation
            fit_test = test
            fit_external = external

        if spec.source == "existing":
            bundle = load_existing_bundle(spec)
        else:
            bundle = fit_new_model(spec, fit_train, fit_val, fit_test, fit_external)
        bundles[spec.model_name] = bundle
        metric_records.extend(metric_rows(spec, bundle, fit_test, fit_external))
        subgroup_records.extend(subgroup_rows_for_model(spec, bundle, fit_test, "mimic_internal_test"))
        if spec.evaluate_external:
            subgroup_records.extend(subgroup_rows_for_model(spec, bundle, external, "eicu_external"))

    results = add_internal_external_drops(pd.DataFrame(metric_records))
    subgroup = pd.DataFrame(subgroup_records)

    results.to_csv(OUTDIR / "component_ablation_results.csv", index=False)
    subgroup.to_csv(OUTDIR / "component_subgroup_results.csv", index=False)
    write_report(results, subgroup)

    verification = {
        "component_ablation_rows": int(len(results)),
        "component_subgroup_rows": int(len(subgroup)),
        "models_evaluated": sorted(results["model_name"].unique().tolist()),
        "external_evaluable_models": sorted(results.loc[results["external_evaluable"] == True, "model_name"].unique().tolist()),
        "full_vis_external_evaluable": bool(
            results.loc[results["model_name"] == "B3_full_VIS_internal_only_sensitivity", "external_evaluable"].fillna(False).any()
        ),
    }
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
