"""
One-time rebuild of features_xgboost.csv from the cached hourly_series.csv.gz
and cohort_final.csv. Use this after the GCS fix (Cell 5 + Cell 16 patches)
when the hourly grid already contains gcs_total but the features file does not.

Replicates the logic of notebook Cell 20 (patched: iterates over every vital
column in hourly_full, not just VITAL_SIGN_ITEMS.keys()), so reconstructed
columns like gcs_total produce gcs_total_mean, gcs_total_std, etc.

Usage:
    python rebuild_features.py            # uses ~/mimic4_study by default
    CAS_BASE_DIR=/path python rebuild_features.py

The existing features file is backed up to features_xgboost.csv.bak.
"""
import os
import shutil
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.expanduser(os.environ.get("CAS_BASE_DIR", "~/mimic4_study"))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

cohort_path = os.path.join(PROCESSED_DIR, "cohort_final.csv")
hourly_path = os.path.join(PROCESSED_DIR, "hourly_series.csv.gz")
features_path = os.path.join(PROCESSED_DIR, "features_xgboost.csv")
backup_path = features_path + ".bak"

for p in [cohort_path, hourly_path]:
    if not os.path.exists(p):
        sys.exit(f"ERROR: required cache missing: {p}\nCannot rebuild without it.")

print(f"Loading cohort: {cohort_path}")
cohort = pd.read_csv(cohort_path)
print(f"  {len(cohort)} stays")

print(f"Loading hourly grid: {hourly_path}")
hourly_full = pd.read_csv(hourly_path, compression="gzip")
print(f"  {len(hourly_full)} rows, {len(hourly_full.columns)} columns")

if "gcs_total" not in hourly_full.columns:
    sys.exit("ERROR: hourly_series.csv.gz does NOT contain gcs_total. "
             "Re-run the notebook from Cell 1 with the patched extraction.")

vital_cols = [c for c in hourly_full.columns if c not in {"stay_id", "hour"}]
print(f"Vital columns to feature-engineer: {vital_cols}")

feature_rows = []
for stay_id, group in tqdm(hourly_full.groupby("stay_id"), desc="Computing features"):
    row = {"stay_id": stay_id}
    for vital in vital_cols:
        vals = group[vital].dropna()
        if len(vals) == 0:
            continue
        row[f"{vital}_mean"] = vals.mean()
        row[f"{vital}_std"] = vals.std() if len(vals) > 1 else 0
        row[f"{vital}_min"] = vals.min()
        row[f"{vital}_max"] = vals.max()
        row[f"{vital}_first"] = vals.iloc[0]
        row[f"{vital}_last"] = vals.iloc[-1]
        row[f"{vital}_range"] = vals.max() - vals.min()
        row[f"{vital}_cv"] = (vals.std() / vals.mean()) if vals.mean() != 0 else 0
        if len(vals) >= 2:
            row[f"{vital}_trend"] = np.polyfit(np.arange(len(vals)), vals.values, 1)[0]
        else:
            row[f"{vital}_trend"] = 0.0
    feature_rows.append(row)

features = pd.DataFrame(feature_rows)
features = features.merge(
    cohort[["stay_id", "age", "gender", "in_hospital_mortality"]], on="stay_id"
)
features["gender_binary"] = (features["gender"] == "M").astype(int)

print(f"\nNew features matrix: {features.shape[0]} patients x {features.shape[1]} columns")
gcs_cols = [c for c in features.columns if "gcs" in c.lower()]
print(f"GCS columns ({len(gcs_cols)}): "
      f"{[c for c in gcs_cols if c.startswith('gcs_total_')]}  (and 27 component cols)")

if os.path.exists(features_path):
    shutil.copy2(features_path, backup_path)
    print(f"\nBacked up old features file to: {backup_path}")

features.to_csv(features_path, index=False)
print(f"Saved rebuilt features to: {features_path}")
print("\nDone. Reopen the notebook, restart the kernel, and Run All.")
