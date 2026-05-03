# Recalibration Targets

## Frozen calibration target

- Best transport model: `MT3_physiology_support_proxy`.
- Model bundle: `C:\Users\GUO\Desktop\try\metre_transport\model_MT3_physiology_support_proxy.pkl`.
- Generated prediction file for this run: `post_metre_recalibration/pred_MT3_eicu_external.parquet`.

## Comparators

- M1: `C:\Users\GUO\Desktop\try\step7_main_modeling\output\pred_main_eicu_external.parquet`.
- C1: `C:\Users\GUO\Desktop\try\step7_main_modeling\output\pred_C1_eicu_external.parquet`.

## Boundary

- No model retraining was performed.
- eICU was used only for local recalibration fitting and untouched hold-out evaluation.
- Death probability was calibrated first; discharge/no-event probabilities were rescaled proportionally to keep three-class probabilities coherent.
