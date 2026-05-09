# Clinical Implementation Notes - Final

## Scope

This file integrates the P15/P12/P10 clinical implementation analysis into the final result package. It does not retrain any model, alter labels, alter Step 1-8 outputs, alter the Sepsis-3 cohort definition, or change the P15 feature set.

## Final model status

- Main validated model remains `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias remains `P15_minimal_bedside_model`.
- Final 15-feature set display name remains `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias remains `F15_minimal_bedside_set`.
- P15 eICU AUROC/AUPRC/calibration slope remain 0.8103 / 0.1892 / 1.0031.

## Clinical implementation roles

- P15: formal main result model and validated reference.
- P12: clinical implementation simplification candidate, labelled as simulated sensitivity only.
- P10: ultra-minimal sensitivity scenario, labelled as simulated sensitivity only.
- Proxy dual-index explanation: `shared_support_intensity_proxy + support_lactate_component` for clinical communication.

## Key simulated tradeoffs

- P12 AUPRC drop vs P15: 7.66%.
- P10 AUPRC drop vs P15: 12.69%.
- P12 is preferred if simplification is needed because it preserves lactate/perfusion interpretability.
- P10 is lowest burden but should not replace P15.

## Wording guardrails

- Do not call P12 or P10 newly trained models.
- Do not describe P12 as the formal main model.
- Do not conflate full VIS with `shared_support_intensity_proxy`.
- Do not frame DCA or lead-time outputs as automatic intervention triggers.
- Use P10/P12 only in supplementary, implementation, or sensitivity framing.
