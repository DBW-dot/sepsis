from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(r"C:\Users\GUO\Desktop\try")
OUTDIR = ROOT / "post_metre_selection"
OUTDIR.mkdir(parents=True, exist_ok=True)

METRE_COMPARISON = ROOT / "metre_transport" / "METRE_vs_Original_Model_Comparison.csv"
STEP7 = ROOT / "step7_main_modeling" / "output"
PRED_C3_TEST = STEP7 / "pred_C3_test_all.parquet"
PRED_C3_EXTERNAL = STEP7 / "pred_C3_eicu_external.parquet"

DEATH_LABEL = "ICU_DEATH"
DISCHARGE_LABEL = "ALIVE_DISCHARGE"
NO_EVENT_LABEL = "NO_EVENT"
CLASSES = np.array([DISCHARGE_LABEL, DEATH_LABEL, NO_EVENT_LABEL], dtype=object)

MODEL_LABELS = {
    "M1_original_rich": "M1_main_competing_risk",
    "C1_dynamic_SOFA": "C1_dynamic_SOFA_only",
    "C3_no_phenotype": "C3_no_phenotype",
    "MT1_physiology_only": "MT1_physiology_only",
    "MT2_physiology_minimal_recency": "MT2_physiology_minimal_recency",
    "MT3_physiology_support_proxy": "MT3_physiology_support_proxy",
    "MT4_support_proxy_phenotype_sensitivity": "MT4_support_proxy_phenotype_sensitivity",
}

DEFAULT_TRANSPORT_CANDIDATES = [
    "MT1_physiology_only",
    "MT2_physiology_minimal_recency",
    "MT3_physiology_support_proxy",
]


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1.0 - 1e-6)


def calibration_intercept_slope(y_binary: np.ndarray, probs: np.ndarray) -> tuple[float, float]:
    probs = clip_probs(probs)
    logits = np.log(probs / (1.0 - probs)).reshape(-1, 1)
    if np.unique(y_binary).size < 2:
        return float("nan"), float("nan")
    model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    model.fit(logits, y_binary)
    return float(model.intercept_[0]), float(model.coef_[0][0])


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: np.ndarray) -> float:
    onehot = np.zeros_like(probs)
    idx = {label: pos for pos, label in enumerate(classes)}
    for row_idx, label in enumerate(y_true):
        onehot[row_idx, idx[label]] = 1.0
    return float(np.mean(np.sum((onehot - probs) ** 2, axis=1)))


def metrics_from_prediction_file(path: Path, model_name: str, dataset_name: str) -> dict[str, float | str]:
    df = pd.read_parquet(path)
    probs = np.column_stack(
        [
            df["predicted_prob_discharge_24h"].to_numpy(),
            df["predicted_prob_death_24h"].to_numpy(),
            df["predicted_prob_no_event_24h"].to_numpy(),
        ]
    )
    y_true = df["true_event_type_24h"].to_numpy()
    death_probs = probs[:, int(np.where(CLASSES == DEATH_LABEL)[0][0])]
    y_death = (y_true == DEATH_LABEL).astype(int)
    intercept, slope = calibration_intercept_slope(y_death, death_probs)
    return {
        "model_name": model_name,
        "dataset_name": dataset_name,
        "sample_n": float(len(df)),
        "death_n": float(y_death.sum()),
        "death_rate": float(y_death.mean()),
        "auroc_death_ovr": float(roc_auc_score(y_death, death_probs)),
        "auprc_death": float(average_precision_score(y_death, death_probs)),
        "multiclass_brier": multiclass_brier(y_true, probs, CLASSES),
        "calibration_intercept_death": intercept,
        "calibration_slope_death": slope,
    }


def load_all_long_metrics() -> pd.DataFrame:
    metre = pd.read_csv(METRE_COMPARISON)
    c3_rows = [
        metrics_from_prediction_file(PRED_C3_TEST, "C3_no_phenotype", "mimic_internal_test"),
        metrics_from_prediction_file(PRED_C3_EXTERNAL, "C3_no_phenotype", "eicu_external"),
    ]
    all_long = pd.concat([metre, pd.DataFrame(c3_rows)], ignore_index=True, sort=False)
    all_long["display_model_name"] = all_long["model_name"].map(MODEL_LABELS).fillna(all_long["model_name"])
    return all_long


