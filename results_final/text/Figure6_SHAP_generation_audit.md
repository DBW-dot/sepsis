# Figure 6 SHAP / feature-importance generation audit

Figure 6 was generated from true frozen P15 model coefficients, not from simulated SHAP values.

- Frozen model object: `D:\try\parsimonious_features\model_P15_minimal_bedside_model.pkl`
- Importance definition: absolute death-class coefficient from the multinomial logistic regression classifier.
- Deployment difficulty source: `results_final/tables/P15_feature_source_availability_deployment_table.csv`
- Bubble-size source: eICU missingness from `results_final/tables/P15_feature_missingness_audit.csv`
- Caution: coefficient importance is not a causal effect and does not quantify treatment benefit.
