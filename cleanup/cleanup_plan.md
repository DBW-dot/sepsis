# Repository Cleanup Plan - Final Parsimonious Manuscript

## Objective

Make the GitHub-facing share repository manuscript-facing and P15-first:

- `P15_minimal_bedside_model` is the final clinically parsimonious transport model.
- `MT3_physiology_support_proxy` is retained as the Post-METRE transport reference model.
- `M1_original_rich` is retained as the internal rich/reference model.
- `phenotype` is retained only as stratification/explanation/calibration audit material.
- Full VIS and measurement-process-heavy materials stay out of the final external transport main path.

## Safety rules

- No model retraining.
- No cohort, label, or Step 1-6 modification.
- No permanent deletion of audit-relevant results.
- Superseded outputs are moved to `archive/` with `cleanup/file_action_manifest.csv` traceability.
- Raw data and heavy artifacts remain excluded from GitHub.

## Planned action counts

```json
{
  "keep": 21,
  "delete": 1,
  "move_to_archive": 87,
  "replace": 19
}
```

## Final main reading path

- `README.md`
- `FINAL_PROJECT_SUMMARY.md`
- `FINAL_FILE_INDEX.md`
- `LOCAL_ASSET_INDEX.md`
- `HEAVY_ARTIFACT_MANIFEST.csv`
- `results_final/`
- `final_freeze/*Parsimonious*`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/*Final_Parsimonious.md`
- `parsimonious_features/`
- `archive/` for superseded but audit-relevant material
