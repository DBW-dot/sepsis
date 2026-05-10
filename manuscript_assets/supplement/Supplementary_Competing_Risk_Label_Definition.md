# Supplementary Competing-risk Label Definition

## Why not simple binary classification

A simple 24-hour death-vs-nondeath label would treat alive ICU discharge/transfer as if it were equivalent to remaining in the ICU, which is clinically and statistically inappropriate for short-horizon ICU risk prediction.

## Three mutually exclusive states

At each prediction time, the 24-hour label distinguishes ICU death, alive ICU discharge/transfer, and continued ICU stay. These states are mutually exclusive within the 24-hour horizon.

## Discharge or transfer as a competing event

Alive ICU discharge/transfer removes a patient from the ICU death risk set during the 24-hour window, so it is handled as a competing event rather than ordinary censoring.

## Model output interpretation

Model outputs should be interpreted as short-horizon competing-risk probabilities. If cumulative-incidence formulas are required for the final manuscript, they should be sourced from an approved methods file before use.

## Clinical utility boundary

DCA and first-alarm lead-time analyses are supplementary estimates. They are not automatic intervention triggers or direct treatment recommendations.
