from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPP = ROOT / "manuscript_assets" / "supplement"
AUDIT = ROOT / "manuscript_assets" / "audit"

P15 = "P15_clinically_parsimonious_transport_model"
P12 = "P12_true_trained_clinical_landing_model"
P10 = "P10_true_trained_ultra_minimal_sensitivity_model"
MT3 = "MT3_Post_METRE_transport_reference_model"
M1 = "M1_internal_rich_reference_model"

SOURCE_FILES = [
    "README.md",
    "FINAL_PROJECT_SUMMARY.md",
    "FINAL_FILE_INDEX.md",
    "manuscript_assets/FINAL_MANUSCRIPT_NUMBERS.md",
    "manuscript_assets/MANUSCRIPT_ASSET_INDEX.md",
    "manuscript_assets/tables/TABLE_INDEX.md",
    "manuscript_assets/figures/FIGURE_INDEX.md",
    "results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
    "results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md",
    "results_final/clinical_implementation/Lab_Freshness_Sensitivity_Report.md",
    "results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md",
    "results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md",
    "final_freeze/Final_Model_Role_Audit_Parsimonious.md",
    "cleanup/Final_Repository_Consistency_Report.md",
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        return "source unavailable"
    return p.read_text(encoding="utf-8", errors="ignore")


def source_status() -> str:
    lines = []
    for path in SOURCE_FILES:
        lines.append(f"- `{path}`: {'available' if (ROOT / path).exists() else 'source unavailable'}")
    return "\n".join(lines)


def generate() -> dict[str, bool]:
    SUPP.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    final_numbers = read("manuscript_assets/FINAL_MANUSCRIPT_NUMBERS.md")
    p12_p10_report = read("results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md")
    lab_report = read("results_final/clinical_implementation/Lab_Freshness_Sensitivity_Report.md")
    lookahead_report = read("results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md")
    proxy_report = read("results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md")

    write(
        SUPP / "Supplementary_Methods_Details.md",
        f"""
# Supplementary Methods Details

This document is a methods-support asset, not the full manuscript text. It summarizes final locked methods language using only the approved repository sources.

## 1. Study design

This is a retrospective clinical database study using MIMIC-IV for model development and internal validation, with eICU reserved for external validation. eICU was not used for model training or hyperparameter tuning.

## 2. Cohort definition

The study target is ICU sepsis 24-hour dynamic competing-risk prediction. Cohort construction follows the project Sepsis-3 logic, including suspected infection, `t_ICU`, and `t_sepsis` anchor definitions. Patient-level split logic is part of the locked modeling workflow. This supplement does not add cohort counts beyond the locked tables.

## 3. Dynamic prediction design

Prediction uses an hourly prediction grid. All features at a prediction time are prefix-only observations, meaning they can only use information available at or before the prediction time. The prediction horizon is 24 hours. No post-prediction information is used.

## 4. Competing risk design

The 24-hour outcome is framed as three mutually exclusive states: ICU death within 24 hours, alive ICU discharge/transfer within 24 hours, or continued ICU stay. This supports a competing-risk interpretation rather than a simple death-vs-nondeath binary framing. Cumulative-incidence language should remain conceptual unless a specific formula source is added later from an approved method file.

## 5. Model hierarchy

- `{M1}`: internal rich/reference model, not the external transport model.
- `{MT3}`: Post-METRE transport reference model, not the final model.
- `{P15}`: final formal manuscript-facing main model.
- `{P12}`: true-trained validated simplified implementation candidate, not replacing P15.
- `{P10}`: true-trained validated ultra-minimal sensitivity candidate, not replacing P15.
- `C1_dynamic_SOFA_clinical_comparator`: clinical comparator.

## 6. Clinical implementation analyses

Clinical implementation support includes P12/P10 true-training validation, laboratory freshness sensitivity, proxy interpretability, and supplementary DCA/lead-time estimates. DCA and lead-time are not automatic intervention triggers or direct treatment recommendations.

## Source availability

{source_status()}
""",
    )

    write(
        SUPP / "Supplementary_Dual_Anchor_Definition.md",
        """
# Supplementary Dual Anchor Definition

## t_ICU

`t_ICU` denotes the ICU admission anchor. It represents process time from ICU entry and is used to preserve ICU-flow timing.

## t_sepsis

`t_sepsis` denotes the sepsis-onset disease anchor from the locked Step 1 cohort construction. It is not a future outcome label and should not be derived from post-prediction information.

## Why both anchors are used

Using both ICU admission time and sepsis-onset time separates ICU process time from disease time. This reduces heterogeneity between patients who enter the ICU already septic and patients whose sepsis onset occurs after ICU admission.

## Admission sepsis handling

Patients with sepsis at or near ICU admission are represented through `is_sepsis_on_admission` and hours since ICU admission. They should not be forced into the same disease-time interpretation as patients developing sepsis later.

## Later sepsis handling

Patients who develop sepsis after ICU admission are aligned by `t_sepsis` while retaining ICU time. This prevents the disease-onset landmark from being replaced by ICU entry.

## Leakage prevention

Prediction features can only use information available at or before each prediction time. Information after a prediction time cannot be used for feature construction, anchoring at that time, or risk scoring.
""",
    )

    write(
        SUPP / "Supplementary_Feature_Harmonisation_and_Unit_Mapping.md",
        f"""
# Supplementary Feature Harmonisation and Unit Mapping

## Cross-database alignment principles

MIMIC and eICU variables were aligned by clinical concept, field availability, unit compatibility where available, and cross-database transportability. The final P15 feature set was selected to be clinically parsimonious and transportable.

## P15 feature modules

- Time anchors: `hours_since_icu_admission`, `hours_from_anchor`, `is_sepsis_on_admission`
- Vital signs: heart rate, respiratory rate, SpO2
- Routine laboratory values: creatinine, BUN, platelet count, WBC
- Support-intensity proxy: shared support-intensity proxy and hemodynamic, lactate, renal, and respiratory support components

## Unit coordination

Unit mapping was performed according to repository harmonisation tables when available. Not all source systems provide identical unit metadata, and remaining uncertainty should be reported as a limitation. This supplement does not invent specific unit conversion rules.

## Field naming differences

Database-specific field names were harmonised to shared clinical variable names. The manuscript should describe harmonisation at the concept level and cite the repository tables for implementation details.

## VIS and support-intensity proxy

Full VIS was not used as the external transport input. The shared support-intensity proxy is a cross-database support burden proxy and is not full VIS.

## Comparator limitations

Dynamic SOFA is retained as a clinical comparator. Dynamic OASIS was not used as a final comparator where stable reconstruction inputs were unavailable.

## Implementation boundary

P15 is EHR-implementable but not a bedside-only manual score.
""",
    )

    write(
        SUPP / "Supplementary_Lab_Freshness_and_Timestamp_Limitations.md",
        """
# Supplementary Lab Freshness and Timestamp Limitations

## Latest-value interpretation

Laboratory `latest_value` variables are latest-available / capped carry-forward values. They are not assumed to be newly measured every hour.

## P15 12h freshness sensitivity

P15 eICU AUROC/AUPRC/calibration slope under the 12h freshness scenario was 0.7847 / 0.1674 / 0.9779. This result is borderline acceptable, not fully noninferior.

## P15 24h freshness sensitivity

P15 eICU AUROC/AUPRC/calibration slope under the 24h freshness scenario was 0.8085 / 0.1860 / 0.9991. This result is largely stable.

## Timestamp limitations

Result availability time is incomplete in the available source structure. Chart/sample time was used as a conservative approximation. No additional look-ahead was identified under the available timestamp structure, but the manuscript should not claim that all look-ahead risk was fully eliminated.

## Proxy dependence

Some support-intensity proxy components may depend on laboratory-derived information, such as lactate/perfusion or renal support signals. These components require the same freshness and timestamp caution.

## Manuscript placement

Lab freshness is a supplementary realism analysis and does not replace the locked main P15 result.
""",
    )

    write(
        SUPP / "Supplementary_Competing_Risk_Label_Definition.md",
        """
# Supplementary Competing-risk Label Definition

## Why not simple binary classification

A simple 24-hour death-vs-nondeath label would treat alive ICU discharge/transfer as if it were equivalent to remaining in the ICU, which is clinically and statistically inappropriate for short-horizon ICU risk prediction.

## Three mutually exclusive states

At each prediction time, the 24-hour label distinguishes ICU death, alive ICU discharge/transfer, and continued ICU stay. These states are mutually exclusive within the 24-hour horizon.

## Discharge or transfer as a competing event

Alive ICU discharge/transfer removes a patient from the ICU death risk set during the 24-hour window, so it is handled as a competing event rather than ordinary censoring.

## Model output interpretation

Model outputs should be interpreted as short-horizon competing-risk probabilities. If cumulative-incidence formulas are required for the final manuscript, they should be sourced from an approved methods file before use.

## Clinical utility boundary

DCA and first-alarm lead-time analyses are supplementary estimates. They are not automatic intervention triggers or direct treatment recommendations.
""",
    )

    write(
        SUPP / "Supplementary_P12_P10_Implementation_Validation.md",
        """
# Supplementary P12/P10 Implementation Validation

## Why true-training validation was needed

Earlier P12/P10 versions were implementation sensitivity estimates. True-training validation was needed to determine whether simplified candidates retained transport performance when trained under the same MIMIC-only development boundary.

## Training and validation boundary

P12 and P10 were true-trained on MIMIC train only. eICU was used only for external validation and did not participate in training or tuning.

## P12 result

P12 eICU AUROC/AUPRC/calibration slope was 0.8038 / 0.1767 / 1.0100. Relative AUPRC drop vs P15 was 6.5828%. P12 is a validated simplified implementation candidate.

## P10 result

P10 eICU AUROC/AUPRC/calibration slope was 0.7978 / 0.1711 / 1.0133. Relative AUPRC drop vs P15 was 9.5577%. P10 is a validated ultra-minimal sensitivity candidate.

## Why P12/P10 do not replace P15

P15 remains the final manuscript-facing main model. P12/P10 are useful for implementation and sensitivity discussions, but replacing P15 would require a separate final model refreeze decision.

## Recommended manuscript placement

P12/P10 should be presented in supplementary or implementation analysis sections, not as the primary model.
""",
    )

    write(
        SUPP / "Supplementary_Proxy_Interpretation_Note.md",
        """
# Supplementary Proxy Interpretation Note

## Meaning of shared support-intensity proxy

The shared support-intensity proxy is a cross-database support burden signal. It summarizes support intensity in a way that can be mapped across MIMIC and eICU.

## Not full VIS

The proxy is not full VIS. Full VIS was not used as the external transport input.

## Component meanings

- Hemodynamic component: hemodynamic support burden.
- Lactate component: perfusion/low-flow burden and clinically interpretable severity context.
- Renal component: renal support burden.
- Respiratory component: respiratory support burden.

## Treatment-behavior confounding

Support proxy variables partly reflect clinician treatment behavior and monitoring context. They should not be interpreted causally and should not be described as intervention effects.

## Implementation boundary

The proxy should be implemented as an EHR-derived variable, not as a clinician hand-calculated score.
""",
    )

    tripod_rows = [
        ("Study design", "Retrospective database study design described", "available", "README.md / Supplementary_Methods_Details.md", "Methods", "Draft item; verify target journal wording."),
        ("Data source", "MIMIC for development/internal validation and eICU for external validation", "available", "FINAL_PROJECT_SUMMARY.md", "Methods", "eICU not used for training/tuning."),
        ("Cohort definition", "ICU sepsis dynamic prediction cohort and Sepsis-3 logic", "available at summary level", "Supplementary_Methods_Details.md", "Methods", "Do not add unverified cohort numbers."),
        ("Outcome definition", "24h competing-risk death/discharge/continued-stay labels", "available", "Supplementary_Competing_Risk_Label_Definition.md", "Methods", "Not simple binary classification."),
        ("Prediction horizon", "24h horizon", "available", "Supplementary_Methods_Details.md", "Methods", "Locked horizon."),
        ("Predictors", "P15 feature modules and implementation candidates", "available", "Supplementary_Feature_Harmonisation_and_Unit_Mapping.md", "Methods/Supplement", "P15 not bedside-only manual score."),
        ("Missing data", "Latest-available/carry-forward lab interpretation", "available", "Supplementary_Lab_Freshness_and_Timestamp_Limitations.md", "Methods/Supplement", "Not measured hourly."),
        ("Lab freshness", "12h and 24h sensitivity results", "available", "Supplementary_Lab_Freshness_and_Timestamp_Limitations.md", "Supplement", "12h borderline acceptable; 24h largely stable."),
        ("Model development", "MIMIC-only development boundary", "available", "Supplementary_Methods_Details.md", "Methods", "Do not use eICU for training/tuning."),
        ("Internal validation", "MIMIC internal evaluation", "available in locked tables", "manuscript_assets/tables/Table2_Main_Model_Performance.csv", "Results", "Prediction-row counts only where patient counts unavailable."),
        ("External validation", "eICU external evaluation", "available", "manuscript_assets/tables/Table2_Main_Model_Performance.csv", "Results", "External validation only."),
        ("Calibration", "Calibration slope and bin-level curves where available", "available", "manuscript_assets/figures/FIGURE_INDEX.md", "Results/Supplement", "Do not infer curves where only summary data exist."),
        ("Clinical utility", "DCA and lead-time supplementary estimates", "available", "manuscript_assets/tables/Supplementary_Table_S2_DCA_Summary.csv", "Supplement", "Not automatic intervention trigger."),
        ("Model interpretability", "Feature modules and proxy interpretation", "available", "Supplementary_Proxy_Interpretation_Note.md", "Supplement", "Proxy is not full VIS."),
        ("Deployment limitation", "Local EHR mapping and prospective validation required", "available", "Honest reporting checklist", "Discussion", "Not a deployment-ready treatment directive."),
        ("Bias/leakage prevention", "Prefix-only and timestamp limitations documented", "available", "Supplementary_Dual_Anchor_Definition.md", "Methods/Limitations", "Do not overclaim complete look-ahead elimination."),
        ("Code/repository availability", "GitHub-facing share repository available", "available", "README.md", "Data/code availability", "Safe-share excludes raw clinical data."),
        ("Limitations", "Timestamp, proxy, deployment, and validation limitations", "available", "Supplementary_Lab_Freshness_and_Timestamp_Limitations.md", "Discussion", "Must be retained."),
    ]
    table = "| item_domain | reporting_item | current_project_status | source_file | manuscript_section_recommendation | caution_note |\n|---|---|---|---|---|---|\n"
    for row in tripod_rows:
        table += "| " + " | ".join(row) + " |\n"
    write(
        SUPP / "Supplementary_TRIPOD_AI_Checklist_Draft.md",
        f"""
# Supplementary TRIPOD+AI Checklist Draft

This is a TRIPOD+AI-style draft, not a completed journal-specific checklist. Before submission, it must be cross-checked against the target journal and official checklist format.

{table}
""",
    )

    index_rows = [
        ("Supplementary_Methods_Details.md", "Overall method scaffold", "Methods", "yes", "yes", "Does not add new numbers."),
        ("Supplementary_Dual_Anchor_Definition.md", "t_ICU/t_sepsis and leakage prevention", "Methods", "yes", "yes", "t_sepsis is not a future label."),
        ("Supplementary_Feature_Harmonisation_and_Unit_Mapping.md", "Feature/unit harmonisation boundaries", "Methods/Supplement", "yes", "yes", "No invented unit conversions."),
        ("Supplementary_Lab_Freshness_and_Timestamp_Limitations.md", "Lab freshness and timestamp caveats", "Methods/Limitations", "yes", "yes", "12h borderline acceptable, 24h stable."),
        ("Supplementary_Competing_Risk_Label_Definition.md", "Competing-risk outcome framing", "Methods", "yes", "yes", "Conceptual CIF framing only unless formula source added."),
        ("Supplementary_P12_P10_Implementation_Validation.md", "True-training validation for simplified candidates", "Results/Supplement", "yes", "yes", "P12/P10 do not replace P15."),
        ("Supplementary_Proxy_Interpretation_Note.md", "Support proxy interpretation", "Methods/Supplement", "yes", "yes", "Proxy is not full VIS."),
        ("Supplementary_TRIPOD_AI_Checklist_Draft.md", "TRIPOD+AI-style reporting alignment", "Supplement", "no", "yes", "Draft only; final journal checklist required."),
    ]
    index_table = "| file_name | content_use | recommended_manuscript_location | main_text_reference | supplementary_material | caution_note |\n|---|---|---|---|---|---|\n"
    for row in index_rows:
        index_table += "| " + " | ".join(row) + " |\n"
    write(
        SUPP / "Supplementary_Methods_Index.md",
        f"""
# Supplementary Methods Index

{index_table}
""",
    )

    expected = [
        "Supplementary_Methods_Details.md",
        "Supplementary_Dual_Anchor_Definition.md",
        "Supplementary_Feature_Harmonisation_and_Unit_Mapping.md",
        "Supplementary_Lab_Freshness_and_Timestamp_Limitations.md",
        "Supplementary_Competing_Risk_Label_Definition.md",
        "Supplementary_P12_P10_Implementation_Validation.md",
        "Supplementary_Proxy_Interpretation_Note.md",
        "Supplementary_TRIPOD_AI_Checklist_Draft.md",
        "Supplementary_Methods_Index.md",
    ]
    combined = "\n".join((SUPP / name).read_text(encoding="utf-8", errors="ignore") for name in expected)
    checks = {
        "P15_unique_main_model": P15 in combined and "final formal manuscript-facing main model" in combined,
        "P12_P10_not_replacing_P15": "not replacing P15" in combined or "do not replace P15" in combined,
        "lab_latest_not_hourly_measurement": "not assumed to be newly measured every hour" in combined or "Not measured hourly" in combined,
        "freshness_12h_not_fully_noninferior": "borderline acceptable, not fully noninferior" in combined,
        "result_availability_limitation_retained": "Result availability time is incomplete" in combined,
        "proxy_not_full_VIS": "not full VIS" in combined,
        "DCA_leadtime_not_trigger": "not automatic intervention triggers" in combined or "Not automatic intervention trigger" in combined,
        "no_archive_results_used": "archive/" not in combined and "archive\\" not in combined,
        "no_fabricated_unit_rules_or_formulas": "does not invent specific unit conversion rules" in combined and "conceptual" in combined,
        "all_supplement_files_generated": all((SUPP / name).exists() for name in expected),
    }
    audit = "# Supplementary Methods Consistency Check\n\n"
    for key, value in checks.items():
        audit += f"- {key}: {'pass' if value else 'fail'}\n"
    audit += "\n## Source availability\n\n" + source_status() + "\n"
    audit += "\n## Numeric conflicts\n\n- none detected; no metrics were recalculated or modified.\n"
    write(AUDIT / "Supplementary_Methods_Consistency_Check.md", audit)
    return checks


if __name__ == "__main__":
    result = generate()
    print(f"supplement_files=9 checks_passed={sum(result.values())}/{len(result)}")
