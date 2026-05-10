# Post-METRE Result Package Index

## Updated main tables

- `tables/Table2_Main_Model_Comparators_Post_METRE.csv`
- `tables/Table3_Phenotype_Gain_Post_METRE.csv`
- `tables/Table4_Measurement_Bias_Post_METRE.csv`

## Updated figure data

- `figures/Figure5_DCA_Leadtime_Post_METRE.csv`
- `figures/Figure6_External_Failure_Modes_Post_METRE.csv`

## Updated manuscript interface text

- `text/Results_Skeleton_zh_Post_METRE.md`
- `text/Discussion_Outline_zh_Post_METRE.md`
- `text/Honest_Reporting_Checklist_Post_METRE.md`
- `text/PI_Decision_Summary_Post_METRE.md`
- `text/Post_METRE_Final_Project_Assessment.md`

## Traceability

- `POST_METRE_RESULT_LINEAGE.csv` records old value, new value, source file, source script, model, recalibration status, and notes.

## Replacement decisions

- Old Figure5 lead-time should be replaced or renamed because it measured eventual-death timing, not strict 24h-label first alarm.
- New Figure5 data should use strict 24h lead-time, exploratory eventual-death lead-time as separate panel, and post-METRE DCA/recalibrated DCA.
- External transport narrative should use MT3, while preserving M1 as the internal rich model.
