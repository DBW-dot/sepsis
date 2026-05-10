# Phenotype Role Reassessment Report

## Objective

This experiment reassessed phenotype as a potential performance driver versus a stratification, calibration, and interpretation tool.

## Verification

- P1 vs P2 internal prediction keys matched exactly: yes (`stay_id + t_pred` identical).
- P1 vs P2 external prediction keys matched exactly: yes (`stay_id + t_pred` identical).
- Assignment merge coverage and mismatch audit:

```json
[
  {
    "use_case": "P1_no_phenotype",
    "dataset_name": "internal_test",
    "row_n": 1030526,
    "unique_stay_n": 10371,
    "missing_assignment_rows": 0,
    "pred_assignment_label_mismatch_rows": 0
  },
  {
    "use_case": "P1_no_phenotype",
    "dataset_name": "external_eicu",
    "row_n": 1051357,
    "unique_stay_n": 9032,
    "missing_assignment_rows": 0,
    "pred_assignment_label_mismatch_rows": 0
  },
  {
    "use_case": "P2_phenotype_input",
    "dataset_name": "internal_test",
    "row_n": 1030526,
    "unique_stay_n": 10371,
    "missing_assignment_rows": 0,
    "pred_assignment_label_mismatch_rows": 0
  },
  {
    "use_case": "P2_phenotype_input",
    "dataset_name": "external_eicu",
    "row_n": 1051357,
    "unique_stay_n": 9032,
    "missing_assignment_rows": 0,
    "pred_assignment_label_mismatch_rows": 0
  }
]
```

## Overall performance comparison

### Internal test

- P1 no phenotype: AUROC=0.8705, AUPRC=0.2736, death Brier=0.0827, slope=0.8986
- P2 phenotype input: AUROC=0.8706, AUPRC=0.2733, death Brier=0.0823, slope=0.8957
- Delta P2 - P1: AUROC=0.000117, AUPRC=-0.000356, death Brier=-0.000406, slope=-0.002893

### External eICU

- P1 no phenotype: AUROC=0.7083, AUPRC=0.0375, death Brier=0.2664, slope=0.0728
- P2 phenotype input: AUROC=0.7090, AUPRC=0.0377, death Brier=0.2570, slope=0.0728
- Delta P2 - P1: AUROC=0.000726, AUPRC=0.000153, death Brier=-0.009449, slope=0.000006

## Does phenotype behave more like a calibration/stratification tool?

- P2 did not materially improve overall discrimination relative to P1 on either internal or external data.
- The more informative signal lies in subgroup heterogeneity:
  - Internal P1 hard-label subgroup AUPRC SD across phenotypes = 0.0211
  - Internal P2 hard-label subgroup AUPRC SD across phenotypes = 0.0205
  - External P1 hard-label subgroup AUPRC SD across phenotypes = 0.0225
  - External P2 hard-label subgroup AUPRC SD across phenotypes = 0.0224
- This pattern supports using phenotype to organize heterogeneity and calibration review rather than claiming it is a strong overall performance booster.

## Phenotype_3 diagnosis

```json
[
  {
    "use_case": "P1_no_phenotype",
    "dataset_name": "internal_test",
    "phenotype3_sample_n": 47790.0,
    "phenotype3_death_n": 1553.0,
    "phenotype3_auroc": 0.8500612782533775,
    "phenotype3_auprc": 0.31475811064751913,
    "phenotype3_brier": 0.1517474602200321,
    "phenotype3_calibration_slope": 0.9401119604459491,
    "phenotype3_confidence_mean": 0.5113863650286866
  },
  {
    "use_case": "P2_phenotype_input",
    "dataset_name": "internal_test",
    "phenotype3_sample_n": 47790.0,
    "phenotype3_death_n": 1553.0,
    "phenotype3_auroc": 0.8496192403591114,
    "phenotype3_auprc": 0.31482935526381217,
    "phenotype3_brier": 0.1832595092937173,
    "phenotype3_calibration_slope": 0.9420730414275456,
    "phenotype3_confidence_mean": 0.5113863650286866
  },
  {
    "use_case": "P1_no_phenotype",
    "dataset_name": "external_eicu",
    "phenotype3_sample_n": 60778.0,
    "phenotype3_death_n": 2575.0,
    "phenotype3_auroc": 0.7493806661619051,
    "phenotype3_auprc": 0.08493380744836096,
    "phenotype3_brier": 0.30578160689730727,
    "phenotype3_calibration_slope": 0.10103792548753825,
    "phenotype3_confidence_mean": 0.8709009625312132
  },
  {
    "use_case": "P2_phenotype_input",
    "dataset_name": "external_eicu",
    "phenotype3_sample_n": 60778.0,
    "phenotype3_death_n": 2575.0,
    "phenotype3_auroc": 0.7490880912454216,
    "phenotype3_auprc": 0.08478123024348094,
    "phenotype3_brier": 0.33719089593514906,
    "phenotype3_calibration_slope": 0.1025546428540145,
    "phenotype3_confidence_mean": 0.8709009625312132
  }
]
```

- External phenotype gain excluding Phenotype_3:
  - P1 external AUROC/AUPRC = 0.7013 / 0.0345
  - P2 external AUROC/AUPRC = 0.7015 / 0.0345
  - Delta P2 - P1 after excluding Phenotype_3: AUROC=0.000262, AUPRC=0.000023
- Excluding Phenotype_3 did not materially change the tiny overall gain, so the current reassessment does **not** support treating Phenotype_3 as the sole or dominant reason phenotype fails to improve headline performance.
- Phenotype_3 should still be discussed separately because it represents a clinically distinct subgroup with cross-database interpretive uncertainty, but this dataset alone does not justify framing it as the main transport failure.

## Membership sensitivity analysis

- This enhanced analysis was feasible because stay-level phenotype membership vectors were available for both MIMIC and eICU.
- Soft-membership P3 external summary:

```json
[
  {
    "phenotype_name": "Phenotype_1",
    "effective_sample_n": 804668.235059,
    "effective_death_n": 15560.272173,
    "auroc_death": 0.7065325818098194,
    "auprc_death": 0.03392650666479888,
    "death_brier": 0.24795617353865046,
    "calibration_slope_death": 0.07166291284000255
  },
  {
    "phenotype_name": "Phenotype_2",
    "effective_sample_n": 179736.543425,
    "effective_death_n": 4390.284095999999,
    "auroc_death": 0.6819345589518606,
    "auprc_death": 0.03808477137776946,
    "death_brier": 0.33216325255409135,
    "calibration_slope_death": 0.061673966751895216
  },
  {
    "phenotype_name": "Phenotype_3",
    "effective_sample_n": 66952.215582,
    "effective_death_n": 2642.443808,
    "auroc_death": 0.7333721705482025,
    "auprc_death": 0.07120922887963534,
    "death_brier": 0.31191615436330933,
    "calibration_slope_death": 0.08756653238276783
  }
]
```

- Soft membership did not redefine the main conclusion; it mainly smooths subgroup boundaries for interpretation.

## Conclusion

- Phenotype is not supported here as a major overall performance driver.
- The more defensible role is:
  1. heterogeneity organization,
  2. calibration and subgroup audit,
  3. explanation interface.
- Phenotype_3 should be described separately as an interpretively uncertain cross-database subgroup, but not overstated as the main cause of weak overall phenotype gain.
