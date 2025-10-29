import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt
from engine.config import UNIVERSE, LOOKBACK_DAYS, BAR_FREQ

def load_history(tickers=UNIVERSE, end=None, days=LOOKBACK_DAYS):
    """Download historical price data in batches to avoid rate limits."""
    end = end or dt.date.today()
    start = end - dt.timedelta(days=days + 60)
    all_px = []
    for i in range(0, len(tickers), 100):
        batch = tickers[i:i+100]
        try:
            data = yf.download(
                batch, start=start, end=end,
                interval=BAR_FREQ, auto_adjust=True, progress=False
            )["Close"]
            all_px.append(data)
        except Exception as e:
            print("Batch failed:", e)
    px = pd.concat(all_px, axis=1)
    px = px.dropna(how="all").ffill().dropna(axis=1, how="all")
    return px

def compute_forward_returns(px: pd.DataFrame, horizon=21):
    """Compute forward returns used for model targets."""
    fwd = px.shift(-horizon) / px - 1.0
    fwd = fwd.rename(columns=lambda t: f"fwd_{horizon}d_{t}")
    return fwd

def to_panel(alphas: dict):
    """Combine multiple signal DataFrames into a single feature panel."""
    out = None
    for k, df in alphas.items():
        df = df.add_prefix(k + "_")
        out = df if out is None else out.join(df, how="outer")
    return out
