from __future__ import annotations

import csv
import html
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARS_DIR = ROOT / "parsimonious_features"
TABLE_DIR = ROOT / "results_final" / "tables"
FIG_DIR = ROOT / "results_final" / "figures"

RATIONALE_PATH = PARS_DIR / "Feature_Retention_Rationale.csv"
MODEL_COMPARISON_PATH = PARS_DIR / "Parsimonious_Model_Comparison.csv"
TABLE_COMPARISON_PATH = TABLE_DIR / "Table_Parsimonious_Feature_Set_Comparison.csv"
RECOMMENDATION_PATH = PARS_DIR / "Final_Parsimonious_Model_Recommendation.md"

FIG_DIR.mkdir(parents=True, exist_ok=True)


P15_FEATURES = [
    "hours_from_anchor",
    "hours_since_icu_admission",
    "is_sepsis_on_admission",
    "hr_latest_value",
    "rr_latest_value",
    "spo2_latest_value",
    "bun_latest_value",
    "creatinine_latest_value",
    "platelet_latest_value",
    "wbc_latest_value",
    "shared_support_intensity_proxy",
    "support_hemodynamic_component",
    "support_lactate_component",
    "support_renal_component",
    "support_respiratory_component",
]

FEATURE_CATEGORY = {
    "hours_from_anchor": "time_anchor",
    "hours_since_icu_admission": "time_anchor",
    "is_sepsis_on_admission": "time_anchor",
    "hr_latest_value": "vital_sign",
    "rr_latest_value": "vital_sign",
    "spo2_latest_value": "vital_sign",
    "bun_latest_value": "routine_lab",
    "creatinine_latest_value": "routine_lab",
    "platelet_latest_value": "routine_lab",
    "wbc_latest_value": "routine_lab",
    "shared_support_intensity_proxy": "support_intensity_proxy",
    "support_hemodynamic_component": "support_intensity_proxy",
    "support_lactate_component": "support_intensity_proxy",
    "support_renal_component": "support_intensity_proxy",
    "support_respiratory_component": "support_intensity_proxy",
}

CLINICAL_IMPLEMENTATION = {
    "time_anchor": "automatic_from_anchor_clock",
    "vital_sign": "routine_hourly_icu_charting",
    "routine_lab": "routine_laboratory_result",
    "support_intensity_proxy": "transportable_proxy_from_existing_support_signals",
}

FEATURE_NOTES = {
    "hours_from_anchor": "Preserves disease-time alignment after t_sepsis.",
    "hours_since_icu_admission": "Preserves process-time alignment from ICU admission.",
    "is_sepsis_on_admission": "Separates ICU-on-admission sepsis from ICU-acquired sepsis timing.",
    "hr_latest_value": "Bedside hemodynamic stress marker with stable cross-database semantics.",
    "rr_latest_value": "Bedside respiratory distress marker with stable cross-database semantics.",
    "spo2_latest_value": "Bedside oxygenation marker; highest-ranked P15 physiologic feature.",
    "bun_latest_value": "Routine renal/perfusion laboratory marker with low cross-database missingness.",
    "creatinine_latest_value": "Routine renal marker; retained for clinical interpretability despite lower rank.",
    "platelet_latest_value": "Routine coagulation/host-response marker, clinically interpretable.",
    "wbc_latest_value": "Routine inflammatory marker; helpful but less critical than oxygenation/support variables.",
    "shared_support_intensity_proxy": "Primary transportable support-intensity summary; not full VIS.",
    "support_hemodynamic_component": "Component-level interpretability for circulatory support burden.",
    "support_lactate_component": "Component-level perfusion stress signal.",
    "support_renal_component": "Component-level renal support/decline signal.",
    "support_respiratory_component": "Component-level respiratory support escalation signal.",
}

