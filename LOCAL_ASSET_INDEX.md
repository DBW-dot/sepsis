# Local Asset Index

## Included in this cleaned GitHub share repo

- Final parsimonious manuscript-facing package:
  - `final_freeze/*Parsimonious*`
  - `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
  - `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
  - `results_package/text/*Final_Parsimonious.md`
  - `parsimonious_features/`
- Cleanup audit:
  - `cleanup/cleanup_plan.md`
  - `cleanup/file_action_manifest.csv`
- Historical audit material:
  - `archive/`
- Heavy artifact index:
  - `HEAVY_ARTIFACT_MANIFEST.csv`

## Left local only

- Raw clinical databases:
  - `eicu/`
  - `mimic-iv-3.1/`
- Heavy analytical outputs:
  - `*.duckdb`
  - `*.parquet`
  - `*.pkl`
  - `*.gz`
- Runtime logs and transient files

## Current final interpretation

This repository is now centered on `P15_minimal_bedside_model` as the final clinically parsimonious transport model. `MT3_physiology_support_proxy` is retained as a Post-METRE reference, and `M1_original_rich` remains an internal rich/reference model.
