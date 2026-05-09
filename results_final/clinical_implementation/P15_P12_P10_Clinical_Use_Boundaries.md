# P15/P12/P10 Clinical Use Boundaries

## P15

- Formal main result model.
- Suitable for EHR auto-extraction and automated risk calculation.
- Not a manual bedside score.
- Not a bedside-only model.
- Requires routine laboratory values and shared support-intensity proxy variables.
- Should be the model used for primary manuscript claims.

## P12

- Preferred simplification candidate if clinical deployment requires lower feature burden.
- Simulated sensitivity / simulated implementation estimate only.
- Cannot replace P15 as the main result.
- Suitable for supplementary material, clinical implementation discussion, and local feasibility planning.
- Uses the dual-index proxy explanation: `shared_support_intensity_proxy + support_lactate_component`.

## P10

- Ultra-minimal sensitivity scenario.
- Suitable only for exploratory discussion in resource-constrained or rapid-screening settings.
- Simulated sensitivity / simulated implementation estimate only.
- Not recommended as the main model.
- Uses `shared_support_intensity_proxy` as the only proxy feature.
