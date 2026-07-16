import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build_model
from dataset import FEATURES

# CPCB India AQI categories
AQI_CATEGORIES = [
    (0,   50,  "Good"),
    (51,  100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 500, "Severe"),
]


def get_category(aqi):
    for lo, hi, label in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label
    return "Out of Range"


def load_model(model_path="models/aqi_cnn_lstm_best.pth"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No checkpoint at {model_path} — run train.py first.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
    model.eval()
    norm_mean = np.array(ckpt["norm_stats"]["mean"])
    norm_std  = np.array(ckpt["norm_stats"]["std"])
    return model, norm_mean, norm_std, ckpt["config"], device


def predict(city, date, features_path="data/features/aqi_features_lags.csv",
            model_path="models/aqi_cnn_lstm_best.pth"):
    model, mean, std, config, device = load_model(model_path)
    seq_len = config["seq_len"]

    df = pd.read_csv(features_path)
    df["date"] = pd.to_datetime(df["date"])
    row = df[(df["City"] == city) & (df["date"] == pd.Timestamp(date))]

    if row.empty:
        raise ValueError(f"No data for {city} on {date}")

    steps = []
    for lag in range(seq_len):
        cols = FEATURES if lag == 0 else [f"{c}_lag{lag}" for c in FEATURES]
        cols = [c for c in cols if c in row.columns]
        steps.append(row[cols].values[0])
    X = np.stack(steps, axis=0).astype(np.float32)
    X = (X - mean) / std

    with torch.no_grad():
        aqi = model(torch.from_numpy(X).unsqueeze(0).to(device)).item()

    aqi = max(0.0, min(500.0, aqi))
    return {"city": city, "date": date, "aqi": round(aqi, 1), "category": get_category(aqi)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Delhi")
    parser.add_argument("--date", default="2024-11-15")
    parser.add_argument("--model", default="models/aqi_cnn_lstm_best.pth")
    parser.add_argument("--data",  default="data/features/aqi_features_lags.csv")
    args = parser.parse_args()

    try:
        result = predict(args.city, args.date, args.data, args.model)
        print(f"\n{result['city']}  {result['date']}")
        print(f"AQI: {result['aqi']}  ({result['category']})")
    except Exception as e:
        print(f"Error: {e}")
