from __future__ import annotations

import json
import math
import pickle
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


REPO = Path(r"D:\try\github_chatgpt_share_repo")
ROOT = Path(r"D:\try")
STEP7 = ROOT / "step7_main_modeling" / "output"
OUT_TABLES = REPO / "results_final" / "tables"
OUT_TEXT = REPO / "results_final" / "text"
OUT_FIGURES = REPO / "results_final" / "figures"
for directory in [OUT_TABLES, OUT_TEXT, OUT_FIGURES]:
    directory.mkdir(parents=True, exist_ok=True)

SEED = 20260511
N_BOOTSTRAP = 1000
THRESHOLDS = [0.005, 0.010, 0.020, 0.030, 0.050, 0.100]
DEATH_LABEL = "ICU_DEATH"
EPS = 1e-6

MODEL_READY_EXTERNAL = STEP7 / "Model_Ready_eICU_External.parquet"
MODEL_READY_TEST = STEP7 / "Model_Ready_Test_All.parquet"
DCA_SOURCE = ROOT / "results_final" / "clinical_implementation" / "P12_P10_TrueTraining_DCA_Summary.csv"

PREDICTION_CANDIDATES = {
    "M1_internal_rich_reference_model_eicu_external": STEP7 / "pred_main_eicu_external.parquet",
    "M1_internal_rich_reference_model_mimic_test": STEP7 / "pred_main_test_all.parquet",
    "C1_dynamic_SOFA_clinical_comparator_eicu_external": STEP7 / "pred_C1_eicu_external.parquet",
    "C1_dynamic_SOFA_clinical_comparator_mimic_test": STEP7 / "pred_C1_test_all.parquet",
    "C3_no_phenotype_eicu_external": STEP7 / "pred_C3_eicu_external.parquet",
    "C3_no_phenotype_mimic_test": STEP7 / "pred_C3_test_all.parquet",
    "MT3_post_metre_recalibration_eicu_external": ROOT / "post_metre_recalibration" / "pred_MT3_eicu_external.parquet",
    "Model_Ready_Test_All": MODEL_READY_TEST,
    "Model_Ready_eICU_External": MODEL_READY_EXTERNAL,
}

FROZEN_MODELS = {
    "P15_clinically_parsimonious_transport_model": ROOT / "parsimonious_features" / "model_P15_minimal_bedside_model.pkl",
    "P12_true_trained_clinical_landing_model": ROOT
    / "results_final"
    / "clinical_implementation"
    / "model_P12_true_trained_clinical_landing_model.pkl",
    "P10_true_trained_ultra_minimal_sensitivity_model": ROOT
    / "results_final"
    / "clinical_implementation"
    / "model_P10_true_trained_ultra_minimal_sensitivity_model.pkl",
}

EXTERNAL_PRED_MODELS = {
    "M1_internal_rich_reference_model": STEP7 / "pred_main_eicu_external.parquet",
    "C1_dynamic_SOFA_clinical_comparator": STEP7 / "pred_C1_eicu_external.parquet",
}

EXPECTED_POINT_ESTIMATES = {
    "P15_clinically_parsimonious_transport_model": {
        "AUROC": 0.8103,
        "AUPRC": 0.1892,
        "calibration_slope": 1.0031,
    },
    "M1_internal_rich_reference_model": {
        "AUROC": 0.7090,
        "AUPRC": 0.0377,
        "calibration_slope": 0.0728,
    },
    "C1_dynamic_SOFA_clinical_comparator": {
        "AUROC": 0.7253,
        "AUPRC": 0.0669,
    },
}

