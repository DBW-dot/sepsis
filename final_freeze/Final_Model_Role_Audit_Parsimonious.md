# Final Model Role Audit - Parsimonious Freeze

## Role assignment

- `P15_clinically_parsimonious_transport_model`: final manuscript-facing model and only formal main model.
- `P12_true_trained_clinical_landing_model`: validated simplified implementation candidate; does not replace P15.
- `P10_true_trained_ultra_minimal_sensitivity_model`: validated ultra-minimal sensitivity candidate; does not replace P15.
- `MT3_Post_METRE_transport_reference_model`: Post-METRE transport reference model; not final model.
- `M1_internal_rich_reference_model`: internal rich/reference model; not external transport model.

## Guardrails

- P15 is EHR-implementable, not bedside-only and not a manual score.
- The shared support-intensity proxy is not full VIS.
- Laboratory features are latest-available carry-forward variables, not hourly real laboratory measurements.
- DCA and lead-time analyses are supplementary utility estimates, not automatic intervention triggers.

Conclusion: model roles are internally consistent for final manuscript writing.
