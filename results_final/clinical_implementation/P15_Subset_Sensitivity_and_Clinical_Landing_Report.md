# P15 模型统一敏感性分析、Proxy 可解释性和子集组合推荐

## 证据边界

本报告只整合 P15 的本地敏感性、proxy 解释、子集组合模拟和临床落地评分。没有修改标签、训练逻辑、模型文件、原始数据或冻结预测结果。P10/P12 以及 proxy 精简场景均为基于现有 P15 结果和模拟敏感性估计的分析，不是新训练。

Legacy 追踪：展示名 `heart_rate_latest_value` / `respiratory_rate_latest_value` 对应内部字段 `hr_latest_value` / `rr_latest_value`；最终模型显示名为 `P15_clinically_parsimonious_transport_model`，旧名 `P15_minimal_bedside_model` 仅作为 legacy alias。

## 冻结外部性能

- AUROC: 0.8103
- AUPRC: 0.1892
- calibration slope: 1.0031

## 子集组合模拟

| 组合 | 特征数 | AUROC | AUPRC | 校准斜率 | AUROC 较 P15 下降 | AUPRC 较 P15 下降 | 证据类型 |
|---|---:|---:|---:|---:|---:|---:|---|
| `P10_ultra_minimal_transport_set` | 10 | 0.7947 | 0.1652 | 0.9181 | 1.93% | 12.69% | simulated_from_P15_component_penalties_no_retraining |
| `P12_balanced_transport_set` | 12 | 0.8010 | 0.1747 | 0.9481 | 1.15% | 7.66% | simulated_from_P15_component_penalties_no_retraining |
| `P15_clinically_parsimonious_transport_model` | 15 | 0.8103 | 0.1892 | 1.0031 | 0.00% | 0.00% | observed_frozen_metric |

## Proxy 总指标 vs 分量方案

| proxy 场景 | AUROC | AUPRC | 校准斜率 | 落地判断 | 说明 |
|---|---:|---:|---:|---|---|
| `Proxy_A_composite_only` | 0.7975 | 0.1687 | 0.9281 | most_implementable_proxy | Keep shared_support_intensity_proxy only; drop all four component proxy variables. |
| `Proxy_B_composite_plus_lactate` | 0.8010 | 0.1747 | 0.9481 | balanced_proxy_candidate | Keep shared proxy plus lactate component for perfusion interpretability. |
| `Proxy_C_composite_plus_hemodynamic_lactate` | 0.8050 | 0.1812 | 0.9731 | balanced_proxy_candidate | Keep shared proxy plus hemodynamic and lactate components as the most clinically direct support subset. |
| `Proxy_D_original_P15_all_components` | 0.8103 | 0.1892 | 1.0031 | best_verified_reference | Original P15 support proxy design: shared proxy plus all four components. |

推荐给临床委员的解释方式：`shared_support_intensity_proxy` 是跨库稳定的总代理指标，不是 full VIS。如果希望增强灌注解释性，可报告 `shared_support_intensity_proxy + support_lactate_component` 作为平衡方案；如果希望保留最完整解释，则使用原 P15 的所有 proxy 分量。

## Proxy 分量对死亡风险贡献

| Proxy 分量 | P15 death-class coefficient | P15 rank | MT3 coefficient | 估计 AUPRC 损失 | 解释 |
|---|---:|---:|---:|---:|---|
| `shared_support_intensity_proxy` | 0.2111 | 4 | 0.2131 | 0.0140 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_hemodynamic_component` | 0.1942 | 6 | 0.1860 | 0.0065 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_lactate_component` | 0.2028 | 5 | 0.2127 | 0.0060 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_renal_component` | 0.0389 | 13 | 0.0409 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_respiratory_component` | 0.0917 | 11 | 0.0850 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |

补充可视化：`P15_Proxy_Contribution_Stacked.svg/png` 将 P15 系数占比、估计 AUPRC 损失占比和 MT3 系数占比分开堆叠展示，便于临床委员区分“模型风险贡献”和“proxy 简化后性能代价”。

## 特征临床信任度和可实施性

