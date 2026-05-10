# Lab freshness 敏感性导师摘要

1. 当前 latest_value 是最近可用值/前向填充表示，不是每小时真实抽血。
2. P15 12h freshness eICU AUROC/AUPRC/slope = 0.7847/0.1674/0.9779。
3. P15 24h freshness eICU AUROC/AUPRC/slope = 0.8085/0.1860/0.9991。
4. P12 12h freshness eICU AUROC/AUPRC/slope = 0.7767/0.1545/0.9578。
5. P10 12h freshness eICU AUROC/AUPRC/slope = 0.7743/0.1498/0.9444。
6. proxy 中存在 lab freshness 依赖，尤其是 lactate/perfusion component 和 renal component。
7. 当前没有新增 look-ahead；限制是缺少 result availability time，只能用 chart/sample time 近似。
8. 建议将 lab12h sensitivity 放入补充材料，并在 Methods 中明确实验室不是小时级真实测量。
9. P15 仍作为正式主模型。
