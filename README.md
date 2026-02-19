# MarketPulse 📈

A real-time crypto market monitoring system that watches live prices of Bitcoin, Ethereum, and Solana — and automatically detects unusual activity like sudden price spikes or volume anomalies.

Think of it as a **smoke detector for crypto**.

## What it does
- Streams live crypto prices via Alpaca WebSocket
- Routes data through Kafka for reliable processing
- Detects anomalies using Isolation Forest + Z-score models
- Stores alerts in PostgreSQL, raw ticks in Parquet
- Surfaces everything through a clean Streamlit dashboard
- Sends Slack alerts when something unusual happens

## Tech Stack
| Layer | Tool |
|---|---|
| Data Source | Alpaca Markets API |
| Message Broker | Apache Kafka |
| Stream Processing | Python + windowed feature engineering |
| Anomaly Detection | Isolation Forest + Z-score |
| Storage | PostgreSQL + Parquet |
| API | FastAPI |
| Dashboard | Streamlit |
| Alerting | Slack Webhook |
| Containers | Docker Compose |

## Getting Started
```bash
# 1. Clone the repo
git clone https://github.com/yourusername/marketpulse.git
cd marketpulse

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your .env file
cp .env.example .env
# Fill in your Alpaca API keys

# 5. Run the stream
python ingestion/alpaca_ws_client.py
```

## Project Structure
```
marketpulse/
├── ingestion/       # WebSocket client + Kafka producer
├── processing/      # Feature engineering on stream
├── detection/       # Anomaly detection models
├── storage/         # PostgreSQL + Parquet writers
├── serving/         # FastAPI endpoints
├── alerting/        # Slack notifications
├── dashboard/       # Streamlit UI
├── config/          # Centralized settings
└── docker/          # Docker Compose setup
```
