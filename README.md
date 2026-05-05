# Reproducibility Pipeline — How Few Sensors Are Enough?

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20041039.svg)](https://doi.org/10.5281/zenodo.20041039)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Note:** the DOI badge above will resolve after the first GitHub Release is archived by Zenodo (see *Citing this software* below).

This repository contains the analysis pipeline for:

> Myroshnyk Y., Leshchenko O. *How Few Sensors Are Enough? Systematic Evaluation of Minimum Vital Sign Requirements for Machine Learning-Based Deterioration Prediction with Multi-Center Validation Across 138 Hospitals.* IEEE Access (under review), 2026.

## Contents

```
cas4_minimum_sensor_pipeline.ipynb    Main analysis pipeline (Steps 0–17)
requirements.txt                            Dependencies (range-pinned for forward compatibility)
setup.sh                                    One-line setup script
README.md                                   This file
LICENSE                                     MIT license
CITATION.cff                                Citation metadata
.gitignore                                  Excludes venv, caches, training artifacts
```

## Quick Start (the easy way)

```bash
git clone https://github.com/myroshnyk/cas4_minimum_sensor_pipeline.git
cd cas4_minimum_sensor_pipeline
bash setup.sh
source .venv/bin/activate
jupyter notebook cas4_minimum_sensor_pipeline.ipynb
```

The `setup.sh` script will:
1. Find a compatible Python (3.10, 3.11, 3.12, or 3.13)
2. Create a `.venv` virtual environment
3. Install all dependencies
4. Verify everything imports correctly

If you have multiple Python versions installed and want to force a specific one:

```bash
bash setup.sh 3.11
```

## Quick Start (manual, if `setup.sh` doesn't fit your workflow)

Any Python 3.10–3.13 will work:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Why range pins instead of exact pins?

Earlier versions of this repo used exact version pins (e.g. `catboost==1.2.2`). This caused install failures on Python 3.12+ because:
- `catboost==1.2.2` has no prebuilt wheel for Python 3.12
- pip would fall back to building from source
- The source build pulls `PyYAML==6.0` which is incompatible with modern Cython

The current `requirements.txt` uses minor-version ranges that:
- Always have prebuilt wheels available
- Stay within the same algorithmic generation as the versions used in the paper
- Produce numerically identical results (verified to 4 decimal places) thanks to fixed `RANDOM_STATE=42` throughout the notebook

The exact versions used in the paper are documented in Section III.H of the manuscript and in `results/all_results.json` (`metadata` field after running) for the historical record.

## Requirements

- Python 3.10–3.13
- ~50 GB free disk for MIMIC-IV `chartevents.csv.gz` + eICU `vitalPeriodic.csv.gz`
- ~16 GB RAM (XGBoost training is memory-intensive)
- Approved PhysioNet credentials with completed CITI training for both:
  - MIMIC-IV v3.1 (https://physionet.org/content/mimiciv/3.1/)
  - eICU-CRD v2.0 (https://physionet.org/content/eicu-crd/2.0/)

## Running the Pipeline

### Configure credentials

The notebook loads PhysioNet credentials from a local `.env` file (gitignored)
via [python-dotenv](https://pypi.org/project/python-dotenv/). Copy the template
and fill in your values:

```bash
cp .env.example .env
# then edit .env in your editor
```

Minimum contents of `.env`:

```
PHYSIONET_USER=your_physionet_username
# PHYSIONET_PASSWORD=your_password   # optional — leave commented to be prompted via getpass
# CAS_BASE_DIR=~/mimic4_study        # optional — defaults to ~/mimic4_study
```

If `PHYSIONET_PASSWORD` is left unset, the notebook prompts for it securely
at the download step (the password is never written to disk or the notebook).

Alternatively, you can export the variables in your shell instead of using
a `.env` file — exported environment variables take precedence over `.env`.

### Launch

```bash
jupyter notebook cas4_minimum_sensor_pipeline.ipynb
```

Or open the notebook directly in VS Code and select the `.venv` kernel.

In the notebook: **Kernel → Restart & Run All**.

Expected runtime on a workstation with 16 GB RAM, no GPU:

| Phase | Time |
|---|---|
| Steps 1–4 (download + cohort + features) | 60–90 min (chartevents.csv.gz is ~6 GB) |
| Step 6 (A(t) computation, vectorized) | 1–2 min |
| Steps 7–14 (XGBoost models + analyses) | 8–12 min |
| Step 15 (eICU validation) | 20–30 min (vitalPeriodic.csv.gz is ~1.7 GB) |
| Step 17 (bootstrap, n=2000) | 1–2 min |

Total cold start: ~1.5–2.5 hours. With cached data: ~25–50 minutes.

## Pipeline Structure

| Step | Description | Output |
|---|---|---|
| 0 | Configuration, imports | — |
| 1 | Download MIMIC-IV from PhysioNet | `raw/hosp/`, `raw/icu/` |
| 2 | Cohort extraction (n≈51,981 after filters) | `processed/cohort_final.csv` |
| 3 | Vital sign extraction from chartevents | `processed/vitals_raw.csv.gz` |
| 4 | Hourly resampling + 9 temporal features per vital | `processed/features_xgboost.csv` |
| 5 | Train/val/test split (70/15/15) | `train_idx`, `val_idx`, `test_idx` |
| 6 | A(t) recalibration on **training set only** | `processed/at_calibration.json`, `at_summary.csv` |
| 7 | XGBoost on 4 conditions (Full, NEWS2, CAS-4, CAS-4 hybrid) | — |
| 8 | NEWS2 scoring baseline | — |
| 9 | Feature reduction curve (9 sensor levels) | `results/feature_reduction_curve.csv`, `figures/fig_CENTRAL_reduction_curve.png` |
| 10 | CatBoost & RandomForest on CAS-4 conditions | `results/all_model_results.csv` |
| 11 | SHAP feature importance | `results/shap_ranking.csv`, `figures/fig_shap_cas4_hybrid.png` |
| 12 | Calibration analysis | `results/calibration_results.csv`, `figures/fig_calibration.png` |
| 13 | Decision Curve Analysis (with explicit NB@p_t=0.10) | `results/dca_results.csv`, `nb_at_pt10.csv`, `figures/fig_dca.png` |
| 14 | Subgroup analysis (age, sex) | `results/subgroup_results.csv` |
| 15 | eICU multi-center validation (hourly A(t)) | `processed/eicu_features.csv.gz`, `figures/fig_calibration_eicu.png` |
| 16 | Aggregate results to JSON | `results/all_results.json` |
| 17 | Bootstrap pairwise AUROC test (n=2000) | `results/bootstrap_auroc_comparisons.csv` |

## Key Results to Verify

After a full run, `results/all_results.json` should contain values close to those reported in the manuscript. See [CHANGELOG.md](CHANGELOG.md) for the per-release version history; the table below lists the **current (v1.1.0)** values.

| Metric | Value | Source in paper |
|---|---|---|
| MIMIC-IV cohort n | 51,981 | Table III |
| Mortality rate | 9.9% | Table III |
| L1-Full AUROC | 0.854 | Table II |
| L3-NEWS2 AUROC | 0.841 (was 0.774 in v1.0.0; see [CHANGELOG.md](CHANGELOG.md)) | Table II |
| L4-5vitals AUROC | 0.774 | Table II |
| L5-CAS4 AUROC | 0.756 | Table II |
| L5b-CAS4+A(t) AUROC | 0.758 | Table II |
| L5b-CAS4+A(t) calibration slope | 0.939 | Table II |
| L6-3vitals AUROC | 0.736 | Table II |
| L6-3vitals calibration slope | 1.006 | Table II |
| L7-2vitals AUROC | 0.684 | Table II |
| L7-2vitals calibration slope | 2.654 (under review, see Step 12c) | Table II |
| eICU AUROC | 0.776 | Table VII |
| eICU calibration slope | 0.965 | Table VII |
| eICU hospitals | 138 | Table VII |
| Knee point ΔAUROC (L5 vs L6) | -0.020, p<0.001 | Section IV.B |
| Knee point ΔAUROC (L6 vs L7, central claim) | -0.052 (formal p-value via Step 17) | Section IV.B |
| CAS-4 vs NEWS2-set ΔAUROC | -0.085, p<0.001 (was -0.017 in v1.0.0) | Section IV.B |

> **Note (v1.1.0):** GCS in MIMIC-IV is now reconstructed from its three component itemids (220739, 223900, 223901). The v1.0.0 release used the MIMIC-III legacy `itemid` 198, which does not exist in MIMIC-IV `chartevents`; this caused L3-NEWS2 to silently degrade to L4-5vitals. Numbers in the table above reflect the corrected pipeline. See [CHANGELOG.md](CHANGELOG.md) for full details.

> **Note (v4 → v5 internal):** Train-only A(t) calibration (introduced in v4) is preserved unchanged. The pipeline executes a formal bootstrap permutation test (Step 17) for the central L6 vs L7 knee-point claim. If you re-run and observe a numerical drift exceeding 0.01 AUROC for any reported metric, please open an issue.

### New diagnostic outputs in v4

The v4 pipeline produces additional CSVs and figures intended for reviewer scrutiny:

- `results/calibration_decile_diagnostic.csv` — decile-level observed/expected for top-3 models (addresses HL-test sensitivity at large n)
- `figures/fig_l7_calibration_diagnostic.png` — predicted-probability histograms for L6/L7/L8 + bootstrapped slope CI for L7 (addresses slope=2.654 sanity check)
- `results/dca_post_platt.csv` — DCA after Platt scaling on validation set (empirical test of recalibration claim)
- `results/eicu_hospital_selection_bias.csv` — characteristics of included vs. excluded eICU hospitals (selection-bias quantification)

## Methodology Notes

### A(t) Index Calibration (Step 6) — v4 fix

The A(t) alarm index from prior work [14] requires three components:
1. **Weights** *w_i* — empirical, derived from correlation between vital sign means and mortality
2. **Population statistics** *μ_i, σ_i* — for z-score normalization
3. **Multipliers** *m_i* — fixed clinical severity factors from [14]

In v3 of this notebook, weights and population statistics were computed on the full cohort before train/val/test split, which constituted test-set leakage. **In v4, both are computed on the training set only**, then applied to all patients (train, validation, test, and eICU).

### eICU Feature Engineering — v4 fix

Previous version computed eICU A(t) features as `at_max=at_mean`, `at_std=0.0`, `at_last=at_mean` (using only per-patient vital means rather than hourly trajectories). **In v4, eICU follows the same hourly methodology as MIMIC-IV**: hourly grid → forward-fill (3h) → hourly A(t) → mean/max/std/last summary. This is the prerequisite for the claim that the model is applied "without retraining or recalibration".

### Reproducibility

- All random operations seeded with `RANDOM_STATE=42`
- Bootstrap operations use `np.random.RandomState(42)` independently of global state
- Train/val/test indices are sorted after splitting for deterministic downstream operations
- All file paths use `os.path.expanduser` for portability

## Troubleshooting

**`bash setup.sh` says "No compatible Python found"**
Install Python 3.12 from https://www.python.org/downloads/ or via `brew install python@3.12` (macOS) / `apt install python3.12` (Ubuntu).

**`pip install` fails on `catboost`, `xgboost`, or another ML package**
You're probably on Python 3.14+ which has incomplete wheel coverage for ML libraries. Use Python 3.12 instead.

**`ModuleNotFoundError` after install**
Your Jupyter kernel is using a different Python than where you installed packages. In VS Code: Cmd/Ctrl+Shift+P → "Python: Select Interpreter" → choose `.venv/bin/python`. In the notebook: Kernel → Change Kernel → select `.venv`.

**PhysioNet 401/403 errors**
Verify your CITI training is current and that you signed the data use agreements at https://physionet.org/content/mimiciv/3.1/ AND https://physionet.org/content/eicu-crd/2.0/.

## Citing this software

If you use this code, please cite both the paper and the archived software release:

**Paper:**
Myroshnyk Y., Leshchenko O. *How Few Sensors Are Enough? Systematic Evaluation of Minimum Vital Sign Requirements for Machine Learning-Based Deterioration Prediction with Multi-Center Validation Across 138 Hospitals.* IEEE Access (under review), 2026.

**Software (Zenodo):**
Each tagged GitHub release is archived on Zenodo and assigned a DOI. Use the DOI corresponding to the version you used (visible on the Zenodo record page). The "concept DOI" `10.5281/zenodo.20041039` always resolves to the latest version.

A machine-readable citation entry is provided in [`CITATION.cff`](CITATION.cff) — GitHub displays a "Cite this repository" button that uses it.

## Contact

Yurii Myroshnyk — myroshnyk@gmail.com
ORCID: 0009-0004-5117-5289

## License

Code: MIT (see [LICENSE](LICENSE))
Data: subject to PhysioNet data use agreements (must be obtained separately)
