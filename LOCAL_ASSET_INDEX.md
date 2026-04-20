# Local Asset Index

## Included in this share repo

- `results_package/`
- `step9_results_packaging/py/run_step9_results_packaging.py`
- this index
- `HEAVY_ARTIFACT_MANIFEST.csv`

## Left local only

- raw database directories:
  - `eicu/`
  - `mimic-iv-3.1/`
- heavy analytical outputs:
  - `*.duckdb`
  - `*.parquet`
  - `*.pkl`
- runtime logs and transient files

## Rationale

This split is intentional. The GitHub repository is meant to help ChatGPT read the project structure, manuscript package, and lightweight result interfaces without forcing code search and file reading through very large binaries that are poorly suited for GitHub-first analysis.
