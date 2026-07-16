import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


FEATURES = [
    "CPCB_PM25", "CPCB_PM10", "CPCB_NO2_surface", "CPCB_SO2",
    "CPCB_CO_surface", "CPCB_O3",
    "TROPOMI_CO_mol_m2", "TROPOMI_HCHO_mol_m2", "TROPOMI_NO2_mol_m2",
    "temp_c", "dewpoint_c", "wind_speed_ms",
    "pressure_hpa", "precip_mm", "rel_humidity_pct",
    "insat_aod", "latitude", "longitude",
]
TARGET = "CPCB_AQI"

# temporal block split — no data leakage across seasons
TRAIN_END  = "2024-08-31"
VAL_START  = "2024-09-01"
VAL_END    = "2024-10-31"
TEST_START = "2024-11-01"


class AQIWindowDataset(Dataset):
    def __init__(self, df, split="train", seq_len=4, norm_stats=None):
        self.seq_len = seq_len
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        if split == "train":
            df = df[df["date"] <= pd.Timestamp(TRAIN_END)]
        elif split == "val":
            df = df[(df["date"] >= pd.Timestamp(VAL_START)) &
                    (df["date"] <= pd.Timestamp(VAL_END))]
        elif split == "test":
            df = df[df["date"] >= pd.Timestamp(TEST_START)]
        else:
            raise ValueError(f"unknown split: {split}")

        # build (N, seq_len, n_features) from lag columns
        steps = []
        for lag in range(seq_len):
            if lag == 0:
                cols = [c for c in FEATURES if c in df.columns]
            else:
                cols = [f"{c}_lag{lag}" for c in FEATURES if f"{c}_lag{lag}" in df.columns]
            steps.append(df[cols].values.astype(np.float32))

        X = np.stack(steps, axis=1)  # (N, T, F)
        y = df[TARGET].values.astype(np.float32)

        # normalise — use training stats if provided
        n_f = X.shape[2]
        if norm_stats is None:
            flat = X.reshape(-1, n_f)
            self._mean = flat.mean(axis=0)
            self._std = flat.std(axis=0) + 1e-8
        else:
            self._mean = norm_stats["mean"]
            self._std = norm_stats["std"]

        X = (X - self._mean) / self._std
        self.X = torch.from_numpy(X)
        self.y = torch.from_numpy(y)

    @property
    def norm_stats(self):
        return {"mean": self._mean, "std": self._std}

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def load_splits(features_path="data/features/aqi_features_lags.csv", seq_len=4):
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"not found: {features_path}")

    df = pd.read_csv(features_path)
    print(f"Loaded {df.shape[0]} rows, {df['City'].nunique()} cities")

    train_ds = AQIWindowDataset(df, "train", seq_len)
    val_ds   = AQIWindowDataset(df, "val",   seq_len, train_ds.norm_stats)
    test_ds  = AQIWindowDataset(df, "test",  seq_len, train_ds.norm_stats)
    print(f"train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")
    return train_ds, val_ds, test_ds


if __name__ == "__main__":
    train_ds, val_ds, test_ds = load_splits()
    x, y = train_ds[0]
    print(f"sample x: {x.shape}, y: {y.item():.1f}")
