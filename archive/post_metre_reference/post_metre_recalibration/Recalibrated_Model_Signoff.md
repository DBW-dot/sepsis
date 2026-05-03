# Recalibrated Model Sign-off

## Required decisions

1. Recalibration materially improved calibration slope: `False`.
   - Raw slope was already near 1, so the main gain is calibration level rather than slope.
2. Recalibration improved death Brier: `True`.
3. Recalibration preserved or improved AUPRC: `True`.
4. Uncalibrated and recalibrated external results should be shown side by side: `True`.
5. Downstream DCA should use recalibrated probabilities: `True`.

## Frozen recommendation

- Best method: `intercept_only`.
- Raw MT3 AUROC/AUPRC/slope: 0.8106 / 0.1913 / 0.9862.
- Recalibrated MT3 AUROC/AUPRC/slope: 0.8106 / 0.1913 / 0.9874.
- Raw vs recalibrated death Brier/ECE: 0.0977/0.2385 -> 0.0191/0.0030.
- The model should be described as requiring local recalibration before deployment because the recalibration step is now part of the externally usable risk framework.
