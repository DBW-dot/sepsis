from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "transport_model"
OUTDIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = ROOT / "step7_main_modeling" / "output" / "Model_Ready_Train.parquet"
TEST_PATH = ROOT / "step7_main_modeling" / "output" / "Model_Ready_Test_All.parquet"
EXTERNAL_PATH = ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet"
PRED_TEST_M1 = ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet"
PRED_EXT_M1 = ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet"


TARGET_COL = "event_type_24h"
DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"

TRANSPORT_CONTEXT = [
    "hours_from_anchor",
    "hours_since_icu_admission",
    "is_sepsis_on_admission",
]

TRANSPORT_PHYSIOLOGY = [
    "hr_latest_value",
    "hr_slope_6h",
    "map_below_65_burden_24h",
    "map_deficit",
    "rr_latest_value",
    "spo2_latest_value",
    "high_fio2_burden_24h",
    "low_spo2_burden_24h",
    "ventilation_transition_count_24h",
    "lactate_gt2_burden_24h",
    "lactate_gt4_burden_24h",
    "oliguria_burden_24h",
    "creatinine_latest_value",
    "creatinine_relative_rise_from_24h_min",
    "bun_latest_value",
    "platelet_latest_value",
    "platelet_relative_drop_24h",
    "wbc_latest_value",
    "worsening_renal_trajectory_flag",
    "antibiotics_active_current",
    "culture_flag_current",
]

MINIMAL_RECENCY = [
    "map_hours_since_last_real_measurement",
    "lactate_hours_since_last_real_measurement",
    "creatinine_hours_since_last_real_measurement",
    "urine_output_hours_since_last_real_measurement",
    "fio2_hours_since_last_real_measurement",
]

PHENOTYPE_FEATURE = ["phenotype_label"]

T1_FEATURES = TRANSPORT_CONTEXT + TRANSPORT_PHYSIOLOGY + MINIMAL_RECENCY
T2_FEATURES = T1_FEATURES + PHENOTYPE_FEATURE

CANDIDATE_POOL = [
    "hours_from_anchor",
    "hours_since_icu_admission",
    "is_sepsis_on_admission",
    "phenotype_label",
    "hr_latest_value",
    "hr_slope_6h",
    "hr_sd_24h",
    "sbp_latest_value",
    "map_latest_value",
    "map_slope_6h",
    "map_below_65_burden_24h",
    "map_deficit",
    "shock_index",
    "shock_index_slope_6h",
    "temperature_latest_value",
    "rr_latest_value",
    "spo2_latest_value",
    "fio2_latest_value",
    "spo2_fio2_ratio",
    "pao2_fio2_ratio",
    "high_fio2_burden_24h",
    "low_spo2_burden_24h",
    "ventilation_transition_count_24h",
    "lactate_latest_value",
    "lactate_slope_6h",
    "lactate_gt2_burden_24h",
    "lactate_gt4_burden_24h",
    "urine_output_latest_value",
    "oliguria_burden_24h",
    "creatinine_latest_value",
    "creatinine_relative_rise_from_24h_min",
    "bun_latest_value",
    "worsening_renal_trajectory_flag",
    "bilirubin_total_latest_value",
    "bilirubin_slope_24h",
    "platelet_latest_value",
    "platelet_relative_drop_24h",
    "wbc_latest_value",
    "antibiotics_active_current",
    "culture_flag_current",
    "hr_is_observed_current_hour",
    "hr_is_forward_filled",
    "hr_hours_since_last_real_measurement",
    "hr_measure_count_last_24h",
    "map_is_observed_current_hour",
    "map_is_forward_filled",
    "map_hours_since_last_real_measurement",
    "map_measure_count_last_24h",
    "lactate_is_observed_current_hour",
    "lactate_is_forward_filled",
    "lactate_hours_since_last_real_measurement",
    "lactate_measure_count_last_24h",
    "creatinine_is_observed_current_hour",
    "creatinine_is_forward_filled",
    "creatinine_hours_since_last_real_measurement",
    "creatinine_measure_count_last_24h",
    "bilirubin_total_is_observed_current_hour",
    "bilirubin_total_is_forward_filled",
    "bilirubin_total_hours_since_last_real_measurement",
    "bilirubin_total_measure_count_last_24h",
    "platelet_is_observed_current_hour",
    "platelet_is_forward_filled",
    "platelet_hours_since_last_real_measurement",
    "platelet_measure_count_last_24h",
    "wbc_is_observed_current_hour",
    "wbc_is_forward_filled",
    "wbc_hours_since_last_real_measurement",
    "wbc_measure_count_last_24h",
    "urine_output_is_observed_current_hour",
    "urine_output_is_forward_filled",
    "urine_output_hours_since_last_real_measurement",
    "urine_output_measure_count_last_24h",
    "fio2_is_observed_current_hour",
    "fio2_is_forward_filled",
    "fio2_hours_since_last_real_measurement",
    "fio2_measure_count_last_24h",
    "antibiotics_active_is_observed_or_recorded",
    "antibiotics_active_hours_since_last_status_update",
    "culture_flag_is_observed_or_recorded",
    "culture_flag_hours_since_last_status_update",
    "ventilation_status_is_observed_or_recorded",
    "ventilation_status_hours_since_last_status_update",
    "ventilation_status_current",
]


