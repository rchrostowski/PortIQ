import os, io, datetime, tempfile
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.units import inch
from engine.market_data import get_macro_snapshot
from engine.metrics import summarize_portfolio


# --------------------------------------------------------------
# Local text generator (offline "AI" commentary)
# --------------------------------------------------------------
def build_local_commentary(profile, portfolio, macro, metrics):
    """Generate structured human-readable commentary without API calls."""
    risk = profile.get("risk_tolerance", "N/A")
    horizon = profile.get("investment_horizon", "N/A")
    themes = profile.get("themes", [])

    # ---- Executive summary ----
    summary = [
        f"This portfolio has been constructed to align with a risk tolerance of {risk} "
        f"and an investment horizon of approximately {horizon} years.",
        "The allocations reflect a diversified approach designed to balance growth and stability "
        "while maintaining exposure across major asset classes and economic sectors."
    ]

    # ---- Market environment ----
    market_context = [
        f"Current macro environment snapshot: {macro}.",
        "The portfolio maintains a neutral-to-moderate risk stance given the recent market conditions. "
        "Exposure to equities provides upside potential while bond and defensive holdings act as volatility dampeners."
    ]

    # ---- Rationale for each holding ----
    holdings_text = []
    for a in portfolio.get("allocations", []):
        holdings_text.append(
            f"{a['ticker']} ({a['weight']*100:.1f}%): {a.get('reason','No reason provided.')}"
        )

    # ---- Outlook & risk discussion ----
    outlook = [
        "Overall, the portfolio is positioned to capture market upside while preserving capital "
        "through diversified exposures. The largest weights represent broad market and technology sectors, "
        "which historically drive performance over long horizons.",
        "Key risks include macroeconomic slowdowns, inflation persistence, and interest-rate sensitivity. "
        "Periodic rebalancing is recommended to maintain strategic weights."
    ]

    return {
        "Executive Summary": "\n".join(summary),
        "Market Environment": "\n".join(market_context),
        "Investment Rationale": "\n".join(holdings_text),
        "Outlook & Risks": "\n".join(outlook),
    }


# --------------------------------------------------------------
# Chart builder
# --------------------------------------------------------------
def create_allocation_chart(portfolio):
    allocs = portfolio.get("allocations", [])
    labels = [a["ticker"] for a in allocs]
    sizes = [a["weight"] for a in allocs]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


# --------------------------------------------------------------
# PDF builder
# --------------------------------------------------------------
def create_report(profile, portfolio):
    """Generate a professional investment report PDF (no API required)."""
    date_str = datetime.date.today().strftime("%B %d, %Y")
    file_path = tempfile.mktemp(suffix="_PortIQ_Report.pdf")

    # --- Gather data ---
    macro = get_macro_snapshot()
    metrics = summarize_portfolio(portfolio)
    commentary = build_local_commentary(profile, portfolio, macro, metrics)

    # --- Build PDF Layout ---
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="PortIQHeading1", fontSize=18, leading=22, spaceAfter=14))
    styles.add(ParagraphStyle(name="PortIQHeading2", fontSize=14, leading=18, spaceAfter=10))
    styles.add(ParagraphStyle(name="PortIQBody", fontSize=11, leading=14))

    story = []

    # --- Cover Page Header ---
    story.append(Paragraph("<b>PortIQ Investment Report</b>", styles["PortIQHeading1"]))
    story.append(Paragraph(f"Date: {date_str}", styles["PortIQBody"]))
    story.append(Paragraph("Confidential — For Client Use Only", styles["PortIQBody"]))
    story.append(Spacer(1, 0.4 * inch))

    # --- Investor Profile ---
    story.append(Paragraph("<b>Investor Profile</b>", styles["PortIQHeading2"]))
    story.append(Paragraph(str(profile).replace("{","").replace("}",""), styles["PortIQBody"]))
    story.append(Spacer(1, 0.3 * inch))

    # --- Allocation Chart ---
    buf = create_allocation_chart(portfolio)
    story.append(Image(buf, width=4*inch, height=4*inch))
    story.append(Spacer(1, 0.3 * inch))

    # --- Allocation Table ---
    story.append(Paragraph("<b>Portfolio Allocation</b>", styles["PortIQHeading2"]))
    allocs = portfolio.get("allocations", [])
    table_data = [["Ticker", "Weight", "Reason"]]
    for a in allocs:
        table_data.append([a["ticker"], f"{a['weight']*100:.1f}%", a.get("reason", "")])

    table = Table(table_data, colWidths=[1.2*inch, 1*inch, 3.3*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,1), (1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4 * inch))

    # --- Commentary Sections ---
    for section, text in commentary.items():
        story.append(Paragraph(f"<b>{section}</b>", styles["PortIQHeading2"]))
        for para in text.split("\n"):
            story.append(Paragraph(para.strip(), styles["PortIQBody"]))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))

    # --- Footer Disclaimer ---
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "This report was generated locally by PortIQ AI. "
        "It is for educational and illustrative purposes only and does not constitute "
        "investment advice or a solicitation to buy or sell any security.",
        styles["PortIQBody"]
    ))

    doc.build(story)
    return file_path
