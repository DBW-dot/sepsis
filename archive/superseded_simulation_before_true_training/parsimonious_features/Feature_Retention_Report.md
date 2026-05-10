# Feature Retention Report

This audit combines clinical interpretability, MIMIC/eICU availability, and regularized model coefficient ranks. Coefficient ranks were used only as supporting evidence, not as a mechanical feature selector.

- Candidate feature count: F15=15, F25=25, F40=40, MT3=21.
- Excluded by design: phenotype label, measurement-intensity variables, full VIS, and non-transportable high-dimensional derivatives.
- Existing cohort, dual-anchor logic, Sepsis-3 suspected infection layer, and 24h competing-risk label were not modified.
