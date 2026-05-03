# Model Selection Criteria

## Priority order

1. eICU external AUPRC is the primary selection criterion.
2. eICU external AUROC is the secondary criterion.
3. eICU calibration slope must not be extreme; values close to 1 are preferred.
4. Internal performance must not collapse relative to the clinical comparator.
5. The feature set must be interpretable and cross-database stable.
6. The default transport model should not rely on high-dimensional measurement-process features or direct phenotype input.

## Frozen selections

- Best internal rich model: `M1_original_rich`.
- Best external transport model: `MT3_physiology_support_proxy`.
- Best baseline comparator: `C1_dynamic_SOFA`.

## Selection evidence

- Internal rich model MIMIC AUROC/AUPRC: 0.8706 / 0.2733.
- External transport model eICU AUROC/AUPRC/slope: 0.8090 / 0.1863 / 0.9652.
- Clinical comparator eICU AUROC/AUPRC/slope: 0.7253 / 0.0669 / 0.4919.

## Boundary rule

`MT4_support_proxy_phenotype_sensitivity` remains a sensitivity model even when AUROC is slightly higher, because the requested default transport role should not use phenotype as a direct performance driver.
