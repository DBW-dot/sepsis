# Results Skeleton zh - Final Parsimonious

## 主要模型和临床精简特征集

在保持既有队列、t_sepsis/t_ICU 双锚点、Sepsis-3 疑似感染定义和 24h competing-risk label 不变的前提下，我们完成了临床精简特征集实验。F15_clinically_parsimonious_feature_set、F25_clinical_core_set 和 F40_balanced_transport_set 均成功训练，并与 MT3_Post_METRE_transport_reference_model 在同一框架下比较。

## 临床精简特征集与 P15 clinically parsimonious transport model

P15_clinically_parsimonious_transport_model 沿用 legacy/internal alias `P15_minimal_bedside_model`，但它不是全床旁人工评分。该模型仅使用 15 个临床可解释特征，包括时间锚点、常规生命体征、常规实验室指标和 shared support-intensity proxy。在 eICU 外部验证中，P15 的 AUROC/AUPRC/calibration slope 为 0.8103/0.1892/1.0031。

这一表现不低于 MT3_Post_METRE_transport_reference_model（legacy ID `MT3_physiology_support_proxy`；eICU AUROC/AUPRC/calibration slope 为 0.8090/0.1863/0.9652），说明模型的外部迁移能力主要依赖少数稳定、可迁移的病理生理变量和共享支持强度代理变量，而不是高维 measurement-process 或复杂派生特征。

因此，P15 被冻结为最终推荐的临床精简迁移模型；MT3 保留为 Post-METRE transport reference 和性能参考。
