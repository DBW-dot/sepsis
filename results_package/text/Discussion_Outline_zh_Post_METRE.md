# Discussion Outline zh Post-METRE

## 1. Main findings

Post-METRE 的核心发现是：跨库 feature alignment 和 shared support-intensity proxy 能显著改善 eICU 外部迁移，而原 M1 更适合定位为 internal rich model。

## 2. Why METRE-style transport layer matters

外部失败主要不是事件率差异，而是 feature semantics、VIS/proxy 不等价和 observation-process shift。MT3 放弃高维 measurement-process 信号后，外部 AUROC/AUPRC 和校准明显更稳。

## 3. Recalibration as deployment requirement

MT3 raw slope 已接近 1，但 probability level 偏移明显；intercept-only local recalibration 显著改善 Brier/ECE。因此论文应明确：模型若部署到本地 ICU 系统，需要 local recalibration。

## 4. Phenotype role after reassessment

Phenotype 不应再写成 performance driver。它更适合组织异质性、解释风险模式、做 subgroup calibration audit。Phenotype_3 仍应作为弱迁移/低确定性表型说明。

## 5. VIS/proxy interpretation

Full VIS 是 MIMIC internal rich 信息，不可与 eICU reduced proxy 混称。Shared support-intensity proxy 是最终 transport model 的支持强度表达。

## 6. Clinical utility and alarm framing

Strict 24h lead-time 取代旧的 79-91h lead-time。DCA 在低阈值区间和再校准后有所改善，但模型仍应定位为 risk stratification，而非自动治疗触发器。

## 7. Limitations

需要报告：MT3 内部性能低于 M1；external recalibration 需要本地标签样本；OASIS 仍不可稳定实现；measurement intensity 的强预测性在外部不可迁移；eICU validation 仍受 core subset 和 proxy 限制。

## 8. Future work

后续可做前瞻性本地再校准、站点级 drift monitoring、可解释性与临床工作流验证，以及更严格的多中心 transport feature registry。
