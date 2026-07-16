"""
train.py — Training Loop, Evaluation & Checkpoint Management

Usage:
    python src/aqi_model/train.py

Outputs:
    models/aqi_cnn_lstm_best.pth      — best validation checkpoint
    metrics/training_metrics.csv      — epoch-wise loss and metrics
    metrics/evaluation_report.json    — final test set evaluation
"""

import os
import sys
import json
import math
import random
import numpy as np
import pandas as pd

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from dataset import load_splits, BASE_FEATURES
from model   import build_model, count_parameters

# ── Reproducibility ───────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ── Hyperparameters ───────────────────────────────────────────────────────────
CONFIG = {
    "seq_len":       4,
    "batch_size":    32,
    "lr":            1e-3,
    "weight_decay":  1e-4,
    "epochs":        80,
    "patience":      12,          # early stopping patience
    "cnn_channels":  32,
    "lstm_hidden":   128,
    "lstm_layers":   2,
    "dropout":       0.3,
    "grad_clip":     1.0,
    "features_path": "data/features/aqi_features_lags.csv",
    "model_dir":     "models",
    "metrics_dir":   "metrics",
    "model_name":    "aqi_cnn_lstm_best.pth",
}


# ── Metrics ───────────────────────────────────────────────────────────────────
def rmse(y_true, y_pred):
    return math.sqrt(((y_true - y_pred) ** 2).mean())

def mae(y_true, y_pred):
    return (abs(y_true - y_pred)).mean()

def r2(y_true, y_pred):
    ss_res = ((y_true - y_pred) ** 2).sum()
    ss_tot = ((y_true - y_true.mean()) ** 2).sum()
    return 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

def pearson_r(y_true, y_pred):
    y_true_c = y_true - y_true.mean()
    y_pred_c = y_pred - y_pred.mean()
    denom = (y_true_c ** 2).sum() ** 0.5 * (y_pred_c ** 2).sum() ** 0.5
    return (y_true_c * y_pred_c).sum() / denom if denom > 0 else 0.0


# ── Evaluation helper ─────────────────────────────────────────────────────────
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_pred, all_true = [], []
    with torch.no_grad():
        for X, y in loader:
            X, y = X.to(device), y.to(device)
            pred = model(X)
            total_loss += criterion(pred, y).item() * len(y)
            all_pred.append(pred.cpu().numpy())
            all_true.append(y.cpu().numpy())
    all_pred = np.concatenate(all_pred)
    all_true = np.concatenate(all_true)
    avg_loss = total_loss / len(loader.dataset)
    return avg_loss, all_pred, all_true


