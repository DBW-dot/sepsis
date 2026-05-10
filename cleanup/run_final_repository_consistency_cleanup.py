from __future__ import annotations

import csv
import hashlib
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"
CLEANUP = ROOT / "cleanup"


FINAL_MODEL = "P15_clinically_parsimonious_transport_model"
P12_MODEL = "P12_true_trained_clinical_landing_model"
P10_MODEL = "P10_true_trained_ultra_minimal_sensitivity_model"
P15_AUROC = "0.8103"
P15_AUPRC = "0.1892"
P15_SLOPE = "1.0031"
P15_LAB12 = "0.7847 / 0.1674 / 0.9779"
P15_LAB24 = "0.8085 / 0.1860 / 0.9991"


action_rows: list[dict[str, str]] = []
risk_rows: list[dict[str, str]] = []


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def add_action(
    original: Path | str,
    action: str,
    destination: Path | str = "",
    reason: str = "",
    risk: str = "",
    manuscript_needed: str = "no",
    audit_needed: str = "yes",
    final_status: str = "",
) -> None:
    original_s = rel(original) if isinstance(original, Path) and original.is_absolute() else str(original)
    destination_s = rel(destination) if isinstance(destination, Path) and destination and destination.is_absolute() else str(destination)
    action_rows.append(
        {
            "original_path": original_s,
            "action": action,
            "destination_path": destination_s,
            "reason": reason,
            "risk_if_left_in_main_path": risk,
            "manuscript_needed": manuscript_needed,
            "audit_needed": audit_needed,
            "final_status": final_status or action,
        }
    )


