# Shared Support Intensity Proxy Definition

## Scope

This is a METRE-style transportable support-intensity proxy. It is **not** full VIS.

## Components

- Hemodynamic component: mean of normalized `map_deficit` and `map_below_65_burden_24h`.
- Lactate component: mean of normalized `lactate_gt2_burden_24h` and `lactate_gt4_burden_24h`.
- Renal component: mean of normalized `oliguria_burden_24h` and `worsening_renal_trajectory_flag`.
- Respiratory component: mean of normalized `high_fio2_burden_24h`, `low_spo2_burden_24h`, and `ventilation_transition_count_24h`.
- Composite: mean of available component scores.

## Explicit VIS separation

- MIMIC full VIS remains a rich internal feature family.
- eICU reduced support signal is not treated as mathematically equivalent to full VIS.
- MT3/MT4 use this shared proxy instead of full VIS.

## Proxy summary

```json
[
  {
    "dataset_name": "eicu_external",
    "row_n": 1051357,
    "missing_rate": 0.0,
    "mean_proxy": 0.04021971670369289,
    "median_proxy": 0.003472222222222222,
    "mean_component_count": 4.0
  },
  {
    "dataset_name": "mimic_internal_test",
    "row_n": 1030526,
    "missing_rate": 0.0,
    "mean_proxy": 0.0663564727301074,
    "median_proxy": 0.03125,
    "mean_component_count": 4.0
  },
  {
    "dataset_name": "mimic_train_inner",
    "row_n": 313496,
    "missing_rate": 0.0,
    "mean_proxy": 0.08110494830875034,
    "median_proxy": 0.04416666666666667,
    "mean_component_count": 4.0
  },
  {
    "dataset_name": "mimic_validation",
    "row_n": 79518,
    "missing_rate": 0.0,
    "mean_proxy": 0.08204106739634073,
    "median_proxy": 0.04513888888888889,
    "mean_component_count": 4.0
  }
]
```
