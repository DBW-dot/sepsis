# Post-METRE Lead-time and DCA Report

## Required answers

1. Should the original lead-time be withdrawn or renamed?
   - Yes. The prior 79-91 hour values are inconsistent with a strict 24h label interpretation and should be renamed as exploratory eventual-death lead-time if retained.

2. Can strict 24h lead-time be used as the main result?
   - Yes, with the limitation that it measures lead-time only among first alarms that are already within a 24h death-label window.
   - MT3 recalibrated strict summary:

```json
[
  {
    "threshold": 0.005,
    "strict_true_alarm_stay_n": 256,
    "strict_lead_time_median_hours": 8.5,
    "strict_lead_time_iqr_low_hours": 3.75,
    "strict_lead_time_iqr_high_hours": 15.783333333333335
  },
  {
    "threshold": 0.01,
    "strict_true_alarm_stay_n": 272,
    "strict_lead_time_median_hours": 8.383333333333333,
    "strict_lead_time_iqr_low_hours": 3.625,
    "strict_lead_time_iqr_high_hours": 15.691666666666666
  },
  {
    "threshold": 0.02,
    "strict_true_alarm_stay_n": 301,
    "strict_lead_time_median_hours": 7.433333333333334,
    "strict_lead_time_iqr_low_hours": 3.316666666666667,
    "strict_lead_time_iqr_high_hours": 13.916666666666666
  },
  {
    "threshold": 0.03,
    "strict_true_alarm_stay_n": 316,
    "strict_lead_time_median_hours": 7.116666666666667,
    "strict_lead_time_iqr_low_hours": 3.154166666666667,
    "strict_lead_time_iqr_high_hours": 13.920833333333333
  },
  {
    "threshold": 0.05,
    "strict_true_alarm_stay_n": 345,
    "strict_lead_time_median_hours": 5.85,
    "strict_lead_time_iqr_low_hours": 2.5833333333333335,
    "strict_lead_time_iqr_high_hours": 13.166666666666666
  },
  {
    "threshold": 0.075,
    "strict_true_alarm_stay_n": 367,
    "strict_lead_time_median_hours": 5.8,
    "strict_lead_time_iqr_low_hours": 2.666666666666667,
    "strict_lead_time_iqr_high_hours": 12.925
  },
  {
    "threshold": 0.1,
    "strict_true_alarm_stay_n": 381,
    "strict_lead_time_median_hours": 5.566666666666666,
    "strict_lead_time_iqr_low_hours": 2.5833333333333335,
    "strict_lead_time_iqr_high_hours": 11.933333333333334
  },
  {
    "threshold": 0.15,
    "strict_true_alarm_stay_n": 376,
    "strict_lead_time_median_hours": 4.9,
    "strict_lead_time_iqr_low_hours": 2.2874999999999996,
    "strict_lead_time_iqr_high_hours": 11.3625
  },
  {
    "threshold": 0.2,
    "strict_true_alarm_stay_n": 347,
    "strict_lead_time_median_hours": 4.533333333333333,
    "strict_lead_time_iqr_low_hours": 2.275,
    "strict_lead_time_iqr_high_hours": 10.333333333333332
  }
]
```

3. Does DCA show positive net benefit at low thresholds?
   - Positive model net benefit exists: `True`.
   - Positive thresholds by model are available in `dca_threshold_sweep_post_metre.csv`.

4. Did recalibrated DCA improve?
   - Recalibrated MT3 has higher net benefit than raw MT3 at thresholds: `[0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3]`.

5. Should the model remain a risk stratification tool rather than an automatic intervention trigger?
   - Yes. Even after METRE repair and recalibration, clinical utility varies by threshold and should not be framed as an automatic intervention trigger.

## Output interpretation

- `strict_24h_first_alarm_summary.csv` is the main lead-time table.
- `eventual_death_leadtime_summary.csv` is exploratory and explicitly not a strict 24h-label analysis.
- `dca_threshold_sweep_post_metre.csv` should replace the old DCA data interface for Figure 5.
