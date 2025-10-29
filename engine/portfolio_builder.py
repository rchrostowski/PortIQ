import os, json, re
from typing import Dict, Any, List

# --- Optional OpenAI (used only if key is set). Otherwise we fall back offline.
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI = False
        _client = None

# Internal imports
from engine.validators import normalize_weights
# For predictive ML engine
from engine.config import HORIZON_DAYS
from engine.data import load_history
from engine.signals import build_signal_panel
from engine.model import build_training_set, train_xgb_like, predict_latest
from engine.risk import ledoit_wolf_cov
from engine.optimizer import mean_variance_opt

# ---------------------------
# Utilities
# ---------------------------
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
    """
    Offline rules-based portfolio when LLM is unavailable.
    Uses risk tolerance & themes to pick a diversified mix.
    """
    risk = profile.get("risk_tolerance", 5)
    themes = [t.lower() for t in (profile.get("themes") or [])]

    # base sleeves by risk
    if risk <= 3:
        core = [
            ("SCHD", 0.30, "Dividend income & quality"),
            ("BND",  0.30, "Core bond exposure"),
            ("VOO",  0.20, "Broad US equities"),
            ("XLU",  0.10, "Defensive utilities"),
            ("TLT",  0.10, "Duration hedge"),
        ]
    elif risk <= 6:
        core = [
            ("VOO",  0.35, "Broad US equities"),
            ("QQQ",  0.20, "Tech growth"),
            ("SCHD", 0.15, "Dividend & quality tilt"),
            ("TLT",  0.15, "Bond hedge"),
            ("XLE",  0.15, "Cyclical / energy"),
        ]
    else:
        core = [
            ("QQQ",  0.35, "High growth technology"),
            ("VOO",  0.25, "Core equities diversification"),
            ("IWM",  0.15, "Small-cap beta"),
            ("XLE",  0.15, "Energy cyclicality"),
            ("TLT",  0.10, "Crisis hedge"),
        ]

    # theme nudges (shift 5% from VOO if applicable)
    allocs = dict((t, w) for t, w, _ in core)
    reasons = dict((t, r) for t, _, r in core)

    def _nudge(from_t, to_t, delta, reason):
        if allocs.get(from_t, 0) >= delta:
            allocs[from_t] -= delta
            allocs[to_t] = allocs.get(to_t, 0) + delta
            reasons[to_t] = reason

    if "technology" in themes or "ai" in themes:
        _nudge("VOO", "SOXX", 0.05, "Semiconductors / AI supply chain")
    if "dividends" in themes:
        _nudge("VOO", "SCHD", 0.05, "Dividend growth tilt")
    if "energy" in themes:
        _nudge("VOO", "XLE", 0.05, "Energy overweight for cyclicality")
    if "emerging markets" in themes:
        _nudge("VOO", "EEM", 0.05, "EM diversification")

    # build output
    out = {"allocations": [
        {"ticker": k, "weight": float(v), "reason": reasons.get(k, "")} for k, v in allocs.items() if v > 0
    ]}
    return normalize_weights(out)

# ---------------------------
# Explainable LLM portfolio
# ---------------------------
PORTFOLIO_PROMPT = """
You are PortIQ, an AI portfolio constructor.

Goal: Given a user profile and market snapshot, return 5–8 US tradable tickers.
Rules:
1) Weights must sum to 1.0 in key "allocations".
2) Each item: {"ticker": "QQQ", "weight": 0.20, "reason": "..."}.
3) Respect risk:
   - Low (0–3): ~70% ETFs/bonds, ~30% equities
   - Medium (4–6): ~50% ETFs, ~50% equities
   - High (7–10): ~80% equities, ~20% ETFs/bonds
4) Favor ETFs at low risk, allow single-stocks at high risk.
5) Maintain sector diversification. Use real tickers only.
Return strictly valid JSON with key "allocations".
"""

def generate_portfolio(profile: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary explainable portfolio generator.
    - If OPENAI is available, use GPT-4o for rationale.
    - Otherwise, fall back to offline heuristic portfolio.
    """
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
        portfolio = _extract_json(text)
        return normalize_weights(portfolio)
    except Exception:
        # graceful fallback
        return _heuristic_portfolio(profile)

# ---------------------------
# Predictive ML portfolio
# ---------------------------
def generate_predictive_portfolio(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predictive engine:
    - Build features (momentum/vol/quality/value/size).
    - Train cross-sectional GBM on forward returns.
    - Estimate mu, build Ledoit-Wolf covariance.
    - Constrained mean-variance optimization.
    Returns allocations with simple explainability.
    """
    try:
        # 1) Data & features
        px = load_history()                      # uses universe.csv
        panel = build_signal_panel(px)
        df = build_training_set(px, panel, HORIZON_DAYS).dropna()
        if df.empty:
            return _heuristic_portfolio(profile)

        models, _ = train_xgb_like(df)

        # 2) Latest feature row per asset
        last_date = panel.index.get_level_values(0).max()
        latest = panel.loc[last_date]            # DataFrame: asset x features

        # 3) Predict expected returns (mu)
        import pandas as pd
        mu = pd.Series(predict_latest(models, latest), index=latest.index)
        mu = mu.clip(lower=mu.quantile(0.05), upper=mu.quantile(0.95))

        # 4) Risk model
        returns = px[latest.index].pct_change().dropna()
        cov = ledoit_wolf_cov(returns)

        # 5) Optimize
        w = mean_variance_opt(mu, cov, long_only=True)

        # 6) Explanations (top signals)
        reasons = {}
        for t in latest.index:
            feats = latest.loc[t].sort_values(ascending=False).head(3)
            reasons[t] = "Top signals: " + ", ".join(f"{k}={v:.2f}" for k, v in feats.items())

        allocs = [{"ticker": t, "weight": float(w[t]), "reason": reasons.get(t, "Model-driven selection")}
                  for t in w.index if w[t] > 1e-6]
        return normalize_weights({"allocations": allocs})

    except Exception:
        # Any failure → do not crash the app; deliver something reasonable
        return _heuristic_portfolio(profile)
