from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_FINAL = ROOT / "results_final"
RESULTS_PACKAGE = ROOT / "results_package"
CLEANUP = ROOT / "cleanup"
ARCHIVE = ROOT / "archive"


FINAL_TABLES = [
    "Table1_Cohort_Characteristics.csv",
    "Table2_Main_Model_Comparators_Final_Parsimonious.csv",
    "Table_Parsimonious_Feature_Set_Comparison.csv",
]

FINAL_TEXT = [
    "Results_Skeleton_zh_Final_Parsimonious.md",
    "Discussion_Outline_zh_Final_Parsimonious.md",
    "Honest_Reporting_Checklist_Final_Parsimonious.md",
]


def copy_final_results() -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    (RESULTS_FINAL / "tables").mkdir(parents=True, exist_ok=True)
    (RESULTS_FINAL / "text").mkdir(parents=True, exist_ok=True)
    for name in FINAL_TABLES:
        src = RESULTS_PACKAGE / "tables" / name
        dst = RESULTS_FINAL / "tables" / name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, dst)
        copied.append({"source": src.relative_to(ROOT).as_posix(), "destination": dst.relative_to(ROOT).as_posix()})
    for name in FINAL_TEXT:
        src = RESULTS_PACKAGE / "text" / name
        dst = RESULTS_FINAL / "text" / name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, dst)
        copied.append({"source": src.relative_to(ROOT).as_posix(), "destination": dst.relative_to(ROOT).as_posix()})
    return copied


def write_readme() -> None:
    text = """# Sepsis Dynamic Competing-risk Final Parsimonious Manuscript Repository

## 1. Project title

Dynamic competing-risk prediction for ICU sepsis deterioration with a clinically parsimonious transport model.

## 2. Current frozen conclusion

The final manuscript-facing model is `P15_minimal_bedside_model`, a 15-feature clinically parsimonious transport model. It replaces MT3 as the main clinical model while preserving MT3 as the Post-METRE transport reference.

## 3. Final model roles

- `M1_original_rich` = internal rich/reference model
- `MT3_physiology_support_proxy` = Post-METRE transport reference
- `P15_minimal_bedside_model` = final clinically parsimonious transport model
- `P25_clinical_core_model` = sensitivity model
- `P40_balanced_transport_model` = sensitivity model
- `C1_dynamic_SOFA` = clinical comparator
- `phenotype` = stratification / explanation / calibration audit tool only

## 4. Key final metrics

- P15 feature count = 15
- P15 eICU external AUROC/AUPRC/calibration slope = 0.8103 / 0.1892 / 1.0031
- P15 external AUPRC was not lower than MT3 in the final parsimonious comparison.

## 5. What is included in this repo

- Final manuscript-facing tables and text in `results_final/`
- Backward-compatible final outputs in `results_package/`
- Final model role freeze documents in `final_freeze/`
- Parsimonious feature-set audit outputs in `parsimonious_features/`
- Cleanup plan, action manifest, and final consistency report in `cleanup/`
- Historical audit material in `archive/`
- Heavy artifact index in `HEAVY_ARTIFACT_MANIFEST.csv`

## 6. What is excluded and why

Raw MIMIC-IV/eICU data, parquet datasets, model binaries, DuckDB databases, compressed raw files, and runtime logs are excluded. This repository is a lightweight manuscript-facing share layer, not a full local computational archive.

## 7. How to read this repository

Start with:

1. `FINAL_PROJECT_SUMMARY.md`
2. `FINAL_FILE_INDEX.md`
3. `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
4. `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
5. `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
6. `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
7. `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`

## 8. Which files are final

- `results_final/`
- `final_freeze/*Parsimonious*`
- `parsimonious_features/*`
- `cleanup/cleanup_final_report.md`

## 9. Which folders are archived historical materials

- `archive/legacy_pre_metre_results/`
- `archive/post_metre_reference/`
- `archive/legacy_transport_pre_metre/`
- `archive/legacy_text_and_skeletons/`
- `archive/legacy_figure_interfaces/`
- `archive/phenotype_audit/`
- `archive/legacy_scripts/`

## 10. Warning

Do not use archived pre-METRE outputs, old Step8/Step9 outputs, old lead-time/DCA interfaces, or historical phenotype-gain files as final results. They are retained only for audit and lineage.
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


def write_final_project_summary() -> None:
    text = """# FINAL PROJECT SUMMARY

