import os, json, re
from typing import Dict, Any

from engine.prompts import PROFILE_PROMPT

# optional OpenAI
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI = False
        _client = None


def _parse_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


def _heuristic_extract(story: str) -> Dict[str, Any]:
    """Offline fallback: quick keyword-based extraction."""
    s = story.lower()
    risk = 5
    if any(k in s for k in ["aggressive", "high risk", "growth", "venture"]):
        risk = 8
    elif any(k in s for k in ["conservative", "safe", "low risk", "income"]):
        risk = 3

    horizon = 7
    for n in range(2, 51):
        if f"{n} year" in s:
            horizon = n
            break

    themes = []
    for t in ["technology", "energy", "healthcare", "dividend", "ai", "emerging", "crypto"]:
        if t in s:
            themes.append(t.capitalize())

    return {
        "risk_tolerance": risk,
        "investment_horizon": horizon,
        "themes": themes,
        "objectives": ["Growth"] if risk >= 6 else ["Balanced"],
        "notes": story[:250] + ("..." if len(story) > 250 else "")
    }


def extract_profile(story: str) -> Dict[str, Any]:
    """Primary extractor with OpenAI or offline fallback."""
    if not story or not story.strip():
        return _heuristic_extract("")

    if not USE_OPENAI:
        return _heuristic_extract(story)

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROFILE_PROMPT},
                {"role": "user", "content": story}
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        data = _parse_json(text)
        if not data:
            data = _heuristic_extract(story)
        return data
    except Exception:
        return _heuristic_extract(story)
