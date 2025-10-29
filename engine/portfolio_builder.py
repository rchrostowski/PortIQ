from openai import OpenAI
import os, json
from dotenv import load_dotenv
from engine.prompts import PORTFOLIO_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_portfolio(profile: dict, market: dict) -> dict:
    prompt = (
        PORTFOLIO_PROMPT
        + "\n\nInvestor profile:\n"
        + json.dumps(profile, ensure_ascii=False)
        + "\n\nMarket data:\n"
        + json.dumps(market, ensure_ascii=False)
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    text = response.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except Exception:
        return {"raw_portfolio_text": text}
