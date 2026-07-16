import os
import sys
import json
import math
import random
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from dataset import load_splits
from model import build_model, count_parameters

# fix seed for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

CONFIG = {
    "seq_len": 4,
    "batch_size": 32,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "epochs": 80,
    "patience": 12,          # stop if val loss doesn't improve for this many epochs
    "cnn_channels": 32,
    "lstm_hidden": 128,
    "lstm_layers": 2,
    "dropout": 0.3,
    "grad_clip": 1.0,        # prevents exploding gradients
    "features_path": "data/features/aqi_features_lags.csv",
    "model_dir": "models",
    "metrics_dir": "metrics",
}


def compute_metrics(y_true, y_pred):
    rmse = math.sqrt(((y_true - y_pred) ** 2).mean())
    mae = abs(y_true - y_pred).mean()
    ss_res = ((y_true - y_pred) ** 2).sum()
    ss_tot = ((y_true - y_true.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    yc = y_true - y_true.mean()
    pc = y_pred - y_pred.mean()
    denom = (yc**2).sum()**0.5 * (pc**2).sum()**0.5
    pearson = (yc * pc).sum() / denom if denom > 0 else 0.0
    return {"rmse": round(rmse, 2), "mae": round(float(mae), 2),
            "r2": round(float(r2), 4), "pearson_r": round(float(pearson), 4)}


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, preds, trues = 0.0, [], []
    with torch.no_grad():
        for X, y in loader:
            X, y = X.to(device), y.to(device)
            out = model(X)
            total_loss += criterion(out, y).item() * len(y)
            preds.append(out.cpu().numpy())
            trues.append(y.cpu().numpy())
    return (total_loss / len(loader.dataset),
            np.concatenate(preds), np.concatenate(trues))


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice: {device}")

    try:
        train_ds, val_ds, test_ds = load_splits(CONFIG["features_path"], CONFIG["seq_len"])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    n_features = train_ds.X.shape[2]

    train_loader = DataLoader(train_ds, batch_size=CONFIG["batch_size"], shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=CONFIG["batch_size"])
    test_loader  = DataLoader(test_ds,  batch_size=CONFIG["batch_size"])

    model = build_model(
        n_features=n_features,
        seq_len=CONFIG["seq_len"],
        cnn_channels=CONFIG["cnn_channels"],
        lstm_hidden=CONFIG["lstm_hidden"],
        lstm_layers=CONFIG["lstm_layers"],
        dropout=CONFIG["dropout"]
    ).to(device)

    print(f"Parameters: {count_parameters(model):,}")

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=CONFIG["lr"],
                                  weight_decay=CONFIG["weight_decay"])
    # halve lr if val loss plateaus for 5 epochs
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5, verbose=True
    )

    os.makedirs(CONFIG["model_dir"], exist_ok=True)
    os.makedirs(CONFIG["metrics_dir"], exist_ok=True)
    model_path = os.path.join(CONFIG["model_dir"], "aqi_cnn_lstm_best.pth")

    best_val_loss = float("inf")
    patience_ctr = 0
    history = []

    print(f"\n{'Epoch':>5}  {'Train':>10}  {'Val':>10}  {'RMSE':>8}  {'R2':>8}")
    print("-" * 50)

    for epoch in range(1, CONFIG["epochs"] + 1):
        model.train()
        train_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(X), y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), CONFIG["grad_clip"])
            optimizer.step()
            train_loss += loss.item() * len(y)
        train_loss /= len(train_ds)

        val_loss, val_pred, val_true = evaluate(model, val_loader, criterion, device)
        m = compute_metrics(val_true, val_pred)
        scheduler.step(val_loss)

        history.append({"epoch": epoch, "train_loss": round(train_loss, 4),
                         "val_loss": round(val_loss, 4), **m})
        print(f"{epoch:>5}  {train_loss:>10.2f}  {val_loss:>10.2f}  {m['rmse']:>8.2f}  {m['r2']:>8.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_ctr = 0
            # save full checkpoint so we can resume inference later
            torch.save({
                "epoch": epoch,
                "model_state": model.state_dict(),
                "val_loss": val_loss,
                "metrics": m,
                "config": CONFIG,
                "norm_stats": {k: v.tolist() for k, v in train_ds.norm_stats.items()},
                "n_features": n_features,
            }, model_path)
            print(f"         -> saved (val_loss={val_loss:.2f})")
        else:
            patience_ctr += 1
            if patience_ctr >= CONFIG["patience"]:
                print(f"\nEarly stopping at epoch {epoch}")
                break

    pd.DataFrame(history).to_csv(
        os.path.join(CONFIG["metrics_dir"], "training_metrics.csv"), index=False
    )

    # load the best checkpoint and evaluate on the holdout test set
    ckpt = torch.load(model_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    _, test_pred, test_true = evaluate(model, test_loader, criterion, device)
    test_m = compute_metrics(test_true, test_pred)

    print(f"\nTest results (Nov-Dec 2024):")
    for k, v in test_m.items():
        print(f"  {k}: {v}")

    report = {"split": "test (Nov-Dec 2024)", "n_samples": len(test_true),
              "best_epoch": ckpt["epoch"], **test_m}
    with open(os.path.join(CONFIG["metrics_dir"], "evaluation_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nDone. Best model: {model_path}")
    return report


if __name__ == "__main__":
    train()
