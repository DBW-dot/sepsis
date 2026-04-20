# Sepsis Dynamic Competing-risk ChatGPT Share Repo

This folder is a GitHub-ready, ChatGPT-friendly share surface prepared from the local project at `C:\Users\GUO\Desktop\try`.

## Included

- `results_package/`
  - manuscript tables
  - figure data interfaces
  - Results / Discussion skeleton text
  - supplementary index
- `step9_results_packaging/py/run_step9_results_packaging.py`
  - the packaging script used to rebuild `results_package`
- `LOCAL_ASSET_INDEX.md`
  - what is included, what is excluded, and why
- `HEAVY_ARTIFACT_MANIFEST.csv`
  - a local index of large artifacts that remain outside GitHub

## Excluded on purpose

- raw MIMIC-IV and eICU data
- `duckdb`, `parquet`, model binaries, and other heavy local artifacts
- local runtime logs

## Why this structure

ChatGPT reads text, Markdown, CSV, code, and lightweight documentation much more reliably than large binary artifacts. This repository is therefore designed as an interface layer for code review, manuscript drafting, and result interpretation rather than as a full archival copy of the local workspace.

## Next step

Create an empty GitHub repository, then connect this folder to that repository and push it. After GitHub indexing catches up, ChatGPT can read this repository much more effectively than it can read the raw local project.
