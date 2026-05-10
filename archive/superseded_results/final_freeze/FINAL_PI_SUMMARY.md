# FINAL PI SUMMARY

## 当前项目最终完成了什么

项目完成了从原始 M1 外部迁移失败到 Post-METRE transportability repair 的完整闭环：模型选择、外部再校准、strict 24h lead-time/DCA 重算、组件重估和结果包更新均已冻结。

## 最强结果

- 原 M1 eICU external AUROC/AUPRC/slope 为 0.7090/0.0377/0.0728。
- 最终 MT3 eICU external AUROC/AUPRC/slope 为 0.8090/0.1863/0.9652。
- eICU hold-out intercept-only recalibration 将 death Brier/ECE 从 0.0977/0.2385 改善到 0.0191/0.0030。

## 最弱结果

- MT3 不是内部性能最强模型；M1 仍是 internal rich model。
- Phenotype_label 和 soft membership 不能作为性能增强卖点。
- Measurement intensity 与 full quality features 在 eICU 外部迁移中表现很差。

## 最终推荐主叙事

推荐主叙事为：`M1_original_rich` 作为 internal rich/reference model，`MT3_physiology_support_proxy` 作为 external transport model，`C1_dynamic_SOFA` 作为 clinical comparator。

## 不能夸大的结论

- 不能说 phenotype 是主性能驱动。
- 不能把 full VIS 和 support-intensity proxy 混为一谈。
- 不能说模型可无需本地再校准直接部署。
- 不能把 exploratory eventual-death lead-time 写成 strict 24h lead-time。

## 是否可以进入论文写作

可以进入正式论文写作阶段。建议论文定位为 transportability-focused 方法学与透明失败修复，而不是单纯强性能模型。
