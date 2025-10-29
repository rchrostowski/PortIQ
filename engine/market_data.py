import yfinance as yf

DEFAULT_TICKERS = ["SPY","QQQ","AAPL","MSFT","NVDA","XLE","TLT","SCHD","VOO","IWM"]

def get_market_snapshot(tickers=None) -> dict:
    if tickers is None:
        tickers = DEFAULT_TICKERS
    prices = yf.download(tickers, period="5d")["Adj Close"].iloc[-1]
    return {t: float(prices[t]) for t in prices.index}
