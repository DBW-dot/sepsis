# Post-METRE Model Sign-off Report

## Final model roles

```json
[
  {
    "model_name": "M1_original_rich",
    "display_model_name": "M1_main_competing_risk",
    "assigned_role": "Internal rich model",
    "selected_as_best_internal_rich": 1,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 0,
    "rationale": "Highest MIMIC internal performance but poor eICU transport and calibration; use as internal rich/reference model."
  },
  {
    "model_name": "C1_dynamic_SOFA",
    "display_model_name": "C1_dynamic_SOFA_only",
    "assigned_role": "Clinical score comparator",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 1,
    "rationale": "Prespecified dynamic SOFA-only clinical comparator."
  },
  {
    "model_name": "C3_no_phenotype",
    "display_model_name": "C3_no_phenotype",
    "assigned_role": "Sensitivity model",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 0,
    "rationale": "No-phenotype sensitivity model for phenotype role audits."
  },
  {
    "model_name": "MT1_physiology_only",
    "display_model_name": "MT1_physiology_only",
    "assigned_role": "Sensitivity model",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 0,
    "rationale": "Minimal METRE physiology transport baseline; useful for support proxy contribution analysis."
  },
  {
    "model_name": "MT2_physiology_minimal_recency",
    "display_model_name": "MT2_physiology_minimal_recency",
    "assigned_role": "Discarded / not recommended",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 0,
    "rationale": "Minimal recency improved AUROC over MT1 but reduced AUPRC and calibration slope, so it is not the frozen transport model."
  },
  {
    "model_name": "MT3_physiology_support_proxy",
    "display_model_name": "MT3_physiology_support_proxy",
    "assigned_role": "External transport model",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 1,
    "selected_as_baseline_comparator": 0,
    "rationale": "Best default METRE transport model by eICU AUPRC/AUROC with strong calibration and no direct phenotype input."
  },
  {
    "model_name": "MT4_support_proxy_phenotype_sensitivity",
    "display_model_name": "MT4_support_proxy_phenotype_sensitivity",
    "assigned_role": "Sensitivity model",
    "selected_as_best_internal_rich": 0,
    "selected_as_external_transport": 0,
    "selected_as_baseline_comparator": 0,
    "rationale": "Phenotype sensitivity model; not default because phenotype gain remains limited and AUPRC is below MT3."
  }
]
```

## Sign-off decision

- Frozen external transport model: `MT3_physiology_support_proxy`.
- Frozen internal rich model: `M1_original_rich`.
- Frozen clinical comparator: `C1_dynamic_SOFA`.

## Why MT3 is selected over MT4

- MT4 has slightly higher eICU AUROC (0.8111 vs MT3 0.8090).
- MT3 has higher eICU AUPRC (0.1863 vs MT4 0.1813).
- MT3 avoids direct phenotype input, preserving phenotype as stratification/sensitivity rather than default performance driver.

## Why M1 is not the external transport model

- M1 remains strongest internally: MIMIC AUROC/AUPRC 0.8706 / 0.2733.
- M1 has poor external transport: eICU AUROC/AUPRC/slope 0.7090 / 0.0377 / 0.0728.
- Therefore M1 is signed off as an internal rich model, not as the default external transport model.

## Downstream analysis map

```json
[
  {
    "downstream_analysis": "External recalibration",
    "primary_model_to_use": "MT3_physiology_support_proxy",
    "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
    "reason": "Recalibration should be rerun on the frozen transport model while retaining M1/C1 for contrast."
  },
  {
    "downstream_analysis": "DCA",
    "primary_model_to_use": "MT3_physiology_support_proxy",
    "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
    "reason": "Clinical utility should be reassessed using the model selected for external transport."
  },
  {
    "downstream_analysis": "strict 24h lead-time",
    "primary_model_to_use": "MT3_physiology_support_proxy",
    "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
    "reason": "Lead-time should use the frozen external transport model and compare against prior main and SOFA baselines."
  },
  {
    "downstream_analysis": "phenotype gain reassessment",
    "primary_model_to_use": "MT3_physiology_support_proxy vs MT4_support_proxy_phenotype_sensitivity",
    "comparison_models": "C3_no_phenotype",
    "reason": "Phenotype should remain a sensitivity/stratification question, not a default driver."
  },
  {
    "downstream_analysis": "VIS/proxy contribution analysis",
    "primary_model_to_use": "MT1_physiology_only vs MT3_physiology_support_proxy",
    "comparison_models": "M1_original_rich",
    "reason": "This isolates the shared support proxy contribution and keeps full VIS framed as internal rich information."
  },
  {
    "downstream_analysis": "final result tables",
    "primary_model_to_use": "MT3_physiology_support_proxy",
    "comparison_models": "M1_original_rich; C1_dynamic_SOFA; MT4_support_proxy_phenotype_sensitivity",
    "reason": "Final tables should show M1 as internal rich, MT3 as transport, C1 as comparator, and MT4 as sensitivity only."
  }
]
```
