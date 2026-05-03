# METRE Transport Final Recommendation

## Required answers

1. Did the METRE transport feature set reduce external AUROC/AUPRC drift?
   - AUROC drift reduction: `True`.
   - Original M1 AUROC drop: 0.1616.
   - Best METRE AUROC drop: -0.0037.

2. Did the shared support-intensity proxy mitigate full VIS to reduced proxy information degradation?
   - Support proxy helped relative to MT1: `True`.
   - MT1 eICU AUROC/AUPRC: 0.7634 / 0.1329.
   - MT3 eICU AUROC/AUPRC: 0.8090 / 0.1863.

3. Did minimal recency improve or harm external transport?
   - Minimal recency AUROC improved relative to MT1: `True`.
   - Minimal recency AUPRC improved relative to MT1: `False`.
   - MT2 eICU AUROC/AUPRC: 0.7704 / 0.0993.
   - Interpretation: minimal recency is mixed if AUROC and AUPRC move in opposite directions.

4. Did phenotype_label still show limited gain?
   - Phenotype sensitivity AUROC improved relative to MT3: `True`.
   - Phenotype sensitivity AUPRC improved relative to MT3: `False`.
   - MT4 eICU AUROC/AUPRC: 0.8111 / 0.1813.
   - Best sensitivity model by AUROC/AUPRC: `MT4_support_proxy_phenotype_sensitivity`.
   - Interpretation: phenotype remains a sensitivity/stratification variable because MT4 is not the default METRE transport model and does not improve AUPRC over MT3.

5. Which model is most suitable as the manuscript external transport model?
   - Recommended transport model: `MT3_physiology_support_proxy`.
   - Rationale: selected among default METRE models MT1-MT3 by external AUROC with AUPRC tie-break, while keeping full VIS and direct phenotype input out of the default transport path.

6. Should original M1 be positioned as an internal rich model?
   - Yes. Original M1 retains the strongest rich internal framing and should not be described as naturally transportable without qualification.
   - M1 internal AUROC/AUPRC: 0.8706 / 0.2733.
   - M1 external AUROC/AUPRC: 0.7090 / 0.0377.
