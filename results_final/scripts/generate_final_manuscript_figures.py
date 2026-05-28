from __future__ import annotations

import json
import math
import pickle
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FuncFormatter


REPO = Path(r"D:\try\github_chatgpt_share_repo")
ROOT = Path(r"D:\try")
FIG_DIR = REPO / "results_final" / "figures"
TEXT_DIR = REPO / "results_final" / "text"
TABLE_DIR = REPO / "results_final" / "tables"
SCRIPT_PATH = REPO / "results_final" / "scripts" / "generate_final_manuscript_figures.py"
for directory in [FIG_DIR, TEXT_DIR, TABLE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

STEP7 = ROOT / "step7_main_modeling" / "output"
MODEL_READY_EXTERNAL = STEP7 / "Model_Ready_eICU_External.parquet"
P15_MODEL = ROOT / "parsimonious_features" / "model_P15_minimal_bedside_model.pkl"
M1_EICU_PRED = STEP7 / "pred_main_eicu_external.parquet"

MAIN_CI = REPO / "results_final" / "tables" / "bootstrap_ci_main_results.csv"
CLINICAL_CI = REPO / "results_final" / "tables" / "bootstrap_ci_clinical_implementation_models.csv"
SUBPHENO_CI = REPO / "results_final" / "tables" / "bootstrap_ci_subphenotype_results.csv"
DCA_SUMMARY = REPO / "results_final" / "clinical_implementation" / "P12_P10_TrueTraining_DCA_Summary.csv"
THRESHOLD_PERF = REPO / "results_final" / "tables" / "P15_eICU_threshold_specific_performance.csv"
FEATURE_SOURCE = REPO / "results_final" / "tables" / "P15_feature_source_availability_deployment_table.csv"
FEATURE_MISSING = REPO / "results_final" / "tables" / "P15_feature_missingness_audit.csv"

DEATH_LABEL = "ICU_DEATH"
RNG_SEED = 20260511


plt.rcParams.update(
    {
        "font.family": "Microsoft YaHei",
        "axes.unicode_minus": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
    }
)


PALETTE = {
    "p15": "#1769aa",
    "m1": "#c73e36",
    "sofa": "#6c757d",
    "p12": "#2a9d8f",
    "p10": "#7b2cbf",
    "mt3": "#f4a261",
    "gold": "#e9c46a",
    "green": "#2f7d32",
    "bg": "#f7f7f2",
}

MODEL_LABELS = {
    "M1_internal_rich_reference_model": "70-feature\nM1",
    "MT3_Post_METRE_transport_reference_model": "MT3",
    "P15_clinically_parsimonious_transport_model": "P15",
    "P12_true_trained_clinical_landing_model": "P12",
    "P10_true_trained_ultra_minimal_sensitivity_model": "P10",
    "C1_dynamic_SOFA_clinical_comparator": "Dynamic\nSOFA",
}


def pct(x: float, pos: int | None = None) -> str:
    return f"{x:.0%}"


def save_fig(fig: plt.Figure, png: Path, pdf: Path) -> None:
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def split_ci(ci: Any) -> tuple[float, float]:
    if pd.isna(ci):
        return math.nan, math.nan
    text = str(ci).replace("–", "-")
    if "-" not in text:
        return math.nan, math.nan
    a, b = text.split("-", 1)
    return float(a), float(b)


def figure_header(ax: plt.Axes, title: str, subtitle: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=13, pad=10, fontweight="bold")
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#555555")


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def build_support_proxy(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["support_hemodynamic_component"] = pd.concat(
        [
            (df["map_deficit"].clip(lower=0, upper=50) / 50.0).where(df["map_deficit"].notna()),
            (df["map_below_65_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["map_below_65_burden_24h"].notna()
            ),
        ],
        axis=1,
    ).mean(axis=1)
    out["support_lactate_component"] = pd.concat(
        [
            (df["lactate_gt2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["lactate_gt2_burden_24h"].notna()
            ),
            (df["lactate_gt4_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["lactate_gt4_burden_24h"].notna()
            ),
        ],
        axis=1,
    ).mean(axis=1)
    out["support_renal_component"] = pd.concat(
        [
            (df["oliguria_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["oliguria_burden_24h"].notna()
            ),
            df["worsening_renal_trajectory_flag"].where(df["worsening_renal_trajectory_flag"].notna()),
        ],
        axis=1,
    ).mean(axis=1)
    out["support_respiratory_component"] = pd.concat(
        [
            (df["high_fio2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["high_fio2_burden_24h"].notna()
            ),
            (df["low_spo2_burden_24h"].clip(lower=0, upper=24) / 24.0).where(
                df["low_spo2_burden_24h"].notna()
            ),
            (df["ventilation_transition_count_24h"].clip(lower=0, upper=6) / 6.0).where(
                df["ventilation_transition_count_24h"].notna()
            ),
        ],
        axis=1,
    ).mean(axis=1)
    out["shared_support_intensity_proxy"] = out[
        [
            "support_hemodynamic_component",
            "support_lactate_component",
            "support_renal_component",
            "support_respiratory_component",
        ]
    ].mean(axis=1)
    return out


def p15_external_predictions() -> pd.DataFrame:
    with P15_MODEL.open("rb") as f:
        bundle = pickle.load(f)
    df = pd.read_parquet(MODEL_READY_EXTERNAL)
    proxy = build_support_proxy(df)
    for col in proxy.columns:
        df[col] = proxy[col]
    features = list(bundle["features"])
    logits = bundle["pipeline"].decision_function(df[features]) / float(bundle.get("temperature", 1.0))
    probs = softmax(logits)
    classes = [str(x) for x in bundle["classes"]]
    death_idx = classes.index(DEATH_LABEL)
    out = df[["patient_id", "stay_id", "event_type_24h", "phenotype_label"]].copy()
    out["predicted_prob_death_24h"] = probs[:, death_idx]
    out["event_indicator_death_24h"] = (out["event_type_24h"].astype(str) == DEATH_LABEL).astype(int)
    return out


def normalize_pred_file(path: Path, model_name: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "prob_death_raw" in df.columns and "predicted_prob_death_24h" not in df.columns:
        df = df.rename(columns={"prob_death_raw": "predicted_prob_death_24h"})
    if "event_indicator_death_24h" not in df.columns:
        label_col = "event_type_24h" if "event_type_24h" in df.columns else "true_event_type_24h"
        df["event_indicator_death_24h"] = (df[label_col].astype(str) == DEATH_LABEL).astype(int)
    df["model_name"] = model_name
    return df


def calibration_curve_data(df: pd.DataFrame, model_name: str, n_bins: int = 20) -> pd.DataFrame:
    work = df[["predicted_prob_death_24h", "event_indicator_death_24h"]].copy()
    work["predicted_prob_death_24h"] = work["predicted_prob_death_24h"].clip(0, 1)
    # Quantile bins avoid empty high-risk bins in low-incidence data.
    work["bin"] = pd.qcut(work["predicted_prob_death_24h"], q=n_bins, duplicates="drop")
    out = (
        work.groupby("bin", observed=True)
        .agg(
            mean_predicted_risk=("predicted_prob_death_24h", "mean"),
            observed_death_rate=("event_indicator_death_24h", "mean"),
            row_n=("event_indicator_death_24h", "size"),
            death_n=("event_indicator_death_24h", "sum"),
        )
        .reset_index(drop=True)
    )
    out["model_name"] = model_name
    return out


def draw_box(ax: plt.Axes, x: float, y: float, w: float, h: float, text: str, color: str, fontsize: int = 9) -> None:
    box = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.2,
        edgecolor=color,
        facecolor=color + "18",
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)


def arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float, color: str = "#333333") -> None:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5, color=color))


def create_graphical_abstract() -> dict[str, Any]:
    png = FIG_DIR / "Graphical_Abstract_P15_vs_highdimensional.png"
    pdf = FIG_DIR / "Graphical_Abstract_P15_vs_highdimensional.pdf"
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(patches.Rectangle((0, 0), 0.49, 1, facecolor="#fff3f0", edgecolor="none"))
    ax.add_patch(patches.Rectangle((0.51, 0), 0.49, 1, facecolor="#eef7ff", edgecolor="none"))
    ax.text(0.245, 0.93, "Traditional high-dimensional path", ha="center", fontsize=15, fontweight="bold", color=PALETTE["m1"])
    ax.text(0.755, 0.93, "P15 clinically aligned path", ha="center", fontsize=15, fontweight="bold", color=PALETTE["p15"])

    left_steps = [
        "Single ICU-admission anchor",
        "Non-competing-risk framing",
        "70 high-dimensional features",
        "eICU calibration slope = 0.0728",
    ]
    right_steps = [
        "Dual anchors: t_ICU + t_sepsis",
        "Competing outcomes: death vs alive discharge",
        "15 clinically parsimonious variables",
        "eICU AUROC 0.8103 | AUPRC 0.1892 | slope 1.0031",
    ]
    for i, text in enumerate(left_steps):
        y = 0.78 - i * 0.13
        draw_box(ax, 0.06, y, 0.32, 0.08, text, PALETTE["m1"])
        if i < len(left_steps) - 1:
            arrow(ax, 0.22, y, 0.22, y - 0.04, PALETTE["m1"])
    for i, text in enumerate(right_steps):
        y = 0.78 - i * 0.13
        draw_box(ax, 0.60, y, 0.34, 0.08, text, PALETTE["p15"])
        if i < len(right_steps) - 1:
            arrow(ax, 0.77, y, 0.77, y - 0.04, PALETTE["p15"])

    # Broken target versus calibrated target.
    ax.add_patch(patches.Circle((0.245, 0.18), 0.095, fill=False, ec=PALETTE["m1"], lw=2))
    ax.add_patch(patches.Circle((0.245, 0.18), 0.055, fill=False, ec=PALETTE["m1"], lw=1.6))
    ax.plot([0.19, 0.225], [0.27, 0.22], color=PALETTE["m1"], lw=3)
    ax.text(0.245, 0.055, "External calibration collapse", ha="center", fontsize=10, color=PALETTE["m1"])

    ax.plot([0.64, 0.89], [0.08, 0.31], ls="--", color="#777777", lw=1.2)
    ax.plot([0.64, 0.89], [0.085, 0.30], color=PALETTE["p15"], lw=3)
    ax.text(0.765, 0.055, "Near-ideal external calibration", ha="center", fontsize=10, color=PALETTE["p15"])
    save_fig(fig, png, pdf)
    return record("Graphical Abstract", "Graphical Abstract", True, "mechanism schematic", "Locked manuscript numbers; no result recomputation", png, pdf)


def create_figure1() -> dict[str, Any]:
    png = FIG_DIR / "Figure1_workflow_double_anchor_competing_risk.png"
    pdf = FIG_DIR / "Figure1_workflow_double_anchor_competing_risk.pdf"
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.95, "Figure 1. Study workflow and dual-anchor competing-risk framework", fontsize=15, fontweight="bold")
    stages = [
        ("Data sources", "MIMIC-IV\ndevelopment/internal validation\n\neICU\nexternal validation"),
        ("Sepsis-3 cohort", "suspected infection\nSOFA change\nICU sepsis stays"),
        ("Dynamic grid", "hourly t_pred\nprefix-only observations\nno future information"),
        ("Model stack", "70-feature M1\nDynamic SOFA\nP15 final model\nP12/P10 sensitivity"),
        ("Competing-risk label", "ICU death within 24h\nalive ICU discharge/transfer\ncontinued ICU stay"),
    ]
    x_positions = [0.04, 0.23, 0.42, 0.61, 0.80]
    for i, ((title, body), x) in enumerate(zip(stages, x_positions)):
        draw_box(ax, x, 0.52, 0.15, 0.27, f"{title}\n\n{body}", PALETTE["p15"], fontsize=8)
        if i < len(stages) - 1:
            arrow(ax, x + 0.15, 0.66, x_positions[i + 1], 0.66)
    ax.text(0.06, 0.36, "Dual-anchor alignment", fontsize=12, fontweight="bold", color=PALETTE["p15"])
    ax.plot([0.08, 0.43], [0.28, 0.28], color="#333", lw=2)
    ax.scatter([0.13, 0.30, 0.38], [0.28, 0.28, 0.28], s=[110, 110, 90], c=[PALETTE["p15"], PALETTE["m1"], "#111111"])
    ax.text(0.13, 0.22, "t_ICU", ha="center")
    ax.text(0.30, 0.22, "t_sepsis", ha="center")
    ax.text(0.38, 0.22, "t_pred", ha="center")
    ax.text(0.52, 0.33, "Output is a three-state risk distribution, not a binary censoring shortcut.", fontsize=10)
    draw_box(ax, 0.52, 0.20, 0.14, 0.08, "p(death)", "#cc3d3d")
    draw_box(ax, 0.68, 0.20, 0.14, 0.08, "p(alive discharge)", "#2a9d8f")
    draw_box(ax, 0.84, 0.20, 0.12, 0.08, "p(continued stay)", "#777777")
    save_fig(fig, png, pdf)
    return record("Figure 1", "研究流程与双锚点竞争风险框架", True, "mechanism/workflow schematic", "Locked cohort/model design documents", png, pdf)


def create_figure1b() -> dict[str, Any]:
    png = FIG_DIR / "Figure1B_double_anchor_patient_timeline.png"
    pdf = FIG_DIR / "Figure1B_double_anchor_patient_timeline.pdf"
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    patients = ["Patient A", "Patient B", "Patient C"]
    icu = np.array([0, 0, 0])
    sepsis = np.array([2, 18, 34])
    pred = np.array([26, 42, 58])
    y = np.arange(len(patients))[::-1]
    for ax, title in zip(axes, ["Single ICU-anchor view", "Dual-anchor view"]):
        ax.set_xlim(-4, 64)
        ax.set_ylim(-0.8, 2.8)
        ax.set_xlabel("Hours on patient trajectory")
        ax.set_yticks(y)
        ax.set_yticklabels(patients)
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
        ax.grid(axis="x", alpha=0.2)
    for i in range(3):
        axes[0].hlines(y[i], icu[i], pred[i] + 6, color="#666", lw=2)
        axes[0].scatter(icu[i], y[i], s=110, color=PALETTE["p15"], label="t_ICU" if i == 0 else "")
        axes[0].scatter(sepsis[i], y[i], s=110, color=PALETTE["m1"], label="t_sepsis" if i == 0 else "")
        axes[0].scatter(pred[i], y[i], s=90, color="#111", label="t_pred" if i == 0 else "")
        axes[0].annotate("", xy=(sepsis[i], y[i] + 0.18), xytext=(icu[i], y[i] + 0.18), arrowprops=dict(arrowstyle="<->", color=PALETTE["m1"], lw=1.2))
        axes[0].text((sepsis[i] + icu[i]) / 2, y[i] + 0.28, "dispersed t_sepsis", ha="center", fontsize=8, color=PALETTE["m1"])

        axes[1].hlines(y[i], icu[i], pred[i] + 6, color="#666", lw=2)
        axes[1].scatter(icu[i], y[i], s=110, color=PALETTE["p15"])
        axes[1].scatter(sepsis[i], y[i], s=110, color=PALETTE["m1"])
        axes[1].scatter(pred[i], y[i], s=90, color="#111")
        axes[1].annotate("", xy=(pred[i], y[i] + 0.18), xytext=(icu[i], y[i] + 0.18), arrowprops=dict(arrowstyle="<->", color=PALETTE["p15"], lw=1.2))
        axes[1].annotate("", xy=(pred[i], y[i] - 0.18), xytext=(sepsis[i], y[i] - 0.18), arrowprops=dict(arrowstyle="<->", color=PALETTE["m1"], lw=1.2))
        axes[1].text((pred[i] + icu[i]) / 2, y[i] + 0.28, "Δt_ICU", ha="center", fontsize=8, color=PALETTE["p15"])
        axes[1].text((pred[i] + sepsis[i]) / 2, y[i] - 0.36, "Δt_sepsis", ha="center", fontsize=8, color=PALETTE["m1"])
    axes[0].legend(frameon=False, loc="lower right")
    fig.suptitle("Figure 1B. Patient trajectory and dual-anchor temporal alignment", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, png, pdf)
    return record("Figure 1B", "患者轨迹与双锚点时间对齐", True, "mechanism/timeline schematic", "Dual-anchor design; illustrative only", png, pdf)


def performance_table() -> pd.DataFrame:
    main = read_csv(MAIN_CI)
    keep = [
        "M1_internal_rich_reference_model",
        "MT3_Post_METRE_transport_reference_model",
        "P15_clinically_parsimonious_transport_model",
        "C1_dynamic_SOFA_clinical_comparator",
    ]
    main = main[main["model_name"].isin(keep)].copy()
    clinical = read_csv(CLINICAL_CI)
    clinical = clinical[clinical["model_name"].isin(
        [
            "P12_true_trained_clinical_landing_model",
            "P10_true_trained_ultra_minimal_sensitivity_model",
        ]
    )].copy()
    for col in ["MIMIC_AUROC", "MIMIC_AUPRC", "MIMIC_Brier"]:
        if col not in clinical.columns:
            clinical[col] = np.nan
    clinical["model_role"] = clinical.get("recommended_role", "clinical implementation sensitivity")
    out = pd.concat([main, clinical], ignore_index=True, sort=False)
    order = [
        "M1_internal_rich_reference_model",
        "MT3_Post_METRE_transport_reference_model",
        "P15_clinically_parsimonious_transport_model",
        "P12_true_trained_clinical_landing_model",
        "P10_true_trained_ultra_minimal_sensitivity_model",
        "C1_dynamic_SOFA_clinical_comparator",
    ]
    out["order"] = out["model_name"].map({m: i for i, m in enumerate(order)})
    return out.sort_values("order").reset_index(drop=True)


def create_figure2() -> list[dict[str, Any]]:
    df = performance_table()
    records = []
    for metric, label, outstem in [
        ("AUROC", "AUROC", "Figure2_transportability_slopegraph_AUROC"),
        ("AUPRC", "AUPRC", "Figure2_transportability_slopegraph_AUPRC"),
    ]:
        png = FIG_DIR / f"{outstem}.png"
        pdf = FIG_DIR / f"{outstem}.pdf"
        fig, ax = plt.subplots(figsize=(8.6, 5.2))
        ax.set_xlim(-0.2, 1.2)
        vals = []
        label_sep = 0.006 if metric == "AUPRC" else 0.008
        left_label_offsets = {
            "MT3_Post_METRE_transport_reference_model": 1.0,
            "P15_clinically_parsimonious_transport_model": -1.0,
        }
        right_label_offsets = {
            "MT3_Post_METRE_transport_reference_model": 1.4,
            "P15_clinically_parsimonious_transport_model": 0.45,
            "P12_true_trained_clinical_landing_model": -0.65,
            "P10_true_trained_ultra_minimal_sensitivity_model": -1.45,
            "C1_dynamic_SOFA_clinical_comparator": 1.5,
            "M1_internal_rich_reference_model": -1.7,
        }
        label_box = {"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.4}
        for _, row in df.iterrows():
            mimic = row.get(f"MIMIC_{metric}", np.nan)
            eicu = row.get(f"eICU_{metric}", np.nan)
            color = PALETTE["m1"] if "M1" in row["model_name"] else PALETTE["p15"] if "P15" in row["model_name"] else "#777777"
            if pd.notna(mimic):
                ax.plot([0, 1], [mimic, eicu], marker="o", lw=2.4, color=color, alpha=0.88)
                left_y = mimic + label_sep * left_label_offsets.get(row["model_name"], 0.0)
                ax.text(-0.035, left_y, f"{MODEL_LABELS.get(row['model_name'], row['model_name'])} {mimic:.3f}", ha="right", va="center", fontsize=8, bbox=label_box)
            else:
                ax.scatter([1], [eicu], color=color, s=45)
            right_y = eicu + label_sep * right_label_offsets.get(row["model_name"], 0.0)
            ax.text(1.03, right_y, f"{MODEL_LABELS.get(row['model_name'], row['model_name'])} {eicu:.3f}", ha="left", va="center", fontsize=8, bbox=label_box)
            vals.extend([v for v in [mimic, eicu] if pd.notna(v)])
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["MIMIC-IV internal", "eICU external"])
        ax.set_ylabel(label)
        ax.set_title(f"Figure 2. Transportability slopegraph ({label})", loc="left", fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.22)
        if vals:
            ax.set_ylim(max(0, min(vals) - 0.08), min(1.05, max(vals) + 0.08))
        ax.set_xlim(-0.20, 1.22)
        ax.text(0.5, ax.get_ylim()[0] + 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0]), "Steeper downward lines indicate weaker external transportability.", ha="center", fontsize=9, color="#555555")
        save_fig(fig, png, pdf)
        records.append(record(f"Figure 2 {label}", f"模型从 MIMIC-IV 到 eICU 的外部迁移轨迹 ({label})", True, "true results plot", str(MAIN_CI) + "; " + str(CLINICAL_CI), png, pdf))
    return records


def create_figure3() -> dict[str, Any]:
    png = FIG_DIR / "Figure3_eICU_smooth_calibration_curve.png"
    pdf = FIG_DIR / "Figure3_eICU_smooth_calibration_curve.pdf"
    p15 = p15_external_predictions()
    m1 = normalize_pred_file(M1_EICU_PRED, "M1")
    c1 = pd.concat(
        [
            calibration_curve_data(p15, "P15", n_bins=20),
            calibration_curve_data(m1, "70-feature M1", n_bins=20),
        ],
        ignore_index=True,
    )
    c1.to_csv(FIG_DIR / "Figure3_eICU_smooth_calibration_curve_data.csv", index=False, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    max_x = max(0.35, float(c1["mean_predicted_risk"].quantile(0.995)) * 1.08)
    ax.plot([0, max_x], [0, max_x], ls="--", color="#777777", lw=1.5, label="Ideal calibration")
    for name, color, ls in [("P15", PALETTE["p15"], "-"), ("70-feature M1", PALETTE["m1"], "--")]:
        d = c1[c1["model_name"] == name].sort_values("mean_predicted_risk")
        ax.plot(d["mean_predicted_risk"], d["observed_death_rate"], marker="o", color=color, lw=2.2, ls=ls, label=name)
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, max_x)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_xlabel("Predicted 24h ICU death risk")
    ax.set_ylabel("Observed 24h ICU death frequency")
    ax.set_title("Figure 3. eICU calibration from prediction-level data", loc="left", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(alpha=0.20)
    save_fig(fig, png, pdf)
    return record("Figure 3", "eICU 外部验证中的平滑校准曲线", True, "true prediction-level reliability diagram", f"{MODEL_READY_EXTERNAL}; {M1_EICU_PRED}", png, pdf)


def create_figure4() -> dict[str, Any]:
    png = FIG_DIR / "Figure4_eICU_decision_curve_analysis.png"
    pdf = FIG_DIR / "Figure4_eICU_decision_curve_analysis.pdf"
    dca = read_csv(DCA_SUMMARY)
    dca = dca[dca["dataset_name"] == "eicu_external"].copy()
    keep = [
        "P15_clinically_parsimonious_transport_model",
        "P12_true_trained_clinical_landing_model",
        "P10_true_trained_ultra_minimal_sensitivity_model",
    ]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    color_map = {
        keep[0]: PALETTE["p15"],
        keep[1]: PALETTE["p12"],
        keep[2]: PALETTE["p10"],
    }
    for model in keep:
        sub = dca[dca["model_name"] == model].sort_values("threshold")
        if sub.empty:
            continue
        lw = 2.8 if model == keep[0] else 1.8
        ax.plot(sub["threshold"], sub["net_benefit"], marker="o", lw=lw, color=color_map[model], label=MODEL_LABELS.get(model, model))
    ref = dca[dca["model_name"] == keep[0]].sort_values("threshold")
    ax.plot(ref["threshold"], ref["treat_all_net_benefit"], color="#777777", ls="--", label="Treat all")
    ax.axhline(0, color="#111111", lw=1.0, ls=":", label="Treat none")
    ax.set_xlabel("Risk threshold")
    ax.set_ylabel("Net benefit")
    ax.set_title("Figure 4. eICU decision curve analysis", loc="left", fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(alpha=0.22)
    save_fig(fig, png, pdf)
    return record("Figure 4", "eICU 外部验证中的决策曲线分析", True, "true DCA results plot", str(DCA_SUMMARY), png, pdf)


def create_figure5() -> dict[str, Any]:
    png = FIG_DIR / "Figure5_subphenotype_robustness_eICU.png"
    pdf = FIG_DIR / "Figure5_subphenotype_robustness_eICU.pdf"
    df = read_csv(SUBPHENO_CI)
    df = df[
        (df["model_name"] == "P15_clinically_parsimonious_transport_model")
        & (df["dataset_name"] == "eicu_external")
        & (df["status"] == "ok")
    ].copy()
    df.to_csv(FIG_DIR / "Figure5_subphenotype_robustness_eICU_data.csv", index=False, encoding="utf-8-sig")
    metrics = [
        ("AUROC", "AUROC", PALETTE["p15"]),
        ("AUPRC", "AUPRC", "#2a9d8f"),
        ("Brier", "Brier", "#8d6e63"),
        ("calibration_slope", "Calibration slope", PALETTE["m1"]),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.8), sharex=True)
    phenos = sorted(df["phenotype_label"].unique())
    x = np.arange(len(phenos))
    for ax, (col, title, color) in zip(axes.ravel(), metrics):
        vals = [float(df.loc[df["phenotype_label"] == p, col].iloc[0]) for p in phenos]
        ax.bar(x, vals, color=color, alpha=0.82)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(phenos, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.18)
        if col == "calibration_slope":
            ax.axhline(1, color="#333333", ls="--", lw=1)
    fig.suptitle("Figure 5. P15 external robustness across eICU phenotypes", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, png, pdf)
    return record("Figure 5", "P15 在 eICU 不同临床表型中的外部验证稳健性", True, "true phenotype-stratified bootstrap result plot", str(SUBPHENO_CI), png, pdf)


def safe_read_feature_table(path: Path) -> pd.DataFrame:
    # Files are UTF-8 with BOM but some terminals display Chinese incorrectly; read with utf-8-sig.
    return pd.read_csv(path, encoding="utf-8-sig")


def deployment_difficulty_map() -> dict[str, float]:
    return {"低": 1.0, "低到中": 2.0, "中": 3.0, "中到高": 4.0, "高": 5.0}


def create_figure6() -> dict[str, Any]:
    png = FIG_DIR / "Figure6_P15_feature_importance_vs_deployment_difficulty.png"
    pdf = FIG_DIR / "Figure6_P15_feature_importance_vs_deployment_difficulty.pdf"
    with P15_MODEL.open("rb") as f:
        bundle = pickle.load(f)
    features = list(bundle["features"])
    classes = [str(x) for x in bundle["classes"]]
    death_idx = classes.index(DEATH_LABEL)
    clf = bundle["pipeline"].named_steps["classifier"] if "classifier" in bundle["pipeline"].named_steps else bundle["pipeline"].steps[-1][1]
    coefs = clf.coef_[death_idx]
    imp = pd.DataFrame({"internal_feature": features, "death_class_coefficient": coefs})
    imp["importance_abs_coefficient"] = imp["death_class_coefficient"].abs()
    alias = {
        "hr_latest_value": "heart_rate_latest_value",
        "rr_latest_value": "respiratory_rate_latest_value",
    }
    imp["feature_name"] = imp["internal_feature"].map(alias).fillna(imp["internal_feature"])

    source = safe_read_feature_table(FEATURE_SOURCE)
    missing = safe_read_feature_table(FEATURE_MISSING)
    source_cols = {c: c for c in source.columns}
    # Handle expected Chinese column names from the generated audit.
    feature_col = "英文变量名" if "英文变量名" in source.columns else source.columns[2]
    cat_col = "特征类别" if "特征类别" in source.columns else source.columns[0]
    diff_col = "部署难度" if "部署难度" in source.columns else source.columns[6]
    source_sub = source[[feature_col, cat_col, diff_col]].rename(columns={feature_col: "feature_name", cat_col: "feature_category", diff_col: "deployment_difficulty"})
    missing_feature_col = "P15 变量" if "P15 变量" in missing.columns else missing.columns[0]
    eicu_missing_col = "eICU 缺失率" if "eICU 缺失率" in missing.columns else missing.columns[2]
    missing_sub = missing[[missing_feature_col, eicu_missing_col]].rename(columns={missing_feature_col: "feature_name", eicu_missing_col: "eicu_missing_rate"})
    plot = imp.merge(source_sub, on="feature_name", how="left").merge(missing_sub, on="feature_name", how="left")
    plot["deployment_difficulty_score"] = plot["deployment_difficulty"].map(deployment_difficulty_map()).fillna(3)
    plot["eicu_missing_rate"] = pd.to_numeric(plot["eicu_missing_rate"], errors="coerce").fillna(0)
    label_alias = {
        "hours_since_icu_admission": "hours_since_ICU",
        "hours_from_anchor": "hours_from_anchor",
        "is_sepsis_on_admission": "sepsis_on_admit",
        "heart_rate_latest_value": "heart_rate",
        "respiratory_rate_latest_value": "resp_rate",
        "spo2_latest_value": "SpO2",
        "creatinine_latest_value": "creatinine",
        "bun_latest_value": "BUN",
        "platelet_latest_value": "platelet",
        "wbc_latest_value": "WBC",
        "shared_support_intensity_proxy": "shared_proxy",
        "support_hemodynamic_component": "hemodynamic",
        "support_lactate_component": "lactate",
        "support_renal_component": "renal_support",
        "support_respiratory_component": "resp_support",
    }
    plot["plot_label"] = plot["feature_name"].map(label_alias).fillna(plot["feature_name"].str.replace("_latest_value", "", regex=False))
    plot.to_csv(TABLE_DIR / "Figure6_P15_importance_deployability_plot_data.csv", index=False, encoding="utf-8-sig")

    colors = {
        "时间锚点": "#457b9d",
        "疾病阶段": "#1d3557",
        "床旁生命体征": "#2a9d8f",
        "常规实验室": "#e9c46a",
        "支持强度代理变量": "#e76f51",
    }
    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    for cat, sub in plot.groupby("feature_category", dropna=False):
        ax.scatter(
            sub["deployment_difficulty_score"],
            sub["importance_abs_coefficient"],
            s=80 + sub["eicu_missing_rate"].astype(float) * 2200,
            alpha=0.78,
            label=str(cat),
            color=colors.get(str(cat), "#999999"),
            edgecolor="white",
            linewidth=0.8,
        )
        for _, row in sub.iterrows():
            ax.text(row["deployment_difficulty_score"] + 0.035, row["importance_abs_coefficient"], row["plot_label"], fontsize=7)
    ax.axvspan(0.5, 2.5, ymin=0.55, ymax=1.0, color=PALETTE["gold"], alpha=0.12)
    ax.text(0.65, plot["importance_abs_coefficient"].max() * 0.95, "Golden quadrant:\nhigh importance,\nlow burden", fontsize=9, color="#7a5c00", va="top")
    ax.set_xlabel("Deployment difficulty score (low to high)")
    ax.set_ylabel("Feature importance |death-class coefficient|")
    ax.set_title("Figure 6. P15 feature importance vs deployment difficulty", loc="left", fontsize=13, fontweight="bold")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(["Low", "Low-mid", "Mid", "Mid-high", "High"])
    ax.grid(alpha=0.18)
    ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.subplots_adjust(right=0.78)
    save_fig(fig, png, pdf)

    audit = """# Figure 6 SHAP / feature-importance generation audit

Figure 6 was generated from true frozen P15 model coefficients, not from simulated SHAP values.

- Frozen model object: `D:\\try\\parsimonious_features\\model_P15_minimal_bedside_model.pkl`
- Importance definition: absolute death-class coefficient from the multinomial logistic regression classifier.
- Deployment difficulty source: `results_final/tables/P15_feature_source_availability_deployment_table.csv`
- Bubble-size source: eICU missingness from `results_final/tables/P15_feature_missingness_audit.csv`
- Caution: coefficient importance is not a causal effect and does not quantify treatment benefit.
"""
    (TEXT_DIR / "Figure6_SHAP_generation_audit.md").write_text(audit, encoding="utf-8")
    return record("Figure 6", "P15 特征重要性与部署难度四象限图", True, "true frozen-model coefficient importance plot", f"{P15_MODEL}; {FEATURE_SOURCE}; {FEATURE_MISSING}", png, pdf)


def create_supplementary_s1() -> dict[str, Any]:
    png = FIG_DIR / "Supplementary_Figure_S1_P15_threshold_operational_performance.png"
    pdf = FIG_DIR / "Supplementary_Figure_S1_P15_threshold_operational_performance.pdf"
    df = read_csv(THRESHOLD_PERF)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.0))
    x = df["threshold"].astype(float)
    axes[0].plot(x, df["sensitivity_recall"].astype(float), marker="o", color=PALETTE["p15"], label="Sensitivity / recall")
    axes[0].plot(x, df["PPV"].astype(float), marker="o", color=PALETTE["m1"], label="PPV")
    axes[0].plot(x, df["screen_positive_proportion"].astype(float), marker="o", color=PALETTE["green"], label="Screen-positive proportion")
    axes[0].set_xlabel("Risk threshold")
    axes[0].set_ylabel("Metric value")
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.18)
    axes[1].plot(x, df["net_benefit"].astype(float), marker="o", color=PALETTE["p15"], label="P15 net benefit")
    axes[1].plot(x, df["treat_all_net_benefit"].astype(float), marker="o", color="#777777", ls="--", label="Treat all")
    axes[1].axhline(0, color="#111111", ls=":", label="Treat none")
    axes[1].set_xlabel("Risk threshold")
    axes[1].set_ylabel("Net benefit")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.18)
    fig.suptitle("Supplementary Figure S1. P15 threshold-specific operational performance in eICU", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, png, pdf)
    return record("Supplementary Figure S1", "P15 在 eICU 外部验证中的阈值特异性操作性能", True, "true threshold-specific results plot", str(THRESHOLD_PERF), png, pdf)


