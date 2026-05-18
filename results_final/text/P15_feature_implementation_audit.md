# P15 特征集临床来源、可获得性与部署难度审计

## 证据边界

本文件仅使用当前项目中的代码、CSV、Markdown 和审计文件。未在当前项目文件中找到的 itemid、原始字段、具体单位换算和 result availability time 均标注为需要作者核对。未重新训练模型，未修改任何冻结点估计，未使用 eICU 调参。

主要证据文件：

- `results_final/clinical_implementation/run_p12_p10_true_training_validation.py`：P15/P12/P10 true-training 特征清单和 support proxy 构造代码。
- `manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv`：P15 特征临床有效性和可实施性审计。
- `archive/post_metre_reference/metre_transport/METRE_Transport_Feature_Set.csv`：跨库概念级映射、缺失率和 transportability grade；该文件位于 archive，但用于审计追踪。
- `archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md`：shared support-intensity proxy 定义；明确不是 full VIS。
- `results_final/clinical_implementation/Lab_Freshness_Missingness_Impact.csv` 与 `results_final/clinical_implementation/Lab_Availability_Lookahead_Audit.md`：实验室 freshness、missingness 和 look-ahead 审计。
- `manuscript_assets/tables/Table3_Clinical_Implementation_TrueTraining_with_95CI.csv`：P12/P10 true-training 结果及 95% CI。

## 任务 1：P15 最终 15 个特征

| 序号 | 论文推荐变量名 | 内部变量名 | 中文推荐名称 | 类别 | aliases | 证据 |
|---:|---|---|---|---|---|---|
| 1 | `hours_since_icu_admission` | `hours_since_icu_admission` | 距 ICU 入室时间 | 时间锚点 | hours_since_icu_admission | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 2 | `hours_from_anchor` | `hours_from_anchor` | 距脓毒症发作锚点时间 | 疾病阶段 | hours_from_anchor | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 3 | `is_sepsis_on_admission` | `is_sepsis_on_admission` | 是否入室时/接近入室时发生脓毒症 | 疾病阶段 | is_sepsis_on_admission | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 4 | `heart_rate_latest_value` | `hr_latest_value` | 最新心率 | 床旁生命体征 | heart_rate_latest_value; hr_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 5 | `respiratory_rate_latest_value` | `rr_latest_value` | 最新呼吸频率 | 床旁生命体征 | respiratory_rate_latest_value; rr_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 6 | `spo2_latest_value` | `spo2_latest_value` | 最新外周血氧饱和度 | 床旁生命体征 | spo2_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 7 | `creatinine_latest_value` | `creatinine_latest_value` | 最新肌酐 | 常规实验室 | creatinine_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 8 | `bun_latest_value` | `bun_latest_value` | 最新尿素氮 | 常规实验室 | bun_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 9 | `platelet_latest_value` | `platelet_latest_value` | 最新血小板计数 | 常规实验室 | platelet_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 10 | `wbc_latest_value` | `wbc_latest_value` | 最新白细胞计数 | 常规实验室 | wbc_latest_value | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 11 | `shared_support_intensity_proxy` | `shared_support_intensity_proxy` | 共享支持强度代理总指标 | 支持强度代理变量 | shared_support_intensity_proxy | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 12 | `support_hemodynamic_component` | `support_hemodynamic_component` | 血流动力学支持分量 | 支持强度代理变量 | support_hemodynamic_component | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 13 | `support_lactate_component` | `support_lactate_component` | 乳酸/灌注支持分量 | 支持强度代理变量 | support_lactate_component | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 14 | `support_renal_component` | `support_renal_component` | 肾脏支持分量 | 支持强度代理变量 | support_renal_component | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |
| 15 | `support_respiratory_component` | `support_respiratory_component` | 呼吸支持分量 | 支持强度代理变量 | support_respiratory_component | results_final/clinical_implementation/run_p12_p10_true_training_validation.py; manuscript_assets/tables/Supplementary_Table_S1_P15_Feature_Clinical_Validity.csv |

结论：P15 最终变量数为 15。用户特别列出的 time since ICU admission、time since sepsis onset、is sepsis on admission、heart rate、respiratory rate、SpO2、creatinine、BUN、platelet、WBC、shared support-intensity proxy 及四个支持强度分量均属于 P15。内部训练脚本使用 `hr_latest_value` 和 `rr_latest_value`；论文推荐使用更可读的 `heart_rate_latest_value` 和 `respiratory_rate_latest_value`，并在补充表中保留 alias。

