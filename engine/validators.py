import yfinance as yf

def validate_tickers(portfolio: dict):
    """
    Validate tickers by checking if price history is available.
    If a ticker returns empty history, it's treated as invalid.
    """
    allocations = portfolio.get("allocations", [])
    valid, invalid = [], []

    for a in allocations:
        t = a.get("ticker", "").upper().strip()
        try:
            data = yf.Ticker(t).history(period="1d")
            if data.empty:
                invalid.append(t)
            else:
                a["ticker"] = t
                valid.append(a)
        except Exception:
            invalid.append(t)

    return valid, invalid


def normalize_weights(portfolio: dict):
    """
    Ensures portfolio weights sum to 1.
    """
    allocs = portfolio.get("allocations", [])
    total = sum(a.get("weight", 0) for a in allocs)
    if total <= 0:
        return portfolio
    for a in allocs:
        a["weight"] = round(a["weight"] / total, 4)
    return portfolio


def check_limits(portfolio: dict):
    """
    Detects over-concentration or exposure risks.
    """
    allocs = portfolio.get("allocations", [])
    weights = sorted([a["weight"] for a in allocs if "weight" in a], reverse=True)
    alerts = []

    if any(w > 0.25 for w in weights):
        alerts.append("⚠️ Single-name exposure exceeds 25%.")
    if sum(weights[:3]) > 0.60:
        alerts.append(f"⚠️ Top-3 concentration {round(sum(weights[:3])*100,1)}% > 60%.")
    if len(allocs) < 4:
        alerts.append("⚠️ Portfolio not diversified (fewer than 4 holdings).")

    return alerts
