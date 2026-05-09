# P15 特征集优化与临床可实施性评估

## 证据边界

本报告只在已冻结的 `P15_clinically_parsimonious_transport_model` 上做特征组合分析和模拟敏感性评估；没有修改标签、训练逻辑、模型系数或任何原始数据。P10/P12 的性能是基于 P15 单特征移除罚分的确定性模拟估计，不是新训练结果。

## 当前冻结性能

- eICU AUROC: 0.8103
- eICU AUPRC: 0.1892
- eICU calibration slope: 1.0031

## 候选特征组合

| 组合 | 特征数 | eICU AUROC | eICU AUPRC | 校准斜率 | 证据类型 | 结论 |
|---|---:|---:|---:|---:|---|---|
| `P10_ultra_minimal_transport_set` | 10 | 0.7947 | 0.1652 | 0.9181 | simulated_from_P15_leave_feature_penalties_no_retraining | True |
| `P12_balanced_transport_set` | 12 | 0.8010 | 0.1747 | 0.9481 | simulated_from_P15_leave_feature_penalties_no_retraining | True |
| `P15_clinically_parsimonious_transport_model` | 15 | 0.8103 | 0.1892 | 1.0031 | observed_frozen_model_metric | True |
| `MT3 full transport set` | 21 | 0.8090 | 0.1863 | 0.9652 | observed_frozen_model_metric | True |

## 推荐结论

正式推荐仍为 `P15_clinically_parsimonious_transport_model`。理由是：P15 是当前仓库中最小的、具有真实冻结外部验证指标且满足 AUROC >= 0.78、AUPRC >= 0.15、calibration slope >= 0.8 的模型。`P10_ultra_minimal_transport_set` 和 `P12_balanced_transport_set` 可以作为临床实施敏感性候选，但在真正重训和外部验证前不能替代 P15。

## proxy 精简解释

极简 P10 只保留 `shared_support_intensity_proxy`，删除 4 个 component-level proxy，以换取更低实施负担。平衡 P12 恢复 `support_lactate_component` 和 `wbc_latest_value`，提升灌注/炎症解释性。原版 P15 保留全部 5 个支持强度 proxy，因此最适合作为已验证的最终版本。

## 单特征敏感性

| 移除特征 | 类别 | 估计 AUROC 变化 | 估计 AUPRC 变化 | 估计校准斜率变化 |
|---|---|---:|---:|---:|
| `shared_support_intensity_proxy` | support_intensity_proxy | -0.0075 | -0.0140 | -0.0550 |
| `spo2_latest_value` | vital_sign | -0.0060 | -0.0120 | -0.0350 |
| `hours_from_anchor` | time_anchor | -0.0065 | -0.0090 | -0.0300 |
| `bun_latest_value` | routine_lab | -0.0045 | -0.0070 | -0.0200 |
| `support_hemodynamic_component` | support_intensity_proxy | -0.0040 | -0.0065 | -0.0250 |

## 可实施性评分

| 特征 | 类别 | 临床解释性 | 跨库稳定性 | 实施便利性 | 模型重要性 | 加权评分 | 建议 |
|---|---|---:|---:|---:|---:|---:|---|
| `spo2_latest_value` | vital_sign | 5 | 4 | 5 | 5 | 4.75 | core_keep |
| `hr_latest_value` | vital_sign | 5 | 5 | 5 | 3 | 4.6 | core_keep |
| `hours_from_anchor` | time_anchor | 4 | 5 | 5 | 4 | 4.5 | core_keep |
| `shared_support_intensity_proxy` | support_intensity_proxy | 5 | 5 | 3 | 5 | 4.5 | core_keep |
| `rr_latest_value` | vital_sign | 5 | 4 | 5 | 3 | 4.35 | core_keep |
| `hours_since_icu_admission` | time_anchor | 4 | 5 | 5 | 3 | 4.3 | core_keep |
| `is_sepsis_on_admission` | time_anchor | 4 | 5 | 5 | 3 | 4.3 | core_keep |
| `bun_latest_value` | routine_lab | 5 | 4 | 4 | 4 | 4.3 | core_keep |
| `platelet_latest_value` | routine_lab | 5 | 4 | 4 | 3 | 4.1 | core_keep |
| `support_hemodynamic_component` | support_intensity_proxy | 4 | 5 | 3 | 4 | 4.0 | balanced_or_P15_keep |
| `creatinine_latest_value` | routine_lab | 5 | 4 | 4 | 2 | 3.9 | core_keep |
| `support_renal_component` | support_intensity_proxy | 4 | 5 | 3 | 3 | 3.8 | balanced_or_P15_keep |
| `support_respiratory_component` | support_intensity_proxy | 4 | 5 | 3 | 3 | 3.8 | balanced_or_P15_keep |
| `support_lactate_component` | support_intensity_proxy | 4 | 4 | 3 | 4 | 3.75 | balanced_or_P15_keep |
| `wbc_latest_value` | routine_lab | 4 | 4 | 4 | 2 | 3.6 | balanced_or_P15_keep |

## 文件索引

- `parsimonious_features/Feature_Set_Combination_Analysis.csv`
- `parsimonious_features/Feature_Implementability_Scorecard.csv`
- `parsimonious_features/Feature_Contribution_Estimates.csv`
- `parsimonious_features/Single_Feature_Removal_Sensitivity.csv`
- `parsimonious_features/Support_Intensity_Proxy_Interpretability.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_final/figures/Parsimonious_Feature_Contribution_MultiMetric.svg`
