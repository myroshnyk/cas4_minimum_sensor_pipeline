# Reproducibility Pipeline — How Few Sensors Are Enough?

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20041039.svg)](https://doi.org/10.5281/zenodo.20041039)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Note:** the DOI badge above will resolve after the first GitHub Release is archived by Zenodo (see *Citing this software* below).

This repository contains the analysis pipeline for:

> Myroshnyk Y., Leshchenko O. *How Few Sensors Are Enough? Systematic Evaluation of Minimum Vital Sign Requirements for Machine Learning-Based Deterioration Prediction with Multi-Center Validation Across 139 Hospitals.* IEEE Access (under review), 2026.

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

Set credentials (avoids interactive prompts):

```bash
export PHYSIONET_USER="your_physionet_username"
export PHYSIONET_PASSWORD="your_password"
export CAS_BASE_DIR="$HOME/mimic4_study"   # optional, defaults to ~/mimic4_study
```

Launch:

```bash
jupyter notebook cas4_minimum_sensor_pipeline.ipynb
```

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

After a full run, `results/all_results.json` should contain values close to:

| Metric | Expected | Source in paper |
|---|---|---|
| MIMIC-IV cohort n | 51,981 | Table III |
| Mortality rate | 9.9% | Table III |
| L5-CAS4 AUROC | 0.759 | Table II |
| L5b-CAS4+A(t) calibration slope | 0.999 | Table II |
| eICU AUROC | 0.734 | Table VII |
| eICU calibration slope | 1.045 | Table VII |
| Knee point delta_AUROC (CAS-4 vs 3-vitals) | -0.053, p<0.001 | Section IV.B |

> **Note (v4):** Train-only A(t) calibration may shift these values slightly from the v3 results reported in the manuscript. Re-run and update the manuscript accordingly.

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
Myroshnyk Y., Leshchenko O. *How Few Sensors Are Enough? Systematic Evaluation of Minimum Vital Sign Requirements for Machine Learning-Based Deterioration Prediction with Multi-Center Validation Across 139 Hospitals.* IEEE Access (under review), 2026.

**Software (Zenodo):**
Each tagged GitHub release is archived on Zenodo and assigned a DOI. Use the DOI corresponding to the version you used (visible on the Zenodo record page). The "concept DOI" `10.5281/zenodo.20041039` always resolves to the latest version.

A machine-readable citation entry is provided in [`CITATION.cff`](CITATION.cff) — GitHub displays a "Cite this repository" button that uses it.

## Contact

Yurii Myroshnyk — myroshnyk@gmail.com
ORCID: 0009-0004-5117-5289

## License

Code: MIT (see [LICENSE](LICENSE))
Data: subject to PhysioNet data use agreements (must be obtained separately)
