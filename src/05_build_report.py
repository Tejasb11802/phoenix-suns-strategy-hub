"""
Step 5: Build the 7 page business report as a PDF.

Output: outputs/Phoenix_Suns_Fan_Revenue_Strategy_Report.pdf
Every number comes from outputs/key_numbers.json and outputs/sql_results, so the report
always matches the SQL results and the Power BI dashboard.
"""
import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CH = OUT / "charts"
RES = OUT / "sql_results"
PDF = OUT / "Phoenix_Suns_Fan_Revenue_Strategy_Report.pdf"

PURPLE = colors.HexColor("#1D1160")
ORANGE = colors.HexColor("#E56020")
DARK = colors.HexColor("#252423")
GRAY = colors.HexColor("#63727A")
LIGHT = colors.HexColor("#F3F1F8")
W, H = letter
MARGIN = 0.7 * inch
CONTENT_W = W - 2 * MARGIN

TITLE = "Phoenix Suns Fan Revenue & Strategy Intelligence Report"
SUBTITLE = "Ticketing, Attendance, Fan Segmentation, and Commercial Opportunities"
DISCLAIMER = ("Independent demonstration project. Not affiliated with or endorsed by the Phoenix Suns. This report uses a "
              "simulated dataset designed to reflect realistic sports business scenarios. It does not describe actual team performance.")

H1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=PURPLE, spaceAfter=4)
LEAD = ParagraphStyle("Lead", fontName="Helvetica", fontSize=10, leading=14, textColor=GRAY, spaceAfter=10)
H2 = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=ORANGE, spaceBefore=8,
                    spaceAfter=4)
