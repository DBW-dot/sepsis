from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "post_metre_recalibration"
OUTDIR.mkdir(parents=True, exist_ok=True)

POST_METRE_MAP = ROOT / "post_metre_selection" / "Downstream_Analysis_Model_Map.csv"
STEP7 = ROOT / "step7_main_modeling" / "output"
EXTERNAL_READY = STEP7 / "Model_Ready_eICU_External.parquet"
PRED_M1_EXTERNAL = STEP7 / "pred_main_eicu_external.parquet"
PRED_C1_EXTERNAL = STEP7 / "pred_C1_eicu_external.parquet"
MT3_BUNDLE = ROOT / "metre_transport" / "model_MT3_physiology_support_proxy.pkl"

DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
CLASSES = np.array([DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL], dtype=object)
RANDOM_SEED = 20260425
RECALIBRATION_FRACTION = 0.20

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


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def logit(p: np.ndarray) -> np.ndarray:
    p = clip_probs(p)
    return np.log(p / (1.0 - p))


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["patient_id", "stay_id", "t_pred"]].copy()
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


def load_mt3_predictions() -> pd.DataFrame:
    with MT3_BUNDLE.open("rb") as handle:
        bundle = pickle.load(handle)
    features = list(bundle["features"])
    pipe = bundle["pipeline"]
    temperature = float(bundle["temperature"])
    classes = np.array(bundle["classes"], dtype=object)
    schema = set(pq.ParquetFile(EXTERNAL_READY).schema.names)
    columns = sorted(
        set(
            [
                "patient_id",
                "stay_id",
                "t_pred",
                "event_type_24h",
                "phenotype_label",
                "is_sepsis_on_admission",
            ]
            + [f for f in features if f in schema]
            + SUPPORT_INPUT_COLUMNS
        )
    )
    df = pd.read_parquet(EXTERNAL_READY, columns=columns)
    proxy = build_support_proxy(df)
    df = df.merge(proxy[["stay_id", "t_pred"] + SUPPORT_MODEL_FEATURES], on=["stay_id", "t_pred"], how="left")
    logits = pipe.decision_function(df[features])
    probs = softmax(logits / temperature)
    class_to_idx = {label: idx for idx, label in enumerate(classes)}
    out = df[["patient_id", "stay_id", "t_pred", "event_type_24h", "phenotype_label", "is_sepsis_on_admission"]].copy()
    out["prob_death_raw"] = probs[:, class_to_idx[DEATH_LABEL]]
    out["prob_discharge_raw"] = probs[:, class_to_idx[DISCHARGE_LABEL]]
    out["prob_no_event_raw"] = probs[:, class_to_idx[NO_EVENT_LABEL]]
    out["model_name"] = "MT3_physiology_support_proxy"
    out.to_parquet(OUTDIR / "pred_MT3_eicu_external.parquet", index=False)
    return out


def load_step7_prediction(path: Path, model_name: str) -> pd.DataFrame:
    df = pd.read_parquet(
        path,
        columns=[
            "patient_id",
            "stay_id",
            "t_pred",
            "true_event_type_24h",
            "phenotype_label",
            "is_sepsis_on_admission",
            "predicted_prob_death_24h",
            "predicted_prob_discharge_24h",
            "predicted_prob_no_event_24h",
        ],
    ).copy()
    df = df.rename(
        columns={
            "true_event_type_24h": "event_type_24h",
            "predicted_prob_death_24h": "prob_death_raw",
            "predicted_prob_discharge_24h": "prob_discharge_raw",
            "predicted_prob_no_event_24h": "prob_no_event_raw",
        }
    )
    df["model_name"] = model_name
    return df


