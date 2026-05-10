# eICU Recalibration Split Definition

## Design

- Split target: eICU external validation cohort only.
- Split level: patient-level.
- Random seed: `20260421`.
- Recalibration patient fraction: `0.20`.
- Stratification rule: patients were stratified by whether they had any 24h ICU-death window before splitting.

## Verification

- Patient overlap between recalibration and hold-out subsets: `False`.
- The same patient-level split was reused for M1, T1, and T2 to keep the comparison fair.

## Split summary

```json
[
  {
    "split": "holdout",
    "patient_n": 7003,
    "stay_n": 7231,
    "row_n": 836256,
    "death_row_n": 18033,
    "death_row_rate": 0.021563970841464816,
    "patients_with_any_death_window": 893
  },
  {
    "split": "recalibration",
    "patient_n": 1751,
    "stay_n": 1801,
    "row_n": 215101,
    "death_row_n": 4560,
    "death_row_rate": 0.021199343564186127,
    "patients_with_any_death_window": 223
  }
]
```

## Rationale

- The recalibration subset is intentionally smaller than the hold-out set because this experiment asks whether a limited local sample can rescue external usability.
- Hold-out evaluation was kept entirely untouched during calibration fitting to avoid optimistic bias.
