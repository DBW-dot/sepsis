# Final English Figure Legends

**Graphical Abstract. P15 avoids the external calibration collapse seen in the high-dimensional pathway by combining dual anchoring, competing-risk framing, and clinically parsimonious variables.** The left panel summarizes the traditional high-dimensional pathway, whereas the right panel summarizes the P15 pathway and its eICU performance.

**Figure 1. The study workflow integrates data sources, dual-anchor dynamic prediction, and competing-risk outcomes in one framework.** MIMIC-IV was used for development/internal validation and eICU for external validation.

**Figure 1B. Dual-anchor temporal alignment explicitly separates ICU process time from sepsis disease time.** This representation preserves both time since ICU admission and time since sepsis onset.

**Figure 2. Strong internal discrimination did not guarantee external transportability, whereas P15 remained externally stable.** The high-dimensional M1 model dropped sharply from MIMIC-IV to eICU, while P15 maintained transportable performance.

**Figure 3. P15 showed substantially better external calibration against observed 24-hour ICU death frequency.** The blue line represents P15, the red dashed line represents the 70-feature model, and the gray dashed line denotes ideal calibration.

**Figure 4. P15 supported low-threshold risk stratification in DCA but should not be interpreted as an automatic intervention trigger.** Net benefit decreased at higher thresholds.

**Figure 5. P15 retained phenotype-stratified discrimination in eICU, with residual calibration pressure varying by phenotype.** These results support audit and recalibration, not treatment-subtype claims.

**Figure 6. P15 feature importance versus deployment difficulty shows the trade-off between transparency and implementation burden.** Importance is based on the frozen model death-class coefficients and is not causal.

**Supplementary Figure S1. Threshold-specific sensitivity, PPV, and net benefit illustrate the operational trade-off for P15 in eICU.** Recall is threshold-dependent and is not a primary performance metric.