def make_patient_split(base: pd.DataFrame) -> pd.DataFrame:
    patient = (
        base.groupby("patient_id")
        .agg(
            has_death_window=("event_type_24h", lambda s: int((s == DEATH_LABEL).any())),
            phenotype_label=("phenotype_label", lambda s: s.mode(dropna=True).iloc[0] if len(s.mode(dropna=True)) else "missing"),
            is_sepsis_on_admission=("is_sepsis_on_admission", lambda s: int(round(float(pd.Series(s).dropna().mean()))) if pd.Series(s).dropna().size else -1),
            row_n=("event_type_24h", "size"),
            death_row_n=("event_type_24h", lambda s: int((s == DEATH_LABEL).sum())),
            stay_n=("stay_id", "nunique"),
        )
        .reset_index()
    )
    patient["stratum_raw"] = (
        patient["has_death_window"].astype(str)
        + "|"
        + patient["phenotype_label"].astype(str)
        + "|"
        + patient["is_sepsis_on_admission"].astype(str)
    )
    counts = patient["stratum_raw"].value_counts()
    patient["stratum"] = patient["stratum_raw"].where(patient["stratum_raw"].map(counts) >= 4, patient["has_death_window"].astype(str))
    recal, holdout = train_test_split(
        patient,
        test_size=1.0 - RECALIBRATION_FRACTION,
        random_state=RANDOM_SEED,
        stratify=patient["stratum"],
    )
    patient["split"] = np.where(patient["patient_id"].isin(set(recal["patient_id"])), "recalibration", "holdout")
    return patient


