"""
dashboard/app.py
----------------
MarketPulse dashboard with login and portfolio management.
Users log in, select their coins, and only see alerts for what they own.
"""

import streamlit as st
import requests
import pandas as pd
import time
import json
import os
import hashlib

API_URL = "http://localhost:8000"
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

st.set_page_config(
    page_title="MarketPulse",
    page_icon="📈",
    layout="wide",
)

AVAILABLE_ASSETS = [
    "BTC/USD", "ETH/USD", "SOL/USD"
]

# ── User storage (simple JSON file) ────────────────────────────────────────

def load_users():
    if not os.path.exists(USERS_FILE):
        # Create default users file
        default_users = {
            "demo": {
                "password": hash_password("demo123"),
                "portfolio": ["BTC/USD"]
            }
        }
        save_users(default_users)
        return default_users
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username, password):
    users = load_users()
    if username in users:
        return users[username]["password"] == hash_password(password)
    return False


def register_user(username, password, portfolio):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = {
        "password": hash_password(password),
        "portfolio": portfolio,
    }
    save_users(users)
    return True, "Account created!"


def get_portfolio(username):
    users = load_users()
    return users.get(username, {}).get("portfolio", [])


def update_portfolio(username, portfolio):
    users = load_users()
    if username in users:
        users[username]["portfolio"] = portfolio
        save_users(users)


# ── API helpers ─────────────────────────────────────────────────────────────

def fetch_status():
    try:
        r = requests.get(f"{API_URL}/status", timeout=3)
        return r.json()
    except:
        return {"status": "offline", "total_alerts": 0, "message": "API not reachable"}


def fetch_alerts_for_symbol(symbol):
    try:
        r = requests.get(f"{API_URL}/alerts/{symbol.replace('/', '-')}", timeout=3)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []


def fetch_all_alerts(limit=200):
    try:
        r = requests.get(f"{API_URL}/alerts?limit={limit}", timeout=3)
        return r.json()
    except:
        return []


# ── Login / Register page ───────────────────────────────────────────────────

def show_login_page():
    st.title("📈 MarketPulse")
    st.caption("Real-time crypto anomaly detection — smoke detector for your crypto.")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Create Account"])

    with tab_login:
        st.subheader("Welcome back")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", use_container_width=True):
            if verify_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.caption("Demo account: username `demo` / password `demo123`")

    with tab_register:
        st.subheader("Create your account")
        new_user = st.text_input("Choose a username", key="reg_user")
        new_pass = st.text_input("Choose a password", type="password", key="reg_pass")
        selected = st.multiselect(
            "Select coins to monitor",
            AVAILABLE_ASSETS,
            default=["BTC/USD"],
            key="reg_portfolio"
        )

        if st.button("Create Account", use_container_width=True):
            if not new_user or not new_pass:
                st.error("Please fill in all fields.")
            elif not selected:
                st.error("Select at least one coin.")
            else:
                success, msg = register_user(new_user, new_pass, selected)
                if success:
                    st.success(f"{msg} You can now log in.")
                else:
                    st.error(msg)


# ── Main dashboard ──────────────────────────────────────────────────────────

def show_dashboard():
    username = st.session_state.username
    portfolio = get_portfolio(username)

    # Sidebar
    with st.sidebar:
        st.title("📈 MarketPulse")
        st.write(f"👤 **{username}**")
        st.divider()

        st.subheader("My Portfolio")
        new_portfolio = st.multiselect(
            "Coins I'm watching",
            AVAILABLE_ASSETS,
            default=portfolio,
        )
        if new_portfolio != portfolio:
            update_portfolio(username, new_portfolio)
            st.success("Portfolio updated!")
            portfolio = new_portfolio

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    # Main content
    st.title(f"📈 MarketPulse")
    st.caption(f"Monitoring: {', '.join(portfolio) if portfolio else 'No coins selected'}")

    if not portfolio:
        st.warning("No coins selected. Add some from the sidebar.")
        return

    # Status row
    status = fetch_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        color = "🟢" if status["status"] == "online" else "🔴"
        st.metric("System Status", f"{color} {status['status'].upper()}")
    with col2:
        st.metric("Total Alerts (All Users)", status["total_alerts"])
    with col3:
        st.metric("Your Watchlist", len(portfolio))

    st.divider()

    # Alerts for user's portfolio only
    st.subheader("🚨 Your Alerts")

    all_alerts = []
    for symbol in portfolio:
        alerts = fetch_alerts_for_symbol(symbol)
        all_alerts.extend(alerts)

    if all_alerts:
        df = pd.DataFrame(all_alerts)
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        display_cols = ["symbol", "anomaly_type", "price", "z_score", "timestamp"]
        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()

        if "price" in df_display.columns:
            df_display["price"] = df_display["price"].apply(lambda x: f"${x:,.2f}")
        if "z_score" in df_display.columns:
            df_display["z_score"] = df_display["z_score"].apply(
                lambda x: f"{float(x):+.3f}" if x is not None else "N/A"
            )

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
        st.info("No alerts yet for your portfolio. Start the pipeline to generate data.")

    st.divider()

    # Per-coin charts
    st.subheader("📊 Price History by Coin")
    tabs = st.tabs(portfolio)

    for tab, symbol in zip(tabs, portfolio):
        with tab:
            data = fetch_alerts_for_symbol(symbol)
            if data:
                df_sym = pd.DataFrame(data)
                df_sym["timestamp"] = pd.to_datetime(df_sym["timestamp"])
                df_sym = df_sym.sort_values("timestamp")

                st.line_chart(df_sym.set_index("timestamp")["price"])

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Alerts", len(df_sym))
                c2.metric("Avg Price", f"${df_sym['price'].mean():,.2f}")
                c3.metric(
                    "Most Common Alert",
                    df_sym["anomaly_type"].mode()[0] if "anomaly_type" in df_sym.columns else "N/A"
                )
            else:
                st.info(f"No data for {symbol} yet.")

    st.caption(f"Last refreshed: {pd.Timestamp.now().strftime('%H:%M:%S')} — auto-refreshes every 10s")


# ── App entry point ─────────────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    show_login_page()
else:
    show_dashboard()
    time.sleep(10)
    st.rerun()