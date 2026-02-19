"""
kafka_producer.py
-----------------
Takes live crypto ticks from Alpaca WebSocket
and pushes them into a Kafka topic.

Why Kafka? Instead of processing data the moment it arrives,
we drop it into Kafka first. This means if our processing layer
crashes or is slow, no data is lost — it's all sitting in Kafka
waiting to be picked up.
"""

import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaProducer
from alpaca.data.live import CryptoDataStream
from config.settings import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    CRYPTO_SYMBOLS,
    KAFKA_BROKER,
    KAFKA_TOPIC_CRYPTO,
)


def create_producer():
    """Create and return a Kafka producer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def format_tick(tick) -> dict:
    """Convert Alpaca tick into clean dictionary."""
    return {
        "symbol": tick.symbol,
        "price": float(tick.price),
        "size": float(tick.size),
        "timestamp": tick.timestamp.isoformat(),
    }


# Create producer once at module level
producer = create_producer()


async def on_crypto_trade(tick):
    """
    Runs every time a new tick arrives.
    Sends it to Kafka instead of just printing.
    """
    data = format_tick(tick)

    # Send to Kafka topic
    producer.send(KAFKA_TOPIC_CRYPTO, value=data)

    # Still print so we can see it's working
    print(f"[KAFKA] Sent → {data['symbol']} | ${data['price']:,.2f} | {data['timestamp']}")


def start_stream():
    print("Starting MarketPulse Kafka producer...")
    print(f"Broker: {KAFKA_BROKER} | Topic: {KAFKA_TOPIC_CRYPTO}")
    print(f"Watching: {', '.join(CRYPTO_SYMBOLS)}")
    print("-" * 50)

    stream = CryptoDataStream(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    stream.subscribe_trades(on_crypto_trade, *CRYPTO_SYMBOLS)
    stream.run()


if __name__ == "__main__":
    start_stream()