@dataclass
class ModelResult:
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


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = np.clip(probs.astype(float), 1e-6, 1 - 1e-6)
    logits = np.log(probs / (1 - probs)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    onehot = np.zeros_like(probs)
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
    for row_idx, label in enumerate(y_true):
        onehot[row_idx, class_to_idx[label]] = 1.0
    return float(np.mean(np.sum((onehot - probs) ** 2, axis=1)))


def compute_metrics(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> dict[str, float]:
    death_idx = int(np.where(classes == DEATH_LABEL)[0][0])
    death_probs = probs[:, death_idx]
    y_death = (y_true == DEATH_LABEL).astype(int)
    auroc = float(roc_auc_score(y_death, death_probs))
    auprc = float(average_precision_score(y_death, death_probs))
    brier_multi = multiclass_brier(y_true, probs, classes)
    cal_intercept, cal_slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "sample_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_ratio": float(y_death.mean()),
        "auroc_death_ovr": auroc,
        "auprc_death": auprc,
        "multiclass_brier": brier_multi,
        "calibration_intercept_death": cal_intercept,
        "calibration_slope_death": cal_slope,
    }


def tune_temperature(y_true: np.ndarray, logits: np.ndarray, classes: np.ndarray) -> tuple[float, float]:
    best_t = 1.0
    best_loss = np.inf
    for t in list(np.linspace(0.5, 3.0, 26)) + [3.5, 4.0, 5.0]:
        probs = softmax(logits / t)
        loss = log_loss(y_true, probs, labels=list(classes))
        if loss < best_loss:
            best_loss = loss
            best_t = float(t)
    return best_t, float(best_loss)


def build_preprocessor(feature_list: list[str]) -> tuple[ColumnTransformer, list[str], list[str]]:
    categorical_features = [f for f in feature_list if f == "phenotype_label"]
    numeric_features = [f for f in feature_list if f not in categorical_features]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )
    return preprocessor, numeric_features, categorical_features