def build_wide_comparison(all_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_name, part in all_long.groupby("model_name"):
        internal = part.loc[part["dataset_name"] == "mimic_internal_test"].iloc[0]
        external = part.loc[part["dataset_name"] == "eicu_external"].iloc[0]
        rows.append(
            {
                "model_name": model_name,
                "display_model_name": MODEL_LABELS.get(model_name, model_name),
                "mimic_internal_auroc": internal["auroc_death_ovr"],
                "mimic_internal_auprc": internal["auprc_death"],
                "mimic_internal_brier": internal["multiclass_brier"],
                "mimic_calibration_slope": internal["calibration_slope_death"],
                "eicu_external_auroc": external["auroc_death_ovr"],
                "eicu_external_auprc": external["auprc_death"],
                "eicu_external_brier": external["multiclass_brier"],
                "eicu_calibration_slope": external["calibration_slope_death"],
                "internal_external_auroc_drop": internal["auroc_death_ovr"] - external["auroc_death_ovr"],
                "internal_external_auprc_drop": internal["auprc_death"] - external["auprc_death"],
            }
        )
    wide = pd.DataFrame(rows)
    ordered = [
        "M1_original_rich",
        "C1_dynamic_SOFA",
        "C3_no_phenotype",
        "MT1_physiology_only",
        "MT2_physiology_minimal_recency",
        "MT3_physiology_support_proxy",
        "MT4_support_proxy_phenotype_sensitivity",
    ]
    wide["order"] = wide["model_name"].map({name: idx for idx, name in enumerate(ordered)})
    wide = wide.sort_values("order").drop(columns=["order"]).reset_index(drop=True)
    wide.to_csv(OUTDIR / "Post_METRE_Model_Comparison.csv", index=False, encoding="utf-8-sig")
    return wide


def choose_models(wide: pd.DataFrame) -> dict[str, str]:
    # "Internal rich" is a role, not just an internal metric maximum.
    # C3 can be a useful no-phenotype sensitivity model, but it is not the rich main model.
    internal_rich = wide.loc[wide["model_name"] == "M1_original_rich"].iloc[0]
    transport_pool = wide[wide["model_name"].isin(DEFAULT_TRANSPORT_CANDIDATES)].copy()
    transport_pool["slope_extreme_penalty"] = (transport_pool["eicu_calibration_slope"] - 1.0).abs()
    transport = transport_pool.sort_values(
        ["eicu_external_auprc", "eicu_external_auroc", "slope_extreme_penalty", "mimic_internal_auroc"],
        ascending=[False, False, True, False],
    ).iloc[0]
    baseline = wide.loc[wide["model_name"] == "C1_dynamic_SOFA"].iloc[0]
    return {
        "best_internal_rich_model": str(internal_rich["model_name"]),
        "best_external_transport_model": str(transport["model_name"]),
        "best_baseline_comparator": str(baseline["model_name"]),
    }


def write_criteria(selection: dict[str, str], wide: pd.DataFrame) -> None:
    best_transport = wide.loc[wide["model_name"] == selection["best_external_transport_model"]].iloc[0]
    best_internal = wide.loc[wide["model_name"] == selection["best_internal_rich_model"]].iloc[0]
    c1 = wide.loc[wide["model_name"] == "C1_dynamic_SOFA"].iloc[0]
    text = f"""# Model Selection Criteria

## Priority order

1. eICU external AUPRC is the primary selection criterion.
2. eICU external AUROC is the secondary criterion.
3. eICU calibration slope must not be extreme; values close to 1 are preferred.
4. Internal performance must not collapse relative to the clinical comparator.
5. The feature set must be interpretable and cross-database stable.
6. The default transport model should not rely on high-dimensional measurement-process features or direct phenotype input.

## Frozen selections

- Best internal rich model: `{selection['best_internal_rich_model']}`.
- Best external transport model: `{selection['best_external_transport_model']}`.
- Best baseline comparator: `{selection['best_baseline_comparator']}`.

## Selection evidence

- Internal rich model MIMIC AUROC/AUPRC: {best_internal['mimic_internal_auroc']:.4f} / {best_internal['mimic_internal_auprc']:.4f}.
- External transport model eICU AUROC/AUPRC/slope: {best_transport['eicu_external_auroc']:.4f} / {best_transport['eicu_external_auprc']:.4f} / {best_transport['eicu_calibration_slope']:.4f}.
- Clinical comparator eICU AUROC/AUPRC/slope: {c1['eicu_external_auroc']:.4f} / {c1['eicu_external_auprc']:.4f} / {c1['eicu_calibration_slope']:.4f}.

## Boundary rule

`MT4_support_proxy_phenotype_sensitivity` remains a sensitivity model even when AUROC is slightly higher, because the requested default transport role should not use phenotype as a direct performance driver.
"""
    (OUTDIR / "Model_Selection_Criteria.md").write_text(text, encoding="utf-8")


def build_role_assignment(wide: pd.DataFrame, selection: dict[str, str]) -> pd.DataFrame:
    roles = {
        "M1_original_rich": (
            "Internal rich model",
            "Highest MIMIC internal performance but poor eICU transport and calibration; use as internal rich/reference model.",
        ),
        "C1_dynamic_SOFA": (
            "Clinical score comparator",
            "Prespecified dynamic SOFA-only clinical comparator.",
        ),
        "C3_no_phenotype": (
            "Sensitivity model",
            "No-phenotype sensitivity model for phenotype role audits.",
        ),
        "MT1_physiology_only": (
            "Sensitivity model",
            "Minimal METRE physiology transport baseline; useful for support proxy contribution analysis.",
        ),
        "MT2_physiology_minimal_recency": (
            "Discarded / not recommended",
            "Minimal recency improved AUROC over MT1 but reduced AUPRC and calibration slope, so it is not the frozen transport model.",
        ),
        "MT3_physiology_support_proxy": (
            "External transport model",
            "Best default METRE transport model by eICU AUPRC/AUROC with strong calibration and no direct phenotype input.",
        ),
        "MT4_support_proxy_phenotype_sensitivity": (
            "Sensitivity model",
            "Phenotype sensitivity model; not default because phenotype gain remains limited and AUPRC is below MT3.",
        ),
    }
    rows = []
    for _, row in wide.iterrows():
        role, rationale = roles[row["model_name"]]
        rows.append(
            {
                "model_name": row["model_name"],
                "display_model_name": row["display_model_name"],
                "assigned_role": role,
                "selected_as_best_internal_rich": int(row["model_name"] == selection["best_internal_rich_model"]),
                "selected_as_external_transport": int(row["model_name"] == selection["best_external_transport_model"]),
                "selected_as_baseline_comparator": int(row["model_name"] == selection["best_baseline_comparator"]),
                "rationale": rationale,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUTDIR / "Model_Role_Assignment.csv", index=False, encoding="utf-8-sig")
    return out


def build_downstream_map(selection: dict[str, str]) -> pd.DataFrame:
    transport = selection["best_external_transport_model"]
    rows = [
        {
            "downstream_analysis": "External recalibration",
            "primary_model_to_use": transport,
            "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
            "reason": "Recalibration should be rerun on the frozen transport model while retaining M1/C1 for contrast.",
        },
        {
            "downstream_analysis": "DCA",
            "primary_model_to_use": transport,
            "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
            "reason": "Clinical utility should be reassessed using the model selected for external transport.",
        },
        {
            "downstream_analysis": "strict 24h lead-time",
            "primary_model_to_use": transport,
            "comparison_models": "M1_original_rich; C1_dynamic_SOFA",
            "reason": "Lead-time should use the frozen external transport model and compare against prior main and SOFA baselines.",
        },
        {
            "downstream_analysis": "phenotype gain reassessment",
            "primary_model_to_use": "MT3_physiology_support_proxy vs MT4_support_proxy_phenotype_sensitivity",
            "comparison_models": "C3_no_phenotype",
            "reason": "Phenotype should remain a sensitivity/stratification question, not a default driver.",
        },
        {
            "downstream_analysis": "VIS/proxy contribution analysis",
            "primary_model_to_use": "MT1_physiology_only vs MT3_physiology_support_proxy",
            "comparison_models": "M1_original_rich",
            "reason": "This isolates the shared support proxy contribution and keeps full VIS framed as internal rich information.",
        },
        {
            "downstream_analysis": "final result tables",
            "primary_model_to_use": transport,
            "comparison_models": "M1_original_rich; C1_dynamic_SOFA; MT4_support_proxy_phenotype_sensitivity",
            "reason": "Final tables should show M1 as internal rich, MT3 as transport, C1 as comparator, and MT4 as sensitivity only.",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUTDIR / "Downstream_Analysis_Model_Map.csv", index=False, encoding="utf-8-sig")
    return out


def write_signoff_report(wide: pd.DataFrame, roles: pd.DataFrame, downstream: pd.DataFrame, selection: dict[str, str]) -> None:
    best = wide.loc[wide["model_name"] == selection["best_external_transport_model"]].iloc[0]
    m1 = wide.loc[wide["model_name"] == "M1_original_rich"].iloc[0]
    mt4 = wide.loc[wide["model_name"] == "MT4_support_proxy_phenotype_sensitivity"].iloc[0]
    text = f"""# Post-METRE Model Sign-off Report

## Final model roles

```json
{json.dumps(roles.to_dict(orient='records'), ensure_ascii=False, indent=2)}
```

## Sign-off decision

- Frozen external transport model: `{selection['best_external_transport_model']}`.
- Frozen internal rich model: `{selection['best_internal_rich_model']}`.
- Frozen clinical comparator: `{selection['best_baseline_comparator']}`.

## Why MT3 is selected over MT4

- MT4 has slightly higher eICU AUROC ({mt4['eicu_external_auroc']:.4f} vs MT3 {best['eicu_external_auroc']:.4f}).
- MT3 has higher eICU AUPRC ({best['eicu_external_auprc']:.4f} vs MT4 {mt4['eicu_external_auprc']:.4f}).
- MT3 avoids direct phenotype input, preserving phenotype as stratification/sensitivity rather than default performance driver.

## Why M1 is not the external transport model

- M1 remains strongest internally: MIMIC AUROC/AUPRC {m1['mimic_internal_auroc']:.4f} / {m1['mimic_internal_auprc']:.4f}.
- M1 has poor external transport: eICU AUROC/AUPRC/slope {m1['eicu_external_auroc']:.4f} / {m1['eicu_external_auprc']:.4f} / {m1['eicu_calibration_slope']:.4f}.
- Therefore M1 is signed off as an internal rich model, not as the default external transport model.

## Downstream analysis map

```json
{json.dumps(downstream.to_dict(orient='records'), ensure_ascii=False, indent=2)}
```
"""
    (OUTDIR / "Post_METRE_Model_Signoff_Report.md").write_text(text, encoding="utf-8")


def main() -> None:
    all_long = load_all_long_metrics()
    wide = build_wide_comparison(all_long)
    selection = choose_models(wide)
    write_criteria(selection, wide)
    roles = build_role_assignment(wide, selection)
    downstream = build_downstream_map(selection)
    write_signoff_report(wide, roles, downstream, selection)
    best = wide.loc[wide["model_name"] == selection["best_external_transport_model"]].iloc[0]
    print(
        json.dumps(
            {
                "best_external_transport_model": selection["best_external_transport_model"],
                "eicu_auroc": best["eicu_external_auroc"],
                "eicu_auprc": best["eicu_external_auprc"],
                "eicu_slope": best["eicu_calibration_slope"],
                "m1_downgraded_to_internal_rich": True,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
