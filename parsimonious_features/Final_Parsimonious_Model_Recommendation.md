# Final Parsimonious Model Recommendation

## Scope And Evidence Boundary

This update only performs feature-set combination analysis and deterministic sensitivity simulation on the frozen P15 result. It does not change labels, model training logic, model coefficients, patient-level data, or the observed AUROC/AUPRC/calibration-slope values already frozen in the repository.

Observed frozen P15 eICU external performance remains:

- AUROC: 0.8103
- AUPRC: 0.1892
- Calibration slope: 1.0031

## Recommended Model

- Recommended clinical transport model: `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias: `P15_minimal_bedside_model`.
- Recommended feature set display name: `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias: `F15_minimal_bedside_set` (15 features).
- MT3 reference display name: `MT3_Post_METRE_transport_reference_model`.
- MT3 legacy ID: `MT3_physiology_support_proxy`.

P15 remains the final recommendation because it is the smallest feature set in this repository with observed frozen external performance that satisfies the external thresholds: AUROC >= 0.78, AUPRC >= 0.15, and calibration slope >= 0.8. P10 and P12 are useful implementation candidates, but their metrics in this update are simulation-only estimates and should not replace P15 unless separately retrained and validated.

## Feature-Set Comparison

| feature set | feature count | eICU AUROC | eICU AUPRC | eICU calibration slope | evidence type | passes thresholds |
|---|---:|---:|---:|---:|---|---|
| `P10_ultra_minimal_transport_set` | 10 | 0.7947 | 0.1652 | 0.9181 | simulated_from_P15_leave_feature_penalties_no_retraining | True |
| `P12_balanced_transport_set` | 12 | 0.8010 | 0.1747 | 0.9481 | simulated_from_P15_leave_feature_penalties_no_retraining | True |
| `P15_clinically_parsimonious_transport_model` | 15 | 0.8103 | 0.1892 | 1.0031 | observed_frozen_model_metric | True |
| `MT3 full transport set` | 21 | 0.8090 | 0.1863 | 0.9652 | observed_frozen_model_metric | True |

## P15 Feature Inventory

- `hours_from_anchor`: time_anchor - Preserves disease-time alignment after t_sepsis.
- `hours_since_icu_admission`: time_anchor - Preserves process-time alignment from ICU admission.
- `is_sepsis_on_admission`: time_anchor - Separates ICU-on-admission sepsis from ICU-acquired sepsis timing.
- `hr_latest_value`: vital_sign - Bedside hemodynamic stress marker with stable cross-database semantics.
- `rr_latest_value`: vital_sign - Bedside respiratory distress marker with stable cross-database semantics.
- `spo2_latest_value`: vital_sign - Bedside oxygenation marker; highest-ranked P15 physiologic feature.
- `bun_latest_value`: routine_lab - Routine renal/perfusion laboratory marker with low cross-database missingness.
- `creatinine_latest_value`: routine_lab - Routine renal marker; retained for clinical interpretability despite lower rank.
- `platelet_latest_value`: routine_lab - Routine coagulation/host-response marker, clinically interpretable.
- `wbc_latest_value`: routine_lab - Routine inflammatory marker; helpful but less critical than oxygenation/support variables.
- `shared_support_intensity_proxy`: support_intensity_proxy - Primary transportable support-intensity summary; not full VIS.
- `support_hemodynamic_component`: support_intensity_proxy - Component-level interpretability for circulatory support burden.
- `support_lactate_component`: support_intensity_proxy - Component-level perfusion stress signal.
- `support_renal_component`: support_intensity_proxy - Component-level renal support/decline signal.
- `support_respiratory_component`: support_intensity_proxy - Component-level respiratory support escalation signal.

## Single-Feature Sensitivity Summary

Largest estimated external AUPRC losses if removed from P15:

| removed feature | category | estimated AUROC delta | estimated AUPRC delta | estimated slope delta |
|---|---|---:|---:|---:|
| `shared_support_intensity_proxy` | support_intensity_proxy | -0.0075 | -0.0140 | -0.0550 |
| `spo2_latest_value` | vital_sign | -0.0060 | -0.0120 | -0.0350 |
| `hours_from_anchor` | time_anchor | -0.0065 | -0.0090 | -0.0300 |
| `bun_latest_value` | routine_lab | -0.0045 | -0.0070 | -0.0200 |
| `support_hemodynamic_component` | support_intensity_proxy | -0.0040 | -0.0065 | -0.0250 |

These single-feature results are simulated sensitivity estimates, not retrained leave-one-feature-out models. They are intended to prioritize which features are least safe to remove before any future validation run.

## Final Interpretation

The most implementation-light option is `P10_ultra_minimal_transport_set`, but it removes WBC and all support-intensity component features except the shared composite proxy. The balanced `P12_balanced_transport_set` restores WBC and the lactate support component, improving clinical face validity while still reducing feature burden. The observed P15 remains the safest GitHub-facing final model because it keeps the shared support-intensity proxy and all component-level support signals without requiring full VIS.

Support-intensity must continue to be described as a transportable proxy, not full VIS. Full VIS remains an internal rich-model concept, while the shared support-intensity proxy is the transport feature used by the parsimonious model.

## Generated Artifacts

- `parsimonious_features/Feature_Set_Combination_Analysis.csv`
- `parsimonious_features/Feature_Contribution_Estimates.csv`
- `parsimonious_features/Single_Feature_Removal_Sensitivity.csv`
- `parsimonious_features/Support_Intensity_Proxy_Interpretability.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_final/figures/Parsimonious_Feature_Contribution_Bar.svg`
- `results_final/figures/Parsimonious_Feature_Contribution_MultiMetric.svg`
- `results_final/figures/Parsimonious_Feature_Set_Performance_Comparison.svg`
- `results_final/figures/Support_Intensity_Proxy_Interpretability.svg`
