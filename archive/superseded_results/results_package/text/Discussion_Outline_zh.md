# Discussion Outline (ZH)

1. 主要发现：主模型内部优于动态 SOFA-only，但外部迁移明显受限。
2. 双锚点价值：减少时间对齐错误，并帮助区分流程时间与疾病时间。
3. phenotype 的作用与边界：增益有限，更偏向异质性组织和解释接口。
4. eICU 外部 AUPRC 偏低原因：observation-process shift、feature shift、Phenotype_3 弱迁移。
5. 临床意义：可作为需本地再校准的风险框架，而非直接跨库部署工具。
6. 方法学意义：显式 competing risk 和质量特征纳入是价值点，但也引入测量行为偏倚风险。
7. 局限性：外部 AUPRC 低、phenotype 增益有限、DCA 绝对净获益有限、lead-time 不一定优于 C1、dynamic OASIS 未纳入。
8. 后续工作：再校准、transportability 研究、病理生理与测量行为信号解耦。
