from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "post_metre_clinical_utility"
OUTDIR.mkdir(parents=True, exist_ok=True)

DOWNSTREAM_MAP = ROOT / "post_metre_selection" / "Downstream_Analysis_Model_Map.csv"
RECAL_SIGNOFF = ROOT / "post_metre_recalibration" / "Recalibrated_Model_Signoff.md"
RECAL_RESULTS = ROOT / "post_metre_recalibration" / "Post_METRE_Recalibration_Results.csv"
RECAL_SPLIT = ROOT / "post_metre_recalibration" / "eicu_recalibration_split.csv"
PRED_MT3 = ROOT / "post_metre_recalibration" / "pred_MT3_eicu_external.parquet"
PRED_M1 = ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet"
PRED_C1 = ROOT / "step7_main_modeling" / "output" / "pred_C1_eicu_external.parquet"
LABELS = ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet"

STRICT_THRESHOLDS = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20]
DCA_THRESHOLDS = [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30]
DEATH_LABEL = "ICU_DEATH"


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def logit(p: np.ndarray) -> np.ndarray:
    p = clip_probs(p)
    return np.log(p / (1.0 - p))


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def apply_intercept(raw_probs: np.ndarray, intercept: float) -> np.ndarray:
    return clip_probs(sigmoid(logit(raw_probs) + intercept))


def load_labels_holdout() -> pd.DataFrame:
    labels = pd.read_parquet(
        LABELS,
        columns=[
            "patient_id",
            "stay_id",
            "t_pred",
            "event_type_24h",
            "event_indicator_death_24h",
            "time_to_event_hours",
            "event_time_absolute",
        ],
    )
    split = pd.read_csv(RECAL_SPLIT, usecols=["patient_id", "split"])
    holdout_patients = set(split.loc[split["split"] == "holdout", "patient_id"])
    labels = labels[labels["patient_id"].isin(holdout_patients)].copy()
    return labels


