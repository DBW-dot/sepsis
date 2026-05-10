# Recalibration Methods Summary

## Methods tested

- `raw`: original uncalibrated probabilities.
- `intercept_only`: logistic intercept update with slope fixed at 1.
- `logistic_recalibration`: logistic recalibration with intercept and slope.
- `isotonic`: monotonic non-parametric calibration.
- `temperature_scaling`: one-parameter logit temperature scaling optimized on recalibration death Brier.

## Competing-risk probability handling

The calibration target is `predicted_prob_death_24h`. After death-risk recalibration, the remaining probability mass is assigned to alive discharge and no event in proportion to their original probabilities. This preserves probability sums while avoiding three separate one-vs-rest calibrators that could break the competing-risk simplex.
