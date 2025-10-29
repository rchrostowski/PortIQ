def summarize_portfolio(portfolio: dict):
    allocs = portfolio.get("allocations", [])
    total = sum(a["weight"] for a in allocs)
    if total <= 0:
        return {}

    top3 = sorted([a["weight"] for a in allocs], reverse=True)[:3]
    metrics = {
        "Holdings": len(allocs),
        "Top-3 Concentration": f"{sum(top3)*100:.1f}%",
        "Largest Position": f"{max(top3)*100:.1f}%",
        "Diversification Index": f"{(1/sum(w**2 for w in top3)):.2f}",
    }
    return metrics
