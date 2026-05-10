# Supplementary P12/P10 Implementation Validation

## Why true-training validation was needed

Earlier P12/P10 versions were implementation sensitivity estimates. True-training validation was needed to determine whether simplified candidates retained transport performance when trained under the same MIMIC-only development boundary.

## Training and validation boundary

P12 and P10 were true-trained on MIMIC train only. eICU was used only for external validation and did not participate in training or tuning.

## P12 result

P12 eICU AUROC/AUPRC/calibration slope was 0.8038 / 0.1767 / 1.0100. Relative AUPRC drop vs P15 was 6.5828%. P12 is a validated simplified implementation candidate.

## P10 result

P10 eICU AUROC/AUPRC/calibration slope was 0.7978 / 0.1711 / 1.0133. Relative AUPRC drop vs P15 was 9.5577%. P10 is a validated ultra-minimal sensitivity candidate.

## Why P12/P10 do not replace P15

P15 remains the final manuscript-facing main model. P12/P10 are useful for implementation and sensitivity discussions, but replacing P15 would require a separate final model refreeze decision.

## Recommended manuscript placement

P12/P10 should be presented in supplementary or implementation analysis sections, not as the primary model.
