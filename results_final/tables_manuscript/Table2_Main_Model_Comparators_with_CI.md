# Table 2. Main model comparators with 95% CI

| Model | feature_count | MIMIC_AUROC | MIMIC_AUROC_95CI | MIMIC_AUPRC | MIMIC_AUPRC_95CI | eICU_AUROC | eICU_AUROC_95CI | eICU_AUPRC | eICU_AUPRC_95CI | eICU_calibration_slope | eICU_calibration_slope_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 70-feature high-dimensional reference model | 70 | 0.8706 | 0.8606-0.8807 | 0.2733 | 0.2480-0.3000 | 0.709 | 0.6921-0.7239 | 0.0377 | 0.0339-0.0414 | 0.0728 | 0.0566-0.0892 |
| P15 double-anchor model | 15 | 0.7977 | 0.7828-0.8129 | 0.1982 | 0.1772-0.2197 | 0.8103 | 0.7963-0.8232 | 0.1892 | 0.1681-0.2116 | 1.0031 | 0.9413-1.0584 |
| P12 simplified implementation candidate | 12 | 0.793 | 0.7778-0.8073 | 0.1785 | 0.1590-0.2002 | 0.8038 | 0.7897-0.8166 | 0.1767 | 0.1576-0.1976 | 1.01 | 0.9476-1.0655 |
| P10 ultra-minimal sensitivity candidate | 10 | 0.7864 | 0.7714-0.8014 | 0.1732 | 0.1542-0.1948 | 0.7978 | 0.7834-0.8108 | 0.1711 | 0.1526-0.1921 | 1.0133 | 0.9542-1.0720 |
| Dynamic SOFA | 15 | 0.7623 | 0.7464-0.7778 | 0.1064 | 0.0917-0.1221 | 0.7253 | 0.7082-0.7420 | 0.0669 | 0.0570-0.0768 | 0.4919 | 0.4556-0.5263 |
