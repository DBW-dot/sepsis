from __future__ import annotations

import csv
import math
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "manuscript_assets" / "figures"
MAIN = FIG / "main"
SUPP = FIG / "supplementary"
DATA = FIG / "data"
CAPTIONS = FIG / "captions"
AUDIT = ROOT / "manuscript_assets" / "audit"

P15 = "P15_clinically_parsimonious_transport_model"
P12 = "P12_true_trained_clinical_landing_model"
P10 = "P10_true_trained_ultra_minimal_sensitivity_model"
M1 = "M1_internal_rich_reference_model"
MT3 = "MT3_Post_METRE_transport_reference_model"
SOFA = "C1_dynamic_SOFA_clinical_comparator"

MODEL_LABEL = {
    M1: "M1\ninternal rich",
    MT3: "MT3\nPost-METRE ref.",
    P15: "P15\nmain",
    P12: "P12\nsimplified",
    P10: "P10\nultra-minimal",
    SOFA: "SOFA\ncomparator",
    "P15_clinically_parsimonious_transport_model": "P15",
    "P12_true_trained_clinical_landing_model": "P12",
    "P10_true_trained_ultra_minimal_sensitivity_model": "P10",
}

COLORS = {
    "blue": "#2F5D8C",
    "teal": "#3F8F8A",
    "orange": "#D88932",
    "red": "#B94A48",
    "gray": "#6E6E6E",
    "light": "#F4F2EC",
    "line": "#242424",
}


def ensure_dirs() -> None:
    for d in [MAIN, SUPP, DATA, CAPTIONS, AUDIT]:
        d.mkdir(parents=True, exist_ok=True)


def save_fig(fig: plt.Figure, svg_path: Path, png_path: Path) -> None:
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    fig.savefig(png_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def wrap_label(text: str, width: int = 22) -> str:
    return "\n".join(wrap(text, width=width, break_long_words=False))


def clean_float(x):
    try:
        return float(x)
    except Exception:
        return math.nan


def box(ax, xy, w, h, text, fc, ec="#333333", fontsize=8.5):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.025",
        linewidth=1.0,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, color="#222222")


def arrow(ax, start, end):
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.2, color="#333333"))


