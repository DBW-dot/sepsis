# Supplementary Bootstrap CI Methods

## Rationale

Prediction rows are serially correlated within patients or ICU stays. Therefore, 95% confidence intervals were generated using patient-level or cluster-level nonparametric bootstrap rather than independent patient-hour row-level bootstrap.

## Bootstrap unit

For each dataset, the script selected the first available cluster identifier in this order: patient-level identifiers first (`patient_id`, `subject_id`, `uniquepid`, `patienthealthsystemstayid`) and stay-level identifiers second (`stay_id`, `patientunitstayid`, `icustay_id`, `hadm_id`). When only stay-level identifiers are available, the output table records that stay-level cluster bootstrap was used.

## Resampling

- Resamples requested: `1000`.
- Random seed: `20260511`.
- Each resample draws clusters with replacement and includes all prediction rows belonging to sampled clusters.
- Direct row-level bootstrap was not used.

## Metrics

- AUROC: death vs non-death one-vs-rest.
- AUPRC: death-class average precision.
- Death Brier score: mean squared error for death probability.
- Multiclass Brier score: sum of squared error over death, alive discharge/transfer, and continued-stay probabilities.
- Calibration slope/intercept: logistic calibration model `observed_death ~ logit(predicted_death_probability)`, with probabilities clipped to `[1e-6, 1 - 1e-6]`.
- ECE: weighted 10-bin expected calibration error for death probability.

## Skipped resamples

Bootstrap resamples with only one death-class category were skipped for AUROC, AUPRC, and calibration metrics. Skip counts are recorded in the CI tables.

## CI method

The 95% interval is the percentile interval using the 2.5th and 97.5th percentiles of valid bootstrap estimates.

## Point estimates

Published point estimates remain the previously frozen authoritative values. Bootstrap recomputation is used only to estimate uncertainty and does not change model ranking, model roles, or the frozen model hierarchy.

## Model role guardrails

P15 remains the formal main manuscript-facing model. P12 and P10 remain true-trained implementation/sensitivity candidates and do not replace P15. Laboratory values remain latest-available / capped carry-forward values rather than hourly laboratory measurements. The shared support-intensity proxy is not full VIS. DCA and lead-time outputs are not intervention triggers.