| 特征 | 类别 | 临床信任度 | 等级 | 实时性 | 跨库稳定性证据 | 保留理由 |
|---|---|---:|---|---|---|---|
| `spo2_latest_value` | vital_sign | 4.75 | very_high | near_real_time | MIMIC missing 0.094; eICU missing 0.031 | SpO2 carries oxygenation information and is the strongest estimated P15 single-feature contributor. |
| `heart_rate_latest_value` | vital_sign | 4.60 | very_high | near_real_time | MIMIC missing 0.074; eICU missing 0.011 | Heart rate is a universally charted bedside marker of circulatory stress. |
| `hours_from_anchor` | time_anchor | 4.50 | very_high | near_real_time | MIMIC missing 0.000; eICU missing 0.000 | Disease-time anchor from t_sepsis; high transport value and preserves prefix-only temporal framing. |
| `shared_support_intensity_proxy` | support_proxy | 4.50 | very_high | derived_after_source_signal_update | MIMIC missing 0.000; eICU missing 0.000 | Transportable support-intensity composite; proxy only, not full VIS. |
| `respiratory_rate_latest_value` | vital_sign | 4.35 | high | near_real_time | MIMIC missing 0.081; eICU missing 0.057 | Respiratory rate is clinically simple, low-cost, and transportable across ICU datasets. |
| `hours_since_icu_admission` | time_anchor | 4.30 | high | near_real_time | MIMIC missing 0.000; eICU missing 0.000 | ICU process-time anchor; available in both databases and necessary for dual-anchor alignment. |
| `is_sepsis_on_admission` | time_anchor | 4.30 | high | near_real_time | MIMIC missing 0.000; eICU missing 0.000 | Separates admission sepsis from ICU-acquired sepsis without using future outcomes. |
| `bun_latest_value` | routine_lab | 4.30 | high | episodic_laboratory_turnaround | MIMIC missing 0.025; eICU missing 0.051 | Routine renal/perfusion marker with strong estimated transport contribution. |
| `platelet_latest_value` | routine_lab | 4.10 | high | episodic_laboratory_turnaround | MIMIC missing 0.030; eICU missing 0.071 | Routine coagulation/host-response marker with clear clinical interpretation. |
| `support_hemodynamic_component` | support_proxy | 4.00 | high | derived_after_source_signal_update | MIMIC missing 0.000; eICU missing 0.000 | Circulatory support component; useful for P15 interpretability but removable in simpler subsets. |
| `creatinine_latest_value` | routine_lab | 3.90 | moderate | episodic_laboratory_turnaround | MIMIC missing 0.025; eICU missing 0.050 | Routine renal laboratory marker; interpretable but lower estimated incremental contribution than BUN. |
| `support_renal_component` | support_proxy | 3.80 | moderate | derived_after_source_signal_update | MIMIC missing 0.000; eICU missing 0.000 | Renal support/decline component; useful in P15, excluded from simpler subsets. |
| `support_respiratory_component` | support_proxy | 3.80 | moderate | derived_after_source_signal_update | MIMIC missing 0.000; eICU missing 0.000 | Respiratory support escalation component; useful in P15, excluded from simpler subsets. |
| `support_lactate_component` | support_proxy | 3.75 | moderate | derived_after_source_signal_update | MIMIC missing 0.000; eICU missing 0.000 | Perfusion component; retained in P12 as the most clinically direct support subcomponent. |
| `wbc_latest_value` | routine_lab | 3.60 | moderate | episodic_laboratory_turnaround | MIMIC missing 0.029; eICU missing 0.072 | Inflammation marker; clinically interpretable but weaker single-feature contribution, so excluded from P10. |

## 最终推荐

1. 主推荐仍为 `P15_clinically_parsimonious_transport_model`，因为它保留冻结真实外部验证性能。
2. `P10_ultra_minimal_transport_set` 可作为极简落地候选，但必须标注为模拟估计；其优点是只保留总代理 proxy，实施负担最低。
3. `P12_balanced_transport_set` 是更适合临床解释的平衡候选，保留 `shared_support_intensity_proxy + support_lactate_component`。
4. 对论文主体，建议只把 P15 作为正式模型；P10/P12 和 proxy 精简场景放入 Supplementary 或导师汇报。

## 审计表

| 检查项 | 标准 | 当前结果 | 结论 |
|---|---|---|---|
| P15 frozen AUROC retained | expected 0.8103 | observed 0.8103 | pass |
| P15 frozen AUPRC retained | expected 0.1892 | observed 0.1892 | pass |
| P15 frozen calibration slope retained | expected 1.0031 | observed 1.0031 | pass |
| P10/P12 marked simulated | required | evidence_type contains simulated/no_retraining | pass |
| full VIS not conflated with proxy | required | report uses shared support-intensity proxy wording | pass |

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
