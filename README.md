# Sepsis Dynamic Competing-risk Prediction Final Share Repository

This repository is the GitHub-facing, safe-share result layer for the ICU sepsis 24-hour dynamic competing-risk prediction project. It excludes raw clinical databases and heavy row-level artifacts.

## Final model roles

- `P15_clinically_parsimonious_transport_model` is the only formal manuscript-facing main model. It is an EHR-implementable clinically parsimonious transport model, not a bedside-only model and not a manual score.
- `P12_true_trained_clinical_landing_model` is a validated simplified implementation candidate after true MIMIC-only training and eICU external validation. It does not replace P15.
- `P10_true_trained_ultra_minimal_sensitivity_model` is a validated ultra-minimal sensitivity candidate after true MIMIC-only training and eICU external validation. It does not replace P15.
- `MT3_Post_METRE_transport_reference_model` is a Post-METRE transport reference model, not the final model.
- `M1_internal_rich_reference_model` is an internal rich/reference model, not the external transport model.

## Frozen P15 external performance

- eICU AUROC: 0.8103
- eICU AUPRC: 0.1892
- eICU calibration slope: 1.0031

## Laboratory freshness and proxy interpretation

- Laboratory variables are latest-available / capped carry-forward values, not hourly real laboratory measurements.
- The 12h laboratory freshness sensitivity result is borderline acceptable, not fully noninferior.
- The 24h laboratory freshness sensitivity result is largely stable.
- No additional look-ahead was identified under the available timestamp structure, but result availability time is incomplete; chart/sample time was used as a conservative approximation and should be reported as a limitation.
- The shared support-intensity proxy is a cross-database support burden proxy, not full VIS. Full VIS was not used as the external transport input.
- DCA and lead-time outputs are supplementary clinical utility estimates for risk stratification or monitoring-escalation discussion, not automatic intervention triggers.

## Start here

1. `FINAL_PROJECT_SUMMARY.md`
2. `FINAL_FILE_INDEX.md`
3. `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
4. `cleanup/Final_Repository_Consistency_Report.md`
