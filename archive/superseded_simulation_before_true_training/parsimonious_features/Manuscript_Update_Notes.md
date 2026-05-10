# Manuscript Update Notes

- Do not rewrite the cohort, anchor, or label methods.
- Add a clinical parsimony experiment that compares F15, F25, F40, and MT3 under the same MIMIC-training/eICU-external-validation design.
- The recommended parsimonious model is `P15_minimal_bedside_model` with 15 features.
- Use feature-count reduction and retained bedside/core organ-function variables to answer clinical implementability concerns.
- Keep phenotype as stratification/interpretation only and keep MT3 as a performance upper-bound reference if parsimony costs are material.
