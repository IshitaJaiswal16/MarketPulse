"""
tick_simulator.py
-----------------
Pushes fake but realistic crypto ticks into Kafka.
Used for testing the pipeline when real market volume is low.
"""

import sys
import os
import json
import time
import random

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaProducer
from datetime import datetime, timezone
from config.settings import KAFKA_BROKER, KAFKA_TOPIC_CRYPTO

# Realistic base prices
BASE_PRICES = {
    "BTC/USD": 66800.0,
    "ETH/USD": 1980.0,
    "SOL/USD": 140.0,
}


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def simulate_tick(symbol: str, last_price: float) -> dict:
    """Generate a realistic tick with small random price movement."""
    # Small random % change each tick (-0.1% to +0.1%)
    change_pct = random.uniform(-0.001, 0.001)

    # Occasionally inject a spike for anomaly testing (1% chance)
    if random.random() < 0.01:
        change_pct = random.uniform(0.005, 0.015)
        print(f"[SPIKE INJECTED] {symbol}")

    new_price = last_price * (1 + change_pct)
    size = round(random.uniform(0.001, 0.5), 6)

    return {
        "symbol": symbol,
        "price": round(new_price, 2),
        "size": size,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def start_simulator(ticks_per_second=2):
    print("Starting tick simulator...")
    print(f"Pushing to: {KAFKA_TOPIC_CRYPTO} at {ticks_per_second} ticks/sec")
    print("-" * 50)

    producer = create_producer()
    prices = BASE_PRICES.copy()

    while True:
        for symbol in prices:
            tick = simulate_tick(symbol, prices[symbol])
            prices[symbol] = tick["price"]  # update for next tick

            producer.send(KAFKA_TOPIC_CRYPTO, value=tick)
            print(f"[SIM] {tick['symbol']} | ${tick['price']:,.2f} | size: {tick['size']}")

        time.sleep(1 / ticks_per_second)


if __name__ == "__main__":
    start_simulator()