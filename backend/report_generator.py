"""
DisasterMind — PDF Report Generator
Produces NDMA-ready A4 situation reports using ReportLab.
Returns PDF bytes via BytesIO — no file system writes needed.
"""

import io
from datetime import datetime, timezone

from reportlab.lib                   import colors
from reportlab.lib.enums             import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes         import A4
from reportlab.lib.styles            import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units             import mm
from reportlab.platypus              import (
    BaseDocTemplate, Frame, HRFlowable, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Colour palette (mirrors tokens.css) ─────────────────────────────────────
NAVY        = colors.HexColor("#0F1923")
WHITE       = colors.white
LIGHT_GREY  = colors.HexColor("#F8F9FA")
MID_GREY    = colors.HexColor("#E2E8F0")
DARK_GREY   = colors.HexColor("#4A5568")
MUTED       = colors.HexColor("#718096")
ACCENT_BLUE = colors.HexColor("#1D4ED8")
TEAL        = colors.HexColor("#0D9488")

RISK_COLORS = {
    "CRITICAL": colors.HexColor("#C41E3A"),
    "HIGH":     colors.HexColor("#D4711A"),
    "MODERATE": colors.HexColor("#B45309"),
    "LOW":      colors.HexColor("#166534"),
}
RISK_BG = {
    "CRITICAL": colors.HexColor("#FFF0F0"),
    "HIGH":     colors.HexColor("#FFF7ED"),
    "MODERATE": colors.HexColor("#FFFBEB"),
    "LOW":      colors.HexColor("#F0FDF4"),
}

# ── Styles ────────────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()

def _style(name, **kwargs) -> ParagraphStyle:
    s = ParagraphStyle(name, parent=_styles["Normal"], **kwargs)
    return s

S_WORDMARK     = _style("wordmark",   fontName="Helvetica-Bold", fontSize=18, textColor=WHITE,    leading=22)
S_REPORT_LABEL = _style("rpt_label",  fontName="Helvetica",      fontSize=9,  textColor=MID_GREY, leading=12)
S_CONF         = _style("conf",       fontName="Helvetica-Bold", fontSize=8,  textColor=MID_GREY, leading=10)
S_SECTION      = _style("section",    fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,     leading=14, spaceBefore=10)
S_BODY         = _style("body",       fontName="Helvetica",      fontSize=9,  textColor=DARK_GREY, leading=13)
S_RISK_LABEL   = _style("risk_label", fontName="Helvetica-Bold", fontSize=20, leading=24)
S_META         = _style("meta",       fontName="Helvetica",      fontSize=8,  textColor=MUTED,    leading=11)
S_ML_BOX       = _style("ml_box",     fontName="Helvetica",      fontSize=9,  textColor=ACCENT_BLUE, leading=13)
S_WARNING      = _style("warning",    fontName="Helvetica-Bold", fontSize=9,  textColor=WHITE,    leading=13)
S_FOOTER       = _style("footer",     fontName="Helvetica",      fontSize=7,  textColor=MUTED,    leading=10, alignment=TA_CENTER)
S_CELL         = _style("cell",       fontName="Helvetica",      fontSize=8,  textColor=DARK_GREY, leading=11)
S_CELL_BOLD    = _style("cell_bold",  fontName="Helvetica-Bold", fontSize=8,  textColor=NAVY,     leading=11)


def generate_pdf(analysis: dict) -> bytes:
    """
    Convert a full analysis dict to NDMA situation report PDF bytes.

    Parameters
    ----------
    analysis : dict returned by agent.run_disaster_analysis()

    Returns
    -------
    bytes — PDF file content
    """
    report    = analysis.get("situation_report", {})
    ml        = analysis.get("ml_prediction",    {})
    raw       = analysis.get("raw_data",         {})
    region    = analysis.get("region",           "Unknown Region")
    timestamp = datetime.now(timezone.utc).strftime("%d %B %Y  %H:%M UTC")
    risk      = report.get("risk_level", "HIGH")
    risk_color = RISK_COLORS.get(risk, DARK_GREY)
    risk_bg    = RISK_BG.get(risk, LIGHT_GREY)

    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=10 * mm, bottomMargin=14 * mm,
    )

    frame = Frame(MARGIN, 14 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 24 * mm, id="main")

    def _header_footer(canvas, doc):
        canvas.saveState()
        # ── header bar ──
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(MARGIN, PAGE_H - 13 * mm, "DisasterMind")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GREY)
        canvas.drawString(MARGIN, PAGE_H - 18 * mm, "AUTONOMOUS DISASTER RESPONSE INTELLIGENCE")
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(MID_GREY)
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13 * mm, "CONFIDENTIAL — FOR OFFICIAL USE")
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 18 * mm, timestamp)
        # ── footer ──
        canvas.setFillColor(MID_GREY)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(
            PAGE_W / 2, 8 * mm,
            f"Generated by DisasterMind AI  ·  NDMA Situation Report  ·  {timestamp}"
        )
        canvas.drawRightString(PAGE_W - MARGIN, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_header_footer)])

    story = []

    def _spacer(h=4):
        story.append(Spacer(1, h * mm))

    def _hr():
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))

    # ── Section 1: Title ─────────────────────────────────────────────────
    story.append(Paragraph(f"SITUATION REPORT — {region.upper()}", _style("title1", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, leading=16)))
    _spacer(1)
    story.append(Paragraph(f"Issued: {timestamp}", S_META))
    story.append(Paragraph("Document classification: FOR OFFICIAL USE ONLY", S_META))
    _spacer(3)
    _hr()
    _spacer(3)

    # ── Section 2: Risk Level Banner ─────────────────────────────────────
    risk_score = report.get("risk_score", "N/A")
    risk_table = Table(
        [[Paragraph(risk, _style("rl", fontName="Helvetica-Bold", fontSize=22, textColor=risk_color, leading=26)),
          Paragraph(f"{risk_score}/10", _style("rs", fontName="Courier-Bold", fontSize=18, textColor=risk_color, leading=22, alignment=TA_RIGHT))]],
        colWidths=[(PAGE_W - 2*MARGIN) * 0.7, (PAGE_W - 2*MARGIN) * 0.3],
    )
    risk_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), risk_bg),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
        ("LINEAFTER",    (0,0), (0,-1),  0, WHITE),
        ("LINEBEFORE",   (0,0), (0,-1),  4, risk_color),
    ]))
    story.append(risk_table)
    _spacer(3)

    # ── Section 3: ML Validation ──────────────────────────────────────────
    flood_prob = ml.get("flood_probability", 0)
    severity   = ml.get("severity_label", "N/A")
    ml_text    = (
        f"<b>ML Validated</b>  ·  Flood probability: {flood_prob:.0%}  ·  "
        f"Severity prediction: {severity}  ·  "
        f"Models: XGBoost Flood Classifier + Random Forest Severity Scorer  ·  "
        f"Confidence: {ml.get('ml_confidence', 'N/A')}"
    )
    ml_table = Table([[Paragraph(ml_text, S_ML_BOX)]])
    ml_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ("LINEBEFORE",   (0,0), (-1,-1), 4, ACCENT_BLUE),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
    ]))
    story.append(ml_table)
    _spacer(4)

    # ── Section 4: Situation Summary ──────────────────────────────────────
    story.append(Paragraph("SITUATION SUMMARY", S_SECTION))
    _spacer(1)
    summary = report.get("situation_summary", "No summary available.")
    sum_table = Table([[Paragraph(summary, S_BODY)]])
    sum_table.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.75, MID_GREY),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
    ]))
    story.append(sum_table)
    _spacer(4)

    # ── Section 5: Key Metrics Row ────────────────────────────────────────
    story.append(Paragraph("KEY METRICS", S_SECTION))
    _spacer(1)
    metrics_data = [
        ["Risk Score", "Affected Population", "Primary Threat", "Evacuation"],
        [
            Paragraph(f"<b>{risk_score}/10</b>", _style("mv", fontName="Courier-Bold", fontSize=14, textColor=risk_color, leading=18, alignment=TA_CENTER)),
            Paragraph(f"<b>{report.get('estimated_affected_population', 'N/A')}</b>", _style("mv2", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=14, alignment=TA_CENTER)),
            Paragraph(f"<b>{report.get('primary_threat', 'N/A').upper()}</b>", _style("mv3", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=14, alignment=TA_CENTER)),
            Paragraph(f"<b>{report.get('evacuation_recommendation', 'N/A')}</b>", _style("mv4", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY, leading=14, alignment=TA_CENTER)),
        ],
    ]
    metrics_table = Table(metrics_data, colWidths=[(PAGE_W - 2*MARGIN)/4] * 4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0),  WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0),  8),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.5, MID_GREY),
        ("BACKGROUND",   (0,1), (-1,-1), LIGHT_GREY),
    ]))
    story.append(metrics_table)
    _spacer(4)

    # ── Section 6: Priority Rescue Zones ─────────────────────────────────
    story.append(Paragraph("PRIORITY RESCUE ZONES", S_SECTION))
    _spacer(1)
    zones = report.get("priority_zones", [])
    if zones:
        urgency_colors = {"IMMEDIATE": RISK_COLORS["CRITICAL"], "URGENT": RISK_COLORS["HIGH"], "MONITOR": ACCENT_BLUE}
        zone_rows = [
            [Paragraph("Zone", S_CELL_BOLD), Paragraph("Name", S_CELL_BOLD),
             Paragraph("Threat", S_CELL_BOLD), Paragraph("Urgency", S_CELL_BOLD)]
        ]
        for z in zones:
            urg    = z.get("urgency", "MONITOR")
            urg_c  = urgency_colors.get(urg, DARK_GREY)
            zone_rows.append([
                Paragraph(str(z.get("zone_id", "")), S_CELL),
                Paragraph(z.get("name", ""),         S_CELL),
                Paragraph(z.get("threat", ""),       S_CELL),
                Paragraph(f"<b>{urg}</b>", _style("urg", fontName="Helvetica-Bold", fontSize=8, textColor=urg_c, leading=11)),
            ])
        cw = [(PAGE_W - 2*MARGIN) * r for r in [0.07, 0.35, 0.32, 0.26]]
        zt = Table(zone_rows, colWidths=cw)
        zt.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0),  NAVY),
            ("TEXTCOLOR",    (0,0), (-1,0),  WHITE),
            ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0),  8),
            ("GRID",         (0,0), (-1,-1), 0.5, MID_GREY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GREY]),
            ("LEFTPADDING",  (0,0), (-1,-1), 6),
            ("TOPPADDING",   (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ]))
        story.append(zt)
    _spacer(4)

    # ── Section 7: Resources Required ────────────────────────────────────
    story.append(Paragraph("RESOURCES REQUIRED", S_SECTION))
    _spacer(1)
    res = report.get("resources_required", {})
    res_items = [
        ("Helicopters",     res.get("helicopters",      0)),
        ("Rescue Boats",    res.get("rescue_boats",     0)),
        ("NDRF Teams",      res.get("ndrf_teams",       0)),
        ("Medical Units",   res.get("medical_units",    0)),
        ("Evacuation Buses",res.get("evacuation_buses", 0)),
    ]
    res_rows = [[Paragraph(k, S_CELL_BOLD), Paragraph(str(v), S_CELL)] for k, v in res_items]
    half = (PAGE_W - 2*MARGIN) / 2 - 2*mm
    res_table = Table(
        [res_rows[:3], res_rows[3:] + [[Paragraph("", S_CELL), Paragraph("", S_CELL)]]],
        colWidths=[half * 0.55, half * 0.45, half * 0.55, half * 0.45],
    )
    res_table.setStyle(TableStyle([
        ("GRID",         (0,0), (-1,-1), 0.5, MID_GREY),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [LIGHT_GREY, WHITE]),
    ]))
    story.append(res_table)
    _spacer(4)

    # ── Section 8: 48-Hour Action Timeline ───────────────────────────────
    story.append(Paragraph("48-HOUR ACTION TIMELINE", S_SECTION))
    _spacer(1)
    timeline = report.get("action_timeline", [])
    if timeline:
        tl_rows = [[Paragraph("#", S_CELL_BOLD), Paragraph("Window", S_CELL_BOLD), Paragraph("Required Action", S_CELL_BOLD)]]
        for i, step in enumerate(timeline, 1):
            tl_rows.append([
                Paragraph(str(i),                  S_CELL),
                Paragraph(step.get("hour", ""),    S_CELL_BOLD),
                Paragraph(step.get("action", ""),  S_CELL),
            ])
        cw2 = [(PAGE_W - 2*MARGIN) * r for r in [0.05, 0.12, 0.83]]
        tl  = Table(tl_rows, colWidths=cw2)
        tl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0),  8),
            ("GRID",          (0,0), (-1,-1), 0.5, MID_GREY),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        story.append(tl)
    _spacer(4)

    # ── Section 9: Escalation Risk ────────────────────────────────────────
    escalation = report.get("escalation_risk", "")
    if escalation:
        story.append(Paragraph("ESCALATION RISK", S_SECTION))
        _spacer(1)
        esc_table = Table([[Paragraph(f"⚠  {escalation}", S_WARNING)]])
        esc_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), RISK_COLORS["CRITICAL"]),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING",   (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ]))
        story.append(esc_table)
        _spacer(4)

    # ── Section 10: Data Sources ──────────────────────────────────────────
    _hr()
    _spacer(2)
    sources = analysis.get("data_sources", [])
    story.append(Paragraph("DATA SOURCES: " + "  ·  ".join(sources), S_META))
    story.append(Paragraph(
        f"Coordination agencies: {', '.join(report.get('coordination_agencies', ['NDMA', 'SDMA']))}",
        S_META
    ))
    story.append(Paragraph(
        f"Road status: {report.get('key_roads_status', 'N/A')}",
        S_META
    ))

    doc.build(story)
    return buf.getvalue()
