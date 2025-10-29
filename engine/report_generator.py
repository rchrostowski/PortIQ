import os, io, datetime, tempfile
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.units import inch
from openai import OpenAI

from engine.market_data import get_macro_snapshot
from engine.metrics import summarize_portfolio

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------------------------------------------------
# AI Commentary Generator
# --------------------------------------------------------------
def ai_generate_commentary(profile, portfolio, macro, metrics):
    """Ask GPT to write an executive-level portfolio memo."""
    prompt = f"""
    You are PortIQ, an institutional investment strategist writing
    for a Goldman Sachs-level investment committee.

    Create a professional, board-ready report with the following structure:
    1. Executive Summary – 2 concise paragraphs summarizing objectives and approach.
    2. Market Environment – 1–2 paragraphs using provided macro data.
    3. Investment Rationale – 1 paragraph per holding explaining why it's included.
    4. Outlook & Risk Discussion – 1–2 paragraphs on risk factors and positioning logic.

    Use analytical, confident language and sound like an experienced CIO.

    --- CONTEXT ---
    Investor profile: {profile}
    Portfolio allocations: {portfolio.get('allocations', [])}
    Macro environment: {macro}
    Portfolio metrics: {metrics}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI commentary unavailable: {e})"

# --------------------------------------------------------------
# Chart builder
# --------------------------------------------------------------
def create_allocation_chart(portfolio):
    """Create pie chart for allocations and return an in-memory PNG."""
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
    """Generate a professional investment report PDF."""
    date_str = datetime.date.today().strftime("%B %d, %Y")
    file_path = tempfile.mktemp(suffix="_PortIQ_Report.pdf")

    # --- Gather data ---
    macro = get_macro_snapshot()
    metrics = summarize_portfolio(portfolio)
    commentary = ai_generate_commentary(profile, portfolio, macro, metrics)

    # --- Build PDF Layout ---
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom PortIQ styles (avoid name collisions)
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
        reason = a.get("reason", "").replace("\n", " ").strip()
        table_data.append([a["ticker"], f"{a['weight']*100:.1f}%", reason])

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

    # --- AI Commentary ---
    story.append(Paragraph("<b>Investment Committee Commentary</b>", styles["PortIQHeading2"]))
    for para in commentary.split("\n\n"):
        story.append(Paragraph(para.strip(), styles["PortIQBody"]))
        story.append(Spacer(1, 0.15 * inch))

    # --- Footer Disclaimer ---
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "This report was generated by the PortIQ AI system. "
        "It is for educational and illustrative purposes only and does not constitute "
        "investment advice or a solicitation to buy or sell any security.",
        styles["PortIQBody"]
    ))

    doc.build(story)
    return file_path
