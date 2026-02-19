"""
anomaly_model.py
----------------
Detects anomalies in crypto tick data using two approaches:
1. Z-Score: flags sudden price spikes statistically
2. Isolation Forest: unsupervised ML that learns what "normal" looks like
   and flags anything that doesn't fit.
"""

import sys
import os
import json
import joblib
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sklearn.ensemble import IsolationForest
from config.settings import ZSCORE_THRESHOLD

# Path to save/load trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.joblib")


def build_model():
    """Create a fresh Isolation Forest model."""
    return IsolationForest(
        n_estimators=100,
        contamination=0.05,  # expect ~5% of data to be anomalous
        random_state=42,
    )


def save_model(model):
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("No trained model found. Run train.py first.")
    return joblib.load(MODEL_PATH)


def extract_features(feature_record: dict) -> list:
    """Pull the numeric features we feed into the model."""
    return [
        feature_record["z_score"],
        feature_record["price_return"],
        feature_record["rolling_std"],
        feature_record["size"],
    ]


def detect_anomaly(model, feature_record: dict) -> dict:
    """
    Run anomaly detection on a feature record.
    Returns anomaly info including type and severity.
    """
    features = extract_features(feature_record)
    features_array = np.array(features).reshape(1, -1)

    # Isolation Forest: -1 = anomaly, 1 = normal
    if_score = model.decision_function(features_array)[0]
    if_prediction = model.predict(features_array)[0]

    # Z-Score check
    z_score = abs(feature_record["z_score"])
    price_return = abs(feature_record["price_return"])

    # Determine anomaly type
    anomaly_type = None
    if if_prediction == -1 or z_score > ZSCORE_THRESHOLD:
        if z_score > ZSCORE_THRESHOLD:
            anomaly_type = "PRICE_SPIKE"
        elif price_return > 0.1:
            anomaly_type = "VOLUME_ANOMALY"
        else:
            anomaly_type = "VOLATILITY_BURST"

    return {
        "is_anomaly": anomaly_type is not None,
        "anomaly_type": anomaly_type,
        "if_score": round(float(if_score), 4),
        "z_score": feature_record["z_score"],
        "symbol": feature_record["symbol"],
        "price": feature_record["price"],
        "timestamp": feature_record.get("timestamp", ""),
    }