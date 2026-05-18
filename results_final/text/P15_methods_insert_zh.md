# 2.X P15 特征集的临床来源与实施可行性

P15_clinically_parsimonious_transport_model 的设计目标不是最大化高维特征数量或内部 AUC，而是在双锚点动态预测框架下保留一组临床语义清楚、跨数据库可迁移且可由结构化 EHR 自动抽取或派生的变量。最终 P15 特征集包含 15 个变量，分为时间锚点、疾病阶段、床旁生命体征、常规实验室指标和支持强度代理变量五类。时间相关变量包括距 ICU 入室时间、距 t_sepsis 疾病锚点时间以及是否入室时或接近入室时已发生脓毒症。t_ICU 可由 ICU stay/admission 时间戳获得；t_sepsis 和 is_sepsis_on_admission 需要根据已锁定的 Sepsis-3 电子表型规则推导，因此在本地部署时必须复核感染证据、SOFA 变化和锚点定义。

生命体征变量包括心率、呼吸频率和 SpO2，项目文件将其归为 bedside monitor 或护理 flowsheet 来源，通常可近实时或小时级记录。常规实验室变量包括肌酐、BUN、血小板计数和 WBC，来源为实验室系统。需要强调的是，模型中的 laboratory latest_value 不是假设每小时真实测量，而是 latest-available / capped carry-forward 值；项目已完成 12h 和 24h freshness sensitivity，以评估实验室结果时效性对部署真实性的影响。由于当前模型 ready 层未保留完整 result availability/store time，相关审计使用 chart/sample time 作为保守近似；这一限制应在方法学和局限性中同时说明。

支持强度代理变量包括 shared_support_intensity_proxy 及其 hemodynamic、lactate/perfusion、renal 和 respiratory 分量。该 proxy 表示跨数据库可共享的支持强度负荷，而不是 full VIS，也不是单纯药物剂量评分。根据项目中的 proxy 定义，血流动力学分量由 MAP deficit 和 MAP below 65 burden 构成，乳酸/灌注分量由 lactate >2 和 >4 burden 构成，肾脏分量由 oliguria burden 和 renal trajectory worsening 构成，呼吸分量由 high FiO2 burden、low SpO2 burden 和 ventilation transition count 构成。上述变量需要本地医嘱、治疗支持、尿量、呼吸支持和实验室字段映射，因此部署难度高于生命体征和常规实验室变量。

P12 和 P10 是在冻结主流程下真实训练验证的低负担候选模型。P12 删除部分支持强度分量但保留 WBC、shared_support_intensity_proxy 和 support_lactate_component；P10 进一步删除 WBC 和所有 proxy 分量，仅保留 shared_support_intensity_proxy。二者可用于数据条件较弱或临床实施负担讨论，但不能直接替代 P15，除非后续由作者重新冻结模型层级并完成相应验证。
