# Final Naming Harmonisation Report

Generated at: 2026-05-03T12:49:25

## Scope

This step only harmonised manuscript-facing names and wording. It did not retrain models, modify feature sets, alter cohorts, change labels, or edit any performance metrics.

## Naming decisions

- `P15_minimal_bedside_model` is retained as a legacy/internal alias.
- Manuscript-facing P15 name: `P15_clinically_parsimonious_transport_model` / P15 临床精简迁移模型.
- `F15_minimal_bedside_set` is retained as a legacy feature-set ID.
- Manuscript-facing F15 name: `F15_clinically_parsimonious_feature_set` / F15 临床精简特征集.
- MT3 is displayed as `MT3_Post_METRE_transport_reference_model`, not the final clinical model.
- Phenotype is retained only as an early static phenotype for stratification, explanation, and calibration audit.
- Full VIS and the shared support-intensity proxy are separated explicitly.

## Modified files

- `FINAL_FILE_INDEX.md`
- `FINAL_PROJECT_SUMMARY.md`
- `README.md`
- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Assignment_Parsimonious.csv`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `parsimonious_features/F15_minimal_bedside_set.csv`
- `parsimonious_features/F25_clinical_core_set.csv`
- `parsimonious_features/F40_balanced_transport_set.csv`
- `parsimonious_features/Feature_Retention_Rationale.csv`
- `parsimonious_features/Final_Parsimonious_Model_Recommendation.md`
- `parsimonious_features/Manuscript_Update_Notes.md`
- `parsimonious_features/Noninferiority_Assessment.csv`
- `parsimonious_features/Parsimonious_Model_Comparison.csv`
- `parsimonious_features/Parsimonious_Model_Report.md`
- `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- `results_package/text/Results_Skeleton_zh_Final_Parsimonious.md`

## Consistency checks

| Check | Pass |
|---|---|
| README updated | True |
| P15 unified as clinically parsimonious transport model | True |
| Legacy alias preserved | True |
| No misleading bedside-only expression remains | True |
| MT3 unified as Post-METRE reference | True |
| Phenotype downgraded to stratification/explanation/calibration audit | True |
| Full VIS and shared support-intensity proxy separated | True |
| Lead-time terminology clean | True |

## Residual risk findings in main path

No unallowed risk expressions were found in the non-archive main path.

## Verification summary

- Legacy IDs remain available for auditability.
- Display names are now separated from legacy/internal aliases.
- No CSV metric columns were recalculated or edited by value.
