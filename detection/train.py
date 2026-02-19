"""
train.py
--------
Trains the Isolation Forest on simulated normal market data.
In a real setup you'd use historical data from Alpaca REST API.
For now we generate realistic training data to bootstrap the model.
"""

import sys
import os
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from detection.anomaly_model import build_model, save_model


def generate_training_data(n_samples=2000):
    """
    Generate realistic normal market feature vectors for training.
    Features: [z_score, price_return, rolling_std, size]
    """
    np.random.seed(42)

    z_scores = np.random.normal(0, 1, n_samples)
    price_returns = np.random.normal(0, 0.05, n_samples)
    rolling_stds = np.abs(np.random.normal(50, 20, n_samples))
    sizes = np.abs(np.random.normal(0.1, 0.05, n_samples))

    return np.column_stack([z_scores, price_returns, rolling_stds, sizes])


def train():
    print("Generating training data...")
    X_train = generate_training_data()
    print(f"Training on {len(X_train)} samples...")

    model = build_model()
    model.fit(X_train)

    save_model(model)
    print("Training complete!")


if __name__ == "__main__":
    train()