def fit_transport_model(
    model_name: str,
    feature_list: list[str],
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    external_df: pd.DataFrame,
) -> ModelResult:
    candidate_cs = [0.03, 0.1, 0.3, 1.0]
    y_train = train_df[TARGET_COL].to_numpy()
    y_val = validation_df[TARGET_COL].to_numpy()

    best = None
    best_score = None

    for c in candidate_cs:
        preprocessor, _, _ = build_preprocessor(feature_list)
        clf = LogisticRegression(
            C=c,
            class_weight="balanced",
            solver="saga",
            penalty="l2",
            max_iter=300,
            tol=1e-3,
            n_jobs=-1,
            random_state=42,
        )
        pipe = Pipeline([("preprocessor", preprocessor), ("classifier", clf)])
        pipe.fit(train_df[feature_list], y_train)

        val_logits = pipe.decision_function(validation_df[feature_list])
        classes = pipe.named_steps["classifier"].classes_
        best_t, val_logloss = tune_temperature(y_val, val_logits, classes)
        val_probs = softmax(val_logits / best_t)
        val_metrics = compute_metrics(y_val, val_probs, classes)

        score = (val_metrics["multiclass_brier"], -val_metrics["auprc_death"], abs(val_metrics["calibration_slope_death"] - 1.0), val_logloss)
        if best_score is None or score < best_score:
            best_score = score
            best = {
                "pipeline": pipe,
                "classes": classes,
                "temperature": best_t,
                "best_c": c,
                "validation_metrics": val_metrics,
            }

    assert best is not None
    pipe = best["pipeline"]
    classes = best["classes"]
    temperature = float(best["temperature"])

    def evaluate(df: pd.DataFrame) -> dict[str, float]:
        logits = pipe.decision_function(df[feature_list])
        probs = softmax(logits / temperature)
        return compute_metrics(df[TARGET_COL].to_numpy(), probs, classes)

    test_metrics = evaluate(test_df)
    external_metrics = evaluate(external_df)

    bundle = {
        "model_name": model_name,
        "features": feature_list,
        "best_c": float(best["best_c"]),
        "temperature": temperature,
        "classes": list(classes),
        "pipeline": pipe,
        "validation_metrics": best["validation_metrics"],
        "test_metrics": test_metrics,
        "external_metrics": external_metrics,
    }
    with (OUTDIR / f"transport_model_{model_name}.pkl").open("wb") as handle:
        pickle.dump(bundle, handle)

    return ModelResult(
        model_name=model_name,
        features=feature_list,
        best_c=float(best["best_c"]),
        temperature=temperature,
        validation_metrics=best["validation_metrics"],
        test_metrics=test_metrics,
        external_metrics=external_metrics,
    )


