# Supplementary Dual Anchor Definition

## t_ICU

`t_ICU` denotes the ICU admission anchor. It represents process time from ICU entry and is used to preserve ICU-flow timing.

## t_sepsis

`t_sepsis` denotes the sepsis-onset disease anchor from the locked Step 1 cohort construction. It is not a future outcome label and should not be derived from post-prediction information.

## Why both anchors are used

Using both ICU admission time and sepsis-onset time separates ICU process time from disease time. This reduces heterogeneity between patients who enter the ICU already septic and patients whose sepsis onset occurs after ICU admission.

## Admission sepsis handling

Patients with sepsis at or near ICU admission are represented through `is_sepsis_on_admission` and hours since ICU admission. They should not be forced into the same disease-time interpretation as patients developing sepsis later.

## Later sepsis handling

Patients who develop sepsis after ICU admission are aligned by `t_sepsis` while retaining ICU time. This prevents the disease-onset landmark from being replaced by ICU entry.

## Leakage prevention

Prediction features can only use information available at or before each prediction time. Information after a prediction time cannot be used for feature construction, anchoring at that time, or risk scoring.
