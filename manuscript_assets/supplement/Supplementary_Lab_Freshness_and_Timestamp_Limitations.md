# Supplementary Lab Freshness and Timestamp Limitations

## Latest-value interpretation

Laboratory `latest_value` variables are latest-available / capped carry-forward values. They are not assumed to be newly measured every hour.

## P15 12h freshness sensitivity

P15 eICU AUROC/AUPRC/calibration slope under the 12h freshness scenario was 0.7847 / 0.1674 / 0.9779. This result is borderline acceptable, not fully noninferior.

## P15 24h freshness sensitivity

P15 eICU AUROC/AUPRC/calibration slope under the 24h freshness scenario was 0.8085 / 0.1860 / 0.9991. This result is largely stable.

## Timestamp limitations

Result availability time is incomplete in the available source structure. Chart/sample time was used as a conservative approximation. No additional look-ahead was identified under the available timestamp structure, but the manuscript should not claim that all look-ahead risk was fully eliminated.

## Proxy dependence

Some support-intensity proxy components may depend on laboratory-derived information, such as lactate/perfusion or renal support signals. These components require the same freshness and timestamp caution.

## Manuscript placement

Lab freshness is a supplementary realism analysis and does not replace the locked main P15 result.
