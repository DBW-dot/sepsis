# Sepsis Dynamic Competing-risk Final Parsimonious Manuscript Repository

## 1. Project title

Dynamic competing-risk prediction for ICU sepsis deterioration with a clinically parsimonious transport model.

## 2. Current frozen conclusion

The final manuscript-facing model is `P15_clinically_parsimonious_transport_model`, using the legacy internal alias `P15_minimal_bedside_model`. It is a 15-feature clinically parsimonious transport model, not an all-bedside manual score. It includes routine vital signs, routine laboratory values, time-anchor variables, and a shared support-intensity proxy. It replaces MT3 as the main clinical model while preserving MT3 as the Post-METRE transport reference.

最终论文主模型为 P15 临床精简迁移模型。该模型沿用历史技术名 `P15_minimal_bedside_model`，但不应理解为完全床旁人工评分；其 15 个特征包括时间锚点、常规生命体征、常规实验室指标和共享支持强度代理变量。

## 3. Final model roles

- `M1_original_rich` / display name `M1_internal_rich_reference_model` = internal rich/reference model
- `MT3_physiology_support_proxy` / display name `MT3_Post_METRE_transport_reference_model` = Post-METRE transport reference
- `P15_minimal_bedside_model` / display name `P15_clinically_parsimonious_transport_model` = final clinically parsimonious transport model
- `P25_clinical_core_model` = sensitivity model
- `P40_balanced_transport_model` = sensitivity model
- `C1_dynamic_SOFA` = clinical comparator
- `phenotype` = early static phenotype for stratification / explanation / calibration audit only

## 4. Key final metrics

- P15 feature count = 15
- P15 eICU external AUROC/AUPRC/calibration slope = 0.8103 / 0.1892 / 1.0031
- P15 external AUPRC was not lower than MT3 in the final parsimonious comparison.

## 5. What is included in this repo

- Final manuscript-facing tables and text in `results_final/`
- Backward-compatible final outputs in `results_package/`
- Final model role freeze documents in `final_freeze/`
- Parsimonious feature-set audit outputs in `parsimonious_features/`
- Cleanup and naming harmonisation reports in `cleanup/`
- Historical audit material in `archive/`
- Heavy artifact index in `HEAVY_ARTIFACT_MANIFEST.csv`

## 6. What is excluded and why

Raw MIMIC-IV/eICU data, parquet datasets, model binaries, DuckDB databases, compressed raw files, and runtime logs are excluded. This repository is a lightweight manuscript-facing share layer, not a full local computational archive.

## 7. How to read this repository

Start with:

1. `FINAL_PROJECT_SUMMARY.md`
2. `FINAL_FILE_INDEX.md`
3. `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
4. `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
5. `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
6. `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
7. `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`

## 8. Which files are final

- `results_final/`
- `final_freeze/*Parsimonious*`
- `parsimonious_features/*`
- `cleanup/cleanup_final_report.md`
- `cleanup/Final_Naming_Harmonisation_Report.md`

## 9. Which folders are archived historical materials

- `archive/legacy_pre_metre_results/`
- `archive/post_metre_reference/`
- `archive/legacy_transport_pre_metre/`
- `archive/legacy_text_and_skeletons/`
- `archive/legacy_figure_interfaces/`
- `archive/phenotype_audit/`
- `archive/legacy_scripts/`

## 10. Warning

Do not use archived pre-METRE outputs, old Step8/Step9 outputs, old lead-time/DCA interfaces, or historical phenotype-gain files as final results. They are retained only for audit and lineage. Do not describe P15 as an all-bedside or manually calculated score; do not describe MT3 as the final clinical model; do not use phenotype as a default performance driver; and do not conflate full VIS with the shared support-intensity proxy.
