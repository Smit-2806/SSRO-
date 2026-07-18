import os
import sys
import json
import pandas as pd
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset import load_splits, FEATURES
from model import build_model
from train import evaluate

def calculate_permutation_importance(model, dataset, base_loss, device):
    # calculates feature importance by permuting each feature column on the test set
    model.eval()
    X = dataset.X.clone()
    y = dataset.y.clone().to(device)
    
    n_features = X.shape[2]
    importances = {}
    
    criterion = torch.nn.MSELoss()
    
    for f_idx in range(n_features):
        X_perm = X.clone()
        # shuffle this feature across all samples (both batch and sequence length to disrupt it)
        perm = torch.randperm(X_perm.shape[0])
        for t in range(X_perm.shape[1]):
            X_perm[:, t, f_idx] = X_perm[perm, t, f_idx]
            
        with torch.no_grad():
            out = model(X_perm.to(device))
            loss = criterion(out, y).item()
            
        # importance = permuted loss - base baseline loss
        importances[FEATURES[f_idx]] = max(0.0, loss - base_loss)
        
    return importances

def analyze_attention_weights(model, dataset, device):
    # reconstructs the temporal attention weights for the dataset
    model.eval()
    X = dataset.X.to(device)
    
    with torch.no_grad():
        # run cnn
        cnn_out = model.cnn(X)
        # run lstm
        lstm_out, _ = model.lstm(cnn_out)
        # get attention weights
        scores = model.attention.attn(lstm_out).squeeze(-1)
        weights = torch.nn.functional.softmax(scores, dim=1).cpu().numpy()
        
    # calculate average weights per lag step (0: current day, 1: 1-day lag, etc.)
    avg_weights = weights.mean(axis=0)
    
    # compare high-wind vs low-wind attention to see meteorological influence
    wind_idx = FEATURES.index("wind_speed_ms")
    wind_speeds = X[:, 0, wind_idx].cpu().numpy()
    high_wind_mask = wind_speeds > np.percentile(wind_speeds, 75)
    low_wind_mask = wind_speeds < np.percentile(wind_speeds, 25)
    
    high_wind_attn = weights[high_wind_mask].mean(axis=0)
    low_wind_attn = weights[low_wind_mask].mean(axis=0)
    
    return {
        "overall_temporal_attention": {f"lag_{i}": float(avg_weights[i]) for i in range(4)},
        "high_wind_temporal_attention": {f"lag_{i}": float(high_wind_attn[i]) for i in range(4)},
        "low_wind_temporal_attention": {f"lag_{i}": float(low_wind_attn[i]) for i in range(4)}
    }

def main():
    print("=== Model Explainability & Uncertainty Analysis ===")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = "models/aqi_cnn_lstm_best.pth"
    if not os.path.exists(model_path):
        print(f"[Error] Checkpoint not found: {model_path}")
        return
        
    ckpt = torch.load(model_path, map_location=device)
    model = build_model(
        n_features=ckpt["n_features"],
        seq_len=ckpt["config"]["seq_len"],
        cnn_channels=ckpt["config"]["cnn_channels"],
        lstm_hidden=ckpt["config"]["lstm_hidden"],
        lstm_layers=ckpt["config"]["lstm_layers"],
        dropout=0.0
    ).to(device)
    model.load_state_dict(ckpt["model_state"])
    
    # load datasets
    train_ds, val_ds, test_ds = load_splits()
    
    # base loss on test dataset
    criterion = torch.nn.MSELoss()
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=32)
    test_loss, preds, trues = evaluate(model, test_loader, criterion, device)
    
    # 1. Feature permutation importance
    print("Calculating feature importance...")
    importances = calculate_permutation_importance(model, test_ds, test_loss, device)
    
    # sort by importance
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    
    # 2. Attention weight analysis
    print("Analysing temporal attention weights...")
    attn_analysis = analyze_attention_weights(model, test_ds, device)
    
    # 3. Confidence/Uncertainty indicators
    # compute residuals on the validation split
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=32)
    _, val_preds, val_trues = evaluate(model, val_loader, criterion, device)
    residuals = val_preds - val_trues
    val_mae = abs(residuals).mean()
    val_std = residuals.std()
    
    # prediction interval = +/- 1.96 * std (representing 95% confidence interval)
    conf_interval_95 = 1.96 * val_std
    
    # compile report
    report = {
        "val_residuals_mean": float(residuals.mean()),
        "val_residuals_std": float(val_std),
        "val_mae": float(val_mae),
        "prediction_95_confidence_interval_margin": float(conf_interval_95),
        "feature_permutation_importance": {k: float(v) for k, v in sorted_importances},
        **attn_analysis
    }
    
    os.makedirs("metrics", exist_ok=True)
    report_path = "metrics/explainability_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\nExplainability & uncertainty report saved → {report_path}")
    print("\nTop 5 Important Features:")
    for k, v in sorted_importances[:5]:
        print(f"  {k:<20} : {v:.4f}")
        
    print("\nAttention Weight Profiles:")
    print("  Overall   : " + ", ".join([f"Lag-{i}: {attn_analysis['overall_temporal_attention'][f'lag_{i}']:.3f}" for i in range(4)]))
    print("  High Wind : " + ", ".join([f"Lag-{i}: {attn_analysis['high_wind_temporal_attention'][f'lag_{i}']:.3f}" for i in range(4)]))
    print("  Low Wind  : " + ", ".join([f"Lag-{i}: {attn_analysis['low_wind_temporal_attention'][f'lag_{i}']:.3f}" for i in range(4)]))

if __name__ == "__main__":
    main()
