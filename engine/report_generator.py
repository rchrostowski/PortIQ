from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

def create_report(profile: dict, portfolio: dict, filename="PortIQ_Report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("<b>PortIQ Investment Summary</b>", styles["Title"])
    date = Paragraph(datetime.now().strftime("%B %d, %Y"), styles["Normal"])
    elements += [title, date, Spacer(1, 20)]

    elements.append(Paragraph("<b>Investor Profile</b>", styles["Heading2"]))
    for k, v in profile.items():
        elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>Recommended Portfolio</b>", styles["Heading2"]))
    data = [["Ticker", "Weight", "Rationale"]] + [
        [a["ticker"], f"{a['weight']*100:.1f}%", a["reason"]] for a in portfolio["allocations"]
    ]
    table = Table(data, colWidths=[80, 80, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#244B9A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    disclaimer = Paragraph(
        "Educational use only. Not investment advice. "
        "PortIQ is not a broker/dealer or investment adviser.",
        styles["Italic"]
    )
    elements.append(disclaimer)

    doc.build(elements)
    return filename
