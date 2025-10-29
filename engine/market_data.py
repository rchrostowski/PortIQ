import streamlit as st
import yfinance as yf
import pandas as pd

DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "XLE", "TLT", "VOO", "SCHD"]

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_snapshot(tickers=None) -> dict:
    if tickers is None:
        tickers = DEFAULT_TICKERS
    try:
        data = yf.download(tickers, period="5d", progress=False)
    except Exception as e:
        return {"error": f"Yahoo Finance request failed: {e}"}

    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.levels[0]:
            data = data["Adj Close"]
        else:
            data = data[data.columns.levels[0][-1]]
    data = data.dropna(how="all")

    try:
        latest = data.iloc[-1]
    except IndexError:
        return {"error": "No valid price data."}

    prices = {}
    for t in latest.index:
        try:
            prices[t] = float(latest[t])
        except Exception:
            continue
    return prices or {"error": "All tickers failed."}
