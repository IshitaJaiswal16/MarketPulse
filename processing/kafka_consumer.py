"""
kafka_consumer.py
-----------------
Reads tick data from Kafka and computes rolling features.
These features are what the anomaly detector will use.

Features we compute:
- rolling_mean: average price over last N ticks
- rolling_std: how much price is varying (volatility)
- z_score: how far current price is from the mean (in standard deviations)
- vwap: volume weighted average price
- price_return: % change from previous tick
"""

import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaConsumer
from collections import defaultdict
import pandas as pd

from config.settings import KAFKA_BROKER, KAFKA_TOPIC_CRYPTO, ROLLING_WINDOW


# Store recent ticks per symbol for rolling calculations
tick_history = defaultdict(list)


def compute_features(symbol: str, price: float, size: float) -> dict:
    """
    Given a new tick, compute rolling features using recent history.
    Returns None if not enough data yet.
    """
    history = tick_history[symbol]
    history.append({"price": price, "size": size})

    # Keep only last N ticks
    if len(history) > ROLLING_WINDOW:
        history.pop(0)

    # Need at least 5 ticks before computing features
    if len(history) < 5:
        return None

    prices = [h["price"] for h in history]
    sizes = [h["size"] for h in history]

    rolling_mean = sum(prices) / len(prices)
    rolling_std = pd.Series(prices).std()

    # Z-score: how many standard deviations away from mean
    z_score = (price - rolling_mean) / rolling_std if rolling_std > 0 else 0

    # VWAP: sum(price * volume) / sum(volume)
    vwap = sum(p * s for p, s in zip(prices, sizes)) / sum(sizes) if sum(sizes) > 0 else price

    # Price return: % change from previous tick
    price_return = ((price - prices[-2]) / prices[-2] * 100) if len(prices) >= 2 else 0

    return {
        "symbol": symbol,
        "price": price,
        "size": size,
        "rolling_mean": round(rolling_mean, 4),
        "rolling_std": round(rolling_std, 4),
        "z_score": round(z_score, 4),
        "vwap": round(vwap, 4),
        "price_return": round(price_return, 6),
        "window_size": len(history),
    }


def start_consumer():
    print("Starting MarketPulse stream processor...")
    print(f"Consuming from: {KAFKA_TOPIC_CRYPTO}")
    print("-" * 50)

    consumer = KafkaConsumer(
        KAFKA_TOPIC_CRYPTO,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",  # only process new messages
        group_id="marketpulse-processor",
    )

    for message in consumer:
        tick = message.value
        symbol = tick["symbol"]
        price = tick["price"]
        size = tick["size"]

        features = compute_features(symbol, price, size)

        if features:
            print(
                f"[FEATURES] {features['symbol']} | "
                f"Price: ${features['price']:,.2f} | "
                f"Z-Score: {features['z_score']:+.3f} | "
                f"VWAP: ${features['vwap']:,.2f} | "
                f"Return: {features['price_return']:+.4f}%"
            )
        else:
            print(f"[WARMING UP] {symbol} — collecting ticks ({len(tick_history[symbol])}/5 needed)")


if __name__ == "__main__":
    start_consumer()