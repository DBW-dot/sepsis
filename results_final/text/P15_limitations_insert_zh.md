# Limitations 补充段落

本研究尚未完成前瞻性部署验证，因此 P15 的实际临床运行性能仍需在目标医院 EHR 环境中进一步评估。P15 虽然是 clinically parsimonious transport model，但其落地仍依赖本地结构化 EHR 的完整程度：t_sepsis 需要由本地 Sepsis-3 电子表型规则推导，支持强度代理变量可能来自医嘱、输液泵、呼吸机接口、护理 flowsheet、尿量和 CRRT/透析记录。上述字段在不同医院系统中的命名、时间戳、更新频率和完整性可能不一致，并可能影响模型校准。实验室 latest_value 变量为 latest-available / capped carry-forward 值，不代表每小时真实测量；由于 result availability time 在当前模型 ready 层不完整，本研究使用 chart/sample time 作为保守近似，这不能完全替代真实报告可用时间。正式部署前需要完成变量映射审计、缺失率评估、单位一致性检查、实验室 freshness 评估和本地再校准，并应避免将 shared support-intensity proxy 解释为 full VIS 或直接治疗建议。
