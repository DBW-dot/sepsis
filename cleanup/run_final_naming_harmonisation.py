from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


DISPLAY_MODEL = {
    "M1_original_rich": "M1_internal_rich_reference_model",
    "MT3_physiology_support_proxy": "MT3_Post_METRE_transport_reference_model",
    "MT3_full_transport_set": "MT3_Post_METRE_transport_reference_model",
    "P15_minimal_bedside_model": "P15_clinically_parsimonious_transport_model",
    "P25_clinical_core_model": "P25_clinical_core_sensitivity_model",
    "P40_balanced_transport_model": "P40_balanced_transport_sensitivity_model",
    "C1_dynamic_SOFA": "C1_dynamic_SOFA_clinical_comparator",
    "phenotype": "early_static_phenotype_audit_tool",
}

MODEL_ROLE = {
    "M1_original_rich": "internal rich/reference model",
    "MT3_physiology_support_proxy": "Post-METRE transport reference model",
    "MT3_full_transport_set": "Post-METRE transport reference model",
    "P15_minimal_bedside_model": "final clinically parsimonious transport model",
    "P25_clinical_core_model": "sensitivity model",
    "P40_balanced_transport_model": "sensitivity model",
    "C1_dynamic_SOFA": "clinical comparator",
    "phenotype": "stratification / explanation / calibration audit tool only",
}

MODEL_NOTE = {
    "P15_minimal_bedside_model": (
        "Not an all-bedside score; includes routine vital signs, routine laboratory variables, "
        "time-anchor variables, and a shared support-intensity proxy."
    ),
    "MT3_physiology_support_proxy": (
        "Post-METRE transport reference, not the final clinically parsimonious model."
    ),
    "MT3_full_transport_set": (
        "Post-METRE transport reference, not the final clinically parsimonious model."
    ),
    "M1_original_rich": "Internal rich/reference model only, not an external transport model.",
    "phenotype": "Early static phenotype is retained for stratification, explanation, and calibration audit only.",
}

FEATURE_DISPLAY = {
    "F15": "F15_clinically_parsimonious_feature_set",
    "F15_minimal_bedside_set": "F15_clinically_parsimonious_feature_set",
    "F25": "F25_clinical_core_feature_set",
    "F25_clinical_core_set": "F25_clinical_core_feature_set",
    "F40": "F40_balanced_transport_feature_set",
    "F40_balanced_transport_set": "F40_balanced_transport_feature_set",
    "MT3 full transport set": "MT3_full_transport_reference_feature_set",
    "MT3_full_transport_set": "MT3_full_transport_reference_feature_set",
}

FEATURE_LEGACY = {
    "F15": "F15_minimal_bedside_set",
    "F15_minimal_bedside_set": "F15_minimal_bedside_set",
    "F25": "F25_clinical_core_set",
    "F25_clinical_core_set": "F25_clinical_core_set",
    "F40": "F40_balanced_transport_set",
    "F40_balanced_transport_set": "F40_balanced_transport_set",
    "MT3 full transport set": "MT3_full_transport_set",
    "MT3_full_transport_set": "MT3_full_transport_set",
}


