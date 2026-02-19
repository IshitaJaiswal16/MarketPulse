import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Alpaca API Credentials ──────────────────────────────────────────────────
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# ── Assets to Monitor ──────────────────────────────────────────────────────
# We use crypto because it trades 24/7 — no market hours dependency
CRYPTO_SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD"]

# ── Kafka Config ───────────────────────────────────────────────────────────
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC_CRYPTO = "market.crypto"

# ── Anomaly Detection Thresholds ───────────────────────────────────────────
ZSCORE_THRESHOLD = 3.0          # flag if Z-score exceeds this
ROLLING_WINDOW = 20             # number of ticks for rolling calculations

# ── Storage ────────────────────────────────────────────────────────────────
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/marketpulse")
PARQUET_OUTPUT_DIR = "data/raw_ticks"