# ── Main training function ────────────────────────────────────────────────────
def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"  SSRO AQI CNN-LSTM + Attention Training")
    print(f"  Device: {device} | Seed: {SEED}")
    print(f"{'='*60}\n")

    # 1. Load data
    try:
        train_ds, val_ds, test_ds = load_splits(
            features_path=CONFIG["features_path"],
            seq_len=CONFIG["seq_len"]
        )
    except FileNotFoundError as e:
        print(f"[Error] {e}")
        print("  Run src/data_pipeline/data_transformation.py first to generate lag features.")
        return

    n_features = train_ds.X.shape[2]
    print(f"Features per timestep : {n_features}")
    print(f"Train / Val / Test    : {len(train_ds)} / {len(val_ds)} / {len(test_ds)}\n")

    train_loader = DataLoader(train_ds, batch_size=CONFIG["batch_size"], shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=CONFIG["batch_size"], shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=CONFIG["batch_size"], shuffle=False, num_workers=0)

    # 2. Build model
    model = build_model(
        n_features   = n_features,
        seq_len      = CONFIG["seq_len"],
        cnn_channels = CONFIG["cnn_channels"],
        lstm_hidden  = CONFIG["lstm_hidden"],
        lstm_layers  = CONFIG["lstm_layers"],
        dropout      = CONFIG["dropout"],
    ).to(device)
    print(f"Model parameters: {count_parameters(model):,}\n")

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=CONFIG["lr"], weight_decay=CONFIG["weight_decay"]
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5, verbose=True
    )

    # 3. Create output directories
    os.makedirs(CONFIG["model_dir"],   exist_ok=True)
    os.makedirs(CONFIG["metrics_dir"], exist_ok=True)
    model_path = os.path.join(CONFIG["model_dir"], CONFIG["model_name"])

    # 4. Training loop with early stopping
    best_val_loss = float("inf")
    patience_counter = 0
    history = []

    print(f"{'Epoch':>5} {'Train Loss':>12} {'Val Loss':>10} {'Val RMSE':>10} {'Val R²':>8}")
    print("-" * 55)

    for epoch in range(1, CONFIG["epochs"] + 1):
        # ── Train ──
        model.train()
        train_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(X)
            loss = criterion(pred, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), CONFIG["grad_clip"])
            optimizer.step()
            train_loss += loss.item() * len(y)
        train_loss /= len(train_ds)

        # ── Validate ──
        val_loss, val_pred, val_true = evaluate(model, val_loader, criterion, device)
        val_rmse = rmse(val_true, val_pred)
        val_r2   = r2(val_true, val_pred)
        val_r    = pearson_r(val_true, val_pred)

        scheduler.step(val_loss)

        history.append({
            "epoch": epoch, "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4), "val_rmse": round(val_rmse, 2),
            "val_r2": round(val_r2, 4), "val_pearson_r": round(float(val_r), 4),
        })
        print(f"{epoch:>5} {train_loss:>12.2f} {val_loss:>10.2f} {val_rmse:>10.2f} {val_r2:>8.4f}")

        # ── Checkpoint ──
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save({
                "epoch":       epoch,
                "model_state": model.state_dict(),
                "optimizer":   optimizer.state_dict(),
                "val_loss":    val_loss,
                "val_rmse":    val_rmse,
                "val_r2":      val_r2,
                "config":      CONFIG,
                "norm_stats":  {k: v.tolist() for k, v in train_ds.norm_stats.items()},
                "n_features":  n_features,
            }, model_path)
            print(f"         ✓ Saved best model (val_loss={val_loss:.2f})")
        else:
            patience_counter += 1
            if patience_counter >= CONFIG["patience"]:
                print(f"\n  Early stopping at epoch {epoch} (patience={CONFIG['patience']})")
                break

    # 5. Save training history
    history_path = os.path.join(CONFIG["metrics_dir"], "training_metrics.csv")
    pd.DataFrame(history).to_csv(history_path, index=False)
    print(f"\nTraining history saved → {history_path}")

    # 6. Final test evaluation (load best model)
    print(f"\n{'='*60}")
    print(f"  FINAL TEST EVALUATION (holdout: Nov–Dec 2024)")
    print(f"{'='*60}")

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state"])

    _, test_pred, test_true = evaluate(model, test_loader, criterion, device)
    test_results = {
        "split":           "test (Nov-Dec 2024)",
        "n_samples":       int(len(test_true)),
        "rmse":            round(rmse(test_true, test_pred), 2),
        "mae":             round(mae(test_true, test_pred), 2),
        "r2":              round(r2(test_true, test_pred), 4),
        "pearson_r":       round(float(pearson_r(test_true, test_pred)), 4),
        "best_val_rmse":   round(checkpoint["val_rmse"], 2),
        "best_epoch":      checkpoint["epoch"],
        "config":          CONFIG,
    }

    print(f"  RMSE        : {test_results['rmse']}")
    print(f"  MAE         : {test_results['mae']}")
    print(f"  R²          : {test_results['r2']}")
    print(f"  Pearson r   : {test_results['pearson_r']}")
    print(f"  Best epoch  : {test_results['best_epoch']}")

    report_path = os.path.join(CONFIG["metrics_dir"], "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\nEvaluation report saved → {report_path}")
    print(f"Best model checkpoint → {model_path}")
    print(f"\n{'='*60}")
    print("  Training complete.")
    print(f"{'='*60}\n")

    return test_results


if __name__ == "__main__":
    train()
