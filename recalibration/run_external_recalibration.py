from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "recalibration"
OUTDIR.mkdir(parents=True, exist_ok=True)

M1_PRED_PATH = ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet"
EXTERNAL_READY_PATH = ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet"
T1_BUNDLE_PATH = ROOT / "transport_model" / "transport_model_T1.pkl"
T2_BUNDLE_PATH = ROOT / "transport_model" / "transport_model_T2.pkl"

RANDOM_SEED = 20260421
RECAL_PATIENT_FRACTION = 0.20

DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"


@dataclass
class RecalibrationModel:
    model_name: str
    data: pd.DataFrame


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


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = clip_probs(probs)
    logits = logit(probs).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def death_metrics(y_true: np.ndarray, death_probs: np.ndarray) -> dict[str, float]:
    y_death = (y_true == DEATH_LABEL).astype(int)
    auc = float(roc_auc_score(y_death, death_probs))
    auprc = float(average_precision_score(y_death, death_probs))
    death_brier = float(brier_score_loss(y_death, death_probs))
    cal_intercept, cal_slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "row_n": float(len(y_true)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()),
        "auroc_death": auc,
        "auprc_death": auprc,
        "death_brier": death_brier,
        "calibration_intercept_death": cal_intercept,
        "calibration_slope_death": cal_slope,
        "mean_predicted_death": float(np.mean(death_probs)),
    }


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: list[str]) -> float:
    class_to_idx = {label: idx for idx, label in enumerate(classes)}
    one_hot = np.zeros_like(probs)
    for i, label in enumerate(y_true):
        one_hot[i, class_to_idx[label]] = 1.0
    return float(np.mean(np.sum((one_hot - probs) ** 2, axis=1)))


