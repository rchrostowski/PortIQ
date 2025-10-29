# scripts/build_universe.py
import os
import pandas as pd
import requests, io  # <-- Make sure these are here

# ---- Core ETFs ----
ETF_LIST = [
    "SPY","QQQ","IWM","TLT","IEF","LQD","HYG",
    "XLF","XLK","XLE","XLY","XLP","XLV","XLI","XLB","XLU",
    "VNQ","GLD","SLV","DBC"
]

def fetch_sp500_symbols():
    """Fetch S&P 500 tickers from Wikipedia with a browser-like header."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    tables = pd.read_html(io.StringIO(r.text))
    df = tables[0]
    syms = df["Symbol"].dropna().astype(str).tolist()
    # Convert dot tickers (BRK.B → BRK-B) for Yahoo
    syms = [s.replace(".", "-").upper().strip() for s in syms]
    return syms

def main():
    here = os.path.dirname(os.path.dirname(__file__))  # repo root
    out_path = os.path.join(here, "engine", "universe.csv")

    try:
        sp500 = fetch_sp500_symbols()
        print(f"Fetched {len(sp500)} S&P 500 tickers.")
    except Exception as e:
        print("WARNING: Could not fetch S&P 500 from Wikipedia:", e)
        sp500 = []

    merged = sorted(set(sp500 + ETF_LIST))
    pd.DataFrame({"ticker": merged}).to_csv(out_path, index=False)
    print(f"Wrote {len(merged)} tickers to {out_path}")

if __name__ == "__main__":
    main()
