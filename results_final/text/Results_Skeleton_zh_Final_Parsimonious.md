# Results Skeleton - Final Parsimonious Version

## 队列、锚点与主模型

最终主结果应报告 `P15_clinically_parsimonious_transport_model`，并明确其是正式主模型。P15 在 eICU 外部验证中的冻结指标为 AUROC 0.8103、AUPRC 0.1892、校准斜率 1.0031。

## 临床简化候选

`P12_true_trained_clinical_landing_model` 已完成真实训练和外部验证，可作为临床简化候选展示。`P10_true_trained_ultra_minimal_sensitivity_model` 已完成真实训练和外部验证，可作为极简敏感性候选展示。二者均不自动替代 P15。

## 实验室时效性

实验室变量应写成 latest-available / capped carry-forward，而不是每小时真实测量。12h freshness 属于边界可接受，24h freshness 基本稳定。result availability time 不完整，应作为局限性说明。

## 支持强度 proxy

shared support-intensity proxy 是跨数据库支持负荷代理变量，不是 full VIS。full VIS 只能作为 internal-rich 或敏感性讨论背景。
