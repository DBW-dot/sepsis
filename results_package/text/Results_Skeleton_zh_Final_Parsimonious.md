# Results Skeleton zh - Final Parsimonious

## 主要模型和临床精简特征集

在保持既有队列、t_sepsis/t_ICU 双锚点、Sepsis-3 疑似感染定义和 24h competing-risk label 不变的前提下，我们完成了临床可实施精简特征集实验。F15_minimal_bedside_set、F25_clinical_core_set 和 F40_balanced_transport_set 均成功训练，并与 MT3_full_transport_set 作为 Post-METRE transport reference 进行同一框架下比较。

## 临床精简特征集与 P15 minimal bedside model

P15_minimal_bedside_model 仅使用 15 个临床可解释特征。在 eICU 外部验证中，P15 的 AUROC/AUPRC/calibration slope 为 0.8103/0.1892/1.0031。这一表现不低于 MT3_physiology_support_proxy（eICU AUROC/AUPRC/calibration slope 为 0.8090/0.1863/0.9652），说明模型的外部迁移能力主要依赖少数稳定、可迁移的病理生理变量和共享支持强度 proxy，而不是高维 measurement-process 或复杂派生特征。

因此，P15 被冻结为最终推荐的临床可实施 transport model；MT3 保留为 Post-METRE transport reference 和性能上限参考。