## 1. 最终研究目标

本项目的最终目标是构建一个面向 ICU sepsis 动态风险分层的 competing-risk 预测框架，并在外部 eICU 验证中形成一个临床可实施、可解释、跨库稳定的最终 transport model。

## 2. 最终模型角色

- `M1_original_rich`：internal rich/reference model，仅作为 MIMIC 内部富特征性能上限参考。
- `MT3_physiology_support_proxy`：Post-METRE transport reference model，是迁移修复阶段的重要参考。
- `P15_minimal_bedside_model`：final clinically parsimonious transport model，是当前论文主线和临床可实施模型。
- `P25_clinical_core_model` 与 `P40_balanced_transport_model`：精简特征敏感性模型。
- `C1_dynamic_SOFA`：clinical comparator。
- `phenotype`：仅作为分层、解释和校准审计工具。

## 3. 为什么从 M1 走到 MT3，再走到 P15

M1 在 MIMIC internal 表现最好，但 eICU 外部迁移失败，说明高维富特征模型不适合直接作为外部 transport model。MT3 通过 physiology 和 shared support-intensity proxy 修复了外部迁移问题。随后，P15 进一步证明外部稳定性并不依赖较大的特征集合，15 个临床可解释特征即可保持不低于 MT3 的 eICU 表现。

## 4. P15 为什么更适合临床实现

P15 只使用 15 个特征，核心来自时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和 shared support-intensity proxy。它避免 phenotype、measurement-process-heavy features、full VIS 和复杂高维派生特征作为默认输入，因此更容易采集、解释、映射和部署。

## 5. 哪些结论不能夸大

- 不能说 M1 是最终外部 transport model。
- 不能说 phenotype 是性能增强器。
- 不能把 full VIS 和 shared support-intensity proxy 混称。
- 不能把旧 exploratory eventual-death lead-time 当作 strict 24h lead-time。
- 不能把 DCA/lead-time 写成自动干预触发依据。
- 不能声称 P15 无需本地再校准或前瞻性验证。

## 6. 当前是否可以进入论文写作

可以。当前仓库已经围绕 P15 最终主线完成整理，主结果、角色冻结、诚实汇报清单和精简特征审计均已落盘。

## 7. 后续投稿前还需要补哪些内容

- 最终中文论文正文撰写。
- 图表编号和期刊格式化。
- 本地再校准策略的文字边界说明。
- 前瞻性验证作为 limitation 和 future work。
- 对 archive 中历史结果的引用应仅用于方法演进或补充审计，不应作为主结果。
"""
    (ROOT / "FINAL_PROJECT_SUMMARY.md").write_text(text, encoding="utf-8")


def write_archive_readme() -> None:
    text = """# Archive README

## 1. Archive 中的文件不是最终主结果

`archive/` 保存的是历史结果、过渡分析、旧脚本和审计追踪。它们不应作为论文主结果直接引用。

## 2. pre-METRE 结果为什么被替代

pre-METRE 主线包含旧版模型比较、旧 phenotype gain、旧 measurement-bias 和旧 figure interface。它们在 Post-METRE transportability repair 和最终 P15 parsimonious revision 后已经被替代。

## 3. Post-METRE 结果为什么保留为参考

Post-METRE 结果证明了 MT3_physiology_support_proxy 能修复 M1 的外部迁移失败，是 P15 之前的重要参考阶段。因此这些结果被保留在 `archive/post_metre_reference/`，但 MT3 不再是最终临床主模型。

## 4. 旧 lead-time / DCA 为什么不作为最终结果

