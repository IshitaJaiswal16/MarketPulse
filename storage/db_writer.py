"""
db_writer.py
------------
Writes anomaly alerts to PostgreSQL.
Every time an anomaly is detected, it gets stored here
so we can query history later via the API and dashboard.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from config.settings import POSTGRES_URL


def get_engine():
    return create_engine(POSTGRES_URL)


def create_tables():
    """Create tables if they don't exist."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS anomaly_alerts (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                anomaly_type VARCHAR(50) NOT NULL,
                price FLOAT NOT NULL,
                z_score FLOAT,
                if_score FLOAT,
                timestamp TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tick_history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                price FLOAT NOT NULL,
                size FLOAT NOT NULL,
                timestamp TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()
    print("Tables ready.")


def insert_alert(alert: dict):
    """Insert an anomaly alert into PostgreSQL."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO anomaly_alerts
                (symbol, anomaly_type, price, z_score, if_score, timestamp)
            VALUES
                (:symbol, :anomaly_type, :price, :z_score, :if_score, :timestamp)
        """), {
            "symbol": alert["symbol"],
            "anomaly_type": alert["anomaly_type"],
            "price": alert["price"],
            "z_score": alert["z_score"],
            "if_score": alert["if_score"],
            "timestamp": alert["timestamp"],
        })
        conn.commit()


def insert_tick(tick: dict):
    """Insert a raw tick into PostgreSQL."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO tick_history (symbol, price, size, timestamp)
            VALUES (:symbol, :price, :size, :timestamp)
        """), tick)
        conn.commit()