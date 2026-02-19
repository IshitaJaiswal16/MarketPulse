## 📈 MarketPulse

A real-time crypto market anomaly detection system. Think of it as a **smoke detector for your crypto** — it watches live prices and alerts you the moment something unusual happens.

Built with production-grade tools: Kafka, Isolation Forest, PostgreSQL, FastAPI, and Streamlit.

---

## 🎬 What It Does

MarketPulse streams live crypto prices (BTC, ETH, SOL) via WebSocket, processes them through a data pipeline, and automatically detects anomalies — sudden price spikes, volume irregularities, and volatility bursts. Users log in, select the coins they own, and see a personalized dashboard with real-time alerts for their portfolio only.

**For a naive user:** "It tells me when something weird is happening with my crypto — before I even check my phone."

**For a technical interviewer:** End-to-end streaming data pipeline with ML-based anomaly detection, persistent storage, REST API, and a multi-user dashboard.

---

## 🏗️ Architecture

```
Alpaca WebSocket API
        ↓
   Kafka Producer          ← ingestion/kafka_producer.py
        ↓
   Kafka Topic             ← market.crypto
        ↓
  Feature Engineering      ← processing/kafka_consumer.py
  (VWAP, Z-score,              rolling_std, price_return
   rolling volatility)
        ↓
  Anomaly Detection        ← detection/scorer.py
  (Isolation Forest +          3 anomaly types
   Z-score threshold)
        ↓
  ┌─────────────┐
  │  PostgreSQL │  ← anomaly alerts
  │  Parquet    │  ← raw tick archive
  └─────────────┘
        ↓
   FastAPI Layer           ← serving/api.py
        ↓
 Streamlit Dashboard       ← dashboard/app.py
 (Login + Portfolio)
```

---

## ⚙️ Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Data Source | Alpaca Markets WebSocket | Real live crypto prices, free tier |
| Message Broker | Apache Kafka | Decouples ingestion from processing, replay capability |
| Stream Processing | Python + windowed aggregations | VWAP, rolling volatility, Z-score computation |
| Anomaly Detection | Isolation Forest (scikit-learn) | Unsupervised, no labeled data needed |
| Storage | PostgreSQL + Parquet | Relational for alerts, columnar for raw tick archive |
| API | FastAPI | Async, auto-docs, Pydantic validation |
| Dashboard | Streamlit | Rapid UI, accessible to non-technical users |
| Containers | Docker Compose | One command to spin up entire infrastructure |

---

## 🚨 Anomaly Types Detected

| Type | What It Means |
|---|---|
| `PRICE_SPIKE` | Price deviates > 3 standard deviations from rolling mean |
| `VOLUME_ANOMALY` | Trade volume diverges significantly from VWAP window |
| `VOLATILITY_BURST` | Rolling volatility jumps sharply in short window |

---

## 🖥️ Dashboard Features

**v1 (app_v1.py):** General system-wide dashboard showing all alerts across all coins.

**v2 (app.py):** User authentication + portfolio management.
- Login / Register with username and password
- Select which coins you want to monitor
- Dashboard filters alerts to your portfolio only
- Per-coin price charts with anomaly history
- Auto-refreshes every 10 seconds

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Docker Desktop
- Alpaca Markets account (free) — for live data

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/IshitaJaiswal16/MarketPulse.git
cd MarketPulse

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Fill in your Alpaca API keys in .env

# 5. Start infrastructure (Kafka + PostgreSQL)
cd docker
docker-compose up -d
cd ..

# 6. Train the anomaly detection model
python detection/train.py
```

### Run the Pipeline

Open 4 terminals:

```bash
# Terminal 1 — Live data (or simulator if market is quiet)
python ingestion/kafka_producer.py
# or: python ingestion/tick_simulator.py

# Terminal 2 — Anomaly detection + storage
python detection/scorer.py

# Terminal 3 — REST API
uvicorn serving.api:app --reload --port 8000

# Terminal 4 — Dashboard
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.
Demo login: username `demo` / password `demo123`

---

## 📁 Project Structure

```
MarketPulse/
├── ingestion/
│   ├── alpaca_ws_client.py     # WebSocket connection to Alpaca
│   ├── kafka_producer.py       # Pushes live ticks to Kafka
│   └── tick_simulator.py       # Simulates ticks for testing
├── processing/
│   └── kafka_consumer.py       # Feature engineering on stream
├── detection/
│   ├── train.py                # Train Isolation Forest model
│   ├── anomaly_model.py        # Model loading + detection logic
│   └── scorer.py               # Full pipeline: Kafka → detect → store
├── storage/
│   ├── db_writer.py            # Write alerts to PostgreSQL
│   └── parquet_writer.py       # Archive raw ticks to Parquet
├── serving/
│   ├── api.py                  # FastAPI endpoints
│   └── schemas.py              # Pydantic response models
├── dashboard/
│   ├── app.py                  # v2: Login + portfolio dashboard
│   └── app_v1.py               # v1: General system dashboard
├── config/
│   └── settings.py             # Centralized config + env vars
├── docker/
│   └── docker-compose.yml      # Kafka + Zookeeper + PostgreSQL
├── tests/
│   └── test_anomaly.py
└── requirements.txt
```

---

## 🔑 Key Engineering Decisions

**Why Kafka?**
Decouples the ingestion layer from the processing layer. If the processor crashes, no data is lost — it waits in Kafka. Also enables replay of historical ticks.

**Why Isolation Forest?**
Unsupervised — no labeled "anomaly" data needed. Works well on multivariate feature vectors and is explainable in interviews.

**Why Parquet?**
Columnar format optimized for time-series analytics. Partitioned by date and symbol for efficient querying.

**Why FastAPI over Flask?**
Async support, automatic OpenAPI docs at `/docs`, Pydantic validation out of the box.

---

