from engine.profile_extractor import extract_profile
from engine.market_data import get_market_snapshot
from engine.portfolio_builder import generate_portfolio
from engine.validators import validate_tickers, normalize_weights, check_limits
from engine.report_generator import create_report
from engine.prompts import PROMPT_VERSION


LOGO_PATH = "assets/portiq_logo.png"

st.set_page_config(page_title="PortIQ", page_icon="📈", layout="centered")

col_logo, col_title = st.columns([1,3])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=140)
with col_title:
    st.title("PortIQ")
    st.caption("Portfolio Intelligence, Built from You.")

st.markdown("#### Tell your investing story")
story = st.text_area(
    "Do not include sensitive information (SSNs, account numbers, addresses).",
    placeholder="I'm 24, saving for a home in 7 years, moderate risk, I like tech and dividends.",
    height=140
)

left, right = st.columns(2)
with left:
    if st.button("Generate Portfolio", use_container_width=True):
        if not story.strip():
            st.error("Please enter your story.")
        else:
            with st.spinner("Analyzing your story..."):
                profile = extract_profile(story)
                market = get_market_snapshot()
                portfolio = generate_portfolio(profile, market)

                # normalize & validate
                if isinstance(portfolio, dict) and "allocations" in portfolio:
                    portfolio = normalize_weights(portfolio)
                valid, invalid = validate_tickers(portfolio if isinstance(portfolio, dict) else {"allocations":[]})
                portfolio["allocations"] = valid
                alerts = check_limits(portfolio)

                st.success("Portfolio generated.")
                st.write("**Prompt version:**", PROMPT_VERSION)

                st.subheader("Investor Profile")
                st.json(profile)

                st.subheader("Recommended Portfolio")
                st.json(portfolio)

                # pie chart
                if portfolio.get("allocations"):
                    labels = [a["ticker"] for a in portfolio["allocations"]]
                    sizes  = [a["weight"] for a in portfolio["allocations"]]
                    fig, ax = plt.subplots()
                    ax.pie(sizes, labels=labels, autopct="%1.1f%%")
                    ax.axis("equal")
                    st.pyplot(fig)

                if invalid:
                    st.error(f"Invalid tickers removed: {invalid}")
                for a in alerts:
                    st.warning(a)

                # PDF download
                pdf_path = create_report(profile, portfolio)
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Download PDF", f, file_name="PortIQ_Report.pdf", use_container_width=True)

with right:
    st.markdown("##### What happens")
    st.write("- PortIQ extracts your **profile** (goal, horizon, risk, themes).")
    st.write("- It snapshots **market data** for context.")
    st.write("- It builds an **explainable portfolio** with reasons per ticker.")
    st.markdown("---")
    st.write("**Disclaimer:** Educational use only. Not investment advice.")

st.markdown("---")
st.write("© PortIQ 2025 · [Terms of Use](./1_Terms_of_Use) · [Privacy Policy](./2_Privacy_Policy)")