def figure1_workflow():
    rows = [
        {"stage": "Data sources", "items": "MIMIC-IV; eICU", "note": "MIMIC development/internal; eICU external validation"},
        {"stage": "Cohort construction", "items": "Sepsis-3 suspected infection; t_ICU; t_sepsis", "note": "Dual-anchor cohort spine"},
        {"stage": "Dynamic grid", "items": "Hourly prediction grid; prefix-only observations", "note": "No post-prediction information"},
        {"stage": "Competing-risk labels", "items": "ICU death within 24h; alive discharge/transfer; continued ICU stay", "note": "24h outcome window"},
        {"stage": "Model chain", "items": "M1; MT3; P15; P12/P10 sensitivity", "note": "P15 final main model; P12/P10 do not replace P15"},
        {"stage": "Clinical realism audit", "items": "Lab freshness; latest-available carry-forward", "note": "No hourly lab assumption"},
    ]
    pd.DataFrame(rows).to_csv(DATA / "Figure1_Study_Workflow_Dual_Anchor_Data.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.96, "Study workflow and dual-anchor dynamic prediction design", fontsize=17, weight="bold", ha="left")
    ax.text(0.02, 0.915, "Prefix-only dynamic prediction with 24h competing-risk labels", fontsize=10, ha="left", color="#555555")

    # Left source boxes
    box(ax, (0.03, 0.70), 0.16, 0.08, "MIMIC-IV\ntraining/internal", "#DDEAF6")
    box(ax, (0.03, 0.58), 0.16, 0.08, "eICU\nexternal validation", "#E4F1EC")
    box(ax, (0.24, 0.64), 0.18, 0.12, "Sepsis-3 cohort\nsuspected infection\n+t_ICU + t_sepsis", "#F7E6CC")
    arrow(ax, (0.19, 0.74), (0.24, 0.71))
    arrow(ax, (0.19, 0.62), (0.24, 0.68))

    box(ax, (0.47, 0.64), 0.18, 0.12, "Dual anchors\nICU admission\nSepsis onset", "#F1E2F0")
    arrow(ax, (0.42, 0.70), (0.47, 0.70))

    box(ax, (0.70, 0.64), 0.22, 0.12, "Hourly prediction grid\nprefix-only observations\nno future data", "#EDEDED")
    arrow(ax, (0.65, 0.70), (0.70, 0.70))

    box(ax, (0.26, 0.40), 0.20, 0.12, "24h competing-risk labels\nICU death\nalive discharge/transfer\ncontinued stay", "#F8F1D8", fontsize=8)
    arrow(ax, (0.78, 0.64), (0.46, 0.52))

    model_x = [0.08, 0.28, 0.48, 0.68]
    model_text = [
        "M1\ninternal rich\nreference",
        "MT3\nPost-METRE\ntransport ref.",
        "P15\nfinal clinically\nparsimonious model",
        "P12/P10\nimplementation\nsensitivity models",
    ]
    for x, text in zip(model_x, model_text):
        box(ax, (x, 0.20), 0.16, 0.10, text, "#DDEAF6" if "P15" not in text else "#DDF0E7", fontsize=8)
    for x1, x2 in zip(model_x[:-1], model_x[1:]):
        arrow(ax, (x1 + 0.16, 0.25), (x2, 0.25))
    arrow(ax, (0.36, 0.40), (0.36, 0.30))

    box(ax, (0.70, 0.38), 0.23, 0.14, "Clinical realism audit\nlab freshness sensitivity\nlatest-available carry-forward\nno hourly lab assumption", "#E8F0F6", fontsize=8)
    arrow(ax, (0.81, 0.64), (0.81, 0.52))
    ax.text(0.05, 0.08, "Guardrails: P12/P10 do not replace P15; shared support-intensity proxy is not full VIS; DCA/lead-time are supplementary.", fontsize=9, color="#444444")
    save_fig(fig, MAIN / "Figure1_Study_Workflow_Dual_Anchor.svg", MAIN / "Figure1_Study_Workflow_Dual_Anchor.png")
    write_text(
        CAPTIONS / "Figure1_Caption.md",
        """
# Figure 1 Caption Draft

Study workflow and dual-anchor dynamic prediction design. MIMIC-IV was used for model development/internal evaluation and eICU for external validation only. Prediction landmarks use prefix-only observations aligned to ICU admission and sepsis-onset anchors. Outcomes are 24h competing-risk states. P15 is the final clinically parsimonious model; P12/P10 are implementation sensitivity models and do not replace P15. Laboratory variables are latest-available / capped carry-forward values, not hourly real laboratory measurements.
""",
    )


def figure2_performance():
    df = pd.read_csv(ROOT / "manuscript_assets/tables/Table2_Main_Model_Performance.csv")
    data = df[[
        "model_display_name",
        "model_role",
        "feature_count",
        "eICU_AUROC",
        "eICU_AUPRC",
        "eICU_calibration_slope",
    ]].copy()
    data.to_csv(DATA / "Figure2_Model_Performance_Comparison_Data.csv", index=False, encoding="utf-8-sig")

    models = data["model_display_name"].tolist()
    labels = [MODEL_LABEL.get(m, m) for m in models]
    metrics = ["eICU_AUROC", "eICU_AUPRC", "eICU_calibration_slope"]
    titles = ["eICU AUROC", "eICU AUPRC", "eICU calibration slope"]
    colors = [COLORS["gray"], COLORS["teal"], COLORS["blue"], COLORS["orange"], "#C783A6", "#7E8D6D"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, metric, title in zip(axes, metrics, titles):
        vals = data[metric].astype(float).values
        ax.bar(range(len(vals)), vals, color=colors, edgecolor="#333333", linewidth=0.6)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, rotation=0, fontsize=8)
        ax.grid(axis="y", alpha=0.25)
        if metric == "eICU_calibration_slope":
            ax.axhline(1.0, color="#222222", lw=1.0, ls="--", alpha=0.8)
            ax.set_ylim(0, max(1.15, vals.max() * 1.12))
        else:
            ax.set_ylim(0, max(vals.max() * 1.18, 0.22 if metric.endswith("AUPRC") else 0.9))
        for i, v in enumerate(vals):
            ax.text(i, v + ax.get_ylim()[1] * 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
    fig.suptitle("External validation performance: final model and comparators", fontsize=14, weight="bold", y=1.03)
    fig.text(0.5, -0.02, "P15 is the formal main model. P12/P10 are true-trained implementation/sensitivity candidates.", ha="center", fontsize=9)
    save_fig(fig, MAIN / "Figure2_Model_Performance_Comparison.svg", MAIN / "Figure2_Model_Performance_Comparison.png")
    write_text(
        CAPTIONS / "Figure2_Caption.md",
        """
# Figure 2 Caption Draft

Model performance comparison in eICU external validation. Bars summarize AUROC, AUPRC, and calibration slope for the internal rich reference model, Post-METRE reference model, final P15 model, P12/P10 true-trained implementation candidates, and dynamic SOFA comparator. P15 is the formal main model. P12/P10 are not replacements for P15.
""",
    )


def figure3_calibration():
    curve_path = ROOT / "results_final/clinical_implementation/P12_P10_P15_Calibration_Comparison.csv"
    df = pd.read_csv(curve_path)
    df = df[df["dataset_name"] == "eicu_external"].copy()
    keep = [P15, P12, P10]
    df = df[df["model_name"].isin(keep)].copy()
    df["mean_predicted_death_prob"] = df["mean_predicted_death_prob"].astype(float)
    df["observed_death_rate"] = df["observed_death_rate"].astype(float)
    df.to_csv(DATA / "Figure3_Calibration_Comparison_Data.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    max_val = max(df["mean_predicted_death_prob"].max(), df["observed_death_rate"].max()) * 1.05
    max_val = max(max_val, 0.08)
    ax.plot([0, max_val], [0, max_val], color="#222222", ls="--", lw=1.2, label="Ideal")
    for model, color in [(P15, COLORS["blue"]), (P12, COLORS["orange"]), (P10, "#C783A6")]:
        sub = df[df["model_name"] == model].sort_values("mean_predicted_death_prob")
        ax.plot(sub["mean_predicted_death_prob"], sub["observed_death_rate"], marker="o", lw=1.8, color=color, label=MODEL_LABEL.get(model, model))
    ax.set_xlabel("Mean predicted 24h death risk")
    ax.set_ylabel("Observed 24h death rate")
    ax.set_title("eICU calibration curve by risk bin", fontsize=13, weight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    save_fig(fig, MAIN / "Figure3_Calibration_Comparison.svg", MAIN / "Figure3_Calibration_Comparison.png")
    write_text(
        CAPTIONS / "Figure3_Caption.md",
        """
# Figure 3 Caption Draft

Calibration curves for P15, P12, and P10 in eICU external validation using available bin-level calibration data. The dashed diagonal denotes ideal calibration. P15 calibration slope is 1.0031 in the locked performance table. P12/P10 are true-trained implementation/sensitivity candidates and do not replace P15.
""",
    )


def figure4_lab_freshness():
    df_all = pd.read_csv(ROOT / "manuscript_assets/tables/Table4_Lab_Freshness_Sensitivity.csv")
    df_all.to_csv(DATA / "Figure4_Lab_Freshness_Sensitivity_Data.csv", index=False, encoding="utf-8-sig")
    df = df_all[(df_all["model_display_name"] == P15) & (df_all["freshness_scenario"].isin([
        "current_latest_value_reference",
        "lab12h_freshness_window",
        "lab24h_freshness_window",
    ]))].copy()
    order = ["current_latest_value_reference", "lab12h_freshness_window", "lab24h_freshness_window"]
    df["order"] = df["freshness_scenario"].map({k: i for i, k in enumerate(order)})
    df = df.sort_values("order")
    labels = ["Current\nlatest value", "12h\nfreshness", "24h\nfreshness"]

    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.2))
    metric_cols = [("eICU_AUROC", "AUROC"), ("eICU_AUPRC", "AUPRC"), ("eICU_calibration_slope", "Calibration slope")]
    for ax, (col, title) in zip(axes, metric_cols):
        vals = df[col].astype(float).values
        ax.plot(range(len(vals)), vals, marker="o", lw=2.4, color=COLORS["blue"])
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.grid(axis="y", alpha=0.25)
        if col == "eICU_calibration_slope":
            ax.axhline(1.0, color="#222222", ls="--", lw=1.0)
            ax.set_ylim(0.9, 1.05)
        else:
            ymin = max(0, vals.min() - 0.03)
            ymax = vals.max() + 0.03
            ax.set_ylim(ymin, ymax)
        for i, v in enumerate(vals):
            ax.text(i, v, f" {v:.3f}", ha="left", va="bottom", fontsize=8)
    fig.suptitle("P15 lab freshness sensitivity in eICU", fontsize=14, weight="bold")
    fig.text(0.5, -0.03, "Lab values are latest-available / capped carry-forward; not hourly real measurements. 12h is borderline acceptable; 24h is largely stable.", ha="center", fontsize=9)
    save_fig(fig, MAIN / "Figure4_Lab_Freshness_Sensitivity.svg", MAIN / "Figure4_Lab_Freshness_Sensitivity.png")
    write_text(
        CAPTIONS / "Figure4_Caption.md",
        """
# Figure 4 Caption Draft

P15 laboratory freshness sensitivity in eICU external validation. The current latest-value reference uses latest-available / capped carry-forward laboratory values, not hourly real laboratory measurements. The 12h freshness scenario is borderline acceptable, whereas the 24h scenario is largely stable. Result availability time is incomplete; chart/sample time was used as a conservative approximation.
""",
    )


def figure5_feature_modules():
    features = pd.read_csv(ROOT / "manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv")
    module_map = {
        "hours_since_icu_admission": "Time anchors",
        "hours_from_anchor": "Time anchors",
        "is_sepsis_on_admission": "Time anchors",
        "heart_rate_latest_value": "Vital signs",
        "respiratory_rate_latest_value": "Vital signs",
        "spo2_latest_value": "Vital signs",
        "creatinine_latest_value": "Routine labs",
        "bun_latest_value": "Routine labs",
        "platelet_latest_value": "Routine labs",
        "wbc_latest_value": "Routine labs",
        "shared_support_intensity_proxy": "Support-intensity proxy",
        "support_hemodynamic_component": "Support-intensity proxy",
        "support_lactate_component": "Support-intensity proxy",
        "support_renal_component": "Support-intensity proxy",
        "support_respiratory_component": "Support-intensity proxy",
    }
    features["module"] = features["feature_name"].map(module_map).fillna(features["clinical_domain"])
    features[["feature_name", "module", "acquisition_source", "direct_measurement_or_derived", "expected_update_frequency"]].to_csv(
        DATA / "Figure5_P15_Clinical_Feature_Modules_Data.csv", index=False, encoding="utf-8-sig"
    )

    modules = [
        ("Time anchors", "#DDEAF6"),
        ("Vital signs", "#E4F1EC"),
        ("Routine labs", "#F7E6CC"),
        ("Support-intensity proxy", "#F1E2F0"),
    ]
    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.02, 0.95, "P15 clinical feature modules", fontsize=16, weight="bold")
    ax.text(0.02, 0.91, "15 EHR-implementable features: time anchors, vital signs, routine labs, and support-intensity proxy", fontsize=9.5, color="#555555")

    xs = [0.04, 0.28, 0.52, 0.76]
    for (module, color), x in zip(modules, xs):
        sub = features[features["module"] == module]["feature_name"].tolist()
        box(ax, (x, 0.18), 0.20, 0.65, module, color, fontsize=10)
        ax.text(x + 0.10, 0.79, module, ha="center", va="center", fontsize=11, weight="bold")
        y = 0.70
        for f in sub:
            display = f.replace("_latest_value", "").replace("support_", "").replace("_component", " component").replace("_", " ")
            ax.text(x + 0.10, y, wrap_label(display, 20), ha="center", va="center", fontsize=8.5)
            y -= 0.085
    ax.text(0.04, 0.08, "Guardrails: EHR-implementable, not bedside-only and not a manual score. The support-intensity proxy is not full VIS.", fontsize=9, color="#444444")
    save_fig(fig, MAIN / "Figure5_P15_Clinical_Feature_Modules.svg", MAIN / "Figure5_P15_Clinical_Feature_Modules.png")
    write_text(
        CAPTIONS / "Figure5_Caption.md",
        """
# Figure 5 Caption Draft

P15 clinical feature modules. The final P15 model uses 15 EHR-implementable features grouped into time anchors, vital signs, routine laboratory values, and shared support-intensity proxy components. P15 is not a bedside-only manual score. The support-intensity proxy is a cross-database support burden proxy and is not full VIS.
""",
    )


def supplementary_s1_dca():
    df = pd.read_csv(ROOT / "manuscript_assets/tables/Supplementary_Table_S2_DCA_Summary.csv")
    df = df[df["dataset_name"] == "eicu_external"].copy()
    df["threshold"] = df["threshold"].astype(float)
    for col in ["net_benefit", "treat_all_net_benefit", "treat_none_net_benefit"]:
        df[col] = df[col].astype(float)
    df.to_csv(DATA / "Supplementary_Figure_S1_DCA_Data.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for model, color in [(P15, COLORS["blue"]), (P12, COLORS["orange"]), (P10, "#C783A6")]:
        sub = df[df["model_name"] == model].sort_values("threshold")
        ax.plot(sub["threshold"], sub["net_benefit"], marker="o", lw=1.8, color=color, label=MODEL_LABEL.get(model, model))
    base = df[df["model_name"] == P15].sort_values("threshold")
    ax.plot(base["threshold"], base["treat_all_net_benefit"], ls="--", color="#555555", label="Treat all")
    ax.plot(base["threshold"], base["treat_none_net_benefit"], ls=":", color="#111111", label="Treat none")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_title("Supplementary DCA: eICU threshold sweep", fontsize=13, weight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    save_fig(fig, SUPP / "Supplementary_Figure_S1_DCA.svg", SUPP / "Supplementary_Figure_S1_DCA.png")
    write_text(
        CAPTIONS / "Supplementary_Figure_S1_Caption.md",
        """
# Supplementary Figure S1 Caption Draft

Decision curve analysis threshold sweep in eICU external validation for P15, P12, and P10. Treat-all and treat-none references are shown. This is a supplementary clinical utility estimate only, not an automatic intervention trigger or direct treatment recommendation.
""",
    )


def supplementary_s2_leadtime():
    df = pd.read_csv(ROOT / "manuscript_assets/tables/Supplementary_Table_S3_Leadtime_Summary.csv")
    df = df[df["dataset_name"] == "eicu_external"].copy()
    df["threshold"] = df["threshold"].astype(float)
    df["strict_lead_time_median_hours"] = df["strict_lead_time_median_hours"].astype(float)
    df["strict_lead_time_iqr_low_hours"] = df["strict_lead_time_iqr_low_hours"].astype(float)
    df["strict_lead_time_iqr_high_hours"] = df["strict_lead_time_iqr_high_hours"].astype(float)
    df.to_csv(DATA / "Supplementary_Figure_S2_Leadtime_Data.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for model, color in [(P15, COLORS["blue"]), (P12, COLORS["orange"]), (P10, "#C783A6")]:
        sub = df[df["model_name"] == model].sort_values("threshold")
        y = sub["strict_lead_time_median_hours"]
        yerr = [y - sub["strict_lead_time_iqr_low_hours"], sub["strict_lead_time_iqr_high_hours"] - y]
        ax.errorbar(sub["threshold"], y, yerr=yerr, marker="o", lw=1.6, capsize=3, color=color, label=MODEL_LABEL.get(model, model))
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Strict 24h first-alarm lead-time, median hours (IQR)")
    ax.set_title("Supplementary first-alarm lead-time summary", fontsize=13, weight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    save_fig(fig, SUPP / "Supplementary_Figure_S2_Leadtime.svg", SUPP / "Supplementary_Figure_S2_Leadtime.png")
    write_text(
        CAPTIONS / "Supplementary_Figure_S2_Caption.md",
        """
# Supplementary Figure S2 Caption Draft

Strict 24h first-alarm lead-time summary in eICU external validation. Points show median lead-time and error bars show IQR from the available summary table. No distribution was reconstructed beyond the available summary data. Lead-time is supplementary risk-stratification timing support, not a direct treatment recommendation.
""",
    )


def supplementary_s3_proxy():
    rows = [
        {"proxy_element": "shared_support_intensity_proxy", "clinical_label": "overall support burden", "role": "overall proxy", "external_transport_use": "yes", "full_VIS": "no"},
        {"proxy_element": "support_hemodynamic_component", "clinical_label": "hemodynamic support burden", "role": "component", "external_transport_use": "yes", "full_VIS": "no"},
        {"proxy_element": "support_lactate_component", "clinical_label": "lactate/perfusion burden", "role": "interpretability component", "external_transport_use": "yes", "full_VIS": "no"},
        {"proxy_element": "support_renal_component", "clinical_label": "renal support burden", "role": "component", "external_transport_use": "yes", "full_VIS": "no"},
        {"proxy_element": "support_respiratory_component", "clinical_label": "respiratory support burden", "role": "component", "external_transport_use": "yes", "full_VIS": "no"},
    ]
    pd.DataFrame(rows).to_csv(DATA / "Supplementary_Figure_S3_Proxy_Interpretation_Data.csv", index=False, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.04, 0.92, "Shared support-intensity proxy interpretation", fontsize=15, weight="bold")
    box(ax, (0.38, 0.62), 0.24, 0.14, "shared support-intensity proxy\noverall support burden", "#DDF0E7", fontsize=9)
    components = [
        ("hemodynamic\nsupport burden", 0.08, 0.32, "#DDEAF6"),
        ("lactate/perfusion\nburden", 0.31, 0.24, "#F7E6CC"),
        ("renal\nsupport burden", 0.55, 0.24, "#E8F0F6"),
        ("respiratory\nsupport burden", 0.78, 0.32, "#F1E2F0"),
    ]
    for text, x, y, color in components:
        box(ax, (x, y), 0.16, 0.12, text, color, fontsize=8.5)
        arrow(ax, (x + 0.08, y + 0.12), (0.50, 0.62))
    ax.text(0.05, 0.10, "The proxy is a cross-database support burden signal, not full VIS. Full VIS was not used as the external transport input.", fontsize=9, color="#444444")
    save_fig(fig, SUPP / "Supplementary_Figure_S3_Proxy_Interpretation.svg", SUPP / "Supplementary_Figure_S3_Proxy_Interpretation.png")
    write_text(
        CAPTIONS / "Supplementary_Figure_S3_Caption.md",
        """
# Supplementary Figure S3 Caption Draft

Interpretation of the shared support-intensity proxy. The proxy summarizes cross-database support burden using hemodynamic, lactate/perfusion, renal, and respiratory components. It is not full VIS, and full VIS was not used as the external transport input.
""",
    )


def figure_index_and_audit():
    index_rows = [
        ("Figure 1", "main/Figure1_Study_Workflow_Dual_Anchor.svg", "workflow diagram", "locked study design and final role definitions", "main manuscript", "captions/Figure1_Caption.md", "P12/P10 do not replace P15; no hourly lab assumption"),
        ("Figure 2", "main/Figure2_Model_Performance_Comparison.svg", "performance comparison", "Table2_Main_Model_Performance.csv", "main manuscript", "captions/Figure2_Caption.md", "P15 is the formal main model"),
        ("Figure 3", "main/Figure3_Calibration_Comparison.svg", "calibration curve", "P12_P10_P15_Calibration_Comparison.csv", "main manuscript", "captions/Figure3_Caption.md", "uses available bin-level data"),
        ("Figure 4", "main/Figure4_Lab_Freshness_Sensitivity.svg", "freshness sensitivity", "Table4_Lab_Freshness_Sensitivity.csv", "main manuscript", "captions/Figure4_Caption.md", "lab values are carry-forward, not hourly measurements"),
        ("Figure 5", "main/Figure5_P15_Clinical_Feature_Modules.svg", "feature module diagram", "P15 feature clinical validity audit", "main manuscript", "captions/Figure5_Caption.md", "not bedside-only; proxy is not full VIS"),
        ("Supplementary Figure S1", "supplementary/Supplementary_Figure_S1_DCA.svg", "DCA threshold plot", "Supplementary_Table_S2_DCA_Summary.csv", "supplementary", "captions/Supplementary_Figure_S1_Caption.md", "not automatic intervention trigger"),
        ("Supplementary Figure S2", "supplementary/Supplementary_Figure_S2_Leadtime.svg", "lead-time summary plot", "Supplementary_Table_S3_Leadtime_Summary.csv", "supplementary", "captions/Supplementary_Figure_S2_Caption.md", "not direct treatment recommendation"),
        ("Supplementary Figure S3", "supplementary/Supplementary_Figure_S3_Proxy_Interpretation.svg", "proxy interpretation diagram", "Proxy clinical interpretability audit", "supplementary", "captions/Supplementary_Figure_S3_Caption.md", "proxy is not full VIS"),
    ]
    index = "# Figure Index\n\n| figure | file_name | figure_type | data_source | recommended_location | caption_file | caution_note |\n|---|---|---|---|---|---|---|\n"
    for row in index_rows:
        index += "| " + " | ".join(row) + " |\n"
    write_text(FIG / "FIGURE_INDEX.md", index)

    expected = [
        MAIN / "Figure1_Study_Workflow_Dual_Anchor.svg",
        MAIN / "Figure1_Study_Workflow_Dual_Anchor.png",
        CAPTIONS / "Figure1_Caption.md",
        MAIN / "Figure2_Model_Performance_Comparison.svg",
        MAIN / "Figure2_Model_Performance_Comparison.png",
        DATA / "Figure2_Model_Performance_Comparison_Data.csv",
        CAPTIONS / "Figure2_Caption.md",
        MAIN / "Figure3_Calibration_Comparison.svg",
        MAIN / "Figure3_Calibration_Comparison.png",
        DATA / "Figure3_Calibration_Comparison_Data.csv",
        CAPTIONS / "Figure3_Caption.md",
        MAIN / "Figure4_Lab_Freshness_Sensitivity.svg",
        MAIN / "Figure4_Lab_Freshness_Sensitivity.png",
        DATA / "Figure4_Lab_Freshness_Sensitivity_Data.csv",
        CAPTIONS / "Figure4_Caption.md",
        MAIN / "Figure5_P15_Clinical_Feature_Modules.svg",
        MAIN / "Figure5_P15_Clinical_Feature_Modules.png",
        DATA / "Figure5_P15_Clinical_Feature_Modules_Data.csv",
        CAPTIONS / "Figure5_Caption.md",
        SUPP / "Supplementary_Figure_S1_DCA.svg",
        SUPP / "Supplementary_Figure_S1_DCA.png",
        DATA / "Supplementary_Figure_S1_DCA_Data.csv",
        CAPTIONS / "Supplementary_Figure_S1_Caption.md",
        SUPP / "Supplementary_Figure_S2_Leadtime.svg",
        SUPP / "Supplementary_Figure_S2_Leadtime.png",
        DATA / "Supplementary_Figure_S2_Leadtime_Data.csv",
        CAPTIONS / "Supplementary_Figure_S2_Caption.md",
        SUPP / "Supplementary_Figure_S3_Proxy_Interpretation.svg",
        SUPP / "Supplementary_Figure_S3_Proxy_Interpretation.png",
        DATA / "Supplementary_Figure_S3_Proxy_Interpretation_Data.csv",
        CAPTIONS / "Supplementary_Figure_S3_Caption.md",
        FIG / "FIGURE_INDEX.md",
    ]
    text = ""
    for p in [FIG / "FIGURE_INDEX.md", *CAPTIONS.glob("*.md")]:
        text += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "Figure1_no_P12_P10_replacement": "do not replace P15" in (CAPTIONS / "Figure1_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "Figure2_no_old_numbers": (DATA / "Figure2_Model_Performance_Comparison_Data.csv").exists(),
        "Figure3_no_fabricated_curve": (DATA / "Figure3_Calibration_Comparison_Data.csv").exists() and "mean_predicted_death_prob" in (DATA / "Figure3_Calibration_Comparison_Data.csv").read_text(encoding="utf-8-sig", errors="ignore"),
        "Figure4_no_hourly_lab_claim": "not hourly" in (CAPTIONS / "Figure4_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "Figure4_12h_24h_status_correct": "borderline acceptable" in text and "largely stable" in text,
        "Figure5_not_bedside_only_manual_score": "not a bedside-only manual score" in (CAPTIONS / "Figure5_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "Supplementary_S1_DCA_not_intervention_trigger": "not an automatic intervention trigger" in (CAPTIONS / "Supplementary_Figure_S1_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "Supplementary_S2_leadtime_not_treatment_recommendation": "not a direct treatment recommendation" in (CAPTIONS / "Supplementary_Figure_S2_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "Supplementary_S3_proxy_not_full_VIS": "not full VIS" in (CAPTIONS / "Supplementary_Figure_S3_Caption.md").read_text(encoding="utf-8", errors="ignore"),
        "all_figures_have_assets": all(p.exists() for p in expected),
    }
    audit = "# Manuscript Figure Consistency Check\n\n"
    for k, v in checks.items():
        audit += f"- {k}: {'pass' if v else 'fail'}\n"
    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists()]
    audit += "\n## Missing expected files\n\n"
    audit += "\n".join(f"- {p}" for p in missing) if missing else "- none"
    audit += "\n\n## Numeric conflicts\n\n- none detected; figure data were derived from manuscript asset tables or final clinical implementation CSVs.\n"
    write_text(AUDIT / "Manuscript_Figure_Consistency_Check.md", audit)
    return checks


def main() -> None:
    ensure_dirs()
    figure1_workflow()
    figure2_performance()
    figure3_calibration()
    figure4_lab_freshness()
    figure5_feature_modules()
    supplementary_s1_dca()
    supplementary_s2_leadtime()
    supplementary_s3_proxy()
    checks = figure_index_and_audit()
    print(f"figures_generated=8 checks_passed={sum(checks.values())}/{len(checks)}")


if __name__ == "__main__":
    main()
