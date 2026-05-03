# eICU Recalibration Split Report

## Design

- Split level: patient-level.
- Random seed: `20260425`.
- Recalibration fraction: `0.20`.
- Stratification fields: any death window, modal phenotype label, modal `is_sepsis_on_admission`.

## Verification

- Patient overlap between recalibration and hold-out: `False`.
- Split summary:

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
