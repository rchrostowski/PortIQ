from openai import OpenAI
import os, json
from dotenv import load_dotenv
import importlib.util, os, sys

# ensure the app root is in sys.path
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_root not in sys.path:
    sys.path.append(app_root)

spec = importlib.util.find_spec("engine.prompts")
if spec is None:
    raise ImportError(f"Cannot find engine.prompts in {sys.path}")
from engine.prompts import PROFILE_PROMPT


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_profile(story: str) -> dict:
    prompt = PROFILE_PROMPT + f"\n\nUser story:\n{story}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    text = response.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except Exception:
        return {"raw_profile_text": text}

