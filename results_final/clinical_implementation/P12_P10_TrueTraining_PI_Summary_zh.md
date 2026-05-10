# P12/P10 真实训练验证导师摘要

1. P12 是否真实训练成功：是。eICU AUROC/AUPRC/calibration slope = 0.8038/0.1767/1.0100。
2. P10 是否真实训练成功：是。eICU AUROC/AUPRC/calibration slope = 0.7978/0.1711/1.0133。
3. P12 相对 P15 AUPRC 下降：6.58%。
4. P10 相对 P15 AUPRC 下降：9.56%。
5. P12 非劣效判断：True，角色为 `validated_simplified_implementation_candidate`。
6. P10 非劣效判断：True，角色为 `validated_ultra_minimal_sensitivity_candidate_but_not_main_model`。
7. P15 仍建议作为正式主模型；P12/P10 是临床实施敏感性分析，不自动替代 P15。
8. DCA 和 strict 24h first-alarm 结果只能用于补充材料或临床部署讨论，不能写成自动干预依据。
