import os, json, re
from typing import Dict, Any

# -------------------------------
# Optional OpenAI client
# -------------------------------
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI = False
        _client = None

# -------------------------------
# Local imports
# -------------------------------
from engine.validators import normalize_weights
from engine.config import HORIZON_DAYS
from engine.data import load_history
from engine.signals import build_signal_panel
from engine.model import build_training_set, train_xgb_like, predict_latest
from engine.risk import ledoit_wolf_cov
from engine.optimizer import mean_variance_opt

# -------------------------------
# Helper utilities
# -------------------------------
def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
        return {"allocations": []}

def _heuristic_portfolio(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Offline rule-based portfolio when AI or data is unavailable."""
    risk = profile.get("risk_tolerance", 5)
    themes = [t.lower() for t in (profile.get("themes") or [])]

    if risk <= 3:
        core = [
            ("SCHD", 0.30, "Dividend income & quality"),
            ("BND",  0.30, "Core bonds"),
            ("VOO",  0.20, "Broad US equities"),
            ("XLU",  0.10, "Utilities defensive"),
            ("TLT",  0.10, "Duration hedge"),
        ]
    elif risk <= 6:
        core = [
            ("VOO",  0.35, "US equities"),
            ("QQQ",  0.20, "Tech growth"),
            ("SCHD", 0.15, "Dividend quality"),
            ("TLT",  0.15, "Bond hedge"),
            ("XLE",  0.15, "Energy cyclical"),
        ]
    else:
        core = [
            ("QQQ",  0.35, "High growth tech"),
            ("VOO",  0.25, "Core equities"),
            ("IWM",  0.15, "Small-cap beta"),
            ("XLE",  0.15, "Energy exposure"),
            ("TLT",  0.10, "Crisis hedge"),
        ]

    # Simple theme nudges
    allocs = dict((t, w) for t, w, _ in core)
    reasons = dict((t, r) for t, _, r in core)
    def _nudge(from_t, to_t, delta, reason):
        if allocs.get(from_t, 0) >= delta:
            allocs[from_t] -= delta
            allocs[to_t] = allocs.get(to_t, 0) + delta
            reasons[to_t] = reason

    if "technology" in themes or "ai" in themes:
        _nudge("VOO", "SOXX", 0.05, "AI/semiconductor exposure")
    if "dividends" in themes:
        _nudge("VOO", "SCHD", 0.05, "Dividend tilt")
    if "energy" in themes:
        _nudge("VOO", "XLE", 0.05, "Energy overweight")
    if "emerging markets" in themes:
        _nudge("VOO", "EEM", 0.05, "Emerging markets exposure")

    out = {"allocations": [
        {"ticker": k, "weight": float(v), "reason": reasons.get(k, "")}
        for k, v in allocs.items() if v > 0
    ]}
    return normalize_weights(out)

# -------------------------------
# Explainable LLM portfolio
# -------------------------------
PORTFOLIO_PROMPT = """
You are PortIQ, an AI portfolio constructor.

Return JSON:
{"allocations": [{"ticker": "QQQ", "weight": 0.20, "reason": "..."}]}
Weights sum to 1.0.
Respect risk tolerance and diversification.
"""

def generate_portfolio(profile: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, Any]:
    """Explainable LLM portfolio (falls back to heuristic if no API)."""
    if not USE_OPENAI:
        return _heuristic_portfolio(profile)
    try:
        prompt = {
            "role": "user",
            "content": json.dumps({
                "system_prompt": PORTFOLIO_PROMPT,
                "profile": profile,
                "market": market
            }, indent=2)
        }
        resp = _client.chat.completions.create(
            model="gpt-4o",
            messages=[prompt],
            temperature=0.25,
        )
        text = resp.choices[0].message.content.strip()
        return normalize_weights(_extract_json(text))
    except Exception:
        return _heuristic_portfolio(profile)

# -------------------------------
# Predictive ML portfolio
# -------------------------------
def generate_predictive_portfolio(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Machine-learning driven portfolio builder."""
    try:
        px = load_history()
        panel = build_signal_panel(px)
        df = build_training_set(px, panel, HORIZON_DAYS).dropna()
        if df.empty:
            return _heuristic_portfolio(profile)

        models, _ = train_xgb_like(df)
        last_date = panel.index.get_level_values(0).max()
        latest = panel.loc[last_date]
        import pandas as pd
        mu = pd.Series(predict_latest(models, latest), index=latest.index)
        mu = mu.clip(lower=mu.quantile(0.05), upper=mu.quantile(0.95))
        rets = px[latest.index].pct_change().dropna()
        cov = ledoit_wolf_cov(rets)
        w = mean_variance_opt(mu, cov, long_only=True)

        reasons = {}
        for t in latest.index:
            feats = latest.loc[t].sort_values(ascending=False).head(3)
            reasons[t] = "Top signals: " + ", ".join(f"{k}={v:.2f}" for k, v in feats.items())

        allocs = [
            {"ticker": t, "weight": float(w[t]), "reason": reasons.get(t, "Model-based selection")}
            for t in w.index if w[t] > 1e-6
        ]
        return normalize_weights({"allocations": allocs})
    except Exception:
        return _heuristic_portfolio(profile)
