# Sepsis Dynamic Competing-risk Final Parsimonious Manuscript Repository

## Project title

Dynamic competing-risk prediction for ICU sepsis deterioration with a clinically parsimonious transport model.

## Current frozen conclusion

The final manuscript-facing model is `P15_clinically_parsimonious_transport_model`, using the legacy/internal alias `P15_minimal_bedside_model`. It is a 15-feature clinically parsimonious transport model, not an all-bedside manual score. It includes time anchors, routine vital signs, routine laboratory values, and a shared support-intensity proxy. MT3 remains the Post-METRE transport reference, while P15 is the final clinically parsimonious model.

## Clinical implementation addendum

The repository now includes an implementation-focused analysis of P15, P12, and P10:

- P15 remains the formal main result model.
- P12 is a clinical simplification candidate, labelled as simulated sensitivity / simulated implementation estimate.
- P10 is an ultra-minimal sensitivity scenario, labelled as simulated sensitivity only.
- The proxy communication recommendation is `shared_support_intensity_proxy + support_lactate_component`.
- P12 and P10 do not replace P15 and are not newly trained models.

Start with:

1. `results_final/clinical_implementation/P15_Subset_Finetuning_Clinical_Implementation_Report.md`
2. `results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv`
3. `results_final/text/Clinical_Implementation_Notes_zh_Final.md`
4. `final_freeze/Final_Clinical_Implementation_Audit.md`

## Final model roles

- `M1_original_rich` / display name `M1_internal_rich_reference_model` = internal rich/reference model
- `MT3_physiology_support_proxy` / display name `MT3_Post_METRE_transport_reference_model` = Post-METRE transport reference
- `P15_minimal_bedside_model` / display name `P15_clinically_parsimonious_transport_model` = final clinically parsimonious transport model
- `P12_balanced_transport_set` = clinical implementation simplification candidate, simulated only
- `P10_ultra_minimal_transport_set` = ultra-minimal sensitivity scenario, simulated only
- `P25_clinical_core_model` and `P40_balanced_transport_model` = sensitivity models
- `C1_dynamic_SOFA` = clinical comparator
- `phenotype` = early static phenotype for stratification / explanation / calibration audit only

## Key final metrics

- P15 feature count = 15
- P15 eICU external AUROC/AUPRC/calibration slope = 0.8103 / 0.1892 / 1.0031
- P12 and P10 metrics are simulated sensitivity estimates, not retrained model results.

## What is included in this repo

- Final manuscript-facing tables and text in `results_final/`
- Clinical implementation package in `results_final/clinical_implementation/`
- Backward-compatible final outputs in `results_package/`
- Final model role freeze documents in `final_freeze/`
- Parsimonious feature-set audit outputs in `parsimonious_features/`
- Cleanup and naming harmonisation reports in `cleanup/`
- Historical audit material in `archive/`
- Heavy artifact index in `HEAVY_ARTIFACT_MANIFEST.csv`

## What is excluded and why

Raw MIMIC-IV/eICU data, parquet datasets, model binaries, DuckDB databases, compressed raw files, and runtime logs are excluded. This repository is a lightweight manuscript-facing share layer, not a full local computational archive.

## Warning

Do not use archived pre-METRE outputs, old Step8/Step9 outputs, old lead-time/DCA interfaces, or historical phenotype-gain files as final results. Do not describe P15 as an all-bedside or manually calculated score; do not describe P12 as the formal main model; do not use phenotype as a default performance driver; and do not conflate full VIS with the shared support-intensity proxy.