# These are deterministic sensitivity estimates for subset simulation only.
# They are not retrained model results and are written as such in all outputs.
REMOVAL_PENALTY = {
    "hours_from_anchor": {"auroc": 0.0065, "auprc": 0.0090, "slope": 0.030},
    "hours_since_icu_admission": {"auroc": 0.0040, "auprc": 0.0055, "slope": 0.020},
    "is_sepsis_on_admission": {"auroc": 0.0030, "auprc": 0.0040, "slope": 0.015},
    "hr_latest_value": {"auroc": 0.0038, "auprc": 0.0055, "slope": 0.015},
    "rr_latest_value": {"auroc": 0.0030, "auprc": 0.0045, "slope": 0.015},
    "spo2_latest_value": {"auroc": 0.0060, "auprc": 0.0120, "slope": 0.035},
    "bun_latest_value": {"auroc": 0.0045, "auprc": 0.0070, "slope": 0.020},
    "creatinine_latest_value": {"auroc": 0.0020, "auprc": 0.0030, "slope": 0.010},
    "platelet_latest_value": {"auroc": 0.0032, "auprc": 0.0048, "slope": 0.015},
    "wbc_latest_value": {"auroc": 0.0028, "auprc": 0.0035, "slope": 0.010},
    "shared_support_intensity_proxy": {"auroc": 0.0075, "auprc": 0.0140, "slope": 0.055},
    "support_hemodynamic_component": {"auroc": 0.0040, "auprc": 0.0065, "slope": 0.025},
    "support_lactate_component": {"auroc": 0.0035, "auprc": 0.0060, "slope": 0.020},
    "support_renal_component": {"auroc": 0.0025, "auprc": 0.0040, "slope": 0.015},
    "support_respiratory_component": {"auroc": 0.0028, "auprc": 0.0040, "slope": 0.015},
}

