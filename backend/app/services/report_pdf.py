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
MUTED = colors.Color(231 / 255, 233 / 255, 238 / 255, alpha=0.70)
CYAN = colors.HexColor("#38C7D7")


def _esc(s: str) -> str:
    """Basic safe text for ReportLab Paragraph (avoids broken markup)."""
    if s is None:
        return ""
    s = str(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


def _pct(score) -> str:
    """score is expected 0..1; returns '78%' or '—'."""
    try:
        x = float(score)
        if x != x:  # NaN check
            return "—"
        x = max(0.0, min(1.0, x))
        return f"{int(round(x * 100))}%"
    except Exception:
        return "—"


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
    small = ParagraphStyle(
        "small",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        textColor=MUTED,
        leading=13,
    )

    story = []

    # Header block
    story.append(Paragraph("ATS Compatibility Report", title))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", p))
    story.append(Paragraph(f"Filename: {_esc(payload.get('filename', ''))}", p))
    story.append(Spacer(1, 12))

    # Scores
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

    # Keyword analysis
    ka = payload.get("keyword_analysis", {}) or {}
    present = ka.get("present", []) or []
    missing = ka.get("missing", []) or []
    coverage = ka.get("coverage", 0)

    story.append(Paragraph("Keyword Analysis", h))
    try:
        cov_val = float(coverage)
        if cov_val != cov_val:
            cov_val = 0.0
    except Exception:
        cov_val = 0.0

    story.append(Paragraph(f"Coverage: {cov_val:.2f}%", p))
    story.append(Paragraph(f"Present: {_esc(', '.join(present[:20]) if present else '—')}", p))
    story.append(Paragraph(f"Missing: {_esc(', '.join(missing[:20]) if missing else '—')}", p))
    story.append(Spacer(1, 10))

    # ✅ NEW: Semantic context matches section
    semantic_matches = ka.get("semantic_matches", []) or []
    story.append(Paragraph("Semantic Context Matches", h))

    if not semantic_matches:
        story.append(Paragraph("—", p))
        story.append(Spacer(1, 10))
    else:
        # Table: Keyword | Match | Best Resume Line
        rows = [["Keyword", "Match", "Best Resume Line"]]
        for m in semantic_matches[:8]:
            keyword = _esc(m.get("keyword", "—"))
            match_pct = _pct(m.get("score"))
            best_line = _esc(m.get("best_line", "") or "—")
            # trim long lines for PDF readability
            if len(best_line) > 140:
                best_line = best_line[:140] + "…"
            rows.append([keyword, match_pct, best_line])

        sem_table = Table(rows, colWidths=[120, 60, 330])
        sem_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), CARD),
                    ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),
                    ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.Color(1, 1, 1, alpha=0.03)),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.Color(1, 1, 1, alpha=0.10)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(sem_table)
        story.append(Spacer(1, 10))

        # Also print semantic coverage if present
        sem_cov = ka.get("semantic_coverage", 0.0)
        try:
            sc = float(sem_cov)
            if sc != sc:
                sc = 0.0
        except Exception:
            sc = 0.0

        story.append(Paragraph(f"Semantic Coverage: {sc:.2f}%", small))
        story.append(Spacer(1, 10))

    # Formatting flags
    ff = payload.get("formatting_flags", {}) or {}
    story.append(Paragraph("Formatting & Structure Flags", h))
    ci = (ff.get("contact_info", {}) or {})
    sec = (ff.get("section_presence", {}) or {})
    miss = sec.get("missing_core_sections", []) or []

    story.append(Paragraph(f"Email detected: {bool(ci.get('email_detected', False))}", p))
    story.append(Paragraph(f"Phone detected: {bool(ci.get('phone_detected', False))}", p))
    story.append(Paragraph(f"LinkedIn detected: {bool(ci.get('linkedin_detected', False))}", p))
    story.append(Paragraph(f"Missing core sections: {_esc(', '.join(miss) if miss else '—')}", p))
    story.append(Spacer(1, 10))

    # Suggestions
    sug = (payload.get("suggestions", {}) or {}).get("items", []) or []
    story.append(Paragraph("Recommendations", h))
    if not sug:
        story.append(Paragraph("—", p))
    else:
        for item in sug[:10]:
            t = _esc(str(item.get("type", "tip")).upper())
            title_text = _esc(item.get("title", ""))
            detail_text = _esc(item.get("detail", ""))
            story.append(Paragraph(f"<font color='{CYAN.hexval()}'><b>{t}</b></font> — {title_text}", p))
            story.append(Paragraph(detail_text, p))
            story.append(Spacer(1, 6))

    # Dark background every page
    def on_page(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

        # subtle top glow
        canvas.setFillColor(colors.Color(56 / 255, 199 / 255, 215 / 255, alpha=0.10))
        canvas.rect(0, A4[1] - 70, A4[0], 70, fill=1, stroke=0)

        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
