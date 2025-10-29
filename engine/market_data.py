import yfinance as yf
import pandas as pd

DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "XLE", "TLT", "VOO", "SCHD"]

def get_market_snapshot(tickers=None) -> dict:
    """
    Download recent prices safely and always return a flat dict {ticker: price}.
    Handles missing tickers and column shape differences gracefully.
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    try:
        data = yf.download(tickers, period="5d", progress=False)
    except Exception as e:
        return {"error": f"Yahoo Finance request failed: {e}"}

    # If "Adj Close" exists as column level, use it; otherwise fallback
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.levels[0]:
            data = data["Adj Close"]
        else:
            # take the last level (e.g., 'Close')
            data = data[data.columns.levels[0][-1]]

    # Drop rows with all NaN
    data = data.dropna(how="all")

    # take the most recent row
    try:
        latest = data.iloc[-1]
    except IndexError:
        return {"error": "No valid price data retrieved."}

    # Convert to plain dict
    prices = {}
    for t in latest.index:
        try:
            prices[t] = float(latest[t])
        except Exception:
            continue

    return prices or {"error": "All tickers failed to return prices."}
import yfinance as yf
import pandas as pd

DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "XLE", "TLT", "VOO", "SCHD"]

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
