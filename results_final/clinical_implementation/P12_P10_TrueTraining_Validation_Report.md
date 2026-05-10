# P12/P10 True-Training Validation Report

## Scope and guardrails

This validation trains P12 and P10 candidate models on the existing MIMIC train-inner split and evaluates them on the existing MIMIC internal test and eICU external validation tables. It does not modify Step 1-8, Sepsis-3 cohort definition, t_ICU/t_sepsis anchors, the 24h competing-risk label, patient-level split, P15 features, P15 frozen metrics, or raw data.

P15 remains the formal main model. P12/P10 are evaluated as clinical implementation sensitivity models and do not automatically replace P15.

## Required questions

1. P12 true-training 后是否仍接近 P15？
   - External AUROC: 0.8038; external AUPRC: 0.1767; calibration slope: 1.0100.
   - Relative AUPRC drop vs P15: 6.58%.

2. P12 是否可以从 simulated candidate 升级？
   - Recommended role: `validated_simplified_implementation_candidate`.

3. P10 true-training 后性能损失是否过大？
   - External AUROC: 0.7978; external AUPRC: 0.1711; calibration slope: 1.0133.
   - Relative AUPRC drop vs P15: 9.56%.

4. P10 是否只能保留为 ultra-minimal exploratory sensitivity model？
   - No, not strictly. By the predefined external AUROC/AUPRC/calibration thresholds, P10 meets noninferiority, but because it is the most compressed candidate it should remain an ultra-minimal sensitivity / deployment-stress-test candidate rather than replacing P15.
   - Recommended role: `validated_ultra_minimal_sensitivity_candidate_but_not_main_model`.

5. 如果 P12 表现接近 P15，是否建议论文补充展示？
   - Yes, as supplementary clinical implementation validation, not as automatic replacement of P15.

6. 是否建议替代 P15？
   - No automatic replacement. P15 remains the formal main model unless there is a separate PI re-freeze decision.

7. 是否仍保持 P15 作为正式主模型？
   - Yes.

8. 是否存在任何泄露风险？
   - No leakage was introduced in this validation. The models use existing prefix-only Model_Ready tables, existing labels, existing patient-level split, MIMIC train only for fitting, and eICU only for external validation.

## Evidence files

- `P12_P10_TrueTraining_Model_Comparison.csv`
- `P12_P10_TrueTraining_Noninferiority_Assessment.csv`
- `P12_P10_TrueTraining_DCA_Summary.csv`
- `P12_P10_TrueTraining_Leadtime_Summary.csv`
- `P12_P10_P15_Performance_Comparison.csv`
- `P12_P10_P15_Calibration_Comparison.csv`
