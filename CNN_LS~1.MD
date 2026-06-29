# CNN-LSTM Model (PyTorch) — Objective 1

## Architecture Overview

The CNN-LSTM hybrid works by:
1. **CNN block**: 1D convolutions along the time axis to extract local temporal patterns
2. **LSTM block**: Captures long-range sequential dependencies across the window
3. **FC head**: Maps LSTM hidden state → pollutant concentration prediction

This is well-suited for satellite time-series because the CNN can learn multi-scale temporal
features (e.g., diurnal cycles) while the LSTM handles week-to-week trends.

---

## Model Architecture

```python
# models/cnn_lstm.py
import torch
import torch.nn as nn
from typing import Optional

class CNNLSTMModel(nn.Module):
    """
    CNN-LSTM for surface pollutant concentration prediction from
    satellite columnar data + meteorological features.

    Input shape:  (batch, seq_len, n_features)
    Output shape: (batch, 1)  — single pollutant or AQI sub-index
    """

    def __init__(
        self,
        n_features: int,
        seq_len: int = 7,
        cnn_channels: list[int] = [64, 128],
        cnn_kernel: int = 3,
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
        dropout: float = 0.3,
        output_dim: int = 1,
    ):
        super().__init__()

        # --- CNN block (operates on feature dim, conv over time) ---
        cnn_layers = []
        in_ch = n_features
        for out_ch in cnn_channels:
            cnn_layers += [
                nn.Conv1d(in_ch, out_ch, kernel_size=cnn_kernel, padding=cnn_kernel // 2),
                nn.BatchNorm1d(out_ch),
                nn.ReLU(),
                nn.Dropout(dropout),
            ]
            in_ch = out_ch
        self.cnn = nn.Sequential(*cnn_layers)

        # --- LSTM block ---
        self.lstm = nn.LSTM(
            input_size=cnn_channels[-1],
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0,
            bidirectional=False,
        )

        # --- Attention (optional but improves performance) ---
        self.attn = nn.Linear(lstm_hidden, 1)

        # --- Fully connected head ---
        self.head = nn.Sequential(
            nn.Linear(lstm_hidden, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F)
        # CNN expects (B, F, T)
        x_cnn = self.cnn(x.permute(0, 2, 1))   # → (B, C, T)
        x_lstm_in = x_cnn.permute(0, 2, 1)      # → (B, T, C)

        lstm_out, _ = self.lstm(x_lstm_in)       # → (B, T, H)

        # Attention-weighted pooling over time steps
        attn_w = torch.softmax(self.attn(lstm_out), dim=1)   # (B, T, 1)
        context = (attn_w * lstm_out).sum(dim=1)              # (B, H)

        return self.head(context)                             # (B, output_dim)


class MultiPollutantCNNLSTM(nn.Module):
    """
    Predict multiple pollutants simultaneously (PM2.5, NO2, SO2, CO, O3).
    Shares CNN-LSTM backbone, separate head per pollutant.
    """
    POLLUTANTS = ["PM2.5", "NO2", "SO2", "CO", "O3"]

    def __init__(self, n_features: int, seq_len: int = 7, **kwargs):
        super().__init__()
        self.backbone = CNNLSTMModel(
            n_features=n_features, seq_len=seq_len,
            output_dim=len(self.POLLUTANTS), **kwargs
        )

    def forward(self, x):
        # Returns dict of pollutant → predicted concentration
        out = self.backbone(x)   # (B, 5)
        return {p: out[:, i] for i, p in enumerate(self.POLLUTANTS)}
```

---

## Training Loop

