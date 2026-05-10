# Discussion Outline zh - Final Parsimonious

## 1. 高维特征并非必要

本轮结果显示，外部迁移表现并不依赖高维特征堆叠。P15 使用 15 个临床可解释特征即可达到与 MT3 相当甚至略高的 eICU AUPRC，并保持接近 1 的 calibration slope。

## 2. 临床可实施性与外部迁移性可以同时获得

P15 支持“少而稳”的 bedside transport model 叙事：保留时间锚点、生命体征、常规实验室、肾功能、凝血/炎症和共享支持强度 proxy，减少跨库语义不稳定的复杂变量。

## 3. Measurement-process 与复杂派生特征的限制

高维 measurement-process 特征、复杂窗口统计和仅在 MIMIC 中稳定的派生变量不应作为外部 transport model 的默认输入。它们可以提高内部表现，但可能牺牲跨库稳定性和临床解释性。

## 4. P15 的临床优势

P15 的优势在于可解释、可部署、跨库稳定。15 个特征更容易映射到 ICU 常规采集流程，也更适合与临床医生讨论风险来源。

## 5. 仍需谨慎

P15 仍需本地再校准和前瞻性验证。当前 DCA/lead-time 结果应被定位为风险分层证据，而不是自动干预触发器。
