# Post-METRE Recalibration Report

## Split summary

```json
[
  {
    "split": "holdout",
    "patient_n": 7004,
    "stay_n": 7214,
    "row_n": 835788,
    "death_row_n": 17984,
    "death_row_rate": 0.02151741829267709,
    "phenotype_1_rate": 0.861984139518634,
    "phenotype_2_rate": 0.08482174905598071,
    "phenotype_3_rate": 0.05319411142538538,
    "sepsis_on_admission_rate": 0.38832694415330204
  },
  {
    "split": "recalibration",
    "patient_n": 1750,
    "stay_n": 1818,
    "row_n": 215569,
    "death_row_n": 4609,
    "death_row_rate": 0.02138062522904499,
    "phenotype_1_rate": 0.8419717120736284,
    "phenotype_2_rate": 0.08232630851374734,
    "phenotype_3_rate": 0.07570197941262427,
    "sepsis_on_admission_rate": 0.38470744865913004
  }
]
```

## MT3 raw vs best recalibrated hold-out result

- Raw MT3: AUROC=0.8106, AUPRC=0.1913, death Brier=0.0977, multiclass Brier=0.5912, slope=0.9862, ECE=0.2385.
- Best MT3 method by death Brier: `intercept_only`.
- Recalibrated MT3: AUROC=0.8106, AUPRC=0.1913, death Brier=0.0191, multiclass Brier=0.4554, slope=0.9874, ECE=0.0030.

## Interpretation

- Recalibration is evaluated only on the hold-out subset.
- AUROC should remain mostly stable for monotonic calibrators; AUPRC may change slightly for isotonic because ties and stepwise mapping can affect ranking.
- The deployment question is mainly whether Brier, ECE, and calibration slope improve without damaging AUPRC.
