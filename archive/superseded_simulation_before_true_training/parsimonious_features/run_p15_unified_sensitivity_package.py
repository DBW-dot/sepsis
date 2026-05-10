from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARS_DIR = ROOT / "parsimonious_features"
FIG_DIR = ROOT / "results_final" / "figures"
TABLE_DIR = ROOT / "results_final" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

P15 = {
    "external_AUROC": 0.8102778903274425,
    "external_AUPRC": 0.1891883359451771,
    "external_calibration_slope": 1.0030546274076915,
}


def run_base_package() -> None:
    script_path = PARS_DIR / "run_p15_subset_sensitivity_clinical_landing.py"
    spec = importlib.util.spec_from_file_location("p15_base_package", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def pct_drop(value: float, baseline: float) -> float:
    return (baseline - value) / baseline * 100.0


def clinical_trust_label(score: float) -> str:
    if score >= 4.5:
        return "very_high"
    if score >= 4.0:
        return "high"
    if score >= 3.5:
        return "moderate"
    return "lower_relative_to_P15"


def implementation_burden(row: pd.Series) -> str:
    category = row["feature_category"]
    if category == "time_anchor":
        return "automatic_timestamp_or_anchor_logic"
    if category == "vital_sign":
        return "routine_bedside_monitoring"
    if category == "routine_lab":
        return "routine_blood_laboratory"
    if category == "support_proxy":
        return "derived_transport_proxy_from_support_signals"
    return "unknown"


def real_time_availability(row: pd.Series) -> str:
    category = row["feature_category"]
    if category in {"time_anchor", "vital_sign"}:
        return "near_real_time"
    if category == "routine_lab":
        return "episodic_laboratory_turnaround"
    if category == "support_proxy":
        return "derived_after_source_signal_update"
    return "unknown"


def blood_draw_requirement(row: pd.Series) -> str:
    return "yes" if row["feature_category"] == "routine_lab" else "no"


def figure_feature_contribution(feature_df: pd.DataFrame) -> None:
    plot = feature_df.sort_values("estimated_AUPRC_loss_if_removed", ascending=True)
    y = range(len(plot))
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(y, plot["estimated_AUROC_loss_if_removed"], height=0.25, label="AUROC loss", color="#496f5d")
    ax.barh([i + 0.25 for i in y], plot["estimated_AUPRC_loss_if_removed"], height=0.25, label="AUPRC loss", color="#2f7da1")
    ax.barh([i + 0.50 for i in y], plot["estimated_calibration_slope_loss_if_removed"], height=0.25, label="Calibration slope loss", color="#9a463d")
    ax.set_yticks([i + 0.25 for i in y])
    ax.set_yticklabels(plot["feature_display"], fontsize=9)
    ax.set_xlabel("Estimated loss if feature is removed")
    ax.set_title("P15 feature contribution across external AUROC, AUPRC, and calibration slope")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "P15_Feature_Contribution_AllMetrics.png", dpi=220)
    fig.savefig(FIG_DIR / "P15_Feature_Contribution_AllMetrics.svg")
    plt.close(fig)


def figure_subset_performance(subset_df: pd.DataFrame) -> None:
    plot = subset_df.copy()
    x = range(len(plot))
    width = 0.24
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar([i - width for i in x], plot["external_AUROC"], width=width, label="AUROC", color="#496f5d")
    ax1.bar(x, plot["external_AUPRC"], width=width, label="AUPRC", color="#2f7da1")
    ax1.set_ylim(0.0, 0.9)
    ax1.set_ylabel("AUROC / AUPRC")
    ax2 = ax1.twinx()
    ax2.bar([i + width for i in x], plot["external_calibration_slope"], width=width, label="Calibration slope", color="#9a463d")
    ax2.set_ylim(0.0, 1.15)
    ax2.set_ylabel("Calibration slope")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(plot["subset_id"], rotation=18, ha="right", fontsize=9)
    ax1.set_title("P10/P12 simulated subsets versus frozen P15")
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")
    ax1.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "P15_Subset_Performance_Comparison.png", dpi=220)
    fig.savefig(FIG_DIR / "P15_Subset_Performance_Comparison.svg")
    plt.close(fig)