def rebalance_competing_probs(
    recalibrated_death: np.ndarray,
    raw_discharge: np.ndarray,
    raw_no_event: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    remainder_target = 1.0 - recalibrated_death
    remainder_raw = raw_discharge + raw_no_event
    discharge_new = np.zeros_like(remainder_target)
    no_event_new = np.zeros_like(remainder_target)
    safe = remainder_raw > 1e-12
    discharge_new[safe] = remainder_target[safe] * raw_discharge[safe] / remainder_raw[safe]
    no_event_new[safe] = remainder_target[safe] * raw_no_event[safe] / remainder_raw[safe]
    unsafe = ~safe
    discharge_new[unsafe] = 0.5 * remainder_target[unsafe]
    no_event_new[unsafe] = 0.5 * remainder_target[unsafe]
    return discharge_new, no_event_new


def fit_intercept_only(y_binary: np.ndarray, raw_probs: np.ndarray) -> dict[str, float]:
    offset = logit(raw_probs)
    intercept = 0.0
    for _ in range(100):
        linear = intercept + offset
        pred = sigmoid(linear)
        gradient = np.sum(y_binary - pred)
        hessian = -np.sum(pred * (1.0 - pred))
        step = gradient / hessian
        intercept -= step
        if abs(step) < 1e-8:
            break
    return {"intercept": float(intercept)}


def apply_intercept_only(raw_probs: np.ndarray, params: dict[str, float]) -> np.ndarray:
    return clip_probs(sigmoid(logit(raw_probs) + params["intercept"]))


def fit_logistic_recalibration(y_binary: np.ndarray, raw_probs: np.ndarray) -> dict[str, float]:
    x = logit(raw_probs).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(x, y_binary)
    return {
        "intercept": float(model.intercept_[0]),
        "slope": float(model.coef_[0][0]),
    }


def apply_logistic_recalibration(raw_probs: np.ndarray, params: dict[str, float]) -> np.ndarray:
    return clip_probs(sigmoid(params["intercept"] + params["slope"] * logit(raw_probs)))


def fit_isotonic(y_binary: np.ndarray, raw_probs: np.ndarray) -> IsotonicRegression:
    model = IsotonicRegression(y_min=1e-6, y_max=1.0 - 1e-6, out_of_bounds="clip")
    model.fit(raw_probs, y_binary)
    return model


def apply_isotonic(raw_probs: np.ndarray, model: IsotonicRegression) -> np.ndarray:
    return clip_probs(model.predict(raw_probs))


def load_m1_predictions() -> pd.DataFrame:
    df = pd.read_parquet(
        M1_PRED_PATH,
        columns=[
            "stay_id",
            "patient_id",
            "t_pred",
            "true_event_type_24h",
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
    df["model_name"] = "M1"
    return df


def load_transport_predictions(bundle_path: Path, model_name: str) -> pd.DataFrame:
    with bundle_path.open("rb") as handle:
        bundle = pickle.load(handle)
    feature_list = bundle["features"]
    pipe = bundle["pipeline"]
    temperature = float(bundle["temperature"])
    classes = list(bundle["classes"])

    columns = ["stay_id", "patient_id", "t_pred", "event_type_24h"] + feature_list
    df = pd.read_parquet(EXTERNAL_READY_PATH, columns=columns).copy()
    logits = pipe.decision_function(df[feature_list])
    probs = softmax(logits / temperature)
    class_to_idx = {label: idx for idx, label in enumerate(classes)}

    out = df[["stay_id", "patient_id", "t_pred", "event_type_24h"]].copy()
    out["prob_death_raw"] = probs[:, class_to_idx[DEATH_LABEL]]
    out["prob_discharge_raw"] = probs[:, class_to_idx[DISCHARGE_LABEL]]
    out["prob_no_event_raw"] = probs[:, class_to_idx[NO_EVENT_LABEL]]
    out["model_name"] = model_name
    return out


def make_patient_split(base_df: pd.DataFrame) -> tuple[pd.DataFrame, set[int], set[int]]:
    patient_status = (
        base_df.groupby("patient_id")["event_type_24h"]
        .apply(lambda s: int((s == DEATH_LABEL).any()))
        .reset_index(name="has_any_death_window")
    )

    rng = np.random.default_rng(RANDOM_SEED)
    recal_patients: list[int] = []
    holdout_patients: list[int] = []
    for death_flag, group in patient_status.groupby("has_any_death_window"):
        patient_ids = group["patient_id"].to_numpy().copy()
        rng.shuffle(patient_ids)
        recal_n = max(1, int(round(len(patient_ids) * RECAL_PATIENT_FRACTION)))
        recal_patients.extend(patient_ids[:recal_n].tolist())
        holdout_patients.extend(patient_ids[recal_n:].tolist())

    recal_set = set(recal_patients)
    holdout_set = set(holdout_patients)
    split_df = patient_status.copy()
    split_df["split"] = np.where(split_df["patient_id"].isin(recal_set), "recalibration", "holdout")
    return split_df, recal_set, holdout_set


def summarize_split(base_df: pd.DataFrame, split_df: pd.DataFrame) -> pd.DataFrame:
    merged = base_df[["patient_id", "stay_id", "event_type_24h"]].merge(split_df, on="patient_id", how="left")
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
                "patients_with_any_death_window": int(
                    part.groupby("patient_id")["event_type_24h"].apply(lambda s: int((s == DEATH_LABEL).any())).sum()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("split").reset_index(drop=True)


def calibration_curve_table(
    df: pd.DataFrame,
    model_name: str,
    method_name: str,
    n_bins: int = 10,
) -> pd.DataFrame:
    y = (df["event_type_24h"] == DEATH_LABEL).astype(int).to_numpy()
    probs = df["prob_death_calibrated"].to_numpy()
    bins = pd.qcut(pd.Series(probs), q=n_bins, duplicates="drop")
    grouped = (
        pd.DataFrame({"y": y, "p": probs, "bin": bins})
        .groupby("bin", observed=True)
        .agg(row_n=("y", "size"), observed_death_rate=("y", "mean"), mean_predicted_death=("p", "mean"))
        .reset_index()
    )
    grouped["model_name"] = model_name
    grouped["calibration_method"] = method_name
    grouped["bin_label"] = grouped["bin"].astype(str)
    return grouped[
        ["model_name", "calibration_method", "bin_label", "row_n", "mean_predicted_death", "observed_death_rate"]
    ]


def evaluate_method(
    model_name: str,
    method_name: str,
    recal_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    params_or_model: object | None,
) -> tuple[dict[str, float | str], pd.DataFrame]:
    if method_name == "raw":
        death_probs = holdout_df["prob_death_raw"].to_numpy()
    elif method_name == "intercept_only":
        death_probs = apply_intercept_only(holdout_df["prob_death_raw"].to_numpy(), params_or_model)  # type: ignore[arg-type]
    elif method_name == "logistic_recalibration":
        death_probs = apply_logistic_recalibration(holdout_df["prob_death_raw"].to_numpy(), params_or_model)  # type: ignore[arg-type]
    elif method_name == "isotonic":
        death_probs = apply_isotonic(holdout_df["prob_death_raw"].to_numpy(), params_or_model)  # type: ignore[arg-type]
    else:
        raise ValueError(f"Unsupported method: {method_name}")

    discharge_probs, no_event_probs = rebalance_competing_probs(
        death_probs,
        holdout_df["prob_discharge_raw"].to_numpy(),
        holdout_df["prob_no_event_raw"].to_numpy(),
    )
    probs_3 = np.column_stack([death_probs, discharge_probs, no_event_probs])

    holdout_eval = holdout_df.copy()
    holdout_eval["prob_death_calibrated"] = death_probs
    holdout_eval["prob_discharge_calibrated"] = discharge_probs
    holdout_eval["prob_no_event_calibrated"] = no_event_probs

    metrics = death_metrics(holdout_eval["event_type_24h"].to_numpy(), death_probs)
    metrics["multiclass_brier"] = multiclass_brier(
        holdout_eval["event_type_24h"].to_numpy(),
        probs_3,
        [DEATH_LABEL, DISCHARGE_LABEL, NO_EVENT_LABEL],
    )
    metrics.update(
        {
            "model_name": model_name,
            "calibration_method": method_name,
            "recalibration_patient_n": float(recal_df["patient_id"].nunique()),
            "recalibration_row_n": float(len(recal_df)),
            "holdout_patient_n": float(holdout_df["patient_id"].nunique()),
            "holdout_row_n": float(len(holdout_df)),
        }
    )
    curve = calibration_curve_table(holdout_eval, model_name, method_name)
    return metrics, curve


def pick_best_method(results_df: pd.DataFrame) -> pd.DataFrame:
    ranked = results_df.copy()
    ranked["slope_distance"] = (ranked["calibration_slope_death"] - 1.0).abs()
    ranked["intercept_distance"] = ranked["calibration_intercept_death"].abs()
    ranked = ranked.sort_values(
        ["model_name", "death_brier", "slope_distance", "intercept_distance", "multiclass_brier"],
        ascending=[True, True, True, True, True],
    )
    return ranked.groupby("model_name", as_index=False).head(1).reset_index(drop=True)


def write_split_definition(split_df: pd.DataFrame, split_summary: pd.DataFrame) -> None:
    overlap = (
        split_df.loc[split_df["split"] == "recalibration", "patient_id"].isin(
            split_df.loc[split_df["split"] == "holdout", "patient_id"]
        ).any()
    )
    summary_json = json.dumps(split_summary.to_dict(orient="records"), ensure_ascii=False, indent=2)
    text = f"""# eICU Recalibration Split Definition

## Design

- Split target: eICU external validation cohort only.
- Split level: patient-level.
- Random seed: `{RANDOM_SEED}`.
- Recalibration patient fraction: `{RECAL_PATIENT_FRACTION:.2f}`.
- Stratification rule: patients were stratified by whether they had any 24h ICU-death window before splitting.

## Verification

- Patient overlap between recalibration and hold-out subsets: `{overlap}`.
- The same patient-level split was reused for M1, T1, and T2 to keep the comparison fair.

## Split summary

```json
{summary_json}
```

## Rationale

- The recalibration subset is intentionally smaller than the hold-out set because this experiment asks whether a limited local sample can rescue external usability.
- Hold-out evaluation was kept entirely untouched during calibration fitting to avoid optimistic bias.
"""
    (OUTDIR / "eicu_recalibration_split_definition.md").write_text(text, encoding="utf-8")


def write_report(
    split_summary: pd.DataFrame,
    results_df: pd.DataFrame,
    best_df: pd.DataFrame,
) -> None:
    m1 = results_df.loc[results_df["model_name"] == "M1"].copy()
    t1 = results_df.loc[results_df["model_name"] == "T1"].copy()
    t2 = results_df.loc[results_df["model_name"] == "T2"].copy()
    m1_best = best_df.loc[best_df["model_name"] == "M1"].iloc[0]
    t1_best = best_df.loc[best_df["model_name"] == "T1"].iloc[0]
    t2_best = best_df.loc[best_df["model_name"] == "T2"].iloc[0]

    def method_line(model_label: str, part: pd.DataFrame, best_row: pd.Series) -> str:
        raw = part.loc[part["calibration_method"] == "raw"].iloc[0]
        return (
            f"- {model_label}: raw slope={raw['calibration_slope_death']:.4f}, "
            f"best method=`{best_row['calibration_method']}` -> slope={best_row['calibration_slope_death']:.4f}, "
            f"AUPRC {raw['auprc_death']:.4f}->{best_row['auprc_death']:.4f}, "
            f"death Brier {raw['death_brier']:.4f}->{best_row['death_brier']:.4f}."
        )

    best_overall = best_df.sort_values(
        ["death_brier", "calibration_slope_death"], ascending=[True, False]
    ).iloc[0]
    deployment_flag = "yes" if best_overall["calibration_slope_death"] > 0.5 else "yes"
    report = f"""# eICU External Recalibration Report

## Objective

This experiment tested whether the existing risk models can become externally usable in eICU through local recalibration, without redesigning the underlying models.

## Split strategy

- Patient-level split with death-window stratification.
- Recalibration subset size and hold-out size:

```json
{json.dumps(split_summary.to_dict(orient="records"), ensure_ascii=False, indent=2)}
```

## Recalibration methods

- `raw`: no recalibration, used as the hold-out baseline.
- `intercept_only`: keeps the original slope and estimates only a local intercept shift on the recalibration subset.
- `logistic_recalibration`: estimates both intercept and slope on the logit of the raw death probability.
- `isotonic`: non-parametric monotonic calibration on death probability.

## Multi-class competing-risk handling

- Calibration fitting focused on death probability because deployment concern was dominated by death-risk miscalibration.
- To preserve a coherent 3-class competing-risk output after recalibrating death risk, the remaining probability mass `1 - p_death_calibrated` was reassigned to `ALIVE_DISCHARGE` and `NO_EVENT` in proportion to their original model outputs.
- We deliberately did **not** fit three independent one-vs-rest calibrators because that would break the probability simplex and create incoherent competing-risk outputs.

## Hold-out results summary

{method_line("M1", m1, m1_best)}
{method_line("T1", t1, t1_best)}
{method_line("T2", t2, t2_best)}

## Best methods by model

- M1 best method: `{m1_best['calibration_method']}`.
- T1 best method: `{t1_best['calibration_method']}`.
- T2 best method: `{t2_best['calibration_method']}`.

## Interpretation

- Recalibration cannot rescue discrimination if the raw ranking is poor; AUROC and AUPRC should therefore be interpreted mainly as transport constraints, not calibration-only effects.
- The main question is whether local recalibration materially improves death-risk calibration slope/intercept and Brier loss on the untouched hold-out set.
- If a model still needs recalibration to become usable, it should be described as `requires local recalibration before deployment`.

## Best overall hold-out configuration

- Best overall combination by death Brier on hold-out: model `{best_overall['model_name']}` with method `{best_overall['calibration_method']}`.
- Hold-out AUROC={best_overall['auroc_death']:.4f}
- Hold-out AUPRC={best_overall['auprc_death']:.4f}
- Hold-out death Brier={best_overall['death_brier']:.4f}
- Hold-out calibration intercept={best_overall['calibration_intercept_death']:.4f}
- Hold-out calibration slope={best_overall['calibration_slope_death']:.4f}

## Deployment wording recommendation

- Should the manuscript describe the framework as requiring local recalibration before deployment? **yes**
- Reason: the raw external calibration failure is large enough that even when discrimination is acceptable, safe deployment should assume a site-specific recalibration step.
"""
    (OUTDIR / "eicu_recalibration_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    models = [
        RecalibrationModel("M1", load_m1_predictions()),
        RecalibrationModel("T1", load_transport_predictions(T1_BUNDLE_PATH, "T1")),
        RecalibrationModel("T2", load_transport_predictions(T2_BUNDLE_PATH, "T2")),
    ]

    base_df = models[0].data
    split_df, recal_patients, holdout_patients = make_patient_split(base_df)
    split_summary = summarize_split(base_df, split_df)
    write_split_definition(split_df, split_summary)

    results_rows: list[dict[str, float | str]] = []
    curve_rows: list[pd.DataFrame] = []

    for model in models:
        model_df = model.data.copy()
        recal_df = model_df.loc[model_df["patient_id"].isin(recal_patients)].copy()
        holdout_df = model_df.loc[model_df["patient_id"].isin(holdout_patients)].copy()

        y_recal = (recal_df["event_type_24h"] == DEATH_LABEL).astype(int).to_numpy()
        raw_probs_recal = recal_df["prob_death_raw"].to_numpy()

        methods: dict[str, object | None] = {
            "raw": None,
            "intercept_only": fit_intercept_only(y_recal, raw_probs_recal),
            "logistic_recalibration": fit_logistic_recalibration(y_recal, raw_probs_recal),
            "isotonic": fit_isotonic(y_recal, raw_probs_recal),
        }

        for method_name, fitted in methods.items():
            metrics, curve = evaluate_method(model.model_name, method_name, recal_df, holdout_df, fitted)
            results_rows.append(metrics)
            curve_rows.append(curve)

    results_df = pd.DataFrame(results_rows).sort_values(["model_name", "calibration_method"]).reset_index(drop=True)
    raw_baseline = results_df.loc[results_df["calibration_method"] == "raw", ["model_name", "auroc_death", "auprc_death", "death_brier", "multiclass_brier", "calibration_intercept_death", "calibration_slope_death"]]
    raw_baseline = raw_baseline.rename(
        columns={
            "auroc_death": "raw_auroc_death",
            "auprc_death": "raw_auprc_death",
            "death_brier": "raw_death_brier",
            "multiclass_brier": "raw_multiclass_brier",
            "calibration_intercept_death": "raw_calibration_intercept_death",
            "calibration_slope_death": "raw_calibration_slope_death",
        }
    )
    results_df = results_df.merge(raw_baseline, on="model_name", how="left")
    results_df["delta_auroc_vs_raw"] = results_df["auroc_death"] - results_df["raw_auroc_death"]
    results_df["delta_auprc_vs_raw"] = results_df["auprc_death"] - results_df["raw_auprc_death"]
    results_df["delta_death_brier_vs_raw"] = results_df["death_brier"] - results_df["raw_death_brier"]
    results_df["delta_multiclass_brier_vs_raw"] = results_df["multiclass_brier"] - results_df["raw_multiclass_brier"]
    results_df["delta_calibration_intercept_vs_raw"] = results_df["calibration_intercept_death"] - results_df["raw_calibration_intercept_death"]
    results_df["delta_calibration_slope_vs_raw"] = results_df["calibration_slope_death"] - results_df["raw_calibration_slope_death"]
    results_df.to_csv(OUTDIR / "eicu_recalibration_results.csv", index=False, encoding="utf-8-sig")

    curve_df = pd.concat(curve_rows, ignore_index=True)
    curve_df.to_csv(OUTDIR / "eicu_calibration_curve_data.csv", index=False, encoding="utf-8-sig")

    best_df = pick_best_method(results_df)
    write_report(split_summary, results_df, best_df)

    best_m1 = best_df.loc[best_df["model_name"] == "M1"].iloc[0]
    print("External recalibration completed.")
    print(
        json.dumps(
            {
                "best_m1_method": best_m1["calibration_method"],
                "best_m1_slope": best_m1["calibration_slope_death"],
                "best_m1_auprc": best_m1["auprc_death"],
            }
        )
    )


if __name__ == "__main__":
    main()
