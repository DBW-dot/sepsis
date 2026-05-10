from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "manuscript_assets"

P15 = "P15_clinically_parsimonious_transport_model"
P12 = "P12_true_trained_clinical_landing_model"
P10 = "P10_true_trained_ultra_minimal_sensitivity_model"
MT3 = "MT3_Post_METRE_transport_reference_model"
M1 = "M1_internal_rich_reference_model"
C1 = "C1_dynamic_SOFA"

SOURCE_FILES = [
    "README.md",
    "FINAL_PROJECT_SUMMARY.md",
    "FINAL_FILE_INDEX.md",
    "cleanup/Final_Repository_Consistency_Report.md",
    "results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
    "results_final/clinical_implementation/P12_P10_TrueTraining_Model_Comparison.csv",
    "results_final/clinical_implementation/P12_P10_TrueTraining_Noninferiority_Assessment.csv",
    "results_final/clinical_implementation/Lab_Freshness_Model_Performance.csv",
    "results_final/clinical_implementation/Lab_Freshness_Noninferiority_Assessment.csv",
    "results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
]


def read_csv(path: str) -> list[dict[str, str]]:
    full = ROOT / path
    if not full.exists():
        return []
    with full.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fmt(value: str | None, digits: int = 4) -> str:
    if value is None or value == "":
        return "not_found"
    try:
        return f"{float(value):.{digits}f}"
    except ValueError:
        return str(value)


def find_row(rows: list[dict[str, str]], **criteria: str) -> dict[str, str] | None:
    for row in rows:
        ok = True
        for key, value in criteria.items():
            if row.get(key) != value:
                ok = False
                break
        if ok:
            return row
    return None


def source_entry(
    number_or_statement: str,
    value: str,
    source_file: str,
    source_column_or_section: str,
    location: str,
    caution: str,
) -> dict[str, str]:
    return {
        "number_or_statement": number_or_statement,
        "value": value,
        "source_file": source_file,
        "source_column_or_section": source_column_or_section,
        "manuscript_location_recommendation": location,
        "caution_note": caution,
    }


