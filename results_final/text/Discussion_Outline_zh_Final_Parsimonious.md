# Discussion Outline - Final Parsimonious Version

## 主要发现

- P15 是最终正式主模型，在外部验证中保持可接受的判别和校准表现。
- P12 通过真实训练验证，可作为临床简化候选；P10 可作为极简敏感性候选。
- 实验室 freshness 分析显示 12h 规则边界可接受，24h 规则基本稳定。

## 必须避免夸大的地方

- 不应把 P15 写成 bedside-only 或 manual score。
- 不应把 P12/P10 写成替代 P15 的最终主模型。
- 不应把 shared support-intensity proxy 写成 full VIS。
- 不应把 DCA 或 lead-time 写成自动干预依据。

## 局限性

- result availability time 不完整，部分实验室可用性只能用 chart/sample time 保守近似。
- 12h freshness 下性能下降提示真实部署需要固定抽血频率或本地校准支持。
- Proxy 变量需要本地 EHR 映射和前瞻性验证。
