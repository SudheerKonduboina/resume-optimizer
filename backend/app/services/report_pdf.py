from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Theme colors (luxury dark + cyan accents similar vibe)
BG = colors.HexColor("#070A12")
CARD = colors.HexColor("#0B0F1A")
TEXT = colors.HexColor("#E7E9EE")
MUTED = colors.Color(231/255, 233/255, 238/255, alpha=0.70)
CYAN = colors.HexColor("#38C7D7")
PURPLE = colors.HexColor("#7C34EA")
BLUE = colors.HexColor("#2E43F3")
GOLD = colors.HexColor("#D4AF37")

def build_pdf(payload: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="ATS Report",
        author="ATS Resume Optimizer",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=TEXT,
        spaceAfter=10,
    )
    h = ParagraphStyle(
        "h",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=TEXT,
        spaceBefore=10,
        spaceAfter=6,
    )
    p = ParagraphStyle(
        "p",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        textColor=MUTED,
        leading=14,
    )

    story = []

    # Header block
    story.append(Paragraph("ATS Compatibility Report", title))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", p))
    story.append(Paragraph(f"Filename: {payload.get('filename','')}", p))
    story.append(Spacer(1, 12))

    scores = payload.get("scores", {}) or {}
    total = scores.get("total", 0)
    bd = (scores.get("breakdown", {}) or {})
    kw = bd.get("keywords", 0)
    fmt = bd.get("formatting", 0)
    cont = bd.get("content", 0)

    # KPI table
    kpi = Table(
        [
            ["Overall Score", "Keywords", "Formatting", "Content"],
            [f"{total}/100", f"{kw}/45", f"{fmt}/25", f"{cont}/30"],
        ],
        colWidths=[130, 120, 120, 120],
    )
    kpi.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CARD),
                ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, 1), colors.Color(1, 1, 1, alpha=0.04)),
                ("TEXTCOLOR", (0, 1), (-1, 1), TEXT),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 12),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.Color(1, 1, 1, alpha=0.12)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi)
    story.append(Spacer(1, 14))

    # Keywords
    ka = payload.get("keyword_analysis", {}) or {}
    present = ka.get("present", []) or []
    missing = ka.get("missing", []) or []
    coverage = ka.get("coverage", 0)

    story.append(Paragraph("Keyword Analysis", h))
    story.append(Paragraph(f"Coverage: {coverage:.2f}", p))
    story.append(Paragraph(f"Present: {', '.join(present[:18]) if present else '—'}", p))
    story.append(Paragraph(f"Missing: {', '.join(missing[:18]) if missing else '—'}", p))
    story.append(Spacer(1, 10))

    # Formatting flags
    ff = payload.get("formatting_flags", {}) or {}
    story.append(Paragraph("Formatting & Structure Flags", h))
    ci = (ff.get("contact_info", {}) or {})
    sec = (ff.get("section_presence", {}) or {})
    miss = sec.get("missing_core_sections", []) or []

    story.append(Paragraph(f"Email detected: {ci.get('email_detected', False)}", p))
    story.append(Paragraph(f"Phone detected: {ci.get('phone_detected', False)}", p))
    story.append(Paragraph(f"LinkedIn detected: {ci.get('linkedin_detected', False)}", p))
    story.append(Paragraph(f"Missing core sections: {', '.join(miss) if miss else '—'}", p))
    story.append(Spacer(1, 10))

    # Suggestions
    sug = (payload.get("suggestions", {}) or {}).get("items", []) or []
    story.append(Paragraph("Recommendations", h))
    if not sug:
        story.append(Paragraph("—", p))
    else:
        for item in sug[:10]:
            t = str(item.get("type", "tip")).upper()
            story.append(Paragraph(f"<font color='{CYAN.hexval()}'><b>{t}</b></font> — {item.get('title','')}", p))
            story.append(Paragraph(f"{item.get('detail','')}", p))
            story.append(Spacer(1, 6))

    # Draw dark background on every page
    def on_page(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        # subtle top gradient strip illusion
        canvas.setFillColor(colors.Color(46/255, 67/255, 243/255, alpha=0.10))
        canvas.rect(0, A4[1]-70, A4[0], 70, fill=1, stroke=0)
        canvas.setFillColor(colors.Color(124/255, 52/255, 234/255, alpha=0.08))
        canvas.rect(0, A4[1]-55, A4[0], 55, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
