from openai import OpenAI
import os, json
from engine.prompts import PROFILE_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_profile(story: str) -> dict:
    prompt = PROFILE_PROMPT + f"\n\nUser story:\n{story}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    text = response.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except Exception:
        return {"raw_profile_text": text}


