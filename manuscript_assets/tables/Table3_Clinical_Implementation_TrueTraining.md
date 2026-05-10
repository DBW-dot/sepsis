# Table 3. P12/P10 True-training Clinical Implementation Validation

P12/P10 are true-trained on MIMIC train only. eICU is external validation only. P12 is a clinical implementation candidate; P10 is an ultra-minimal sensitivity candidate.

| model_display_name | feature_count | training_status | eICU_AUROC | eICU_AUPRC | eICU_calibration_slope | delta_AUROC_vs_P15 | delta_AUPRC_vs_P15 | relative_AUPRC_drop_pct_vs_P15 | noninferiority_status | recommended_role | caution_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P15_clinically_parsimonious_transport_model | 15 | frozen_preexisting_reference_not_retrained_this_round | 0.8103 | 0.1892 | 1.0031 | 0.0000 | 0.0000 | 0.0000 | True | formal_main_model_reference | P15 formal main model. |
| P12_true_trained_clinical_landing_model | 12 | true_trained_on_mimic_train_inner_only | 0.8038 | 0.1767 | 1.0100 | -0.0065 | -0.0125 | 6.5828 | True | validated_simplified_implementation_candidate | True-trained on MIMIC train only; eICU external validation only; does not replace P15. |
| P10_true_trained_ultra_minimal_sensitivity_model | 10 | true_trained_on_mimic_train_inner_only | 0.7978 | 0.1711 | 1.0133 | -0.0125 | -0.0181 | 9.5577 | True | validated_ultra_minimal_sensitivity_candidate_but_not_main_model | True-trained on MIMIC train only; eICU external validation only; does not replace P15. |
