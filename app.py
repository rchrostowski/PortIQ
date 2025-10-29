import streamlit as st
import yfinance as yf
import openai, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="PortIQ", page_icon="📈")

st.title("PortIQ")
st.subheader("Portfolio Intelligence, Built from You.")
st.write("Tell your story below 👇")

user_story = st.text_area("Enter your investing story", height=150)

if st.button("Generate Portfolio"):
    with st.spinner("Analyzing..."):
        prompt = f"""
        The user wrote: "{user_story}".
        Return a JSON with goal, horizon, risk_tolerance, and 5 stock tickers with weights and reasons.
        """
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        st.json(resp.choices[0].message.content)
