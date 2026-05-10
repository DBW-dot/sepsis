# Results Skeleton zh Post-METRE

## 1. Post-METRE 模型角色更新

原 M1 仍是 MIMIC 内部 rich model，内部 AUROC/AUPRC 为 0.8706/0.2733，但 eICU 外部 AUROC/AUPRC/slope 仅为 0.7090/0.0377/0.0728。Post-METRE 后，最终 external transport model 固定为 MT3，即 physiology + temporal context + shared support-intensity proxy，不直接纳入 phenotype_label。

## 2. 外部验证改善

MT3 在 eICU full external 上 AUROC/AUPRC/slope 为 0.8090/0.1863/0.9652。相对于 M1，外部 AUPRC 从 0.0377 提升到 0.1863，AUROC 从 0.7090 提升到 0.8090。但 MT3 内部 AUPRC 0.2053 低于 M1 内部 AUPRC 0.2733，说明它是 transport-focused model，而不是内部性能最强模型。

## 3. 外部再校准

在 eICU patient-level hold-out 上，MT3 raw AUROC/AUPRC/slope 为 0.8106/0.1913/0.9862；intercept-only recalibration 后为 0.8106/0.1913/0.9874。再校准不改变判别能力，但 death Brier/ECE 从 0.0977/0.2385 改善到 0.0191/0.0030。因此外部部署应表述为 requires local recalibration。

## 4. Strict 24h lead-time 与 DCA

旧 Figure5 中 79-91 小时 lead-time 不再作为 strict 24h 主结果，应改名为 exploratory eventual-death lead-time。新的 strict 24h first-alarm 结果中，MT3 recalibrated 在阈值 0.10 的 median lead-time 为 5.5667 小时，最大 strict lead-time 不超过 24 小时。DCA 在阈值 0.005 和 0.10 的 net benefit 分别为 0.0169 和 0.0043，再校准后低阈值和中等阈值区间均优于未校准 MT3。

## 5. Phenotype、VIS/proxy 与 measurement-process 结论

Post-METRE component reassessment 显示 hard phenotype model MT4 的外部 AUPRC 为 0.1813，低于 MT3 的 0.1863；soft membership 外部 AUPRC 为 0.1587，也未优于 MT3。因此 phenotype 应降级为分层/解释/校准审计工具。Full VIS 保留为 internal rich/sensitivity 模块；跨库主分析使用 shared support-intensity proxy。Full quality + measurement intensity 外部 AUPRC 为 0.0295 且 calibration slope 为 0.0361，因此不进入最终 transport feature set。

## 6. 当前结果定位

Post-METRE 后项目比原始外部结果更稳，但仍需诚实报告：MT3 不追求 MIMIC 内部最高性能；外部部署需要 local recalibration；phenotype 不是性能增强器；measurement-process features 破坏外部迁移；模型更适合风险分层和审计式临床辅助，而不是自动干预触发器。
