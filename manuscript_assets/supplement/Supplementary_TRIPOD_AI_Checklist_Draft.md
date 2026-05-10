# Supplementary TRIPOD+AI Checklist Draft

This is a TRIPOD+AI-style draft, not a completed journal-specific checklist. Before submission, it must be cross-checked against the target journal and official checklist format.

| item_domain | reporting_item | current_project_status | source_file | manuscript_section_recommendation | caution_note |
|---|---|---|---|---|---|
| Study design | Retrospective database study design described | available | README.md / Supplementary_Methods_Details.md | Methods | Draft item; verify target journal wording. |
| Data source | MIMIC for development/internal validation and eICU for external validation | available | FINAL_PROJECT_SUMMARY.md | Methods | eICU not used for training/tuning. |
| Cohort definition | ICU sepsis dynamic prediction cohort and Sepsis-3 logic | available at summary level | Supplementary_Methods_Details.md | Methods | Do not add unverified cohort numbers. |
| Outcome definition | 24h competing-risk death/discharge/continued-stay labels | available | Supplementary_Competing_Risk_Label_Definition.md | Methods | Not simple binary classification. |
| Prediction horizon | 24h horizon | available | Supplementary_Methods_Details.md | Methods | Locked horizon. |
| Predictors | P15 feature modules and implementation candidates | available | Supplementary_Feature_Harmonisation_and_Unit_Mapping.md | Methods/Supplement | P15 not bedside-only manual score. |
| Missing data | Latest-available/carry-forward lab interpretation | available | Supplementary_Lab_Freshness_and_Timestamp_Limitations.md | Methods/Supplement | Not measured hourly. |
| Lab freshness | 12h and 24h sensitivity results | available | Supplementary_Lab_Freshness_and_Timestamp_Limitations.md | Supplement | 12h borderline acceptable; 24h largely stable. |
| Model development | MIMIC-only development boundary | available | Supplementary_Methods_Details.md | Methods | Do not use eICU for training/tuning. |
| Internal validation | MIMIC internal evaluation | available in locked tables | manuscript_assets/tables/Table2_Main_Model_Performance.csv | Results | Prediction-row counts only where patient counts unavailable. |
| External validation | eICU external evaluation | available | manuscript_assets/tables/Table2_Main_Model_Performance.csv | Results | External validation only. |
| Calibration | Calibration slope and bin-level curves where available | available | manuscript_assets/figures/FIGURE_INDEX.md | Results/Supplement | Do not infer curves where only summary data exist. |
| Clinical utility | DCA and lead-time supplementary estimates | available | manuscript_assets/tables/Supplementary_Table_S2_DCA_Summary.csv | Supplement | Not automatic intervention trigger. |
| Model interpretability | Feature modules and proxy interpretation | available | Supplementary_Proxy_Interpretation_Note.md | Supplement | Proxy is not full VIS. |
| Deployment limitation | Local EHR mapping and prospective validation required | available | Honest reporting checklist | Discussion | Not a deployment-ready treatment directive. |
| Bias/leakage prevention | Prefix-only and timestamp limitations documented | available | Supplementary_Dual_Anchor_Definition.md | Methods/Limitations | Do not overclaim complete look-ahead elimination. |
| Code/repository availability | GitHub-facing share repository available | available | README.md | Data/code availability | Safe-share excludes raw clinical data. |
| Limitations | Timestamp, proxy, deployment, and validation limitations | available | Supplementary_Lab_Freshness_and_Timestamp_Limitations.md | Discussion | Must be retained. |