## 任务 2：临床来源、可获得性与部署难度

已生成表：`results_final/tables/P15_feature_source_availability_deployment_table.csv`。

概括：7 个生命体征/常规实验室变量可直接从监护或实验室系统抽取；`hours_since_icu_admission` 可从 ICU 入室时间戳派生；`hours_from_anchor` 和 `is_sepsis_on_admission` 需要 Sepsis-3 电子表型推导；5 个支持强度 proxy 变量需要本地字段映射和派生。

## 任务 3：MIMIC-IV 与 eICU 字段映射

已生成表：`results_final/tables/P15_feature_mapping_audit.csv`。

### 已确认字段映射

当前项目可确认到概念级表/字段映射。例如 HR 来自 MIMIC `mimiciv_icu.chartevents` 和 eICU `vitalPeriodic / nurseCharting`，实验室变量来自 MIMIC `mimiciv_hosp.labevents` 和 eICU `lab`，时间锚点来自 prediction grid。

### 未确认字段映射

当前最终文件未找到完整原始 itemid 级映射，也未找到完整数据库字段 fallback 细节。支持强度 proxy 的底层变量已确认为动态特征名，但原始设备/医嘱/呼吸机/CRRT 字段级映射仍需作者核对。

### 需要作者核对字段映射

- MIMIC-IV chartevents/labevents 的 itemid 级定义。
- eICU vitalPeriodic、nurseCharting、respiratoryCharting、lab、intakeOutput、infusionDrug 或其他治疗支持字段的本地字段名。
- proxy 底层 MAP、FiO2、SpO2、ventilation transition、urine output、worsening renal trajectory 和 lactate burden 的构造代码与单位口径。

## 任务 4：缺失率审计

已生成表：`results_final/tables/P15_feature_missingness_audit.csv`。

当前可确认所有 15 个 P15 变量均有 model-ready 或 METRE registry 层面的缺失率证据。建议逐项缺失率放补充材料；主文只概述 P15 变量可获得性较高，并重点报告 lab freshness sensitivity。

## 任务 5：单位转换、时间对齐和 look-ahead

- `METRE_Transport_Feature_Set.csv` 将 P15 生命体征和实验室变量标记为 already canonicalized in Step2/Step3 feature layer。
- 当前最终主路径未找到完整 Canonical Unit Dictionary 或 itemid 级单位转换表；不能在论文中编造具体单位换算公式。
- 支持强度 proxy 使用 0-1 proxy scale 或 component score 表达，不是 full VIS，也不是药物剂量单位。
- Step2/Step3 层使用 capped forward-fill where applicable；动态 burden 使用 prefix-only windows。
- 实验室 latest_value 是 latest-available / capped carry-forward，不是每小时真实实验室测量。
- 未找到 linear interpolation、MICE 或将 missingness mask 纳入 P15 的证据；不能声称 P15 使用这些机制。
- `Lab_Availability_Lookahead_Audit.md` 说明 model-ready 层未找到 explicit result availability/store time；可用 freshness 字段基于 chart/sample-time derived quality indicators。
- 审计未引入 t_pred 之后的实验室值；但不能证明所有真实报告延迟风险已完全消除。

P15 current latest_value reference eICU AUROC/AUPRC/calibration slope: 0.8103 / 0.1892 / 1.0031。

P15 12h freshness eICU AUROC/AUPRC/calibration slope: 0.7847 / 0.1674 / 0.9779，状态为 borderline acceptable，不应写成 fully noninferior。

P15 24h freshness eICU AUROC/AUPRC/calibration slope: 0.8085 / 0.1860 / 0.9991，状态为 largely stable。

## 任务 6：支持强度代理变量定义

