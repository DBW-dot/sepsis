# Transport Model Report

## Goal

This experiment trained transport-focused competing-risk models to improve eICU transportability and external calibration rather than to maximize internal-only performance.

## Final transport feature strategy

- T1 (`no phenotype`) used 29 inputs.
- T2 (`with phenotype_label`) used 30 inputs.
- Retained inputs focused on cross-database core physiology, support-intensity surrogates, alignment variables, and only minimal recency provenance.
- High-dimensional observation-process variables such as `*_measure_count_last_24h`, `*_is_observed_current_hour`, and `*_is_forward_filled` were removed.
- Highly unstable or externally sparse raw support proxies such as `ventilation_status_current`, `shock_index`, `sbp_latest_value`, `lactate_latest_value`, and `urine_output_latest_value` were removed from the transport set.

### T1 retained feature list

[
  "hours_from_anchor",
  "hours_since_icu_admission",
  "is_sepsis_on_admission",
  "hr_latest_value",
  "hr_slope_6h",
  "map_below_65_burden_24h",
  "map_deficit",
  "rr_latest_value",
  "spo2_latest_value",
  "high_fio2_burden_24h",
  "low_spo2_burden_24h",
  "ventilation_transition_count_24h",
  "lactate_gt2_burden_24h",
  "lactate_gt4_burden_24h",
  "oliguria_burden_24h",
  "creatinine_latest_value",
  "creatinine_relative_rise_from_24h_min",
  "bun_latest_value",
  "platelet_latest_value",
  "platelet_relative_drop_24h",
  "wbc_latest_value",
  "worsening_renal_trajectory_flag",
  "antibiotics_active_current",
  "culture_flag_current",
  "map_hours_since_last_real_measurement",
  "lactate_hours_since_last_real_measurement",
  "creatinine_hours_since_last_real_measurement",
  "urine_output_hours_since_last_real_measurement",
  "fio2_hours_since_last_real_measurement"
]

### T2 added feature

[
  "phenotype_label"
]

## Excluded feature groups

- Observation-process heavy features removed:
  bilirubin_total_is_forward_filled, bilirubin_total_is_observed_current_hour, bilirubin_total_measure_count_last_24h, creatinine_is_forward_filled, creatinine_is_observed_current_hour, creatinine_measure_count_last_24h, fio2_is_forward_filled, fio2_is_observed_current_hour, fio2_measure_count_last_24h, hr_is_forward_filled, hr_is_observed_current_hour, hr_measure_count_last_24h, lactate_is_forward_filled, lactate_is_observed_current_hour, lactate_measure_count_last_24h, map_is_forward_filled, map_is_observed_current_hour, map_measure_count_last_24h, platelet_is_forward_filled, platelet_is_observed_current_hour
- High-missingness / unstable raw signals removed:
  bilirubin_slope_24h, bilirubin_total_latest_value, fio2_latest_value, lactate_latest_value, lactate_slope_6h, map_latest_value, map_slope_6h, pao2_fio2_ratio, sbp_latest_value, shock_index, shock_index_slope_6h, spo2_fio2_ratio, temperature_latest_value, urine_output_latest_value

## Training design

- Base learner: regularized multinomial logistic regression with balanced class weights.
- Development split used for this transport experiment:
  - `train_inner` for fitting
  - `validation` for regularization and temperature selection
- Selection criterion: lowest validation multiclass Brier score after temperature scaling, with tie-break on death AUPRC.
- Selected hyperparameters:
  - T1: `C=1.0`, `temperature=1.100`
  - T2: `C=0.03`, `temperature=1.100`

## Validation snapshot

- T1 validation metrics: {"sample_n": 79518.0, "death_n": 4091.0, "death_ratio": 0.051447471012852436, "auroc_death_ovr": 0.8664321062824598, "auprc_death": 0.39243245109924413, "multiclass_brier": 0.5343386214946301, "calibration_intercept_death": -2.4824112856226397, "calibration_slope_death": 0.9514051448893734}
- T2 validation metrics: {"sample_n": 79518.0, "death_n": 4091.0, "death_ratio": 0.051447471012852436, "auroc_death_ovr": 0.8672995444299382, "auprc_death": 0.38966041119392436, "multiclass_brier": 0.5322972607516533, "calibration_intercept_death": -2.5009291468565014, "calibration_slope_death": 0.9314648362868431}

## Internal vs external comparison

### M1 baseline

- Internal test: AUROC=0.8706, AUPRC=0.2733, multiclass Brier=0.4672, calibration slope=0.8957
- eICU external: AUROC=0.7090, AUPRC=0.0377, multiclass Brier=0.8788, calibration slope=0.0728

### T1 (no phenotype)

- Internal test: AUROC=0.8399, AUPRC=0.1984, multiclass Brier=0.5410, calibration slope=0.9063
- eICU external: AUROC=0.7591, AUPRC=0.0519, multiclass Brier=0.8149, calibration slope=0.1643
- External delta vs M1: ΔAUPRC=0.0143, Δslope=0.0914

### T2 (with phenotype_label)

- Internal test: AUROC=0.8424, AUPRC=0.2021, multiclass Brier=0.5386, calibration slope=0.9120
- eICU external: AUROC=0.7620, AUPRC=0.0531, multiclass Brier=0.8211, calibration slope=0.1647
- External delta vs M1: ΔAUPRC=0.0154, Δslope=0.0919

## Interpretation

- The transport revision directly tests whether removing observation-process-heavy variables improves external transportability.
- T1 is the primary transport candidate because it does not rely on phenotype.
- T2 isolates whether phenotype still adds value once the model is already transport-constrained.
- A model should only be considered for deployment-oriented reporting if it materially improves eICU AUPRC and external calibration slope without catastrophic internal collapse.

## Recommendation

- Recommend transport model as main deployed model: **yes**
- Practical reading:
  - If `yes`, the transport model is a strong candidate for deployment-oriented emphasis because it improves external discrimination and calibration.
  - If `no`, it is still worth keeping as a transport-focused supplementary model that explicitly shows the internal-versus-transport tradeoff.
