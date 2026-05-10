# Final Consistency Cleanup Plan

## Objective

Freeze the repository main path around the final parsimonious P15 model, true-trained P12/P10 implementation candidates, and lab freshness audit. Preserve superseded analyses in `archive/` for audit, rather than deleting result-bearing files.

## Keep principles

- Keep final public entry points: `README.md`, `FINAL_PROJECT_SUMMARY.md`, and `FINAL_FILE_INDEX.md`.
- Keep final model role and clinical implementation audit files under `final_freeze/`.
- Keep true-training P12/P10 validation and lab freshness outputs under `results_final/clinical_implementation/`.
- Keep final writing support under `results_final/text/`.

## Archive principles

- Archive old Pre-METRE/Post-METRE working directories and previous result packages.
- Archive old simulation-only P10/P12 materials that are superseded by true-training validation.
- Archive old figure interfaces and old scripts that are no longer the final reading path.

## Delete principles

Only cache or compiled artifacts were eligible for deletion, such as `__pycache__` and `.pyc`. No result-bearing files were permanently deleted without archiving or recording.
