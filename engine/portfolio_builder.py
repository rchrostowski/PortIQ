from openai import OpenAI
import os, json, re
from engine.prompts import PORTFOLIO_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FALLBACK_PORTFOLIO = {
    "allocations": [
        {"ticker": "SPY", "weight": 0.4, "reason": "Broad U.S. market exposure"},
        {"ticker": "QQQ", "weight": 0.25, "reason": "Tech sector growth"},
        {"ticker": "VOO", "weight": 0.15, "reason": "Low-cost S&P 500 ETF"},
        {"ticker": "TLT", "weight": 0.1, "reason": "Bond diversification"},
        {"ticker": "XLE", "weight": 0.1, "reason": "Energy sector balance"},
    ]
}

def _extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return FALLBACK_PORTFOLIO
        return FALLBACK_PORTFOLIO

def generate_portfolio(profile: dict, market: dict) -> dict:
    prompt = (
        PORTFOLIO_PROMPT
        + "\n\nInvestor profile:\n"
        + json.dumps(profile, indent=2)
        + "\n\nMarket snapshot:\n"
        + json.dumps(market, indent=2)
        + "\n\nReturn ONLY valid JSON."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
        )
        text = response.choices[0].message.content.strip()
        portfolio = _extract_json(text)
        if not portfolio.get("allocations"):
            return FALLBACK_PORTFOLIO
        return portfolio
    except Exception as e:
        print("Portfolio generation failed:", e)
        return FALLBACK_PORTFOLIO

