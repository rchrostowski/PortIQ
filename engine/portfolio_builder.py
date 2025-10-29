from openai import OpenAI
import os, json, re
from dotenv import load_dotenv
import importlib.util, os, sys
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_root not in sys.path:
    sys.path.append(app_root)

spec = importlib.util.find_spec("engine.prompts")
if spec is None:
    raise ImportError(f"Cannot find engine.prompts in {sys.path}")
from engine.prompts import PORTFOLIO_PROMPT


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FALLBACK_PORTFOLIO = {
    "allocations": [
        {"ticker": "SPY", "weight": 0.40, "reason": "Broad U.S. market exposure"},
        {"ticker": "QQQ", "weight": 0.25, "reason": "Tech growth exposure"},
        {"ticker": "VOO", "weight": 0.15, "reason": "Low-cost S&P 500 ETF"},
        {"ticker": "TLT", "weight": 0.10, "reason": "Treasury bond diversification"},
        {"ticker": "XLE", "weight": 0.10, "reason": "Energy sector balance"},
    ]
}

def clean_json(text: str):
    """Extract JSON from possibly messy model output."""
    try:
        return json.loads(text)
    except Exception:
        # Try to extract JSON substring with regex
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
        + "\n\nMarket data snapshot:\n"
        + json.dumps(market, indent=2)
        + "\n\nReturn ONLY valid JSON strictly following the format."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25
        )
        text = response.choices[0].message.content.strip()
        portfolio = clean_json(text)

        # guarantee allocations exist
        if "allocations" not in portfolio or not portfolio["allocations"]:
            return FALLBACK_PORTFOLIO
        return portfolio
    except Exception as e:
        print("LLM call failed:", e)
        return FALLBACK_PORTFOLIO
