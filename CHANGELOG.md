# Changelog

All notable changes to this repository are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The internal pipeline version string is reported in
`results/all_results.json[metadata.version]` after each run; the repo/release
version (this file, `CITATION.cff`) follows semver.

---

## [1.1.1] — 2026-05-05 — Calibration metrics expansion

Internal pipeline version: `Scenario_C_v5_gcs_fix` (unchanged).

No existing numerical results changed in this release. Adds three calibration
metrics that close residual gaps in the panel.

### Added

- **eICU CITL.** `cal_itl(y_eicu, y_prob_eicu)` is now computed alongside
  `slope_e` and `brier_e` in Cell 60 and reported in
  `all_results.json[eicu_validation.citl]`. Result: +0.265, nearly identical
  to the MIMIC test-set CITL of +0.255 for the same model — indicating that
  the systematic over-prediction is intrinsic to the XGBoost +
  `scale_pos_weight` configuration, not cohort-specific. Implication: the
  Platt-scaling recalibration that fixes MIMIC calibration generalizes to
  eICU.
- **Post-Platt Brier and BSS** for CAS-4 hybrid A + XGBoost on the test set
  (Cell 55). Results saved to `results/post_platt_calibration.csv` and
  `all_results.json[post_platt_calibration]`. Key numbers:
  - Brier: 0.160 → 0.081 (−49%)
  - Scaled Brier: −0.78 → +0.09 (crosses the no-skill baseline)
  - CITL: +0.255 → −0.001 (essentially perfect)
  - Net benefit at p_t=0.10: 0.0068 → 0.0382 (×5.6)
- **L7 calibration-slope bootstrap CI** persisted to
  `results/l7_slope_bootstrap.json` (point estimate 2.65, 95% CI
  [2.37, 2.92], σ = 0.14, *n* = 1000, seed 42). Confirms the L7 slope is
  numerically stable rather than an estimation artifact.

### Changed

- None. All v1.1.0 numbers reproduce exactly.

---

## [1.1.0] — 2026-05-05 — GCS reconstruction fix

Internal pipeline version: `Scenario_C_v5_gcs_fix` (was `Scenario_C_v4`).

### Fixed

- **GCS extraction now uses the correct MIMIC-IV itemids.** The previous
  release used MIMIC-III legacy `itemid` 198 for `gcs_total`, which does not
  exist in MIMIC-IV `chartevents`. As a result, `gcs_total` silently dropped
  from the feature matrix and the L3-NEWS2 reduction level collapsed to L4
  (identical 45 columns, identical AUROC=0.7735).
  - Now extracts the three component itemids `220739` (eye), `223900`
    (verbal), `223901` (motor) and reconstructs `gcs_total` per
    `(stay_id, charttime)` when all three components are charted, following
    the [MIT-LCP `mimic-code`](https://github.com/MIT-LCP/mimic-code)
    convention. Synthetic totals are filtered to plausible range 3–15.
  - Plausibility ranges added per component (1–4 / 1–5 / 1–6).
  - `Cell 5`, `Cell 16`, `Cell 20` updated. `Cell 20` now iterates over every
    vital column in `hourly_full` rather than `VITAL_SIGN_ITEMS.keys()`, so
    reconstructed columns are picked up automatically.

### Added

- **L3-NEWS2 SHAP analysis.** New cell after the existing CAS-4 SHAP cell
  retrains XGBoost on the L3-NEWS2 column set and exports
  `results/shap_ranking_l3_news2.csv` and `figures/fig_shap_l3_news2.png`.
- **Self-healing block in Cell 39 (Step 9b diagnostic).** Reconstructs
  `reduction_features` from `REDUCTION_LEVELS` if the dict is not in scope,
  so the diagnostic runs without re-executing the full Step 9 loop.
- **`.env` workflow.** `python-dotenv` integration: credentials and optional
  config (`PHYSIONET_USER`, `PHYSIONET_PASSWORD`, `CAS_BASE_DIR`) are loaded
  from a local `.env` file via `load_dotenv()` at the top of the notebook.
  Template provided in `.env.example`. `python-dotenv>=1.0` added to
  `requirements.txt`.
- **`rebuild_features.py`** — one-time script to rebuild
  `features_xgboost.csv` from a cached `hourly_series.csv.gz` without
  re-parsing the 5 GB chartevents file. Useful when the feature engineering
  logic changes but the upstream extraction is current.
- **`MANUSCRIPT_CHANGES.md`** — checklist of every place in the manuscript
  that needs to change as a result of the GCS fix (numeric replacements,
  paragraph rewrites, figure re-renders).

### Changed — affected results

L4 through L8 are unchanged. Only L1, L2, L3 and the L1/L3-derived rows of the
calibration / DCA / model-comparison tables move. Cohort size (51,981 stays),
mortality rate (9.9%), and the central L6 vs L7 knee-point claim are
unchanged.

| Metric | v1.0.0 (broken) | **v1.1.0 (fixed)** |
|---|---|---|
| L1-Full features | 94 | **103** |
| L1-Full AUROC | 0.8557 | 0.8544 |
| **L3-NEWS2 features** | **45** | **54** |
| **L3-NEWS2 AUROC** | **0.7735** | **0.8408** |
| L3-NEWS2 cal. slope | 1.067 | 1.014 |
| L3-NEWS2 NB at p=0.10 | 0.0033 | 0.0249 |
| CAS-4 vs NEWS2-set ΔAUROC | -0.017 (***) | **-0.085 (***)** |

The CAS-4 vs NEWS2-set comparison flips from "CAS-4 nearly matches NEWS2-set"
to "CAS-4 sacrifices 8.5 pp AUROC for the wearable form factor." This is a
substantive change to the manuscript narrative; see `MANUSCRIPT_CHANGES.md`
for the full edit list.

The new top-1 SHAP feature for L3-NEWS2 is `gcs_total_last`, with mean
|SHAP| = 0.677 — over 3× the next feature. Five of the top ten L3 features
are GCS-derived.

---

## [1.0.0] — 2026-05-05 — Initial public release

Internal pipeline version: `Scenario_C_v4`.

- First public release on Zenodo (DOI [10.5281/zenodo.20041039](https://doi.org/10.5281/zenodo.20041039)).
- Train-only A(t) calibration (no leakage from val/test into A(t) weights).
- Bootstrap permutation test for the central L6 vs L7 knee-point claim.
- SHAP ranking exported to CSV.
- DCA net benefit at p_t=0.10 explicitly reported.
- Multi-center external validation across 138 eICU-CRD hospitals.
- **Known issue (fixed in 1.1.0):** GCS itemid mismatch caused L3-NEWS2 to
  silently degrade to L4-5vitals.

[1.1.1]: https://github.com/myroshnyk/cas4_minimum_sensor_pipeline/releases/tag/v1.1.1
[1.1.0]: https://github.com/myroshnyk/cas4_minimum_sensor_pipeline/releases/tag/v1.1.0
[1.0.0]: https://github.com/myroshnyk/cas4_minimum_sensor_pipeline/releases/tag/v1.0.0
