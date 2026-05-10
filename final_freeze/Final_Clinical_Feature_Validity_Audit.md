# Final Clinical Feature Validity Audit

The final P15 feature set remains clinically reasonable for EHR implementation. It is not a manual bedside-only score because several variables require routine laboratory availability, timestamp handling, and derived support-burden proxy construction.

The main feature risks are laboratory freshness and interpretability of proxy components. These risks are now explicitly handled through the lab freshness sensitivity audit and the proxy clinical interpretability audit.

No final main-path file should describe P12 or P10 as replacing P15. No final main-path file should conflate the shared support-intensity proxy with full VIS.
