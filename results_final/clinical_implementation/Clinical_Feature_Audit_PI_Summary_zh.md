# Clinical Feature Audit PI Summary

## 1. 当前 P15 特征集在临床上是否仍然太多？

不算太多。15 个变量对于人工手算偏多，但对于 EHR 自动抽取模型是可接受的。P15 不应被描述为 bedside-only manual score，而应被描述为 clinically parsimonious EHR-implementable transport model。

## 2. 哪些特征最容易落地？

最容易落地的是时间锚点、心率、呼吸频率、SpO2、BUN、肌酐、血小板和 WBC。这些变量来自时间戳、床旁监护或常规实验室。

## 3. 哪些特征最容易被质疑？

最容易被质疑的是 support proxy 相关变量，因为它们不是直接测量值，而是 EHR-derived/treatment-support-derived 的支持强度负荷指标。

## 4. proxy 特征应该如何解释？

应解释为“支持强度负荷”而不是“药物剂量评分”。一句话解释：这些 proxy 表示患者在循环、灌注、肾脏和呼吸方面接受或需要支持的总体负荷，用于跨数据库稳定表达病情支持强度。

## 5. P12 和 P10 是否值得保留？

值得保留，但只能作为 simulated sensitivity / implementation estimate。P12 是更实用的临床简化候选；P10 是极简敏感性方案。

## 6. 如果导师问“为什么不直接用 P12 或 P10”，如何回答？

因为 P15 是已冻结验证的正式主模型，P12/P10 是基于模拟敏感性分析的简化候选，还不是新训练或独立验证模型。可以把 P12/P10 放在补充材料和临床落地讨论中，但不能替代 P15 的主结果。

## 7. 如果临床医生问“这个模型能不能手算”，如何回答？

不建议手算。P15 是临床精简但 EHR 实施的模型，不是人工床旁评分。它适合由 EHR 自动抽取变量并计算风险。

## 8. 当前结果是否足以支持论文中写“临床可实施性”？

可以支持，但措辞应为 EHR-implementable / clinically parsimonious，而不是 bedside-only 或 manual score。还必须说明正式部署需要本地 EHR 映射和前瞻性验证。