def create_additional_figures() -> list[dict[str, Any]]:
    df = performance_table()
    records = []
    png = FIG_DIR / "Additional_Figure_A_eICU_external_performance_overview.png"
    pdf = FIG_DIR / "Additional_Figure_A_eICU_external_performance_overview.pdf"
    metrics = [("eICU_AUROC", "AUROC"), ("eICU_AUPRC", "AUPRC"), ("eICU_calibration_slope", "Calibration slope")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharex=True)
    labels = [MODEL_LABELS.get(m, m) for m in df["model_name"]]
    x = np.arange(len(df))
    for ax, (col, title) in zip(axes, metrics):
        ax.bar(x, df[col].astype(float), color=[PALETTE["m1"] if "M1" in m else PALETTE["p15"] if "P15" in m else "#8aa" for m in df["model_name"]])
        ax.set_title(title, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.18)
        if col == "eICU_calibration_slope":
            ax.axhline(1, color="#333", ls="--", lw=1)
    fig.suptitle("Additional Figure A. eICU external performance overview", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, png, pdf)
    records.append(record("Additional Figure A", "eICU 外部验证表现总览", True, "true results summary plot", str(MAIN_CI) + "; " + str(CLINICAL_CI), png, pdf))

    png = FIG_DIR / "Additional_Figure_B_eICU_calibration_slope_forest.png"
    pdf = FIG_DIR / "Additional_Figure_B_eICU_calibration_slope_forest.pdf"
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    sub = df.dropna(subset=["eICU_calibration_slope"]).copy()
    y = np.arange(len(sub))[::-1]
    ax.errorbar(sub["eICU_calibration_slope"], y, fmt="o", color=PALETTE["p15"], capsize=3)
    # Draw CIs where available.
    for yi, (_, row) in zip(y, sub.iterrows()):
        ci = row.get("eICU_calibration_slope_95CI", np.nan)
        lo, hi = split_ci(ci)
        if pd.notna(lo):
            ax.plot([lo, hi], [yi, yi], color="#555", lw=1.5)
    ax.axvline(1, color="#333", ls="--", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([MODEL_LABELS.get(m, m) for m in sub["model_name"]])
    ax.set_xlabel("eICU calibration slope")
    ax.set_title("Additional Figure B. External calibration slope", loc="left", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.18)
    save_fig(fig, png, pdf)
    records.append(record("Additional Figure B", "eICU 外部校准斜率森林图", True, "true calibration-slope forest plot", str(MAIN_CI) + "; " + str(CLINICAL_CI), png, pdf))
    return records


def record(
    figure_id: str,
    figure_name: str,
    generated: bool,
    figure_type: str,
    data_source: str,
    png: Path | None,
    pdf: Path | None,
    warning: str = "",
) -> dict[str, Any]:
    return {
        "figure_id": figure_id,
        "figure_name": figure_name,
        "generated": generated,
        "inserted_into_word": False,
        "figure_type": figure_type,
        "data_source": data_source,
        "script_used": str(SCRIPT_PATH.relative_to(REPO)),
        "output_png": str(png.relative_to(REPO)) if png else "",
        "output_pdf": str(pdf.relative_to(REPO)) if pdf else "",
        "warning": warning,
    }


def write_legends(records: list[dict[str, Any]]) -> None:
    zh = [
        "# 正式中文图注",
        "",
        "**图文摘要。P15 通过双锚点、竞争风险和临床简约变量避免了高维模型的外部校准崩溃。** 左侧为传统高维路径：单一 ICU 入室锚点、非竞争风险处理和 70 特征输入在 eICU 外部验证中校准斜率降至 0.0728。右侧为 P15 路径：t_ICU 与 t_sepsis 双锚点、ICU 死亡与活体出院竞争结局、15 个临床可解释变量，在 eICU 中保持 AUROC 0.8103、AUPRC 0.1892 和校准斜率 1.0031。",
        "",
        "**图 1。研究流程将数据库来源、双锚点动态预测和竞争风险结局组织到同一框架内。** MIMIC-IV 用于开发/内部验证，eICU 用于外部验证；模型比较包括 70 特征内部 rich 参考模型、动态 SOFA、P15 以及 P12/P10 实施敏感性模型。",
        "",
        "**图 1B。双锚点时间对齐将 ICU 流程时间与脓毒症疾病时间同时显式化。** 传统单锚点视角下 t_sepsis 在患者之间分散；双锚点框架同时保留 Δt_ICU 和 Δt_sepsis，减少病程阶段混杂。",
        "",
        "**图 2。高维内部最优不等于外部可移植，P15 的外部迁移更稳定。** 70 特征 M1 在 MIMIC-IV 内部 AUROC/AUPRC 较高，但到 eICU 后明显下跌；P15 在 eICU 中保持接近 MT3 的外部性能和更简约的变量结构。",
        "",
        "**图 3。P15 在 eICU 的预测风险更接近实际 24 小时 ICU 死亡频率。** 蓝线表示 P15，红色虚线表示 70 特征 M1，灰色虚线为理想 45 度校准线。校准偏离是临床安全性问题，而不仅是统计拟合问题。",
        "",
        "**图 4。P15 的 DCA 支持低阈值风险分层，但不支持自动干预触发。** 低风险阈值下 P15 可获得正净获益；较高阈值下净获益转负，提示阈值选择必须结合临床资源和假阳性负担。",
        "",
        "**图 5。P15 在 eICU 表型分层中总体保持判别能力，但不同表型的校准压力不同。** 分层结果用于稳健性和再校准线索，不应被过度解释为治疗分型。",
        "",
        "**图 6。P15 特征重要性与部署难度显示了模型可解释性和工程负担之间的权衡。** 纵轴为冻结 P15 death-class 系数绝对值，横轴为部署难度；该图用于透明度和部署审计，feature importance 不代表因果效应。",
        "",
        "**补充图 S1。P15 的召回率、PPV 和净获益随阈值变化呈现明显操作性权衡。** 召回率是阈值特异性指标，不能脱离阈值单独解释；该图仅用于补充操作性能说明。",
    ]
    en = [
        "# Final English Figure Legends",
        "",
        "**Graphical Abstract. P15 avoids the external calibration collapse seen in the high-dimensional pathway by combining dual anchoring, competing-risk framing, and clinically parsimonious variables.** The left panel summarizes the traditional high-dimensional pathway, whereas the right panel summarizes the P15 pathway and its eICU performance.",
        "",
        "**Figure 1. The study workflow integrates data sources, dual-anchor dynamic prediction, and competing-risk outcomes in one framework.** MIMIC-IV was used for development/internal validation and eICU for external validation.",
        "",
        "**Figure 1B. Dual-anchor temporal alignment explicitly separates ICU process time from sepsis disease time.** This representation preserves both time since ICU admission and time since sepsis onset.",
        "",
        "**Figure 2. Strong internal discrimination did not guarantee external transportability, whereas P15 remained externally stable.** The high-dimensional M1 model dropped sharply from MIMIC-IV to eICU, while P15 maintained transportable performance.",
        "",
        "**Figure 3. P15 showed substantially better external calibration against observed 24-hour ICU death frequency.** The blue line represents P15, the red dashed line represents the 70-feature model, and the gray dashed line denotes ideal calibration.",
        "",
        "**Figure 4. P15 supported low-threshold risk stratification in DCA but should not be interpreted as an automatic intervention trigger.** Net benefit decreased at higher thresholds.",
        "",
        "**Figure 5. P15 retained phenotype-stratified discrimination in eICU, with residual calibration pressure varying by phenotype.** These results support audit and recalibration, not treatment-subtype claims.",
        "",
        "**Figure 6. P15 feature importance versus deployment difficulty shows the trade-off between transparency and implementation burden.** Importance is based on the frozen model death-class coefficients and is not causal.",
        "",
        "**Supplementary Figure S1. Threshold-specific sensitivity, PPV, and net benefit illustrate the operational trade-off for P15 in eICU.** Recall is threshold-dependent and is not a primary performance metric.",
    ]
    (TEXT_DIR / "final_figure_legends_zh.md").write_text("\n".join(zh) + "\n", encoding="utf-8")
    (TEXT_DIR / "final_figure_legends_en.md").write_text("\n".join(en) + "\n", encoding="utf-8")


def write_intext_refs() -> None:
    text = """# 正文图表引用段落

图文摘要应首先引导读者关注两条路径的核心分歧：红色高维路径在外部校准上崩溃，而蓝色 P15 路径通过双锚点、竞争风险和 15 个临床变量保持外部校准。

在方法部分引用图 1 时，应强调 MIMIC-IV 与 eICU 的角色分离，以及 P15、70 特征 M1 和动态 SOFA 处在同一外部验证框架中。引用图 1B 时，应引导读者看同一预测时点同时对应 Δt_ICU 和 Δt_sepsis，而不是只按 ICU 入室时间粗糙对齐。

在结果部分引用图 2 时，应明确提示读者观察红色 70 特征模型线条从 MIMIC-IV 到 eICU 的下坠，以及 P15 线条相对平稳的对比；这比单独报告内部 AUROC 更能说明外部可移植性。

在结果部分引用图 3 时，应引导读者比较蓝线贴近 45 度线与红线偏离的差异。这里的重点不是曲线是否美观，而是外部校准是否足以支持临床风险解释。

在临床效用部分引用图 4 时，应强调低阈值区间的正净获益与高阈值区间转负的边界，避免把 DCA 解读成自动干预触发器。

在稳健性部分引用图 5 时，应强调 P15 在不同表型中的 AUROC 保持情况，同时指出 Phenotype 3 或部分表型的校准压力可作为本地再校准线索。

在部署讨论中引用图 6 时，应引导读者关注左上角高重要性、低部署难度的黄金象限，以及支持强度 proxy 的较高工程负担。该图用于透明度和部署审计，不代表因果效应。

在补充材料中引用补充图 S1 时，应明确召回率依赖阈值；低阈值提高敏感性，但 PPV 低、筛查阳性比例高，因此只能作为操作性补充指标。
"""
    (TEXT_DIR / "final_figure_intext_references_zh.md").write_text(text, encoding="utf-8")


def make_figures_pdf(records: list[dict[str, Any]]) -> Path:
    out = FIG_DIR / "sepsis_complete_figures_pack.pdf"
    with PdfPages(out) as pdf:
        for rec in records:
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis("off")
            ax.text(0.05, 0.96, f"{rec['figure_id']}. {rec['figure_name']}", fontsize=14, fontweight="bold", va="top")
            if rec["generated"] and rec["output_png"]:
                img = plt.imread(REPO / rec["output_png"])
                ax.imshow(img, extent=(0.05, 0.95, 0.20, 0.88), aspect="auto")
                note = "Data source: " + str(rec["data_source"])[:150]
            else:
                note = f"{rec['figure_id']} not generated. Reason: {rec.get('warning', 'source unavailable')}"
            ax.text(0.05, 0.11, note, fontsize=9, va="top", wrap=True)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    return out


def try_insert_word(records: list[dict[str, Any]]) -> tuple[bool, str]:
    # The project currently contains no docx; keep this function explicit for auditability.
    candidates = [
        "sepsis_paper_chinese_final_figures_restored_cleaned.docx",
        "sepsis_paper_chinese_final_figures_restored.docx",
        "sepsis_paper_chinese_final_visual_legend_optimized.docx",
        "sepsis_paper_chinese_final_clinical_narrative_submission.docx",
    ]
    found = []
    for base in [ROOT, REPO]:
        for name in candidates:
            found.extend(base.rglob(name))
        found.extend(base.rglob("manuscript*.docx"))
        found.extend(base.rglob("paper*.docx"))
    if not found:
        return False, "Word source unavailable: no .docx manuscript found under D:\\try or the share repository."
    return False, "Word source found but insertion not implemented in this run."


def write_audit(records: list[dict[str, Any]], pdf_pack: Path, word_inserted: bool, word_note: str, warnings: list[str]) -> None:
    audit_df = pd.DataFrame(records)
    audit_df.to_csv(TABLE_DIR / "final_figure_completion_audit.csv", index=False, encoding="utf-8-sig")
    generated_missing = [r["figure_id"] for r in records if not r["generated"]]
    md = [
        "# Final Figure Completion Audit",
        "",
        f"- Complete figures PDF: `{pdf_pack}`",
        f"- Word insertion: {word_inserted}. {word_note}",
        f"- Validation warnings: {warnings if warnings else '[]'}",
        "",
        "## Figure status",
        "",
    ]
    for rec in records:
        md.append(
            f"- {rec['figure_id']}: generated={rec['generated']}; type={rec['figure_type']}; source={rec['data_source']}; png=`{rec['output_png']}`; pdf=`{rec['output_pdf']}`; warning={rec['warning'] or 'none'}"
        )
    md.extend(
        [
            "",
            "## Quality checks",
            "",
            "- Mechanism figures are limited to the Graphical Abstract, Figure 1, and Figure 1B.",
            "- Figures 2-5 and Supplementary Figure S1 use true locked result files or prediction-level data.",
            "- Figure 6 uses true frozen P15 model coefficients, not synthetic SHAP values.",
            "- No model retraining was performed.",
            "- No frozen model point estimates were modified.",
            "- eICU was not used for tuning.",
            "- DCA and threshold figures are clinical utility estimates, not automatic intervention triggers.",
        ]
    )
    if generated_missing:
        md.append(f"- Missing figures: {', '.join(generated_missing)}")
    (TEXT_DIR / "final_figure_completion_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    records.append(create_graphical_abstract())
    records.append(create_figure1())
    records.append(create_figure1b())
    records.extend(create_figure2())
    records.append(create_figure3())
    records.append(create_figure4())
    records.append(create_figure5())
    try:
        records.append(create_figure6())
    except Exception as exc:
        reason = f"Figure 6 not generated from true feature importance: {exc}"
        (TEXT_DIR / "Figure6_not_generated_reason.md").write_text(reason + "\n", encoding="utf-8")
        warnings.append(reason)
        records.append(record("Figure 6", "P15 特征重要性与部署难度四象限图", False, "true feature-importance plot", "source unavailable or computation failed", None, None, reason))
    records.append(create_supplementary_s1())
    records.extend(create_additional_figures())
    write_legends(records)
    write_intext_refs()
    pdf_pack = make_figures_pdf(records)
    word_inserted, word_note = try_insert_word(records)
    write_audit(records, pdf_pack, word_inserted, word_note, warnings)
    summary = {
        "records": records,
        "complete_figures_pdf": str(pdf_pack.relative_to(REPO)),
        "word_inserted": word_inserted,
        "word_note": word_note,
        "validation_warnings": warnings,
    }
    (TEXT_DIR / "final_figure_generation_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
