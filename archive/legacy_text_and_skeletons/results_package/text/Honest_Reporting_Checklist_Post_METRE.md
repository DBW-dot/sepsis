# Honest Reporting Checklist Post-METRE

1. M1 内部表现最好，但不能作为外部 transport model；eICU AUPRC 仅 0.0377，calibration slope 仅 0.0728。
2. MT3 明显改善外部 AUPRC 至 0.1863，但内部 AUPRC 低于 M1，因此是 transport-focused trade-off，不是全方位更强模型。
3. eICU local recalibration 应作为部署前要求；intercept-only recalibration 主要改善 Brier/ECE，不提高 AUROC/AUPRC。
4. 旧 79-91 小时 lead-time 不能称为 strict 24h lead-time，只能作为 exploratory eventual-death lead-time 或撤出主图。
5. DCA 虽有正 net benefit 阈值区间，且再校准改善 DCA，但模型仍不应表述为自动干预触发器。
6. Phenotype_label 和 soft membership 均未改善 MT3 外部 AUPRC；phenotype 应降级为分层/解释/校准审计工具。
7. Phenotype_3 仍是弱迁移/低确定性表型；较高 subgroup AUPRC 可能受死亡率较高影响，不能等同于迁移更好。
8. Full VIS 只能作为 MIMIC internal rich/sensitivity 信息；transport model 使用 shared support-intensity proxy，不能把 full VIS 与 eICU proxy 混称。
9. Full quality 和 measurement intensity features 在 eICU 外部明显破坏迁移，不能纳入最终 transport feature set。
10. Dynamic OASIS 仍不可稳定实现，原因是 final model-ready tables 缺少必要 GCS、age scoring interface 和 pre-ICU LOS 等输入。
