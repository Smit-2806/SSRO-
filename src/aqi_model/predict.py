"""
predict.py — Inference script for trained AQI CNN-LSTM model

Usage:
    python src/aqi_model/predict.py --city Delhi --date 2024-11-15

Loads the best checkpoint and returns a predicted AQI value with
category label (Good / Satisfactory / Moderate / Poor / Very Poor / Severe).
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build_model

# ── AQI Category mapping (CPCB India standard) ────────────────────────────────
AQI_CATEGORIES = [
    (0,   50,  "Good",          "🟢"),
    (51,  100, "Satisfactory",  "🟡"),
    (101, 200, "Moderate",      "🟠"),
    (201, 300, "Poor",          "🔴"),
    (301, 400, "Very Poor",     "🟣"),
    (401, 500, "Severe",        "⚫"),
]

def get_aqi_category(aqi: float) -> tuple:
    for lo, hi, label, icon in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label, icon
    return "Out of Range", "❓"


def load_checkpoint(model_path: str = "models/aqi_cnn_lstm_best.pth",
                    device: torch.device = None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model checkpoint not found: {model_path}\n"
            "  Run: python src/aqi_model/train.py first."
        )
    ckpt = torch.load(model_path, map_location=device)
    model = build_model(
        n_features   = ckpt["n_features"],
        seq_len      = ckpt["config"]["seq_len"],
        cnn_channels = ckpt["config"]["cnn_channels"],
        lstm_hidden  = ckpt["config"]["lstm_hidden"],
        lstm_layers  = ckpt["config"]["lstm_layers"],
        dropout      = 0.0,   # no dropout at inference
    ).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    norm_mean = np.array(ckpt["norm_stats"]["mean"])
    norm_std  = np.array(ckpt["norm_stats"]["std"])
    return model, norm_mean, norm_std, ckpt["config"], device


def predict_from_features(features_row: np.ndarray,
                           model_path: str = "models/aqi_cnn_lstm_best.pth") -> dict:
    """
    Predict AQI from a (seq_len × n_features) numpy array.

    Args:
        features_row : np.ndarray of shape (seq_len, n_features)
        model_path   : path to the .pth checkpoint

    Returns:
        dict with keys: aqi, category, icon, confidence_range
    """
    model, norm_mean, norm_std, config, device = load_checkpoint(model_path)

    x = (features_row - norm_mean) / norm_std           # normalise
    x_tensor = torch.from_numpy(x.astype(np.float32)).unsqueeze(0).to(device)  # (1, T, F)

    with torch.no_grad():
        aqi_pred = model(x_tensor).item()

    aqi_pred = max(0.0, min(500.0, aqi_pred))           # clip to valid range
    category, icon = get_aqi_category(aqi_pred)

    return {
        "aqi":              round(aqi_pred, 1),
        "category":         category,
        "icon":             icon,
        "model_checkpoint": model_path,
    }


def predict_for_city_date(city: str, date: str,
                           features_path: str = "data/features/aqi_features_lags.csv",
                           model_path:    str = "models/aqi_cnn_lstm_best.pth") -> dict:
    """
    Look up a city+date in the lag features file and predict AQI.
    """
    from dataset import BASE_FEATURES, AQIWindowDataset

    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features not found: {features_path}")

    df = pd.read_csv(features_path)
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["City"] == city) & (df["date"] == pd.Timestamp(date))
    row = df[mask]
    if row.empty:
        raise ValueError(f"No data found for City='{city}' on date='{date}'")

    # Build (seq_len × n_features) array from lag columns
    model_obj, norm_mean, norm_std, config, device = load_checkpoint(model_path)
    seq_len = config["seq_len"]

    step_arrays = []
    for lag in range(seq_len):
        cols = BASE_FEATURES if lag == 0 else [f"{c}_lag{lag}" for c in BASE_FEATURES]
        available = [c for c in cols if c in row.columns]
        step_arrays.append(row[available].values[0])
    features_array = np.stack(step_arrays, axis=0)   # (seq_len, n_features)

    result = predict_from_features(features_array, model_path)
    result.update({"city": city, "date": date})
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="SSRO AQI CNN-LSTM inference"
    )
    parser.add_argument("--city",   default="Delhi", help="City name (default: Delhi)")
    parser.add_argument("--date",   default="2024-11-15", help="Date YYYY-MM-DD")
    parser.add_argument("--model",  default="models/aqi_cnn_lstm_best.pth")
    parser.add_argument("--data",   default="data/features/aqi_features_lags.csv")
    args = parser.parse_args()

    print(f"\n  SSRO AQI Predictor")
    print(f"  City: {args.city}  |  Date: {args.date}")
    print(f"  Model: {args.model}\n")

    try:
        result = predict_for_city_date(
            city=args.city, date=args.date,
            features_path=args.data, model_path=args.model
        )
        print(f"  Predicted AQI : {result['aqi']}")
        print(f"  Category      : {result['icon']} {result['category']}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"[Error] {e}")


if __name__ == "__main__":
    main()
