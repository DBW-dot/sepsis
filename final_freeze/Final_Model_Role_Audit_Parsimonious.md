# Final Model Role Audit - Parsimonious Integration

## Verdict

Final parsimonious model role consistency: `PASS`.

## Frozen roles

| Technical / legacy ID | Manuscript display name | Frozen role |
|---|---|---|
| M1_original_rich | M1_internal_rich_reference_model | internal rich/reference model |
| MT3_physiology_support_proxy | MT3_Post_METRE_transport_reference_model | Post-METRE transport reference model |
| P15_minimal_bedside_model | P15_clinically_parsimonious_transport_model | final clinically parsimonious transport model |
| P25_clinical_core_model | P25_clinical_core_sensitivity_model | sensitivity model |
| P40_balanced_transport_model | P40_balanced_transport_sensitivity_model | sensitivity model |
| C1_dynamic_SOFA | C1_dynamic_SOFA_clinical_comparator | clinical comparator |
| phenotype | early_static_phenotype_audit_tool | stratification / explanation / calibration audit tool |

## Naming guardrails

- P15 should be described as a clinically parsimonious transport model, not as an all-bedside manual score.
- `P15_minimal_bedside_model` is retained only as a legacy/internal alias for traceability.
- MT3 is a Post-METRE transport reference model, not the final clinical model.
- M1 is an internal rich/reference model, not the external transport model.
- Early static phenotype is retained only for stratification, explanation, and calibration audit.
- Full VIS is retained only for internal-rich/sensitivity analyses; the cross-database transport model uses the shared support-intensity proxy.

## Guardrails verified

- No model was retrained in this integration step.
- Cohort, Step 1-6 artifacts, dual-anchor logic, Sepsis-3 suspected infection definition, and 24h competing-risk labels were not modified.
- eICU remains external validation only.
- Phenotype is not restored as a default transport input.
- Full VIS is not used as an external transport input.
- Measurement-process variables are not restored into the final transport model.
