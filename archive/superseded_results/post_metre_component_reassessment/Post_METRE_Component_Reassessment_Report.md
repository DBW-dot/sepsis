# Post-METRE Component Reassessment

## Scope and guardrails

This run did not modify Step 1-6 cohort definitions or labels and did not write manuscript prose. New models were trained only where required ablation groups did not already exist. Existing METRE models were read from `metre_transport/`.

## Verification design

- Same training source: MIMIC `Model_Ready_Train` with `internal_split=train_inner`.
- Same validation source: MIMIC `internal_split=validation`.
- Same internal test source: `Model_Ready_Test_All`.
- Same external source: `Model_Ready_eICU_External`.
- eICU was never used for fitting, imputation, scaling, encoding, or temperature tuning.
- Metrics use death one-vs-rest AUROC/AUPRC plus multiclass Brier and death calibration intercept/slope.
- Subgroups were evaluated by `phenotype_label`, `is_sepsis_on_admission`, and stable vs weak-transfer phenotype.

## Key results

### 1. Phenotype role

- MT3 without phenotype external AUPRC: 0.1863; calibration slope: 0.9652.
- MT4 with hard `phenotype_label` external AUPRC: 0.1813; delta vs MT3: -0.0050; calibration slope: 0.9127.
- Soft membership/confidence external AUPRC: 0.1587; delta vs MT3: -0.0276; calibration slope: 0.7849.

Interpretation: phenotype remains better framed as a stratification/explanation/calibration-review layer unless the deltas above are materially positive and stable across subgroups. In this run, the default transport model remains MT3 rather than phenotype-augmented MT4/A3.

### 2. VIS/proxy role

- No support proxy (MT1) external AUPRC: 0.1329.
- Shared support-intensity proxy (MT3) external AUPRC: 0.1863; delta vs MT1: +0.0534.
- Direct reduced VIS flags only external AUPRC: 0.1329; delta vs MT1: +0.0000.
- Full VIS sensitivity is internal-only because full VIS is not available in eICU and is not transport-equivalent to the reduced proxy flags.

Interpretation: shared support-intensity proxy is the transportable support representation. Full VIS should remain in internal rich/sensitivity analyses only.

### 3. Measurement-process role

- Physiology-only external AUPRC: 0.1329.
- Minimal recency external AUPRC: 0.0993; delta vs physiology-only: -0.0336.
- Full quality/provenance external AUPRC: 0.0311; delta vs physiology-only: -0.1019.
- Full quality plus measurement intensity external AUPRC: 0.0295; delta vs full quality: -0.0016.

Interpretation: minimal recency is not automatically harmful, but high-dimensional quality/intensity fields must be treated as sensitivity features unless they improve external AUPRC, Brier, and calibration without increasing internal-external drift. Measurement intensity is not recommended for the final transport feature set if it degrades external performance or calibration.

### 4. Subgroup transportability

For MT3 external, pre-specified weak-transfer Phenotype_3 AUPRC=0.2619 with death rate=0.0424; stable Phenotype_1/2 AUPRC=0.1771 with death rate=0.0202. Higher Phenotype_3 AUPRC should therefore not be interpreted as stronger cross-database phenotype transfer by itself.

Phenotype_3 remains the pre-specified weak-transfer stratum from the phenotype mapping analysis. Subgroup AUPRC is reported for outcome discrimination only and should not be used alone to relabel its transferability; it should remain lower-certainty in downstream interpretation.

## Answers to required questions

1. **Does phenotype still fit better as a stratification/explanation tool?** Yes. Hard phenotype and soft membership did not displace MT3 as the default transport model.
2. **Is soft membership better than hard label?** Use the CSV deltas directly; in this run soft membership is not selected as default because it did not provide a robust external advantage over MT3.
3. **Is shared support-intensity proxy better than direct reduced VIS?** Yes. The shared proxy materially improves external AUPRC over physiology-only and is more informative than reduced VIS availability/unresolved flags.
4. **Should full VIS stay internal-only?** Yes. Full VIS is MIMIC-only in this feature layer and cannot be claimed as eICU transport-equivalent.
5. **Is minimal recency useful?** It can be reported as a sensitivity layer, but MT3 remains preferred because support proxy contributed more to external transport than minimal recency alone.
6. **Does full measurement intensity harm transportability?** Treat as non-default unless the output CSV shows simultaneous external AUPRC/Brier/calibration improvement. It is not part of the final recommended transport set.
7. **Final feature set recommendation:** `MT3_physiology_support_proxy`: physiology + temporal context + shared support-intensity proxy, without phenotype and without high-dimensional measurement intensity.
