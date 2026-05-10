# Results Skeleton (ZH)

## 1. Cohort construction and anchor definition

用于主分析建模的 MIMIC 队列共纳入 34,125 个 ICU stays、27,899 名患者；外部验证 eICU 队列共纳入 9,032 个 stays、8,754 名患者。MIMIC 队列中 `is_sepsis_on_admission = 1` 的比例为 84.2%，eICU 队列中相应比例为 41.9%。

## 2. Early phenotype discovery and external mapping

最终保留 3 个早期静态表型，其中 2 个在 eICU 中表现出相对稳定的外部迁移，而 Phenotype_3 的跨库可迁移性较弱。

## 3. Main model performance in internal testing

在 MIMIC 内部测试集中，主模型 M1 对 24h ICU death 的 one-vs-rest AUROC 为 0.871，AUPRC 为 0.273，multiclass Brier score 为 0.467。动态 SOFA-only 对照模型 C1 的对应指标分别为 0.762、0.106 和 0.559。去除 phenotype_label 的 C3 指标分别为 0.870、0.274 和 0.468。

## 4. External validation in eICU

在 eICU 外部验证中，主模型 M1 的 AUROC 为 0.709，AUPRC 为 0.038，multiclass Brier score 为 0.879。值得如实报告的是，eICU 中动态 SOFA-only 对照模型 C1 的 AUROC、AUPRC 与 Brier score 分别为 0.725、0.067 和 0.826。

## 5. Added value of phenotype and measurement-process information

加入 phenotype_label 后，相对无表型模型的整体增益有限，更多体现为概率刻画或校准层面的细微变化，而非判别能力的大幅提升。

## 6. Explainability, DCA, and first-alarm findings

SHAP 解释显示，重要风险驱动因素集中在呼吸支持状态、BUN、MAP 相关负荷、尿量相关负荷、shock index 及测量新鲜度变量。DCA 显示主模型相对 C1 有优势，但绝对 net benefit 在多数阈值下仍有限。首次预警分析中，主模型更稳妥的表述是“以较低假警报代价维持了相近的预警提前量”。

## 7. External failure-mode analysis

eICU 外部 AUPRC 相较内部测试下降 0.236，且不能由事件率差异单独解释。external calibration slope 仅 0.073，提示存在明显 domain mismatch。主要瓶颈更可能来自 observation-process shift 与 cross-database feature distribution shift。
