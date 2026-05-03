# FINAL PI SUMMARY - Parsimonious Model

## 1. 为什么“特征太多”的问题已经解决？

我们新增并完成了临床精简特征集实验，比较 F15、F25、F40 与 MT3 transport reference。最终 P15 仅保留 15 个临床可解释特征，且不使用 phenotype、measurement intensity、full VIS 或高维复杂派生变量作为默认 transport 输入。

## 2. P15 为什么可以替代 MT3？

P15 在 eICU 外部验证中的 AUROC/AUPRC/calibration slope 为 0.8103/0.1892/1.0031，MT3 为 0.8090/0.1863/0.9652。P15 的 AUPRC 相对 MT3 没有下降，反而略高，并且 calibration slope 更接近 1。

## 3. 15 个特征是否足够临床实施？

从特征结构看，P15 主要包含时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和 shared support-intensity proxy，均可对应 ICU 常规临床信息或清晰 proxy。它不是全床旁无实验室模型，也不是人工手算评分；更准确的名称是 P15 临床精简迁移模型。

## 4. P15 相比 MT3 损失了多少性能？

按 eICU external AUPRC，P15 没有性能损失，AUPRC 从 MT3 的 0.1863 到 P15 的 0.1892；AUROC 也从 MT3 的 0.8090 到 P15 的 0.8103，基本持平。

## 5. 对论文投稿有什么好处？

该结果直接回应“特征太多、临床难以实现”的质疑。论文可以把主模型叙事从高维 transport model 调整为临床精简、可解释、跨库稳定的 P15 clinically parsimonious transport model，同时保留 MT3 作为 Post-METRE 迁移参考模型。

## 6. 是否可以进入最终中文论文写作？

可以。建议进入最终中文论文重写阶段，但必须诚实保留：M1 是 internal rich/reference model；MT3 是 Post-METRE reference；P15 是 final clinically parsimonious transport model；P15 仍需本地再校准和前瞻性验证。
