# Final Model Role Audit - Parsimonious Integration

## Verdict

Final parsimonious model role consistency: `PASS`.

## Frozen roles

| Model or object | Frozen role |
|---|---|
| M1_original_rich | internal rich/reference model |
| MT3_physiology_support_proxy | Post-METRE transport reference model |
| P15_minimal_bedside_model | final clinically parsimonious transport model |
| P25_clinical_core_model | sensitivity model |
| P40_balanced_transport_model | sensitivity model |
| C1_dynamic_SOFA | clinical comparator |
| phenotype | stratification / explanation / calibration audit tool |

## Guardrails verified

- No model was retrained in this integration step.
- Cohort, Step 1-6 artifacts, dual-anchor logic, Sepsis-3 suspected infection definition, and 24h competing-risk labels were not modified.
- eICU remains external validation only.
- Phenotype is not restored as a default transport input.
- Full VIS is not used as an external transport input.
- Measurement-process variables are not restored into the final transport model.
