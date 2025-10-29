import sys, os, json
import streamlit as st
import matplotlib.pyplot as plt

# ensure the engine package is on the path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from engine.profile_extractor import extract_profile
from engine.market_data import get_market_snapshot
from engine.portfolio_builder import generate_portfolio
from engine.validators import validate_tickers, normalize_weights, check_limits
from engine.report_generator import create_report
from engine.prompts import PROMPT_VERSION

st.set_page_config(page_title="PortIQ", page_icon="📈", layout="centered")

# --- UI HEADER ---
st.image("assets/portiq_logo.png", width=160)
st.title("PortIQ")
st.caption("Portfolio Intelligence, Built from You.")
st.markdown("---")

story = st.text_area(
    "Tell your investing story:",
    placeholder="I'm 24, saving for a home in 7 years, moderate risk, interested in tech and clean energy.",
    height=140,
)

if st.button("Generate Portfolio", use_container_width=True):
    if not story.strip():
        st.error("Please enter a story first.")
        st.stop()

    with st.spinner("Analyzing your story..."):
        profile = extract_profile(story)
        market = get_market_snapshot()
        portfolio = generate_portfolio(profile, market)

        # Validation
        portfolio = normalize_weights(portfolio)
        valid, invalid = validate_tickers(portfolio)
        portfolio["allocations"] = valid
        alerts = check_limits(portfolio)

        st.success("Portfolio generated successfully!")
        st.write("Prompt version:", PROMPT_VERSION)

        st.subheader("Investor Profile")
        st.json(profile)

        st.subheader("Recommended Portfolio")
        st.json(portfolio)

        if portfolio.get("allocations"):
            labels = [a["ticker"] for a in portfolio["allocations"]]
            sizes = [a["weight"] for a in portfolio["allocations"]]
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct="%1.1f%%")
            ax.axis("equal")
            st.pyplot(fig)

        if invalid:
            st.error(f"Invalid tickers removed: {invalid}")
        for a in alerts:
            st.warning(a)

        pdf_path = create_report(profile, portfolio)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF", f, file_name="PortIQ_Report.pdf")

st.markdown("---")
st.write(
    "© PortIQ 2025 — Educational use only. Not investment advice. [Terms](./1_Terms_of_Use) | [Privacy](./2_Privacy_Policy)"
)


