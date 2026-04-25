# METRE Transport Model Report

## Training design

- Training source: MIMIC `train_inner` only.
- Validation source: MIMIC `validation` only.
- External evaluation: eICU only, never used for fitting, imputation, scaling, encoding, or model selection.
- Model family: regularized multinomial logistic regression with balanced class weights and validation-selected temperature scaling.
- Outcome: three-class competing-risk label (`ICU_DEATH`, `ALIVE_DISCHARGE`, `NO_EVENT`).

## METRE model definitions

- MT1: transport physiology plus temporal anchor context.
- MT2: MT1 plus minimal recency/provenance features.
- MT3: MT1 plus shared support-intensity proxy.
- MT4: MT3 plus `phenotype_label` sensitivity.

## External comparison snapshot

- M1 original rich external AUROC/AUPRC/slope: 0.7090 / 0.0377 / 0.0728
- MT1 external AUROC/AUPRC/slope: 0.7634 / 0.1329 / 0.9984
- MT2 external AUROC/AUPRC/slope: 0.7704 / 0.0993 / 0.6418
- MT3 external AUROC/AUPRC/slope: 0.8090 / 0.1863 / 0.9652
- MT4 external AUROC/AUPRC/slope: 0.8111 / 0.1813 / 0.9127

## Best external model by AUROC/AUPRC

- Best default METRE model: `MT3_physiology_support_proxy`
- eICU AUROC=0.8090
- eICU AUPRC=0.1863
- eICU calibration slope=0.9652
- Best sensitivity model including MT4: `MT4_support_proxy_phenotype_sensitivity` with AUROC=0.8111, AUPRC=0.1813, slope=0.9127

## Interpretation

- METRE-style restriction reduced dependence on high-dimensional observation-process features.
- The shared support proxy must be interpreted as a cross-database support signal, not a replacement for full VIS.
- MT4 tests phenotype sensitivity only; phenotype is not promoted to the default transport model even when AUROC changes slightly.
