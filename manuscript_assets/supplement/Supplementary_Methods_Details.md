# Supplementary Methods Details

This document is a methods-support asset, not the full manuscript text. It summarizes final locked methods language using only the approved repository sources.

## 1. Study design

This is a retrospective clinical database study using MIMIC-IV for model development and internal validation, with eICU reserved for external validation. eICU was not used for model training or hyperparameter tuning.

## 2. Cohort definition

The study target is ICU sepsis 24-hour dynamic competing-risk prediction. Cohort construction follows the project Sepsis-3 logic, including suspected infection, `t_ICU`, and `t_sepsis` anchor definitions. Patient-level split logic is part of the locked modeling workflow. This supplement does not add cohort counts beyond the locked tables.

## 3. Dynamic prediction design

Prediction uses an hourly prediction grid. All features at a prediction time are prefix-only observations, meaning they can only use information available at or before the prediction time. The prediction horizon is 24 hours. No post-prediction information is used.

## 4. Competing risk design

The 24-hour outcome is framed as three mutually exclusive states: ICU death within 24 hours, alive ICU discharge/transfer within 24 hours, or continued ICU stay. This supports a competing-risk interpretation rather than a simple death-vs-nondeath binary framing. Cumulative-incidence language should remain conceptual unless a specific formula source is added later from an approved method file.

## 5. Model hierarchy

- `M1_internal_rich_reference_model`: internal rich/reference model, not the external transport model.
- `MT3_Post_METRE_transport_reference_model`: Post-METRE transport reference model, not the final model.
- `P15_clinically_parsimonious_transport_model`: final formal manuscript-facing main model.
- `P12_true_trained_clinical_landing_model`: true-trained validated simplified implementation candidate, not replacing P15.
- `P10_true_trained_ultra_minimal_sensitivity_model`: true-trained validated ultra-minimal sensitivity candidate, not replacing P15.
- `C1_dynamic_SOFA_clinical_comparator`: clinical comparator.

## 6. Clinical implementation analyses

Clinical implementation support includes P12/P10 true-training validation, laboratory freshness sensitivity, proxy interpretability, and supplementary DCA/lead-time estimates. DCA and lead-time are not automatic intervention triggers or direct treatment recommendations.

## Source availability

- `README.md`: available
- `FINAL_PROJECT_SUMMARY.md`: available
- `FINAL_FILE_INDEX.md`: available
- `manuscript_assets/FINAL_MANUSCRIPT_NUMBERS.md`: available
- `manuscript_assets/MANUSCRIPT_ASSET_INDEX.md`: available
- `manuscript_assets/tables/TABLE_INDEX.md`: available
- `manuscript_assets/figures/FIGURE_INDEX.md`: available
- `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`: available
- `results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md`: available
- `results_final/clinical_implementation/Lab_Freshness_Sensitivity_Report.md`: available
- `results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md`: available
- `results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md`: available
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`: available
- `cleanup/Final_Repository_Consistency_Report.md`: available
