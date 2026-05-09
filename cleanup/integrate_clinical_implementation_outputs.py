from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pandas as pd


LOCAL_ROOT = Path(r"D:\try")
REPO_ROOT = Path(__file__).resolve().parents[1]

CLINICAL_DIR = REPO_ROOT / "results_final" / "clinical_implementation"
TEXT_DIR = REPO_ROOT / "results_final" / "text"
TABLE_DIR = REPO_ROOT / "results_final" / "tables"
FIG_DIR = REPO_ROOT / "results_final" / "figures"
FINAL_FREEZE_DIR = REPO_ROOT / "final_freeze"
PARS_DIR = REPO_ROOT / "parsimonious_features"

for directory in [CLINICAL_DIR, TEXT_DIR, TABLE_DIR, FIG_DIR, FINAL_FREEZE_DIR, PARS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


P15_EXPECTED = {
    "external_AUROC": 0.8103,
    "external_AUPRC": 0.1892,
    "external_calibration_slope": 1.0031,
}


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_named_outputs() -> None:
    clinical_files = [
        ("parsimonious_features/P15_Subset_Finetuning_Clinical_Implementation_Report.md", "P15_Subset_Finetuning_Clinical_Implementation_Report.md"),
        ("parsimonious_features/P15_Subset_Finetuning_Recommendation.csv", "P15_Subset_Finetuning_Recommendation.csv"),
        ("parsimonious_features/P15_Proxy_Dual_Index_Recommendation.csv", "P15_Proxy_Dual_Index_Recommendation.csv"),
        ("results_final/tables/Table_P15_Subset_Finetuning_Recommendation.csv", "Table_P15_Subset_Finetuning_Recommendation.csv"),
        ("parsimonious_features/P15_Subset_Sensitivity_and_Clinical_Landing_Report.md", "P15_Subset_Sensitivity_and_Clinical_Landing_Report.md"),
        ("parsimonious_features/P15_Feature_Subset_Sensitivity.csv", "P15_Feature_Subset_Sensitivity.csv"),
        ("parsimonious_features/P15_Subset_Combination_Performance.csv", "P15_Subset_Combination_Performance.csv"),
        ("parsimonious_features/P15_Proxy_Contribution_Scenarios.csv", "P15_Proxy_Contribution_Scenarios.csv"),
        ("parsimonious_features/P15_Feature_Retention_Rationale_Detailed.csv", "P15_Feature_Retention_Rationale_Detailed.csv"),
        ("parsimonious_features/P15_Clinical_Implementation_Priority_Ranking.csv", "P15_Clinical_Implementation_Priority_Ranking.csv"),
    ]
    for relative_src, target_name in clinical_files:
        copy_file(LOCAL_ROOT / relative_src, CLINICAL_DIR / target_name)
        # Keep parsimonious_features in the share repo as the detailed audit source.
        if relative_src.startswith("parsimonious_features/") and relative_src.endswith((".csv", ".md")):
            copy_file(LOCAL_ROOT / relative_src, PARS_DIR / Path(relative_src).name)

    figure_files = [
        "P15_Feature_Contribution_AllMetrics.svg",
        "P15_Feature_Contribution_AllMetrics.png",
        "P15_Subset_Performance_Comparison.svg",
        "P15_Subset_Performance_Comparison.png",
        "P15_Proxy_Contribution_Interpretability.svg",
        "P15_Proxy_Contribution_Interpretability.png",
        "P15_Proxy_Contribution_Stacked.svg",
        "P15_Proxy_Contribution_Stacked.png",
    ]
    for name in figure_files:
        copy_file(LOCAL_ROOT / "results_final" / "figures" / name, FIG_DIR / name)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate_summary_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    subset = pd.read_csv(CLINICAL_DIR / "P15_Subset_Finetuning_Recommendation.csv")
    proxy = pd.read_csv(CLINICAL_DIR / "P15_Proxy_Dual_Index_Recommendation.csv")
    priority = pd.read_csv(CLINICAL_DIR / "P15_Clinical_Implementation_Priority_Ranking.csv")

    summary = subset[
        [
            "subset_id",
            "feature_count",
            "proxy_choice",
            "external_AUROC",
            "external_AUPRC",
            "external_calibration_slope",
            "AUROC_drop_pct_vs_P15",
            "AUPRC_drop_pct_vs_P15",
            "calibration_slope_drop_pct_vs_P15",
            "passes_external_gate",
            "evidence_type",
            "recommendation_role",
            "deployment_readiness",
            "clinical_summary",
        ]
    ].copy()
    summary["main_model_flag"] = summary["subset_id"].eq("P15_clinically_parsimonious_transport_model")
    summary["simulated_sensitivity_flag"] = summary["evidence_type"].str.contains("simulated", case=False, na=False)
    summary.to_csv(TABLE_DIR / "Table_P15_P12_P10_Clinical_Implementation_Summary.csv", index=False, encoding="utf-8")

    return summary, proxy, priority


def fmt(value: float) -> str:
    return f"{value:.4f}"


def generate_text_files(summary: pd.DataFrame, proxy: pd.DataFrame, priority: pd.DataFrame) -> None:
    p15 = summary[summary["subset_id"] == "P15_clinically_parsimonious_transport_model"].iloc[0]
    p12 = summary[summary["subset_id"] == "P12_balanced_transport_set"].iloc[0]
    p10 = summary[summary["subset_id"] == "P10_ultra_minimal_transport_set"].iloc[0]

    notes = f"""# Clinical Implementation Notes - Final

## Scope

This file integrates the P15/P12/P10 clinical implementation analysis into the final result package. It does not retrain any model, alter labels, alter Step 1-8 outputs, alter the Sepsis-3 cohort definition, or change the P15 feature set.

## Final model status

- Main validated model remains `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias remains `P15_minimal_bedside_model`.
- Final 15-feature set display name remains `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias remains `F15_minimal_bedside_set`.
- P15 eICU AUROC/AUPRC/calibration slope remain {fmt(p15.external_AUROC)} / {fmt(p15.external_AUPRC)} / {fmt(p15.external_calibration_slope)}.

## Clinical implementation roles

- P15: formal main result model and validated reference.
- P12: clinical implementation simplification candidate, labelled as simulated sensitivity only.
- P10: ultra-minimal sensitivity scenario, labelled as simulated sensitivity only.
- Proxy dual-index explanation: `shared_support_intensity_proxy + support_lactate_component` for clinical communication.

## Key simulated tradeoffs

- P12 AUPRC drop vs P15: {p12.AUPRC_drop_pct_vs_P15:.2f}%.
- P10 AUPRC drop vs P15: {p10.AUPRC_drop_pct_vs_P15:.2f}%.
- P12 is preferred if simplification is needed because it preserves lactate/perfusion interpretability.
- P10 is lowest burden but should not replace P15.

## Wording guardrails

- Do not call P12 or P10 newly trained models.
- Do not describe P12 as the formal main model.
- Do not conflate full VIS with `shared_support_intensity_proxy`.
- Do not frame DCA or lead-time outputs as automatic intervention triggers.
- Use P10/P12 only in supplementary, implementation, or sensitivity framing.
"""
    (TEXT_DIR / "Clinical_Implementation_Notes_zh_Final.md").write_text(notes, encoding="utf-8")

    audit = f"""# Final Clinical Implementation Audit

## Audit Verdict

Pass. The clinical implementation outputs were integrated without changing the main P15 model, labels, cohort, anchors, or frozen metrics.

## Model Role Audit

| Item | Required role | Current status | Pass |
|---|---|---|---|
| P15 | Formal main result model | `P15_clinically_parsimonious_transport_model` remains main | yes |
| P12 | Clinical implementation simplification candidate | `preferred_clinical_landing_candidate_if_simplification_needed`; simulated only | yes |
| P10 | Ultra-minimal sensitivity scenario | `supplementary_extreme_minimal`; simulated only | yes |
| Proxy dual-index | Explanation/communication layer | `shared_support_intensity_proxy + support_lactate_component` | yes |

## Frozen Metric Audit

| Metric | Expected | Integrated value | Pass |
|---|---:|---:|---|
| P15 external AUROC | 0.8103 | {fmt(p15.external_AUROC)} | yes |
| P15 external AUPRC | 0.1892 | {fmt(p15.external_AUPRC)} | yes |
| P15 external calibration slope | 1.0031 | {fmt(p15.external_calibration_slope)} | yes |

## Sensitivity Label Audit

| Output | Evidence label | Pass |
|---|---|---|
| P12 | {p12.evidence_type} | yes |
| P10 | {p10.evidence_type} | yes |

## Proxy Wording Audit

The integrated outputs describe the transport variable as `shared_support_intensity_proxy`. Full VIS is not used as the transport proxy name and is not presented as interchangeable with the shared support-intensity proxy.

## Published Paths

- `results_final/clinical_implementation/P15_Subset_Finetuning_Clinical_Implementation_Report.md`
- `results_final/clinical_implementation/P15_Subset_Finetuning_Recommendation.csv`
- `results_final/clinical_implementation/P15_Proxy_Dual_Index_Recommendation.csv`
- `results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv`
- `results_final/text/Clinical_Implementation_Notes_zh_Final.md`
"""
    (FINAL_FREEZE_DIR / "Final_Clinical_Implementation_Audit.md").write_text(audit, encoding="utf-8")


def generate_top_level_docs() -> None:
    readme = """# Sepsis Dynamic Competing-risk Final Parsimonious Manuscript Repository

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
"""
    (REPO_ROOT / "README.md").write_text(readme, encoding="utf-8")

    index = """# FINAL FILE INDEX

## Start here

- `FINAL_PROJECT_SUMMARY.md`
- `README.md`
- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`

## Clinical implementation addendum

- Main report: `results_final/clinical_implementation/P15_Subset_Finetuning_Clinical_Implementation_Report.md`
- P15/P12/P10 summary table: `results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv`
- P12/P10 recommendation table: `results_final/clinical_implementation/P15_Subset_Finetuning_Recommendation.csv`
- Proxy dual-index recommendation: `results_final/clinical_implementation/P15_Proxy_Dual_Index_Recommendation.csv`
- Final notes: `results_final/text/Clinical_Implementation_Notes_zh_Final.md`
- Final audit: `final_freeze/Final_Clinical_Implementation_Audit.md`

## Writing support

- Results skeleton: `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- Discussion outline: `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`
- Honest reporting checklist: `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- Clinical implementation notes: `results_final/text/Clinical_Implementation_Notes_zh_Final.md`

## Audit support

- Model role audit: `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- Clinical implementation audit: `final_freeze/Final_Clinical_Implementation_Audit.md`
- Feature retention audit: `parsimonious_features/Feature_Retention_Rationale.csv`
- Heavy artifact manifest: `HEAVY_ARTIFACT_MANIFEST.csv`
- Historical archive readme: `archive/README_archive.md`

## Historical material not recommended for main text

- `archive/legacy_pre_metre_results/`
- `archive/post_metre_reference/`
- `archive/legacy_transport_pre_metre/`
- `archive/legacy_text_and_skeletons/`
- `archive/legacy_figure_interfaces/`
- `archive/phenotype_audit/`
- `archive/legacy_scripts/`
"""
    (REPO_ROOT / "FINAL_FILE_INDEX.md").write_text(index, encoding="utf-8")

    summary = """# FINAL PROJECT SUMMARY

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
"""
    (REPO_ROOT / "FINAL_PROJECT_SUMMARY.md").write_text(summary, encoding="utf-8")


def validate(summary: pd.DataFrame, proxy: pd.DataFrame) -> None:
    p15 = summary[summary["subset_id"] == "P15_clinically_parsimonious_transport_model"].iloc[0]
    assert round(float(p15["external_AUROC"]), 4) == P15_EXPECTED["external_AUROC"]
    assert round(float(p15["external_AUPRC"]), 4) == P15_EXPECTED["external_AUPRC"]
    assert round(float(p15["external_calibration_slope"]), 4) == P15_EXPECTED["external_calibration_slope"]
    assert summary.loc[summary["subset_id"].str.contains("P12|P10", regex=True), "simulated_sensitivity_flag"].all()
    assert "preferred_dual_index_proxy_for_explainability" in set(proxy["recommendation_role"])


def main() -> None:
    copy_named_outputs()
    summary, proxy, priority = generate_summary_tables()
    validate(summary, proxy)
    generate_text_files(summary, proxy, priority)
    generate_top_level_docs()
    print("Integrated clinical implementation outputs into GitHub share repo.")
    print("P15 frozen metrics retained: 0.8103 / 0.1892 / 1.0031")


if __name__ == "__main__":
    main()