BODY = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=DARK)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=12, bulletIndent=0, spaceAfter=4)
CELL = ParagraphStyle("Cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=DARK)
CELL_B = ParagraphStyle("CellB", parent=CELL, fontName="Helvetica-Bold")
HEAD = ParagraphStyle("Head", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)
KPI_V = ParagraphStyle("KpiV", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=PURPLE, alignment=TA_CENTER)
KPI_L = ParagraphStyle("KpiL", fontName="Helvetica", fontSize=7.5, leading=10, textColor=GRAY, alignment=TA_CENTER)


def money(x):
    return f"${x / 1e6:,.1f}M" if abs(x) >= 1e6 else f"${x:,.0f}"


def bullets(items):
    return [Paragraph(t, BULLET, bulletText="\u2022") for t in items]


def chart(name, width=CONTENT_W, max_height=None):
    img = Image(str(CH / name))
    ratio = img.imageHeight / img.imageWidth
    w = width
    h = w * ratio
    if max_height and h > max_height:
        h = max_height
        w = h / ratio
    img.drawWidth, img.drawHeight = w, h
    img.hAlign = "CENTER"
    return img


def table(rows, col_widths, header=True, zebra=True):
    data = []
    for i, r in enumerate(rows):
        style = HEAD if (header and i == 0) else CELL
        data.append([c if not isinstance(c, str) else Paragraph(c, style) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    cmds = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D9D6E3"))]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), PURPLE))
    if zebra:
        for i in range(2 if header else 1, len(rows), 2):
            cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def kpi_row(items):
    """items: list of (value, label). One row of KPI tiles."""
    cells = [[Paragraph(v, KPI_V), Paragraph(l, KPI_L)] for v, l in items]
    w = CONTENT_W / len(items)
    t = Table([cells], colWidths=[w] * len(items), rowHeights=[0.72 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LINEBEFORE", (1, 0), (-1, 0), 3, colors.white),
                           ("LINEABOVE", (0, 0), (-1, 0), 2, ORANGE)]))
    return t


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, W, H, stroke=0, fill=1)
    canvas.setFillColor(ORANGE)
    canvas.rect(MARGIN, H - 3.35 * inch, 1.1 * inch, 0.09 * inch, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 31)
    for i, line in enumerate(["Phoenix Suns", "Fan Revenue & Strategy", "Intelligence Report"]):
        canvas.drawString(MARGIN, H - 4.05 * inch - i * 0.52 * inch, line)
    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(colors.HexColor("#D9D3E8"))
    canvas.drawString(MARGIN, H - 5.75 * inch, SUBTITLE)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(MARGIN, 2.3 * inch, "Tejas Bhanushali")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(MARGIN, 2.08 * inch, "MS Data Science, Analytics and Engineering, Arizona State University")
    canvas.drawString(MARGIN, 1.86 * inch, "Simulated 41 game home season  |  Python, SQL, Power BI")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#B8B2D0"))
    text = canvas.beginText(MARGIN, 1.1 * inch)
    text.setLeading(10)
    for line in ["Independent demonstration project. Not affiliated with or endorsed by the Phoenix Suns.",
                 "This report uses a simulated dataset designed to reflect realistic sports business scenarios",
                 "and to demonstrate an analytical approach. It does not describe actual team performance."]:
        text.textLine(line)
    canvas.drawText(text)
    canvas.restoreState()


def inner(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, H - 0.42 * inch, W, 0.42 * inch, stroke=0, fill=1)
    canvas.setFillColor(ORANGE)
    canvas.rect(0, H - 0.46 * inch, W, 0.04 * inch, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(MARGIN, H - 0.27 * inch, "PHOENIX SUNS FAN REVENUE & STRATEGY INTELLIGENCE REPORT")
    canvas.drawRightString(W - MARGIN, H - 0.27 * inch, f"{doc.page}")
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 6.5)
    cut = DISCLAIMER.index("This report")
    canvas.drawString(MARGIN, 0.42 * inch, DISCLAIMER[:cut].strip())
    canvas.drawString(MARGIN, 0.31 * inch, DISCLAIMER[cut:])
    canvas.restoreState()


def main():
    k = json.loads((OUT / "key_numbers.json").read_text(encoding="utf-8"))
    games = pd.read_csv(RES / "02_game_performance.csv")
    segval = pd.read_csv(RES / "04_segment_value.csv")
    ctype = pd.read_csv(RES / "07_campaign_type_performance.csv")
    conv = pd.read_csv(RES / "08_conversion_by_segment.csv")
    spon = pd.read_csv(RES / "09_sponsor_performance.csv")
    act = pd.read_csv(RES / "10_activation_performance.csv")
    recs = k["recommendations"]
    s = []

    # ---------------- Page 1: cover ----------------
    s.append(PageBreak())

    # ---------------- Page 2: executive summary ----------------
    s.append(Paragraph("Executive Summary", H1))
    s.append(Paragraph(
        "How a professional basketball organization could use fan, ticketing, attendance, marketing, and sponsorship "
        "data to improve revenue, retention, and engagement. Built on a simulated 41 game home season.", LEAD))
    s.append(kpi_row([(money(k["ticket_revenue"]), "Total ticket revenue"), (f"${k['avg_ticket_price']:.0f}", "Average ticket price"),
                      (f"{k['sell_through_pct']:.1f}%", "Sell-through rate"), (f"{k['attendance_rate_pct']:.1f}%", "Attendance rate")]))
    s.append(Spacer(1, 6))
    s.append(kpi_row([(f"{k['repeat_purchase_rate_pct']:.1f}%", "Repeat purchase rate"),
                      (f"{k['retention_rate_pct']:.1f}%", "Fan retention rate"),
                      (f"{k['campaign_conversion_pct']:.1f}%", "Campaign conversion"),
                      (f"{k['sponsor_engagements'] / 1e6:.1f}M", "Sponsor engagements")]))
    s.append(Paragraph("Key insights", H2))
    s += bullets(k["insights"])
    s.append(Paragraph("Main recommendations", H2))
    s += bullets([f"<b>{r['action']}.</b> {r['sizing']}" for r in recs[:4]])
    s.append(PageBreak())

    # ---------------- Page 3: ticketing and attendance ----------------
    s.append(Paragraph("Ticketing &amp; Attendance Insights", H1))
    s.append(Paragraph("Revenue trends, tickets sold versus attendance, the opponent and day of week effect, and no-shows.", LEAD))
    s.append(chart("01_sold_vs_attendance.png", max_height=2.3 * inch))
    s.append(Spacer(1, 4))
    s.append(chart("02_opponent_and_weekday.png", width=CONTENT_W * 0.82, max_height=2.1 * inch))
    s.append(Paragraph("What the data shows", H2))
    s += bullets([
        f"<b>Opponent and day of week drive demand.</b> {k['best_tier_day']} games average {k['best_tier_day_pct']:.0f}% "
        f"sell-through. {k['worst_tier_day']} games average {k['worst_tier_day_pct']:.0f}%.",
        f"<b>Sold is not the same as attended.</b> {k['no_show_pct']:.1f}% of tickets sold were never scanned, "
        f"{k['weekday_no_show_pct']:.1f}% on weekdays against {k['weekend_no_show_pct']:.1f}% on weekends.",
        f"<b>The weak spots are predictable.</b> {k['soft_games']} games hold {k['soft_unsold_share_pct']}% of unsold seats. "
        f"The lowest five by sell-through:",
    ])
    rows = [["Date", "Opponent", "Day", "Sell-through", "Unsold", "No-show"]]
    for r in games.sort_values("sell_through_pct").head(5).itertuples():
        rows.append([pd.Timestamp(r.game_date).strftime("%b %d"), r.opponent, r.weekday, f"{r.sell_through_pct:.1f}%",
                     f"{r.unsold_seats:,}", f"{r.no_show_pct:.1f}%"])
    s.append(table(rows, [0.8 * inch, 2.2 * inch, 1.1 * inch, 1.1 * inch, 0.9 * inch, 0.9 * inch]))
    s.append(PageBreak())

    # ---------------- Page 4: fan behavior and segmentation ----------------
    s.append(Paragraph("Fan Behavior &amp; Segmentation", H1))
    s.append(Paragraph(
        "Every fan is scored on recency, frequency, and monetary value, plus an engagement score built from attendance "
        "and campaign response. Rules then assign one segment per fan.", LEAD))
    s.append(chart("03_segment_size_vs_revenue.png", max_height=2.2 * inch))
    rows = [["Segment", "Fans", "Revenue", "Share", "Avg spend", "Avg games", "Engagement"]]
    for r in segval[segval["total_revenue"] > 0].itertuples():
        rows.append([r.segment, f"{int(r.fans):,}", money(r.total_revenue), f"{r.pct_of_revenue:.1f}%",
                     f"${r.avg_spend_per_fan:,.0f}", f"{r.avg_games:.1f}", f"{r.avg_engagement_score:.0f}"])
    s.append(Spacer(1, 4))
    s.append(table(rows, [1.9 * inch, 0.8 * inch, 0.95 * inch, 0.75 * inch, 0.95 * inch, 0.85 * inch, 0.9 * inch]))
    s.append(Paragraph("What the data shows", H2))
    s += bullets([
        f"<b>Best fans.</b> Season ticket members generate {k['member_revenue_share_pct']:.0f}% of ticket revenue. "
        f"High-value fans are the strongest non member group.",
        f"<b>At risk.</b> {k['insights'][2]}",
        f"<b>Ready for more.</b> {k['insights'][3]}",
        f"<b>Retention.</b> {k['repeat_purchase_rate_pct']:.0f}% of non member buyers purchased more than once, and "
        f"{k['retention_rate_pct']:.0f}% of first half buyers came back in the second half.",
    ])
    s.append(chart("04_spend_vs_engagement.png", width=CONTENT_W * 0.6, max_height=1.9 * inch))
    s.append(PageBreak())

    # ---------------- Page 5: marketing and conversion ----------------
    s.append(Paragraph("Marketing &amp; Conversion", H1))
    s.append(Paragraph("Twelve campaigns across email, SMS, push, paid social, and paid search, measured on response, "
                       "conversion, revenue, and ROI.", LEAD))
    s.append(chart("05_campaign_performance.png", max_height=2.5 * inch))
    s.append(Spacer(1, 4))
    s.append(chart("06_conversion_by_segment.png", width=CONTENT_W * 0.62, max_height=1.8 * inch))
    rows = [["Campaign type", "Campaigns", "Conversion", "Cost", "Revenue", "ROI"]]
    for r in ctype.itertuples():
        rows.append([r.campaign_type, str(r.campaigns), f"{r.conversion_rate_pct:.1f}%", money(r.cost),
                     money(r.revenue_generated), f"{r.roi:.1f}x"])
    s.append(Spacer(1, 4))
    s.append(table(rows, [1.9 * inch, 1.0 * inch, 1.1 * inch, 1.0 * inch, 1.1 * inch, 1.0 * inch]))
    s.append(Paragraph("What the data shows", H2))
    top2 = conv.iloc[1]
    s += bullets([
        f"<b>Owned channels win.</b> Email, SMS, and push returned {k['owned_roi']:.1f}x on cost against "
        f"{k['paid_roi']:.1f}x for paid media. {k['best_campaign']} was the best campaign at {k['best_campaign_roi']:.1f}x.",
        f"<b>Target by segment.</b> The {k['top_segment_conv']} segment converts at {k['top_segment_conv_pct']:.1f}% and "
        f"{top2['segment']} at {top2['conversion_rate_pct']:.1f}%, far above cold audiences.",
        "<b>Caveat.</b> Attribution is last-touch. It ranks campaigns and does not prove incremental lift. "
        "A holdout test would be the next step.",
    ])
    s.append(PageBreak())

    # ---------------- Page 6: sponsorship ----------------
    s.append(Paragraph("Sponsorship &amp; Commercial Insights", H1))
    s.append(Paragraph("Eight partners (fictional names) across six activation types, measured on reach, engagement, "
                       "and estimated partner value.", LEAD))
    s.append(chart("08_partner_engagement.png", width=CONTENT_W * 0.72, max_height=2.2 * inch))
    s.append(Spacer(1, 4))
    s.append(chart("07_activation_engagement.png", width=CONTENT_W * 0.72, max_height=2.2 * inch))
    rows = [["Activation", "Partners", "Impressions", "Engagements", "Eng rate", "Est. value"]]
    for r in act.itertuples():
        rows.append([r.activation_name, str(r.sponsors_using), f"{r.impressions / 1e6:,.1f}M", f"{r.engagements:,.0f}",
                     f"{r.engagement_rate_pct:.2f}%", money(r.estimated_value)])
    s.append(Spacer(1, 6))
    s.append(table(rows, [2.0 * inch, 0.85 * inch, 1.05 * inch, 1.15 * inch, 0.95 * inch, 1.1 * inch]))
    s.append(Paragraph("What the data shows", H2))
    s += bullets([
        f"<b>Interactive beats passive.</b> {k['top_activation']} engages {k['top_activation_rate']:.1f}% of the fans it "
        f"reaches against {k['low_activation_rate']:.2f}% for {k['low_activation']}.",
        f"<b>Partner spread is wide.</b> {k['top_sponsor']} leads with {k['top_sponsor_engagements'] / 1e6:.1f}M engagements. "
        f"{k['weak_sponsors'][0]} and {k['weak_sponsors'][1]} trail because their packages are signage and displays only.",
        f"<b>Cross-promotion.</b> In-arena activations scale with scanned attendance, so reducing no-shows on soft "
        f"games also lifts partner delivery. Total estimated partner value: {money(k['partner_value'])}.",
    ])
    s.append(PageBreak())

    # ---------------- Page 7: strategic recommendations ----------------
    s.append(Paragraph("Strategic Recommendations", H1))
    s.append(Paragraph("Six practical actions, each tied to a finding. Sizing figures are scenarios built from "
                       "observed averages and stated assumptions, not forecasts.", LEAD))
    rows = [["#", "Action", "What to do", "Sizing"]]
    for i, r in enumerate(recs, start=1):
        rows.append([str(i), Paragraph(r["action"], CELL_B), r["detail"], r["sizing"]])
    s.append(table(rows, [0.3 * inch, 1.65 * inch, 2.6 * inch, 2.55 * inch]))
    s.append(Paragraph("Implementation roadmap", H2))
    road = [["Phase", "Focus", "Actions"],
            ["Days 1 to 30", "Quick wins on owned channels",
             "Launch at-risk win-back and second game offers. Stand up the sold versus scanned report by game."],
            ["Days 31 to 60", "Product and pricing",
             "Pilot weekday bundles on the softest games. Send plan and premium offers to frequent buyers."],
            ["Days 61 to 90", "Renewals and partners",
             "Start usage outreach to low usage season ticket accounts. Add interactive activations to the weakest partner packages."]]
    s.append(table(road, [1.1 * inch, 1.9 * inch, 4.1 * inch]))
    s.append(Paragraph("Method and data", H2))
    s.append(Paragraph(
        "This project uses a simulated dataset designed to reflect realistic sports business scenarios and to "
        "demonstrate an analytical approach. The schedule is illustrative and no figure describes actual Phoenix Suns "
        "performance. Pipeline: Python and SQL for data generation, cleaning, validation, segmentation, and analysis. "
        "Power BI for the dashboard.", BODY))

    doc = BaseDocTemplate(str(PDF), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=0.75 * inch, bottomMargin=0.65 * inch, title=TITLE, author="Tejas Bhanushali",
                          subject=SUBTITLE)
    frame = Frame(MARGIN, 0.65 * inch, CONTENT_W, H - 0.75 * inch - 0.65 * inch, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=cover, autoNextPageTemplate="inner"),
                          PageTemplate(id="inner", frames=[frame], onPage=inner)])
    doc.build(s)
    print(f"  report written to outputs/{PDF.name} ({doc.page} pages)")


if __name__ == "__main__":
    print("Step 5: building PDF report")
    main()
