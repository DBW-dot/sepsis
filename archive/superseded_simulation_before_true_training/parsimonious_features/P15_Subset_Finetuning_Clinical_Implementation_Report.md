# P15 模型子集微调与临床落地可实施性分析

## 证据边界

本报告只整合已有 P15 冻结结果、模拟敏感性、proxy 分量系数和临床落地评分。没有修改标签、训练逻辑、模型文件或原始数据。P10/P12 和 proxy 精简方案均为模拟分析，不是新训练。

## P10 / P12 / P15 微调推荐

| 子集 | 特征数 | AUROC | AUPRC | 校准斜率 | AUPRC 较 P15 下降 | 推荐角色 | 证据类型 |
|---|---:|---:|---:|---:|---:|---|---|
| `P10_ultra_minimal_transport_set` | 10 | 0.7947 | 0.1652 | 0.9181 | 12.69% | supplementary_extreme_minimal | simulated_from_P15_component_penalties_no_retraining |
| `P12_balanced_transport_set` | 12 | 0.8010 | 0.1747 | 0.9481 | 7.66% | preferred_clinical_landing_candidate_if_simplification_needed | simulated_from_P15_component_penalties_no_retraining |
| `P15_clinically_parsimonious_transport_model` | 15 | 0.8103 | 0.1892 | 1.0031 | 0.00% | main_verified_reference | observed_frozen_metric |

## Proxy 双指标组合推荐

| Proxy 方案 | AUROC | AUPRC | 校准斜率 | 推荐角色 | 解释性/落地权衡 |
|---|---:|---:|---:|---|---|
| `Proxy_A_composite_only` | 0.7975 | 0.1687 | 0.9281 | simplest_proxy_for_operational_rollout | lowest implementation burden; weakest component-level clinical explanation |
| `Proxy_B_composite_plus_lactate` | 0.8010 | 0.1747 | 0.9481 | preferred_dual_index_proxy_for_explainability | adds perfusion/lactate explanation with moderate simulated performance cost |
| `Proxy_D_original_P15_all_components` | 0.8103 | 0.1892 | 1.0031 | full_P15_reference_proxy | most complete proxy explanation; highest burden among proxy candidates |

明确建议：如果只追求最简落地，使用 `shared_support_intensity_proxy`；如果要兼顾解释性，优先使用 `shared_support_intensity_proxy + support_lactate_component`。完整 P15 继续保留全部 proxy 分量作为验证参考。

## Proxy 分量死亡风险 logit 贡献

| 分量 | P15 death-class coefficient | P15 rank | 估计 AUPRC 移除损失 | 解释 |
|---|---:|---:|---:|---|
| `shared_support_intensity_proxy` | 0.2111 | 4 | 0.0140 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_hemodynamic_component` | 0.1942 | 6 | 0.0065 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_lactate_component` | 0.2028 | 5 | 0.0060 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_renal_component` | 0.0389 | 13 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |
| `support_respiratory_component` | 0.0917 | 11 | 0.0040 | positive death-class coefficient in frozen P15; higher proxy burden is associated with higher death-risk logit |

## 临床实施优先级排序

| 排名 | 特征 | 临床信任度 | 等级 | 实施负担 | 实时性 | 建议 |
|---:|---|---:|---|---|---|---|
| 1 | `spo2_latest_value` | 4.75 | very_high | routine_bedside_monitoring | near_real_time | core_keep |
| 2 | `heart_rate_latest_value` | 4.60 | very_high | routine_bedside_monitoring | near_real_time | core_keep |
| 3 | `hours_from_anchor` | 4.50 | very_high | automatic_timestamp_or_anchor_logic | near_real_time | core_keep |
| 4 | `shared_support_intensity_proxy` | 4.50 | very_high | derived_transport_proxy_from_support_signals | derived_after_source_signal_update | core_keep |
| 5 | `respiratory_rate_latest_value` | 4.35 | high | routine_bedside_monitoring | near_real_time | core_keep |
| 6 | `hours_since_icu_admission` | 4.30 | high | automatic_timestamp_or_anchor_logic | near_real_time | core_keep |
| 7 | `is_sepsis_on_admission` | 4.30 | high | automatic_timestamp_or_anchor_logic | near_real_time | core_keep |
| 8 | `bun_latest_value` | 4.30 | high | routine_blood_laboratory | episodic_laboratory_turnaround | core_keep |
| 9 | `platelet_latest_value` | 4.10 | high | routine_blood_laboratory | episodic_laboratory_turnaround | core_keep |
| 10 | `support_hemodynamic_component` | 4.00 | high | derived_transport_proxy_from_support_signals | derived_after_source_signal_update | balanced_or_P15_keep |
| 11 | `creatinine_latest_value` | 3.90 | moderate | routine_blood_laboratory | episodic_laboratory_turnaround | core_keep |
| 12 | `support_renal_component` | 3.80 | moderate | derived_transport_proxy_from_support_signals | derived_after_source_signal_update | balanced_or_P15_keep |
| 13 | `support_respiratory_component` | 3.80 | moderate | derived_transport_proxy_from_support_signals | derived_after_source_signal_update | balanced_or_P15_keep |
| 14 | `support_lactate_component` | 3.75 | moderate | derived_transport_proxy_from_support_signals | derived_after_source_signal_update | balanced_or_P15_keep |
| 15 | `wbc_latest_value` | 3.60 | moderate | routine_blood_laboratory | episodic_laboratory_turnaround | balanced_or_P15_keep |

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