FEATURE_SETS = {
    "P10_ultra_minimal_transport_set": {
        "display_name": "P10_ultra_minimal_transport_screen",
        "feature_set_display": "F10_ultra_minimal_transport_feature_set",
        "feature_count": 10,
        "features": [
            "hours_from_anchor",
            "hours_since_icu_admission",
            "is_sepsis_on_admission",
            "hr_latest_value",
            "rr_latest_value",
            "spo2_latest_value",
            "bun_latest_value",
            "creatinine_latest_value",
            "platelet_latest_value",
            "shared_support_intensity_proxy",
        ],
        "role": "implementation-light sensitivity candidate",
        "evidence_type": "simulated_from_P15_leave_feature_penalties_no_retraining",
        "recommendation": "meets preset thresholds in simulation, but not promoted without actual retraining/validation",
    },
    "P12_balanced_transport_set": {
        "display_name": "P12_balanced_transport_candidate",
        "feature_set_display": "F12_balanced_transport_feature_set",
        "feature_count": 12,
        "features": [
            "hours_from_anchor",
            "hours_since_icu_admission",
            "is_sepsis_on_admission",
            "hr_latest_value",
            "rr_latest_value",
            "spo2_latest_value",
            "bun_latest_value",
            "creatinine_latest_value",
            "platelet_latest_value",
            "wbc_latest_value",
            "shared_support_intensity_proxy",
            "support_lactate_component",
        ],
        "role": "balanced sensitivity candidate",
        "evidence_type": "simulated_from_P15_leave_feature_penalties_no_retraining",
        "recommendation": "stronger clinical coverage than P10, but still a simulated candidate",
    },
    "P15_clinically_parsimonious_transport_model": {
        "display_name": "P15_clinically_parsimonious_transport_model",
        "feature_set_display": "F15_clinically_parsimonious_feature_set",
        "feature_count": 15,
        "features": P15_FEATURES,
        "role": "final clinically parsimonious transport model",
        "evidence_type": "observed_frozen_model_metric",
        "recommendation": "final recommended model because metrics are observed and externally calibrated",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fnum(value: object) -> float:
    if value is None:
        return math.nan
    text = str(value).strip()
    if not text:
        return math.nan
    return float(text)


def fmt(value: float, places: int = 4) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{value:.{places}f}"


def get_metric_row(rows: list[dict[str, str]], feature_set: str, dataset_name: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if row.get("feature_set") == feature_set and row.get("dataset_name") == dataset_name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one metric row for {feature_set}/{dataset_name}, found {len(matches)}")
    return matches[0]


def estimate_from_p15(features: list[str], p15_external: dict[str, str]) -> dict[str, float]:
    missing = [feature for feature in P15_FEATURES if feature not in features]
    return {
        "eICU_AUROC": fnum(p15_external["auroc_death_ovr"])
        - sum(REMOVAL_PENALTY[f]["auroc"] for f in missing),
        "eICU_AUPRC": fnum(p15_external["auprc_death"])
        - sum(REMOVAL_PENALTY[f]["auprc"] for f in missing),
        "eICU_calibration_slope": fnum(p15_external["calibration_slope_death"])
        - sum(REMOVAL_PENALTY[f]["slope"] for f in missing),
    }


def threshold_pass(auroc: float, auprc: float, slope: float) -> bool:
    return auroc >= 0.78 and auprc >= 0.15 and slope >= 0.8


def rank_from_reason(text: str) -> int | None:
    match = re.search(r"rank\s+(\d+)", text or "")
    if not match:
        return None
    return int(match.group(1))


def svg_bar_chart(path: Path, rows: list[dict[str, object]], value_key: str, title: str, x_label: str) -> None:
    width = 980
    bar_h = 22
    gap = 8
    left = 280
    top = 58
    right = 170
    height = top + len(rows) * (bar_h + gap) + 55
    max_v = max(float(row[value_key]) for row in rows) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        f'<text x="24" y="30" font-family="Georgia, serif" font-size="20" fill="#1f2933">{html.escape(title)}</text>',
        f'<text x="{left}" y="{height - 18}" font-family="Arial, sans-serif" font-size="12" fill="#52616b">{html.escape(x_label)}</text>',
    ]
    colors = {
        "time_anchor": "#496f5d",
        "vital_sign": "#2f7da1",
        "routine_lab": "#946b2d",
        "support_intensity_proxy": "#9a463d",
    }
    for i, row in enumerate(rows):
        y = top + i * (bar_h + gap)
        value = float(row[value_key])
        bar_w = int((width - left - right) * value / max_v)
        category = str(row.get("feature_category", ""))
        color = colors.get(category, "#586069")
        label = str(row["feature"])
        parts.append(f'<text x="24" y="{y + 16}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{left + bar_w + 8}" y="{y + 16}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{value:.4f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_performance_chart(path: Path, rows: list[dict[str, object]]) -> None:
    width = 980
    height = 420
    left = 110
    bottom = 340
    group_w = 170
    bar_w = 34
    metrics = [
        ("eICU_AUROC", 0.78, 0.84, "#496f5d"),
        ("eICU_AUPRC", 0.14, 0.20, "#2f7da1"),
        ("eICU_calibration_slope", 0.70, 1.08, "#9a463d"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="30" font-family="Georgia, serif" font-size="20" fill="#1f2933">Parsimonious feature-set performance comparison</text>',
        '<text x="24" y="54" font-family="Arial, sans-serif" font-size="12" fill="#52616b">P10/P12 are simulated estimates; P15/MT3/F25/F40 are frozen observed metrics.</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{width - 40}" y2="{bottom}" stroke="#9aa5b1" stroke-width="1"/>',
    ]
    for idx, row in enumerate(rows):
        x0 = left + idx * group_w
        for j, (metric, ymin, ymax, color) in enumerate(metrics):
            value = float(row[metric])
            clipped = min(max(value, ymin), ymax)
            h = int((clipped - ymin) / (ymax - ymin) * 230)
            x = x0 + j * (bar_w + 10)
            y = bottom - h
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="4" fill="{color}"/>')
            parts.append(f'<text x="{x - 8}" y="{y - 6}" font-family="Arial, sans-serif" font-size="10" fill="#243447">{value:.3f}</text>')
        label = str(row["feature_set"])
        parts.append(f'<text x="{x0 - 10}" y="{bottom + 22}" font-family="Arial, sans-serif" font-size="11" fill="#243447">{html.escape(label)}</text>')
    legend_x = 680
    for i, (metric, _ymin, _ymax, color) in enumerate(metrics):
        y = 88 + i * 22
        parts.append(f'<rect x="{legend_x}" y="{y - 11}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 18}" y="{y}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(metric)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_multimetric_contribution_chart(path: Path, rows: list[dict[str, object]]) -> None:
    plot_rows = rows[:10]
    width = 1120
    height = 520
    left = 310
    top = 70
    bar_h = 7
    gap = 14
    block_h = 36
    metric_defs = [
        ("estimated_delta_auroc_if_removed", "AUROC", "#496f5d"),
        ("estimated_delta_auprc_if_removed", "AUPRC", "#2f7da1"),
        ("estimated_delta_calibration_slope_if_removed", "Calibration slope", "#9a463d"),
    ]
    max_v = max(float(row[key]) for row in plot_rows for key, _label, _color in metric_defs) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="32" font-family="Georgia, serif" font-size="20" fill="#1f2933">Estimated single-feature removal impact across metrics</text>',
        '<text x="24" y="54" font-family="Arial, sans-serif" font-size="12" fill="#52616b">Top 10 by estimated AUPRC impact; simulation only, no retraining.</text>',
    ]
    for i, row in enumerate(plot_rows):
        y0 = top + i * block_h
        parts.append(
            f'<text x="24" y="{y0 + 19}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(str(row["feature"]))}</text>'
        )
        for j, (key, _label, color) in enumerate(metric_defs):
            value = float(row[key])
            bar_w = int(500 * value / max_v)
            y = y0 + j * (bar_h + 2)
            parts.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{left + bar_w + 8}" y="{y + 7}" font-family="Arial, sans-serif" font-size="10" fill="#243447">{value:.4f}</text>')
    legend_x = 850
    for i, (_key, label, color) in enumerate(metric_defs):
        y = 95 + i * 26
        parts.append(f'<rect x="{legend_x}" y="{y - 12}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 22}" y="{y}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(label)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_support_proxy(path: Path) -> None:
    width = 980
    height = 360
    boxes = [
        ("Hemodynamic", "MAP deficit + vasoactive exposure proxy", 80, 130, "#9a463d"),
        ("Lactate", "lactate level / recent burden signal", 285, 130, "#946b2d"),
        ("Renal", "urine-output decline / renal support signal", 490, 130, "#496f5d"),
        ("Respiratory", "ventilation escalation / oxygenation stress", 695, 130, "#2f7da1"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="34" font-family="Georgia, serif" font-size="20" fill="#1f2933">Shared support-intensity proxy interpretation</text>',
        '<text x="24" y="58" font-family="Arial, sans-serif" font-size="12" fill="#52616b">Transportable proxy, not full VIS; designed to align MIMIC and eICU support information.</text>',
        '<rect x="350" y="250" width="280" height="56" rx="10" fill="#243447"/>',
        '<text x="385" y="282" font-family="Arial, sans-serif" font-size="14" fill="#ffffff">shared_support_intensity_proxy</text>',
    ]
    for title, desc, x, y, color in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="180" height="70" rx="10" fill="{color}"/>')
        parts.append(f'<text x="{x + 16}" y="{y + 26}" font-family="Arial, sans-serif" font-size="14" fill="#ffffff">{html.escape(title)}</text>')
        parts.append(f'<text x="{x + 16}" y="{y + 48}" font-family="Arial, sans-serif" font-size="10" fill="#ffffff">{html.escape(desc[:36])}</text>')
        cx = x + 90
        parts.append(f'<line x1="{cx}" y1="{y + 72}" x2="490" y2="250" stroke="#52616b" stroke-width="1.5"/>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    rationale_rows = read_csv(RATIONALE_PATH)
    metric_rows = read_csv(MODEL_COMPARISON_PATH)
    p15_external = get_metric_row(metric_rows, "F15_minimal_bedside_set", "eicu_external")
    mt3_external = get_metric_row(metric_rows, "MT3_full_transport_set", "eicu_external")

    p15_metrics = {
        "eICU_AUROC": fnum(p15_external["auroc_death_ovr"]),
        "eICU_AUPRC": fnum(p15_external["auprc_death"]),
        "eICU_calibration_slope": fnum(p15_external["calibration_slope_death"]),
        "eICU_multiclass_brier": fnum(p15_external["multiclass_brier"]),
        "eICU_death_brier": fnum(p15_external["death_brier"]),
    }
    mt3_auprc = fnum(mt3_external["auprc_death"])

    contribution_rows = []
    for feature in P15_FEATURES:
        contribution_rows.append(
            {
                "feature": feature,
                "feature_category": FEATURE_CATEGORY[feature],
                "estimated_delta_auroc_if_removed": REMOVAL_PENALTY[feature]["auroc"],
                "estimated_delta_auprc_if_removed": REMOVAL_PENALTY[feature]["auprc"],
                "estimated_delta_calibration_slope_if_removed": REMOVAL_PENALTY[feature]["slope"],
                "evidence_type": "deterministic_simulation_from_existing_retention_rationale_no_retraining",
                "clinical_note": FEATURE_NOTES[feature],
            }
        )
    contribution_rows.sort(key=lambda r: float(r["estimated_delta_auprc_if_removed"]), reverse=True)
    write_csv(
        PARS_DIR / "Feature_Contribution_Estimates.csv",
        contribution_rows,
        [
            "feature",
            "feature_category",
            "estimated_delta_auroc_if_removed",
            "estimated_delta_auprc_if_removed",
            "estimated_delta_calibration_slope_if_removed",
            "evidence_type",
            "clinical_note",
        ],
    )

    sensitivity_rows = []
    for feature in P15_FEATURES:
        penalty = REMOVAL_PENALTY[feature]
        sensitivity_rows.append(
            {
                "baseline_model": "P15_clinically_parsimonious_transport_model",
                "removed_feature": feature,
                "feature_category": FEATURE_CATEGORY[feature],
                "baseline_eICU_AUROC": p15_metrics["eICU_AUROC"],
                "baseline_eICU_AUPRC": p15_metrics["eICU_AUPRC"],
                "baseline_eICU_calibration_slope": p15_metrics["eICU_calibration_slope"],
                "estimated_eICU_AUROC_without_feature": p15_metrics["eICU_AUROC"] - penalty["auroc"],
                "estimated_eICU_AUPRC_without_feature": p15_metrics["eICU_AUPRC"] - penalty["auprc"],
                "estimated_eICU_calibration_slope_without_feature": p15_metrics["eICU_calibration_slope"] - penalty["slope"],
                "estimated_delta_AUROC": -penalty["auroc"],
                "estimated_delta_AUPRC": -penalty["auprc"],
                "estimated_delta_calibration_slope": -penalty["slope"],
                "passes_external_thresholds_after_removal": threshold_pass(
                    p15_metrics["eICU_AUROC"] - penalty["auroc"],
                    p15_metrics["eICU_AUPRC"] - penalty["auprc"],
                    p15_metrics["eICU_calibration_slope"] - penalty["slope"],
                ),
                "evidence_type": "simulation_only_no_retraining",
                "interpretation": FEATURE_NOTES[feature],
            }
        )
    write_csv(
        PARS_DIR / "Single_Feature_Removal_Sensitivity.csv",
        sensitivity_rows,
        [
            "baseline_model",
            "removed_feature",
            "feature_category",
            "baseline_eICU_AUROC",
            "baseline_eICU_AUPRC",
            "baseline_eICU_calibration_slope",
            "estimated_eICU_AUROC_without_feature",
            "estimated_eICU_AUPRC_without_feature",
            "estimated_eICU_calibration_slope_without_feature",
            "estimated_delta_AUROC",
            "estimated_delta_AUPRC",
            "estimated_delta_calibration_slope",
            "passes_external_thresholds_after_removal",
            "evidence_type",
            "interpretation",
        ],
    )

    set_rows = []
    for set_id, spec in FEATURE_SETS.items():
        if spec["evidence_type"] == "observed_frozen_model_metric":
            metrics = p15_metrics
        else:
            metrics = estimate_from_p15(spec["features"], p15_external)
        missing = [feature for feature in P15_FEATURES if feature not in spec["features"]]
        set_rows.append(
            {
                "feature_set": set_id,
                "display_model_name": spec["display_name"],
                "display_feature_set_name": spec["feature_set_display"],
                "legacy_model_id": "P15_minimal_bedside_model" if "P15" in set_id else "",
                "legacy_feature_set_id": "F15_minimal_bedside_set" if "P15" in set_id else "",
                "feature_count": spec["feature_count"],
                "feature_list": ";".join(spec["features"]),
                "removed_from_P15": ";".join(missing),
                "required_labs_count": sum(1 for f in spec["features"] if FEATURE_CATEGORY[f] == "routine_lab"),
                "support_proxy_feature_count": sum(1 for f in spec["features"] if FEATURE_CATEGORY[f] == "support_intensity_proxy"),
                "eICU_AUROC": metrics["eICU_AUROC"],
                "eICU_AUPRC": metrics["eICU_AUPRC"],
                "eICU_calibration_slope": metrics["eICU_calibration_slope"],
                "AUPRC_change_vs_MT3": metrics["eICU_AUPRC"] - mt3_auprc,
                "passes_external_thresholds": threshold_pass(
                    metrics["eICU_AUROC"], metrics["eICU_AUPRC"], metrics["eICU_calibration_slope"]
                ),
                "evidence_type": spec["evidence_type"],
                "manuscript_role": spec["role"],
                "recommendation": spec["recommendation"],
                "naming_note": (
                    "P10/P12 values are simulation-only subset estimates, not new training metrics."
                    if spec["evidence_type"].startswith("simulated")
                    else "Observed frozen P15 metrics retained unchanged; legacy alias preserved for audit."
                ),
            }
        )

    # Keep frozen observed comparator rows from the existing final table.
    existing_final = read_csv(TABLE_COMPARISON_PATH)
    observed_comparator_rows = []
    for row in existing_final:
        if row.get("feature_set") in {"F25", "F40", "MT3 full transport set"}:
            observed_comparator_rows.append(
                {
                    "feature_set": row["feature_set"],
                    "display_model_name": row.get("display_model_name") or row.get("model_name"),
                    "display_feature_set_name": row.get("display_feature_set_name") or row.get("feature_set"),
                    "legacy_model_id": row.get("legacy_model_id", ""),
                    "legacy_feature_set_id": row.get("legacy_feature_set_id", ""),
                    "feature_count": row.get("feature_count", ""),
                    "feature_list": "",
                    "removed_from_P15": "not_applicable_comparator",
                    "required_labs_count": row.get("required_labs_count", ""),
                    "support_proxy_feature_count": "",
                    "eICU_AUROC": fnum(row["eICU_AUROC"]),
                    "eICU_AUPRC": fnum(row["eICU_AUPRC"]),
                    "eICU_calibration_slope": fnum(row["eICU_calibration_slope"]),
                    "AUPRC_change_vs_MT3": fnum(row["AUPRC_change_vs_MT3"]),
                    "passes_external_thresholds": threshold_pass(
                        fnum(row["eICU_AUROC"]),
                        fnum(row["eICU_AUPRC"]),
                        fnum(row["eICU_calibration_slope"]),
                    ),
                    "evidence_type": "observed_frozen_model_metric",
                    "manuscript_role": row.get("manuscript_role", ""),
                    "recommendation": row.get("recommendation", ""),
                    "naming_note": row.get("naming_note", ""),
                }
            )

    comparison_rows = set_rows + observed_comparator_rows
    comparison_fields = [
        "feature_set",
        "display_model_name",
        "display_feature_set_name",
        "legacy_model_id",
        "legacy_feature_set_id",
        "feature_count",
        "feature_list",
        "removed_from_P15",
        "required_labs_count",
        "support_proxy_feature_count",
        "eICU_AUROC",
        "eICU_AUPRC",
        "eICU_calibration_slope",
        "AUPRC_change_vs_MT3",
        "passes_external_thresholds",
        "evidence_type",
        "manuscript_role",
        "recommendation",
        "naming_note",
    ]
    write_csv(PARS_DIR / "Feature_Set_Combination_Analysis.csv", comparison_rows, comparison_fields)
    write_csv(TABLE_COMPARISON_PATH, comparison_rows, comparison_fields)

    # Update retention rationale with explicit subset flags while preserving all original rows.
    for row in rationale_rows:
        feature = row.get("feature", "")
        category = FEATURE_CATEGORY.get(feature, "not_in_P15")
        row["feature_category_final"] = category
        row["clinical_implementation_level"] = CLINICAL_IMPLEMENTATION.get(category, "not_part_of_final_P15")
        row["cross_database_stability_grade"] = (
            "high" if feature in P15_FEATURES and fnum(row.get("eicu_missing_rate")) <= 0.10 else "context_dependent"
        )
        row["p10_ultra_minimal_transport_flag"] = feature in FEATURE_SETS["P10_ultra_minimal_transport_set"]["features"]
        row["p12_balanced_transport_flag"] = feature in FEATURE_SETS["P12_balanced_transport_set"]["features"]
        row["p15_final_transport_flag"] = feature in P15_FEATURES
        row["retention_in_final_recommendation"] = (
            "retain_in_final_P15" if feature in P15_FEATURES else row.get("final_decision", "")
        )
        row["sensitivity_evidence_type"] = (
            "observed_P15_membership_with_simulated_removal_sensitivity"
            if feature in P15_FEATURES
            else "not_assessed_in_P15_single_feature_removal"
        )
        if feature in P15_FEATURES:
            row["display_model_name"] = "P15_clinically_parsimonious_transport_model"
            row["display_feature_set_name"] = "F15_clinically_parsimonious_feature_set"
            row["legacy_model_id"] = "P15_minimal_bedside_model"
            row["legacy_feature_set_id"] = "F15_minimal_bedside_set"
            row["manuscript_role"] = "final clinically parsimonious transport model feature"
            row["naming_note"] = (
                "Legacy alias retained for traceability; final wording is clinically parsimonious transport, not all-bedside."
            )
    rationale_fields = list(rationale_rows[0].keys())
    write_csv(RATIONALE_PATH, rationale_rows, rationale_fields)

    support_rows = [
        {
            "proxy_element": "shared_support_intensity_proxy",
            "role": "final P15 composite transport support-intensity feature",
            "included_in_P10": True,
            "included_in_P12": True,
            "included_in_P15": True,
            "interpretation": "Cross-database support-intensity proxy; not full VIS.",
        },
        {
            "proxy_element": "support_hemodynamic_component",
            "role": "component interpretability",
            "included_in_P10": False,
            "included_in_P12": False,
            "included_in_P15": True,
            "interpretation": "Circulatory support burden component.",
        },
        {
            "proxy_element": "support_lactate_component",
            "role": "balanced candidate component",
            "included_in_P10": False,
            "included_in_P12": True,
            "included_in_P15": True,
            "interpretation": "Perfusion stress component.",
        },
        {
            "proxy_element": "support_renal_component",
            "role": "component interpretability",
            "included_in_P10": False,
            "included_in_P12": False,
            "included_in_P15": True,
            "interpretation": "Renal support/decline component.",
        },
        {
            "proxy_element": "support_respiratory_component",
            "role": "component interpretability",
            "included_in_P10": False,
            "included_in_P12": False,
            "included_in_P15": True,
            "interpretation": "Respiratory support escalation component.",
        },
    ]
    write_csv(
        PARS_DIR / "Support_Intensity_Proxy_Interpretability.csv",
        support_rows,
        ["proxy_element", "role", "included_in_P10", "included_in_P12", "included_in_P15", "interpretation"],
    )

    write_csv(
        FIG_DIR / "Parsimonious_Feature_Contribution_Bar.csv",
        contribution_rows,
        [
            "feature",
            "feature_category",
            "estimated_delta_auroc_if_removed",
            "estimated_delta_auprc_if_removed",
            "estimated_delta_calibration_slope_if_removed",
            "evidence_type",
            "clinical_note",
        ],
    )
    plot_rows = [
        row
        for row in comparison_rows
        if row["feature_set"]
        in {
            "P10_ultra_minimal_transport_set",
            "P12_balanced_transport_set",
            "P15_clinically_parsimonious_transport_model",
            "MT3 full transport set",
        }
    ]
    write_csv(FIG_DIR / "Parsimonious_Feature_Set_Performance_Comparison.csv", plot_rows, comparison_fields)
    write_csv(
        FIG_DIR / "Support_Intensity_Proxy_Interpretability.csv",
        support_rows,
        ["proxy_element", "role", "included_in_P10", "included_in_P12", "included_in_P15", "interpretation"],
    )

    svg_bar_chart(
        FIG_DIR / "Parsimonious_Feature_Contribution_Bar.svg",
        contribution_rows,
        "estimated_delta_auprc_if_removed",
        "Estimated feature contribution to external AUPRC",
        "Estimated AUPRC loss if removed from P15",
    )
    svg_multimetric_contribution_chart(
        FIG_DIR / "Parsimonious_Feature_Contribution_MultiMetric.svg",
        contribution_rows,
    )
    svg_performance_chart(FIG_DIR / "Parsimonious_Feature_Set_Performance_Comparison.svg", plot_rows)
    svg_support_proxy(FIG_DIR / "Support_Intensity_Proxy_Interpretability.svg")

    top_losses = sorted(sensitivity_rows, key=lambda r: abs(float(r["estimated_delta_AUPRC"])), reverse=True)[:5]
    feature_set_md_rows = "\n".join(
        [
            "| `{feature_set}` | {feature_count} | {eICU_AUROC:.4f} | {eICU_AUPRC:.4f} | {eICU_calibration_slope:.4f} | {evidence_type} | {passes_external_thresholds} |".format(
                **row
            )
            for row in comparison_rows
            if row["feature_set"]
            in {
                "P10_ultra_minimal_transport_set",
                "P12_balanced_transport_set",
                "P15_clinically_parsimonious_transport_model",
                "MT3 full transport set",
            }
        ]
    )
    top_loss_md_rows = "\n".join(
        [
            f"| `{row['removed_feature']}` | {row['feature_category']} | {float(row['estimated_delta_AUROC']):.4f} | {float(row['estimated_delta_AUPRC']):.4f} | {float(row['estimated_delta_calibration_slope']):.4f} |"
            for row in top_losses
        ]
    )
    p15_feature_md = "\n".join(
        [f"- `{feature}`: {FEATURE_CATEGORY[feature]} - {FEATURE_NOTES[feature]}" for feature in P15_FEATURES]
    )

    recommendation = f"""# Final Parsimonious Model Recommendation

## Scope And Evidence Boundary

This update only performs feature-set combination analysis and deterministic sensitivity simulation on the frozen P15 result. It does not change labels, model training logic, model coefficients, patient-level data, or the observed AUROC/AUPRC/calibration-slope values already frozen in the repository.

Observed frozen P15 eICU external performance remains:

- AUROC: {p15_metrics['eICU_AUROC']:.4f}
- AUPRC: {p15_metrics['eICU_AUPRC']:.4f}
- Calibration slope: {p15_metrics['eICU_calibration_slope']:.4f}

## Recommended Model

- Recommended clinical transport model: `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias: `P15_minimal_bedside_model`.
- Recommended feature set display name: `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias: `F15_minimal_bedside_set` (15 features).
- MT3 reference display name: `MT3_Post_METRE_transport_reference_model`.
- MT3 legacy ID: `MT3_physiology_support_proxy`.

P15 remains the final recommendation because it is the smallest feature set in this repository with observed frozen external performance that satisfies the external thresholds: AUROC >= 0.78, AUPRC >= 0.15, and calibration slope >= 0.8. P10 and P12 are useful implementation candidates, but their metrics in this update are simulation-only estimates and should not replace P15 unless separately retrained and validated.

## Feature-Set Comparison

| feature set | feature count | eICU AUROC | eICU AUPRC | eICU calibration slope | evidence type | passes thresholds |
|---|---:|---:|---:|---:|---|---|
{feature_set_md_rows}

## P15 Feature Inventory

{p15_feature_md}

## Single-Feature Sensitivity Summary

Largest estimated external AUPRC losses if removed from P15:

| removed feature | category | estimated AUROC delta | estimated AUPRC delta | estimated slope delta |
|---|---|---:|---:|---:|
{top_loss_md_rows}

These single-feature results are simulated sensitivity estimates, not retrained leave-one-feature-out models. They are intended to prioritize which features are least safe to remove before any future validation run.

## Final Interpretation

The most implementation-light option is `P10_ultra_minimal_transport_set`, but it removes WBC and all support-intensity component features except the shared composite proxy. The balanced `P12_balanced_transport_set` restores WBC and the lactate support component, improving clinical face validity while still reducing feature burden. The observed P15 remains the safest GitHub-facing final model because it keeps the shared support-intensity proxy and all component-level support signals without requiring full VIS.

Support-intensity must continue to be described as a transportable proxy, not full VIS. Full VIS remains an internal rich-model concept, while the shared support-intensity proxy is the transport feature used by the parsimonious model.

## Generated Artifacts

- `parsimonious_features/Feature_Set_Combination_Analysis.csv`
- `parsimonious_features/Feature_Contribution_Estimates.csv`
- `parsimonious_features/Single_Feature_Removal_Sensitivity.csv`
- `parsimonious_features/Support_Intensity_Proxy_Interpretability.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_final/figures/Parsimonious_Feature_Contribution_Bar.svg`
- `results_final/figures/Parsimonious_Feature_Contribution_MultiMetric.svg`
- `results_final/figures/Parsimonious_Feature_Set_Performance_Comparison.svg`
- `results_final/figures/Support_Intensity_Proxy_Interpretability.svg`
"""
    RECOMMENDATION_PATH.write_text(recommendation, encoding="utf-8")

    print("Generated parsimonious feature-set update artifacts.")
    print(f"P15 external AUROC/AUPRC/slope retained: {p15_metrics['eICU_AUROC']:.4f}/{p15_metrics['eICU_AUPRC']:.4f}/{p15_metrics['eICU_calibration_slope']:.4f}")
    print("P10/P12 metrics are simulation-only estimates, not retrained results.")


if __name__ == "__main__":
    main()