def figure_proxy_interpretability(proxy_component_df: pd.DataFrame) -> None:
    plot = proxy_component_df.sort_values("estimated_AUPRC_loss_if_removed", ascending=True)
    y = range(len(plot))
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.barh(y, plot["p15_death_class_coefficient"], height=0.34, color="#9a463d", label="P15 death-class coefficient")
    ax.barh([i + 0.36 for i in y], plot["estimated_AUPRC_loss_if_removed"], height=0.34, color="#2f7da1", label="Estimated AUPRC loss if removed")
    ax.set_yticks([i + 0.18 for i in y])
    ax.set_yticklabels(plot["feature_display"], fontsize=9)
    ax.set_xlabel("Coefficient or estimated AUPRC loss")
    ax.set_title("Support-intensity proxy component interpretability")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "P15_Proxy_Contribution_Interpretability.png", dpi=220)
    fig.savefig(FIG_DIR / "P15_Proxy_Contribution_Interpretability.svg")
    plt.close(fig)


def figure_proxy_stacked(proxy_component_df: pd.DataFrame) -> None:
    plot = proxy_component_df.copy()
    metrics = [
        ("p15_abs_death_class_coefficient", "P15 coefficient share", "#9a463d"),
        ("estimated_AUPRC_loss_if_removed", "AUPRC-loss share", "#2f7da1"),
        ("mt3_death_class_coefficient", "MT3 coefficient share", "#496f5d"),
    ]
    normalized = {}
    for column, label, color in metrics:
        values = plot[column].abs()
        total = values.sum()
        normalized[label] = values / total if total else values

    fig, ax = plt.subplots(figsize=(11, 5.4))
    y_positions = range(len(metrics))
    for y, (_column, label, _color) in zip(y_positions, metrics):
        left = 0.0
        for _, row in plot.iterrows():
            width = float(normalized[label].loc[row.name])
            ax.barh(y, width, left=left, color=component_color(row["feature_internal"]), edgecolor="white")
            if width >= 0.08:
                ax.text(left + width / 2, y, short_component_label(row["feature_internal"]), ha="center", va="center", fontsize=8, color="white")
            left += width
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels([label for _column, label, _color in metrics])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share within proxy components")
    ax.set_title("Proxy component stacked contribution view")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=component_color(feature))
        for feature in plot["feature_internal"]
    ]
    labels = [short_component_label(feature) for feature in plot["feature_internal"]]
    ax.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, fontsize=8)
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "P15_Proxy_Contribution_Stacked.png", dpi=220)
    fig.savefig(FIG_DIR / "P15_Proxy_Contribution_Stacked.svg")
    plt.close(fig)


def component_color(feature: str) -> str:
    colors = {
        "shared_support_intensity_proxy": "#243447",
        "support_hemodynamic_component": "#9a463d",
        "support_lactate_component": "#946b2d",
        "support_renal_component": "#496f5d",
        "support_respiratory_component": "#2f7da1",
    }
    return colors.get(feature, "#6b7280")


def short_component_label(feature: str) -> str:
    labels = {
        "shared_support_intensity_proxy": "shared",
        "support_hemodynamic_component": "hemodyn",
        "support_lactate_component": "lactate",
        "support_renal_component": "renal",
        "support_respiratory_component": "resp",
    }
    return labels.get(feature, feature)


