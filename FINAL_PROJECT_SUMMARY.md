# FINAL PROJECT SUMMARY

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
