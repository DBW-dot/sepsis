# PI Decision Summary Post-METRE

## 最强的 3 点

1. METRE-style transport layer 将 eICU external AUPRC 从 M1 的 0.0377 提升到 MT3 的 0.1863，且 raw calibration slope 接近 1。
2. 结果叙事从“内部强但外部失败”转为“internal rich model + external transport model”的双模型框架，更容易防守。
3. Component reassessment 明确了 phenotype、VIS/proxy、measurement-process features 的边界，避免过度声称。

## 最弱的 3 点

1. MT3 内部性能低于 M1，不能说它整体更强。
2. 外部部署需要 local recalibration，说明概率尺度仍存在站点漂移。
3. Phenotype 增益有限，且 Phenotype_3 迁移弱，不能作为核心性能卖点。

## 投稿定位建议

主线更适合“方法学严谨 + transportability repair + 透明失败分析”，而不是“强性能模型”。当前已可进入正式论文写作阶段，但写作必须保留负面结果和部署限制。
