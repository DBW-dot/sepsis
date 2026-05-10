# Final PI Summary - Parsimonious Model

The final manuscript-facing model is `P15_clinically_parsimonious_transport_model`. It keeps the frozen eICU external AUROC 0.8103, AUPRC 0.1892, and calibration slope 1.0031.

P12 is a true-trained validated simplified implementation candidate and P10 is a true-trained validated ultra-minimal sensitivity candidate. They are important for clinical implementation discussion but do not replace P15 without a separate PI refreeze decision.

The most important implementation caveats are laboratory freshness and support proxy interpretation. Laboratory variables are latest-available / capped carry-forward values, not hourly real measurements. The 12h freshness result is borderline acceptable; the 24h freshness result is largely stable. The shared support-intensity proxy is not full VIS.

The project is ready for manuscript writing using the files in `FINAL_FILE_INDEX.md`, with archived materials treated as audit history only.
