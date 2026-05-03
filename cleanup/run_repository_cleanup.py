from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


SHARE_ROOT = Path(__file__).resolve().parents[1]
LOCAL_ROOT = SHARE_ROOT.parent
CLEANUP_DIR = SHARE_ROOT / "cleanup"
ARCHIVE_DIR = SHARE_ROOT / "archive"

FINAL_COPY_FILES = [
    ("final_freeze/Final_Model_Role_Audit_Parsimonious.md", "final_freeze/Final_Model_Role_Audit_Parsimonious.md"),
    ("final_freeze/Final_Model_Role_Assignment_Parsimonious.csv", "final_freeze/Final_Model_Role_Assignment_Parsimonious.csv"),
    ("final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md", "final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md"),
    ("final_freeze/Final_Parsimonious_Integration_Audit.json", "final_freeze/Final_Parsimonious_Integration_Audit.json"),
    (
        "results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
        "results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
    ),
    (
        "results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
        "results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
    ),
    (
        "results_package/text/Results_Skeleton_zh_Final_Parsimonious.md",
        "results_package/text/Results_Skeleton_zh_Final_Parsimonious.md",
    ),
    (
        "results_package/text/Discussion_Outline_zh_Final_Parsimonious.md",
        "results_package/text/Discussion_Outline_zh_Final_Parsimonious.md",
    ),
    (
        "results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
        "results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
    ),
    ("parsimonious_features/F15_minimal_bedside_set.csv", "parsimonious_features/F15_minimal_bedside_set.csv"),
    ("parsimonious_features/F25_clinical_core_set.csv", "parsimonious_features/F25_clinical_core_set.csv"),
    ("parsimonious_features/F40_balanced_transport_set.csv", "parsimonious_features/F40_balanced_transport_set.csv"),
    ("parsimonious_features/Feature_Retention_Rationale.csv", "parsimonious_features/Feature_Retention_Rationale.csv"),
    ("parsimonious_features/Feature_Retention_Report.md", "parsimonious_features/Feature_Retention_Report.md"),
    ("parsimonious_features/Parsimonious_Model_Comparison.csv", "parsimonious_features/Parsimonious_Model_Comparison.csv"),
    ("parsimonious_features/Parsimonious_Model_Report.md", "parsimonious_features/Parsimonious_Model_Report.md"),
    ("parsimonious_features/Noninferiority_Assessment.csv", "parsimonious_features/Noninferiority_Assessment.csv"),
    ("parsimonious_features/Final_Parsimonious_Model_Recommendation.md", "parsimonious_features/Final_Parsimonious_Model_Recommendation.md"),
    ("parsimonious_features/Manuscript_Update_Notes.md", "parsimonious_features/Manuscript_Update_Notes.md"),
]

FINAL_MAIN_KEEP = {
    ".gitignore",
    "README.md",
    "LOCAL_ASSET_INDEX.md",
    "HEAVY_ARTIFACT_MANIFEST.csv",
    "SYNC_COPIED_MANIFEST.csv",
    "SYNC_EXCLUDED_MANIFEST.csv",
    "cleanup/run_repository_cleanup.py",
    "cleanup/cleanup_plan.md",
    "cleanup/file_action_manifest.csv",
    "cleanup/cleanup_execution_summary.json",
    "final_freeze/Final_Model_Role_Audit_Parsimonious.md",
    "final_freeze/Final_Model_Role_Assignment_Parsimonious.csv",
    "final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md",
    "final_freeze/Final_Parsimonious_Integration_Audit.json",
    "results_package/tables/Table1_Cohort_Characteristics.csv",
    "results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
    "results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
    "results_package/text/Results_Skeleton_zh_Final_Parsimonious.md",
    "results_package/text/Discussion_Outline_zh_Final_Parsimonious.md",
    "results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md",
    "results_package/supplementary/Supplementary_Index.md",
    "parsimonious_features/F15_minimal_bedside_set.csv",
    "parsimonious_features/F25_clinical_core_set.csv",
    "parsimonious_features/F40_balanced_transport_set.csv",
    "parsimonious_features/Feature_Retention_Rationale.csv",
    "parsimonious_features/Feature_Retention_Report.md",
    "parsimonious_features/Parsimonious_Model_Comparison.csv",
    "parsimonious_features/Parsimonious_Model_Report.md",
    "parsimonious_features/Noninferiority_Assessment.csv",
    "parsimonious_features/Final_Parsimonious_Model_Recommendation.md",
    "parsimonious_features/Manuscript_Update_Notes.md",
}

DIRECT_DELETE_PATTERNS = (
    "__pycache__/",
    ".pyc",
    ".pyo",
)


def rel(path: Path) -> str:
    return path.relative_to(SHARE_ROOT).as_posix()


