# app.py — PortIQ v0.4 "Modern Vivid" UI
import sys, os, json, uuid, datetime, pathlib
import streamlit as st
import matplotlib.pyplot as plt

# --- PATH SETUP ---
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# --- ENGINE IMPORTS ---
from engine.profile_extractor import extract_profile
from engine.market_data import get_market_snapshot, get_macro_snapshot
from engine.portfolio_builder import generate_portfolio, generate_predictive_portfolio
from engine.validators import validate_tickers, normalize_weights, check_limits
from engine.report_generator import create_report
from engine.prompts import PROMPT_VERSION
from engine.metrics import summarize_portfolio

# ---------------------------
# THEME / STYLES
# ---------------------------
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');

    :root{
      --bg: #0b1220;            /* deep blue */
      --card: rgba(255,255,255,0.06);
      --card-border: rgba(255,255,255,0.12);
      --text: #e9eefc;
      --muted: #a8b3cf;
      --brand: #6EE7F9;         /* cyan */
      --brand-2: #7C3AED;       /* violet */
      --accent: #22d3ee;
      --warn: #fbbf24;
      --danger: #fb7185;
      --success: #34d399;
    }

    html, body, [data-testid="stAppViewContainer"]{
      background: radial-gradient(1200px 800px at 20% 0%, #101734, #0b1220 60%);
      font-family: 'Inter', sans-serif !important;
      color: var(--text);
    }

    /* Hide default Streamlit chrome we don't need */
    header, footer { visibility: hidden; height: 0; }
    .e1fqkh3o3 { padding-top: 0 !important; }

    /* Hero */
    .hero {
      border: 1px solid var(--card-border);
      background: linear-gradient(160deg, rgba(124,58,237,0.18), rgba(34,211,238,0.08));
      border-radius: 24px; padding: 28px 28px;
      box-shadow: 0 6px 40px rgba(0,0,0,0.35), inset 0 0 60px rgba(124,58,237,0.12);
    }
    .hero h1 {
      font-weight: 800; font-size: 40px; line-height: 1.1; margin: 0 0 8px 0;
      background: linear-gradient(90deg, #e9eefc 0%, #b7c5ff 40%, #6EE7F9 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p { color: var(--muted); font-size: 15px; margin-top: 6px; }

    /* Glass cards */
    .card {
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 18px; padding: 18px 18px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }

    .badge{
      display: inline-flex; align-items:center; gap:8px;
      padding: 6px 10px; border-radius: 999px; font-size: 12px;
      color: #0b1220; font-weight: 700; background: linear-gradient(90deg, var(--brand), var(--brand-2));
      box-shadow: 0 6px 24px rgba(110,231,249,0.25);
    }

    /* Buttons */
    .stButton>button{
      width: 100%; border-radius: 12px; padding: 12px 16px; font-weight: 700;
      border: 1px solid rgba(255,255,255,0.12);
      background: linear-gradient(90deg, rgba(34,211,238,0.2), rgba(124,58,237,0.2));
      color: var(--text);
    }
    .stButton>button:hover{
      transform: translateY(-1px);
      border-color: rgba(255,255,255,0.3);
    }

    /* Tables */
    .styled-table thead th{
      background: #0f1833; color: #cfe3ff; font-weight: 700; font-size: 12px; letter-spacing: 0.02em;
      border-bottom: 1px solid var(--card-border);
    }
    .styled-table tbody td{ font-size: 13px; color: var(--text); }
    .muted{ color: var(--muted); }

    /* Metrics row */
    .metric{
      display:flex; flex-direction:column; gap:6px; padding:16px; border-radius:14px;
      background: rgba(124,58,237,0.09); border: 1px solid var(--card-border);
    }
    .metric .label{ font-size:12px; color: #cdd6f4; text-transform: uppercase; letter-spacing: .06em; }
    .metric .value{ font-size:20px; font-weight:800; }

    /* Pie chart container */
    .figure-card{ padding: 10px; border-radius: 18px; background: var(--card); border: 1px solid var(--card-border); }

    /* Sidebar polish */
    section[data-testid="stSidebar"]{
      background: #0a0f21 !important; border-right: 1px solid var(--card-border);
    }
    </style>
    """, unsafe_allow_html=True)

def metric_card(label, value):
    st.markdown(f"""
    <div class="metric">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="PortIQ", page_icon="📈", layout="wide")
inject_css()

# --- SIDEBAR NAVIGATION (native pages) ---
st.sidebar.title("PortIQ")
st.sidebar.page_link("app.py", label="🏠 Dashboard")
st.sidebar.page_link("pages/1_Terms_of_Use.py", label="📄 Terms of Use")
st.sidebar.page_link("pages/2_Privacy_Policy.py", label="🔒 Privacy Policy")
st.sidebar.markdown("---")
st.sidebar.info("v0.4 · Predictive ML + LLM")

# --- HEADER / HERO ---
c1, c2 = st.columns([1.15, 1])
with c1:
    st.markdown("""
    <div class="hero">
      <div class="badge">PORTFOLIO INTELLIGENCE</div>
      <h1>PortIQ — Build, Explain & Export<br/>Board-Ready Portfolios</h1>
      <p>Hybrid engine: predictive ML + explainable AI. Generate allocations, rationale,
         risk flags, macro context, and a premium PDF in minutes.</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("<div class='card'><span class='muted'>Status</span><br/><b>Ready</b> — market data and models load on demand.</div>", unsafe_allow_html=True)

st.markdown("")

# --- ENGINE SELECTOR & INPUT CARD ---
left, right = st.columns([1.1, 1])
with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Your Preferences", divider="rainbow")

    col1, col2 = st.columns(2)
    with col1:
        risk = st.slider("Risk Tolerance", 0, 10, 5, help="0 = conservative, 10 = aggressive")
    with col2:
        horizon = st.number_input("Investment Horizon (years)", 1, 50, 7)

    themes = st.multiselect(
        "Investment Themes",
        ["Technology","Energy","Healthcare","Dividends","Sustainability","AI","Emerging Markets"],
    )

    story = st.text_area(
        "Tell us your story",
        placeholder="I'm 24, saving for a home in 7 years, moderate risk, like tech and dividends.",
        height=120
    )
    story = (story or "").strip()
    story += f"\n\nRisk tolerance: {risk}/10. Horizon: {horizon} years."
    if themes: story += f"\nThemes: {', '.join(themes)}."

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Engine", divider="rainbow")
    mode = st.radio("Portfolio Engine", ["Predictive ML (Stocks + ETFs)", "Explainable LLM"], horizontal=False)
    st.caption("Predictive ML learns cross-sectional signals; Explainable LLM follows rules with rationale.")
    go = st.button("🚀 Generate Portfolio", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# --- RESULTS AREA ---
if go:
    if not story.strip():
        st.error("Please enter your investing story first.")
        st.stop()

    progress_bar = st.progress(0, text="Starting analysis...")

    with st.spinner("Extracting profile…"):
        progress_bar.progress(20, text="Extracting profile…")
        profile = extract_profile(story)

    with st.spinner("Fetching market…"):
        progress_bar.progress(45, text="Fetching market data…")
        market = get_market_snapshot()

    with st.spinner("Generating portfolio…"):
        progress_bar.progress(70, text="Generating portfolio…")
        if mode.startswith("Predictive"):
            portfolio = generate_predictive_portfolio(profile)
        else:
            portfolio = generate_portfolio(profile, market)

    # Validate & metrics
    portfolio = normalize_weights(portfolio)
    valid, invalid = validate_tickers(portfolio)
    portfolio["allocations"] = valid
    alerts = check_limits(portfolio)
    metrics = summarize_portfolio(portfolio)
    macro = get_macro_snapshot()
    progress_bar.progress(100, text="Done!")

    st.markdown("")

    # TABS
    t1, t2, t3, t4 = st.tabs(["Overview", "Holdings", "Macro & Rationale", "Export"])

    # --- OVERVIEW TAB ---
    with t1:
        top = st.columns([1.1, 1])
        with top[0]:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Portfolio Snapshot")
            run_id = str(uuid.uuid4())[:8]
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.caption(f"Run ID: {run_id} • {ts} • Prompt v{PROMPT_VERSION}")
            if invalid:
                st.error(f"Invalid tickers removed: {invalid}")
            for a in alerts:
                st.warning(a)

            # Pie chart
            if portfolio.get("allocations"):
                labels = [a["ticker"] for a in portfolio["allocations"]]
                sizes = [a["weight"] for a in portfolio["allocations"]]
                fig, ax = plt.subplots(figsize=(4.6, 4.6))
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
                ax.axis("equal")
                st.markdown("<div class='figure-card'>", unsafe_allow_html=True)
                st.pyplot(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with top[1]:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("Key Metrics")
            m1, m2 = st.columns(2)
            metric_card("Holdings", metrics.get("Holdings","—"))
            with m1:
                metric_card("Top-3 Concentration", metrics.get("Top-3 Concentration","—"))
                metric_card("Largest Position", metrics.get("Largest Position","—"))
            with m2:
                metric_card("Diversification Index", metrics.get("Diversification Index","—"))
                metric_card("Engine", "Predictive ML" if mode.startswith("Predictive") else "Explainable LLM")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- HOLDINGS TAB ---
    with t2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Allocations")
        allocs = portfolio.get("allocations", [])
        if not allocs:
            st.info("No allocations generated.")
        else:
            # Pretty table
            rows = "".join(
                f"<tr><td>{a['ticker']}</td><td style='text-align:right'>{a['weight']*100:.1f}%</td>"
                f"<td class='muted'>{(a.get('reason','') or '').replace('<','&lt;').replace('>','&gt;')}</td></tr>"
                for a in allocs
            )
            st.markdown(f"""
            <table class="styled-table" style="width:100%">
              <thead><tr><th>Ticker</th><th style='text-align:right'>Weight</th><th>Reason</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MACRO & RATIONALE TAB ---
    with t3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Macro Context")
        st.code(json.dumps(macro, indent=2), language="json")
        st.markdown("</div>", unsafe_allow_html=True)

        if portfolio.get("critique"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("AI Portfolio Review")
            st.markdown(portfolio["critique"])
            st.markdown("</div>", unsafe_allow_html=True)

    # --- EXPORT TAB ---
    with t4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Export & Session")
        pdf_path = create_report(profile, portfolio)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF Report", f, file_name="PortIQ_Report.pdf", use_container_width=True)
        if st.button("🔁 Regenerate with Same Inputs", use_container_width=True):
            st.experimental_rerun()
        if st.button("🗑️ Clear Session", use_container_width=True):
            st.session_state.clear()
            st.success("Session cleared.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("<div class='card muted'>Tip: Pick your engine and click <b>Generate Portfolio</b> to see the new UI.</div>", unsafe_allow_html=True)
