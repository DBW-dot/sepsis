# Manuscript Update Notes

- Do not rewrite the cohort, anchor, or label methods.
- Add a clinical parsimony experiment that compares F15, F25, F40, and MT3 under the same MIMIC-training/eICU-external-validation design.
- The recommended parsimonious model is `P15_clinically_parsimonious_transport_model` with legacy/internal alias `P15_minimal_bedside_model`.
- Use feature-count reduction and retained vital-sign, routine-laboratory, organ-function, time-anchor, and shared support-intensity proxy variables to answer clinical implementability concerns.
- Do not describe P15 as an all-bedside or manually calculated score; it includes routine labs and the shared support-intensity proxy.
- Keep early static phenotype as stratification/explanation/calibration audit only.
- Keep MT3 as the Post-METRE transport reference, not as the final clinical model.
- Keep full VIS limited to internal-rich/sensitivity analyses and do not conflate it with the shared support-intensity proxy.