def archive_destination(path: Path) -> Path:
    r = rel(path)
    if r.startswith("results_package/tables/Table2_Main_Model_Comparators.csv"):
        return ARCHIVE_DIR / "legacy_pre_metre_results" / r
    if r.startswith("results_package/tables/Table3_") or r.startswith("results_package/tables/Table4_"):
        return ARCHIVE_DIR / "legacy_pre_metre_results" / r
    if r.startswith("results_package/text/") and not r.endswith("_Final_Parsimonious.md"):
        return ARCHIVE_DIR / "legacy_text_and_skeletons" / r
    if r.startswith("results_package/figures/"):
        return ARCHIVE_DIR / "legacy_figure_interfaces" / r
    if r.startswith("results_package/POST_METRE") or r.startswith("results_package/MANUSCRIPT_READY_INDEX.md"):
        return ARCHIVE_DIR / "legacy_result_indices" / r
    if r.startswith("results_package/update_post_metre_result_package.py"):
        return ARCHIVE_DIR / "legacy_scripts" / r
    if r.startswith("final_freeze/") and not r.endswith("_Parsimonious.md") and "Parsimonious" not in r:
        return ARCHIVE_DIR / "legacy_final_freeze" / r
    if r.startswith("metre_transport/"):
        return ARCHIVE_DIR / "post_metre_reference" / r
    if r.startswith("post_metre_") or r.startswith("post_metre/"):
        return ARCHIVE_DIR / "post_metre_reference" / r
    if r.startswith("transport_model/") or r.startswith("recalibration/"):
        return ARCHIVE_DIR / "legacy_transport_pre_metre" / r
    if r.startswith("phenotype_reassessment/"):
        return ARCHIVE_DIR / "phenotype_audit" / r
    if r.startswith("step9_results_packaging/"):
        return ARCHIVE_DIR / "legacy_scripts" / r
    return ARCHIVE_DIR / "misc_superseded" / r


def reason_for(path: Path, action: str) -> tuple[str, str, str]:
    r = rel(path)
    if action == "keep":
        if "Parsimonious" in r or r.startswith("parsimonious_features/"):
            return "Final P15 parsimonious manuscript-facing artifact.", "low", "yes"
        if r in {"README.md", "LOCAL_ASSET_INDEX.md", "HEAVY_ARTIFACT_MANIFEST.csv"}:
            return "Required repository/data-boundary documentation retained and updated.", "low", "yes"
        return "Still useful in final manuscript-facing entry path.", "low", "yes"
    if action == "delete":
        return "Cache or transient file without manuscript or audit value.", "low", "no"
    if "Post_METRE" in r or r.startswith("metre_transport/") or r.startswith("post_metre_"):
        return "Superseded by final P15 mainline but retained for audit/reference.", "medium", "supplementary/archive"
    if "phenotype" in r.lower():
        return "Phenotype is no longer a default performance route; retained as stratification/explanation audit.", "medium", "supplementary/archive"
    if r.startswith("results_package/figures/") or r.endswith("_Post_METRE.csv") or r.endswith("_Post_METRE.md"):
        return "Old figure/table/text interface superseded by final parsimonious package.", "medium", "archive"
    if r.startswith("final_freeze/"):
        return "Previous final-freeze output superseded by parsimonious final freeze.", "medium", "archive"
    return "Legacy or transitional artifact moved out of the main reading path.", "medium", "archive"


def build_manifest() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(SHARE_ROOT.rglob("*")):
        if ".git" in path.parts or path.is_dir():
            continue
        r = rel(path)
        if any((pat.endswith("/") and pat.strip("/") in path.parts) or r.endswith(pat) for pat in DIRECT_DELETE_PATTERNS):
            action = "delete"
            dest = ""
        elif r in FINAL_MAIN_KEEP or r.startswith("archive/"):
            action = "keep"
            dest = r
        else:
            action = "move_to_archive"
            dest = rel(archive_destination(path))
        reason, risk, needed = reason_for(path, action)
        rows.append(
            {
                "file_path": r,
                "action": action,
                "reason": reason,
                "final_destination": dest,
                "risk_level": risk,
                "whether_needed_for_manuscript": needed,
            }
        )
    for _, dst in FINAL_COPY_FILES:
        if not (SHARE_ROOT / dst).exists():
            rows.append(
                {
                    "file_path": dst,
                    "action": "replace",
                    "reason": "Final parsimonious artifact copied from local verified output into GitHub share repo.",
                    "final_destination": dst,
                    "risk_level": "low",
                    "whether_needed_for_manuscript": "yes",
                }
            )
    return rows


def write_plan_and_manifest(rows: list[dict[str, str]]) -> None:
    CLEANUP_DIR.mkdir(parents=True, exist_ok=True)
    with (CLEANUP_DIR / "file_action_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_path",
                "action",
                "reason",
                "final_destination",
                "risk_level",
                "whether_needed_for_manuscript",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["action"]] = counts.get(row["action"], 0) + 1
    plan = f"""# Repository Cleanup Plan - Final Parsimonious Manuscript

## Objective

Make the GitHub-facing share repository manuscript-facing and P15-first:

- `P15_minimal_bedside_model` is the final clinically parsimonious transport model.
- `MT3_physiology_support_proxy` is retained as the Post-METRE transport reference model.
- `M1_original_rich` is retained as the internal rich/reference model.
- `phenotype` is retained only as stratification/explanation/calibration audit material.
- Full VIS and measurement-process-heavy materials stay out of the final external transport main path.

## Safety rules

- No model retraining.
- No cohort, label, or Step 1-6 modification.
- No permanent deletion of audit-relevant results.
- Superseded outputs are moved to `archive/` with `cleanup/file_action_manifest.csv` traceability.
- Raw data and heavy artifacts remain excluded from GitHub.

## Planned action counts

```json
{json.dumps(counts, ensure_ascii=False, indent=2)}
```

## Final main reading path

- `README.md`
- `LOCAL_ASSET_INDEX.md`
- `HEAVY_ARTIFACT_MANIFEST.csv`
- `final_freeze/*Parsimonious*`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/*Final_Parsimonious.md`
- `parsimonious_features/`
- `archive/` for superseded but audit-relevant material
"""
    (CLEANUP_DIR / "cleanup_plan.md").write_text(plan, encoding="utf-8")