| proxy 变量 | 精确定义/项目内定义 | 临床解释 | 部署风险 | 是否可用于主文 | 是否建议仅放补充材料 | 证据文件路径 |
|---|---|---|---|---|---|---|
| `shared_support_intensity_proxy` | 四个可用分量的平均值 | 总体支持强度负荷 | 字段映射、治疗文档延迟、本地再校准 | 主文可用，但必须定义清楚 | 否，可放主文方法和补充表 | archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md; results_final/clinical_implementation/run_p12_p10_true_training_validation.py; results_final/clinical_implementation/Proxy_Clinical_Interpretability_Audit.md |
| `support_hemodynamic_component` | normalized map_deficit 与 map_below_65_burden_24h 的均值 | 循环支持/低血压负荷 | 血压来源、MAP 口径、与 VIS 混称风险 | 可用于主文特征表 | 可在补充材料给公式 | archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md; results_final/clinical_implementation/run_p12_p10_true_training_validation.py |
| `support_lactate_component` | normalized lactate_gt2_burden_24h 与 lactate_gt4_burden_24h 的均值 | 乳酸/灌注负荷 | 乳酸结果 freshness 和报告时间 | 可用于主文特征表 | 建议补充解释 freshness | archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md; results_final/clinical_implementation/Lab_Freshness_Missingness_Impact.csv |
| `support_renal_component` | normalized oliguria_burden_24h 与 worsening_renal_trajectory_flag 的均值 | 肾脏支持/恶化负荷 | 尿量、CRRT/透析、肌酐 freshness 映射 | 可用于主文特征表 | 建议补充字段映射 | archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md; results_final/clinical_implementation/Lab_Freshness_Missingness_Impact.csv |
| `support_respiratory_component` | normalized high_fio2_burden_24h、low_spo2_burden_24h、ventilation_transition_count_24h 的均值 | 呼吸支持/氧合恶化负荷 | FiO2、通气状态和呼吸治疗记录映射 | 可用于主文特征表 | 建议补充字段映射 | archive/post_metre_reference/metre_transport/Shared_Support_Intensity_Proxy_Definition.md; results_final/clinical_implementation/run_p12_p10_true_training_validation.py |

结论：shared support-intensity proxy 是跨数据库支持强度负荷代理变量，明确不是 full VIS。MIMIC full VIS 只可作为 internal-rich/sensitivity 背景，不是 eICU external transport 输入。

## 任务 7：P12/P10 删除变量和性能

### P12 相对 P15 删除

- `support_hemodynamic_component` (支持强度代理变量): 牺牲 血流动力学支持分量 相关信息。
- `support_renal_component` (支持强度代理变量): 牺牲 肾脏支持分量 相关信息。
- `support_respiratory_component` (支持强度代理变量): 牺牲 呼吸支持分量 相关信息。

### P10 相对 P15 删除

- `wbc_latest_value` (常规实验室): 牺牲 最新白细胞计数 相关信息。
- `support_hemodynamic_component` (支持强度代理变量): 牺牲 血流动力学支持分量 相关信息。
- `support_lactate_component` (支持强度代理变量): 牺牲 乳酸/灌注支持分量 相关信息。
- `support_renal_component` (支持强度代理变量): 牺牲 肾脏支持分量 相关信息。
- `support_respiratory_component` (支持强度代理变量): 牺牲 呼吸支持分量 相关信息。

### 可直接插入 Results 的中文段落

在冻结的 P15 主模型基础上，P12 和 P10 作为低负担实现候选进行了真实训练验证，而不是仅保留模拟敏感性估计。P12 保留 12 个变量，相对 P15 删除 support_hemodynamic_component, support_renal_component, support_respiratory_component，eICU 外部 AUROC/AUPRC/校准斜率为 0.8038/0.1767/1.0100 （95% CI: AUROC 0.7897-0.8166; AUPRC 0.1576-0.1976; 校准斜率 0.9476-1.0655）。P10 保留 10 个变量，相对 P15 删除 wbc_latest_value, support_hemodynamic_component, support_lactate_component, support_renal_component, support_respiratory_component，eICU 外部 AUROC/AUPRC/校准斜率为 0.7978/0.1711/1.0133 （95% CI: AUROC 0.7834-0.8108; AUPRC 0.1526-0.1921; 校准斜率 0.9542-1.0720）。这些结果支持 P12/P10 作为低负担部署候选或敏感性模型进行补充展示，但不改变 P15 作为正式主模型的冻结定位；P15 保留完整支持强度代理分量，仍提供最完整的临床语义覆盖。

## 未确认信息清单

- 未在当前项目文件中找到完整 itemid 级字段映射表。
- 未在当前项目文件中找到完整 Canonical Unit Dictionary 或所有变量具体单位换算公式。
- 未在 model-ready 层找到 result availability/store time；当前只确认使用 chart/sample-time freshness 近似。
- 支持强度 proxy 底层原始设备字段、医嘱字段、CRRT/透析字段和呼吸机接口字段需作者按原始特征工程代码进一步核对。
