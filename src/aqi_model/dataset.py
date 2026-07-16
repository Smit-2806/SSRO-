"""
dataset.py — Sliding Window Dataset Loader for the SSRO AQI Estimation Model

Loads aqi_features_lags.csv and returns (X, y) tensors for CNN-LSTM training.
Input shape:  (N, seq_len=4, n_features=18)
Target shape: (N,) — continuous CPCB_AQI values

Design decisions:
  - seq_len = 4 because we use t, t-1, t-2, t-3 (current + 3 lags)
  - Features are normalised per-city using training-set statistics to prevent
    data leakage. Validation/test splits use ONLY the training μ/σ.
  - Temporal block splits are enforced: train Jan–Aug, val Sep–Oct, test Nov–Dec.
    This avoids temporal autocorrelation leakage (r=0.914 in Delhi).
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


# ---------------------------------------------------------------------------
# Feature columns used by the model (18 base features × 4 time steps = input)
# ---------------------------------------------------------------------------
BASE_FEATURES = [
    "CPCB_PM25", "CPCB_PM10", "CPCB_NO2_surface", "CPCB_SO2",
    "CPCB_CO_surface", "CPCB_O3",
    "TROPOMI_CO_mol_m2", "TROPOMI_HCHO_mol_m2", "TROPOMI_NO2_mol_m2",
    "temp_c", "dewpoint_c", "wind_speed_ms",
    "pressure_hpa", "precip_mm", "rel_humidity_pct",
    "insat_aod",
    "latitude", "longitude",
]
TARGET_COL = "CPCB_AQI"

# Temporal block split boundaries (2024 data)
TRAIN_END  = "2024-08-31"
VAL_START  = "2024-09-01"
VAL_END    = "2024-10-31"
TEST_START = "2024-11-01"
TEST_END   = "2024-12-31"


class AQIWindowDataset(Dataset):
    """
    Sliding window dataset for CNN-LSTM AQI estimation.

    Each sample is a (seq_len, n_features) tensor representing
    days [t-3, t-2, t-1, t] for a single city.
    Target is the CPCB_AQI on day t.

    Args:
        df          : DataFrame with lag features (from aqi_features_lags.csv)
        split       : 'train', 'val', or 'test'
        seq_len     : window length (default 4 = current + 3 lags)
        norm_stats  : dict with 'mean' and 'std' (computed on train split only)
    """

    def __init__(self, df: pd.DataFrame, split: str = "train",
                 seq_len: int = 4, norm_stats: dict = None):
        self.seq_len = seq_len
        self.split = split

        # Apply temporal block split
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        if split == "train":
            df = df[df["date"] <= pd.Timestamp(TRAIN_END)]
        elif split == "val":
            df = df[(df["date"] >= pd.Timestamp(VAL_START)) &
                    (df["date"] <= pd.Timestamp(VAL_END))]
        elif split == "test":
            df = df[(df["date"] >= pd.Timestamp(TEST_START)) &
                    (df["date"] <= pd.Timestamp(TEST_END))]
        else:
            raise ValueError(f"split must be 'train', 'val', or 'test', got '{split}'")

        # Build lag feature matrix (seq_len × n_features per sample)
        # Column pattern: base col at lag-0, then {col}_lag1, {col}_lag2, {col}_lag3
        lag_cols_ordered = []
        for lag in range(seq_len):
            if lag == 0:
                lag_cols_ordered.append([c for c in BASE_FEATURES if c in df.columns])
            else:
                lag_cols_ordered.append([f"{c}_lag{lag}" for c in BASE_FEATURES
                                         if f"{c}_lag{lag}" in df.columns])

        # Flatten: X is (N, seq_len, n_features)
        X_list = []
        for step_cols in lag_cols_ordered:
            step_data = df[step_cols].values.astype(np.float32)
            X_list.append(step_data)

        # Stack along axis 1: shape (N, seq_len, n_features)
        X = np.stack(X_list, axis=1)

        # Target
        y = df[TARGET_COL].values.astype(np.float32)

        # Normalise using training statistics
        n_feat = X.shape[2]
        if norm_stats is None:
            # Compute from this split (only call on train!)
            X_flat = X.reshape(-1, n_feat)
            self._mean = X_flat.mean(axis=0)
            self._std  = X_flat.std(axis=0) + 1e-8
        else:
            self._mean = norm_stats["mean"]
            self._std  = norm_stats["std"]

        X = (X - self._mean) / self._std

        self.X = torch.from_numpy(X)          # (N, seq_len, n_features)
        self.y = torch.from_numpy(y)          # (N,)
        self.dates  = df["date"].values
        self.cities = df["City"].values if "City" in df.columns else None

    @property
    def norm_stats(self):
        return {"mean": self._mean, "std": self._std}

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def load_splits(features_path: str = "data/features/aqi_features_lags.csv",
                seq_len: int = 4):
    """
    Convenience function: load train/val/test splits from a single CSV.
    Returns (train_ds, val_ds, test_ds) with shared normalisation.

    Usage:
        train_ds, val_ds, test_ds = load_splits()
        loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")

    df = pd.read_csv(features_path)
    print(f"Loaded features: {df.shape} | Cities: {df['City'].nunique() if 'City' in df.columns else 'unknown'}")

    train_ds = AQIWindowDataset(df, split="train", seq_len=seq_len)
    val_ds   = AQIWindowDataset(df, split="val",   seq_len=seq_len,
                                norm_stats=train_ds.norm_stats)
    test_ds  = AQIWindowDataset(df, split="test",  seq_len=seq_len,
                                norm_stats=train_ds.norm_stats)

    print(f"  Train: {len(train_ds):,} samples | Val: {len(val_ds):,} | Test: {len(test_ds):,}")
    return train_ds, val_ds, test_ds


if __name__ == "__main__":
    train_ds, val_ds, test_ds = load_splits()
    x, y = train_ds[0]
    print(f"\nSample X shape : {x.shape}   (seq_len × n_features)")
    print(f"Sample y value : {y.item():.1f} (CPCB AQI)")
    print(f"Norm mean[:3]  : {train_ds.norm_stats['mean'][:3]}")
