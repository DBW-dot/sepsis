# Table 1. Cohort and Event Distribution

Counts are prediction-row counts from the locked model evaluation tables. eICU is external validation only and was not used for training or tuning.

| database | cohort_role | prediction_rows_n | death_n | death_rate | event_definition | use_in_modeling | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MIMIC internal | development/internal evaluation | 1030526.0 | 20807.0 | 0.0202 | 24h competing-risk prediction death-class event | MIMIC used for training and internal evaluation; row count is prediction rows, not patient count. | Patient-level count was not extracted into this table; do not interpret prediction_rows_n as patient_n. |
| eICU external | external validation only | 1051357.0 | 22593.0 | 0.0215 | 24h competing-risk prediction death-class event | eICU used only for external validation; not used for training or tuning. | Patient-level count was not extracted into this table; do not interpret prediction_rows_n as patient_n. |
