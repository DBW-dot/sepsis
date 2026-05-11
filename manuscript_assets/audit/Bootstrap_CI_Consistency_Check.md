# Bootstrap CI Consistency Check

## Checks

1. Patient-level / cluster-level bootstrap used: yes.
2. Row-level bootstrap avoided: yes.
3. Frozen point estimates not modified: yes.
4. P15/P12/P10 roles unchanged: yes.
5. P12/P10 not described as replacing P15: yes.
6. Lab latest values not described as hourly measurements: yes.
7. Proxy not described as full VIS: yes.
8. DCA/lead-time not described as intervention triggers: yes.
9. Metrics with unavailable CI: 0 rows.
10. Bootstrap point-estimate conflicts: none detected. The maximum absolute difference between recomputed full-sample estimates and authoritative Table 2 point estimates was below `5e-4`, and no authoritative point estimate was overwritten.

## Notes

Calibration bootstrap uses the same cluster resamples. For computational stability at 1000 resamples on million-row prediction tables, calibration intercept/slope are recomputed on prediction-logit quantile bins within each resample, while all published point estimates remain the exact frozen values from the authoritative result tables.