def build_feature_manifest(train_df: pd.DataFrame, external_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_selected = set(T2_FEATURES)
    for feature in CANDIDATE_POOL:
        if feature in TRANSPORT_CONTEXT:
            domain = "alignment"
        elif feature in MINIMAL_RECENCY:
            domain = "minimal_recency"
        elif feature == "phenotype_label":
            domain = "phenotype"
        else:
            domain = "physiology_or_support"

        if feature in T1_FEATURES:
            status_t1 = "keep"
        else:
            status_t1 = "exclude"
        if feature in T2_FEATURES:
            status_t2 = "keep"
        else:
            status_t2 = "exclude"

        external_missing = float(external_df[feature].isna().mean()) if feature in external_df.columns else np.nan

        if feature in T1_FEATURES or feature in T2_FEATURES:
            reason = "Retained for transport-focused core physiology/support or minimal recency provenance."
        elif "measure_count_last_24h" in feature or "is_observed_current_hour" in feature or "is_forward_filled" in feature:
            reason = "Removed because high-dimensional observation-process signal harmed transportability in prior experiments."
        elif feature in {"ventilation_status_current", "ventilation_status_hours_since_last_status_update"}:
            reason = "Removed because respiratory support state mapping was highly incomplete in eICU."
        elif feature in {"sbp_latest_value", "shock_index", "shock_index_slope_6h", "map_latest_value", "map_slope_6h", "temperature_latest_value", "fio2_latest_value", "spo2_fio2_ratio", "pao2_fio2_ratio", "lactate_latest_value", "lactate_slope_6h", "urine_output_latest_value", "bilirubin_total_latest_value", "bilirubin_slope_24h"}:
            reason = "Removed because the raw instantaneous signal had high external missingness or unstable transport mapping."
        elif feature in {"antibiotics_active_is_observed_or_recorded", "antibiotics_active_hours_since_last_status_update", "culture_flag_is_observed_or_recorded", "culture_flag_hours_since_last_status_update", "ventilation_status_is_observed_or_recorded"}:
            reason = "Removed because status-update metadata reflects local observation workflow more than transportable physiology."
        elif feature == "phenotype_label":
            reason = "Excluded from T1 by design and reintroduced only in T2 to audit phenotype transport value."
        else:
            reason = "Removed to keep the transport model compact and reduce dependence on measurement-process proxies."

        rows.append(
            {
                "feature_name": feature,
                "feature_domain": domain,
                "external_missing_rate": external_missing,
                "t1_status": status_t1,
                "t2_status": status_t2,
                "selection_reason": reason,
            }
        )
    manifest = pd.DataFrame(rows).sort_values(["t1_status", "t2_status", "feature_domain", "feature_name"]).reset_index(drop=True)
    manifest.to_csv(OUTDIR / "Transport_Feature_Set.csv", index=False, encoding="utf-8-sig")
    return manifest


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    columns = sorted(set(CANDIDATE_POOL + [TARGET_COL, "internal_split"]))
    train = pd.read_parquet(TRAIN_PATH, columns=columns)
    test = pd.read_parquet(TEST_PATH, columns=sorted(set(CANDIDATE_POOL + [TARGET_COL])))
    external = pd.read_parquet(EXTERNAL_PATH, columns=sorted(set(CANDIDATE_POOL + [TARGET_COL])))
    train_inner = train.loc[train["internal_split"] == "train_inner"].copy()
    validation = train.loc[train["internal_split"] == "validation"].copy()
    return train_inner, validation, test, external


def load_m1_metrics() -> list[dict[str, float | str]]:
    rows = []
    mapping = {
        "test_all": PRED_TEST_M1,
        "eicu_external": PRED_EXT_M1,
    }
    for dataset_name, path in mapping.items():
        df = pd.read_parquet(path)
        classes = np.array([ALIVE_DISCHARGE_LABEL := DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL], dtype=object)
        # Use the death/discharge/no-event columns exactly as persisted in Step 7.
        probs = np.column_stack(
            [
                df["predicted_prob_discharge_24h"].to_numpy(),
                df["predicted_prob_death_24h"].to_numpy(),
                df["predicted_prob_no_event_24h"].to_numpy(),
            ]
        )
        metrics = compute_metrics(df["true_event_type_24h"].to_numpy(), probs, classes)
        metrics.update({"model_name": "M1", "dataset_name": dataset_name})
        rows.append(metrics)
    return rows


def comparison_table(t1: ModelResult, t2: ModelResult, m1_rows: list[dict[str, float | str]]) -> pd.DataFrame:
    rows = []
    for dataset_name, metrics in [("test_all", t1.test_metrics), ("eicu_external", t1.external_metrics)]:
        row = {"model_name": "T1_no_phenotype", "dataset_name": dataset_name, **metrics}
        rows.append(row)
    for dataset_name, metrics in [("test_all", t2.test_metrics), ("eicu_external", t2.external_metrics)]:
        row = {"model_name": "T2_with_phenotype", "dataset_name": dataset_name, **metrics}
        rows.append(row)
    rows.extend(m1_rows)
    table = pd.DataFrame(rows)

    baseline = table.loc[table["model_name"] == "M1", ["dataset_name", "auroc_death_ovr", "auprc_death", "multiclass_brier", "calibration_intercept_death", "calibration_slope_death"]]
    baseline = baseline.rename(columns={c: f"m1_{c}" for c in baseline.columns if c != "dataset_name"})
    table = table.merge(baseline, on="dataset_name", how="left")
    table["delta_auroc_vs_m1"] = table["auroc_death_ovr"] - table["m1_auroc_death_ovr"]
    table["delta_auprc_vs_m1"] = table["auprc_death"] - table["m1_auprc_death"]
    table["delta_brier_vs_m1"] = table["multiclass_brier"] - table["m1_multiclass_brier"]
    table["delta_calibration_slope_vs_m1"] = table["calibration_slope_death"] - table["m1_calibration_slope_death"]
    table.to_csv(OUTDIR / "Transport_Model_Comparison.csv", index=False, encoding="utf-8-sig")
    return table


def report_text(manifest: pd.DataFrame, t1: ModelResult, t2: ModelResult, comparison: pd.DataFrame) -> str:
    kept = manifest.loc[manifest["t1_status"] == "keep", "feature_name"].tolist()
    excluded_obs = manifest.loc[manifest["selection_reason"].str.contains("observation-process", na=False), "feature_name"].tolist()
    excluded_high_missing = manifest.loc[manifest["selection_reason"].str.contains("high external missingness", na=False), "feature_name"].tolist()

    def row(model_name: str, dataset_name: str) -> pd.Series:
        return comparison.loc[(comparison["model_name"] == model_name) & (comparison["dataset_name"] == dataset_name)].iloc[0]

    m1_test = row("M1", "test_all")
    m1_ext = row("M1", "eicu_external")
    t1_test = row("T1_no_phenotype", "test_all")
    t1_ext = row("T1_no_phenotype", "eicu_external")
    t2_test = row("T2_with_phenotype", "test_all")
    t2_ext = row("T2_with_phenotype", "eicu_external")

    recommend_main = "yes" if (t1_ext["auprc_death"] > m1_ext["auprc_death"] and t1_ext["calibration_slope_death"] > m1_ext["calibration_slope_death"]) else "no"
    report = f"""# Transport Model Report

## Goal

This experiment trained transport-focused competing-risk models to improve eICU transportability and external calibration rather than to maximize internal-only performance.

## Final transport feature strategy

- T1 (`no phenotype`) used {len(T1_FEATURES)} inputs.
- T2 (`with phenotype_label`) used {len(T2_FEATURES)} inputs.
- Retained inputs focused on cross-database core physiology, support-intensity surrogates, alignment variables, and only minimal recency provenance.
- High-dimensional observation-process variables such as `*_measure_count_last_24h`, `*_is_observed_current_hour`, and `*_is_forward_filled` were removed.
- Highly unstable or externally sparse raw support proxies such as `ventilation_status_current`, `shock_index`, `sbp_latest_value`, `lactate_latest_value`, and `urine_output_latest_value` were removed from the transport set.

### T1 retained feature list

{json.dumps(T1_FEATURES, ensure_ascii=False, indent=2)}

### T2 added feature

{json.dumps([f for f in T2_FEATURES if f not in T1_FEATURES], ensure_ascii=False, indent=2)}

## Excluded feature groups

- Observation-process heavy features removed:
  {', '.join(excluded_obs[:20])}
- High-missingness / unstable raw signals removed:
  {', '.join(excluded_high_missing[:20])}

## Training design

- Base learner: regularized multinomial logistic regression with balanced class weights.
- Development split used for this transport experiment:
  - `train_inner` for fitting
  - `validation` for regularization and temperature selection
- Selection criterion: lowest validation multiclass Brier score after temperature scaling, with tie-break on death AUPRC.
- Selected hyperparameters:
  - T1: `C={t1.best_c}`, `temperature={t1.temperature:.3f}`
  - T2: `C={t2.best_c}`, `temperature={t2.temperature:.3f}`

## Validation snapshot

- T1 validation metrics: {json.dumps(t1.validation_metrics, ensure_ascii=False)}
- T2 validation metrics: {json.dumps(t2.validation_metrics, ensure_ascii=False)}

## Internal vs external comparison

### M1 baseline

- Internal test: AUROC={m1_test['auroc_death_ovr']:.4f}, AUPRC={m1_test['auprc_death']:.4f}, multiclass Brier={m1_test['multiclass_brier']:.4f}, calibration slope={m1_test['calibration_slope_death']:.4f}
- eICU external: AUROC={m1_ext['auroc_death_ovr']:.4f}, AUPRC={m1_ext['auprc_death']:.4f}, multiclass Brier={m1_ext['multiclass_brier']:.4f}, calibration slope={m1_ext['calibration_slope_death']:.4f}

### T1 (no phenotype)

- Internal test: AUROC={t1_test['auroc_death_ovr']:.4f}, AUPRC={t1_test['auprc_death']:.4f}, multiclass Brier={t1_test['multiclass_brier']:.4f}, calibration slope={t1_test['calibration_slope_death']:.4f}
- eICU external: AUROC={t1_ext['auroc_death_ovr']:.4f}, AUPRC={t1_ext['auprc_death']:.4f}, multiclass Brier={t1_ext['multiclass_brier']:.4f}, calibration slope={t1_ext['calibration_slope_death']:.4f}
- External delta vs M1: ΔAUPRC={t1_ext['delta_auprc_vs_m1']:.4f}, Δslope={t1_ext['delta_calibration_slope_vs_m1']:.4f}

### T2 (with phenotype_label)

- Internal test: AUROC={t2_test['auroc_death_ovr']:.4f}, AUPRC={t2_test['auprc_death']:.4f}, multiclass Brier={t2_test['multiclass_brier']:.4f}, calibration slope={t2_test['calibration_slope_death']:.4f}
- eICU external: AUROC={t2_ext['auroc_death_ovr']:.4f}, AUPRC={t2_ext['auprc_death']:.4f}, multiclass Brier={t2_ext['multiclass_brier']:.4f}, calibration slope={t2_ext['calibration_slope_death']:.4f}
- External delta vs M1: ΔAUPRC={t2_ext['delta_auprc_vs_m1']:.4f}, Δslope={t2_ext['delta_calibration_slope_vs_m1']:.4f}

## Interpretation

- The transport revision directly tests whether removing observation-process-heavy variables improves external transportability.
- T1 is the primary transport candidate because it does not rely on phenotype.
- T2 isolates whether phenotype still adds value once the model is already transport-constrained.
- A model should only be considered for deployment-oriented reporting if it materially improves eICU AUPRC and external calibration slope without catastrophic internal collapse.

## Recommendation

- Recommend transport model as main deployed model: **{recommend_main}**
- Practical reading:
  - If `yes`, the transport model is a strong candidate for deployment-oriented emphasis because it improves external discrimination and calibration.
  - If `no`, it is still worth keeping as a transport-focused supplementary model that explicitly shows the internal-versus-transport tradeoff.
"""
    return report


def main() -> None:
    train_inner, validation, test_df, external_df = load_frames()
    manifest = build_feature_manifest(pd.concat([train_inner, validation], ignore_index=True), external_df)
    t1 = fit_transport_model("T1", T1_FEATURES, train_inner, validation, test_df, external_df)
    t2 = fit_transport_model("T2", T2_FEATURES, train_inner, validation, test_df, external_df)
    m1_rows = load_m1_metrics()
    comparison = comparison_table(t1, t2, m1_rows)
    report = report_text(manifest, t1, t2, comparison)
    (OUTDIR / "Transport_Model_Report.md").write_text(report, encoding="utf-8-sig")
    print("Transport model experiment completed.")
    print(json.dumps(
        {
            "T1_external_auprc": t1.external_metrics["auprc_death"],
            "T2_external_auprc": t2.external_metrics["auprc_death"],
            "M1_external_auprc": comparison.loc[(comparison["model_name"] == "M1") & (comparison["dataset_name"] == "eicu_external"), "auprc_death"].iloc[0],
            "T1_external_slope": t1.external_metrics["calibration_slope_death"],
            "T2_external_slope": t2.external_metrics["calibration_slope_death"],
        },
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
