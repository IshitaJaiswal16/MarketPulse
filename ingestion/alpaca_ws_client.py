"""
alpaca_ws_client.py
-------------------
Connects to Alpaca's WebSocket and streams live crypto prices.
Right now it just prints ticks to the console — in Phase 2
we'll route these into Kafka instead.

What is a tick?
A tick is a single price/volume update from the market.
Every time BTC's price changes, Alpaca sends us a tick.
"""

import sys
import os

# This makes sure Python can find the config folder regardless of how you run the file
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from alpaca.data.live import CryptoDataStream
from config.settings import ALPACA_API_KEY, ALPACA_SECRET_KEY, CRYPTO_SYMBOLS


def format_tick(tick) -> dict:
    """
    Convert raw Alpaca tick object into a clean dictionary.
    This is the format we'll use throughout the whole pipeline.
    """
    return {
        "symbol": tick.symbol,
        "price": float(tick.price),
        "size": float(tick.size),       # size = volume of that trade
        "timestamp": tick.timestamp.isoformat(),
    }


async def on_crypto_trade(tick):
    """
    This function runs every time a new tick arrives.
    For now: just print it. Phase 2: send to Kafka.
    """
    data = format_tick(tick)
    print(f"[TICK] {data['symbol']} | Price: ${data['price']:,.2f} | Size: {data['size']} | Time: {data['timestamp']}")


def start_stream():
    """
    Start the WebSocket stream.
    Subscribes to all symbols defined in settings.
    """
    print("Starting MarketPulse stream...")
    print(f"Watching: {', '.join(CRYPTO_SYMBOLS)}")
    print("-" * 50)

    # Create the stream client
    stream = CryptoDataStream(ALPACA_API_KEY, ALPACA_SECRET_KEY)

    # Subscribe to trade updates for each symbol
    stream.subscribe_trades(on_crypto_trade, *CRYPTO_SYMBOLS)

    # This blocks and keeps running until you stop it (Ctrl+C)
    stream.run()


if __name__ == "__main__":
    start_stream()
