# Final Parsimonious Model Recommendation

- Recommended clinical transport model: `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias: `P15_minimal_bedside_model`.
- Recommended feature set display name: `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias: `F15_minimal_bedside_set` (15 features).
- eICU AUROC/AUPRC/slope: 0.8103 / 0.1892 / 1.0031.
- MT3 reference display name: `MT3_Post_METRE_transport_reference_model`.
- MT3 legacy ID: `MT3_physiology_support_proxy`.
- MT3 reference eICU AUROC/AUPRC/slope: 0.8090 / 0.1863 / 0.9652.
- AUPRC drop vs MT3: -1.54%.
- Main-text replacement recommendation: True.
- Reason: accepted by noninferiority thresholds with the smallest feature count.

P15 should be described as a clinically parsimonious transport model, not as an all-bedside or manually calculated score. It includes routine vital signs, routine laboratory variables, time anchors, and a shared support-intensity proxy.

MT3 should remain as the Post-METRE transport reference and performance comparator after P15 is accepted as the main clinically parsimonious model.
