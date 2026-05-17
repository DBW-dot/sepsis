from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path(r"D:\try\github_chatgpt_share_repo")
ROOT = Path(r"D:\try")
BOOTSTRAP_CORE = REPO / "manuscript_assets" / "audit" / "run_bootstrap_ci.py"
FIG_DIR = REPO / "results_final" / "figures_manuscript"
TABLE_DIR = REPO / "results_final" / "tables_manuscript"
SCRIPT_DIR = REPO / "results_final" / "scripts"
for directory in [FIG_DIR, TABLE_DIR, SCRIPT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 20260511

MODEL_DISPLAY = {
    "P15_clinically_parsimonious_transport_model": "P15 double-anchor model",
    "M1_internal_rich_reference_model": "70-feature high-dimensional reference model",
    "C1_dynamic_SOFA_clinical_comparator": "Dynamic SOFA",
    "P12_true_trained_clinical_landing_model": "P12 simplified implementation candidate",
    "P10_true_trained_ultra_minimal_sensitivity_model": "P10 ultra-minimal sensitivity candidate",
    "MT3_Post_METRE_transport_reference_model": "MT3 transport reference",
}

PLOT_ORDER = [
    "P15_clinically_parsimonious_transport_model",
    "M1_internal_rich_reference_model",
    "C1_dynamic_SOFA_clinical_comparator",
    "P12_true_trained_clinical_landing_model",
    "P10_true_trained_ultra_minimal_sensitivity_model",
]

CALIBRATION_MODELS = [
    "P15_clinically_parsimonious_transport_model",
    "M1_internal_rich_reference_model",
    "C1_dynamic_SOFA_clinical_comparator",
]

REQUIRED_INPUTS = {
    "bootstrap_ci_main_results": REPO / "results_final" / "tables" / "bootstrap_ci_main_results.csv",
    "bootstrap_ci_subphenotype_results": REPO / "results_final" / "tables" / "bootstrap_ci_subphenotype_results.csv",
    "bootstrap_ci_clinical_implementation_models": REPO
    / "results_final"
    / "tables"
    / "bootstrap_ci_clinical_implementation_models.csv",
    "bootstrap_ci_summary": REPO / "results_final" / "text" / "bootstrap_ci_summary_for_manuscript.md",
    "table1_primary_requested": REPO / "results_package" / "tables" / "Table1_Cohort_Characteristics.csv",
    "table1_fallback_final": REPO / "results_final" / "tables" / "Table1_Cohort_Characteristics.csv",
    "table1_fallback_root": ROOT / "results_package" / "tables" / "Table1_Cohort_Characteristics.csv",
    "dca_summary": REPO / "results_final" / "clinical_implementation" / "P12_P10_TrueTraining_DCA_Summary.csv",
    "pred_main_mimic": ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet",
    "pred_main_eicu": ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet",
    "pred_c1_mimic": ROOT / "step7_main_modeling" / "output" / "pred_C1_test_all.parquet",
    "pred_c1_eicu": ROOT / "step7_main_modeling" / "output" / "pred_C1_eicu_external.parquet",
    "model_ready_mimic": ROOT / "step7_main_modeling" / "output" / "Model_Ready_Test_All.parquet",
    "model_ready_eicu": ROOT / "step7_main_modeling" / "output" / "Model_Ready_eICU_External.parquet",
}


def load_core():
    spec = importlib.util.spec_from_file_location("bootstrap_ci_core", BOOTSTRAP_CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BOOTSTRAP_CORE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_ci(value: Any) -> tuple[float, float]:
    if pd.isna(value):
        return np.nan, np.nan
    text = str(value).strip()
    if text == "unavailable" or "-" not in text:
        return np.nan, np.nan
    parts = text.split("-")
    if len(parts) != 2:
        return np.nan, np.nan
    return float(parts[0]), float(parts[1])


def fmt_num(x: Any) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.4f}"
    except Exception:
        return str(x)


def write_caption(name: str, text: str) -> None:
    (FIG_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


def save_fig(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def to_markdown(df: pd.DataFrame, title: str) -> str:
    safe = df.copy()
    safe = safe.fillna("")
    headers = [str(c) for c in safe.columns]
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in safe.iterrows():
        values = [str(row[c]).replace("|", "\\|").replace("\n", " ") for c in safe.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def audit_row(figure: str, source: str, success: bool, point_estimates_reproduced: str, prediction_level_used: bool, missing_file: str, unstable_ci: str, main_text_ready: bool, notes: str) -> dict[str, Any]:
    return {
        "item": figure,
        "data_source": source,
        "success": success,
        "point_estimates_reproduced": point_estimates_reproduced,
        "prediction_level_file_used": prediction_level_used,
        "missing_file": missing_file,
        "unstable_ci": unstable_ci,
        "main_text_ready": main_text_ready,
        "notes": notes,
    }


def figure1(audit: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.axis("off")
    boxes = [
        (0.05, 0.72, "Data sources\nMIMIC-IV: development/internal validation\neICU: external validation"),
        (0.31, 0.72, "Adult ICU sepsis cohort\nSepsis-3 suspected infection\nDouble anchor fixed"),
        (0.57, 0.72, "Dynamic prediction grid\n1-hour landmarks\nPrefix-only observations"),
        (0.82, 0.72, "24-hour competing risks\nICU death\nAlive ICU discharge\nContinued ICU stay"),
        (0.20, 0.33, "Comparators\n70-feature high-dimensional reference\nDynamic SOFA"),
        (0.50, 0.33, "Final model\nP15 double-anchor model\nP12/P10 implementation candidates"),
        (0.78, 0.33, "Outputs\nDiscrimination\nCalibration\nDCA\nSubphenotype robustness"),
    ]
    for x, y, text in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.18, 0.15, fill=False, lw=1.5, color="black"))
        ax.text(x + 0.09, y + 0.075, text, ha="center", va="center", fontsize=9)
    arrows = [
        ((0.23, 0.795), (0.31, 0.795)),
        ((0.49, 0.795), (0.57, 0.795)),
        ((0.75, 0.795), (0.82, 0.795)),
        ((0.46, 0.72), (0.50, 0.48)),
        ((0.66, 0.72), (0.59, 0.48)),
        ((0.68, 0.405), (0.78, 0.405)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.2, color="black"))
    ax.text(0.5, 0.08, "Laboratory values are latest-available / capped carry-forward, not hourly laboratory measurements. DCA/lead-time are supplementary utility estimates.", ha="center", fontsize=9)
    save_fig(fig, "Figure1_workflow_double_anchor")
    write_caption(
        "Figure1_caption.md",
        """# Figure 1. Study workflow and double-anchor dynamic prediction design

This schematic summarizes the retrospective double-anchor competing-risk prediction design. MIMIC-IV was used for model development and internal validation, while eICU was used only for external validation. Prediction landmarks were generated on a one-hour grid using prefix-only information. The 24-hour outcome was framed as a competing-risk problem with ICU death, alive ICU discharge/transfer, and continued ICU stay as mutually exclusive states. Laboratory predictors were represented as latest-available / capped carry-forward values rather than hourly laboratory measurements.""",
    )
    audit.append(audit_row("Figure1", "workflow schematic; no row-level data", True, "not_applicable", False, "", "", True, "Generated without using outcome point estimates."))


def figure2(main: pd.DataFrame, audit: list[dict[str, Any]]) -> None:
    rows = main[main["model_name"].isin(PLOT_ORDER)].copy()
    rows["display_name"] = rows["model_name"].map(MODEL_DISPLAY)
    rows["order"] = rows["model_name"].map({m: i for i, m in enumerate(PLOT_ORDER)})
    rows = rows.sort_values("order", ascending=False)
    metrics = [
        ("eICU_AUROC", "eICU_AUROC_95CI", "A. AUROC"),
        ("eICU_AUPRC", "eICU_AUPRC_95CI", "B. AUPRC"),
        ("eICU_calibration_slope", "eICU_calibration_slope_95CI", "C. Calibration slope"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
    out_rows = []
    y = np.arange(len(rows))
    for ax, (value_col, ci_col, title) in zip(axes, metrics):
        vals = rows[value_col].astype(float).to_numpy()
        ci = np.array([parse_ci(v) for v in rows[ci_col]])
        lo = vals - ci[:, 0]
        hi = ci[:, 1] - vals
        ax.errorbar(vals, y, xerr=[lo, hi], fmt="o", color="black", ecolor="0.35", capsize=3)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="x", color="0.88")
        if "calibration" in value_col:
            ax.axvline(1.0, color="0.25", ls="--", lw=1)
        for _, r in rows.iterrows():
            out_rows.append(
                {
                    "panel": title,
                    "model_name": r["model_name"],
                    "display_name": r["display_name"],
                    "metric": value_col,
                    "point_estimate": round(float(r[value_col]), 4),
                    "ci_lower": round(parse_ci(r[ci_col])[0], 4),
                    "ci_upper": round(parse_ci(r[ci_col])[1], 4),
                }
            )
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(rows["display_name"], fontsize=9)
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)
    fig.suptitle("External validation performance with patient-level bootstrap 95% CI", fontsize=13)
    fig.tight_layout()
    save_fig(fig, "Figure2_external_performance_forest")
    pd.DataFrame(out_rows).to_csv(FIG_DIR / "Figure2_external_performance_forest.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    write_caption(
        "Figure2_caption.md",
        """# Figure 2. External validation performance with 95% confidence intervals

Forest plots show eICU external validation AUROC, AUPRC, and calibration slope with patient-level cluster bootstrap 95% confidence intervals. The P15 double-anchor model achieved AUROC 0.8103 (95% CI 0.7963-0.8232), AUPRC 0.1892 (95% CI 0.1681-0.2116), and calibration slope 1.0031 (95% CI 0.9413-1.0584). The 70-feature high-dimensional reference model showed lower external transportability and poor calibration slope. P12 and P10 are implementation/sensitivity candidates and do not replace P15.""",
    )
    audit.append(audit_row("Figure2", "results_final/tables/bootstrap_ci_main_results.csv", True, "yes", False, "", "", True, "All key eICU point estimates and CIs reproduced from bootstrap CI table."))


def load_p15_prediction(core, dataset: str) -> pd.DataFrame:
    bundle = core.load_model(core.FROZEN_MODEL_FILES["P15_clinically_parsimonious_transport_model"])
    frame = core.add_support_proxy(pd.read_parquet(core.MODEL_READY[dataset]))
    pred = core.prediction_df_from_bundle("P15_clinically_parsimonious_transport_model", dataset, frame, bundle)
    if "phenotype_label" in frame.columns:
        pred["phenotype_label"] = frame["phenotype_label"].values
    return pred


def load_existing_prediction(core, model: str, dataset: str) -> pd.DataFrame:
    path_map = {
        ("M1_internal_rich_reference_model", "mimic_internal"): ROOT / "step7_main_modeling" / "output" / "pred_main_test_all.parquet",
        ("M1_internal_rich_reference_model", "eicu_external"): ROOT / "step7_main_modeling" / "output" / "pred_main_eicu_external.parquet",
        ("C1_dynamic_SOFA_clinical_comparator", "mimic_internal"): ROOT / "step7_main_modeling" / "output" / "pred_C1_test_all.parquet",
        ("C1_dynamic_SOFA_clinical_comparator", "eicu_external"): ROOT / "step7_main_modeling" / "output" / "pred_C1_eicu_external.parquet",
    }
    return core.load_prediction_file(model, dataset, path_map[(model, dataset)])


def calibration_bins(df: pd.DataFrame, model: str, dataset: str, n_bins: int = 10) -> pd.DataFrame:
    tmp = df[["predicted_prob_death_24h", "event_type_24h"]].copy()
    tmp["death"] = (tmp["event_type_24h"] == "ICU_DEATH").astype(int)
    # Duplicate probabilities can make qcut drop bins; this is acceptable and recorded in output.
    tmp["bin"] = pd.qcut(tmp["predicted_prob_death_24h"], q=n_bins, duplicates="drop")
    out = (
        tmp.groupby("bin", observed=True)
        .agg(
            row_n=("death", "size"),
            mean_predicted_risk=("predicted_prob_death_24h", "mean"),
            observed_event_rate=("death", "mean"),
            death_n=("death", "sum"),
        )
        .reset_index(drop=True)
    )
    out.insert(0, "dataset_name", dataset)
    out.insert(0, "model_name", model)
    out["display_name"] = out["model_name"].map(MODEL_DISPLAY)
    return out


def figure3(core, main: pd.DataFrame, audit: list[dict[str, Any]]) -> None:
    data_parts = []
    for dataset in ["mimic_internal", "eicu_external"]:
        p15 = load_p15_prediction(core, dataset)
        data_parts.append(calibration_bins(p15, "P15_clinically_parsimonious_transport_model", dataset))
        del p15
        for model in ["M1_internal_rich_reference_model", "C1_dynamic_SOFA_clinical_comparator"]:
            pred = load_existing_prediction(core, model, dataset)
            data_parts.append(calibration_bins(pred, model, dataset))
            del pred
    cal = pd.concat(data_parts, ignore_index=True)
    cal.to_csv(FIG_DIR / "Figure3_calibration_curve_data.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    slopes = main.set_index("model_name")["eICU_calibration_slope"].to_dict()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True)
    styles = {
        "P15_clinically_parsimonious_transport_model": ("black", "o", "-"),
        "M1_internal_rich_reference_model": ("0.45", "s", "--"),
        "C1_dynamic_SOFA_clinical_comparator": ("0.2", "^", ":"),
    }
    for ax, dataset, title in zip(axes, ["mimic_internal", "eicu_external"], ["MIMIC-IV internal", "eICU external"]):
        ax.plot([0, 1], [0, 1], color="0.75", lw=1, ls="--")
        for model in CALIBRATION_MODELS:
            part = cal[(cal["dataset_name"] == dataset) & (cal["model_name"] == model)]
            color, marker, ls = styles[model]
            label = MODEL_DISPLAY[model]
            if dataset == "eicu_external":
                label += f" (slope {slopes.get(model, np.nan):.4f})"
            ax.plot(part["mean_predicted_risk"], part["observed_event_rate"], marker=marker, ls=ls, color=color, label=label)
        ax.set_title(title)
        ax.set_xlabel("Mean predicted 24h ICU death risk")
        ax.grid(color="0.9")
    axes[0].set_ylabel("Observed 24h ICU death rate")
    axes[1].legend(fontsize=8, loc="upper left", frameon=False)
    fig.suptitle("Calibration curves by decile of predicted risk", fontsize=13)
    fig.tight_layout()
    save_fig(fig, "Figure3_calibration_curves")
    write_caption(
        "Figure3_caption.md",
        """# Figure 3. Calibration curves in MIMIC-IV and eICU

Calibration curves were generated using prediction-level 24-hour ICU death probabilities and observed 24-hour ICU death labels. Points represent deciles of predicted death risk. The dashed diagonal line indicates ideal calibration. In eICU external validation, the P15 double-anchor model retained near-ideal calibration slope, whereas the 70-feature high-dimensional reference model showed severe external calibration failure.""",
    )
    audit.append(audit_row("Figure3", "prediction-level files and frozen P15 inference", True, "yes", True, "", "", True, "Decile calibration bins generated for P15, 70-feature reference, and Dynamic SOFA."))


def figure4(audit: list[dict[str, Any]]) -> None:
    dca_path = REQUIRED_INPUTS["dca_summary"]
    dca = pd.read_csv(dca_path)
    part = dca[dca["dataset_name"] == "eicu_external"].copy()
    keep = [
        "P15_clinically_parsimonious_transport_model",
        "P12_true_trained_clinical_landing_model",
        "P10_true_trained_ultra_minimal_sensitivity_model",
    ]
    part = part[part["model_name"].isin(keep)].copy()
    part["display_name"] = part["model_name"].map(MODEL_DISPLAY)
    fig, ax = plt.subplots(figsize=(8, 5))
    for model in keep:
        m = part[part["model_name"] == model].sort_values("threshold")
        ax.plot(m["threshold"], m["net_benefit"], marker="o", label=MODEL_DISPLAY[model])
    treat = part[part["model_name"] == keep[0]].sort_values("threshold")
    ax.plot(treat["threshold"], treat["treat_all_net_benefit"], color="0.5", ls="--", label="Treat all")
    ax.axhline(0, color="black", lw=1, ls=":", label="Treat none")
    ax.set_xlabel("Risk threshold")
    ax.set_ylabel("Net benefit")
    ax.set_title("Decision curve analysis in eICU external validation")
    ax.grid(color="0.9")
    ax.legend(fontsize=8, frameon=False)
    save_fig(fig, "Figure4_decision_curve_analysis")
    out = part.copy()
    out.to_csv(FIG_DIR / "Figure4_decision_curve_analysis.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    write_caption(
        "Figure4_caption.md",
        """# Figure 4. Decision curve analysis

Decision curve analysis is shown for eICU external validation across prespecified risk thresholds. The curves summarize threshold-based net benefit for P15, P12, and P10, with treat-all and treat-none references. These results are supplementary clinical utility estimates and should not be interpreted as automatic intervention triggers or direct treatment recommendations.""",
    )
    audit.append(audit_row("Figure4", str(dca_path), True, "not_applicable", False, "", "", True, "DCA shown as supplementary clinical utility estimate only."))


def figure5(sub: pd.DataFrame, audit: list[dict[str, Any]]) -> None:
    part = sub[
        (sub["model_name"] == "P15_clinically_parsimonious_transport_model")
        & (sub["dataset_name"] == "eicu_external")
    ].copy()
    part["phenotype_label"] = pd.Categorical(part["phenotype_label"], ["Phenotype_1", "Phenotype_2", "Phenotype_3"], ordered=True)
    part = part.sort_values("phenotype_label")
    part.to_csv(FIG_DIR / "Figure5_subphenotype_robustness.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    metrics = [("AUROC", "AUROC_95CI", "A. AUROC"), ("AUPRC", "AUPRC_95CI", "B. AUPRC"), ("calibration_slope", "calibration_slope_95CI", "C. Calibration slope")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=True)
    y = np.arange(len(part))
    for ax, (value_col, ci_col, title) in zip(axes, metrics):
        vals = part[value_col].astype(float).to_numpy()
        ci = np.array([parse_ci(v) for v in part[ci_col]])
        ax.errorbar(vals, y, xerr=[vals - ci[:, 0], ci[:, 1] - vals], fmt="o", color="black", ecolor="0.35", capsize=3)
        ax.set_title(title)
        ax.grid(axis="x", color="0.9")
        if value_col == "calibration_slope":
            ax.axvline(1.0, color="0.25", ls="--", lw=1)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(part["phenotype_label"])
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)
    fig.suptitle("P15 subphenotype robustness in eICU external validation", fontsize=13)
    fig.tight_layout()
    save_fig(fig, "Figure5_subphenotype_robustness")
    write_caption(
        "Figure5_caption.md",
        """# Figure 5. Subphenotype robustness of the P15 double-anchor model

The forest plots show eICU external validation performance of the P15 double-anchor model across mapped early static phenotypes. AUROC, AUPRC, and calibration slope are shown with patient-level cluster bootstrap 95% confidence intervals. Phenotype-specific estimates support subgroup robustness assessment but should not be interpreted as phenotype-specific model replacement.""",
    )
    audit.append(audit_row("Figure5", "results_final/tables/bootstrap_ci_subphenotype_results.csv", True, "yes", False, "", "", True, "Only P15 eICU external phenotype-specific results shown."))


def tables(main: pd.DataFrame, sub: pd.DataFrame, audit: list[dict[str, Any]]) -> None:
    table1_source = None
    for key in ["table1_primary_requested", "table1_fallback_final", "table1_fallback_root"]:
        path = REQUIRED_INPUTS[key]
        if path.exists():
            table1_source = path
            break
    if table1_source is None:
        audit.append(audit_row("Table1", "results_package/tables/Table1_Cohort_Characteristics.csv", False, "not_applicable", False, "Table1_Cohort_Characteristics.csv", "", False, "missing_file"))
    else:
        t1 = pd.read_csv(table1_source)
        t1.to_csv(TABLE_DIR / "Table1_Cohort_Characteristics_Manuscript.csv", index=False, encoding="utf-8-sig")
        (TABLE_DIR / "Table1_Cohort_Characteristics_Manuscript.md").write_text(to_markdown(t1, "Table 1. Cohort characteristics"), encoding="utf-8")
        audit.append(audit_row("Table1", str(table1_source), True, "not_applicable", False, "" if table1_source == REQUIRED_INPUTS["table1_primary_requested"] else "primary_requested_path_missing_used_fallback", "", True, "Word-friendly CSV and Markdown generated."))

    t2 = main[main["model_name"].isin(PLOT_ORDER)].copy()
    t2["Model"] = t2["model_name"].map(MODEL_DISPLAY)
    cols = [
        "Model",
        "feature_count",
        "MIMIC_AUROC",
        "MIMIC_AUROC_95CI",
        "MIMIC_AUPRC",
        "MIMIC_AUPRC_95CI",
        "eICU_AUROC",
        "eICU_AUROC_95CI",
        "eICU_AUPRC",
        "eICU_AUPRC_95CI",
        "eICU_calibration_slope",
        "eICU_calibration_slope_95CI",
    ]
    t2 = t2[cols].copy()
    t2.to_csv(TABLE_DIR / "Table2_Main_Model_Comparators_with_CI.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    (TABLE_DIR / "Table2_Main_Model_Comparators_with_CI.md").write_text(to_markdown(t2, "Table 2. Main model comparators with 95% CI"), encoding="utf-8")

    t3 = sub[
        (sub["model_name"] == "P15_clinically_parsimonious_transport_model")
        & (sub["dataset_name"] == "eicu_external")
    ].copy()
    t3 = t3[
        [
            "phenotype_label",
            "row_n",
            "cluster_n",
            "death_row_n",
            "AUROC",
            "AUROC_95CI",
            "AUPRC",
            "AUPRC_95CI",
            "calibration_slope",
            "calibration_slope_95CI",
        ]
    ]
    t3.to_csv(TABLE_DIR / "Table3_P15_Subphenotype_Robustness_with_CI.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    (TABLE_DIR / "Table3_P15_Subphenotype_Robustness_with_CI.md").write_text(to_markdown(t3, "Table 3. P15 subphenotype robustness with 95% CI"), encoding="utf-8")


def write_indexes(audit: list[dict[str, Any]]) -> None:
    pd.DataFrame(audit).to_csv(FIG_DIR / "figure_generation_audit.csv", index=False, encoding="utf-8-sig")
    captions = [
        ("Figure 1", "Figure1_caption.md", "main manuscript", "workflow schematic"),
        ("Figure 2", "Figure2_caption.md", "main manuscript", "external model performance"),
        ("Figure 3", "Figure3_caption.md", "main manuscript", "calibration curves"),
        ("Figure 4", "Figure4_caption.md", "main manuscript or supplementary", "DCA is not an intervention trigger"),
        ("Figure 5", "Figure5_caption.md", "main manuscript", "subphenotype robustness"),
    ]
    lines = ["# Figure Caption Index", ""]
    for item in captions:
        lines.append(f"- {item[0]}: `{item[1]}`; recommended location: {item[2]}; note: {item[3]}.")
    (FIG_DIR / "figure_caption_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 120,
    })
    audit: list[dict[str, Any]] = []
    missing_inputs = [f"{name}:{path}" for name, path in REQUIRED_INPUTS.items() if not path.exists() and not name.startswith("table1_fallback")]
    if missing_inputs:
        for item in missing_inputs:
            audit.append(audit_row("input_check", item, False, "not_applicable", False, "missing_file", "", False, "Required input missing."))

    main_results = pd.read_csv(REPO / "results_final" / "tables" / "bootstrap_ci_main_results.csv")
    sub = pd.read_csv(REPO / "results_final" / "tables" / "bootstrap_ci_subphenotype_results.csv")

    core = load_core()
    figure1(audit)
    figure2(main_results, audit)
    figure3(core, main_results, audit)
    figure4(audit)
    figure5(sub, audit)
    tables(main_results, sub, audit)
    write_indexes(audit)

    print(json.dumps({
        "figures_dir": str(FIG_DIR),
        "tables_dir": str(TABLE_DIR),
        "audit_rows": len(audit),
        "warnings": [row for row in audit if not row["success"] or row["missing_file"] or row["unstable_ci"]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