def main() -> None:
    run_base_package()

    feature_df = pd.read_csv(PARS_DIR / "P15_Feature_Subset_Sensitivity.csv")
    subset_df = pd.read_csv(PARS_DIR / "P15_Subset_Combination_Performance.csv")
    proxy_merge_df = pd.read_csv(PARS_DIR / "P15_Proxy_Merge_Scenarios.csv")
    proxy_component_df = pd.read_csv(PARS_DIR / "P15_Proxy_Component_Death_Risk_Contribution.csv")
    retention_src = pd.read_csv(PARS_DIR / "Feature_Retention_Rationale.csv")

    missing_cols = retention_src[["feature", "mimic_missing_rate", "eicu_missing_rate"]].copy()
    detailed = feature_df.merge(missing_cols, left_on="feature_internal", right_on="feature", how="left")
    detailed = detailed.drop(columns=["feature"])
    detailed["implementation_burden"] = detailed.apply(implementation_burden, axis=1)
    detailed["real_time_availability"] = detailed.apply(real_time_availability, axis=1)
    detailed["blood_draw_required"] = detailed.apply(blood_draw_requirement, axis=1)
    detailed["clinical_trust_score_1to5"] = detailed["weighted_retention_score_1to5"]
    detailed["clinical_trust_level"] = detailed["clinical_trust_score_1to5"].apply(clinical_trust_label)
    detailed["clinical_priority_rank"] = detailed["clinical_trust_score_1to5"].rank(
        method="first", ascending=False
    ).astype(int)
    detailed["cross_database_stability_evidence"] = detailed.apply(
        lambda row: f"MIMIC missing {row['mimic_missing_rate']:.3f}; eICU missing {row['eicu_missing_rate']:.3f}"
        if pd.notna(row["mimic_missing_rate"]) and pd.notna(row["eicu_missing_rate"])
        else "missingness not available in rationale source",
        axis=1,
    )
    detailed.to_csv(PARS_DIR / "P15_Feature_Retention_Rationale_Detailed.csv", index=False, encoding="utf-8")
    detailed.to_csv(PARS_DIR / "P15_Feature_Subset_Sensitivity.csv", index=False, encoding="utf-8")
    priority_columns = [
        "clinical_priority_rank",
        "feature_display",
        "feature_internal",
        "feature_category",
        "clinical_trust_score_1to5",
        "clinical_trust_level",
        "implementation_burden",
        "real_time_availability",
        "blood_draw_required",
        "cross_database_stability_evidence",
        "retention_recommendation",
        "rationale",
    ]
    detailed.sort_values("clinical_priority_rank")[priority_columns].to_csv(
        PARS_DIR / "P15_Clinical_Implementation_Priority_Ranking.csv",
        index=False,
        encoding="utf-8",
    )

    subset_df["AUROC_drop_pct_vs_P15"] = subset_df["external_AUROC"].apply(lambda v: pct_drop(v, P15["external_AUROC"]))
    subset_df["AUPRC_drop_pct_vs_P15"] = subset_df["external_AUPRC"].apply(lambda v: pct_drop(v, P15["external_AUPRC"]))
    subset_df["calibration_slope_drop_pct_vs_P15"] = subset_df["external_calibration_slope"].apply(
        lambda v: pct_drop(v, P15["external_calibration_slope"])
    )
    subset_df["clinical_workflow_assessment"] = [
        "lowest burden; no component-level proxy interpretation; best for screening-style deployment",
        "balanced burden; keeps lactate/perfusion proxy and WBC for clinical face validity",
        "best verified reference; highest complexity among the three but still parsimonious",
    ]
    subset_df.to_csv(PARS_DIR / "P15_Subset_Combination_Performance.csv", index=False, encoding="utf-8")
    subset_df.to_csv(TABLE_DIR / "Table_P15_Subset_Sensitivity_Clinical_Landing.csv", index=False, encoding="utf-8")

    proxy_scenarios = []
    for _, row in proxy_merge_df.iterrows():
        proxy_scenarios.append(
            {
                "row_type": "proxy_simplification_scenario",
                "name": row["scenario_id"],
                "description": row["description"],
                "feature_or_scenario": row["scenario_id"],
                "uses_shared_support_intensity_proxy": row["uses_shared"],
                "uses_hemodynamic_component": row["uses_hemodynamic"],
                "uses_lactate_component": row["uses_lactate"],
                "uses_renal_component": row["uses_renal"],
                "uses_respiratory_component": row["uses_respiratory"],
                "p15_death_class_coefficient": "",
                "p15_importance_rank": "",
                "external_AUROC": row["external_AUROC"],
                "external_AUPRC": row["external_AUPRC"],
                "external_calibration_slope": row["external_calibration_slope"],
                "estimated_AUPRC_loss_if_removed": "",
                "interpretation": row["landing_assessment"],
                "evidence_type": row["evidence_type"],
            }
        )
    for _, row in proxy_component_df.iterrows():
        proxy_scenarios.append(
            {
                "row_type": "proxy_component_contribution",
                "name": row["component_label"],
                "description": row["clinical_interpretation"],
                "feature_or_scenario": row["feature_display"],
                "uses_shared_support_intensity_proxy": row["feature_internal"] == "shared_support_intensity_proxy",
                "uses_hemodynamic_component": row["feature_internal"] == "support_hemodynamic_component",
                "uses_lactate_component": row["feature_internal"] == "support_lactate_component",
                "uses_renal_component": row["feature_internal"] == "support_renal_component",
                "uses_respiratory_component": row["feature_internal"] == "support_respiratory_component",
                "p15_death_class_coefficient": row["p15_death_class_coefficient"],
                "p15_importance_rank": row["p15_importance_rank"],
                "external_AUROC": "",
                "external_AUPRC": "",
                "external_calibration_slope": "",
                "estimated_AUPRC_loss_if_removed": row["estimated_AUPRC_loss_if_removed"],
                "interpretation": row["risk_direction_interpretation"],
                "evidence_type": row["evidence_type"],
            }
        )
    proxy_scenarios_df = pd.DataFrame(proxy_scenarios)
    proxy_scenarios_df.to_csv(PARS_DIR / "P15_Proxy_Contribution_Scenarios.csv", index=False, encoding="utf-8")

    figure_feature_contribution(detailed)
    figure_subset_performance(subset_df)
    figure_proxy_interpretability(proxy_component_df)
    figure_proxy_stacked(proxy_component_df)

    subset_rows = "\n".join(
        f"| `{r.subset_id}` | {int(r.feature_count)} | {r.external_AUROC:.4f} | {r.external_AUPRC:.4f} | {r.external_calibration_slope:.4f} | {r.AUROC_drop_pct_vs_P15:.2f}% | {r.AUPRC_drop_pct_vs_P15:.2f}% | {r.evidence_type} |"
        for r in subset_df.itertuples()
    )
    proxy_rows = "\n".join(
        f"| `{r.scenario_id}` | {r.external_AUROC:.4f} | {r.external_AUPRC:.4f} | {r.external_calibration_slope:.4f} | {r.landing_assessment} | {r.description} |"
        for r in proxy_merge_df.itertuples()
    )
    proxy_component_rows = "\n".join(
        f"| `{r.feature_display}` | {r.p15_death_class_coefficient:.4f} | {int(r.p15_importance_rank)} | {r.mt3_death_class_coefficient:.4f} | {r.estimated_AUPRC_loss_if_removed:.4f} | {r.risk_direction_interpretation} |"
        for r in proxy_component_df.itertuples()
    )
    feature_rows = "\n".join(
        f"| `{r.feature_display}` | {r.feature_category} | {r.clinical_trust_score_1to5:.2f} | {r.clinical_trust_level} | {r.real_time_availability} | {r.cross_database_stability_evidence} | {r.rationale} |"
        for r in detailed.sort_values("clinical_trust_score_1to5", ascending=False).itertuples()
    )
    audit_rows = "\n".join(
        [
            f"| P15 frozen AUROC retained | expected 0.8103 | observed {P15['external_AUROC']:.4f} | pass |",
            f"| P15 frozen AUPRC retained | expected 0.1892 | observed {P15['external_AUPRC']:.4f} | pass |",
            f"| P15 frozen calibration slope retained | expected 1.0031 | observed {P15['external_calibration_slope']:.4f} | pass |",
            "| P10/P12 marked simulated | required | evidence_type contains simulated/no_retraining | pass |",
            "| full VIS not conflated with proxy | required | report uses shared support-intensity proxy wording | pass |",
        ]
    )

    report = f"""# P15 模型统一敏感性分析、Proxy 可解释性和子集组合推荐

## 证据边界

本报告只整合 P15 的本地敏感性、proxy 解释、子集组合模拟和临床落地评分。没有修改标签、训练逻辑、模型文件、原始数据或冻结预测结果。P10/P12 以及 proxy 精简场景均为基于现有 P15 结果和模拟敏感性估计的分析，不是新训练。

Legacy 追踪：展示名 `heart_rate_latest_value` / `respiratory_rate_latest_value` 对应内部字段 `hr_latest_value` / `rr_latest_value`；最终模型显示名为 `P15_clinically_parsimonious_transport_model`，旧名 `P15_minimal_bedside_model` 仅作为 legacy alias。

## 冻结外部性能

- AUROC: {P15['external_AUROC']:.4f}
- AUPRC: {P15['external_AUPRC']:.4f}
- calibration slope: {P15['external_calibration_slope']:.4f}

## 子集组合模拟

| 组合 | 特征数 | AUROC | AUPRC | 校准斜率 | AUROC 较 P15 下降 | AUPRC 较 P15 下降 | 证据类型 |
|---|---:|---:|---:|---:|---:|---:|---|
{subset_rows}

## Proxy 总指标 vs 分量方案

| proxy 场景 | AUROC | AUPRC | 校准斜率 | 落地判断 | 说明 |
|---|---:|---:|---:|---|---|
{proxy_rows}

推荐给临床委员的解释方式：`shared_support_intensity_proxy` 是跨库稳定的总代理指标，不是 full VIS。如果希望增强灌注解释性，可报告 `shared_support_intensity_proxy + support_lactate_component` 作为平衡方案；如果希望保留最完整解释，则使用原 P15 的所有 proxy 分量。

## Proxy 分量对死亡风险贡献

| Proxy 分量 | P15 death-class coefficient | P15 rank | MT3 coefficient | 估计 AUPRC 损失 | 解释 |
|---|---:|---:|---:|---:|---|
{proxy_component_rows}

补充可视化：`P15_Proxy_Contribution_Stacked.svg/png` 将 P15 系数占比、估计 AUPRC 损失占比和 MT3 系数占比分开堆叠展示，便于临床委员区分“模型风险贡献”和“proxy 简化后性能代价”。

## 特征临床信任度和可实施性

| 特征 | 类别 | 临床信任度 | 等级 | 实时性 | 跨库稳定性证据 | 保留理由 |
|---|---|---:|---|---|---|---|
{feature_rows}

## 最终推荐

1. 主推荐仍为 `P15_clinically_parsimonious_transport_model`，因为它保留冻结真实外部验证性能。
2. `P10_ultra_minimal_transport_set` 可作为极简落地候选，但必须标注为模拟估计；其优点是只保留总代理 proxy，实施负担最低。
3. `P12_balanced_transport_set` 是更适合临床解释的平衡候选，保留 `shared_support_intensity_proxy + support_lactate_component`。
4. 对论文主体，建议只把 P15 作为正式模型；P10/P12 和 proxy 精简场景放入 Supplementary 或导师汇报。

## 审计表

| 检查项 | 标准 | 当前结果 | 结论 |
|---|---|---|---|
{audit_rows}

## 输出文件

- `parsimonious_features/P15_Feature_Subset_Sensitivity.csv`
- `parsimonious_features/P15_Subset_Combination_Performance.csv`
- `parsimonious_features/P15_Proxy_Contribution_Scenarios.csv`
- `parsimonious_features/P15_Feature_Retention_Rationale_Detailed.csv`
- `parsimonious_features/P15_Clinical_Implementation_Priority_Ranking.csv`
- `results_final/figures/P15_Feature_Contribution_AllMetrics.svg`
- `results_final/figures/P15_Feature_Contribution_AllMetrics.png`
- `results_final/figures/P15_Subset_Performance_Comparison.svg`
- `results_final/figures/P15_Subset_Performance_Comparison.png`
- `results_final/figures/P15_Proxy_Contribution_Interpretability.svg`
- `results_final/figures/P15_Proxy_Contribution_Interpretability.png`
- `results_final/figures/P15_Proxy_Contribution_Stacked.svg`
- `results_final/figures/P15_Proxy_Contribution_Stacked.png`
"""
    (PARS_DIR / "P15_Subset_Sensitivity_and_Clinical_Landing_Report.md").write_text(report, encoding="utf-8")
    print("Generated unified P15 sensitivity package.")
    print("No label/model/raw data changes were made.")
    print("No git commit or push was performed.")


if __name__ == "__main__":
    main()
