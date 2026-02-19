"""
api.py
------
FastAPI app that serves anomaly alerts and system status.
The Streamlit dashboard will call these endpoints.

Endpoints:
  GET /status        — is the system healthy?
  GET /alerts        — recent anomaly alerts (all symbols)
  GET /alerts/{symbol} — alerts for a specific coin
  GET /history/{symbol} — recent tick history
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from typing import List, Optional
from datetime import datetime

from config.settings import POSTGRES_URL
from serving.schemas import AlertResponse, StatusResponse

app = FastAPI(
    title="MarketPulse API",
    description="Real-time crypto anomaly detection system",
    version="1.0.0",
)

# Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_engine():
    return create_engine(POSTGRES_URL)


@app.get("/status", response_model=StatusResponse)
def get_status():
    """Check if the system is running and return total alert count."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM anomaly_alerts"))
            count = result.scalar()
        return StatusResponse(
            status="online",
            total_alerts=count,
            message="MarketPulse pipeline is running."
        )
    except Exception as e:
        return StatusResponse(
            status="offline",
            total_alerts=0,
            message=f"Database error: {str(e)}"
        )


@app.get("/alerts", response_model=List[dict])
def get_alerts(
    limit: int = Query(50, description="Number of alerts to return"),
    symbol: Optional[str] = Query(None, description="Filter by symbol e.g. BTC/USD")
):
    """Get recent anomaly alerts, optionally filtered by symbol."""
    engine = get_engine()
    with engine.connect() as conn:
        if symbol:
            result = conn.execute(text("""
                SELECT * FROM anomaly_alerts
                WHERE symbol = :symbol
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"symbol": symbol, "limit": limit})
        else:
            result = conn.execute(text("""
                SELECT * FROM anomaly_alerts
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"limit": limit})

        rows = result.mappings().all()
        return [dict(row) for row in rows]


@app.get("/alerts/{symbol}")
def get_alerts_by_symbol(symbol: str, limit: int = 20):
    """Get alerts for a specific symbol."""
    clean_symbol = symbol.replace("-", "/").upper()
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM anomaly_alerts
            WHERE symbol = :symbol
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"symbol": clean_symbol, "limit": limit})
        rows = result.mappings().all()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No alerts found for {clean_symbol}")
        return [dict(row) for row in rows]


@app.get("/history/{symbol}")
def get_tick_history(symbol: str, limit: int = 100):
    """Get recent tick history for a symbol."""
    clean_symbol = symbol.replace("-", "/").upper()
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM tick_history
            WHERE symbol = :symbol
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"symbol": clean_symbol, "limit": limit})
        rows = result.mappings().all()
        return [dict(row) for row in rows]


@app.get("/")
def root():
    return {"message": "MarketPulse API is running. Visit /docs for API documentation."}