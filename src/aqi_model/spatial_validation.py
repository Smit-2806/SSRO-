import os
import sys
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset import FEATURES, TARGET, AQIWindowDataset
from model import build_model, count_parameters
from train import compute_metrics, evaluate

CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Hyderabad"]

def main():
    print("=== Running Leave-One-City-Out (LOCO) Spatial Validation ===")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    features_path = "data/features/aqi_features_lags.csv"
    if not os.path.exists(features_path):
        print(f"[Error] Features file not found: {features_path}")
        return
        
    df = pd.read_csv(features_path)
    df["date"] = pd.to_datetime(df["date"])
    
    loco_results = []
    
    for holdout_city in CITIES:
        print(f"\nHoldout City: {holdout_city}")
        
        # split data by city
        train_df = df[df["City"] != holdout_city].copy()
        test_df  = df[df["City"] == holdout_city].copy()
        
        # custom datasets without time boundary constraints (using all dates)
        def create_loco_dataset(sub_df, norm_stats=None):
            steps = []
            for lag in range(4):
                cols = FEATURES if lag == 0 else [f"{c}_lag{lag}" for c in FEATURES]
                cols = [c for c in cols if c in sub_df.columns]
                steps.append(sub_df[cols].values.astype(np.float32))
            X = np.stack(steps, axis=1)
            y = sub_df[TARGET].values.astype(np.float32)
            
            n_f = X.shape[2]
            if norm_stats is None:
                flat = X.reshape(-1, n_f)
                mean = flat.mean(axis=0)
                std = flat.std(axis=0) + 1e-8
                
                # Z-score target scaling statistics
                y_mean = y.mean()
                y_std = y.std() + 1e-8
                
                norm_stats = {
                    "mean": mean, 
                    "std": std,
                    "y_mean": y_mean,
                    "y_std": y_std
                }
            
            X = (X - norm_stats["mean"]) / norm_stats["std"]
            
            # Normalise y using target scaling stats
            y_norm = (y - norm_stats["y_mean"]) / norm_stats["y_std"]
            
            class SimpleDataset(Dataset):
                def __init__(self, X_t, y_t):
                    self.X = torch.from_numpy(X_t)
                    self.y = torch.from_numpy(y_t)
                def __len__(self): return len(self.y)
                def __getitem__(self, idx): return self.X[idx], self.y[idx]
                
            return SimpleDataset(X, y_norm), norm_stats
            
        train_ds, norm_stats = create_loco_dataset(train_df)
        test_ds, _ = create_loco_dataset(test_df, norm_stats)
        
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
        test_loader  = DataLoader(test_ds, batch_size=32)
        
        # init model
        model = build_model(n_features=train_ds.X.shape[2]).to(device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        
        # fast training: 20 epochs for validation test
        for epoch in range(20):
            model.train()
            for X, y in train_loader:
                X, y = X.to(device), y.to(device)
                optimizer.zero_grad()
                loss = criterion(model(X), y)
                loss.backward()
                optimizer.step()
                
        # evaluate and denormalise
        _, preds_norm, trues_norm = evaluate(model, test_loader, criterion, device)
        
        preds = preds_norm * norm_stats["y_std"] + norm_stats["y_mean"]
        trues = trues_norm * norm_stats["y_std"] + norm_stats["y_mean"]
        
        m = compute_metrics(trues, preds)
        print(f"  Holdout {holdout_city} Results: RMSE: {m['rmse']:.2f} | R2: {m['r2']:.4f}")
        loco_results.append({"holdout_city": holdout_city, **m})
        
    os.makedirs("metrics", exist_ok=True)
    df_loco = pd.DataFrame(loco_results)
    df_loco.to_csv("metrics/loco_validation_results.csv", index=False)
    print("\nLOCO validation results saved to metrics/loco_validation_results.csv")

if __name__ == "__main__":
    main()