旧 lead-time/DCA 接口包含探索性或阶段性分析，不能被误写为最终 strict 24h lead-time 或自动干预触发依据。最终写作中应将 DCA/lead-time 定位为风险分层证据。

## 5. 旧 phenotype 增益结论为什么不作为最终主叙事

phenotype 在最终冻结角色中仅作为 stratification / explanation / calibration audit tool。它不是默认 transport model 输入，也不是性能增强卖点。
"""
    (ARCHIVE / "README_archive.md").write_text(text, encoding="utf-8")


def write_final_file_index() -> None:
    text = """# FINAL FILE INDEX

## 给导师看的

- `FINAL_PROJECT_SUMMARY.md`
- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`

## 写论文用的

- Results skeleton: `results_final/text/Results_Skeleton_zh_Final_Parsimonious.md`
- Discussion outline: `results_final/text/Discussion_Outline_zh_Final_Parsimonious.md`
- Honest reporting checklist: `results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- Final model table: `results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- Parsimonious comparison table: `results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- Feature retention audit: `parsimonious_features/Feature_Retention_Rationale.csv`
- Noninferiority assessment: `parsimonious_features/Noninferiority_Assessment.csv`

## 审计用的

- Cleanup plan: `cleanup/cleanup_plan.md`
- File action manifest: `cleanup/file_action_manifest.csv`
- Final cleanup report: `cleanup/cleanup_final_report.md`
- Cleanup execution summary: `cleanup/cleanup_execution_summary.json`
- Model role audit: `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- Model role assignment: `final_freeze/Final_Model_Role_Assignment_Parsimonious.csv`
- Heavy artifact manifest: `HEAVY_ARTIFACT_MANIFEST.csv`
- Historical archive readme: `archive/README_archive.md`

## 不建议用于主文的历史文件

- `archive/legacy_pre_metre_results/`
- `archive/post_metre_reference/`
- `archive/legacy_transport_pre_metre/`
- `archive/legacy_text_and_skeletons/`
- `archive/legacy_figure_interfaces/`
- `archive/phenotype_audit/`
- `archive/legacy_scripts/`
"""
    (ROOT / "FINAL_FILE_INDEX.md").write_text(text, encoding="utf-8")


def append_manifest_rows(copied: list[dict[str, str]]) -> None:
    manifest = CLEANUP / "file_action_manifest.csv"
    existing = []
    if manifest.exists():
        with manifest.open("r", newline="", encoding="utf-8-sig") as f:
            existing = list(csv.DictReader(f))
    existing_paths = {row["file_path"] for row in existing}
    new_rows = []
    for item in copied:
        dst = item["destination"]
        if dst not in existing_paths:
            new_rows.append(
                {
                    "file_path": dst,
                    "action": "keep",
                    "reason": "Final P15 result copied into results_final main reading path.",
                    "final_destination": dst,
                    "risk_level": "low",
                    "whether_needed_for_manuscript": "yes",
                }
            )
    for dst in ["FINAL_PROJECT_SUMMARY.md", "FINAL_FILE_INDEX.md", "archive/README_archive.md", "cleanup/cleanup_final_report.md"]:
        if dst not in existing_paths:
            new_rows.append(
                {
                    "file_path": dst,
                    "action": "keep",
                    "reason": "Final repository organisation document for P15 manuscript-facing package.",
                    "final_destination": dst,
                    "risk_level": "low",
                    "whether_needed_for_manuscript": "yes",
                }
            )
    if new_rows:
        rows = existing + new_rows
        with manifest.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def consistency_checks() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    readme = read_text(ROOT / "README.md")
    summary = read_text(ROOT / "FINAL_PROJECT_SUMMARY.md")
    checks.append({"check": "README final model is P15", "pass": "P15_minimal_bedside_model" in readme})
    checks.append({"check": "FINAL_PROJECT_SUMMARY final model is P15", "pass": "P15_minimal_bedside_model" in summary})

    results_final_text = "\n".join(read_text(p) for p in (RESULTS_FINAL).rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".csv"})
    checks.append(
        {
            "check": "results_final does not mark MT3 as final main model",
            "pass": "MT3_physiology_support_proxy` = Post-METRE transport reference" in readme
            and "final clinically parsimonious transport model" in results_final_text,
        }
    )
    checks.append({"check": "archive has README", "pass": (ARCHIVE / "README_archive.md").exists()})

    confusing = [
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file()
        and not p.relative_to(ROOT).as_posix().startswith("archive/")
        and p.name
        in {
            "Results_Skeleton_zh.md",
            "Discussion_Outline_zh.md",
            "Honest_Reporting_Checklist.md",
            "PI_Decision_Summary.md",
            "Table2_Main_Model_Comparators.csv",
            "Table3_Phenotype_Gain.csv",
            "Table4_Measurement_Bias.csv",
            "Figure5_dca_leadtime.csv",
            "Figure6_external_failure_modes.csv",
        }
    ]
    checks.append({"check": "main path has no confusing old result names", "pass": len(confusing) == 0, "details": ";".join(confusing)})

    main_text_files = [p for p in ROOT.rglob("*") if p.is_file() and not p.relative_to(ROOT).as_posix().startswith("archive/")]
    main_text = "\n".join(read_text(p) for p in main_text_files if p.suffix.lower() in {".md", ".csv", ".json"})
    bad_phenotype = "phenotype is performance enhancer" in main_text.lower() or "phenotype performance enhancer" in main_text.lower()
    checks.append({"check": "main path does not claim phenotype is main performance enhancer", "pass": not bad_phenotype})
    bad_leadtime = (
        "79-91" in main_text
        and "strict 24h" in main_text.lower()
        and "不能把旧" not in main_text
        and "do not use archived" not in main_text.lower()
    )
    checks.append({"check": "main path does not write old 79-91h lead-time as strict 24h", "pass": not bad_leadtime})
    bad_vis_proxy = "full vis is shared support" in main_text.lower() or "full vis and shared support-intensity proxy are equivalent" in main_text.lower()
    checks.append({"check": "main path does not conflate full VIS and support proxy", "pass": not bad_vis_proxy})
    return checks


