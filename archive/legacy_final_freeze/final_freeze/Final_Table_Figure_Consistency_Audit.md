# Final Table/Figure Consistency Audit

## Verdict

Post-METRE table and figure consistency: `PASS`.

## Numeric table checks

| audit_item | pass_n | total_n |
|---|---:|---:|
| Table2_vs_Post_METRE_Model_Comparison | 40 | 40 |
| Table3_vs_component_reassessment | 24 | 24 |
| Table4_vs_component_reassessment | 32 | 32 |


Number of inconsistent numeric cells: `0`.

## Figure 5 checks

| Check | Status |
|---|---:|
| Contains strict 24h first-alarm panel | True |
| Contains exploratory eventual-death lead-time panel | True |
| Contains DCA 24h death panel | True |
| Strict lead-time max <= 24h | True |
| Includes recalibrated MT3 DCA | True |
| Eventual-death lead-time explicitly marked not strict 24h | True |

## Figure 6 checks

| Check | Status |
|---|---:|
| Expected external failure modes present | True |
| Missing failure modes | none |
| Post-METRE result text mentions MT3/support/phenotype updates | True |

## Interpretation

- Table2_Post_METRE is numerically audited against `Post_METRE_Model_Comparison.csv`.
- Table3_Post_METRE is numerically audited against `component_ablation_results.csv` for phenotype model variants.
- Table4_Post_METRE is numerically audited against `component_ablation_results.csv` for measurement-process variants.
- Figure5_Post_METRE uses strict 24h first-alarm as the main lead-time interface and separately labels eventual-death lead-time as exploratory.
- Figure6_Post_METRE reflects external failure-mode updates after METRE repair.