def copy_final_outputs() -> list[str]:
    copied = []
    for src_rel, dst_rel in FINAL_COPY_FILES:
        src = LOCAL_ROOT / src_rel
        dst = SHARE_ROOT / dst_rel
        if not src.exists():
            raise FileNotFoundError(f"Missing local final artifact: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst_rel)
    return copied


def update_readme() -> None:
    readme = """# Sepsis Dynamic Competing-risk Final Manuscript Share Repo

This is the manuscript-facing cleaned repository for the final clinically parsimonious model package.

## Final model line

- Final main clinical transport model: `P15_minimal_bedside_model`
- Feature count: 15
- eICU external AUROC/AUPRC/calibration slope: 0.8103 / 0.1892 / 1.0031
- Post-METRE transport reference: `MT3_physiology_support_proxy`
- Internal rich/reference model: `M1_original_rich`
- Clinical comparator: `C1_dynamic_SOFA`
- Phenotype: stratification / explanation / calibration audit only

## Main reading path

- `final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md`
- `final_freeze/Final_Model_Role_Audit_Parsimonious.md`
- `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
- `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
- `results_package/text/Results_Skeleton_zh_Final_Parsimonious.md`
- `results_package/text/Discussion_Outline_zh_Final_Parsimonious.md`
- `results_package/text/Honest_Reporting_Checklist_Final_Parsimonious.md`
- `parsimonious_features/`

## Archive

Superseded Pre-METRE, Post-METRE transition, old figure/table interfaces, and phenotype audit materials have been moved to `archive/`. They are retained for traceability but are no longer the main manuscript path.

## Data boundary

Raw MIMIC-IV/eICU data, parquet datasets, model binaries, DuckDB databases, and runtime logs are not included in this GitHub repository. See `HEAVY_ARTIFACT_MANIFEST.csv` and `LOCAL_ASSET_INDEX.md`.

## Cleanup audit

See `cleanup/cleanup_plan.md` and `cleanup/file_action_manifest.csv` for every keep/move/delete decision.
"""
    (SHARE_ROOT / "README.md").write_text(readme, encoding="utf-8")

    local_index = """# Local Asset Index

## Included in this cleaned GitHub share repo

- Final parsimonious manuscript-facing package:
  - `final_freeze/*Parsimonious*`
  - `results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv`
  - `results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv`
  - `results_package/text/*Final_Parsimonious.md`
  - `parsimonious_features/`
- Cleanup audit:
  - `cleanup/cleanup_plan.md`
  - `cleanup/file_action_manifest.csv`
- Historical audit material:
  - `archive/`
- Heavy artifact index:
  - `HEAVY_ARTIFACT_MANIFEST.csv`

## Left local only

- Raw clinical databases:
  - `eicu/`
  - `mimic-iv-3.1/`
- Heavy analytical outputs:
  - `*.duckdb`
  - `*.parquet`
  - `*.pkl`
  - `*.gz`
- Runtime logs and transient files

## Current final interpretation

This repository is now centered on `P15_minimal_bedside_model` as the final clinically parsimonious transport model. `MT3_physiology_support_proxy` is retained as a Post-METRE reference, and `M1_original_rich` remains an internal rich/reference model.
"""
    (SHARE_ROOT / "LOCAL_ASSET_INDEX.md").write_text(local_index, encoding="utf-8")


def apply_manifest(rows: list[dict[str, str]]) -> dict[str, object]:
    copied = copy_final_outputs()
    moved = []
    deleted = []
    for row in rows:
        src = SHARE_ROOT / row["file_path"]
        if not src.exists():
            continue
        if row["action"] == "move_to_archive":
            dst = SHARE_ROOT / row["final_destination"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
            moved.append({"from": row["file_path"], "to": row["final_destination"]})
        elif row["action"] == "delete":
            src.unlink()
            deleted.append(row["file_path"])
    update_readme()
    summary = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "copied_final_artifacts": copied,
        "moved_to_archive_count": len(moved),
        "deleted_count": len(deleted),
        "moved_to_archive": moved,
        "deleted": deleted,
        "p15_mainline": True,
    }
    (CLEANUP_DIR / "cleanup_execution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = build_manifest()
    write_plan_and_manifest(rows)
    if args.apply:
        summary = apply_manifest(rows)
    else:
        summary = {"planned_only": True, "action_count": len(rows)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
