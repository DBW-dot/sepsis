# Final Figure Completion Audit

- Complete figures PDF: `D:\try\github_chatgpt_share_repo\results_final\figures\sepsis_complete_figures_pack.pdf`
- Word insertion: False. Word source unavailable: no .docx manuscript found under D:\try or the share repository.
- Validation warnings: []

## Figure status

- Graphical Abstract: generated=True; type=mechanism schematic; source=Locked manuscript numbers; no result recomputation; png=`results_final\figures\Graphical_Abstract_P15_vs_highdimensional.png`; pdf=`results_final\figures\Graphical_Abstract_P15_vs_highdimensional.pdf`; warning=none
- Figure 1: generated=True; type=mechanism/workflow schematic; source=Locked cohort/model design documents; png=`results_final\figures\Figure1_workflow_double_anchor_competing_risk.png`; pdf=`results_final\figures\Figure1_workflow_double_anchor_competing_risk.pdf`; warning=none
- Figure 1B: generated=True; type=mechanism/timeline schematic; source=Dual-anchor design; illustrative only; png=`results_final\figures\Figure1B_double_anchor_patient_timeline.png`; pdf=`results_final\figures\Figure1B_double_anchor_patient_timeline.pdf`; warning=none
- Figure 2 AUROC: generated=True; type=true results plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_main_results.csv; D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_clinical_implementation_models.csv; png=`results_final\figures\Figure2_transportability_slopegraph_AUROC.png`; pdf=`results_final\figures\Figure2_transportability_slopegraph_AUROC.pdf`; warning=none
- Figure 2 AUPRC: generated=True; type=true results plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_main_results.csv; D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_clinical_implementation_models.csv; png=`results_final\figures\Figure2_transportability_slopegraph_AUPRC.png`; pdf=`results_final\figures\Figure2_transportability_slopegraph_AUPRC.pdf`; warning=none
- Figure 3: generated=True; type=true prediction-level reliability diagram; source=D:\try\step7_main_modeling\output\Model_Ready_eICU_External.parquet; D:\try\step7_main_modeling\output\pred_main_eicu_external.parquet; png=`results_final\figures\Figure3_eICU_smooth_calibration_curve.png`; pdf=`results_final\figures\Figure3_eICU_smooth_calibration_curve.pdf`; warning=none
- Figure 4: generated=True; type=true DCA results plot; source=D:\try\github_chatgpt_share_repo\results_final\clinical_implementation\P12_P10_TrueTraining_DCA_Summary.csv; png=`results_final\figures\Figure4_eICU_decision_curve_analysis.png`; pdf=`results_final\figures\Figure4_eICU_decision_curve_analysis.pdf`; warning=none
- Figure 5: generated=True; type=true phenotype-stratified bootstrap result plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_subphenotype_results.csv; png=`results_final\figures\Figure5_subphenotype_robustness_eICU.png`; pdf=`results_final\figures\Figure5_subphenotype_robustness_eICU.pdf`; warning=none
- Figure 6: generated=True; type=true frozen-model coefficient importance plot; source=D:\try\parsimonious_features\model_P15_minimal_bedside_model.pkl; D:\try\github_chatgpt_share_repo\results_final\tables\P15_feature_source_availability_deployment_table.csv; D:\try\github_chatgpt_share_repo\results_final\tables\P15_feature_missingness_audit.csv; png=`results_final\figures\Figure6_P15_feature_importance_vs_deployment_difficulty.png`; pdf=`results_final\figures\Figure6_P15_feature_importance_vs_deployment_difficulty.pdf`; warning=none
- Supplementary Figure S1: generated=True; type=true threshold-specific results plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\P15_eICU_threshold_specific_performance.csv; png=`results_final\figures\Supplementary_Figure_S1_P15_threshold_operational_performance.png`; pdf=`results_final\figures\Supplementary_Figure_S1_P15_threshold_operational_performance.pdf`; warning=none
- Additional Figure A: generated=True; type=true results summary plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_main_results.csv; D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_clinical_implementation_models.csv; png=`results_final\figures\Additional_Figure_A_eICU_external_performance_overview.png`; pdf=`results_final\figures\Additional_Figure_A_eICU_external_performance_overview.pdf`; warning=none
- Additional Figure B: generated=True; type=true calibration-slope forest plot; source=D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_main_results.csv; D:\try\github_chatgpt_share_repo\results_final\tables\bootstrap_ci_clinical_implementation_models.csv; png=`results_final\figures\Additional_Figure_B_eICU_calibration_slope_forest.png`; pdf=`results_final\figures\Additional_Figure_B_eICU_calibration_slope_forest.pdf`; warning=none

## Quality checks

- Mechanism figures are limited to the Graphical Abstract, Figure 1, and Figure 1B.
- Figures 2-5 and Supplementary Figure S1 use true locked result files or prediction-level data.
- Figure 6 uses true frozen P15 model coefficients, not synthetic SHAP values.
- No model retraining was performed.
- No frozen model point estimates were modified.
- eICU was not used for tuning.
- DCA and threshold figures are clinical utility estimates, not automatic intervention triggers.
