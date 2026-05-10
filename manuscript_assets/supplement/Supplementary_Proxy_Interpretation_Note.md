# Supplementary Proxy Interpretation Note

## Meaning of shared support-intensity proxy

The shared support-intensity proxy is a cross-database support burden signal. It summarizes support intensity in a way that can be mapped across MIMIC and eICU.

## Not full VIS

The proxy is not full VIS. Full VIS was not used as the external transport input.

## Component meanings

- Hemodynamic component: hemodynamic support burden.
- Lactate component: perfusion/low-flow burden and clinically interpretable severity context.
- Renal component: renal support burden.
- Respiratory component: respiratory support burden.

## Treatment-behavior confounding

Support proxy variables partly reflect clinician treatment behavior and monitoring context. They should not be interpreted causally and should not be described as intervention effects.

## Implementation boundary

The proxy should be implemented as an EHR-derived variable, not as a clinician hand-calculated score.
