# FINAL MANUSCRIPT HANDOFF INDEX

## Abstract should cite

- External transport performance: `results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv`.
- Key improvement lineage: `results_package/POST_METRE_RESULT_LINEAGE.csv`.
- Final model role: `final_freeze/Final_Model_Role_Audit.md`.

## Results should cite

- Table 2: `results_package/tables/Table2_Main_Model_Comparators_Post_METRE.csv`.
- Table 3: `results_package/tables/Table3_Phenotype_Gain_Post_METRE.csv`.
- Table 4: `results_package/tables/Table4_Measurement_Bias_Post_METRE.csv`.
- Figure 5 data: `results_package/figures/Figure5_DCA_Leadtime_Post_METRE.csv`.
- Figure 6 data: `results_package/figures/Figure6_External_Failure_Modes_Post_METRE.csv`.
- Narrative scaffold: `results_package/text/Results_Skeleton_zh_Post_METRE.md`.

## Discussion should emphasize

- M1 is internal rich model, not external transport model.
- MT3_physiology_support_proxy is the frozen external transport model.
- External deployment should require local recalibration.
- Strict 24h lead-time replaces old non-strict/eventual-style lead-time.
- DCA supports risk stratification, not automatic intervention triggering.
- Phenotype is a stratification/explanation/calibration audit tool, not a main performance driver.
- Full VIS and shared support-intensity proxy must remain separate concepts.
- Measurement intensity features are excluded from final transport feature set.

## Negative results that must remain

- MT3 internal performance is lower than M1.
- Local recalibration is required for deployment-ready probability scale.
- Phenotype_label and soft membership do not improve final external transport performance.
- Phenotype_3 remains weak-transfer/lower-certainty.
- Full VIS is internal-only.
- Full quality and measurement intensity harm external transport.
- Dynamic OASIS remains unavailable.

## Exploratory / sensitivity only

- Eventual-death lead-time from `Figure5_DCA_Leadtime_Post_METRE.csv`.
- MT4 phenotype sensitivity model.
- Full VIS internal-only sensitivity model.
- Historical pre-METRE Step8/Step9 outputs.
