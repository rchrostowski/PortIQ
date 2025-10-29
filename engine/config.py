import os
import pandas as pd

# -------------------------------
# Universe loader
# -------------------------------
UNIVERSE_PATH = os.path.join(os.path.dirname(__file__), "universe.csv")

def load_universe():
    """Load universe tickers (S&P500 + ETFs)."""
    if not os.path.exists(UNIVERSE_PATH):
        raise FileNotFoundError(
            f"Universe file missing: {UNIVERSE_PATH}. Run scripts/build_universe.py."
        )
    df = pd.read_csv(UNIVERSE_PATH)
    return df["ticker"].dropna().astype(str).str.upper().unique().tolist()

# -------------------------------
# Global parameters
# -------------------------------
UNIVERSE = load_universe()
BAR_FREQ = "1d"
LOOKBACK_DAYS = 365 * 5
HORIZON_DAYS = 21
RETRAIN_WINDOW = 252 * 2
TRANSACTION_COST_BPS = 5
MAX_WEIGHT = 0.25
TOP3_MAX = 0.60
TARGET_VOL = 0.10
SEED = 42
