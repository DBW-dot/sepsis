from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARS_DIR = ROOT / "parsimonious_features"
TABLE_DIR = ROOT / "results_final" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    subset = pd.read_csv(PARS_DIR / "P15_Subset_Combination_Performance.csv")
    proxy = pd.read_csv(PARS_DIR / "P15_Proxy_Contribution_Scenarios.csv")
    priority = pd.read_csv(PARS_DIR / "P15_Clinical_Implementation_Priority_Ranking.csv")

    subset_recs = []
    for _, row in subset.iterrows():
        if row["subset_id"] == "P10_ultra_minimal_transport_set":
            recommendation = "supplementary_extreme_minimal"
            deployment_readiness = "high_implementation_feasibility_but_simulated_only"
            clinical_summary = (
                "Best for a low-burden screening-style deployment; loses all proxy components except the shared composite."
            )
            proxy_choice = "shared_support_intensity_proxy_only"
        elif row["subset_id"] == "P12_balanced_transport_set":
            recommendation = "preferred_clinical_landing_candidate_if_simplification_needed"
            deployment_readiness = "balanced_feasibility_and_interpretability_but_simulated_only"
            clinical_summary = (
                "Best compromise if P15 is considered too complex; keeps WBC and lactate/perfusion proxy component."
            )
            proxy_choice = "shared_support_intensity_proxy_plus_support_lactate_component"
        else:
            recommendation = "main_verified_reference"
            deployment_readiness = "best_verified_evidence_with_highest_feature_burden_among_candidates"
            clinical_summary = (
                "Primary model for manuscript and validation claims; observed frozen external performance is retained."
            )
            proxy_choice = "shared_proxy_plus_all_four_proxy_components"

        subset_recs.append(
            {
                "subset_id": row["subset_id"],
                "feature_count": int(row["feature_count"]),
                "proxy_choice": proxy_choice,
                "external_AUROC": row["external_AUROC"],
                "external_AUPRC": row["external_AUPRC"],
                "external_calibration_slope": row["external_calibration_slope"],
                "AUROC_drop_pct_vs_P15": row["AUROC_drop_pct_vs_P15"],
                "AUPRC_drop_pct_vs_P15": row["AUPRC_drop_pct_vs_P15"],
                "calibration_slope_drop_pct_vs_P15": row["calibration_slope_drop_pct_vs_P15"],
                "passes_external_gate": row["passes_external_gate"],
                "evidence_type": row["evidence_type"],
                "recommendation_role": recommendation,
                "deployment_readiness": deployment_readiness,
                "clinical_summary": clinical_summary,
            }
        )

    subset_recs_df = pd.DataFrame(subset_recs)
    subset_recs_df.to_csv(PARS_DIR / "P15_Subset_Finetuning_Recommendation.csv", index=False, encoding="utf-8")
    subset_recs_df.to_csv(TABLE_DIR / "Table_P15_Subset_Finetuning_Recommendation.csv", index=False, encoding="utf-8")

    proxy_scenarios = proxy[proxy["row_type"] == "proxy_simplification_scenario"].copy()
    proxy_components = proxy[proxy["row_type"] == "proxy_component_contribution"].copy()
    proxy_focus = proxy_scenarios[
        proxy_scenarios["name"].isin(
            [
                "Proxy_A_composite_only",
                "Proxy_B_composite_plus_lactate",
                "Proxy_D_original_P15_all_components",
            ]
        )
    ].copy()
    proxy_focus["recommendation_role"] = proxy_focus["name"].map(
        {
            "Proxy_A_composite_only": "simplest_proxy_for_operational_rollout",
            "Proxy_B_composite_plus_lactate": "preferred_dual_index_proxy_for_explainability",
            "Proxy_D_original_P15_all_components": "full_P15_reference_proxy",
        }
    )
    proxy_focus["interpretability_tradeoff"] = proxy_focus["name"].map(
        {
            "Proxy_A_composite_only": "lowest implementation burden; weakest component-level clinical explanation",
            "Proxy_B_composite_plus_lactate": "adds perfusion/lactate explanation with moderate simulated performance cost",
            "Proxy_D_original_P15_all_components": "most complete proxy explanation; highest burden among proxy candidates",
        }
    )
    proxy_focus.to_csv(PARS_DIR / "P15_Proxy_Dual_Index_Recommendation.csv", index=False, encoding="utf-8")

    subset_rows = "\n".join(
        f"| `{r.subset_id}` | {r.feature_count} | {r.external_AUROC:.4f} | {r.external_AUPRC:.4f} | {r.external_calibration_slope:.4f} | {r.AUPRC_drop_pct_vs_P15:.2f}% | {r.recommendation_role} | {r.evidence_type} |"
        for r in subset_recs_df.itertuples()
    )
    proxy_rows = "\n".join(
        f"| `{r.name}` | {r.external_AUROC:.4f} | {r.external_AUPRC:.4f} | {r.external_calibration_slope:.4f} | {r.recommendation_role} | {r.interpretability_tradeoff} |"
        for r in proxy_focus.itertuples()
    )
    component_rows = "\n".join(
        f"| `{r.feature_or_scenario}` | {float(r.p15_death_class_coefficient):.4f} | {int(float(r.p15_importance_rank))} | {float(r.estimated_AUPRC_loss_if_removed):.4f} | {r.interpretation} |"
        for r in proxy_components.itertuples()
    )
    priority_rows = "\n".join(
        f"| {int(r.clinical_priority_rank)} | `{r.feature_display}` | {r.clinical_trust_score_1to5:.2f} | {r.clinical_trust_level} | {r.implementation_burden} | {r.real_time_availability} | {r.retention_recommendation} |"
        for r in priority.head(15).itertuples()
    )

    report = f"""# P15 模型子集微调与临床落地可实施性分析

## 证据边界

本报告只整合已有 P15 冻结结果、模拟敏感性、proxy 分量系数和临床落地评分。没有修改标签、训练逻辑、模型文件或原始数据。P10/P12 和 proxy 精简方案均为模拟分析，不是新训练。

## P10 / P12 / P15 微调推荐

| 子集 | 特征数 | AUROC | AUPRC | 校准斜率 | AUPRC 较 P15 下降 | 推荐角色 | 证据类型 |
|---|---:|---:|---:|---:|---:|---|---|
{subset_rows}

## Proxy 双指标组合推荐

| Proxy 方案 | AUROC | AUPRC | 校准斜率 | 推荐角色 | 解释性/落地权衡 |
|---|---:|---:|---:|---|---|
{proxy_rows}

明确建议：如果只追求最简落地，使用 `shared_support_intensity_proxy`；如果要兼顾解释性，优先使用 `shared_support_intensity_proxy + support_lactate_component`。完整 P15 继续保留全部 proxy 分量作为验证参考。

## Proxy 分量死亡风险 logit 贡献

| 分量 | P15 death-class coefficient | P15 rank | 估计 AUPRC 移除损失 | 解释 |
|---|---:|---:|---:|---|
{component_rows}

## 临床实施优先级排序

| 排名 | 特征 | 临床信任度 | 等级 | 实施负担 | 实时性 | 建议 |
|---:|---|---:|---|---|---|---|
{priority_rows}

## 最终推荐

1. 正式论文主模型仍推荐 `P15_clinically_parsimonious_transport_model`，因为它有冻结的真实外部验证性能。
2. 临床落地微调的首选简化方案是 `P12_balanced_transport_set`，因为它相较 P10 更保留 perfusion/lactate 解释性，AUPRC 模拟下降也较小。
3. 如果系统集成或人工解释负担是第一约束，可报告 `P10_ultra_minimal_transport_set` 作为极简敏感性方案，但不能替代 P15 的主结果。
4. Proxy 解释层面推荐展示“双指标方案”：`shared_support_intensity_proxy + support_lactate_component`。

## 审计结论

- P15 冻结 AUROC/AUPRC/校准斜率保持为 0.8103 / 0.1892 / 1.0031。
- P10/P12 均保留 simulated/no-retraining 标记。
- 未新增特征，未修改标签，未修改训练逻辑。
- legacy alias 保留：展示名 heart_rate/respiratory_rate，对应内部字段 hr/rr。
- shared support-intensity proxy 与 full VIS 没有混用。
"""
    (PARS_DIR / "P15_Subset_Finetuning_Clinical_Implementation_Report.md").write_text(report, encoding="utf-8")

    print("Generated P15 subset finetuning recommendation package.")
    print("No git commit or push was performed.")


if __name__ == "__main__":
    main()
