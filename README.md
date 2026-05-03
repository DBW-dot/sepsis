# Sepsis Dynamic Competing-risk Final Manuscript Share Repo

This is the manuscript-facing cleaned repository for the final clinically parsimonious model package.

## Final model line

- Final main clinical transport model: `P15_minimal_bedside_model`
- Feature count: 15
- eICU external AUROC/AUPRC/calibration slope: 0.8103 / 0.1892 / 1.0031
- Post-METRE transport reference: `MT3_physiology_support_proxy`
- Internal rich/reference model: `M1_original_rich`
- Clinical comparator: `C1_dynamic_SOFA`
- Phenotype: stratification / explanation / calibration audit only

## Main reading path

- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_package/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- `parsimonious_features/`

## Archive

Superseded Pre-METRE, Post-METRE transition, old figure/table interfaces, and phenotype audit materials have been moved to `archive/`. They are retained for traceability but are no longer the main manuscript path.

## Data boundary

Raw MIMIC-IV/eICU data, parquet datasets, model binaries, DuckDB databases, and runtime logs are not included in this GitHub repository. See `HEAVY_ARTIFACT_MANIFEST.csv` and `LOCAL_ASSET_INDEX.md`.

## Cleanup audit

See `cleanup/cleanup_plan.md` and `cleanup/file_action_manifest.csv` for every keep/move/delete decision.
