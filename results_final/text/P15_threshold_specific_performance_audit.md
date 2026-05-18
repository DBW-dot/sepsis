# P15 threshold-specific performance audit

## Data files

- `M1_internal_rich_reference_model_eicu_external`: `D:\try\step7_main_modeling\output\pred_main_eicu_external.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `M1_internal_rich_reference_model_mimic_test`: `D:\try\step7_main_modeling\output\pred_main_test_all.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `C1_dynamic_SOFA_clinical_comparator_eicu_external`: `D:\try\step7_main_modeling\output\pred_C1_eicu_external.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `C1_dynamic_SOFA_clinical_comparator_mimic_test`: `D:\try\step7_main_modeling\output\pred_C1_test_all.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `C3_no_phenotype_eicu_external`: `D:\try\step7_main_modeling\output\pred_C3_eicu_external.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `C3_no_phenotype_mimic_test`: `D:\try\step7_main_modeling\output\pred_C3_test_all.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=predicted_prob_death_24h.
- `MT3_post_metre_recalibration_eicu_external`: `D:\try\post_metre_recalibration\pred_MT3_eicu_external.parquet`; exists=True; usable=True; id=patient_id; label=event_type_24h; prediction=prob_death_raw.
- `Model_Ready_Test_All`: `D:\try\step7_main_modeling\output\Model_Ready_Test_All.parquet`; exists=True; usable=False; id=patient_id; label=event_indicator_death_24h; prediction=missing_prediction_col.
- `Model_Ready_eICU_External`: `D:\try\step7_main_modeling\output\Model_Ready_eICU_External.parquet`; exists=True; usable=False; id=patient_id; label=event_indicator_death_24h; prediction=missing_prediction_col.

## Analysis rules

- Thresholds: 0.005, 0.01, 0.02, 0.03, 0.05, 0.1.
- Bootstrap: patient-level cluster bootstrap using `patient_id` when available.
- Bootstrap resamples: 1000; seed: 20260511.
- No model retraining was performed.
- eICU was used only for external validation threshold evaluation, not for tuning.
- Recall/sensitivity is reported as a threshold-specific operational metric, not a primary model metric.
- Main model interpretation remains based on AUROC, AUPRC, calibration slope, and DCA.

## Output files

- `results_final/tables/threshold_prediction_file_audit.csv`
- `results_final/tables/P15_eICU_threshold_specific_performance.csv`
- `results_final/tables/P15_eICU_threshold_specific_performance_bootstrap_ci.csv`
- `results_final/tables/P15_eICU_threshold_DCA_integrated_table.csv`
- `results_final/tables/eICU_threshold_performance_model_comparison.csv`
- `results_final/tables/Supplementary_Table_Sx_P15_threshold_specific_operational_performance.csv`
- `results_final/text/Supplementary_Table_Sx_P15_threshold_specific_operational_performance_zh.md`
- `results_final/text/P15_threshold_specific_results_insert_zh.md`
- `results_final/text/P15_threshold_specific_discussion_insert_zh.md`
- `results_final/figures/Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.png`
- `results_final/figures/Supplementary_Figure_Sx_P15_threshold_sensitivity_PPV.pdf`

## DCA alignment

- Existing DCA source read: `D:\try\results_final\clinical_implementation\P12_P10_TrueTraining_DCA_Summary.csv`.
- P15/eICU threshold net benefit was aligned against the existing DCA summary when matching thresholds were available.

## Validation warnings

- validation_warnings = []
