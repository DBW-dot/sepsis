# Manuscript Table Index

| file_name | table_use | source_files | recommended_location | caution_note |
|---|---|---|---|---|
| Table1_Cohort_and_Event_Distribution.csv | Cohort and prediction-row event distribution | P12/P10 true-training model comparison | main manuscript | prediction_rows_n is not patient_n |
| Table2_Main_Model_Performance.csv | Main model and comparator performance | Final parsimonious Table2 and true-training table | main manuscript | P15 is formal main model |
| Table3_Clinical_Implementation_TrueTraining.csv | P12/P10 implementation validation | True-training and noninferiority tables | main manuscript | P12/P10 do not replace P15 |
| Table4_Lab_Freshness_Sensitivity.csv | Lab freshness sensitivity | Lab freshness performance and noninferiority tables | main manuscript | 12h borderline acceptable; 24h largely stable |
| Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv | Feature clinical validity audit | P15 feature validity audit | supplementary | do not infer missing fields |
| Supplementary_Table_S2_DCA_Summary.csv | DCA threshold summary | P12/P10 true-training DCA summary | supplementary | not automatic intervention trigger |
| Supplementary_Table_S3_Leadtime_Summary.csv | Lead-time summary | P12/P10 true-training lead-time summary | supplementary | risk-stratification timing support only |
| Supplementary_Table_S4_Honest_Reporting_Checklist.csv | Honest reporting checklist | Final honest reporting checklist | supplementary | TRIPOD+AI alignment support |

## Bootstrap 95% Confidence Interval Tables

- `Table2_Main_Model_Performance_with_95CI.csv`: manuscript Table 2 with patient-level / cluster-level bootstrap 95% CIs.
- `Table3_Clinical_Implementation_TrueTraining_with_95CI.csv`: P12/P10 true-training validation table with bootstrap 95% CIs.
- `Table4_Lab_Freshness_Sensitivity_with_95CI.csv`: lab freshness sensitivity table with bootstrap 95% CIs.
- `../supplement/Supplementary_Table_S5_Bootstrap_CI_AllMetrics.csv`: all bootstrap CI metrics for audit and supplement.

Original point-estimate-only tables remain preserved for audit traceability.
