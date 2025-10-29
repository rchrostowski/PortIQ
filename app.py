import sys, os, json
import streamlit as st
import matplotlib.pyplot as plt

# --- PATH SETUP ---
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# --- ENGINE IMPORTS ---
from engine.profile_extractor import extract_profile
from engine.market_data import get_market_snapshot
from engine.portfolio_builder import generate_portfolio
from engine.validators import validate_tickers, normalize_weights, check_limits
from engine.report_generator import create_report
from engine.prompts import PROMPT_VERSION

# --- PAGE CONFIG ---
st.set_page_config(page_title="PortIQ", page_icon="📈", layout="centered")

# --- HEADER ---
LOGO_PATH = "assets/portiq_logo.png"
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=160)
st.title("PortIQ")
st.warning("⚠️ Educational use only — not investment advice.")
st.caption("Portfolio Intelligence, Built from You.")
st.markdown("---")

# --- USER INPUT CONTROLS ---
st.subheader("Set Your Investment Preferences")

col1, col2 = st.columns(2)
with col1:
    risk = st.slider("Risk Tolerance (0 = low, 10 = high)", 0, 10, 5)
with col2:
    horizon = st.number_input("Investment Horizon (years)", 1, 50, 7)

themes = st.multiselect(
    "Preferred Investment Themes",
    ["Technology", "Energy", "Healthcare", "Dividends", "Sustainability", "AI", "Emerging Markets"],
)
if themes:
    st.caption(f"Selected themes: {', '.join(themes)}")

st.markdown("#### Tell your investing story")
story = st.text_area(
    "Describe your goals, time horizon, risk comfort, etc.",
    placeholder="I'm 24, saving for a home in 7 years, moderate risk, like tech and dividends.",
    height=140,
)

# Append structured inputs to story
story = (
    story
    + f"\n\nRisk tolerance: {risk}/10."
    + f"\nInvestment horizon: {horizon} years."
    + (f"\nThemes: {', '.join(themes)}." if themes else "")
)

st.markdown("---")

# --- MAIN ACTION ---
if st.button("🚀 Generate Portfolio", use_container_width=True):
    if not story.strip():
        st.error("Please enter your investing story first.")
        st.stop()

    # Progress indicator
    progress_text = "Starting analysis..."
    progress_bar = st.progress(0, text=progress_text)

    with st.spinner("Analyzing your story..."):
        progress_bar.progress(20, text="Extracting profile...")
        profile = extract_profile(story)

        progress_bar.progress(50, text="Fetching market data...")
        market = get_market_snapshot()

        progress_bar.progress(80, text="Generating portfolio...")
        portfolio = generate_portfolio(profile, market)

        # --- VALIDATION ---
        portfolio = normalize_weights(portfolio)
        valid, invalid = validate_tickers(portfolio)
        portfolio["allocations"] = valid
        alerts = check_limits(portfolio)

        progress_bar.progress(100, text="Done!")

        # --- RESULTS ---
        st.success("✅ Portfolio generated successfully!")
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

# --- DELETE DATA ---
if st.button("🗑️ Delete my data for this session", use_container_width=True):
    st.session_state.clear()
    st.success("All session data cleared from memory.")

# --- FOOTER ---
st.info(
    "PortIQ outputs are AI-generated and may contain errors. "
    "No investment recommendations or brokerage services are provided."
)
st.write(
    "© PortIQ 2025 — Educational use only. [Terms of Use](./1_Terms_of_Use) | [Privacy Policy](./2_Privacy_Policy)"
)



