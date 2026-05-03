# Cleanup Final Report

Generated at: 2026-05-03T12:22:28

## Final organisation actions

- Added `results_final/` as the main manuscript-facing final result layer.
- Kept backward-compatible final `results_package/text/*Final_Parsimonious.md` paths.
- Added `FINAL_PROJECT_SUMMARY.md`, `FINAL_FILE_INDEX.md`, and `archive/README_archive.md`.
- Retained historical files in `archive/` for audit rather than deleting them.
- No model retraining, cohort modification, label modification, or metric recomputation was performed.

## Copied final files

- `results_package/tables/Table1_Cohort_Characteristics.csv` -> `results_final/tables/Table1_Cohort_Characteristics.csv`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv` -> `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv` -> `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/Results_Skeleton_zh_Final_Parsimonious.md` -> `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_package/text/Discussion_Outline_zh_Final_Parsimonious.md` -> `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md` -> `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`

## Consistency checks

| Check | Pass | Details |
|---|---:|---|
| README final model is P15 | True |  |
| FINAL_PROJECT_SUMMARY final model is P15 | True |  |
| results_final does not mark MT3 as final main model | True |  |
| archive has README | True |  |
| main path has no confusing old result names | True |  |
| main path does not claim phenotype is main performance enhancer | True |  |
| main path does not write old 79-91h lead-time as strict 24h | True |  |
| main path does not conflate full VIS and support proxy | True |  |

## Overall status: PASS

The repository is now organised around `P15_minimal_bedside_model` as the final clinically parsimonious transport model.
