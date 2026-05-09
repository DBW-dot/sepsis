# Final Clinical Feature Validity Audit

## Scope

This audit reviews the final P15 feature set, P12 simplification candidate, P10 ultra-minimal sensitivity scenario, and support-intensity proxy wording from a clinical validity and implementation perspective. It does not retrain models or alter labels, features, predictions, anchors, or Step 1-8 outputs.

## Output Files

- `results_final/clinical_implementation/P15_Final_Clinical_Feature_Validity_Audit.csv`
- `results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md`
- `results_final/clinical_implementation/P15_P12_P10_Clinical_Use_Boundaries.md`
- `results_final/clinical_implementation/Clinical_Feature_Audit_PI_Summary_zh.md`
- `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`

## Verdict

- P15 remains clinically reasonable as an EHR-implementable, clinically parsimonious transport model.
- P12 is appropriate as a simulated simplification candidate if feature burden must be reduced.
- P10 is appropriate only as an ultra-minimal sensitivity scenario.
- Proxy variables are acceptable if explained as cross-database support-burden proxies, not full VIS or drug-dose scores.

## Risk Wording Scan

No unqualified risky wording was found. Negated guardrails were allowed.

| file | line | risk phrase | line text |
|---|---:|---|---|
| none | none | none | none |

## Frozen Metric Check

| Metric | Expected | Status |
|---|---:|---|
| P15 external AUROC | 0.8103 | retained |
| P15 external AUPRC | 0.1892 | retained |
| P15 external calibration slope | 1.0031 | retained |

## Final Recommendation

The project can proceed to final manuscript rewriting with P15 as the main model, P12/P10 as implementation sensitivity outputs, and the proxy dual-index explanation used for clinical communication.
