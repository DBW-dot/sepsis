# Final Parsimonious Model Recommendation

- Recommended clinical landing model: `P15_minimal_bedside_model`.
- Recommended feature set: `F15_minimal_bedside_set` (15 features).
- eICU AUROC/AUPRC/slope: 0.8103 / 0.1892 / 1.0031.
- MT3 reference eICU AUROC/AUPRC/slope: 0.8090 / 0.1863 / 0.9652.
- AUPRC drop vs MT3: -1.54%.
- Main-text replacement recommendation: True.
- Reason: accepted by noninferiority thresholds with the smallest feature count.

MT3 should remain as the performance upper-bound reference unless the selected parsimonious model is accepted as the main clinical model.