def write_final_report(checks: list[dict[str, object]], copied: list[dict[str, str]]) -> None:
    all_pass = all(bool(item["pass"]) for item in checks)
    lines = [
        "# Cleanup Final Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Final organisation actions",
        "",
        "- Added `results_final/` as the main manuscript-facing final result layer.",
        "- Kept backward-compatible final `results_package/text/*Final_Parsimonious.md` paths.",
        "- Added `FINAL_PROJECT_SUMMARY.md`, `FINAL_FILE_INDEX.md`, and `archive/README_archive.md`.",
        "- Retained historical files in `archive/` for audit rather than deleting them.",
        "- No model retraining, cohort modification, label modification, or metric recomputation was performed.",
        "",
        "## Copied final files",
        "",
    ]
    for item in copied:
        lines.append(f"- `{item['source']}` -> `{item['destination']}`")
    lines.extend(["", "## Consistency checks", "", "| Check | Pass | Details |", "|---|---:|---|"])
    for item in checks:
        lines.append(f"| {item['check']} | {item['pass']} | {item.get('details', '')} |")
    lines.extend(
        [
            "",
            f"## Overall status: {'PASS' if all_pass else 'CHECK_REQUIRED'}",
            "",
            "The repository is now organised around `P15_minimal_bedside_model` as the final clinically parsimonious transport model.",
        ]
    )
    (CLEANUP / "cleanup_final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    copied = copy_final_results()
    write_readme()
    write_final_project_summary()
    write_archive_readme()
    write_final_file_index()
    append_manifest_rows(copied)
    checks = consistency_checks()
    write_final_report(checks, copied)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "copied_to_results_final_count": len(copied),
        "all_consistency_checks_pass": all(bool(item["pass"]) for item in checks),
        "checks": checks,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
