import os, json, openai
from dotenv import load_dotenv
from engine.prompts import PROFILE_PROMPT

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_profile(story: str) -> dict:
    prompt = PROFILE_PROMPT + f"\n\nUser story:\n{story}"
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2
    )
    text = resp.choices[0].message.content.strip()
    # try to coerce to JSON
    try:
        return json.loads(text)
    except Exception:
        return {"raw_profile_text": text}
