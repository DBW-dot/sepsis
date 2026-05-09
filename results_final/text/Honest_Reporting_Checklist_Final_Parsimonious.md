# Honest Reporting Checklist - Final Parsimonious

- `P15_clinically_parsimonious_transport_model` is the final manuscript-facing model.
- `P15_minimal_bedside_model` is retained only as a legacy/internal alias.
- P15 is EHR-implementable but not a bedside-only manual score.
- P15 includes time anchors, routine vital signs, routine laboratory variables, and shared support-intensity proxy variables.
- P12 and P10 are implementation sensitivity estimates, not validated replacement models.
- P12 is a clinical simplification candidate, not the formal main model.
- P10 is an ultra-minimal sensitivity scenario, not the formal main model.
- shared support-intensity proxy should be explained as a cross-database support burden proxy, not full VIS.
- Proxy components require clear clinical interpretation before deployment.
- Clinical implementation still requires local EHR mapping and prospective validation.
- MT3 remains the Post-METRE transport reference, not the final clinical model.
- M1 remains an internal rich/reference model, not the external transport model.
- Phenotype is a stratification / explanation / calibration audit tool, not a default performance driver.
- DCA and lead-time outputs should be framed as risk stratification evidence, not automatic intervention triggers.
- Strict 24h first-alarm lead-time and exploratory eventual-death lead-time must be described separately.
- Do not hide unfavorable sensitivity results, including weaker calibration or AUPRC drops in non-final feature sets.
