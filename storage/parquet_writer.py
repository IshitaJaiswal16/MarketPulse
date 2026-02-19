"""
parquet_writer.py
-----------------
Archives raw ticks to Parquet files on disk.
Partitioned by date and symbol — efficient for
time-series analytics later.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from datetime import datetime
from config.settings import PARQUET_OUTPUT_DIR


def write_tick(tick: dict):
    """
    Append a tick to a Parquet file.
    Files are partitioned by date: data/raw_ticks/2024-02-19/BTC_USD.parquet
    """
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    symbol_clean = tick["symbol"].replace("/", "_")

    folder = os.path.join(PARQUET_OUTPUT_DIR, date_str)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{symbol_clean}.parquet")

    df_new = pd.DataFrame([tick])

    if os.path.exists(filepath):
        df_existing = pd.read_parquet(filepath)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_parquet(filepath, index=False)