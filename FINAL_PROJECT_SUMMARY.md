# Final Project Summary

## Final frozen position

The final manuscript-facing model is `P15_clinically_parsimonious_transport_model`. It remains the only formal main model and keeps the frozen eICU external metrics: AUROC 0.8103, AUPRC 0.1892, and calibration slope 1.0031.

`P12_true_trained_clinical_landing_model` and `P10_true_trained_ultra_minimal_sensitivity_model` have moved beyond simulation-only summaries through true MIMIC-only training and eICU external validation. P12 is a validated simplified implementation candidate. P10 is a validated ultra-minimal sensitivity candidate. Neither model automatically replaces P15.

## Clinical implementation positioning

P15 is intended for EHR implementation. It is not a bedside-only manual score because it uses latest-available carry-forward laboratory variables and a shared support-intensity proxy. P12 can be discussed as a simplification candidate if clinical feature burden must be reduced. P10 should remain an ultra-minimal sensitivity option.

## Laboratory freshness

The project explicitly treats laboratory variables as latest-available / capped carry-forward values, not hourly real measurements. The 12h freshness sensitivity for P15 has eICU AUROC/AUPRC/calibration slope = 0.7847 / 0.1674 / 0.9779, which is borderline acceptable. The 24h freshness sensitivity has eICU AUROC/AUPRC/calibration slope = 0.8085 / 0.1860 / 0.9991, which is largely stable. No additional look-ahead was identified under available timestamps, but result availability time is incomplete and chart/sample time was used as a conservative approximation.

## Proxy and clinical utility boundaries

The shared support-intensity proxy is not full VIS and should be explained as a cross-database support burden proxy. DCA and first-alarm lead-time analyses are supplementary utility estimates. They support risk stratification and monitoring-escalation discussion, not automatic treatment recommendations.

## Current readiness

The repository is ready for final manuscript writing after reading the final file index and cleanup report. Archive materials are retained for audit traceability but are not the main result path.
