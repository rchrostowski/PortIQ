import yfinance as yf

def validate_tickers(portfolio: dict):
    allocations = portfolio.get("allocations", [])
    valid, invalid = [], []
    for a in allocations:
        t = a.get("ticker","").upper()
        try:
            info = yf.Ticker(t).info
            if info.get("shortName"):
                a["ticker"] = t
                valid.append(a)
            else:
                invalid.append(t)
        except Exception:
            invalid.append(t)
    return valid, invalid

def normalize_weights(portfolio: dict):
    allocs = portfolio.get("allocations", [])
    total = sum(a.get("weight", 0) for a in allocs)
    if total <= 0:
        return portfolio
    for a in allocs:
        a["weight"] = round(a["weight"] / total, 4)
    return portfolio

def check_limits(portfolio: dict):
    allocs = portfolio.get("allocations", [])
    weights = sorted([a["weight"] for a in allocs], reverse=True)
    alerts = []
    if any(w > 0.25 for w in weights):
        alerts.append("⚠️ Single-name exposure exceeds 25%.")
    if sum(weights[:3]) > 0.60:
        alerts.append(f"⚠️ Top-3 concentration {round(sum(weights[:3])*100,1)}% > 60%.")
    return alerts