TEXT_FILES: dict[str, str] = {
    "README.md": """# Sepsis Dynamic Competing-risk Final Parsimonious Manuscript Repository

## 1. Project title

Dynamic competing-risk prediction for ICU sepsis deterioration with a clinically parsimonious transport model.

## 2. Current frozen conclusion

The final manuscript-facing model is `P15_clinically_parsimonious_transport_model`, using the legacy internal alias `P15_minimal_bedside_model`. It is a 15-feature clinically parsimonious transport model, not an all-bedside manual score. It includes routine vital signs, routine laboratory values, time-anchor variables, and a shared support-intensity proxy. It replaces MT3 as the main clinical model while preserving MT3 as the Post-METRE transport reference.

最终论文主模型为 P15 临床精简迁移模型。该模型沿用历史技术名 `P15_minimal_bedside_model`，但不应理解为完全床旁人工评分；其 15 个特征包括时间锚点、常规生命体征、常规实验室指标和共享支持强度代理变量。

## 3. Final model roles

- `M1_original_rich` / display name `M1_internal_rich_reference_model` = internal rich/reference model
- `MT3_physiology_support_proxy` / display name `MT3_Post_METRE_transport_reference_model` = Post-METRE transport reference
- `P15_minimal_bedside_model` / display name `P15_clinically_parsimonious_transport_model` = final clinically parsimonious transport model
- `P25_clinical_core_model` = sensitivity model
- `P40_balanced_transport_model` = sensitivity model
- `C1_dynamic_SOFA` = clinical comparator
- `phenotype` = early static phenotype for stratification / explanation / calibration audit only

## 4. Key final metrics

- P15 feature count = 15
- P15 eICU external AUROC/AUPRC/calibration slope = 0.8103 / 0.1892 / 1.0031
- P15 external AUPRC was not lower than MT3 in the final parsimonious comparison.

## 5. What is included in this repo

- Final manuscript-facing tables and text in `results_final/`
- Backward-compatible final outputs in `results_package/`
- Final model role freeze documents in `final_freeze/`
- Parsimonious feature-set audit outputs in `parsimonious_features/`
- Cleanup and naming harmonisation reports in `cleanup/`
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
- `cleanup/Final_Naming_Harmonisation_Report.md`

## 9. Which folders are archived historical materials

- `archive/legacy_pre_metre_results/`
- `archive/post_metre_reference/`
- `archive/legacy_transport_pre_metre/`
- `archive/legacy_text_and_skeletons/`
- `archive/legacy_figure_interfaces/`
- `archive/phenotype_audit/`
- `archive/legacy_scripts/`

## 10. Warning

Do not use archived pre-METRE outputs, old Step8/Step9 outputs, old lead-time/DCA interfaces, or historical phenotype-gain files as final results. They are retained only for audit and lineage. Do not describe P15 as an all-bedside or manually calculated score; do not describe MT3 as the final clinical model; do not use phenotype as a default performance driver; and do not conflate full VIS with the shared support-intensity proxy.
""",
    "FINAL_PROJECT_SUMMARY.md": """# FINAL PROJECT SUMMARY

## 1. 最终研究目标

本项目的最终目标是构建一个面向 ICU sepsis 动态恶化风险的 competing-risk 预测框架，并在外部 eICU 验证中形成一个临床精简、可解释、跨库稳定的 transport model。

## 2. 最终模型角色

- `M1_original_rich` / `M1_internal_rich_reference_model`：内部富特征参考模型，仅作为 MIMIC internal 性能上限参考。
- `MT3_physiology_support_proxy` / `MT3_Post_METRE_transport_reference_model`：Post-METRE 迁移参考模型，是迁移修复阶段的重要参考，但不是最终临床主模型。
- `P15_minimal_bedside_model` / `P15_clinically_parsimonious_transport_model`：最终临床精简迁移模型，是当前论文主线和临床可实施模型。旧名仅作为 legacy/internal alias 保留。
- `P25_clinical_core_model` 与 `P40_balanced_transport_model`：精简特征敏感性模型。
- `C1_dynamic_SOFA`：临床对照模型。
- `phenotype`：早期静态表型，仅作为分层、解释和校准审计工具。

## 3. 为什么从 M1 走到 MT3，再走到 P15

M1 在 MIMIC internal 表现最好，但 eICU 外部迁移不稳定，说明高维富特征模型不适合直接作为外部 transport model。MT3 通过 physiology 和 shared support-intensity proxy 修复了主要迁移问题。随后，P15 进一步证明外部稳定性并不依赖较大的特征集合：15 个临床可解释特征即可保持不低于 MT3 的 eICU 表现。

## 4. P15 为什么更适合临床实现

P15 只使用 15 个特征，核心来自时间锚点、常规生命体征、常规实验室指标、肾功能、凝血/炎症和 shared support-intensity proxy。它不是全床旁或人工手算评分，而是临床精简迁移模型：保留常规 ICU 可获得变量，避免 phenotype、measurement-process-heavy features、full VIS 和复杂高维派生特征作为默认 transport 输入。

## 5. 哪些结论不能夸大

- 不能说 M1 是最终外部 transport model。
- 不能说 MT3 是最终临床主模型；MT3 是 Post-METRE transport reference。
- 不能说 phenotype 是性能增强器；phenotype 只用于分层、解释和校准审计。
- 不能把 full VIS 和 shared support-intensity proxy 混称；full VIS 仅用于 internal-rich/sensitivity，transport model 使用 shared support-intensity proxy。
- 不能把探索性最终死亡提前量当作严格 24 小时首次预警提前量。
- 不能把 DCA/lead-time 写成自动干预触发依据。
- 不能声称 P15 无需本地再校准或前瞻性验证。

## 6. 当前是否可以进入论文写作

可以。当前仓库已经围绕 P15 临床精简迁移模型完成整理，主结果、模型角色冻结、诚实汇报清单和精简特征审计均已落盘。

## 7. 后续投稿前还需要补哪些内容

- 最终中文论文正文撰写。
- 图表编号和期刊格式化。
- 本地再校准策略的文字边界说明。
- 前瞻性验证作为 limitation 和 future work。
- archive 中历史结果仅用于方法演进或补充审计，不应作为主结果。
""",
    "FINAL_FILE_INDEX.md": """# FINAL FILE INDEX

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
- Naming harmonisation report: `cleanup/Final_Naming_Harmonisation_Report.md`
- Naming harmonisation changes: `cleanup/Final_Naming_Harmonisation_Changes.csv`
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
""",
    "final_freeze/Final_Model_Role_Audit_Parsimonious.md": """# Final Model Role Audit - Parsimonious Integration

## Verdict

Final parsimonious model role consistency: `PASS`.

## Frozen roles

| Technical / legacy ID | Manuscript display name | Frozen role |
|---|---|---|
| M1_original_rich | M1_internal_rich_reference_model | internal rich/reference model |
| MT3_physiology_support_proxy | MT3_Post_METRE_transport_reference_model | Post-METRE transport reference model |
| P15_minimal_bedside_model | P15_clinically_parsimonious_transport_model | final clinically parsimonious transport model |
| P25_clinical_core_model | P25_clinical_core_sensitivity_model | sensitivity model |
| P40_balanced_transport_model | P40_balanced_transport_sensitivity_model | sensitivity model |
| C1_dynamic_SOFA | C1_dynamic_SOFA_clinical_comparator | clinical comparator |
| phenotype | early_static_phenotype_audit_tool | stratification / explanation / calibration audit tool |

## Naming guardrails

- P15 should be described as a clinically parsimonious transport model, not as an all-bedside manual score.
- `P15_minimal_bedside_model` is retained only as a legacy/internal alias for traceability.
- MT3 is a Post-METRE transport reference model, not the final clinical model.
- M1 is an internal rich/reference model, not the external transport model.
- Early static phenotype is retained only for stratification, explanation, and calibration audit.
- Full VIS is retained only for internal-rich/sensitivity analyses; the cross-database transport model uses the shared support-intensity proxy.

## Guardrails verified

- No model was retrained in this integration step.
- Cohort, Step 1-6 artifacts, dual-anchor logic, Sepsis-3 suspected infection definition, and 24h competing-risk labels were not modified.
- eICU remains external validation only.
- Phenotype is not restored as a default transport input.
- Full VIS is not used as an external transport input.
- Measurement-process variables are not restored into the final transport model.
""",
    "final_freeze/FINAL_PI_SUMMARY_PARSIMONIOUS.md": """# FINAL PI SUMMARY - Parsimonious Model

## 1. 为什么“特征太多”的问题已经解决？

我们新增并完成了临床精简特征集实验，比较 F15、F25、F40 与 MT3 transport reference。最终 P15 仅保留 15 个临床可解释特征，且不使用 phenotype、measurement intensity、full VIS 或高维复杂派生变量作为默认 transport 输入。

## 2. P15 为什么可以替代 MT3？

P15 在 eICU 外部验证中的 AUROC/AUPRC/calibration slope 为 0.8103/0.1892/1.0031，MT3 为 0.8090/0.1863/0.9652。P15 的 AUPRC 相对 MT3 没有下降，反而略高，并且 calibration slope 更接近 1。

## 3. 15 个特征是否足够临床实施？

从特征结构看，P15 主要包含时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和 shared support-intensity proxy，均可对应 ICU 常规临床信息或清晰 proxy。它不是全床旁无实验室模型，也不是人工手算评分；更准确的名称是 P15 临床精简迁移模型。

## 4. P15 相比 MT3 损失了多少性能？

按 eICU external AUPRC，P15 没有性能损失，AUPRC 从 MT3 的 0.1863 到 P15 的 0.1892；AUROC 也从 MT3 的 0.8090 到 P15 的 0.8103，基本持平。

## 5. 对论文投稿有什么好处？

该结果直接回应“特征太多、临床难以实现”的质疑。论文可以把主模型叙事从高维 transport model 调整为临床精简、可解释、跨库稳定的 P15 clinically parsimonious transport model，同时保留 MT3 作为 Post-METRE 迁移参考模型。

## 6. 是否可以进入最终中文论文写作？

可以。建议进入最终中文论文重写阶段，但必须诚实保留：M1 是 internal rich/reference model；MT3 是 Post-METRE reference；P15 是 final clinically parsimonious transport model；P15 仍需本地再校准和前瞻性验证。
""",
    "results_final/text/Results_Skeleton_zh_Final_Parsimonious.md": """# Results Skeleton zh - Final Parsimonious

## 主要模型和临床精简特征集

在保持既有队列、t_sepsis/t_ICU 双锚点、Sepsis-3 疑似感染定义和 24h competing-risk label 不变的前提下，我们完成了临床精简特征集实验。F15_clinically_parsimonious_feature_set、F25_clinical_core_set 和 F40_balanced_transport_set 均成功训练，并与 MT3_Post_METRE_transport_reference_model 在同一框架下比较。

## 临床精简特征集与 P15 clinically parsimonious transport model

P15_clinically_parsimonious_transport_model 沿用 legacy/internal alias `P15_minimal_bedside_model`，但它不是全床旁人工评分。该模型仅使用 15 个临床可解释特征，包括时间锚点、常规生命体征、常规实验室指标和 shared support-intensity proxy。在 eICU 外部验证中，P15 的 AUROC/AUPRC/calibration slope 为 0.8103/0.1892/1.0031。

这一表现不低于 MT3_Post_METRE_transport_reference_model（legacy ID `MT3_physiology_support_proxy`；eICU AUROC/AUPRC/calibration slope 为 0.8090/0.1863/0.9652），说明模型的外部迁移能力主要依赖少数稳定、可迁移的病理生理变量和共享支持强度代理变量，而不是高维 measurement-process 或复杂派生特征。

因此，P15 被冻结为最终推荐的临床精简迁移模型；MT3 保留为 Post-METRE transport reference 和性能参考。
""",
    "results_final/text/Discussion_Outline_zh_Final_Parsimonious.md": """# Discussion Outline zh - Final Parsimonious

## 1. 高维特征并非必要

本轮结果显示，外部迁移表现并不依赖高维特征堆叠。P15 clinically parsimonious transport model 使用 15 个临床可解释特征即可达到与 MT3 Post-METRE transport reference 相当甚至略高的 eICU AUPRC，并保持接近 1 的 calibration slope。

## 2. 临床可实施性与外部迁移性可以同时获得

P15 支持“少而稳”的 clinical transport model 叙事：保留时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和 shared support-intensity proxy，减少跨库语义不稳定的复杂变量。它不是全床旁或手工评分模型，而是面向 ICU 常规数据流的临床精简迁移模型。

## 3. Measurement-process 与复杂派生特征的限制

高维 measurement-process 特征、复杂窗口统计和仅在 MIMIC 中稳定的派生变量不应作为外部 transport model 的默认输入。它们可以提高内部表现，但可能牺牲跨库稳定性和临床解释性。

## 4. full VIS 与 shared support-intensity proxy 的边界

Full VIS 仅保留在 internal-rich/sensitivity 分析中。外部迁移主模型使用 shared support-intensity proxy，二者不能混称。shared support-intensity proxy 是跨数据库支持强度表达，而不是 full VIS 的同义词。

## 5. phenotype 的定位

Early static phenotype 只用于分层、解释和校准审计，不应被表述为默认性能增强器或最终 transport model 的核心输入。

## 6. 仍需谨慎

P15 仍需本地再校准和前瞻性验证。当前 DCA/lead-time 结果应定位为风险分层证据，而不是自动干预触发器。严格主结果应使用 strict 24h first-alarm lead-time；探索性结果应标注为 exploratory eventual-death lead-time。
""",
    "results_final/text/Honest_Reporting_Checklist_Final_Parsimonious.md": """# Honest Reporting Checklist - Final Parsimonious

- M1_original_rich / M1_internal_rich_reference_model 仍是 MIMIC internal 表现最强的 rich/reference model。
- P15_clinically_parsimonious_transport_model 是最终推荐的临床精简外部 transport model；`P15_minimal_bedside_model` 仅作为 legacy/internal alias 保留。
- P15 不是全床旁人工评分；它包含常规实验室指标和 shared support-intensity proxy。
- MT3_physiology_support_proxy / MT3_Post_METRE_transport_reference_model 是 Post-METRE transport reference model，不再是最终主临床模型。
- phenotype_label 不是性能增强器；early static phenotype 仅作为 stratification / explanation / calibration audit tool。
- full VIS 仍不是 eICU external transport 输入；外部 transport 使用 shared support-intensity proxy。
- P15 虽然外部表现稳定，仍需本地校准和前瞻性验证。
- DCA/lead-time 应定位为风险分层，而非自动干预触发。
- strict 24h first-alarm lead-time 与 exploratory eventual-death lead-time 必须分开表述。
- 不应隐藏 F25 的 AUPRC 边界下降或 F40 的 calibration slope 不佳。
""",
    "parsimonious_features/Final_Parsimonious_Model_Recommendation.md": """# Final Parsimonious Model Recommendation

- Recommended clinical transport model: `P15_clinically_parsimonious_transport_model`.
- Legacy/internal alias: `P15_minimal_bedside_model`.
- Recommended feature set display name: `F15_clinically_parsimonious_feature_set`.
- Legacy feature-set alias: `F15_minimal_bedside_set` (15 features).
- eICU AUROC/AUPRC/slope: 0.8103 / 0.1892 / 1.0031.
- MT3 reference display name: `MT3_Post_METRE_transport_reference_model`.
- MT3 legacy ID: `MT3_physiology_support_proxy`.
- MT3 reference eICU AUROC/AUPRC/slope: 0.8090 / 0.1863 / 0.9652.
- AUPRC drop vs MT3: -1.54%.
- Main-text replacement recommendation: True.
- Reason: accepted by noninferiority thresholds with the smallest feature count.

P15 should be described as a clinically parsimonious transport model, not as an all-bedside or manually calculated score. It includes routine vital signs, routine laboratory variables, time anchors, and a shared support-intensity proxy.

MT3 should remain as the Post-METRE transport reference and performance comparator after P15 is accepted as the main clinically parsimonious model.
""",
    "parsimonious_features/Manuscript_Update_Notes.md": """# Manuscript Update Notes

- Do not rewrite the cohort, anchor, or label methods.
- Add a clinical parsimony experiment that compares F15, F25, F40, and MT3 under the same MIMIC-training/eICU-external-validation design.
- The recommended parsimonious model is `P15_clinically_parsimonious_transport_model` with legacy/internal alias `P15_minimal_bedside_model`.
- Use feature-count reduction and retained vital-sign, routine-laboratory, organ-function, time-anchor, and shared support-intensity proxy variables to answer clinical implementability concerns.
- Do not describe P15 as an all-bedside or manually calculated score; it includes routine labs and the shared support-intensity proxy.
- Keep early static phenotype as stratification/explanation/calibration audit only.
- Keep MT3 as the Post-METRE transport reference, not as the final clinical model.
- Keep full VIS limited to internal-rich/sensitivity analyses and do not conflate it with the shared support-intensity proxy.
""",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def update_text_files(changes: list[dict[str, str]]) -> None:
    for rel, text in TEXT_FILES.items():
        before = read_text(ROOT / rel) if (ROOT / rel).exists() else ""
        write_text(rel, text)
        changes.append(
            {
                "file_path": rel,
                "change_type": "rewrite_text",
                "old_expression": "legacy wording / mojibake / ambiguous bedside naming",
                "new_expression": "clinically parsimonious transport wording with legacy alias",
                "legacy_alias_preserved": "yes",
                "note": "No metrics, cohort, feature list, label, or model artifact was changed.",
            }
        )

    # Keep results_package synchronized with the final text layer.
    for name in [
        "Results_Skeleton_zh_Final_Parsimonious.md",
        "Discussion_Outline_zh_Final_Parsimonious.md",
        "Honest_Reporting_Checklist_Final_Parsimonious.md",
    ]:
        src = ROOT / "results_final" / "text" / name
        dst = ROOT / "results_package" / "text" / name
        if dst.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            changes.append(
                {
                    "file_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                    "change_type": "sync_text_copy",
                    "old_expression": "older final parsimonious copy",
                    "new_expression": "same naming as results_final",
                    "legacy_alias_preserved": "yes",
                    "note": "Synchronized backward-compatible results_package text.",
                }
            )

    for rel in ["LOCAL_ASSET_INDEX.md", "cleanup/cleanup_plan.md", "cleanup/cleanup_final_report.md"]:
        path = ROOT / rel
        if not path.exists():
            continue
        text = read_text(path)
        original = text
        text = text.replace(
            "`P15_minimal_bedside_model` as the final clinically parsimonious transport model",
            "`P15_clinically_parsimonious_transport_model` as the final clinically parsimonious transport model "
            "(legacy alias `P15_minimal_bedside_model`)",
        )
        text = text.replace(
            "`P15_minimal_bedside_model` is the final clinically parsimonious transport model.",
            "`P15_clinically_parsimonious_transport_model` is the final clinically parsimonious transport model "
            "(legacy alias `P15_minimal_bedside_model`).",
        )
        text = text.replace(
            "The repository is now organised around `P15_minimal_bedside_model` as the final clinically parsimonious transport model.",
            "The repository is now organised around `P15_clinically_parsimonious_transport_model` as the final clinically parsimonious transport model; `P15_minimal_bedside_model` is retained only as a legacy/internal alias.",
        )
        if text != original:
            path.write_text(text, encoding="utf-8", newline="\n")
            changes.append(
                {
                    "file_path": rel,
                    "change_type": "targeted_text_update",
                    "old_expression": "P15_minimal_bedside_model as display name",
                    "new_expression": "P15_clinically_parsimonious_transport_model with legacy alias",
                    "legacy_alias_preserved": "yes",
                    "note": "Updated cleanup/index metadata wording only.",
                }
            )


def model_display(model_name: str) -> str:
    return DISPLAY_MODEL.get(model_name, model_name)


def model_role(model_name: str, existing: str = "") -> str:
    return MODEL_ROLE.get(model_name, existing)


def model_note(model_name: str) -> str:
    return MODEL_NOTE.get(model_name, "")


def feature_display(feature_set: str) -> str:
    return FEATURE_DISPLAY.get(feature_set, "")


def feature_legacy(feature_set: str) -> str:
    return FEATURE_LEGACY.get(feature_set, feature_set if feature_set else "")


def read_csv_normalized(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = [(name or "").lstrip("\ufeff") for name in (reader.fieldnames or [])]
        rows = [{(key or "").lstrip("\ufeff"): value for key, value in raw.items()} for raw in reader]
    return fields, rows


def add_or_update_columns(rel: str, changes: list[dict[str, str]]) -> None:
    path = ROOT / rel
    if not path.exists():
        return

    original_fields, rows = read_csv_normalized(path)
    if not rows and rel == "results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv":
        backup = ROOT / "results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv"
        if backup.exists():
            original_fields, rows = read_csv_normalized(backup)

    if not rows:
        return

    required = [
        "display_model_name",
        "display_feature_set_name",
        "legacy_model_id",
        "legacy_feature_set_id",
        "manuscript_role",
        "naming_note",
    ]
    fields = original_fields[:]
    for col in required:
        if col not in fields:
            fields.append(col)

    for row in rows:
        model_name = row.get("model_name", "")
        feature_set = row.get("feature_set", "")
        role = row.get("role", "")

        row["display_model_name"] = model_display(model_name) if model_name else row.get("display_model_name", "")
        row["display_feature_set_name"] = feature_display(feature_set) if feature_set else row.get("display_feature_set_name", "")
        row["legacy_model_id"] = model_name or row.get("legacy_model_id", "")
        row["legacy_feature_set_id"] = feature_legacy(feature_set) if feature_set else row.get("legacy_feature_set_id", "")
        row["manuscript_role"] = model_role(model_name, role) if model_name else row.get("manuscript_role", role)

        notes = []
        if model_name in MODEL_NOTE:
            notes.append(MODEL_NOTE[model_name])
        if feature_set in ("F15", "F15_minimal_bedside_set"):
            notes.append("F15 is not an all-bedside score; it includes routine labs and a shared support-intensity proxy.")
        row["naming_note"] = " ".join(notes) or row.get("naming_note", "")

        if model_name == "P15_minimal_bedside_model":
            if "role" in row:
                row["role"] = "final clinically parsimonious transport model"
            if "interpretation" in row:
                row["interpretation"] = (
                    "Final clinically parsimonious transport model; 15 features with stable eICU discrimination "
                    "and calibration. Not an all-bedside score; includes routine labs and a shared support-intensity proxy."
                )
        if model_name in ("MT3_physiology_support_proxy", "MT3_full_transport_set"):
            if "role" in row:
                row["role"] = "Post-METRE transport reference model"
            if "interpretation" in row:
                row["interpretation"] = (
                    "Post-METRE transport reference and comparator for the clinically parsimonious P15 model."
                )
        if feature_set == "F15" and "recommendation" in row:
            row["recommendation"] = "final recommended clinically parsimonious transport model"
        if model_name == "MT3_full_transport_set" and "recommendation" in row:
            row["recommendation"] = "Post-METRE transport reference comparator"

        if "notes" in row:
            row["notes"] = row["notes"].replace(
                "15 interpretable bedside/core physiology features",
                "15 clinically parsimonious features including routine labs and shared support-intensity proxy",
            )

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    changes.append(
        {
            "file_path": rel,
            "change_type": "csv_display_columns",
            "old_expression": "technical IDs only",
            "new_expression": "display names plus preserved legacy IDs",
            "legacy_alias_preserved": "yes",
            "note": "Added manuscript-facing naming columns without changing metrics.",
        }
    )


def update_csv_files(changes: list[dict[str, str]]) -> None:
    csv_targets = [
        "final_freeze/Final_Model_Role_Assignment_Parsimonious.csv",
        "results_final/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
        "results_final/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
        "results_package/tables/Table2_Main_Model_Comparators_Final_Parsimonious.csv",
        "results_package/tables/Table_Parsimonious_Feature_Set_Comparison.csv",
        "parsimonious_features/F15_minimal_bedside_set.csv",
        "parsimonious_features/F25_clinical_core_set.csv",
        "parsimonious_features/F40_balanced_transport_set.csv",
        "parsimonious_features/Feature_Retention_Rationale.csv",
        "parsimonious_features/Noninferiority_Assessment.csv",
        "parsimonious_features/Parsimonious_Model_Comparison.csv",
    ]
    for rel in csv_targets:
        add_or_update_columns(rel, changes)


def update_markdown_table_report(changes: list[dict[str, str]]) -> None:
    rel = "parsimonious_features/Parsimonious_Model_Report.md"
    path = ROOT / rel
    if not path.exists():
        return
    text = read_text(path)
    original = text
    text = text.replace("F15_minimal_bedside_set", "F15_clinically_parsimonious_feature_set")
    text = text.replace(
        "# Parsimonious Model Report",
        "# Parsimonious Model Report\n\nNaming note: `F15_minimal_bedside_set` and `P15_minimal_bedside_model` are retained as legacy/internal aliases. The manuscript-facing names are `F15_clinically_parsimonious_feature_set` and `P15_clinically_parsimonious_transport_model`.",
    )
    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
        changes.append(
            {
                "file_path": rel,
                "change_type": "targeted_text_update",
                "old_expression": "F15_minimal_bedside_set display wording",
                "new_expression": "F15_clinically_parsimonious_feature_set",
                "legacy_alias_preserved": "yes",
                "note": "Updated report wording only.",
            }
        )


def scan_main_path() -> tuple[list[dict[str, str]], dict[str, bool]]:
    scanned_files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and "archive" not in p.parts
        and p.name not in {"Final_Naming_Harmonisation_Report.md", "Final_Naming_Harmonisation_Changes.csv"}
        and p.suffix.lower() in {".md", ".csv", ".txt"}
    ]
    findings: list[dict[str, str]] = []
    risk_patterns = {
        "bedside-only": re.compile(r"bedside-only", re.I),
        "pure bedside": re.compile(r"pure bedside", re.I),
        "minimal bedside model": re.compile(r"minimal bedside model", re.I),
        "MT3 final model": re.compile(r"MT3\s+final\s+model", re.I),
        "phenotype performance driver": re.compile(r"phenotype\s+performance\s+driver", re.I),
        "full VIS proxy": re.compile(r"full\s+VIS\s+proxy", re.I),
        "79-91h strict lead-time": re.compile(r"79\s*[-–]\s*91h\s+strict\s+lead[- ]time", re.I),
    }
    for path in scanned_files:
        text = read_text(path)
        for i, line in enumerate(text.splitlines(), start=1):
            for name, pat in risk_patterns.items():
                if pat.search(line):
                    # Allow explicit negation/guardrail wording that prevents the exact misconception.
                    lower = line.lower()
                    allowed_guardrail = any(
                        token in lower
                        for token in [
                            "not bedside-only",
                            "not a bedside-only",
                            "do not describe",
                            "不是 bedside-only",
                            "不能",
                            "not as",
                            "does not",
                        ]
                    )
                    if not allowed_guardrail:
                        findings.append(
                            {
                                "file_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                                "line_number": str(i),
                                "risk": name,
                                "line": line.strip(),
                            }
                        )
            if "eventual-death lead-time" in line and "exploratory eventual-death lead-time" not in line:
                findings.append(
                    {
                        "file_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "line_number": str(i),
                        "risk": "eventual-death lead-time not marked exploratory",
                        "line": line.strip(),
                    }
                )

    status = {
        "readme_updated": "P15_clinically_parsimonious_transport_model" in read_text(ROOT / "README.md"),
        "p15_display_unified": not findings and "P15_clinically_parsimonious_transport_model" in read_text(ROOT / "README.md"),
        "legacy_alias_preserved": "P15_minimal_bedside_model" in read_text(ROOT / "README.md"),
        "no_bedside_only_misleading": not any(f["risk"] in {"bedside-only", "pure bedside", "minimal bedside model"} for f in findings),
        "mt3_reference_unified": "MT3_Post_METRE_transport_reference_model" in read_text(ROOT / "README.md"),
        "phenotype_audit_only": "stratification / explanation / calibration audit" in read_text(ROOT / "README.md"),
        "vis_proxy_separated": "Full VIS" in read_text(ROOT / "results_final/text/Discussion_Outline_zh_Final_Parsimonious.md")
        and "shared support-intensity proxy" in read_text(ROOT / "results_final/text/Discussion_Outline_zh_Final_Parsimonious.md"),
        "lead_time_terms_clean": not any("lead" in f["risk"] for f in findings),
    }
    return findings, status


def write_change_csv(changes: list[dict[str, str]]) -> None:
    path = ROOT / "cleanup/Final_Naming_Harmonisation_Changes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "file_path",
        "change_type",
        "old_expression",
        "new_expression",
        "legacy_alias_preserved",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(changes)


def write_report(changes: list[dict[str, str]], findings: list[dict[str, str]], status: dict[str, bool]) -> None:
    changed_files = sorted({c["file_path"] for c in changes})
    lines = [
        "# Final Naming Harmonisation Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "This step only harmonised manuscript-facing names and wording. It did not retrain models, modify feature sets, alter cohorts, change labels, or edit any performance metrics.",
        "",
        "## Naming decisions",
        "",
        "- `P15_minimal_bedside_model` is retained as a legacy/internal alias.",
        "- Manuscript-facing P15 name: `P15_clinically_parsimonious_transport_model` / P15 临床精简迁移模型.",
        "- `F15_minimal_bedside_set` is retained as a legacy feature-set ID.",
        "- Manuscript-facing F15 name: `F15_clinically_parsimonious_feature_set` / F15 临床精简特征集.",
        "- MT3 is displayed as `MT3_Post_METRE_transport_reference_model`, not the final clinical model.",
        "- Phenotype is retained only as an early static phenotype for stratification, explanation, and calibration audit.",
        "- Full VIS and the shared support-intensity proxy are separated explicitly.",
        "",
        "## Modified files",
        "",
    ]
    for rel in changed_files:
        lines.append(f"- `{rel}`")
    lines.extend(
        [
            "",
            "## Consistency checks",
            "",
            "| Check | Pass |",
            "|---|---|",
        ]
    )
    check_labels = {
        "readme_updated": "README updated",
        "p15_display_unified": "P15 unified as clinically parsimonious transport model",
        "legacy_alias_preserved": "Legacy alias preserved",
        "no_bedside_only_misleading": "No misleading bedside-only expression remains",
        "mt3_reference_unified": "MT3 unified as Post-METRE reference",
        "phenotype_audit_only": "Phenotype downgraded to stratification/explanation/calibration audit",
        "vis_proxy_separated": "Full VIS and shared support-intensity proxy separated",
        "lead_time_terms_clean": "Lead-time terminology clean",
    }
    for key, label in check_labels.items():
        lines.append(f"| {label} | {status.get(key, False)} |")

    lines.extend(["", "## Residual risk findings in main path", ""])
    if findings:
        lines.append("| file | line | risk | text |")
        lines.append("|---|---:|---|---|")
        for f in findings:
            safe_line = f["line"].replace("|", "\\|")
            lines.append(f"| `{f['file_path']}` | {f['line_number']} | {f['risk']} | {safe_line} |")
    else:
        lines.append("No unallowed risk expressions were found in the non-archive main path.")

    lines.extend(
        [
            "",
            "## Verification summary",
            "",
            "- Legacy IDs remain available for auditability.",
            "- Display names are now separated from legacy/internal aliases.",
            "- No CSV metric columns were recalculated or edited by value.",
        ]
    )
    write_text("cleanup/Final_Naming_Harmonisation_Report.md", "\n".join(lines))


def main() -> None:
    changes: list[dict[str, str]] = []
    update_text_files(changes)
    update_csv_files(changes)
    update_markdown_table_report(changes)
    write_change_csv(changes)
    findings, status = scan_main_path()
    write_report(changes, findings, status)

    if findings:
        raise SystemExit(f"Naming harmonisation completed with residual findings: {len(findings)}")
    print("Final naming harmonisation completed with no unallowed main-path risk findings.")


if __name__ == "__main__":
    main()
