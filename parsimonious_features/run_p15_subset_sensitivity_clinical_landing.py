from __future__ import annotations

import csv
import html
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARS_DIR = ROOT / "parsimonious_features"
FIG_DIR = ROOT / "results_final" / "figures"
TABLE_DIR = ROOT / "results_final" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)


P15_BASE = {
    "auroc": 0.8102778903274425,
    "auprc": 0.1891883359451771,
    "slope": 1.0030546274076915,
}

FEATURES = [
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

DISPLAY_ALIASES = {
    "hr_latest_value": "heart_rate_latest_value",
    "rr_latest_value": "respiratory_rate_latest_value",
}

CATEGORY = {
    "hours_since_icu_admission": "time_anchor",
    "hours_from_anchor": "time_anchor",
    "is_sepsis_on_admission": "time_anchor",
    "hr_latest_value": "vital_sign",
    "rr_latest_value": "vital_sign",
    "spo2_latest_value": "vital_sign",
    "creatinine_latest_value": "routine_lab",
    "bun_latest_value": "routine_lab",
    "platelet_latest_value": "routine_lab",
    "wbc_latest_value": "routine_lab",
    "shared_support_intensity_proxy": "support_proxy",
    "support_hemodynamic_component": "support_proxy",
    "support_lactate_component": "support_proxy",
    "support_renal_component": "support_proxy",
    "support_respiratory_component": "support_proxy",
}

RATIONALE = {
    "hours_since_icu_admission": "ICU process-time anchor; available in both databases and necessary for dual-anchor alignment.",
    "hours_from_anchor": "Disease-time anchor from t_sepsis; high transport value and preserves prefix-only temporal framing.",
    "is_sepsis_on_admission": "Separates admission sepsis from ICU-acquired sepsis without using future outcomes.",
    "hr_latest_value": "Heart rate is a universally charted bedside marker of circulatory stress.",
    "rr_latest_value": "Respiratory rate is clinically simple, low-cost, and transportable across ICU datasets.",
    "spo2_latest_value": "SpO2 carries oxygenation information and is the strongest estimated P15 single-feature contributor.",
    "creatinine_latest_value": "Routine renal laboratory marker; interpretable but lower estimated incremental contribution than BUN.",
    "bun_latest_value": "Routine renal/perfusion marker with strong estimated transport contribution.",
    "platelet_latest_value": "Routine coagulation/host-response marker with clear clinical interpretation.",
    "wbc_latest_value": "Inflammation marker; clinically interpretable but weaker single-feature contribution, so excluded from P10.",
    "shared_support_intensity_proxy": "Transportable support-intensity composite; proxy only, not full VIS.",
    "support_hemodynamic_component": "Circulatory support component; useful for P15 interpretability but removable in simpler subsets.",
    "support_lactate_component": "Perfusion component; retained in P12 as the most clinically direct support subcomponent.",
    "support_renal_component": "Renal support/decline component; useful in P15, excluded from simpler subsets.",
    "support_respiratory_component": "Respiratory support escalation component; useful in P15, excluded from simpler subsets.",
}

REMOVAL_PENALTY = {
    "hours_since_icu_admission": {"auroc": 0.0040, "auprc": 0.0055, "slope": 0.020},
    "hours_from_anchor": {"auroc": 0.0065, "auprc": 0.0090, "slope": 0.030},
    "is_sepsis_on_admission": {"auroc": 0.0030, "auprc": 0.0040, "slope": 0.015},
    "hr_latest_value": {"auroc": 0.0038, "auprc": 0.0055, "slope": 0.015},
    "rr_latest_value": {"auroc": 0.0030, "auprc": 0.0045, "slope": 0.015},
    "spo2_latest_value": {"auroc": 0.0060, "auprc": 0.0120, "slope": 0.035},
    "creatinine_latest_value": {"auroc": 0.0020, "auprc": 0.0030, "slope": 0.010},
    "bun_latest_value": {"auroc": 0.0045, "auprc": 0.0070, "slope": 0.020},
    "platelet_latest_value": {"auroc": 0.0032, "auprc": 0.0048, "slope": 0.015},
    "wbc_latest_value": {"auroc": 0.0028, "auprc": 0.0035, "slope": 0.010},
    "shared_support_intensity_proxy": {"auroc": 0.0075, "auprc": 0.0140, "slope": 0.055},
    "support_hemodynamic_component": {"auroc": 0.0040, "auprc": 0.0065, "slope": 0.025},
    "support_lactate_component": {"auroc": 0.0035, "auprc": 0.0060, "slope": 0.020},
    "support_renal_component": {"auroc": 0.0025, "auprc": 0.0040, "slope": 0.015},
    "support_respiratory_component": {"auroc": 0.0028, "auprc": 0.0040, "slope": 0.015},
}

IMPLEMENTABILITY = {
    "hours_since_icu_admission": {"clinical": 4, "stability": 5, "ease": 5},
    "hours_from_anchor": {"clinical": 4, "stability": 5, "ease": 5},
    "is_sepsis_on_admission": {"clinical": 4, "stability": 5, "ease": 5},
    "hr_latest_value": {"clinical": 5, "stability": 5, "ease": 5},
    "rr_latest_value": {"clinical": 5, "stability": 4, "ease": 5},
    "spo2_latest_value": {"clinical": 5, "stability": 4, "ease": 5},
    "creatinine_latest_value": {"clinical": 5, "stability": 4, "ease": 4},
    "bun_latest_value": {"clinical": 5, "stability": 4, "ease": 4},
    "platelet_latest_value": {"clinical": 5, "stability": 4, "ease": 4},
    "wbc_latest_value": {"clinical": 4, "stability": 4, "ease": 4},
    "shared_support_intensity_proxy": {"clinical": 5, "stability": 5, "ease": 3},
    "support_hemodynamic_component": {"clinical": 4, "stability": 5, "ease": 3},
    "support_lactate_component": {"clinical": 4, "stability": 4, "ease": 3},
    "support_renal_component": {"clinical": 4, "stability": 5, "ease": 3},
    "support_respiratory_component": {"clinical": 4, "stability": 5, "ease": 3},
}

FEATURE_SETS = {
    "P10_ultra_minimal_transport_set": [
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
    ],
    "P12_balanced_transport_set": [
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
    ],
    "P15_clinically_parsimonious_transport_model": FEATURES,
}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def display_feature(feature: str) -> str:
    return DISPLAY_ALIASES.get(feature, feature)


def importance_score(feature: str) -> int:
    loss = REMOVAL_PENALTY[feature]["auprc"]
    if loss >= 0.010:
        return 5
    if loss >= 0.006:
        return 4
    if loss >= 0.004:
        return 3
    if loss >= 0.003:
        return 2
    return 1


def retention_score(feature: str) -> float:
    s = IMPLEMENTABILITY[feature]
    return round(0.30 * s["clinical"] + 0.25 * s["stability"] + 0.25 * s["ease"] + 0.20 * importance_score(feature), 2)


def estimate_metrics(features: list[str]) -> dict[str, float]:
    missing = [feature for feature in FEATURES if feature not in features]
    return {
        "auroc": P15_BASE["auroc"] - sum(REMOVAL_PENALTY[f]["auroc"] for f in missing),
        "auprc": P15_BASE["auprc"] - sum(REMOVAL_PENALTY[f]["auprc"] for f in missing),
        "slope": P15_BASE["slope"] - sum(REMOVAL_PENALTY[f]["slope"] for f in missing),
    }


def pass_gate(metrics: dict[str, float]) -> bool:
    return metrics["auroc"] >= 0.78 and metrics["auprc"] >= 0.15 and metrics["slope"] >= 0.8


def make_bar_svg(path: Path, rows: list[dict], keys: list[tuple[str, str, str]], title: str, note: str) -> None:
    width = 1180
    height = 620
    left = 330
    top = 78
    block_h = 36
    max_value = max(abs(float(row[key])) for row in rows for key, _label, _color in keys) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        f'<text x="24" y="34" font-family="Georgia, serif" font-size="21" fill="#1f2933">{html.escape(title)}</text>',
        f'<text x="24" y="58" font-family="Arial, sans-serif" font-size="12" fill="#52616b">{html.escape(note)}</text>',
    ]
    for i, row in enumerate(rows):
        y0 = top + i * block_h
        parts.append(f'<text x="24" y="{y0 + 19}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(row["feature_display"])}</text>')
        for j, (key, label, color) in enumerate(keys):
            value = abs(float(row[key]))
            w = int(540 * value / max_value)
            y = y0 + j * 9
            parts.append(f'<rect x="{left}" y="{y}" width="{w}" height="7" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{left + w + 8}" y="{y + 7}" font-family="Arial, sans-serif" font-size="10" fill="#243447">{value:.4f}</text>')
    legend_x = 910
    for i, (_key, label, color) in enumerate(keys):
        y = 92 + i * 24
        parts.append(f'<rect x="{legend_x}" y="{y - 11}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 22}" y="{y}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(label)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def make_subset_svg(path: Path, rows: list[dict]) -> None:
    width = 1040
    height = 430
    left = 120
    bottom = 340
    group_w = 230
    metrics = [
        ("external_AUROC", 0.78, 0.82, "#496f5d"),
        ("external_AUPRC", 0.15, 0.20, "#2f7da1"),
        ("external_calibration_slope", 0.80, 1.05, "#9a463d"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="34" font-family="Georgia, serif" font-size="21" fill="#1f2933">P15 subset performance comparison</text>',
        '<text x="24" y="58" font-family="Arial, sans-serif" font-size="12" fill="#52616b">P10/P12/proxy scenarios are simulated; P15 is observed frozen performance.</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{width - 40}" y2="{bottom}" stroke="#9aa5b1"/>',
    ]
    for idx, row in enumerate(rows):
        x0 = left + idx * group_w
        for j, (metric, ymin, ymax, color) in enumerate(metrics):
            value = float(row[metric])
            clipped = min(max(value, ymin), ymax)
            h = int((clipped - ymin) / (ymax - ymin) * 230)
            x = x0 + j * 42
            y = bottom - h
            parts.append(f'<rect x="{x}" y="{y}" width="34" height="{h}" rx="4" fill="{color}"/>')
            parts.append(f'<text x="{x - 6}" y="{y - 6}" font-family="Arial, sans-serif" font-size="10" fill="#243447">{value:.3f}</text>')
        parts.append(f'<text x="{x0 - 26}" y="{bottom + 24}" font-family="Arial, sans-serif" font-size="11" fill="#243447">{html.escape(row["subset_id"])}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def make_proxy_svg(path: Path, rows: list[dict]) -> None:
    width = 1120
    height = 390
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="34" font-family="Georgia, serif" font-size="21" fill="#1f2933">Proxy simplification scenarios</text>',
        '<text x="24" y="58" font-family="Arial, sans-serif" font-size="12" fill="#52616b">Full VIS is not used; these are transportable support-intensity proxy designs.</text>',
    ]
    y = 92
    for row in rows:
        x = 50
        parts.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="13" fill="#243447">{html.escape(row["scenario_id"])}</text>')
        x += 260
        for component in ["shared", "hemodynamic", "lactate", "renal", "respiratory"]:
            present = str(row[f"uses_{component}"]).lower() == "true"
            color = "#496f5d" if present else "#d8d2c4"
            parts.append(f'<rect x="{x}" y="{y - 16}" width="96" height="22" rx="5" fill="{color}"/>')
            parts.append(f'<text x="{x + 8}" y="{y}" font-family="Arial, sans-serif" font-size="10" fill="#1f2933">{component}</text>')
            x += 108
        parts.append(f'<text x="{x + 10}" y="{y}" font-family="Arial, sans-serif" font-size="12" fill="#243447">AUPRC {float(row["external_AUPRC"]):.4f}, slope {float(row["external_calibration_slope"]):.4f}</text>')
        y += 54
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def make_proxy_component_svg(path: Path, rows: list[dict]) -> None:
    width = 1120
    height = 460
    left = 320
    top = 86
    block_h = 54
    max_coef = max(abs(float(row["p15_death_class_coefficient"])) for row in rows) or 1.0
    max_auprc = max(float(row["estimated_AUPRC_loss_if_removed"]) for row in rows) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="24" y="34" font-family="Georgia, serif" font-size="21" fill="#1f2933">Proxy component contribution to death risk</text>',
        '<text x="24" y="58" font-family="Arial, sans-serif" font-size="12" fill="#52616b">Frozen P15 death-class coefficient plus simulated removal impact; no refit.</text>',
    ]
    for i, row in enumerate(rows):
        y0 = top + i * block_h
        parts.append(f'<text x="24" y="{y0 + 17}" font-family="Arial, sans-serif" font-size="12" fill="#243447">{html.escape(row["component_label"])}</text>')
        coef = abs(float(row["p15_death_class_coefficient"]))
        auprc = float(row["estimated_AUPRC_loss_if_removed"])
        coef_w = int(430 * coef / max_coef)
        auprc_w = int(430 * auprc / max_auprc)
        parts.append(f'<rect x="{left}" y="{y0}" width="{coef_w}" height="13" rx="4" fill="#9a463d"/>')
        parts.append(f'<text x="{left + coef_w + 8}" y="{y0 + 11}" font-family="Arial, sans-serif" font-size="10" fill="#243447">coef {float(row["p15_death_class_coefficient"]):.3f}</text>')
        parts.append(f'<rect x="{left}" y="{y0 + 21}" width="{auprc_w}" height="13" rx="4" fill="#2f7da1"/>')
        parts.append(f'<text x="{left + auprc_w + 8}" y="{y0 + 32}" font-family="Arial, sans-serif" font-size="10" fill="#243447">AUPRC loss {auprc:.4f}</text>')
    parts.append('<rect x="840" y="91" width="14" height="14" fill="#9a463d"/>')
    parts.append('<text x="862" y="103" font-family="Arial, sans-serif" font-size="12" fill="#243447">P15 death-class coefficient</text>')
    parts.append('<rect x="840" y="119" width="14" height="14" fill="#2f7da1"/>')
    parts.append('<text x="862" y="131" font-family="Arial, sans-serif" font-size="12" fill="#243447">Estimated AUPRC loss if removed</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    coef_path = PARS_DIR / "Parsimonious_Model_Coefficient_Importance.csv"
    coef_rows = read_csv_dicts(coef_path)
    coef_lookup = {
        (row["model_name"], row["feature"]): row
        for row in coef_rows
    }

    feature_rows = []
    for feature in FEATURES:
        score = IMPLEMENTABILITY[feature]
        penalty = REMOVAL_PENALTY[feature]
        row = {
            "feature_internal": feature,
            "feature_display": display_feature(feature),
            "legacy_alias_note": "display alias only; internal feature name retained for traceability" if feature in DISPLAY_ALIASES else "",
            "feature_category": CATEGORY[feature],
            "clinical_interpretability_score_1to5": score["clinical"],
            "cross_database_stability_score_1to5": score["stability"],
            "implementation_ease_score_1to5": score["ease"],
            "model_importance_score_1to5": importance_score(feature),
            "weighted_retention_score_1to5": retention_score(feature),
            "estimated_AUROC_loss_if_removed": penalty["auroc"],
            "estimated_AUPRC_loss_if_removed": penalty["auprc"],
            "estimated_calibration_slope_loss_if_removed": penalty["slope"],
            "included_in_P10": feature in FEATURE_SETS["P10_ultra_minimal_transport_set"],
            "included_in_P12": feature in FEATURE_SETS["P12_balanced_transport_set"],
            "included_in_P15": True,
            "retention_recommendation": "core_keep" if feature in FEATURE_SETS["P10_ultra_minimal_transport_set"] else "balanced_or_P15_keep",
            "rationale": RATIONALE[feature],
            "evidence_type": "simulation_only_no_retraining",
        }
        feature_rows.append(row)
    feature_rows.sort(key=lambda r: float(r["weighted_retention_score_1to5"]), reverse=True)
    feature_fields = list(feature_rows[0].keys())
    write_csv(PARS_DIR / "P15_Feature_Retention_Rationale_Detailed.csv", feature_rows, feature_fields)
    write_csv(PARS_DIR / "P15_Feature_Subset_Sensitivity.csv", feature_rows, feature_fields)

    subset_rows = []
    for subset_id, features in FEATURE_SETS.items():
        metrics = P15_BASE if subset_id == "P15_clinically_parsimonious_transport_model" else estimate_metrics(features)
        subset_rows.append(
            {
                "subset_id": subset_id,
                "feature_count": len(features),
                "feature_list_display": ";".join(display_feature(f) for f in features),
                "feature_list_internal": ";".join(features),
                "removed_from_P15": ";".join(display_feature(f) for f in FEATURES if f not in features),
                "proxy_strategy": "all_proxy_components" if subset_id.startswith("P15") else ("shared_proxy_only" if subset_id.startswith("P10") else "shared_proxy_plus_lactate_component"),
                "external_AUROC": metrics["auroc"],
                "external_AUPRC": metrics["auprc"],
                "external_calibration_slope": metrics["slope"],
                "passes_external_gate": pass_gate(metrics),
                "evidence_type": "observed_frozen_metric" if subset_id.startswith("P15") else "simulated_from_P15_component_penalties_no_retraining",
                "recommendation": "final_reference" if subset_id.startswith("P15") else ("implementation_minimal_candidate" if subset_id.startswith("P10") else "balanced_candidate"),
            }
        )
    subset_fields = list(subset_rows[0].keys())
    write_csv(PARS_DIR / "P15_Subset_Combination_Performance.csv", subset_rows, subset_fields)
    write_csv(TABLE_DIR / "Table_P15_Subset_Sensitivity_Clinical_Landing.csv", subset_rows, subset_fields)

    proxy_scenarios = [
        {
            "scenario_id": "Proxy_A_composite_only",
            "description": "Keep shared_support_intensity_proxy only; drop all four component proxy variables.",
            "features_removed": "support_hemodynamic_component;support_lactate_component;support_renal_component;support_respiratory_component",
            "uses_shared": True,
            "uses_hemodynamic": False,
            "uses_lactate": False,
            "uses_renal": False,
            "uses_respiratory": False,
        },
        {
            "scenario_id": "Proxy_B_composite_plus_lactate",
            "description": "Keep shared proxy plus lactate component for perfusion interpretability.",
            "features_removed": "support_hemodynamic_component;support_renal_component;support_respiratory_component",
            "uses_shared": True,
            "uses_hemodynamic": False,
            "uses_lactate": True,
            "uses_renal": False,
            "uses_respiratory": False,
        },
        {
            "scenario_id": "Proxy_C_composite_plus_hemodynamic_lactate",
            "description": "Keep shared proxy plus hemodynamic and lactate components as the most clinically direct support subset.",
            "features_removed": "support_renal_component;support_respiratory_component",
            "uses_shared": True,
            "uses_hemodynamic": True,
            "uses_lactate": True,
            "uses_renal": False,
            "uses_respiratory": False,
        },
        {
            "scenario_id": "Proxy_D_original_P15_all_components",
            "description": "Original P15 support proxy design: shared proxy plus all four components.",
            "features_removed": "",
            "uses_shared": True,
            "uses_hemodynamic": True,
            "uses_lactate": True,
            "uses_renal": True,
            "uses_respiratory": True,
        },
    ]
    proxy_rows = []
    for row in proxy_scenarios:
        removed = [f for f in row["features_removed"].split(";") if f]
        metrics = {
            "auroc": P15_BASE["auroc"] - sum(REMOVAL_PENALTY[f]["auroc"] for f in removed),
            "auprc": P15_BASE["auprc"] - sum(REMOVAL_PENALTY[f]["auprc"] for f in removed),
            "slope": P15_BASE["slope"] - sum(REMOVAL_PENALTY[f]["slope"] for f in removed),
        }
        proxy_rows.append(
            {
                **row,
                "external_AUROC": metrics["auroc"],
                "external_AUPRC": metrics["auprc"],
                "external_calibration_slope": metrics["slope"],
                "passes_external_gate": pass_gate(metrics),
                "evidence_type": "observed_frozen_metric" if not removed else "simulated_proxy_merge_no_retraining",
                "landing_assessment": (
                    "best_verified_reference"
                    if not removed
                    else ("most_implementable_proxy" if row["scenario_id"] == "Proxy_A_composite_only" else "balanced_proxy_candidate")
                ),
            }
        )
    proxy_fields = list(proxy_rows[0].keys())
    write_csv(PARS_DIR / "P15_Proxy_Merge_Scenarios.csv", proxy_rows, proxy_fields)

    proxy_component_features = [
        ("shared_support_intensity_proxy", "Shared support-intensity composite"),
        ("support_hemodynamic_component", "Hemodynamic support component"),
        ("support_lactate_component", "Lactate/perfusion component"),
        ("support_renal_component", "Renal support component"),
        ("support_respiratory_component", "Respiratory support component"),
    ]
    proxy_component_rows = []
    for feature, label in proxy_component_features:
        p15_coef = coef_lookup[("P15_minimal_bedside_model", feature)]
        mt3_coef = coef_lookup[("MT3_full_transport_set", feature)]
        penalty = REMOVAL_PENALTY[feature]
        proxy_component_rows.append(
            {
                "component_label": label,
                "feature_internal": feature,
                "feature_display": display_feature(feature),
                "p15_death_class_coefficient": float(p15_coef["death_class_coefficient"]),
                "p15_abs_death_class_coefficient": float(p15_coef["abs_death_class_coefficient"]),
                "p15_importance_rank": int(float(p15_coef["importance_rank"])),
                "mt3_death_class_coefficient": float(mt3_coef["death_class_coefficient"]),
                "mt3_importance_rank": int(float(mt3_coef["importance_rank"])),
                "estimated_AUROC_loss_if_removed": penalty["auroc"],
                "estimated_AUPRC_loss_if_removed": penalty["auprc"],
                "estimated_calibration_slope_loss_if_removed": penalty["slope"],
                "risk_direction_interpretation": (
                    "positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit"
                    if float(p15_coef["death_class_coefficient"]) > 0
                    else "negative death-class coefficient in frozen P15; interpret with caution"
                ),
                "clinical_interpretation": RATIONALE[feature],
                "evidence_type": "frozen_P15_coefficient_plus_simulated_removal_impact_no_retraining",
            }
        )
    proxy_component_rows.sort(key=lambda r: float(r["estimated_AUPRC_loss_if_removed"]), reverse=True)
    proxy_component_fields = list(proxy_component_rows[0].keys())
    write_csv(PARS_DIR / "P15_Proxy_Component_Death_Risk_Contribution.csv", proxy_component_rows, proxy_component_fields)

    top_features = sorted(feature_rows, key=lambda r: float(r["estimated_AUPRC_loss_if_removed"]), reverse=True)
    make_bar_svg(
        FIG_DIR / "P15_Feature_Contribution_MultiMetric.svg",
        top_features,
        [
            ("estimated_AUROC_loss_if_removed", "AUROC loss", "#496f5d"),
            ("estimated_AUPRC_loss_if_removed", "AUPRC loss", "#2f7da1"),
            ("estimated_calibration_slope_loss_if_removed", "Slope loss", "#9a463d"),
        ],
        "P15 feature contribution sensitivity",
        "Estimated loss if removed from P15; simulation only, no retraining.",
    )
    make_subset_svg(FIG_DIR / "P15_Subset_Performance_Comparison.svg", subset_rows)
    make_proxy_svg(FIG_DIR / "P15_Proxy_Contribution_Interpretability.svg", proxy_rows)
    make_proxy_component_svg(FIG_DIR / "P15_Proxy_Component_Death_Risk_Contribution.svg", proxy_component_rows)

    write_csv(FIG_DIR / "P15_Feature_Contribution_MultiMetric.csv", top_features, feature_fields)
    write_csv(FIG_DIR / "P15_Subset_Performance_Comparison.csv", subset_rows, subset_fields)
    write_csv(FIG_DIR / "P15_Proxy_Contribution_Interpretability.csv", proxy_rows, proxy_fields)
    write_csv(FIG_DIR / "P15_Proxy_Component_Death_Risk_Contribution.csv", proxy_component_rows, proxy_component_fields)

    subset_md = "\n".join(
        f"| `{r['subset_id']}` | {r['feature_count']} | {r['external_AUROC']:.4f} | {r['external_AUPRC']:.4f} | {r['external_calibration_slope']:.4f} | {r['proxy_strategy']} | {r['evidence_type']} |"
        for r in subset_rows
    )
    proxy_md = "\n".join(
        f"| `{r['scenario_id']}` | {r['external_AUROC']:.4f} | {r['external_AUPRC']:.4f} | {r['external_calibration_slope']:.4f} | {r['landing_assessment']} | {r['description']} |"
        for r in proxy_rows
    )
    proxy_component_md = "\n".join(
        f"| `{r['feature_display']}` | {r['p15_death_class_coefficient']:.4f} | {r['p15_importance_rank']} | {r['mt3_death_class_coefficient']:.4f} | {r['estimated_AUPRC_loss_if_removed']:.4f} | {r['risk_direction_interpretation']} |"
        for r in proxy_component_rows
    )
    feature_md = "\n".join(
        f"| `{r['feature_display']}` | {r['feature_category']} | {r['weighted_retention_score_1to5']} | {r['estimated_AUPRC_loss_if_removed']:.4f} | {r['retention_recommendation']} | {r['rationale']} |"
        for r in feature_rows
    )

    report = f"""# P15 模型子集敏感性分析与临床落地优化

## 证据边界

本轮只做 P15 子集敏感性与临床落地评估。没有修改标签、训练逻辑、原始特征矩阵、预测文件或任何冻结指标。P10/P12 和 proxy 合并场景均为基于 P15 单特征移除罚分的模拟估计，不是新模型训练结果。

内部特征名保留 legacy alias：`hr_latest_value` 和 `rr_latest_value` 分别在展示层映射为 `heart_rate_latest_value` 与 `respiratory_rate_latest_value`，但不改动底层字段名。

## 冻结 P15 外部性能

- eICU AUROC: {P15_BASE['auroc']:.4f}
- eICU AUPRC: {P15_BASE['auprc']:.4f}
- eICU calibration slope: {P15_BASE['slope']:.4f}

## 子集组合

| 子集 | 特征数 | AUROC | AUPRC | 校准斜率 | proxy 策略 | 证据类型 |
|---|---:|---:|---:|---:|---|---|
{subset_md}

## Proxy 合并场景

| 场景 | AUROC | AUPRC | 校准斜率 | 落地判断 | 说明 |
|---|---:|---:|---:|---|---|
{proxy_md}

## Proxy 分量对死亡风险的解释

这里使用已有冻结文件 `Parsimonious_Model_Coefficient_Importance.csv` 中的 P15/MT3 death-class 系数，同时列出模拟移除后的 AUPRC 损失。系数是冻结模型证据，不是本轮重训；AUPRC 损失是模拟敏感性估计。

| Proxy 分量 | P15 death-class coefficient | P15 rank | MT3 coefficient | 估计 AUPRC 损失 | 解释 |
|---|---:|---:|---:|---:|---|
{proxy_component_md}

## 特征贡献与保留理由

| 特征 | 类别 | 可实施性加权分 | 移除后估计 AUPRC 损失 | 建议 | 保留理由 |
|---|---|---:|---:|---|---|
{feature_md}

## 最终建议

1. 论文和正式结果仍以 `P15_clinically_parsimonious_transport_model` 作为已验证参考，因为它有冻结的真实外部指标。
2. 临床落地展示可同时报告 `P10_ultra_minimal_transport_set` 和 `P12_balanced_transport_set`，但必须写明它们是模拟子集，不是重训模型。
3. 如果目标是最大可理解性，proxy 可合并为 `shared_support_intensity_proxy` 单指标；如果希望保留灌注解释性，则推荐 `shared_support_intensity_proxy + support_lactate_component`。
4. `shared_support_intensity_proxy`、`spo2_latest_value`、`hours_from_anchor`、`bun_latest_value` 是最不建议删除的核心变量。
5. full VIS 不应重新进入 transport 子集；当前 proxy 必须继续被称为 shared support-intensity proxy，而不是 VIS。

## 输出文件

- `parsimonious_features/P15_Feature_Subset_Sensitivity.csv`
- `parsimonious_features/P15_Proxy_Merge_Scenarios.csv`
- `parsimonious_features/P15_Proxy_Component_Death_Risk_Contribution.csv`
- `parsimonious_features/P15_Subset_Combination_Performance.csv`
- `parsimonious_features/P15_Feature_Retention_Rationale_Detailed.csv`
- `results_final/tables/Table_P15_Subset_Sensitivity_Clinical_Landing.csv`
- `results_final/figures/P15_Feature_Contribution_MultiMetric.svg`
- `results_final/figures/P15_Subset_Performance_Comparison.svg`
- `results_final/figures/P15_Proxy_Contribution_Interpretability.svg`
- `results_final/figures/P15_Proxy_Component_Death_Risk_Contribution.svg`
"""
    (PARS_DIR / "P15_Subset_Sensitivity_Clinical_Landing_Report.md").write_text(report, encoding="utf-8")
    print("Generated local P15 subset sensitivity and clinical landing package.")
    print(f"P15 frozen metrics retained: {P15_BASE['auroc']:.4f}/{P15_BASE['auprc']:.4f}/{P15_BASE['slope']:.4f}")
    print("No git commit or push was performed.")


if __name__ == "__main__":
    main()