```python
# models/train.py
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
from pathlib import Path

def train_model(
    X: np.ndarray,         # (N, seq_len, n_features)
    y: np.ndarray,         # (N,)
    model: nn.Module,
    epochs: int = 100,
    batch_size: int = 64,
    lr: float = 1e-3,
    val_split: float = 0.15,
    checkpoint_dir: str = "models/checkpoints",
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> dict:

    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    model = model.to(device)

    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)
    dataset = TensorDataset(X_t, y_t)

    n_val = int(len(dataset) * val_split)
    train_ds, val_ds = random_split(dataset, [len(dataset) - n_val, n_val])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size)

    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.HuberLoss(delta=1.0)   # robust to outlier stations

    history = {"train_loss": [], "val_loss": [], "val_rmse": []}
    best_val = float("inf")

    for epoch in range(1, epochs + 1):
        # --- train ---
        model.train()
        train_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_losses.append(loss.item())
        scheduler.step()

        # --- validate ---
        model.eval()
        val_losses, preds, trues = [], [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                val_losses.append(criterion(pred, yb).item())
                preds.append(pred.cpu().numpy())
                trues.append(yb.cpu().numpy())

        val_loss = np.mean(val_losses)
        preds_arr = np.concatenate(preds).ravel()
        trues_arr = np.concatenate(trues).ravel()
        val_rmse  = np.sqrt(np.mean((preds_arr - trues_arr) ** 2))

        history["train_loss"].append(np.mean(train_losses))
        history["val_loss"].append(val_loss)
        history["val_rmse"].append(val_rmse)

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), f"{checkpoint_dir}/best_model.pt")

        if epoch % 10 == 0:
            print(f"Epoch {epoch:4d} | train_loss={np.mean(train_losses):.4f} "
                  f"| val_loss={val_loss:.4f} | val_RMSE={val_rmse:.4f}")

    return history


def evaluate_model(model, X_test, y_test, scaler_y, device="cpu"):
    """Compute RMSE, MAE, R², MBE on held-out test set (original units)."""
    from sklearn.metrics import r2_score, mean_absolute_error
    model.eval()
    with torch.no_grad():
        X_t = torch.tensor(X_test, dtype=torch.float32).to(device)
        pred_scaled = model(X_t).cpu().numpy().ravel()

    pred = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).ravel()
    true = scaler_y.inverse_transform(y_test.reshape(-1, 1)).ravel()

    rmse = np.sqrt(np.mean((pred - true) ** 2))
    mae  = mean_absolute_error(true, pred)
    r2   = r2_score(true, pred)
    mbe  = np.mean(pred - true)

    print(f"RMSE: {rmse:.3f} | MAE: {mae:.3f} | R²: {r2:.3f} | MBE: {mbe:.3f}")
    return {"RMSE": rmse, "MAE": mae, "R2": r2, "MBE": mbe}
```

---

## AQI Computation (India NAAQs)

```python
# analysis/aqi_compute.py
import numpy as np
import pandas as pd

# Breakpoints: (C_lo, C_hi, I_lo, I_hi)
AQI_BREAKPOINTS = {
    "PM2.5": [(0,30,0,50),(31,60,51,100),(61,90,101,200),(91,120,201,300),(121,250,301,400),(251,500,401,500)],
    "PM10":  [(0,50,0,50),(51,100,51,100),(101,250,101,200),(251,350,201,300),(351,430,301,400),(431,600,401,500)],
    "NO2":   [(0,40,0,50),(41,80,51,100),(81,180,101,200),(181,280,201,300),(281,400,301,400),(401,600,401,500)],
    "SO2":   [(0,40,0,50),(41,80,51,100),(81,380,101,200),(381,800,201,300),(801,1600,301,400),(1601,2000,401,500)],
    "CO":    [(0,1,0,50),(1.1,2,51,100),(2.1,10,101,200),(10.1,17,201,300),(17.1,34,301,400),(34,50,401,500)],
    "O3":    [(0,50,0,50),(51,100,51,100),(101,168,101,200),(169,208,201,300),(209,748,301,400),(748,1000,401,500)],
}

def sub_index(C: float, breakpoints: list) -> float:
    """Compute sub-AQI for a single pollutant concentration."""
    if np.isnan(C):
        return np.nan
    for C_lo, C_hi, I_lo, I_hi in breakpoints:
        if C_lo <= C <= C_hi:
            return ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
    return 500.0  # beyond severe

def compute_aqi(row: pd.Series) -> float:
    """Compute overall AQI as max of available sub-indices."""
    indices = []
    for pollutant, bp in AQI_BREAKPOINTS.items():
        if pollutant in row and not np.isnan(row[pollutant]):
            indices.append(sub_index(row[pollutant], bp))
    return max(indices) if indices else np.nan

def aqi_category(aqi: float) -> str:
    thresholds = [(50,"Good"),(100,"Satisfactory"),(200,"Moderate"),
                  (300,"Poor"),(400,"Very Poor"),(500,"Severe")]
    for limit, label in thresholds:
        if aqi <= limit:
            return label
    return "Severe"
```

---

## Spatial AQI Mapping

```python
# viz/maps.py  (static cartopy map)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

AQI_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "aqi",
    [(0,"#00e400"),(50/500,"#ffff00"),(100/500,"#ff7e00"),
     (200/500,"#ff0000"),(300/500,"#8f3f97"),(400/500,"#7e0023"),(1,"#7e0023")]
)

def plot_aqi_map(lons, lats, aqi_grid, title="Surface AQI — India", out_path="aqi_map.png"):
    fig, ax = plt.subplots(figsize=(10, 10),
                           subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_extent([68, 97.5, 6.5, 37.5], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.BORDERS, linewidth=0.8)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.STATES, linewidth=0.4, alpha=0.5)

    im = ax.pcolormesh(lons, lats, aqi_grid, cmap=AQI_CMAP,
                       vmin=0, vmax=500, transform=ccrs.PlateCarree())
    plt.colorbar(im, ax=ax, orientation="vertical", label="AQI", shrink=0.7)
    ax.set_title(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")
```
