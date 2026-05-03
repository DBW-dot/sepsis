# Parsimonious Model Report

Naming note: `F15_minimal_bedside_set` and `P15_minimal_bedside_model` are retained as legacy/internal aliases. The manuscript-facing names are `F15_clinically_parsimonious_feature_set` and `P15_clinically_parsimonious_transport_model`.

Naming note: `F15_clinically_parsimonious_feature_set` and `P15_minimal_bedside_model` are retained as legacy/internal aliases. The manuscript-facing names are `F15_clinically_parsimonious_feature_set` and `P15_clinically_parsimonious_transport_model`.

Naming note: `F15_clinically_parsimonious_feature_set` and `P15_minimal_bedside_model` are retained as legacy/internal aliases. The manuscript-facing names are `F15_clinically_parsimonious_feature_set` and `P15_clinically_parsimonious_transport_model`.

Naming note: `F15_clinically_parsimonious_feature_set` and `P15_minimal_bedside_model` are retained as legacy/internal aliases. The manuscript-facing names are `F15_clinically_parsimonious_feature_set` and `P15_clinically_parsimonious_transport_model`.

Training source: MIMIC train_inner only. Validation tuning: MIMIC validation only. External validation: eICU only.
All models output three competing-risk classes and use the same labels and split as the existing MT3 repair workflow.

| feature_set | n | eICU AUROC | eICU AUPRC | eICU slope | status vs MT3 |
|---|---:|---:|---:|---:|---|
| F15_clinically_parsimonious_feature_set | 15 | 0.8103 | 0.1892 | 1.0031 | acceptable |
| MT3_full_transport_set | 21 | 0.8090 | 0.1863 | 0.9652 | acceptable |
| F25_clinical_core_set | 25 | 0.8131 | 0.1509 | 0.7370 | borderline_acceptable |
| F40_balanced_transport_set | 40 | 0.8186 | 0.1811 | 0.5592 | not_recommended |
