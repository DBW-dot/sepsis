# Lab Availability and Look-ahead Audit

## Fields checked

- Model-ready tables include latest-value laboratory variables and quality/freshness fields for creatinine, platelet, WBC, lactate, urine output, and other variables.
- BUN freshness is present in Step2/Step3 feature banks as `bun_hours_since_last_real_measurement`, but it was not carried into Step7 Model_Ready. This audit merges BUN freshness back from Step3 using `stay_id + t_pred`.

## Result availability time

No explicit laboratory result availability/store time was found in the model-ready layer. The available freshness fields are based on chart/sample-time derived quality indicators. Therefore, chart/sample time is used as a conservative approximation.

## Look-ahead defense

- No laboratory value after `t_pred` is introduced.
- Freshness scenarios only convert already-carried latest values to missing when their last-real-measurement age exceeds the configured window.
- Existing model imputers then handle missing values under the original fixed-model pipelines.

## Limitation

If the raw source databases contain result availability timestamps that were not propagated to Step7, this audit cannot verify delayed lab reporting at the result-availability level. This limitation should be reported.
