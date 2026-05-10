# Supplementary Feature Harmonisation and Unit Mapping

## Cross-database alignment principles

MIMIC and eICU variables were aligned by clinical concept, field availability, unit compatibility where available, and cross-database transportability. The final P15 feature set was selected to be clinically parsimonious and transportable.

## P15 feature modules

- Time anchors: `hours_since_icu_admission`, `hours_from_anchor`, `is_sepsis_on_admission`
- Vital signs: heart rate, respiratory rate, SpO2
- Routine laboratory values: creatinine, BUN, platelet count, WBC
- Support-intensity proxy: shared support-intensity proxy and hemodynamic, lactate, renal, and respiratory support components

## Unit coordination

Unit mapping was performed according to repository harmonisation tables when available. Not all source systems provide identical unit metadata, and remaining uncertainty should be reported as a limitation. This supplement does not invent specific unit conversion rules.

## Field naming differences

Database-specific field names were harmonised to shared clinical variable names. The manuscript should describe harmonisation at the concept level and cite the repository tables for implementation details.

## VIS and support-intensity proxy

Full VIS was not used as the external transport input. The shared support-intensity proxy is a cross-database support burden proxy and is not full VIS.

## Comparator limitations

Dynamic SOFA is retained as a clinical comparator. Dynamic OASIS was not used as a final comparator where stable reconstruction inputs were unavailable.

## Implementation boundary

P15 is EHR-implementable but not a bedside-only manual score.
