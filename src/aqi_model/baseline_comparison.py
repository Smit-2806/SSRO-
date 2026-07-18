import os
import sys
import json
import pandas as pd
import numpy as np

# setup paths to import from aqi_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor

from dataset import load_splits
from train import compute_metrics

def flatten_data(ds):
    # flattens (N, seq_len, n_features) to (N, seq_len * n_features)
    X = ds.X.numpy()
    y = ds.y.numpy()
    N, T, F = X.shape
    return X.reshape(N, T * F), y

def main():
    print("=== Training Baseline Models ===")
    
    # load splits
    train_ds, val_ds, test_ds = load_splits()
    X_train, y_train = flatten_data(train_ds)
    X_val, y_val = flatten_data(val_ds)
    X_test, y_test = flatten_data(test_ds)
    
    # define baselines
    models = {
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "MLP Regressor": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42)
    }
    
    results = []
    
    # train and evaluate each model
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        
        # evaluate on test set
        preds = model.predict(X_test)
        m = compute_metrics(y_test, preds)
        
        print(f"  Test RMSE: {m['rmse']:.2f} | R2: {m['r2']:.4f}")
        results.append({"model": name, **m})
        
    # save baseline results
    os.makedirs("metrics", exist_ok=True)
    df_results = pd.DataFrame(results)
    df_results.to_csv("metrics/model_arena_comparison.csv", index=False)
    print("\nBaseline comparison saved to metrics/model_arena_comparison.csv")

if __name__ == "__main__":
    main()
