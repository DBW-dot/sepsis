# Lab Freshness and Carry-forward Sensitivity Audit

## Scope

This audit evaluates fixed-model P15/P12/P10 predictions under laboratory freshness restrictions. It does not modify cohort definition, anchors, labels, patient-level split, P15 frozen main results, or model hierarchy. eICU is used only for external evaluation.

## Availability and look-ahead defense

- Current latest-value features are carried-forward values, not hourly true measurements.
- Step2/Step3 provide `*_hours_since_last_real_measurement` fields derived from chart/sample-time based quality indicators.
- No result availability/store time field is present in the model-ready tables. Therefore, chart/sample-time freshness is used as a conservative approximation and this is a limitation.
- BUN freshness was recovered from Step3 feature banks because Step7 Model_Ready retained `bun_latest_value` but not `bun_hours_since_last_real_measurement`.
- No value after `t_pred` is introduced in this audit; filtering only removes stale existing values.

## Required answers

1. 当前 latest_value 逻辑是否已经等价于前向填充？
   - Yes. It is a capped carry-forward / latest-available representation, not hourly real laboratory measurement.

2. 12h freshness window 下 P15 是否仍稳定？
   - eICU AUROC/AUPRC/calibration slope = 0.7847/0.1674/0.9779.
   - Noninferiority status: `borderline_acceptable`.

3. 24h freshness window 下 P15 是否仍稳定？
   - eICU AUROC/AUPRC/calibration slope = 0.8085/0.1860/0.9991.

4. P12/P10 对 lab freshness 是否比 P15 更敏感？
   - P12 12h eICU AUROC/AUPRC/slope = 0.7767/0.1545/0.9578.
   - P10 12h eICU AUROC/AUPRC/slope = 0.7743/0.1498/0.9444.
   - Full model-by-scenario deltas are in `Lab_Freshness_Noninferiority_Assessment.csv`.

5. 哪些实验室指标最容易因为 freshness window 变成 missing？
   - Top 12h missingness increases:

```text
  dataset_name              feature_name  missingness_increase  post_filter_missing_rate
 eicu_external support_lactate_component              0.619855                  0.619855
mimic_internal support_lactate_component              0.609927                  0.609927
 eicu_external          wbc_latest_value              0.384253                  0.456145
 eicu_external     platelet_latest_value              0.381576                  0.453053
 eicu_external   creatinine_latest_value              0.349230                  0.399667
 eicu_external          bun_latest_value              0.348750                  0.399954
mimic_internal          wbc_latest_value              0.337907                  0.368560
mimic_internal     platelet_latest_value              0.335413                  0.366325
mimic_internal          bun_latest_value              0.256479                  0.282614
mimic_internal   creatinine_latest_value              0.255842                  0.281560
```

6. proxy 中是否存在实验室 freshness 依赖？
   - Yes. `support_lactate_component` depends on lactate-derived burden signals. `support_renal_component` partly depends on creatinine-derived renal worsening plus urine-output support signals. `shared_support_intensity_proxy` inherits these component dependencies.

7. 是否存在 look-ahead bias 风险？
   - No new look-ahead was introduced in this audit. The remaining limitation is that result availability time is unavailable, so chart/sample time is used as a conservative approximation.

8. 是否需要在方法学中明确实验室指标不是小时级真实测量？
   - Yes.

9. 是否建议将 lab12h sensitivity 放入论文补充材料？
   - Yes.

10. 是否仍建议 P15 作为正式主模型？
   - Yes. This is a sensitivity audit and does not replace frozen P15 main results.
