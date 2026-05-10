# Honest Reporting Checklist - Final Parsimonious Model

- `P15_clinically_parsimonious_transport_model` is the only formal manuscript-facing main model.
- `P12_true_trained_clinical_landing_model` is a true-trained validated simplified implementation candidate, not the final model and not a replacement for P15.
- `P10_true_trained_ultra_minimal_sensitivity_model` is a true-trained validated ultra-minimal sensitivity candidate, not the final model and not a replacement for P15.
- P15 is EHR-implementable but not a bedside-only manual score.
- Laboratory variables are not assumed to be measured hourly.
- Laboratory latest values should be interpreted as most recent available values under capped carry-forward rules.
- The 12h laboratory freshness sensitivity is borderline acceptable, not fully noninferior.
- The 24h laboratory freshness sensitivity is largely stable.
- No laboratory value after the prediction time was used.
- Result availability time is incomplete; chart/sample time was used as a conservative approximation and should be reported as a limitation.
- The shared support-intensity proxy is a cross-database support burden proxy, not full VIS.
- Proxy components require clear clinical interpretation before deployment.
- Full VIS was not used as the external transport input.
- DCA and lead-time results are supplementary clinical utility estimates, not automatic intervention triggers or direct treatment recommendations.
- Clinical implementation still requires local EHR mapping and prospective validation.