SUPPORT_PROXY_COLS = [
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
]


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def read_model_bundle(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return pickle.load(f)


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
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
    oliguria = (df["oliguria_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
        df["oliguria_burden_24h"].notna()
    )
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
    out["shared_support_intensity_proxy"] = out[SUPPORT_PROXY_COLS[1:]].mean(axis=1)
    return out


def add_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    proxy = build_support_proxy(out)
    for col in SUPPORT_PROXY_COLS:
        out[col] = proxy[col]
    return out


def predict_from_frozen_model(model_name: str, model_path: Path, model_ready: pd.DataFrame) -> pd.DataFrame:
    bundle = read_model_bundle(model_path)
    df = add_support_proxy(model_ready)
    features = list(bundle["features"])
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise RuntimeError(f"{model_name}: missing frozen feature columns: {missing}")
    logits = bundle["pipeline"].decision_function(df[features]) / float(bundle.get("temperature", 1.0))
    probs = softmax(logits)
    classes = [str(x) for x in bundle["classes"]]
    death_idx = classes.index(DEATH_LABEL)
    out = df[
        [
            "patient_id",
            "stay_id",
            "t_pred",
            "event_type_24h",
            "event_indicator_death_24h",
            "phenotype_label",
            "is_sepsis_on_admission",
            "hours_since_icu_admission",
            "hours_from_anchor",
        ]
    ].copy()
    out["predicted_prob_death_24h"] = probs[:, death_idx]
    out["model_name"] = model_name
    out["dataset_name"] = "eicu_external"
    return out


def normalize_prediction_file(path: Path, model_name: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    rename = {
        "prob_death_raw": "predicted_prob_death_24h",
        "pred_death_24h": "predicted_prob_death_24h",
        "true_event_type_24h": "event_type_24h",
    }
    for old, new in rename.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    if "event_indicator_death_24h" not in df.columns:
        if "event_type_24h" in df.columns:
            df["event_indicator_death_24h"] = (df["event_type_24h"].astype(str) == DEATH_LABEL).astype(int)
        elif "true_event_type_24h" in df.columns:
            df["event_indicator_death_24h"] = (df["true_event_type_24h"].astype(str) == DEATH_LABEL).astype(int)
    if "phenotype_label" not in df.columns:
        df["phenotype_label"] = "missing"
    df["model_name"] = model_name
    df["dataset_name"] = "eicu_external"
    return df


def choose_columns(df: pd.DataFrame) -> dict[str, str | None]:
    id_col = next((c for c in ["patient_id", "subject_id", "uniquepid", "stay_id", "patientunitstayid"] if c in df.columns), None)
    label_col = next(
        (
            c
            for c in ["event_indicator_death_24h", "event_type_24h", "true_event_type_24h"]
            if c in df.columns
        ),
        None,
    )
    pred_col = next(
        (
            c
            for c in ["predicted_prob_death_24h", "prob_death_raw", "pred_death_24h"]
            if c in df.columns
        ),
        None,
    )
    phen_col = next((c for c in ["phenotype_label", "phenotype"] if c in df.columns), None)
    return {"id_col": id_col, "label_col": label_col, "pred_col": pred_col, "phenotype_col": phen_col}


def y_from_label(series: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).to_numpy()
    return (series.astype(str) == DEATH_LABEL).astype(int).to_numpy()


def audit_prediction_files() -> pd.DataFrame:
    rows = []
    for name, path in PREDICTION_CANDIDATES.items():
        row: dict[str, Any] = {
            "model_or_file": name,
            "path": str(path),
            "exists": path.exists(),
            "row_count": "missing_prediction_file",
            "patient_or_stay_n": "missing_prediction_file",
            "death_event_n": "missing_prediction_file",
            "death_event_rate": "missing_prediction_file",
            "id_col": "missing_prediction_file",
            "label_col": "missing_prediction_file",
            "prediction_col": "missing_prediction_file",
            "phenotype_col": "missing_prediction_file",
            "usable_for_threshold_specific_performance": False,
        }
        if path.exists():
            df = pd.read_parquet(path)
            cols = choose_columns(df)
            row.update(
                {
                    "row_count": len(df),
                    "id_col": cols["id_col"] or "missing_id_col",
                    "label_col": cols["label_col"] or "missing_label_col",
                    "prediction_col": cols["pred_col"] or "missing_prediction_col",
                    "phenotype_col": cols["phenotype_col"] or "missing_phenotype_col",
                }
            )
            if cols["id_col"]:
                row["patient_or_stay_n"] = int(df[cols["id_col"]].nunique(dropna=True))
            if cols["label_col"]:
                y = y_from_label(df[cols["label_col"]])
                row["death_event_n"] = int(y.sum())
                row["death_event_rate"] = float(y.mean())
            row["usable_for_threshold_specific_performance"] = bool(cols["id_col"] and cols["label_col"] and cols["pred_col"])
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "threshold_prediction_file_audit.csv", index=False, encoding="utf-8-sig")
    return out


def point_metrics(df: pd.DataFrame) -> dict[str, float]:
    y = df["event_indicator_death_24h"].astype(int).to_numpy()
    p = df["predicted_prob_death_24h"].astype(float).to_numpy()
    probs = np.clip(p, EPS, 1 - EPS)
    logits = np.log(probs / (1 - probs)).reshape(-1, 1)
    slope = math.nan
    try:
        model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
        model.fit(logits, y)
        slope = float(model.coef_[0][0])
    except Exception:
        slope = math.nan
    return {
        "AUROC": float(roc_auc_score(y, p)),
        "AUPRC": float(average_precision_score(y, p)),
        "calibration_slope": slope,
        "death_brier": float(brier_score_loss(y, p)),
        "event_rate": float(y.mean()),
    }


def threshold_metrics_from_counts(tp: int, fp: int, tn: int, fn: int, threshold: float) -> dict[str, float]:
    n = tp + fp + tn + fn
    prevalence = (tp + fn) / n if n else math.nan

    def div(num: float, den: float) -> float:
        return float(num / den) if den else math.nan

    sensitivity = div(tp, tp + fn)
    specificity = div(tn, tn + fp)
    ppv = div(tp, tp + fp)
    npv = div(tn, tn + fn)
    f1 = div(2 * tp, 2 * tp + fp + fn)
    screen_positive = tp + fp
    nb = div(tp, n) - div(fp, n) * threshold / (1 - threshold)
    treat_all = prevalence - (1 - prevalence) * threshold / (1 - threshold)
    return {
        "true_positives": float(tp),
        "false_positives": float(fp),
        "true_negatives": float(tn),
        "false_negatives": float(fn),
        "sensitivity_recall": sensitivity,
        "specificity": specificity,
        "PPV": ppv,
        "NPV": npv,
        "F1_score": f1,
        "false_positive_rate": 1 - specificity if not math.isnan(specificity) else math.nan,
        "false_negative_rate": 1 - sensitivity if not math.isnan(sensitivity) else math.nan,
        "number_screened_positive": float(screen_positive),
        "screen_positive_proportion": div(screen_positive, n),
        "event_rate_among_screen_positive": ppv,
        "event_rate_among_screen_negative": div(fn, fn + tn),
        "net_benefit": nb,
        "treat_all_net_benefit": treat_all,
        "treat_none_net_benefit": 0.0,
        "prevalence": prevalence,
        "n": float(n),
    }


def threshold_metrics(df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    y = df["event_indicator_death_24h"].astype(int).to_numpy()
    p = df["predicted_prob_death_24h"].astype(float).to_numpy()
    rows = []
    for threshold in THRESHOLDS:
        pos = p >= threshold
        tp = int(np.sum(pos & (y == 1)))
        fp = int(np.sum(pos & (y == 0)))
        tn = int(np.sum((~pos) & (y == 0)))
        fn = int(np.sum((~pos) & (y == 1)))
        row = {"model_name": model_name, "threshold": threshold}
        row.update(threshold_metrics_from_counts(tp, fp, tn, fn, threshold))
        row["unstable_threshold_note"] = "TP or FP is zero" if (tp == 0 or fp == 0) else ""
        rows.append(row)
    return pd.DataFrame(rows)


def write_csv_no_nan(df: pd.DataFrame, path: Path) -> None:
    out = df.copy()
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.astype(object).where(pd.notna(out), "not_estimable_no_screen_negative")
    out.to_csv(path, index=False, encoding="utf-8-sig")


def bootstrap_threshold_ci(df: pd.DataFrame, cluster_col: str = "patient_id") -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    work = df[[cluster_col, "event_indicator_death_24h", "predicted_prob_death_24h"]].copy()
    work["event_indicator_death_24h"] = work["event_indicator_death_24h"].astype(int)
    work["predicted_prob_death_24h"] = work["predicted_prob_death_24h"].astype(float)
    clusters = pd.Index(work[cluster_col].drop_duplicates())
    rows = []
    for threshold in THRESHOLDS:
        tmp = work.copy()
        tmp["pred_pos"] = tmp["predicted_prob_death_24h"] >= threshold
        tmp["tp"] = ((tmp["pred_pos"]) & (tmp["event_indicator_death_24h"] == 1)).astype(int)
        tmp["fp"] = ((tmp["pred_pos"]) & (tmp["event_indicator_death_24h"] == 0)).astype(int)
        tmp["tn"] = ((~tmp["pred_pos"]) & (tmp["event_indicator_death_24h"] == 0)).astype(int)
        tmp["fn"] = ((~tmp["pred_pos"]) & (tmp["event_indicator_death_24h"] == 1)).astype(int)
        grouped = tmp.groupby(cluster_col, sort=False)[["tp", "fp", "tn", "fn"]].sum().reindex(clusters).fillna(0)
        arr = grouped.to_numpy(dtype=float)
        metric_samples: dict[str, list[float]] = {
            "sensitivity_recall": [],
            "specificity": [],
            "PPV": [],
            "NPV": [],
            "F1_score": [],
            "false_positive_rate": [],
            "false_negative_rate": [],
            "screen_positive_proportion": [],
            "event_rate_among_screen_positive": [],
            "event_rate_among_screen_negative": [],
            "net_benefit": [],
        }
        skipped = 0
        n_clusters = len(clusters)
        for _ in range(N_BOOTSTRAP):
            idx = rng.integers(0, n_clusters, size=n_clusters)
            sums = arr[idx].sum(axis=0)
            tp, fp, tn, fn = [int(x) for x in sums]
            if (tp + fn) == 0 or (tn + fp) == 0:
                skipped += 1
                continue
            metrics = threshold_metrics_from_counts(tp, fp, tn, fn, threshold)
            for metric in metric_samples:
                val = metrics[metric]
                if math.isfinite(val):
                    metric_samples[metric].append(val)
        for metric, values in metric_samples.items():
            values_arr = np.asarray(values, dtype=float)
            if len(values_arr) == 0:
                lower: float | str = "not_estimable_no_screen_negative"
                upper: float | str = "not_estimable_no_screen_negative"
                valid = 0
            else:
                lower, upper = np.percentile(values_arr, [2.5, 97.5])
                lower = float(lower)
                upper = float(upper)
                valid = len(values_arr)
            rows.append(
                {
                    "threshold": threshold,
                    "metric": metric,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "n_resamples_requested": N_BOOTSTRAP,
                    "n_resamples_valid": valid,
                    "n_resamples_skipped": skipped,
                    "bootstrap_unit": cluster_col,
                    "bootstrap_level": "patient-level" if cluster_col == "patient_id" else "stay-level cluster",
                    "seed": SEED,
                }
            )
    out = pd.DataFrame(rows)
    write_csv_no_nan(out, OUT_TABLES / "P15_eICU_threshold_specific_performance_bootstrap_ci.csv")
    return out


def _is_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def ci_lookup(ci: pd.DataFrame, threshold: float, metric: str) -> tuple[Any, Any]:
    row = ci[(ci["threshold"] == threshold) & (ci["metric"] == metric)]
    if row.empty:
        return "not_estimable", "not_estimable"
    lower = row.iloc[0]["ci_lower"]
    upper = row.iloc[0]["ci_upper"]
    if not _is_number(lower) or not _is_number(upper):
        return "not_estimable_no_screen_negative", "not_estimable_no_screen_negative"
    return float(lower), float(upper)


def fmt_ci(point: Any, lower: Any, upper: Any, digits: int = 3, zh: bool = False) -> str:
    if not _is_number(point) or not _is_number(lower) or not _is_number(upper):
        return "不可估计（无筛查阴性样本）" if zh else "not estimable (no screen-negative rows)"
    point = float(point)
    lower = float(lower)
    upper = float(upper)
    if zh:
        return f"{point:.{digits}f}（95% CI：{lower:.{digits}f}–{upper:.{digits}f}）"
    return f"{point:.{digits}f} (95% CI, {lower:.{digits}f}–{upper:.{digits}f})"


def interpretation(row: pd.Series) -> str:
    notes: list[str] = []
    if row["sensitivity_recall"] >= 0.8 and row["PPV"] < 0.05:
        notes.append("sensitive screening threshold; high false-positive burden")
    if row["net_benefit"] > row["treat_all_net_benefit"] and row["net_benefit"] > row["treat_none_net_benefit"]:
        notes.append("clinically useful threshold range")
    if row["net_benefit"] < row["treat_none_net_benefit"]:
        notes.append("not preferred as operational threshold")
    if row["threshold"] >= 0.05 and row["sensitivity_recall"] < 0.5:
        notes.append("restrictive threshold; likely misses events")
    return "; ".join(notes) if notes else "threshold-specific operational trade-off"


def make_integrated_table(point: pd.DataFrame, ci: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in point.iterrows():
        out = {"threshold": float(row["threshold"])}
        for metric, col in [
            ("sensitivity_recall", "sensitivity_recall"),
            ("specificity", "specificity"),
            ("PPV", "PPV"),
            ("NPV", "NPV"),
            ("net_benefit", "net_benefit"),
        ]:
            lower, upper = ci_lookup(ci, float(row["threshold"]), metric)
            out[col] = float(row[metric]) if _is_number(row[metric]) else "not_estimable_no_screen_negative"
            out[f"{col}_95CI"] = (
                f"{float(lower):.4f}-{float(upper):.4f}"
                if _is_number(lower) and _is_number(upper)
                else "not_estimable_no_screen_negative"
            )
        out["treat_all_net_benefit"] = float(row["treat_all_net_benefit"])
        out["treat_none_net_benefit"] = float(row["treat_none_net_benefit"])
        out["interpretation"] = interpretation(row)
        rows.append(out)
    integrated = pd.DataFrame(rows)
    write_csv_no_nan(integrated, OUT_TABLES / "P15_eICU_threshold_DCA_integrated_table.csv")
    return integrated


def align_existing_dca(point: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    out = point.copy()
    out["dca_source_file"] = str(DCA_SOURCE)
    out["dca_source_net_benefit"] = "not_available"
    out["dca_source_match"] = "not_available"
    if not DCA_SOURCE.exists():
        warnings.append(f"missing_dca_source_file: {DCA_SOURCE}")
        return out
    dca = pd.read_csv(DCA_SOURCE)
    required = {"dataset_name", "model_name", "threshold", "net_benefit", "treat_all_net_benefit", "treat_none_net_benefit"}
    if not required.issubset(dca.columns):
        warnings.append(f"dca_source_missing_required_columns: {DCA_SOURCE}")
        return out
    dca_p15 = dca[
        (dca["dataset_name"].astype(str) == "eicu_external")
        & (dca["model_name"].astype(str) == "P15_clinically_parsimonious_transport_model")
    ].copy()
    for idx, row in out.iterrows():
        threshold = float(row["threshold"])
        match = dca_p15[np.isclose(dca_p15["threshold"].astype(float), threshold)]
        if match.empty:
            out.at[idx, "dca_source_match"] = "missing_threshold_in_dca_source"
            warnings.append(f"missing_dca_threshold_for_P15_eicu: {threshold}")
            continue
        dca_row = match.iloc[0]
        out.at[idx, "dca_source_net_benefit"] = float(dca_row["net_benefit"])
        diff = abs(float(row["net_benefit"]) - float(dca_row["net_benefit"]))
        out.at[idx, "dca_source_match"] = "yes" if diff < 1e-10 else f"diff={diff:.6g}"
        if diff >= 1e-6:
            warnings.append(f"dca_net_benefit_mismatch_threshold_{threshold}: computed={row['net_benefit']} source={dca_row['net_benefit']}")
        for col in ["net_benefit", "treat_all_net_benefit", "treat_none_net_benefit"]:
            out.at[idx, col] = float(dca_row[col])
    return out


def supplementary_table(point: pd.DataFrame, ci: pd.DataFrame, integrated: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in point.iterrows():
        threshold = float(row["threshold"])
        out = {"风险阈值": f"{threshold:.3f}"}
        for metric, label in [
            ("sensitivity_recall", "敏感性/召回率"),
            ("specificity", "特异性"),
            ("PPV", "阳性预测值"),
            ("NPV", "阴性预测值"),
            ("F1_score", "F1 值"),
            ("screen_positive_proportion", "筛查阳性比例"),
            ("net_benefit", "净获益"),
        ]:
            lower, upper = ci_lookup(ci, threshold, metric)
            out[label] = fmt_ci(float(row[metric]), lower, upper, digits=3, zh=True)
        out["操作性解释"] = integrated.loc[integrated["threshold"] == threshold, "interpretation"].iloc[0]
        rows.append(out)
    table = pd.DataFrame(rows)
    write_csv_no_nan(table, OUT_TABLES / "Supplementary_Table_Sx_P15_threshold_specific_operational_performance.csv")
    def markdown_table(df: pd.DataFrame) -> str:
        cols = list(df.columns)
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, record in df.iterrows():
            lines.append("| " + " | ".join(str(record[col]) for col in cols) + " |")
        return "\n".join(lines)

    md = [
        "# 补充表 Sx. P15 双锚点模型在 eICU 外部验证中的阈值特异性操作性能",
        "",
        "说明：召回率/敏感性是阈值特异性操作指标，不能脱离风险阈值单独解释。本表用于补充说明不同阈值下敏感性、PPV、NPV、筛查阳性比例与净获益之间的权衡，不作为主性能指标，也不构成自动干预触发规则。",
        "",
        markdown_table(table),
    ]
    (OUT_TEXT / "Supplementary_Table_Sx_P15_threshold_specific_operational_performance_zh.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )
    return table


def write_text_outputs(point: pd.DataFrame, integrated: pd.DataFrame, audit: pd.DataFrame, warnings: list[str]) -> None:
    def get(th: float, col: str) -> float:
        return float(point.loc[point["threshold"] == th, col].iloc[0])

    low = point[point["threshold"].isin([0.005, 0.01, 0.02, 0.03])].copy()
    best_nb = point.loc[point["net_benefit"].idxmax()]
    results = f"""# Results 插入段落：阈值特异性召回率/敏感性分析

由于 24 小时 ICU 死亡是低发生率事件，单一固定阈值下的召回率不作为本研究的主性能指标。P15 在 eICU 外部验证中的 prediction-row 事件率为 {get(0.005, 'prevalence'):.3%}。在较低阈值下，模型可获得较高敏感性，但阳性预测值和筛查阳性负担显示出明显权衡：阈值 0.5%、1%、2% 和 3% 下，敏感性分别为 {get(0.005, 'sensitivity_recall'):.3f}、{get(0.01, 'sensitivity_recall'):.3f}、{get(0.02, 'sensitivity_recall'):.3f} 和 {get(0.03, 'sensitivity_recall'):.3f}，对应 PPV 分别为 {get(0.005, 'PPV'):.3f}、{get(0.01, 'PPV'):.3f}、{get(0.02, 'PPV'):.3f} 和 {get(0.03, 'PPV'):.3f}。筛查阳性比例也随阈值升高而下降，提示低阈值更适合作为高敏感筛查设定，但会带来较高假阳性负担。本研究因此将阈值特异性敏感性、特异性、PPV 和 NPV 作为操作性补充分析，并与 DCA 联合解释；主评价框架仍为 AUROC、AUPRC、校准斜率和净获益分析。当前 DCA 显示净获益最高的候选阈值为 {float(best_nb['threshold']):.3f}（net benefit={float(best_nb['net_benefit']):.4f}），但这些结果仅支持风险分层和监测升级讨论，不应解释为自动干预触发器。
"""
    (OUT_TEXT / "P15_threshold_specific_results_insert_zh.md").write_text(results, encoding="utf-8")

    discussion = """# Discussion 插入段落：召回率低的解释边界

召回率低本身不能脱离阈值解释。对于 24 小时 ICU 死亡这类低发生率结局，若单纯追求高 recall，模型必须在很低风险阈值下运行，这会显著增加筛查阳性比例和假阳性预警负担；反之，较高阈值会减少假阳性，但不可避免地牺牲敏感性。因此，ICU 动态预警模型的临床意义不应由某一个固定阈值下的 recall 单独决定，而应同时考虑概率校准、阈值下净获益、病区可承受的预警资源容量以及临床团队对假阳性的容忍度。在低发生率死亡预测中，AUPRC 比 accuracy 或单点 recall 更能反映模型在不同阈值下识别事件的整体能力。P15 的主要定位是提供可迁移、校准稳定、变量语义清楚的风险分层框架，而不是在任意阈值下最大化召回率，也不能被解释为已经可以直接指导治疗的自动化触发系统。
"""
    (OUT_TEXT / "P15_threshold_specific_discussion_insert_zh.md").write_text(discussion, encoding="utf-8")

    audit_md = [
        "# P15 threshold-specific performance audit",
        "",
        "## Data files",
        "",
    ]
    for _, row in audit.iterrows():
        audit_md.append(
            f"- `{row['model_or_file']}`: `{row['path']}`; exists={row['exists']}; usable={row['usable_for_threshold_specific_performance']}; id={row['id_col']}; label={row['label_col']}; prediction={row['prediction_col']}."
        )
    audit_md.extend(
        [
            "",
            "## Analysis rules",
            "",
            f"- Thresholds: {', '.join(str(x) for x in THRESHOLDS)}.",
            "- Bootstrap: patient-level cluster bootstrap using `patient_id` when available.",
            f"- Bootstrap resamples: {N_BOOTSTRAP}; seed: {SEED}.",
            "- No model retraining was performed.",
            "- eICU was used only for external validation threshold evaluation, not for tuning.",
            "- Recall/sensitivity is reported as a threshold-specific operational metric, not a primary model metric.",
            "- Main model interpretation remains based on AUROC, AUPRC, calibration slope, and DCA.",
            "",
            "## Output files",
            "",
            "- `results_final/tables/threshold_prediction_file_audit.csv`",
            "- `results_final/tables/P15_eICU_threshold_specific_performance.csv`",
            "- `results_final/tables/P15_eICU_threshold_specific_performance_bootstrap_ci.csv`",
            "- `results_final/tables/P15_eICU_threshold_DCA_integrated_table.csv`",
            "- `results_final/tables/eICU_threshold_performance_model_comparison.csv`",
            "- `results_final/tables/Supplementary_Table_Sx_P15_threshold_specific_operational_performance.csv`",
            "- `results_final/text/Supplementary_Table_Sx_P15_threshold_specific_operational_performance_zh.md`",
            "- `results_final/text/P15_threshold_specific_results_insert_zh.md`",
            "- `results_final/text/P15_threshold_specific_discussion_insert_zh.md`",
            "- `results_final/figures/Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.png`",
            "- `results_final/figures/Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.pdf`",
            "",
            "## DCA alignment",
            "",
            f"- Existing DCA source read: `{DCA_SOURCE}`.",
            "- P15/eICU threshold net benefit was aligned against the existing DCA summary when matching thresholds were available.",
            "",
            "## Validation warnings",
            "",
        ]
    )
    if warnings:
        audit_md.extend([f"- {w}" for w in warnings])
    else:
        audit_md.append("- validation_warnings = []")
    (OUT_TEXT / "P15_threshold_specific_performance_audit.md").write_text("\n".join(audit_md) + "\n", encoding="utf-8")


def plot_threshold_figure(point: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=300)
    x = point["threshold"].astype(float).to_numpy()
    axes[0].plot(x, point["sensitivity_recall"], marker="o", label="Sensitivity / recall", color="#1f5a93")
    axes[0].plot(x, point["PPV"], marker="o", label="PPV", color="#b4552b")
    axes[0].plot(x, point["screen_positive_proportion"], marker="o", label="Screen-positive proportion", color="#5f7f3a")
    axes[0].set_xlabel("Risk threshold")
    axes[0].set_ylabel("Metric value")
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(frameon=False, loc="best")
    axes[0].set_title("Threshold-specific operating metrics")

    axes[1].plot(x, point["net_benefit"], marker="o", label="P15 net benefit", color="#1f5a93")
    axes[1].plot(x, point["treat_all_net_benefit"], marker="o", label="Treat all", color="#777777")
    axes[1].axhline(0, color="#222222", linewidth=0.8, linestyle="--", label="Treat none")
    axes[1].set_xlabel("Risk threshold")
    axes[1].set_ylabel("Net benefit")
    axes[1].set_title("Decision-curve context")
    axes[1].legend(frameon=False, loc="best")
    fig.suptitle("Supplementary Figure Sx. P15 threshold-specific sensitivity and PPV in eICU")
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.png", dpi=300)
    fig.savefig(OUT_FIGURES / "Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.pdf")
    plt.close(fig)


def validate_outputs(paths: list[Path]) -> list[str]:
    warnings = []
    for path in paths:
        if not path.exists():
            warnings.append(f"missing_output_file: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore") if path.suffix.lower() in [".md", ".csv"] else ""
        if "[下限]" in text or "[上限]" in text:
            warnings.append(f"placeholder_ci_found: {path}")
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
            if df.isin([np.inf, -np.inf]).any().any():
                warnings.append(f"inf_found: {path}")
            # CI tables should not contain NaN; audit files may use textual missing markers instead.
            if "bootstrap_ci" in path.name.lower() or "Supplementary_Table_Sx" in path.name:
                if df.isna().any().any():
                    warnings.append(f"nan_found_in_ci_table: {path}")
    return warnings


def main() -> None:
    warnings: list[str] = []
    audit = audit_prediction_files()

    model_ready_external = pd.read_parquet(MODEL_READY_EXTERNAL)
    predictions: dict[str, pd.DataFrame] = {}
    for model_name, path in FROZEN_MODELS.items():
        if path.exists():
            predictions[model_name] = predict_from_frozen_model(model_name, path, model_ready_external)
        else:
            warnings.append(f"missing_prediction_file: {path}")
    for model_name, path in EXTERNAL_PRED_MODELS.items():
        if path.exists():
            predictions[model_name] = normalize_prediction_file(path, model_name)
        else:
            warnings.append(f"missing_prediction_file: {path}")

    point_check_rows = []
    comparison_rows = []
    for model_name, df in predictions.items():
        metrics = point_metrics(df)
        expected = EXPECTED_POINT_ESTIMATES.get(model_name, {})
        for metric_name, value in metrics.items():
            if metric_name in expected:
                diff = abs(value - expected[metric_name])
                if diff > 0.005:
                    warnings.append(f"point_estimate_warning: {model_name} {metric_name} computed {value:.4f} expected {expected[metric_name]:.4f}")
        point_check_rows.append({"model_name": model_name, **metrics})
        tm = threshold_metrics(df, model_name)
        comparison_rows.append(tm)

    comparison = pd.concat(comparison_rows, ignore_index=True)
    write_csv_no_nan(comparison, OUT_TABLES / "eICU_threshold_performance_model_comparison.csv")

    p15 = predictions["P15_clinically_parsimonious_transport_model"]
    p15_point = threshold_metrics(p15, "P15_clinically_parsimonious_transport_model")
    p15_point = align_existing_dca(p15_point, warnings)
    write_csv_no_nan(p15_point, OUT_TABLES / "P15_eICU_threshold_specific_performance.csv")
    ci = bootstrap_threshold_ci(p15, cluster_col="patient_id")
    integrated = make_integrated_table(p15_point, ci)
    supplementary_table(p15_point, ci, integrated)
    plot_threshold_figure(p15_point)

    write_csv_no_nan(
        pd.DataFrame(point_check_rows),
        OUT_TABLES / "threshold_point_estimate_reproduction_check.csv",
    )

    write_text_outputs(p15_point, integrated, audit, warnings)

    outputs = [
        OUT_TABLES / "threshold_prediction_file_audit.csv",
        OUT_TABLES / "P15_eICU_threshold_specific_performance.csv",
        OUT_TABLES / "P15_eICU_threshold_specific_performance_bootstrap_ci.csv",
        OUT_TABLES / "P15_eICU_threshold_DCA_integrated_table.csv",
        OUT_TABLES / "eICU_threshold_performance_model_comparison.csv",
        OUT_TABLES / "Supplementary_Table_Sx_P15_threshold_specific_operational_performance.csv",
        OUT_TEXT / "Supplementary_Table_Sx_P15_threshold_specific_operational_performance_zh.md",
        OUT_TEXT / "P15_threshold_specific_results_insert_zh.md",
        OUT_TEXT / "P15_threshold_specific_discussion_insert_zh.md",
        OUT_TEXT / "P15_threshold_specific_performance_audit.md",
        OUT_FIGURES / "Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.png",
        OUT_FIGURES / "Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.pdf",
    ]
    validation_warnings = validate_outputs(outputs)
    warnings.extend(validation_warnings)

    # Refresh audit with final validation warnings.
    write_text_outputs(p15_point, integrated, audit, warnings)

    summary = {
        "validation_warnings": warnings,
        "p15_event_rate": float(p15_point["prevalence"].iloc[0]),
        "key_thresholds": {
            str(row["threshold"]): {
                "sensitivity_recall": float(row["sensitivity_recall"]),
                "PPV": float(row["PPV"]),
                "net_benefit": float(row["net_benefit"]),
            }
            for _, row in p15_point.iterrows()
        },
        "outputs": [str(p.relative_to(REPO)) for p in outputs],
    }
    (OUT_TEXT / "P15_threshold_specific_run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
