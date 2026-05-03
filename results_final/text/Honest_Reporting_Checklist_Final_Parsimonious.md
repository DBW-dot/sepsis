# Honest Reporting Checklist - Final Parsimonious

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
