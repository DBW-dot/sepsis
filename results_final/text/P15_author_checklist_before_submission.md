# P15 作者投稿前核对清单

- [ ] 核对每个支持强度代理变量的精确定义，尤其是 MAP deficit、MAP below 65 burden、lactate burden、oliguria burden、renal trajectory worsening、FiO2/SpO2 burden 和 ventilation transition count。
- [ ] 核对 MIMIC-IV 与 eICU 的字段映射表；当前项目文件确认到概念级表/字段，未找到完整 itemid 级映射。
- [ ] 核对各 P15 特征在 MIMIC-IV 和 eICU 中的最终缺失率；当前输出已整理 model-ready/registry 缺失率，但若主文逐项报告，建议作者重新从最终 model-ready 表复核。
- [ ] 核对单位转换规则；当前文件说明已 canonicalized，但未完整展开具体单位换算。
- [ ] 核对实验室前向携带最大窗口和 freshness 规则；当前结果显示 12h borderline acceptable、24h largely stable。
- [ ] 核对 t_sepsis 电子表型规则，包括 suspected infection、SOFA 变化和入室即脓毒症定义。
- [ ] 核对 P12/P10 删除变量清单是否与 true-training 脚本一致。
- [ ] 确认所有支持强度代理变量只使用 t_pred 及之前的信息，未引入预测时点后的治疗状态或实验室结果。
- [ ] 判断目标医院是否需要本地再校准，特别是在支持治疗文档和实验室报告时间不同的系统中。
- [ ] 决定表 X 放主文还是补充材料；建议主文概述来源和部署边界，逐项字段映射/缺失率放补充表。
