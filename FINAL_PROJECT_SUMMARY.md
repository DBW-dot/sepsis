# FINAL PROJECT SUMMARY

## Final research goal

This project builds a dynamic competing-risk prediction framework for 24-hour ICU sepsis deterioration and death, using MIMIC-IV as the primary development source and eICU as external validation. The final manuscript-facing model is the clinically parsimonious transport model P15.

## Final model roles

- `P15_clinically_parsimonious_transport_model`: formal main result model.
- `P15_minimal_bedside_model`: legacy/internal alias for traceability only.
- `MT3_Post_METRE_transport_reference_model`: Post-METRE transport reference model.
- `M1_internal_rich_reference_model`: internal rich/reference model.
- `P12_balanced_transport_set`: clinical simplification candidate, simulated sensitivity only.
- `P10_ultra_minimal_transport_set`: ultra-minimal sensitivity scenario, simulated sensitivity only.
- `phenotype`: stratification/explanation/calibration audit tool, not a performance driver.

## Frozen P15 performance

- eICU AUROC = 0.8103
- eICU AUPRC = 0.1892
- eICU calibration slope = 1.0031

## Clinical implementation conclusion

P15 remains the formal main model. P12 is the preferred simplification candidate if implementation burden must be reduced, but it must be presented as a simulated implementation estimate. P10 is an ultra-minimal sensitivity scenario. The recommended proxy explanation for clinical communication is the dual-index view: `shared_support_intensity_proxy + support_lactate_component`.

## Claims that must not be overstated

- P12 and P10 are not newly trained models.
- P12 is not the formal main model.
- full VIS is not the shared support-intensity proxy.
- DCA or lead-time outputs are not automatic intervention triggers.
- Phenotype should not be framed as a main performance driver.

## Ready for manuscript writing

Yes, with the above boundaries. Use `results_final/` and `final_freeze/` as the final-facing sources. Historical files under `archive/` are retained only for audit and lineage.
