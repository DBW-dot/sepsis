# eICU External Recalibration Report

## Objective

This experiment tested whether the existing risk models can become externally usable in eICU through local recalibration, without redesigning the underlying models.

## Split strategy

- Patient-level split with death-window stratification.
- Recalibration subset size and hold-out size:

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

## Recalibration methods

- `raw`: no recalibration, used as the hold-out baseline.
- `intercept_only`: keeps the original slope and estimates only a local intercept shift on the recalibration subset.
- `logistic_recalibration`: estimates both intercept and slope on the logit of the raw death probability.
- `isotonic`: non-parametric monotonic calibration on death probability.

## Multi-class competing-risk handling

- Calibration fitting focused on death probability because deployment concern was dominated by death-risk miscalibration.
- To preserve a coherent 3-class competing-risk output after recalibrating death risk, the remaining probability mass `1 - p_death_calibrated` was reassigned to `ALIVE_DISCHARGE` and `NO_EVENT` in proportion to their original model outputs.
- We deliberately did **not** fit three independent one-vs-rest calibrators because that would break the probability simplex and create incoherent competing-risk outputs.

## Hold-out results summary

- M1: raw slope=0.0743, best method=`isotonic` -> slope=1.1653, AUPRC 0.0384->0.0448, death Brier 0.2582->0.0208.
- T1: raw slope=0.1572, best method=`logistic_recalibration` -> slope=0.7325, AUPRC 0.0524->0.0524, death Brier 0.2186->0.0217.
- T2: raw slope=0.1573, best method=`logistic_recalibration` -> slope=0.7191, AUPRC 0.0534->0.0535, death Brier 0.1910->0.0219.

## Best methods by model

- M1 best method: `isotonic`.
- T1 best method: `logistic_recalibration`.
- T2 best method: `logistic_recalibration`.

## Interpretation

- Recalibration cannot rescue discrimination if the raw ranking is poor; AUROC and AUPRC should therefore be interpreted mainly as transport constraints, not calibration-only effects.
- The main question is whether local recalibration materially improves death-risk calibration slope/intercept and Brier loss on the untouched hold-out set.
- If a model still needs recalibration to become usable, it should be described as `requires local recalibration before deployment`.

## Best overall hold-out configuration

- Best overall combination by death Brier on hold-out: model `M1` with method `isotonic`.
- Hold-out AUROC=0.7260
- Hold-out AUPRC=0.0448
- Hold-out death Brier=0.0208
- Hold-out calibration intercept=0.6008
- Hold-out calibration slope=1.1653

## Deployment wording recommendation

- Should the manuscript describe the framework as requiring local recalibration before deployment? **yes**
- Reason: the raw external calibration failure is large enough that even when discrimination is acceptable, safe deployment should assume a site-specific recalibration step.
