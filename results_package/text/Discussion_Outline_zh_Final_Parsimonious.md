# Discussion Outline zh - Final Parsimonious

## 1. 高维特征并非必要

本轮结果显示，外部迁移表现并不依赖高维特征堆叠。P15 clinically parsimonious transport model 使用 15 个临床可解释特征即可达到与 MT3 Post-METRE transport reference 相当甚至略高的 eICU AUPRC，并保持接近 1 的 calibration slope。

## 2. 临床可实施性与外部迁移性可以同时获得

P15 支持“少而稳”的 clinical transport model 叙事：保留时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和 shared support-intensity proxy，减少跨库语义不稳定的复杂变量。它不是全床旁或手工评分模型，而是面向 ICU 常规数据流的临床精简迁移模型。

## 3. Measurement-process 与复杂派生特征的限制

高维 measurement-process 特征、复杂窗口统计和仅在 MIMIC 中稳定的派生变量不应作为外部 transport model 的默认输入。它们可以提高内部表现，但可能牺牲跨库稳定性和临床解释性。

## 4. full VIS 与 shared support-intensity proxy 的边界

Full VIS 仅保留在 internal-rich/sensitivity 分析中。外部迁移主模型使用 shared support-intensity proxy，二者不能混称。shared support-intensity proxy 是跨数据库支持强度表达，而不是 full VIS 的同义词。

## 5. phenotype 的定位

Early static phenotype 只用于分层、解释和校准审计，不应被表述为默认性能增强器或最终 transport model 的核心输入。

## 6. 仍需谨慎

P15 仍需本地再校准和前瞻性验证。当前 DCA/lead-time 结果应定位为风险分层证据，而不是自动干预触发器。严格主结果应使用 strict 24h first-alarm lead-time；探索性结果应标注为 exploratory eventual-death lead-time。