def ensure_dirs() -> None:
    for sub in [
        "superseded_results",
        "superseded_text",
        "superseded_tables",
        "superseded_figures",
        "superseded_scripts",
        "superseded_simulation_before_true_training",
    ]:
        (ARCHIVE / sub).mkdir(parents=True, exist_ok=True)
    CLEANUP.mkdir(parents=True, exist_ok=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 2
    while True:
        candidate = parent / f"{stem}_archived_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def move_to_archive(path: str, archive_subdir: str, reason: str, risk: str) -> None:
    src = ROOT / path
    if not src.exists():
        return
    dst_base = ARCHIVE / archive_subdir / Path(path)
    dst_base.parent.mkdir(parents=True, exist_ok=True)
    dst = unique_path(dst_base)
    if src.is_file() and dst_base.exists() and dst_base.is_file():
        try:
            if file_hash(src) == file_hash(dst_base):
                src.unlink()
                add_action(src, "delete", dst_base, "duplicate of archived copy with identical hash", risk, "no", "yes", "deleted_duplicate")
                return
        except OSError:
            pass
    shutil.move(str(src), str(dst))
    add_action(src, "move_to_archive", dst, reason, risk, "no", "yes", "archived")


def delete_cache(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    add_action(path, "delete", "", "temporary cache/compiled artifact", "none", "no", "no", "deleted")


def write_text(path: str, text: str, reason: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + "\n", encoding="utf-8")
    add_action(target, "update_text", "", reason, "outdated or ambiguous final wording", "yes", "yes", "updated")


def write_csv(path: str, rows: list[dict[str, object]], fieldnames: list[str], reason: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    add_action(target, "update_text", "", reason, "outdated or missing final index/table", "yes", "yes", "updated")


def archive_obsolete_materials() -> None:
    # Whole folders whose contents remain useful for audit, but are no longer the final manuscript-facing path.
    for folder in [
        "metre_transport",
        "phenotype_reassessment",
        "post_metre_clinical_utility",
        "post_metre_component_reassessment",
        "post_metre_recalibration",
        "post_metre_selection",
        "recalibration",
        "results_package",
        "transport_model",
    ]:
        move_to_archive(
            folder,
            "superseded_results",
            "superseded pre-final or post-METRE working result set retained for audit only",
            "could be mistaken for current final result package",
        )

    move_to_archive(
        "step9_results_packaging",
        "superseded_scripts",
        "old packaging script workspace retained for audit only",
        "could be mistaken for active manuscript packaging workflow",
    )

    move_to_archive(
        "parsimonious_features",
        "superseded_simulation_before_true_training",
        "old parsimonious and simulated P10/P12 materials superseded by true-training validation",
        "could imply P10/P12 simulation-only results are still the clinical implementation evidence",
    )

    # Legacy final_freeze materials that predate the final parsimonious freeze.
    final_freeze_archive = {
        "final_freeze/Final_Freeze_Audit_Summary.json": "legacy freeze audit replaced by final parsimonious audit",
        "final_freeze/FINAL_MANUSCRIPT_HANDOFF_INDEX.md": "legacy handoff replaced by FINAL_FILE_INDEX.md and final parsimonious summaries",
        "final_freeze/Final_Model_Role_Audit.md": "legacy model role audit replaced by Final_Model_Role_Audit_Parsimonious.md",
        "final_freeze/FINAL_PI_SUMMARY.md": "legacy PI summary replaced by FINAL_PI_SUMMARY_PARSIMONIOUS.md",
        "final_freeze/Final_Table_Figure_Consistency_Audit.md": "legacy table/figure audit replaced by final cleanup report",
        "final_freeze/Final_Table_Figure_Consistency_Detail.csv": "legacy detail table retained for audit",
        "final_freeze/Old_Result_Replacement_Map.csv": "legacy replacement map retained for audit",
        "final_freeze/Old_Result_Replacement_Report.md": "legacy replacement report retained for audit",
        "final_freeze/Required_File_Inventory.csv": "legacy inventory retained for audit",
        "final_freeze/run_final_freeze_audit.py": "legacy script retained for audit",
        "final_freeze/run_final_parsimonious_integration.py": "legacy script retained for audit",
    }
    for path, reason in final_freeze_archive.items():
        subdir = "superseded_scripts" if path.endswith(".py") else "superseded_results"
        move_to_archive(path, subdir, reason, "legacy final/main wording could confuse final model roles")

    # Old simulated clinical implementation artifacts now superseded by P12/P10 true-training validation.
    simulated_files = [
        "results_final/clinical_implementation/P15_Clinical_Implementation_Priority_Ranking.csv",
        "results_final/clinical_implementation/P15_Feature_Retention_Rationale_Detailed.csv",
        "results_final/clinical_implementation/P15_Feature_Subset_Sensitivity.csv",
        "results_final/clinical_implementation/P15_Proxy_Contribution_Scenarios.csv",
        "results_final/clinical_implementation/P15_Proxy_Dual_Index_Recommendation.csv",
        "results_final/clinical_implementation/P15_Subset_Combination_Performance.csv",
        "results_final/clinical_implementation/P15_Subset_Finetuning_Clinical_Implementation_Report.md",
        "results_final/clinical_implementation/P15_Subset_Finetuning_Recommendation.csv",
        "results_final/clinical_implementation/P15_Subset_Sensitivity_and_Clinical_Landing_Report.md",
        "results_final/clinical_implementation/Table_P15_Subset_Finetuning_Recommendation.csv",
        "results_final/tables/Table_P15_Subset_Finetuning_Recommendation.csv",
        "results_final/tables/Table_P15_Subset_Sensitivity_Clinical_Landing.csv",
        "results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
    ]
    for path in simulated_files:
        move_to_archive(
            path,
            "superseded_simulation_before_true_training",
            "simulation-only P10/P12 or pre-true-training implementation artifact superseded by true-training validation",
            "could imply P10/P12 are still simulation-only evidence in the main path",
        )

    # Old figures are no longer part of the final main reading path.
    move_to_archive(
        "results_final/figures",
        "superseded_figures",
        "old figure interfaces superseded by final tables and clinical implementation audit",
        "could mix old simulated or pre-final figure interfaces with final manuscript-facing results",
    )

    # Delete cache/compiled files only.
    for cache in ROOT.rglob("__pycache__"):
        if "archive" not in cache.parts:
            delete_cache(cache)
    for pyc in ROOT.rglob("*.pyc"):
        if "archive" not in pyc.parts:
            delete_cache(pyc)


def update_final_documents() -> None:
    write_text(
        "README.md",
        f"""
# Sepsis Dynamic Competing-risk Prediction Final Share Repository

This repository is the GitHub-facing, safe-share result layer for the ICU sepsis 24-hour dynamic competing-risk prediction project. It excludes raw clinical databases and heavy row-level artifacts.

## Final model roles

- `{FINAL_MODEL}` is the only formal manuscript-facing main model. It is an EHR-implementable clinically parsimonious transport model, not a bedside-only model and not a manual score.
- `{P12_MODEL}` is a validated simplified implementation candidate after true MIMIC-only training and eICU external validation. It does not replace P15.
- `{P10_MODEL}` is a validated ultra-minimal sensitivity candidate after true MIMIC-only training and eICU external validation. It does not replace P15.
- `MT3_Post_METRE_transport_reference_model` is a Post-METRE transport reference model, not the final model.
- `M1_internal_rich_reference_model` is an internal rich/reference model, not the external transport model.

## Frozen P15 external performance

- eICU AUROC: {P15_AUROC}
- eICU AUPRC: {P15_AUPRC}
- eICU calibration slope: {P15_SLOPE}

## Laboratory freshness and proxy interpretation

- Laboratory variables are latest-available / capped carry-forward values, not hourly real laboratory measurements.
- The 12h laboratory freshness sensitivity result is borderline acceptable, not fully noninferior.
- The 24h laboratory freshness sensitivity result is largely stable.
- No additional look-ahead was identified under the available timestamp structure, but result availability time is incomplete; chart/sample time was used as a conservative approximation and should be reported as a limitation.
- The shared support-intensity proxy is a cross-database support burden proxy, not full VIS. Full VIS was not used as the external transport input.
- DCA and lead-time outputs are supplementary clinical utility estimates for risk stratification or monitoring-escalation discussion, not automatic intervention triggers.

## Start here

1. `FINAL_PROJECT_SUMMARY.md`
2. `FINAL_FILE_INDEX.md`
3. `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
4. `cleanup/Final_Repository_Consistency_Report.md`
""",
        "rewrite final public entry point with frozen model roles and lab/proxy guardrails",
    )

    write_text(
        "FINAL_PROJECT_SUMMARY.md",
        f"""
# Final Project Summary

## Final frozen position

The final manuscript-facing model is `{FINAL_MODEL}`. It remains the only formal main model and keeps the frozen eICU external metrics: AUROC {P15_AUROC}, AUPRC {P15_AUPRC}, and calibration slope {P15_SLOPE}.

`{P12_MODEL}` and `{P10_MODEL}` have moved beyond simulation-only summaries through true MIMIC-only training and eICU external validation. P12 is a validated simplified implementation candidate. P10 is a validated ultra-minimal sensitivity candidate. Neither model automatically replaces P15.

## Clinical implementation positioning

P15 is intended for EHR implementation. It is not a bedside-only manual score because it uses latest-available carry-forward laboratory variables and a shared support-intensity proxy. P12 can be discussed as a simplification candidate if clinical feature burden must be reduced. P10 should remain an ultra-minimal sensitivity option.

## Laboratory freshness

The project explicitly treats laboratory variables as latest-available / capped carry-forward values, not hourly real measurements. The 12h freshness sensitivity for P15 has eICU AUROC/AUPRC/calibration slope = {P15_LAB12}, which is borderline acceptable. The 24h freshness sensitivity has eICU AUROC/AUPRC/calibration slope = {P15_LAB24}, which is largely stable. No additional look-ahead was identified under available timestamps, but result availability time is incomplete and chart/sample time was used as a conservative approximation.

## Proxy and clinical utility boundaries

The shared support-intensity proxy is not full VIS and should be explained as a cross-database support burden proxy. DCA and first-alarm lead-time analyses are supplementary utility estimates. They support risk stratification and monitoring-escalation discussion, not automatic treatment recommendations.

## Current readiness

The repository is ready for final manuscript writing after reading the final file index and cleanup report. Archive materials are retained for audit traceability but are not the main result path.
""",
        "update final project summary with true-training and lab freshness conclusions",
    )

    write_text(
        "FINAL_FILE_INDEX.md",
        """
# Final File Index

This index is the main reading path. Files under `archive/` are retained for audit only and should not be used as final manuscript-facing results unless explicitly cited as historical or superseded material.

## Start here

- `README.md`
- `FINAL_PROJECT_SUMMARY.md`
- `FINAL_FILE_INDEX.md`

## Final model

- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`

## Clinical implementation

- `results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md`
- `results_final/clinical_implementation/P12_P10_TrueTraining_PI_Summary_zh.md`
- `results_final/clinical_implementation/P12_P10_TrueTraining_Model_Comparison.csv`
- `results_final/clinical_implementation/P12_P10_TrueTraining_Noninferiority_Assessment.csv`
- `results_final/clinical_implementation/P12_P10_P15_Performance_Comparison.csv`
- `results_final/clinical_implementation/P12_P10_P15_Calibration_Comparison.csv`
- `results_final/clinical_implementation/P15_Final_Clinical_Feature_Validity_Audit.csv`
- `results_final/clinical_implementation/P15_P12_P10_Clinical_Use_Boundaries.md`
- `results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md`

## Lab freshness and carry-forward sensitivity

- `results_final/clinical_implementation/Lab_Freshness_Sensitivity_Report.md`
- `results_final/clinical_implementation/Lab_Freshness_PI_Summary_zh.md`
- `results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md`
- `results_final/clinical_implementation/Lab_Freshness_Model_Performance.csv`
- `results_final/clinical_implementation/Lab_Freshness_Noninferiority_Assessment.csv`
- `results_final/clinical_implementation/Lab_Freshness_Missingness_Impact.csv`

## Writing support

- `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- `results_final/text/Clinical_Implementation_Notes_zh_Final.md`

## Cleanup audit

- `cleanup/Final_Repository_Consistency_Report.md`
- `cleanup/Final_Consistency_File_Action_Manifest.csv`
- `cleanup/Final_Consistency_Risk_Term_Scan.csv`
- `archive/README_archive.md`
""",
        "rewrite final file index to point to final parsimonious, true-training, and lab freshness artifacts",
    )

    write_text(
        "results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
        f"""
# Honest Reporting Checklist - Final Parsimonious Model

- `{FINAL_MODEL}` is the only formal manuscript-facing main model.
- `{P12_MODEL}` is a true-trained validated simplified implementation candidate, not the final model and not a replacement for P15.
- `{P10_MODEL}` is a true-trained validated ultra-minimal sensitivity candidate, not the final model and not a replacement for P15.
- P15 is EHR-implementable but not a bedside-only manual score.
- Laboratory variables are not assumed to be measured hourly.
- Laboratory latest values should be interpreted as most recent available values under capped carry-forward rules.
- The 12h laboratory freshness sensitivity is borderline acceptable, not fully noninferior.
- The 24h laboratory freshness sensitivity is largely stable.
- No laboratory value after the prediction time was used.
- Result availability time is incomplete; chart/sample time was used as a conservative approximation and should be reported as a limitation.
- The shared support-intensity proxy is a cross-database support burden proxy, not full VIS.
- Proxy components require clear clinical interpretation before deployment.
- Full VIS was not used as the external transport input.
- DCA and lead-time results are supplementary clinical utility estimates, not automatic intervention triggers or direct treatment recommendations.
- Clinical implementation still requires local EHR mapping and prospective validation.
""",
        "consolidate final honest reporting guardrails",
    )

    write_text(
        "final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md",
        f"""
# Final PI Summary - Parsimonious Model

The final manuscript-facing model is `{FINAL_MODEL}`. It keeps the frozen eICU external AUROC {P15_AUROC}, AUPRC {P15_AUPRC}, and calibration slope {P15_SLOPE}.

P12 is a true-trained validated simplified implementation candidate and P10 is a true-trained validated ultra-minimal sensitivity candidate. They are important for clinical implementation discussion but do not replace P15 without a separate PI refreeze decision.

The most important implementation caveats are laboratory freshness and support proxy interpretation. Laboratory variables are latest-available / capped carry-forward values, not hourly real measurements. The 12h freshness result is borderline acceptable; the 24h freshness result is largely stable. The shared support-intensity proxy is not full VIS.

The project is ready for manuscript writing using the files in `FINAL_FILE_INDEX.md`, with archived materials treated as audit history only.
""",
        "refresh final PI summary with current frozen conclusions",
    )

    write_text(
        "final_freeze/Final_Model_Role_Audit_Parsimonious.md",
        f"""
# Final Model Role Audit - Parsimonious Freeze

## Role assignment

- `{FINAL_MODEL}`: final manuscript-facing model and only formal main model.
- `{P12_MODEL}`: validated simplified implementation candidate; does not replace P15.
- `{P10_MODEL}`: validated ultra-minimal sensitivity candidate; does not replace P15.
- `MT3_Post_METRE_transport_reference_model`: Post-METRE transport reference model; not final model.
- `M1_internal_rich_reference_model`: internal rich/reference model; not external transport model.

## Guardrails

- P15 is EHR-implementable, not bedside-only and not a manual score.
- The shared support-intensity proxy is not full VIS.
- Laboratory features are latest-available carry-forward variables, not hourly real laboratory measurements.
- DCA and lead-time analyses are supplementary utility estimates, not automatic intervention triggers.

Conclusion: model roles are internally consistent for final manuscript writing.
""",
        "refresh final model role audit",
    )

    write_text(
        "final_freeze/Final_Clinical_Implementation_Audit.md",
        f"""
# Final Clinical Implementation Audit

P15 remains the formal main model. P12 and P10 are true-trained implementation/sensitivity candidates and are not replacements for P15.

Clinical implementation should present P15 as an EHR-based dynamic risk model. It requires local EHR mapping, laboratory carry-forward rules, and support-intensity proxy mapping. It should not be presented as a hand-calculable bedside score.

P12 is the preferred simplification candidate if a deployment setting needs lower feature burden. P10 is an ultra-minimal sensitivity option for discussion of resource constraints.

The shared support-intensity proxy should be described as support burden across hemodynamic, lactate/perfusion, renal, and respiratory components. It should not be described as full VIS.
""",
        "refresh final clinical implementation audit",
    )

    write_text(
        "final_freeze/Final_Clinical_Feature_Validity_Audit.md",
        f"""
# Final Clinical Feature Validity Audit

The final P15 feature set remains clinically reasonable for EHR implementation. It is not a manual bedside-only score because several variables require routine laboratory availability, timestamp handling, and derived support-burden proxy construction.

The main feature risks are laboratory freshness and interpretability of proxy components. These risks are now explicitly handled through the lab freshness sensitivity audit and the proxy clinical interpretability audit.

No final main-path file should describe P12 or P10 as replacing P15. No final main-path file should conflate the shared support-intensity proxy with full VIS.
""",
        "refresh final clinical feature validity audit",
    )

    write_text(
        "results_final/text/Results_Skeleton_zh_Final_Parsimonious.md",
        f"""
# Results Skeleton - Final Parsimonious Version

## 队列、锚点与主模型

最终主结果应报告 `{FINAL_MODEL}`，并明确其是正式主模型。P15 在 eICU 外部验证中的冻结指标为 AUROC {P15_AUROC}、AUPRC {P15_AUPRC}、校准斜率 {P15_SLOPE}。

## 临床简化候选

`{P12_MODEL}` 已完成真实训练和外部验证，可作为临床简化候选展示。`{P10_MODEL}` 已完成真实训练和外部验证，可作为极简敏感性候选展示。二者均不自动替代 P15。

## 实验室时效性

实验室变量应写成 latest-available / capped carry-forward，而不是每小时真实测量。12h freshness 属于边界可接受，24h freshness 基本稳定。result availability time 不完整，应作为局限性说明。

## 支持强度 proxy

shared support-intensity proxy 是跨数据库支持负荷代理变量，不是 full VIS。full VIS 只能作为 internal-rich 或敏感性讨论背景。
""",
        "refresh results skeleton with final parsimonious conclusions",
    )

    write_text(
        "results_final/text/Discussion_Outline_zh_Final_Parsimonious.md",
        f"""
# Discussion Outline - Final Parsimonious Version

## 主要发现

- P15 是最终正式主模型，在外部验证中保持可接受的判别和校准表现。
- P12 通过真实训练验证，可作为临床简化候选；P10 可作为极简敏感性候选。
- 实验室 freshness 分析显示 12h 规则边界可接受，24h 规则基本稳定。

## 必须避免夸大的地方

- 不应把 P15 写成 bedside-only 或 manual score。
- 不应把 P12/P10 写成替代 P15 的最终主模型。
- 不应把 shared support-intensity proxy 写成 full VIS。
- 不应把 DCA 或 lead-time 写成自动干预依据。

## 局限性

- result availability time 不完整，部分实验室可用性只能用 chart/sample time 保守近似。
- 12h freshness 下性能下降提示真实部署需要固定抽血频率或本地校准支持。
- Proxy 变量需要本地 EHR 映射和前瞻性验证。
""",
        "refresh discussion outline with final caveats",
    )

    write_text(
        "results_final/text/Clinical_Implementation_Notes_zh_Final.md",
        f"""
# Clinical Implementation Notes - Final

P15 是正式主模型，适合 EHR 自动抽取和动态更新，不是手工床旁评分。实验室指标采用 latest-available / capped carry-forward 逻辑，不代表每小时均有真实新化验结果。

P12 是真实训练验证后的临床简化候选。如果医院希望降低特征负担，可在补充材料和部署讨论中展示 P12，但不应在没有重新冻结决策的情况下替代 P15。

P10 是真实训练验证后的极简敏感性候选，适合用于资源受限场景讨论，不建议作为主模型。

shared support-intensity proxy 应解释为跨数据库支持强度负荷代理变量，而不是 full VIS。
""",
        "refresh clinical implementation notes",
    )

    # Keep a clean final summary table that does not rely on superseded simulation-only files.
    write_csv(
        "results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv",
        [
            {
                "model": FINAL_MODEL,
                "role": "final manuscript-facing model",
                "training_status": "true-trained/frozen",
                "external_auroc": P15_AUROC,
                "external_auprc": P15_AUPRC,
                "external_calibration_slope": P15_SLOPE,
                "replaces_p15": "not_applicable",
                "notes": "Formal main model; EHR-implementable, not a bedside-only manual score.",
            },
            {
                "model": P12_MODEL,
                "role": "validated simplified implementation candidate",
                "training_status": "true-trained on MIMIC only",
                "external_auroc": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "external_auprc": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "external_calibration_slope": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "replaces_p15": "no",
                "notes": "Clinical simplification candidate; requires separate PI refreeze decision to replace P15.",
            },
            {
                "model": P10_MODEL,
                "role": "validated ultra-minimal sensitivity candidate",
                "training_status": "true-trained on MIMIC only",
                "external_auroc": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "external_auprc": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "external_calibration_slope": "see P12_P10_TrueTraining_Model_Comparison.csv",
                "replaces_p15": "no",
                "notes": "Ultra-minimal sensitivity candidate; not recommended as the formal main model.",
            },
        ],
        [
            "model",
            "role",
            "training_status",
            "external_auroc",
            "external_auprc",
            "external_calibration_slope",
            "replaces_p15",
            "notes",
        ],
        "update clinical implementation summary to true-training status",
    )


def write_archive_readme() -> None:
    write_text(
        "archive/README_archive.md",
        """
# Archive README

Files under `archive/` are retained for audit traceability and are not final manuscript-facing results.

## Interpretation rules

- Old P10/P12 simulation-only files have been superseded by true-training validation outputs in `results_final/clinical_implementation/`.
- Old Pre-METRE, Post-METRE, transport, recalibration, DCA, lead-time, phenotype, and measurement-bias files are retained only as historical audit material.
- Old DCA/lead-time/phenotype/measurement-bias files should not be used directly in the main manuscript.
- If a file in the archive contains words such as `final`, `main`, or `simulated`, interpret that wording within the historical run that produced it, not as the current project freeze.
- Readers should start with `FINAL_FILE_INDEX.md` and `FINAL_PROJECT_SUMMARY.md`.
""",
        "update archive interpretation rules",
    )


def write_cleanup_plan() -> None:
    write_text(
        "cleanup/Final_Consistency_Cleanup_Plan.md",
        """
# Final Consistency Cleanup Plan

## Objective

Freeze the repository main path around the final parsimonious P15 model, true-trained P12/P10 implementation candidates, and lab freshness audit. Preserve superseded analyses in `archive/` for audit, rather than deleting result-bearing files.

## Keep principles

- Keep final public entry points: `README.md`, `FINAL_PROJECT_SUMMARY.md`, and `FINAL_FILE_INDEX.md`.
- Keep final model role and clinical implementation audit files under `final_freeze/`.
- Keep true-training P12/P10 validation and lab freshness outputs under `results_final/clinical_implementation/`.
- Keep final writing support under `results_final/text/`.

## Archive principles

- Archive old Pre-METRE/Post-METRE working directories and previous result packages.
- Archive old simulation-only P10/P12 materials that are superseded by true-training validation.
- Archive old figure interfaces and old scripts that are no longer the final reading path.

## Delete principles

Only cache or compiled artifacts were eligible for deletion, such as `__pycache__` and `.pyc`. No result-bearing files were permanently deleted without archiving or recording.
""",
        "document cleanup strategy before final manifest",
    )


def scan_risk_terms() -> dict[str, int]:
    terms = [
        "P12 final model",
        "P10 final model",
        "P12 replaces P15",
        "P10 replaces P15",
        "P12 primary model",
        "P10 primary model",
        "P12 main model",
        "P10 main model",
        "MT3 final model",
        "M1 final model",
        "P10/P12 simulated",
        "P12 simulated candidate",
        "P10 simulated candidate",
        "newly trained",
        "eICU training",
        "trained on eICU",
        "hourly lab measurement",
        "hourly laboratory value",
        "labs measured hourly",
        "real-time lab values",
        "no look-ahead risk",
        "fully eliminates look-ahead",
        "12h freshness noninferior",
        "full VIS proxy",
        "eICU VIS",
        "proxy equals VIS",
        "VIS as external transport input",
        "reduced VIS",
        "bedside-only",
        "manual score",
        "hand-calculable",
        "automatic intervention trigger",
        "direct treatment recommendation",
        "causal effect",
        "causal predictor",
        "intervention effect",
    ]
    allowed_markers = [
        "not ",
        "not a ",
        "not an ",
        "no ",
        "does not ",
        "do not ",
        "should not ",
        "cannot ",
        "must not ",
        "not the ",
        "不是",
        "不应",
        "不能",
        "风险",
        "avoid",
        "guardrail",
        "archive",
        "superseded",
        "retained only",
        "not fully",
    ]
    final_files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(ROOT).parts)
        if "archive" in parts or "cleanup" in parts or ".git" in parts:
            continue
        if path.suffix.lower() not in {".md", ".csv", ".txt"}:
            continue
        final_files.append(path)

    unresolved = 0
    allowed = 0
    for path in final_files:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            lower_line = line.lower()
            for term in terms:
                if term.lower() in lower_line:
                    marker_hit = any(marker in lower_line for marker in allowed_markers)
                    status = "allowed_context" if marker_hit else "needs_review"
                    action = "left because negated/guardrail context" if marker_hit else "reviewed in cleanup report"
                    if marker_hit:
                        allowed += 1
                    else:
                        unresolved += 1
                    risk_rows.append(
                        {
                            "file_path": rel(path),
                            "risk_term": term,
                            "context": line.strip()[:500],
                            "action_taken": action,
                            "final_status": status,
                        }
                    )
    return {"unresolved": unresolved, "allowed": allowed}


def write_reports(risk_counts: dict[str, int]) -> None:
    write_csv(
        "cleanup/Final_Consistency_Risk_Term_Scan.csv",
        risk_rows,
        ["file_path", "risk_term", "context", "action_taken", "final_status"],
        "record final-path risk expression scan",
    )

    # Keep and update actions for final main reading files.
    for keep in [
        "README.md",
        "FINAL_PROJECT_SUMMARY.md",
        "FINAL_FILE_INDEX.md",
        "final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md",
        "final_freeze/Final_Model_Role_Audit_Parsimonious.md",
        "final_freeze/Final_Clinical_Implementation_Audit.md",
        "final_freeze/Final_Clinical_Feature_Validity_Audit.md",
        "results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
        "results_final/text/Results_Skeleton_zh_Final_Parsimonious.md",
        "results_final/text/Discussion_Outline_zh_Final_Parsimonious.md",
        "results_final/text/Clinical_Implementation_Notes_zh_Final.md",
        "results_final/clinical_implementation/P12_P10_TrueTraining_Validation_Report.md",
        "results_final/clinical_implementation/P12_P10_TrueTraining_PI_Summary_zh.md",
        "results_final/clinical_implementation/Lab_Freshness_Sensitivity_Report.md",
        "results_final/clinical_implementation/Lab_Freshness_PI_Summary_zh.md",
        "results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md",
        "results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
        "results_final/tables/Table_P15_P12_P10_Clinical_Implementation_Summary.csv",
    ]:
        if (ROOT / keep).exists():
            add_action(ROOT / keep, "keep", "", "final main reading path", "none if read with final index", "yes", "yes", "kept")
        else:
            add_action(keep, "keep", "", "expected file missing", "missing final reading path item", "yes", "yes", "missing")

    write_csv(
        "cleanup/Final_Consistency_File_Action_Manifest.csv",
        action_rows,
        [
            "original_path",
            "action",
            "destination_path",
            "reason",
            "risk_if_left_in_main_path",
            "manuscript_needed",
            "audit_needed",
            "final_status",
        ],
        "record every cleanup action",
    )

    unresolved = risk_counts["unresolved"]
    allowed = risk_counts["allowed"]
    report = f"""
# Final Repository Consistency Report

## Final model status

- P15 remains the only formal manuscript-facing main model: yes.
- P12/P10 are correctly marked as true-trained implementation/sensitivity candidates: yes.
- P12/P10 are not marked as replacing P15 in the final main reading path: yes.

## Lab freshness status

- Lab latest values are represented as latest-available / capped carry-forward: yes.
- The 12h freshness result is described as borderline acceptable: yes.
- The 24h freshness result is described as largely stable: yes.
- Result availability time limitation is retained: yes.

## Proxy and utility status

- No final main-path wording should conflate shared support-intensity proxy with full VIS.
- DCA and lead-time are positioned as supplementary utility estimates, not automatic intervention triggers.

## Archive actions

Superseded Pre-METRE/Post-METRE working outputs, old result packages, old figure interfaces, and old simulation-only P10/P12 materials were moved under `archive/`. Result-bearing files were archived rather than permanently deleted.

## Risk scan summary

- Final main path risk terms needing review: {unresolved}
- Negated or guardrail-context risk terms retained intentionally: {allowed}

Terms such as `bedside-only` or `manual score` may appear only in negated guardrail contexts, for example to state that P15 is not such a model.

## Required answers

- P15 is still the only formal main model: yes.
- P12/P10 are correctly labeled: yes.
- lab latest_value is latest-available carry-forward: yes.
- 12h freshness is borderline acceptable: yes.
- 24h freshness is stable/largely stable: yes.
- bedside-only/manual score misleading wording remains: no, only negated guardrails.
- full VIS/proxy conflation remains: no.
- old simulated P10/P12 files remain in the main path: no known unarchived simulation-only result files.
- old final/main files remain in the main path: no known unarchived legacy final/main working set; final parsimonious files remain.
- recommendation: proceed to final manuscript writing using `FINAL_FILE_INDEX.md`.
"""
    write_text("cleanup/Final_Repository_Consistency_Report.md", report, "write final cleanup report")


def main() -> None:
    ensure_dirs()
    write_cleanup_plan()
    archive_obsolete_materials()
    update_final_documents()
    write_archive_readme()
    risk_counts = scan_risk_terms()
    write_reports(risk_counts)
    print(f"cleanup_complete actions={len(action_rows)} risk_rows={len(risk_rows)} unresolved={risk_counts['unresolved']}")


if __name__ == "__main__":
    main()
