# Final Clinical Implementation Audit

## Audit Verdict

Pass. The clinical implementation outputs were integrated without changing the main P15 model, labels, cohort, anchors, or frozen metrics.

## Model Role Audit

| Item | Required role | Current status | Pass |
|---|---|---|---|
| P15 | Formal main result model | `P15_clinically_parsimonious_transport_model` remains main | yes |
| P12 | Clinical implementation simplification candidate | `preferred_clinical_landing_candidate_if_simplification_needed`; simulated only | yes |
| P10 | Ultra-minimal sensitivity scenario | `supplementary_extreme_minimal`; simulated only | yes |
| Proxy dual-index | Explanation/communication layer | `shared_support_intensity_proxy + support_lactate_component` | yes |

## Frozen Metric Audit

| Metric | Expected | Integrated value | Pass |
|---|---:|---:|---|
| P15 external AUROC | 0.8103 | 0.8103 | yes |
| P15 external AUPRC | 0.1892 | 0.1892 | yes |
| P15 external calibration slope | 1.0031 | 1.0031 | yes |

## Sensitivity Label Audit

| Output | Evidence label | Pass |
|---|---|---|
| P12 | simulated_from_P15_component_penalties_no_retraining | yes |
| P10 | simulated_from_P15_component_penalties_no_retraining | yes |

## Proxy Wording Audit

The integrated outputs describe the transport variable as `shared_support_intensity_proxy`. Full VIS is not used as the transport proxy name and is not presented as interchangeable with the shared support-intensity proxy.

## Published Paths

- `results_final/clinical_implementation/P15_Subset_Finetuning_Clinical_Implementation_Report.md`
- `results_final/clinical_implementation/P15_Subset_Finetuning_Recommendation.csv`
- `results_final/clinical_implementation/P15_Proxy_Dual_Index_Recommendation.csv`
- `results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv`
- `results_final/text/Clinical_Implementation_Notes_zh_Final.md`
