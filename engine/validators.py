import pandas as pd

def normalize_weights(portfolio):
    """Ensure weights sum to 1.0"""
    allocs = portfolio.get("allocations", [])
    total = sum(a["weight"] for a in allocs)
    if total == 0:
        return portfolio
    for a in allocs:
        a["weight"] = a["weight"] / total
    portfolio["allocations"] = allocs
    return portfolio

def validate_tickers(portfolio):
    """Separate valid and invalid tickers (naive placeholder)."""
    valid, invalid = [], []
    for a in portfolio.get("allocations", []):
        if isinstance(a["ticker"], str) and len(a["ticker"]) <= 5:
            valid.append(a)
        else:
            invalid.append(a)
    return valid, [a["ticker"] for a in invalid]

def check_limits(portfolio):
    """Return warnings about concentration and exposure."""
    allocs = portfolio.get("allocations", [])
    alerts = []
    if not allocs:
        return alerts
    weights = [a["weight"] for a in allocs]
    weights.sort(reverse=True)
    if max(weights) > 0.25:
        alerts.append("⚠️ Single-name exposure exceeds 25%.")
    if sum(weights[:3]) > 0.60:
        alerts.append(f"⚠️ Top-3 concentration {sum(weights[:3])*100:.1f}% > 60%.")
    return alerts
