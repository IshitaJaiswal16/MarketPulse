"""
dashboard/app.py
----------------
Streamlit dashboard for MarketPulse.
Simple, clean UI that any non-technical user can understand.

Shows:
1. System status
2. Live anomaly alerts table
3. Price chart with anomaly markers
4. Per-coin breakdown
"""

import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="MarketPulse",
    page_icon="📈",
    layout="wide",
)

# ── Header ─────────────────────────────────────────────────────────────────
st.title("📈 MarketPulse")
st.caption("Real-time crypto anomaly detection — smoke detector for your crypto.")

# ── Auto-refresh every 5 seconds ───────────────────────────────────────────
refresh = st.empty()

# ── Helper functions ────────────────────────────────────────────────────────
def fetch_status():
    try:
        r = requests.get(f"{API_URL}/status", timeout=3)
        return r.json()
    except:
        return {"status": "offline", "total_alerts": 0, "message": "API not reachable"}


def fetch_alerts(limit=100):
    try:
        r = requests.get(f"{API_URL}/alerts?limit={limit}", timeout=3)
        return r.json()
    except:
        return []


def fetch_symbol_alerts(symbol):
    try:
        r = requests.get(f"{API_URL}/alerts/{symbol.replace('/', '-')}", timeout=3)
        return r.json()
    except:
        return []


# ── Main dashboard ──────────────────────────────────────────────────────────
def render_dashboard():
    # Row 1: Status
    status = fetch_status()
    col1, col2, col3 = st.columns(3)

    with col1:
        color = "🟢" if status["status"] == "online" else "🔴"
        st.metric("System Status", f"{color} {status['status'].upper()}")

    with col2:
        st.metric("Total Alerts Detected", status["total_alerts"])

    with col3:
        st.metric("Monitored Assets", "BTC/USD, ETH/USD, SOL/USD")

    st.divider()

    # Row 2: Recent alerts table
    st.subheader("🚨 Recent Anomaly Alerts")
    alerts = fetch_alerts(limit=100)

    if alerts:
        df = pd.DataFrame(alerts)

        # Clean up columns for display
        display_cols = ["symbol", "anomaly_type", "price", "z_score", "timestamp"]
        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()

        if "price" in df_display.columns:
            df_display["price"] = df_display["price"].apply(lambda x: f"${x:,.2f}")

        if "z_score" in df_display.columns:
            df_display["z_score"] = df_display["z_score"].apply(
                lambda x: f"{x:+.3f}" if x is not None else "N/A"
            )

        # Color anomaly types
        def color_type(val):
            colors = {
                "PRICE_SPIKE": "background-color: #ff4444; color: white",
                "VOLUME_ANOMALY": "background-color: #ff8c00; color: white",
                "VOLATILITY_BURST": "background-color: #ffd700; color: black",
            }
            return colors.get(val, "")

        st.dataframe(
            df_display.style.map(color_type, subset=["anomaly_type"]),
            use_container_width=True,
            height=300,
        )
    else:
        st.info("No alerts yet. Start the simulator and scorer to generate data.")

    st.divider()

    # Row 3: Price chart per coin
    st.subheader("📊 Anomaly History by Coin")
    tab1, tab2, tab3 = st.tabs(["BTC/USD", "ETH/USD", "SOL/USD"])

    for tab, symbol in zip([tab1, tab2, tab3], ["BTC/USD", "ETH/USD", "SOL/USD"]):
        with tab:
            data = fetch_symbol_alerts(symbol)
            if data:
                df_sym = pd.DataFrame(data)
                if "timestamp" in df_sym.columns and "price" in df_sym.columns:
                    df_sym["timestamp"] = pd.to_datetime(df_sym["timestamp"])
                    df_sym = df_sym.sort_values("timestamp")
                    st.line_chart(df_sym.set_index("timestamp")["price"])

                    # Summary stats
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Alerts", len(df_sym))
                    c2.metric("Avg Price", f"${df_sym['price'].mean():,.2f}")
                    c3.metric(
                        "Most Common Type",
                        df_sym["anomaly_type"].mode()[0] if "anomaly_type" in df_sym else "N/A"
                    )
            else:
                st.info(f"No alerts for {symbol} yet.")

    st.divider()
    st.caption(f"Last refreshed: {pd.Timestamp.now().strftime('%H:%M:%S')} — refreshes every 10 seconds")


render_dashboard()

# Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()