def summarize_split(base: pd.DataFrame, split: pd.DataFrame) -> pd.DataFrame:
    merged = base.merge(split[["patient_id", "split"]], on="patient_id", how="left")
    rows = []
    for split_name, part in merged.groupby("split"):
        y_death = (part["event_type_24h"] == DEATH_LABEL).astype(int)
        rows.append(
            {
                "split": split_name,
                "patient_n": int(part["patient_id"].nunique()),
                "stay_n": int(part["stay_id"].nunique()),
                "row_n": int(len(part)),
                "death_row_n": int(y_death.sum()),
                "death_row_rate": float(y_death.mean()),
                "phenotype_1_rate": float((part["phenotype_label"] == "Phenotype_1").mean()),
                "phenotype_2_rate": float((part["phenotype_label"] == "Phenotype_2").mean()),
                "phenotype_3_rate": float((part["phenotype_label"] == "Phenotype_3").mean()),
                "sepsis_on_admission_rate": float(part["is_sepsis_on_admission"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("split").reset_index(drop=True)


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = clip_probs(probs)
    if np.unique(y_binary).size < 2:
        return float("nan"), float("nan")
    logits = logit(probs).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray) -> float:
    onehot = np.zeros_like(probs)
    idx = {label: pos for pos, label in enumerate(CLASSES)}
    for row_idx, label in enumerate(y_true):
        onehot[row_idx, idx[label]] = 1.0
    return float(np.mean(np.sum((onehot - probs) ** 2, axis=1)))


def ece_binary(y_binary: np.ndarray, probs: np.ndarray, n_bins: int = 10) -> float:
    y_binary = np.asarray(y_binary, dtype=int)
    probs = np.asarray(probs, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        if i == n_bins - 1:
            mask = (probs >= edges[i]) & (probs <= edges[i + 1])
        else:
            mask = (probs >= edges[i]) & (probs < edges[i + 1])
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(y_binary[mask].mean()) - float(probs[mask].mean()))
    return ece


def evaluate(y_true: np.ndarray, death_probs: np.ndarray, discharge_probs: np.ndarray, no_event_probs: np.ndarray) -> dict[str, float]:
    y_death = (y_true == DEATH_LABEL).astype(int)
    intercept, slope = calibration_intercept_slope(y_death, death_probs)
    probs_3 = np.column_stack([discharge_probs, death_probs, no_event_probs])
    return {
        "row_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()),
        "auroc_death": float(roc_auc_score(y_death, death_probs)),
        "auprc_death": float(average_precision_score(y_death, death_probs)),
        "death_brier": float(brier_score_loss(y_death, death_probs)),
        "multiclass_brier": multiclass_brier(y_true, probs_3),
        "calibration_intercept_death": intercept,
        "calibration_slope_death": slope,
        "ece_death_10bin": ece_binary(y_death, death_probs, n_bins=10),
        "mean_predicted_death": float(np.mean(death_probs)),
        "median_predicted_death": float(np.median(death_probs)),
        "p90_predicted_death": float(np.quantile(death_probs, 0.90)),
        "p99_predicted_death": float(np.quantile(death_probs, 0.99)),
    }


def fit_intercept_only(y_binary: np.ndarray, raw_probs: np.ndarray) -> dict[str, float]:
    offset = logit(raw_probs)
    intercept = 0.0
    for _ in range(100):
        pred = sigmoid(intercept + offset)
        gradient = np.sum(y_binary - pred)
        hessian = -np.sum(pred * (1.0 - pred))
        step = gradient / hessian
        intercept -= step
        if abs(step) < 1e-8:
            break
    return {"intercept": float(intercept)}


def apply_intercept_only(raw_probs: np.ndarray, params: dict[str, float]) -> np.ndarray:
    return clip_probs(sigmoid(logit(raw_probs) + params["intercept"]))


def fit_logistic(y_binary: np.ndarray, raw_probs: np.ndarray) -> dict[str, float]:
    x = logit(raw_probs).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(x, y_binary)
    return {"intercept": float(model.intercept_[0]), "slope": float(model.coef_[0][0])}


def apply_logistic(raw_probs: np.ndarray, params: dict[str, float]) -> np.ndarray:
    return clip_probs(sigmoid(params["intercept"] + params["slope"] * logit(raw_probs)))


def fit_isotonic(y_binary: np.ndarray, raw_probs: np.ndarray) -> IsotonicRegression:
    model = IsotonicRegression(y_min=1e-6, y_max=1.0 - 1e-6, out_of_bounds="clip")
    model.fit(raw_probs, y_binary)
    return model


def fit_temperature(y_binary: np.ndarray, raw_probs: np.ndarray) -> dict[str, float]:
    logits = logit(raw_probs)
    best_t = 1.0
    best_brier = np.inf
    for temp in list(np.linspace(0.3, 3.0, 28)) + [3.5, 4.0, 5.0, 6.0]:
        probs = sigmoid(logits / temp)
        brier = brier_score_loss(y_binary, probs)
        if brier < best_brier:
            best_brier = brier
            best_t = float(temp)
    return {"temperature": best_t}


def apply_temperature(raw_probs: np.ndarray, params: dict[str, float]) -> np.ndarray:
    return clip_probs(sigmoid(logit(raw_probs) / params["temperature"]))


def rebalance(death_probs: np.ndarray, raw_discharge: np.ndarray, raw_no_event: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    remainder = 1.0 - death_probs
    raw_remainder = raw_discharge + raw_no_event
    safe = raw_remainder > 1e-12
    discharge = np.zeros_like(death_probs)
    no_event = np.zeros_like(death_probs)
    discharge[safe] = remainder[safe] * raw_discharge[safe] / raw_remainder[safe]
    no_event[safe] = remainder[safe] * raw_no_event[safe] / raw_remainder[safe]
    discharge[~safe] = 0.5 * remainder[~safe]
    no_event[~safe] = 0.5 * remainder[~safe]
    return discharge, no_event


def calibration_curve_rows(df: pd.DataFrame, model_name: str, method: str) -> pd.DataFrame:
    y = (df["event_type_24h"] == DEATH_LABEL).astype(int).to_numpy()
    probs = df["prob_death_calibrated"].to_numpy()
    bins = pd.qcut(pd.Series(probs), q=10, duplicates="drop")
    curve = (
        pd.DataFrame({"y": y, "p": probs, "bin": bins})
        .groupby("bin", observed=True)
        .agg(row_n=("y", "size"), observed_death_rate=("y", "mean"), mean_predicted_death=("p", "mean"))
        .reset_index()
    )
    curve["model_name"] = model_name
    curve["calibration_method"] = method
    curve["bin_label"] = curve["bin"].astype(str)
    return curve[["model_name", "calibration_method", "bin_label", "row_n", "mean_predicted_death", "observed_death_rate"]]


def run_recalibration_for_model(model_df: pd.DataFrame, split: pd.DataFrame) -> tuple[list[dict[str, float | str]], list[pd.DataFrame]]:
    model_name = str(model_df["model_name"].iloc[0])
    df = model_df.merge(split[["patient_id", "split"]], on="patient_id", how="left")
    recal = df[df["split"] == "recalibration"].copy()
    holdout = df[df["split"] == "holdout"].copy()
    y_recal = (recal["event_type_24h"] == DEATH_LABEL).astype(int).to_numpy()
    raw_recal = recal["prob_death_raw"].to_numpy()
    methods: dict[str, object | None] = {
        "raw": None,
        "intercept_only": fit_intercept_only(y_recal, raw_recal),
        "logistic_recalibration": fit_logistic(y_recal, raw_recal),
        "isotonic": fit_isotonic(y_recal, raw_recal),
        "temperature_scaling": fit_temperature(y_recal, raw_recal),
    }
    rows = []
    curves = []
    for method, fitted in methods.items():
        if method == "raw":
            death = holdout["prob_death_raw"].to_numpy()
        elif method == "intercept_only":
            death = apply_intercept_only(holdout["prob_death_raw"].to_numpy(), fitted)  # type: ignore[arg-type]
        elif method == "logistic_recalibration":
            death = apply_logistic(holdout["prob_death_raw"].to_numpy(), fitted)  # type: ignore[arg-type]
        elif method == "isotonic":
            death = clip_probs(fitted.predict(holdout["prob_death_raw"].to_numpy()))  # type: ignore[union-attr]
        elif method == "temperature_scaling":
            death = apply_temperature(holdout["prob_death_raw"].to_numpy(), fitted)  # type: ignore[arg-type]
        else:
            raise ValueError(method)
        discharge, no_event = rebalance(
            death,
            holdout["prob_discharge_raw"].to_numpy(),
            holdout["prob_no_event_raw"].to_numpy(),
        )
        metrics = evaluate(holdout["event_type_24h"].to_numpy(), death, discharge, no_event)
        metrics.update(
            {
                "model_name": model_name,
                "calibration_method": method,
                "recalibration_patient_n": float(recal["patient_id"].nunique()),
                "holdout_patient_n": float(holdout["patient_id"].nunique()),
                "method_parameters_json": json.dumps(fitted if isinstance(fitted, dict) else {}, ensure_ascii=False),
            }
        )
        rows.append(metrics)
        curve_df = holdout[["event_type_24h"]].copy()
        curve_df["prob_death_calibrated"] = death
        curves.append(calibration_curve_rows(curve_df, model_name, method))
    return rows, curves


def write_targets() -> None:
    model_map = pd.read_csv(POST_METRE_MAP)
    target = model_map.loc[model_map["downstream_analysis"] == "External recalibration", "primary_model_to_use"].iloc[0]
    text = f"""# Recalibration Targets

## Frozen calibration target

- Best transport model: `{target}`.
- Model bundle: `{MT3_BUNDLE}`.
- Generated prediction file for this run: `post_metre_recalibration/pred_MT3_eicu_external.parquet`.

## Comparators

- M1: `{PRED_M1_EXTERNAL}`.
- C1: `{PRED_C1_EXTERNAL}`.

## Boundary

- No model retraining was performed.
- eICU was used only for local recalibration fitting and untouched hold-out evaluation.
- Death probability was calibrated first; discharge/no-event probabilities were rescaled proportionally to keep three-class probabilities coherent.
"""
    (OUTDIR / "Recalibration_Targets.md").write_text(text, encoding="utf-8")


def write_split_report(split: pd.DataFrame, summary: pd.DataFrame) -> None:
    overlap = bool(
        set(split.loc[split["split"] == "recalibration", "patient_id"]).intersection(
            set(split.loc[split["split"] == "holdout", "patient_id"])
        )
    )
    text = f"""# eICU Recalibration Split Report

## Design

- Split level: patient-level.
- Random seed: `{RANDOM_SEED}`.
- Recalibration fraction: `{RECALIBRATION_FRACTION:.2f}`.
- Stratification fields: any death window, modal phenotype label, modal `is_sepsis_on_admission`.

## Verification

- Patient overlap between recalibration and hold-out: `{overlap}`.
- Split summary:

```json
{json.dumps(summary.to_dict(orient='records'), ensure_ascii=False, indent=2)}
```
"""
    (OUTDIR / "eicu_recalibration_split_report.md").write_text(text, encoding="utf-8")


def write_methods_summary() -> None:
    text = """# Recalibration Methods Summary

## Methods tested

- `raw`: original uncalibrated probabilities.
- `intercept_only`: logistic intercept update with slope fixed at 1.
- `logistic_recalibration`: logistic recalibration with intercept and slope.
- `isotonic`: monotonic non-parametric calibration.
- `temperature_scaling`: one-parameter logit temperature scaling optimized on recalibration death Brier.

## Competing-risk probability handling

The calibration target is `predicted_prob_death_24h`. After death-risk recalibration, the remaining probability mass is assigned to alive discharge and no event in proportion to their original probabilities. This preserves probability sums while avoiding three separate one-vs-rest calibrators that could break the competing-risk simplex.
"""
    (OUTDIR / "recalibration_methods_summary.md").write_text(text, encoding="utf-8")


def write_report(results: pd.DataFrame, split_summary: pd.DataFrame) -> None:
    best = (
        results[results["model_name"] == "MT3_physiology_support_proxy"]
        .sort_values(["death_brier", "calibration_slope_distance", "auprc_death"], ascending=[True, True, False])
        .iloc[0]
    )
    raw = results[
        (results["model_name"] == "MT3_physiology_support_proxy") & (results["calibration_method"] == "raw")
    ].iloc[0]
    text = f"""# Post-METRE Recalibration Report

## Split summary

```json
{json.dumps(split_summary.to_dict(orient='records'), ensure_ascii=False, indent=2)}
```

## MT3 raw vs best recalibrated hold-out result

- Raw MT3: AUROC={raw['auroc_death']:.4f}, AUPRC={raw['auprc_death']:.4f}, death Brier={raw['death_brier']:.4f}, multiclass Brier={raw['multiclass_brier']:.4f}, slope={raw['calibration_slope_death']:.4f}, ECE={raw['ece_death_10bin']:.4f}.
- Best MT3 method by death Brier: `{best['calibration_method']}`.
- Recalibrated MT3: AUROC={best['auroc_death']:.4f}, AUPRC={best['auprc_death']:.4f}, death Brier={best['death_brier']:.4f}, multiclass Brier={best['multiclass_brier']:.4f}, slope={best['calibration_slope_death']:.4f}, ECE={best['ece_death_10bin']:.4f}.

## Interpretation

- Recalibration is evaluated only on the hold-out subset.
- AUROC should remain mostly stable for monotonic calibrators; AUPRC may change slightly for isotonic because ties and stepwise mapping can affect ranking.
- The deployment question is mainly whether Brier, ECE, and calibration slope improve without damaging AUPRC.
"""
    (OUTDIR / "Post_METRE_Recalibration_Report.md").write_text(text, encoding="utf-8")


def write_signoff(results: pd.DataFrame) -> None:
    mt3 = results[results["model_name"] == "MT3_physiology_support_proxy"].copy()
    raw = mt3[mt3["calibration_method"] == "raw"].iloc[0]
    best = mt3.sort_values(["death_brier", "calibration_slope_distance", "auprc_death"], ascending=[True, True, False]).iloc[0]
    slope_distance_delta = abs(raw["calibration_slope_death"] - 1.0) - abs(best["calibration_slope_death"] - 1.0)
    slope_materially_improved = slope_distance_delta >= 0.05
    brier_improved = best["death_brier"] < raw["death_brier"]
    ece_improved = best["ece_death_10bin"] < raw["ece_death_10bin"]
    auprc_ok = best["auprc_death"] >= raw["auprc_death"] - 1e-6
    use_for_dca = bool(brier_improved and ece_improved and auprc_ok)
    text = f"""# Recalibrated Model Sign-off

## Required decisions

1. Recalibration materially improved calibration slope: `{slope_materially_improved}`.
   - Raw slope was already near 1, so the main gain is calibration level rather than slope.
2. Recalibration improved death Brier: `{brier_improved}`.
3. Recalibration preserved or improved AUPRC: `{auprc_ok}`.
4. Uncalibrated and recalibrated external results should be shown side by side: `True`.
5. Downstream DCA should use recalibrated probabilities: `{use_for_dca}`.

## Frozen recommendation

- Best method: `{best['calibration_method']}`.
- Raw MT3 AUROC/AUPRC/slope: {raw['auroc_death']:.4f} / {raw['auprc_death']:.4f} / {raw['calibration_slope_death']:.4f}.
- Recalibrated MT3 AUROC/AUPRC/slope: {best['auroc_death']:.4f} / {best['auprc_death']:.4f} / {best['calibration_slope_death']:.4f}.
- Raw vs recalibrated death Brier/ECE: {raw['death_brier']:.4f}/{raw['ece_death_10bin']:.4f} -> {best['death_brier']:.4f}/{best['ece_death_10bin']:.4f}.
- The model should be described as requiring local recalibration before deployment because the recalibration step is now part of the externally usable risk framework.
"""
    (OUTDIR / "Recalibrated_Model_Signoff.md").write_text(text, encoding="utf-8")


def main() -> None:
    write_targets()
    mt3 = load_mt3_predictions()
    m1 = load_step7_prediction(PRED_M1_EXTERNAL, "M1_original_rich")
    c1 = load_step7_prediction(PRED_C1_EXTERNAL, "C1_dynamic_SOFA")
    split = make_patient_split(mt3)
    split.to_csv(OUTDIR / "eicu_recalibration_split.csv", index=False, encoding="utf-8-sig")
    split_summary = summarize_split(mt3, split)
    write_split_report(split, split_summary)
    write_methods_summary()

    rows = []
    curves = []
    for model_df in [mt3, m1, c1]:
        model_rows, model_curves = run_recalibration_for_model(model_df, split)
        rows.extend(model_rows)
        curves.extend(model_curves)
    results = pd.DataFrame(rows)
    raw_ref = results[results["calibration_method"] == "raw"][
        ["model_name", "auroc_death", "auprc_death", "death_brier", "multiclass_brier", "calibration_slope_death", "ece_death_10bin"]
    ].rename(
        columns={
            "auroc_death": "raw_auroc_death",
            "auprc_death": "raw_auprc_death",
            "death_brier": "raw_death_brier",
            "multiclass_brier": "raw_multiclass_brier",
            "calibration_slope_death": "raw_calibration_slope_death",
            "ece_death_10bin": "raw_ece_death_10bin",
        }
    )
    results = results.merge(raw_ref, on="model_name", how="left")
    results["delta_auroc_vs_raw"] = results["auroc_death"] - results["raw_auroc_death"]
    results["delta_auprc_vs_raw"] = results["auprc_death"] - results["raw_auprc_death"]
    results["delta_death_brier_vs_raw"] = results["death_brier"] - results["raw_death_brier"]
    results["delta_multiclass_brier_vs_raw"] = results["multiclass_brier"] - results["raw_multiclass_brier"]
    results["delta_slope_vs_raw"] = results["calibration_slope_death"] - results["raw_calibration_slope_death"]
    results["delta_ece_vs_raw"] = results["ece_death_10bin"] - results["raw_ece_death_10bin"]
    results["calibration_slope_distance"] = (results["calibration_slope_death"] - 1.0).abs()
    results.to_csv(OUTDIR / "Post_METRE_Recalibration_Results.csv", index=False, encoding="utf-8-sig")
    pd.concat(curves, ignore_index=True).to_csv(OUTDIR / "Post_METRE_Calibration_Curve_Data.csv", index=False, encoding="utf-8-sig")
    write_report(results, split_summary)
    write_signoff(results)

    mt3 = results[results["model_name"] == "MT3_physiology_support_proxy"].copy()
    best = mt3.sort_values(["death_brier", "calibration_slope_distance", "auprc_death"], ascending=[True, True, False]).iloc[0]
    raw = mt3[mt3["calibration_method"] == "raw"].iloc[0]
    print(
        json.dumps(
            {
                "best_method": best["calibration_method"],
                "raw_auroc": raw["auroc_death"],
                "raw_auprc": raw["auprc_death"],
                "raw_slope": raw["calibration_slope_death"],
                "calibrated_auroc": best["auroc_death"],
                "calibrated_auprc": best["auprc_death"],
                "calibrated_slope": best["calibration_slope_death"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
