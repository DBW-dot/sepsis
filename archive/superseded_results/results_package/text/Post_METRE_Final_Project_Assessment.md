# Post-METRE Final Project Assessment

## 1. Post-METRE 后项目是否更稳

是。原 M1 的 eICU external AUROC/AUPRC/slope 为 0.7090/0.0377/0.0728；MT3 为 0.8090/0.1863/0.9652。外部判别与校准均明显更可防守。

## 2. 是否能把 external transport model 放入主结果

可以。建议主结果中并列展示：M1 as internal rich model，MT3 as external transport model，C1 as clinical comparator，MT3 recalibrated as deployment-oriented local recalibration result。

## 3. M1 是否仍保留为 internal rich model

是。M1 的 MIMIC internal AUROC/AUPRC 仍最高，为 0.8706/0.2733，但不应作为外部迁移主模型。

## 4. 仍需诚实报告的负面结果

- MT3 内部性能低于 M1。
- Local recalibration 是外部部署要求。
- Phenotype 和 soft membership 不是性能增强器。
- Full VIS 不能跨库直接迁移。
- Measurement intensity features 破坏外部迁移。
- DCA 改善主要支持风险分层，不支持自动干预触发。
- 旧 lead-time 必须撤回或改名为 exploratory eventual-death lead-time。

## 5. 是否可以进入正式论文写作

可以。当前结果包已经具备进入正式论文写作的结构化材料，但论文写作必须以 transportability 和透明失败修复为主线，而不是夸大模型性能。
