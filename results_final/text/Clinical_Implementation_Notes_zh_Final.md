# Clinical Implementation Notes - Final

P15 是正式主模型，适合 EHR 自动抽取和动态更新，不是手工床旁评分。实验室指标采用 latest-available / capped carry-forward 逻辑，不代表每小时均有真实新化验结果。

P12 是真实训练验证后的临床简化候选。如果医院希望降低特征负担，可在补充材料和部署讨论中展示 P12，但不应在没有重新冻结决策的情况下替代 P15。

P10 是真实训练验证后的极简敏感性候选，适合用于资源受限场景讨论，不建议作为主模型。

shared support-intensity proxy 应解释为跨数据库支持强度负荷代理变量，而不是 full VIS。