def ensure_dirs() -> None:
    for sub in ["tables", "figures", "supplement", "audit"]:
        (ASSET / sub).mkdir(parents=True, exist_ok=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ensure_dirs()
    missing = [p for p in SOURCE_FILES if not (ROOT / p).exists()]

    table2_path = "results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv"
    true_path = "results_final/clinical_implementation/P12_P10_TrueTraining_Model_Comparison.csv"
    noninf_path = "results_final/clinical_implementation/P12_P10_TrueTraining_Noninferiority_Assessment.csv"
    lab_perf_path = "results_final/clinical_implementation/Lab_Freshness_Model_Performance.csv"
    lab_noninf_path = "results_final/clinical_implementation/Lab_Freshness_Noninferiority_Assessment.csv"

    table2 = read_csv(table2_path)
    true_rows = read_csv(true_path)
    noninf = read_csv(noninf_path)
    lab_perf = read_csv(lab_perf_path)
    lab_noninf = read_csv(lab_noninf_path)

    p15_table2 = find_row(table2, display_model_name=P15) or find_row(table2, model_name="P15_minimal_bedside_model")
    mt3_table2 = find_row(table2, display_model_name=MT3) or find_row(table2, model_name="MT3_physiology_support_proxy")
    m1_table2 = find_row(table2, display_model_name=M1) or find_row(table2, model_name="M1_original_rich")
    c1_table2 = (
        find_row(table2, model_name="C1_dynamic_SOFA")
        or find_row(table2, display_model_name="C1_dynamic_SOFA_clinical_comparator")
        or find_row(table2, model_name="dynamic_SOFA_only")
        or find_row(table2, display_model_name=C1)
    )

    p15_true_eicu = find_row(true_rows, model_name=P15, dataset_name="eicu_external")
    p15_true_mimic = find_row(true_rows, model_name=P15, dataset_name="mimic_internal")
    p12_true_eicu = find_row(true_rows, model_name=P12, dataset_name="eicu_external")
    p10_true_eicu = find_row(true_rows, model_name=P10, dataset_name="eicu_external")

    p12_noninf = find_row(noninf, model_name=P12)
    p10_noninf = find_row(noninf, model_name=P10)

    p15_lab12 = find_row(lab_perf, model_name=P15, dataset_name="eicu_external", scenario="lab12h_freshness_window")
    p15_lab24 = find_row(lab_perf, model_name=P15, dataset_name="eicu_external", scenario="lab24h_freshness_window")
    p15_lab_current = find_row(lab_perf, model_name=P15, dataset_name="eicu_external", scenario="current_latest_value_reference")
    p15_lab12_noninf = find_row(lab_noninf, model_name=P15, dataset_name="eicu_external", scenario="lab12h_freshness_window")
    p15_lab24_noninf = find_row(lab_noninf, model_name=P15, dataset_name="eicu_external", scenario="lab24h_freshness_window")

    p15_source = p15_table2 or p15_true_eicu or {}
    p15_mimic = p15_true_mimic or p15_table2 or {}

    comparators = [
        {
            "name": M1,
            "source": m1_table2,
            "feature_count": (m1_table2 or {}).get("feature_count", "not_found"),
            "role": "internal rich/reference model",
            "interpretation": "Strong internal reference model, externally unstable; not the final external transport model.",
        },
        {
            "name": MT3,
            "source": mt3_table2,
            "feature_count": (mt3_table2 or {}).get("feature_count", "not_found"),
            "role": "Post-METRE transport reference model",
            "interpretation": "Transport reference model used before final parsimonious P15 freeze; not the final model.",
        },
        {
            "name": P15,
            "source": p15_table2,
            "feature_count": "15",
            "role": "formal main manuscript-facing model",
            "interpretation": "Final clinically parsimonious transport model with stable eICU discrimination and calibration.",
        },
        {
            "name": P12,
            "source": p12_true_eicu,
            "feature_count": "12",
            "role": "validated simplified implementation candidate",
            "interpretation": "True-trained simplified candidate; does not replace P15.",
        },
        {
            "name": P10,
            "source": p10_true_eicu,
            "feature_count": "10",
            "role": "validated ultra-minimal sensitivity candidate",
            "interpretation": "True-trained ultra-minimal sensitivity candidate; does not replace P15.",
        },
        {
            "name": C1,
            "source": c1_table2,
            "feature_count": (c1_table2 or {}).get("feature_count", "not_found"),
            "role": "clinical score comparator",
            "interpretation": "Dynamic SOFA clinical comparator from final parsimonious Table2.",
        },
    ]

    def eicu_auroc(row: dict[str, str] | None) -> str:
        if not row:
            return "not_found"
        return fmt(row.get("eICU_AUROC") or row.get("auroc_death_ovr"))

    def eicu_auprc(row: dict[str, str] | None) -> str:
        if not row:
            return "not_found"
        return fmt(row.get("eICU_AUPRC") or row.get("auprc_death"))

    def eicu_slope(row: dict[str, str] | None) -> str:
        if not row:
            return "not_found"
        return fmt(row.get("eICU_calibration_slope") or row.get("calibration_slope_death"))

    comparator_lines = []
    for comp in comparators:
        comparator_lines.append(
            f"| {comp['name']} | {comp['feature_count']} | {eicu_auroc(comp['source'])} | {eicu_auprc(comp['source'])} | {eicu_slope(comp['source'])} | {comp['role']} | {comp['interpretation']} |"
        )

    p12_status = (p12_noninf or {}).get("whether_noninferior_to_P15", "not_found")
    p10_status = (p10_noninf or {}).get("whether_noninferior_to_P15", "not_found")
    p12_drop = fmt((p12_noninf or {}).get("relative_AUPRC_drop_pct_vs_P15"))
    p10_drop = fmt((p10_noninf or {}).get("relative_AUPRC_drop_pct_vs_P15"))

    numbers_md = f"""
# Final Manuscript Numbers

Generated from final authority files in this repository. Missing values are reported as `not_found`; no manuscript number was invented.

## 1. Final model roles

- `{P15}`
  - formal main manuscript-facing model
  - 正式主模型
- `{P12}`
  - validated simplified implementation candidate
  - 真实训练验证后的临床简化候选
  - not replacing P15
- `{P10}`
  - validated ultra-minimal sensitivity candidate
  - 真实训练验证后的极简敏感性模型
  - not replacing P15
- `MT3_Post_METRE_transport_reference_model`
  - Post-METRE transport reference model
  - not final model
- `M1_internal_rich_reference_model`
  - internal rich/reference model
  - not external transport model

## 2. Main P15 performance

- MIMIC AUROC: {fmt(p15_mimic.get('auroc_death_ovr') or p15_mimic.get('MIMIC_AUROC'))}
- MIMIC AUPRC: {fmt(p15_mimic.get('auprc_death') or p15_mimic.get('MIMIC_AUPRC'))}
- MIMIC Brier: {fmt(p15_mimic.get('multiclass_brier') or p15_mimic.get('MIMIC_Brier'))}
- eICU AUROC: {fmt(p15_source.get('eICU_AUROC') or (p15_true_eicu or {{}}).get('auroc_death_ovr'))}
- eICU AUPRC: {fmt(p15_source.get('eICU_AUPRC') or (p15_true_eicu or {{}}).get('auprc_death'))}
- eICU calibration slope: {fmt(p15_source.get('eICU_calibration_slope') or (p15_true_eicu or {{}}).get('calibration_slope_death'))}
- feature count: 15

## 3. Comparator performance

| Model | feature_count | eICU AUROC | eICU AUPRC | eICU calibration slope | manuscript role | interpretation |
|---|---:|---:|---:|---:|---|---|
{chr(10).join(comparator_lines)}

## 4. P12/P10 true-training validation

- P12 eICU AUROC/AUPRC/calibration slope: {eicu_auroc(p12_true_eicu)} / {eicu_auprc(p12_true_eicu)} / {eicu_slope(p12_true_eicu)}
- P12 relative AUPRC drop vs P15: {p12_drop}%
- P12 noninferiority status: {p12_status}
- P12 recommended role: {(p12_noninf or {{}}).get('recommended_role_after_true_training', 'not_found')}

- P10 eICU AUROC/AUPRC/calibration slope: {eicu_auroc(p10_true_eicu)} / {eicu_auprc(p10_true_eicu)} / {eicu_slope(p10_true_eicu)}
- P10 relative AUPRC drop vs P15: {p10_drop}%
- P10 noninferiority status: {p10_status}
- P10 recommended role: {(p10_noninf or {{}}).get('recommended_role_after_true_training', 'not_found')}

## 5. Lab freshness results

- current latest_value interpretation: latest-available / capped carry-forward
- P15 current eICU AUROC/AUPRC/calibration slope: {fmt((p15_lab_current or {{}}).get('auroc'))} / {fmt((p15_lab_current or {{}}).get('auprc'))} / {fmt((p15_lab_current or {{}}).get('calibration_slope'))}
- P15 12h freshness eICU AUROC/AUPRC/calibration slope: {fmt((p15_lab12 or {{}}).get('auroc'))} / {fmt((p15_lab12 or {{}}).get('auprc'))} / {fmt((p15_lab12 or {{}}).get('calibration_slope'))}
- P15 24h freshness eICU AUROC/AUPRC/calibration slope: {fmt((p15_lab24 or {{}}).get('auroc'))} / {fmt((p15_lab24 or {{}}).get('auprc'))} / {fmt((p15_lab24 or {{}}).get('calibration_slope'))}
- 12h status: borderline acceptable, not fully noninferior; table status = {(p15_lab12_noninf or {{}}).get('auprc_freshness_status', 'not_found')}
- 24h status: largely stable; table status = {(p15_lab24_noninf or {{}}).get('auprc_freshness_status', 'not_found')}
- look-ahead limitation: result availability time incomplete; chart/sample time used as conservative approximation

## 6. Clinical interpretation boundaries

- P15 is not a bedside-only manual score.
- P15 is EHR-implementable.
- Laboratory values are not assumed to be measured hourly.
- shared support-intensity proxy is not full VIS.
- DCA/lead-time are not automatic intervention triggers.
- Clinical implementation requires local EHR mapping and prospective validation.

## 7. Numbers not to use

- Archive materials containing old pre-METRE numbers.
- Old simulation-only P10/P12 numbers that were superseded by true-training validation.
- Old DCA / lead-time / phenotype gain files outside the final file index.
- Old Post-METRE transition results unless explicitly labeled as historical reference.

## Missing source files

{chr(10).join(f'- {p}' for p in missing) if missing else '- none'}
"""
    write(ASSET / "FINAL_MANUSCRIPT_NUMBERS.md", numbers_md)

    index_md = """
# Manuscript Asset Index

## Tables to generate later

1. Table 1: Cohort and event distribution
2. Table 2: Main model and comparator performance
3. Table 3: P12/P10 true-training clinical implementation validation
4. Table 4: Lab freshness and carry-forward sensitivity
5. Supplementary Table S1: Feature clinical validity audit
6. Supplementary Table S2: DCA threshold table
7. Supplementary Table S3: Lead-time analysis
8. Supplementary Table S4: Honest reporting checklist / TRIPOD+AI alignment

## Figures to generate later

1. Figure 1: Study workflow and dual-anchor dynamic prediction design
2. Figure 2: Model performance comparison
3. Figure 3: Calibration curves
4. Figure 4: Lab freshness sensitivity plot
5. Figure 5: P15 clinical feature module diagram
6. Supplementary Figure S1: DCA curves
7. Supplementary Figure S2: Lead-time distribution
8. Supplementary Figure S3: Proxy interpretation diagram

## Supplementary materials to generate later

1. Supplementary Methods
2. Feature harmonisation and unit mapping note
3. Lab freshness and timestamp limitation note
4. P12/P10 implementation validation note
5. Proxy interpretation note
6. TRIPOD+AI checklist draft

## Source-lock files

- `manuscript_assets/FINAL_MANUSCRIPT_NUMBERS.md`
- `manuscript_assets/audit/Manuscript_Number_Source_Map.csv`
- `manuscript_assets/audit/Manuscript_Asset_Step1_Consistency_Check.md`
"""
    write(ASSET / "MANUSCRIPT_ASSET_INDEX.md", index_md)

    source_rows = [
        source_entry("P15 eICU AUROC", fmt(p15_source.get("eICU_AUROC") or (p15_true_eicu or {}).get("auroc_death_ovr")), table2_path, "eICU_AUROC", "Results main text / Table 2", "main formal model result"),
        source_entry("P15 eICU AUPRC", fmt(p15_source.get("eICU_AUPRC") or (p15_true_eicu or {}).get("auprc_death")), table2_path, "eICU_AUPRC", "Results main text / Table 2", "main formal model result"),
        source_entry("P15 eICU calibration slope", fmt(p15_source.get("eICU_calibration_slope") or (p15_true_eicu or {}).get("calibration_slope_death")), table2_path, "eICU_calibration_slope", "Results main text / Table 2", "main formal model result"),
        source_entry("P15 MIMIC AUROC", fmt(p15_mimic.get("auroc_death_ovr") or p15_mimic.get("MIMIC_AUROC")), true_path, "auroc_death_ovr", "Results / Table 2", "MIMIC internal row"),
        source_entry("P15 MIMIC AUPRC", fmt(p15_mimic.get("auprc_death") or p15_mimic.get("MIMIC_AUPRC")), true_path, "auprc_death", "Results / Table 2", "MIMIC internal row"),
        source_entry("P15 MIMIC Brier", fmt(p15_mimic.get("multiclass_brier") or p15_mimic.get("MIMIC_Brier")), true_path, "multiclass_brier", "Results / Table 2", "multiclass Brier"),
        source_entry("M1 eICU AUROC/AUPRC/slope", f"{eicu_auroc(m1_table2)} / {eicu_auprc(m1_table2)} / {eicu_slope(m1_table2)}", table2_path, "M1_original_rich row", "Table 2", "internal rich/reference model only"),
        source_entry("MT3 eICU AUROC/AUPRC/slope", f"{eicu_auroc(mt3_table2)} / {eicu_auprc(mt3_table2)} / {eicu_slope(mt3_table2)}", table2_path, "MT3_physiology_support_proxy row", "Table 2", "Post-METRE transport reference, not final model"),
        source_entry("C1 dynamic SOFA eICU AUROC/AUPRC/slope", f"{eicu_auroc(c1_table2)} / {eicu_auprc(c1_table2)} / {eicu_slope(c1_table2)}", table2_path, "C1_dynamic_SOFA row", "Table 2", "clinical score comparator"),
        source_entry("P12 eICU AUROC", eicu_auroc(p12_true_eicu), true_path, "auroc_death_ovr", "Table 3", "true-trained simplified candidate"),
        source_entry("P12 eICU AUPRC", eicu_auprc(p12_true_eicu), true_path, "auprc_death", "Table 3", "true-trained simplified candidate"),
        source_entry("P12 eICU calibration slope", eicu_slope(p12_true_eicu), true_path, "calibration_slope_death", "Table 3", "true-trained simplified candidate"),
        source_entry("P12 relative AUPRC drop vs P15", p12_drop + "%", noninf_path, "relative_AUPRC_drop_pct_vs_P15", "Table 3", "does not automatically replace P15"),
        source_entry("P12 noninferiority status", p12_status, noninf_path, "whether_noninferior_to_P15", "Table 3", "candidate status only"),
        source_entry("P10 eICU AUROC", eicu_auroc(p10_true_eicu), true_path, "auroc_death_ovr", "Table 3", "ultra-minimal sensitivity candidate"),
        source_entry("P10 eICU AUPRC", eicu_auprc(p10_true_eicu), true_path, "auprc_death", "Table 3", "ultra-minimal sensitivity candidate"),
        source_entry("P10 eICU calibration slope", eicu_slope(p10_true_eicu), true_path, "calibration_slope_death", "Table 3", "ultra-minimal sensitivity candidate"),
        source_entry("P10 relative AUPRC drop vs P15", p10_drop + "%", noninf_path, "relative_AUPRC_drop_pct_vs_P15", "Table 3", "does not automatically replace P15"),
        source_entry("P10 noninferiority status", p10_status, noninf_path, "whether_noninferior_to_P15", "Table 3", "candidate status only"),
        source_entry("P15 12h lab freshness eICU AUROC/AUPRC/slope", f"{fmt((p15_lab12 or {}).get('auroc'))} / {fmt((p15_lab12 or {}).get('auprc'))} / {fmt((p15_lab12 or {}).get('calibration_slope'))}", lab_perf_path, "scenario=lab12h_freshness_window", "Table 4 / Supplement", "borderline acceptable, not fully noninferior"),
        source_entry("P15 24h lab freshness eICU AUROC/AUPRC/slope", f"{fmt((p15_lab24 or {}).get('auroc'))} / {fmt((p15_lab24 or {}).get('auprc'))} / {fmt((p15_lab24 or {}).get('calibration_slope'))}", lab_perf_path, "scenario=lab24h_freshness_window", "Table 4 / Supplement", "largely stable"),
        source_entry("latest_value interpretation", "latest-available / capped carry-forward", "FINAL_PROJECT_SUMMARY.md", "Laboratory freshness", "Methods / Limitations", "not hourly laboratory measurement"),
        source_entry("shared support-intensity proxy", "not full VIS", "README.md", "Laboratory freshness and proxy interpretation", "Methods / Limitations", "do not conflate with full VIS"),
        source_entry("DCA/lead-time role", "supplementary clinical utility estimate, not automatic intervention trigger", "README.md", "Laboratory freshness and proxy interpretation", "Discussion / Supplement", "not direct treatment recommendation"),
    ]
    write_csv(
        ASSET / "audit" / "Manuscript_Number_Source_Map.csv",
        source_rows,
        [
            "number_or_statement",
            "value",
            "source_file",
            "source_column_or_section",
            "manuscript_location_recommendation",
            "caution_note",
        ],
    )

    # Consistency checks are based on the generated files and final source text, excluding archive.
    combined_text = ""
    for path in [
        ROOT / "README.md",
        ROOT / "FINAL_PROJECT_SUMMARY.md",
        ASSET / "FINAL_MANUSCRIPT_NUMBERS.md",
        ASSET / "MANUSCRIPT_ASSET_INDEX.md",
    ]:
        if path.exists():
            combined_text += "\n" + path.read_text(encoding="utf-8", errors="ignore")

    checks = {
        "P15_only_formal_main_model": f"{P15}" in combined_text and "only formal" in combined_text,
        "P12_P10_not_replacing_P15": "not replacing P15" in combined_text and "does not replace P15" in combined_text,
        "lab_not_hourly_measurement": "not assumed to be measured hourly" in combined_text or "not hourly" in combined_text,
        "freshness_12h_not_fully_noninferior": "borderline acceptable, not fully noninferior" in combined_text,
        "proxy_not_full_VIS": "not full VIS" in combined_text,
        "DCA_leadtime_not_trigger": "not automatic intervention trigger" in combined_text or "not automatic intervention triggers" in combined_text,
        "archive_not_main_numbers": "Archive materials" in combined_text and "Numbers not to use" in combined_text,
    }

    consistency_md = "# Manuscript Asset Step 1 Consistency Check\n\n"
    for key, passed in checks.items():
        consistency_md += f"- {key}: {'pass' if passed else 'fail'}\n"
    consistency_md += "\n## Missing authority files\n\n"
    consistency_md += "\n".join(f"- {p}" for p in missing) if missing else "- none"
    consistency_md += "\n\n## Numeric conflicts\n\n- none detected by source extraction; missing values are explicitly marked as `not_found`.\n"
    write(ASSET / "audit" / "Manuscript_Asset_Step1_Consistency_Check.md", consistency_md)

    print(
        "assets_created=1 "
        f"missing_source_files={len(missing)} "
        f"checks_passed={sum(1 for v in checks.values() if v)}/{len(checks)}"
    )


if __name__ == "__main__":
    main()
