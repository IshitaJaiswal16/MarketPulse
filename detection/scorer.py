"""
scorer.py
---------
Full pipeline: Kafka → Features → Anomaly Detection → Storage
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaConsumer
from collections import defaultdict
import pandas as pd

from config.settings import KAFKA_BROKER, KAFKA_TOPIC_CRYPTO, ROLLING_WINDOW
from detection.anomaly_model import load_model, detect_anomaly
from storage.db_writer import create_tables, insert_alert, insert_tick
from storage.parquet_writer import write_tick


tick_history = defaultdict(list)


def compute_features(symbol, price, size, timestamp):
    history = tick_history[symbol]
    history.append({"price": price, "size": size})

    if len(history) > ROLLING_WINDOW:
        history.pop(0)

    if len(history) < 5:
        return None

    prices = [h["price"] for h in history]
    sizes = [h["size"] for h in history]

    rolling_mean = sum(prices) / len(prices)
    rolling_std = pd.Series(prices).std()
    z_score = (price - rolling_mean) / rolling_std if rolling_std > 0 else 0
    vwap = sum(p * s for p, s in zip(prices, sizes)) / sum(sizes) if sum(sizes) > 0 else price
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
        "timestamp": timestamp,
    }


def start_scorer():
    print("Setting up database tables...")
    create_tables()

    print("Loading anomaly model...")
    model = load_model()
    print("Model loaded. Starting scorer...")
    print("-" * 50)

    consumer = KafkaConsumer(
        KAFKA_TOPIC_CRYPTO,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="marketpulse-scorer",
    )

    for message in consumer:
        tick = message.value

        # Archive raw tick to Parquet
        write_tick(tick)

        features = compute_features(
            tick["symbol"], tick["price"], tick["size"], tick["timestamp"]
        )

        if not features:
            continue

        result = detect_anomaly(model, features)

        if result["is_anomaly"]:
            print(
                f"🚨 ANOMALY | {result['symbol']} | "
                f"{result['anomaly_type']} | "
                f"${result['price']:,.2f} | "
                f"Z: {result['z_score']:+.3f}"
            )
            # Save alert to PostgreSQL
            insert_alert(result)
        else:
            print(f"✅ Normal | {result['symbol']} | ${result['price']:,.2f}")


if __name__ == "__main__":
    start_scorer()