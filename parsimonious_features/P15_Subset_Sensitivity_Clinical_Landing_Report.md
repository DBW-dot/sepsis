# P15 模型子集敏感性分析与临床落地优化

## 证据边界

本轮只做 P15 子集敏感性与临床落地评估。没有修改标签、训练逻辑、原始特征矩阵、预测文件或任何冻结指标。P10/P12 和 proxy 合并场景均为基于 P15 单特征移除罚分的模拟估计，不是新模型训练结果。

内部特征名保留 legacy alias：`hr_latest_value` 和 `rr_latest_value` 分别在展示层映射为 `heart_rate_latest_value` 与 `respiratory_rate_latest_value`，但不改动底层字段名。

## 冻结 P15 外部性能

- eICU AUROC: 0.8103
- eICU AUPRC: 0.1892
- eICU calibration slope: 1.0031

## 子集组合

| 子集 | 特征数 | AUROC | AUPRC | 校准斜率 | proxy 策略 | 证据类型 |
|---|---:|---:|---:|---:|---|---|
| `P10_ultra_minimal_transport_set` | 10 | 0.7947 | 0.1652 | 0.9181 | shared_proxy_only | simulated_from_P15_component_penalties_no_retraining |
| `P12_balanced_transport_set` | 12 | 0.8010 | 0.1747 | 0.9481 | shared_proxy_plus_lactate_component | simulated_from_P15_component_penalties_no_retraining |
| `P15_clinically_parsimonious_transport_model` | 15 | 0.8103 | 0.1892 | 1.0031 | all_proxy_components | observed_frozen_metric |

## Proxy 合并场景

| 场景 | AUROC | AUPRC | 校准斜率 | 落地判断 | 说明 |
|---|---:|---:|---:|---|---|
| `Proxy_A_composite_only` | 0.7975 | 0.1687 | 0.9281 | most_implementable_proxy | Keep shared_support_intensity_proxy only; drop all four component proxy variables. |
| `Proxy_B_composite_plus_lactate` | 0.8010 | 0.1747 | 0.9481 | balanced_proxy_candidate | Keep shared proxy plus lactate component for perfusion interpretability. |
| `Proxy_C_composite_plus_hemodynamic_lactate` | 0.8050 | 0.1812 | 0.9731 | balanced_proxy_candidate | Keep shared proxy plus hemodynamic and lactate components as the most clinically direct support subset. |
| `Proxy_D_original_P15_all_components` | 0.8103 | 0.1892 | 1.0031 | best_verified_reference | Original P15 support proxy design: shared proxy plus all four components. |

## Proxy 分量对死亡风险的解释

这里使用已有冻结文件 `Parsimonious_Model_Coefficient_Importance.csv` 中的 P15/MT3 death-class 系数，同时列出模拟移除后的 AUPRC 损失。系数是冻结模型证据，不是本轮重训；AUPRC 损失是模拟敏感性估计。

| Proxy 分量 | P15 death-class coefficient | P15 rank | MT3 coefficient | 估计 AUPRC 损失 | 解释 |
|---|---:|---:|---:|---:|---|
| `shared_support_intensity_proxy` | 0.2111 | 4 | 0.2131 | 0.0140 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_hemodynamic_component` | 0.1942 | 6 | 0.1860 | 0.0065 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_lactate_component` | 0.2028 | 5 | 0.2127 | 0.0060 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_renal_component` | 0.0389 | 13 | 0.0409 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_respiratory_component` | 0.0917 | 11 | 0.0850 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |

## 特征贡献与保留理由

| 特征 | 类别 | 可实施性加权分 | 移除后估计 AUPRC 损失 | 建议 | 保留理由 |
|---|---|---:|---:|---|---|
| `spo2_latest_value` | vital_sign | 4.75 | 0.0120 | core_keep | SpO2 carries oxygenation information and is the strongest estimated P15 single-feature contributor. |
| `heart_rate_latest_value` | vital_sign | 4.6 | 0.0055 | core_keep | Heart rate is a universally charted bedside marker of circulatory stress. |
| `hours_from_anchor` | time_anchor | 4.5 | 0.0090 | core_keep | Disease-time anchor from t_sepsis; high transport value and preserves prefix-only temporal framing. |
| `shared_support_intensity_proxy` | support_proxy | 4.5 | 0.0140 | core_keep | Transportable support-intensity composite; proxy only, not full VIS. |
| `respiratory_rate_latest_value` | vital_sign | 4.35 | 0.0045 | core_keep | Respiratory rate is clinically simple, low-cost, and transportable across ICU datasets. |
| `hours_since_icu_admission` | time_anchor | 4.3 | 0.0055 | core_keep | ICU process-time anchor; available in both databases and necessary for dual-anchor alignment. |
| `is_sepsis_on_admission` | time_anchor | 4.3 | 0.0040 | core_keep | Separates admission sepsis from ICU-acquired sepsis without using future outcomes. |
| `bun_latest_value` | routine_lab | 4.3 | 0.0070 | core_keep | Routine renal/perfusion marker with strong estimated transport contribution. |
| `platelet_latest_value` | routine_lab | 4.1 | 0.0048 | core_keep | Routine coagulation/host-response marker with clear clinical interpretation. |
| `support_hemodynamic_component` | support_proxy | 4.0 | 0.0065 | balanced_or_P15_keep | Circulatory support component; useful for P15 interpretability but removable in simpler subsets. |
| `creatinine_latest_value` | routine_lab | 3.9 | 0.0030 | core_keep | Routine renal laboratory marker; interpretable but lower estimated incremental contribution than BUN. |
| `support_renal_component` | support_proxy | 3.8 | 0.0040 | balanced_or_P15_keep | Renal support/decline component; useful in P15, excluded from simpler subsets. |
| `support_respiratory_component` | support_proxy | 3.8 | 0.0040 | balanced_or_P15_keep | Respiratory support escalation component; useful in P15, excluded from simpler subsets. |
| `support_lactate_component` | support_proxy | 3.75 | 0.0060 | balanced_or_P15_keep | Perfusion component; retained in P12 as the most clinically direct support subcomponent. |
| `wbc_latest_value` | routine_lab | 3.6 | 0.0035 | balanced_or_P15_keep | Inflammation marker; clinically interpretable but weaker single-feature contribution, so excluded from P10. |

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
