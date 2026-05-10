# Final Manuscript Numbers

Generated from final authority files in this repository. Missing values are reported as `not_found`; no manuscript number was invented.

## 1. Final model roles

- `P15_clinically_parsimonious_transport_model`
  - formal main manuscript-facing model
  - 正式主模型
- `P12_true_trained_clinical_landing_model`
  - validated simplified implementation candidate
  - 真实训练验证后的临床简化候选
  - not replacing P15
- `P10_true_trained_ultra_minimal_sensitivity_model`
  - validated ultra-minimal sensitivity candidate
  - 真实训练验证后的极简敏感性模型
  - not replacing P15
- `MT3_Post_METRE_transport_reference_model`
  - Post-METRE transport reference model
  - not final model
- `M1_internal_rich_reference_model`
  - internal rich/reference model
  - not external transport model

## 2. Main P15 performance

- MIMIC AUROC: 0.7977
- MIMIC AUPRC: 0.1982
- MIMIC Brier: 0.5843
- eICU AUROC: 0.8103
- eICU AUPRC: 0.1892
- eICU calibration slope: 1.0031
- feature count: 15

## 3. Comparator performance

| Model | feature_count | eICU AUROC | eICU AUPRC | eICU calibration slope | manuscript role | interpretation |
|---|---:|---:|---:|---:|---|---|
| M1_internal_rich_reference_model | 70 | 0.7090 | 0.0377 | 0.0728 | internal rich/reference model | Strong internal reference model, externally unstable; not the final external transport model. |
| MT3_Post_METRE_transport_reference_model | 21 | 0.8090 | 0.1863 | 0.9652 | Post-METRE transport reference model | Transport reference model used before final parsimonious P15 freeze; not the final model. |
| P15_clinically_parsimonious_transport_model | 15 | 0.8103 | 0.1892 | 1.0031 | formal main manuscript-facing model | Final clinically parsimonious transport model with stable eICU discrimination and calibration. |
| P12_true_trained_clinical_landing_model | 12 | 0.8038 | 0.1767 | 1.0100 | validated simplified implementation candidate | True-trained simplified candidate; does not replace P15. |
| P10_true_trained_ultra_minimal_sensitivity_model | 10 | 0.7978 | 0.1711 | 1.0133 | validated ultra-minimal sensitivity candidate | True-trained ultra-minimal sensitivity candidate; does not replace P15. |
| C1_dynamic_SOFA | 15 | 0.7253 | 0.0669 | 0.4919 | clinical score comparator | Dynamic SOFA clinical comparator from final parsimonious Table2. |

## 4. P12/P10 true-training validation

- P12 eICU AUROC/AUPRC/calibration slope: 0.8038 / 0.1767 / 1.0100
- P12 relative AUPRC drop vs P15: 6.5828%
- P12 noninferiority status: True
- P12 recommended role: validated_simplified_implementation_candidate

- P10 eICU AUROC/AUPRC/calibration slope: 0.7978 / 0.1711 / 1.0133
- P10 relative AUPRC drop vs P15: 9.5577%
- P10 noninferiority status: True
- P10 recommended role: validated_ultra_minimal_sensitivity_candidate_but_not_main_model

## 5. Lab freshness results

- current latest_value interpretation: latest-available / capped carry-forward
- P15 current eICU AUROC/AUPRC/calibration slope: 0.8103 / 0.1892 / 1.0031
- P15 12h freshness eICU AUROC/AUPRC/calibration slope: 0.7847 / 0.1674 / 0.9779
- P15 24h freshness eICU AUROC/AUPRC/calibration slope: 0.8085 / 0.1860 / 0.9991
- 12h status: borderline acceptable, not fully noninferior; table status = borderline_acceptable
- 24h status: largely stable; table status = acceptable
- look-ahead limitation: result availability time incomplete; chart/sample time used as conservative approximation

## 6. Clinical interpretation boundaries

- P15 is not a bedside-only manual score.
- P15 is EHR-implementable.
- Laboratory values are not assumed to be measured hourly.
- shared support-intensity proxy is not full VIS.
- DCA/lead-time are not automatic intervention triggers.
- Clinical implementation requires local EHR mapping and prospective validation.

## 7. Numbers not to use

- Archive materials containing old pre-METRE numbers.
- Old simulation-only P10/P12 numbers that were superseded by true-training validation.
- Old DCA / lead-time / phenotype gain files outside the final file index.
- Old Post-METRE transition results unless explicitly labeled as historical reference.

## Missing source files

- none