def load_mt3(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mt3 = pd.read_parquet(PRED_MT3)
    mt3 = mt3.merge(
        labels[
            [
                "patient_id",
                "stay_id",
                "t_pred",
                "event_indicator_death_24h",
                "time_to_event_hours",
                "event_time_absolute",
            ]
        ],
        on=["patient_id", "stay_id", "t_pred"],
        how="inner",
        validate="one_to_one",
    )
    mt3 = mt3.rename(columns={"prob_death_raw": "predicted_prob_death_24h"})
    raw = mt3[
        [
            "patient_id",
            "stay_id",
            "t_pred",
            "event_type_24h",
            "event_indicator_death_24h",
            "time_to_event_hours",
            "event_time_absolute",
            "predicted_prob_death_24h",
        ]
    ].copy()
    raw["model_name"] = "MT3_raw"

    recal = raw.copy()
    params = pd.read_csv(RECAL_RESULTS)
    intercept_json = params.loc[
        (params["model_name"] == "MT3_physiology_support_proxy")
        & (params["calibration_method"] == "intercept_only"),
        "method_parameters_json",
    ].iloc[0]
    intercept = float(json.loads(intercept_json)["intercept"])
    recal["predicted_prob_death_24h"] = apply_intercept(raw["predicted_prob_death_24h"].to_numpy(), intercept)
    recal["model_name"] = "MT3_recalibrated_intercept_only"
    return raw, recal


def load_step7_pred(path: Path, model_name: str, labels: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_parquet(
        path,
        columns=[
            "patient_id",
            "stay_id",
            "t_pred",
            "true_event_type_24h",
            "predicted_prob_death_24h",
        ],
    ).rename(columns={"true_event_type_24h": "event_type_24h"})
    df = df.merge(
        labels[
            [
                "patient_id",
                "stay_id",
                "t_pred",
                "event_indicator_death_24h",
                "time_to_event_hours",
                "event_time_absolute",
            ]
        ],
        on=["patient_id", "stay_id", "t_pred"],
        how="inner",
        validate="one_to_one",
    )
    df["model_name"] = model_name
    return df


def add_eventual_death_time(df: pd.DataFrame) -> pd.DataFrame:
    if "eventual_death_time" in df.columns and "eventual_death_flag" in df.columns:
        return df.copy()
    death_times = (
        df.loc[df["event_indicator_death_24h"] == 1]
        .groupby("stay_id")["event_time_absolute"]
        .min()
        .rename("eventual_death_time")
        .reset_index()
    )
    out = df.merge(death_times, on="stay_id", how="left")
    out["eventual_death_flag"] = out["eventual_death_time"].notna().astype(int)
    return out


def first_alarm_rows(model_df: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    model_df = add_eventual_death_time(model_df).sort_values(["stay_id", "t_pred"])
    evaluated_stays = model_df[["patient_id", "stay_id", "eventual_death_flag", "eventual_death_time"]].drop_duplicates("stay_id")
    for threshold in thresholds:
        alarms = model_df[model_df["predicted_prob_death_24h"] >= threshold].copy()
        if alarms.empty:
            continue
        first = alarms.sort_values(["stay_id", "t_pred"]).groupby("stay_id", as_index=False).first()
        first["threshold"] = threshold
        first["strict_24h_true_alarm"] = (
            (first["event_indicator_death_24h"] == 1)
            & (first["time_to_event_hours"].between(0, 24, inclusive="both"))
        ).astype(int)
        first["strict_24h_lead_time_hours"] = np.where(
            first["strict_24h_true_alarm"] == 1, first["time_to_event_hours"], np.nan
        )
        first["eventual_death_lead_time_hours"] = (
            (first["eventual_death_time"] - first["t_pred"]).dt.total_seconds() / 3600.0
        )
        first.loc[first["eventual_death_lead_time_hours"] < 0, "eventual_death_lead_time_hours"] = np.nan
        first["lead_time_type"] = np.where(
            first["strict_24h_true_alarm"] == 1,
            "strict_24h_label_lead_time",
            np.where(first["eventual_death_flag"] == 1, "eventual_death_lead_time_not_strict_24h", "no_death_or_false_alarm"),
        )
        rows.append(first)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["evaluated_stay_n_for_model"] = int(evaluated_stays["stay_id"].nunique())
    return out


def summarize_strict(patient_level: pd.DataFrame, all_models: pd.DataFrame) -> pd.DataFrame:
    model_stay_counts = (
        all_models.groupby("model_name")
        .agg(
            evaluated_stay_n=("stay_id", "nunique"),
            eventual_death_stay_n=("eventual_death_flag", lambda s: int(all_models.loc[s.index].drop_duplicates("stay_id")["eventual_death_flag"].sum())),
        )
        .reset_index()
    )
    rows = []
    for (model_name, threshold), part in patient_level.groupby(["model_name", "threshold"]):
        base = model_stay_counts[model_stay_counts["model_name"] == model_name].iloc[0]
        true_part = part[part["strict_24h_true_alarm"] == 1]
        rows.append(
            {
                "model_name": model_name,
                "threshold": threshold,
                "evaluated_stay_n": int(base["evaluated_stay_n"]),
                "eventual_death_stay_n": int(base["eventual_death_stay_n"]),
                "first_alarm_stay_n": int(part["stay_id"].nunique()),
                "strict_true_alarm_stay_n": int(true_part["stay_id"].nunique()),
                "false_or_non_strict_first_alarm_stay_n": int(part["stay_id"].nunique() - true_part["stay_id"].nunique()),
                "no_alarm_stay_n": int(base["evaluated_stay_n"] - part["stay_id"].nunique()),
                "strict_true_alarm_ppv": float(true_part["stay_id"].nunique() / part["stay_id"].nunique()) if part["stay_id"].nunique() else np.nan,
                "strict_eventual_death_capture_rate": float(true_part["stay_id"].nunique() / base["eventual_death_stay_n"]) if base["eventual_death_stay_n"] else np.nan,
                "strict_lead_time_median_hours": float(true_part["strict_24h_lead_time_hours"].median()) if len(true_part) else np.nan,
                "strict_lead_time_iqr_low_hours": float(true_part["strict_24h_lead_time_hours"].quantile(0.25)) if len(true_part) else np.nan,
                "strict_lead_time_iqr_high_hours": float(true_part["strict_24h_lead_time_hours"].quantile(0.75)) if len(true_part) else np.nan,
                "strict_lead_time_max_hours": float(true_part["strict_24h_lead_time_hours"].max()) if len(true_part) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["model_name", "threshold"]).reset_index(drop=True)


def summarize_eventual(patient_level: pd.DataFrame) -> pd.DataFrame:
    rows = []
    valid = patient_level[
        (patient_level["eventual_death_flag"] == 1)
        & patient_level["eventual_death_lead_time_hours"].notna()
        & (patient_level["eventual_death_lead_time_hours"] >= 0)
    ].copy()
    for (model_name, threshold), part in valid.groupby(["model_name", "threshold"]):
        rows.append(
            {
                "model_name": model_name,
                "threshold": threshold,
                "lead_time_definition": "eventual_death_lead_time_not_strict_24h",
                "alarm_before_eventual_death_stay_n": int(part["stay_id"].nunique()),
                "eventual_lead_time_median_hours": float(part["eventual_death_lead_time_hours"].median()),
                "eventual_lead_time_iqr_low_hours": float(part["eventual_death_lead_time_hours"].quantile(0.25)),
                "eventual_lead_time_iqr_high_hours": float(part["eventual_death_lead_time_hours"].quantile(0.75)),
                "eventual_lead_time_max_hours": float(part["eventual_death_lead_time_hours"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values(["model_name", "threshold"]).reset_index(drop=True)


def net_benefit(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, float]:
    pred = p >= threshold
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    n = len(y)
    nb = tp / n - fp / n * (threshold / (1.0 - threshold))
    return {"tp": tp, "fp": fp, "positive_n": int(pred.sum()), "net_benefit": float(nb)}


def dca_table(models: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for df in models:
        model_name = df["model_name"].iloc[0]
        y = (df["event_indicator_death_24h"] == 1).astype(int).to_numpy()
        p = df["predicted_prob_death_24h"].to_numpy()
        prevalence = float(y.mean())
        n = len(y)
        for threshold in DCA_THRESHOLDS:
            m = net_benefit(y, p, threshold)
            treat_all = prevalence - (1.0 - prevalence) * threshold / (1.0 - threshold)
            rows.append(
                {
                    "model_name": model_name,
                    "threshold": threshold,
                    "n": n,
                    "prevalence": prevalence,
                    **m,
                    "treat_all_net_benefit": float(treat_all),
                    "treat_none_net_benefit": 0.0,
                    "net_benefit_minus_treat_all": float(m["net_benefit"] - treat_all),
                    "net_benefit_minus_treat_none": float(m["net_benefit"]),
                }
            )
    # Add explicit treat-all/treat-none rows for plotting.
    reference = models[0]
    y = (reference["event_indicator_death_24h"] == 1).astype(int).to_numpy()
    prevalence = float(y.mean())
    n = len(y)
    for threshold in DCA_THRESHOLDS:
        treat_all = prevalence - (1.0 - prevalence) * threshold / (1.0 - threshold)
        rows.append(
            {
                "model_name": "treat_all",
                "threshold": threshold,
                "n": n,
                "prevalence": prevalence,
                "tp": int(y.sum()),
                "fp": int((1 - y).sum()),
                "positive_n": n,
                "net_benefit": float(treat_all),
                "treat_all_net_benefit": float(treat_all),
                "treat_none_net_benefit": 0.0,
                "net_benefit_minus_treat_all": 0.0,
                "net_benefit_minus_treat_none": float(treat_all),
            }
        )
        rows.append(
            {
                "model_name": "treat_none",
                "threshold": threshold,
                "n": n,
                "prevalence": prevalence,
                "tp": 0,
                "fp": 0,
                "positive_n": 0,
                "net_benefit": 0.0,
                "treat_all_net_benefit": float(treat_all),
                "treat_none_net_benefit": 0.0,
                "net_benefit_minus_treat_all": float(-treat_all),
                "net_benefit_minus_treat_none": 0.0,
            }
        )
    return pd.DataFrame(rows)


def write_targets() -> None:
    model_map = pd.read_csv(DOWNSTREAM_MAP)
    recal_text = RECAL_SIGNOFF.read_text(encoding="utf-8") if RECAL_SIGNOFF.exists() else ""
    external_model = model_map.loc[model_map["downstream_analysis"] == "DCA", "primary_model_to_use"].iloc[0]
    text = f"""# Clinical Utility Model Targets

## Models used

- Best transport model, uncalibrated: `{external_model}` as `MT3_raw`.
- Best transport model, recalibrated: `MT3_recalibrated_intercept_only`.
- Original main model: `M1_original_rich`.
- Clinical comparator: `C1_dynamic_SOFA`.

## Evaluation subset

- Dataset: eICU external hold-out subset from post-METRE recalibration.
- Reason: recalibrated probabilities must be evaluated on patients not used for recalibration fitting.

## Recalibration sign-off excerpt

```text
{recal_text.strip()}
```
"""
    (OUTDIR / "Clinical_Utility_Model_Targets.md").write_text(text, encoding="utf-8")


def write_report(strict_summary: pd.DataFrame, dca: pd.DataFrame) -> None:
    mt3_strict = strict_summary[strict_summary["model_name"] == "MT3_recalibrated_intercept_only"]
    positive_dca = dca[(dca["model_name"].isin(["MT3_raw", "MT3_recalibrated_intercept_only", "M1_original_rich", "C1_dynamic_SOFA"])) & (dca["net_benefit"] > 0)]
    mt3_raw_dca = dca[dca["model_name"] == "MT3_raw"][["threshold", "net_benefit"]].rename(columns={"net_benefit": "raw_nb"})
    mt3_rec_dca = dca[dca["model_name"] == "MT3_recalibrated_intercept_only"][["threshold", "net_benefit"]].rename(columns={"net_benefit": "recalibrated_nb"})
    dca_compare = mt3_raw_dca.merge(mt3_rec_dca, on="threshold")
    improved_thresholds = dca_compare[dca_compare["recalibrated_nb"] > dca_compare["raw_nb"]]["threshold"].tolist()
    best_threshold_rows = mt3_strict[["threshold", "strict_true_alarm_stay_n", "strict_lead_time_median_hours", "strict_lead_time_iqr_low_hours", "strict_lead_time_iqr_high_hours"]].to_dict(orient="records")
    text = f"""# Post-METRE Lead-time and DCA Report

## Required answers

1. Should the original lead-time be withdrawn or renamed?
   - Yes. The prior 79-91 hour values are inconsistent with a strict 24h label interpretation and should be renamed as exploratory eventual-death lead-time if retained.

2. Can strict 24h lead-time be used as the main result?
   - Yes, with the limitation that it measures lead-time only among first alarms that are already within a 24h death-label window.
   - MT3 recalibrated strict summary:

```json
{json.dumps(best_threshold_rows, ensure_ascii=False, indent=2)}
```

3. Does DCA show positive net benefit at low thresholds?
   - Positive model net benefit exists: `{bool(len(positive_dca))}`.
   - Positive thresholds by model are available in `dca_threshold_sweep_post_metre.csv`.

4. Did recalibrated DCA improve?
   - Recalibrated MT3 has higher net benefit than raw MT3 at thresholds: `{improved_thresholds}`.

5. Should the model remain a risk stratification tool rather than an automatic intervention trigger?
   - Yes. Even after METRE repair and recalibration, clinical utility varies by threshold and should not be framed as an automatic intervention trigger.

## Output interpretation

- `strict_24h_first_alarm_summary.csv` is the main lead-time table.
- `eventual_death_leadtime_summary.csv` is exploratory and explicitly not a strict 24h-label analysis.
- `dca_threshold_sweep_post_metre.csv` should replace the old DCA data interface for Figure 5.
"""
    (OUTDIR / "Post_METRE_Leadtime_DCA_Report.md").write_text(text, encoding="utf-8")


def main() -> None:
    write_targets()
    labels = load_labels_holdout()
    mt3_raw, mt3_recal = load_mt3(labels)
    m1 = load_step7_pred(PRED_M1, "M1_original_rich", labels)
    c1 = load_step7_pred(PRED_C1, "C1_dynamic_SOFA", labels)
    models = [mt3_raw, mt3_recal, m1, c1]
    models = [add_eventual_death_time(m) for m in models]

    patient_rows = []
    for m in models:
        patient_rows.append(first_alarm_rows(m, STRICT_THRESHOLDS))
    patient_level = pd.concat(patient_rows, ignore_index=True)
    patient_level.to_parquet(OUTDIR / "strict_24h_first_alarm_patient_level.parquet", index=False)

    all_models = pd.concat(models, ignore_index=True)
    strict_summary = summarize_strict(patient_level, all_models)
    strict_summary.to_csv(OUTDIR / "strict_24h_first_alarm_summary.csv", index=False, encoding="utf-8-sig")

    eventual_summary = summarize_eventual(patient_level)
    eventual_summary.to_csv(OUTDIR / "eventual_death_leadtime_summary.csv", index=False, encoding="utf-8-sig")

    dca = dca_table(models)
    dca.to_csv(OUTDIR / "dca_threshold_sweep_post_metre.csv", index=False, encoding="utf-8-sig")
    write_report(strict_summary, dca)

    print(
        json.dumps(
            {
                "strict_rows": int(len(strict_summary)),
                "patient_level_rows": int(len(patient_level)),
                "positive_dca_rows": int((dca["net_benefit"] > 0).sum()),
                "outputs": str(OUTDIR),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
