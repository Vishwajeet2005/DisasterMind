"""
DisasterMind — PDF Report Generator  v2
Produces a premium, well-structured NDMA-ready A4 situation report.
"""

import io
from datetime import datetime, timezone

from reportlab.lib                   import colors
from reportlab.lib.enums             import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes         import A4
from reportlab.lib.styles            import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units             import mm
from reportlab.platypus              import (
    BaseDocTemplate, Frame, HRFlowable, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

# ── Colour palette ────────────────────────────────────────────────────────────
INK          = colors.HexColor("#0D1117")   # near-black
NAVY         = colors.HexColor("#0F2044")
NAVY_LIGHT   = colors.HexColor("#162c5e")
WHITE        = colors.white
OFF_WHITE    = colors.HexColor("#F9FAFB")
RULE         = colors.HexColor("#DDE3EC")
LIGHT_GREY   = colors.HexColor("#F3F4F6")
MID_GREY     = colors.HexColor("#9CA3AF")
DARK_GREY    = colors.HexColor("#374151")
ACCENT       = colors.HexColor("#1D4ED8")
TEAL         = colors.HexColor("#0D9488")

RISK_COLORS = {
    "CRITICAL": colors.HexColor("#B91C1C"),
    "HIGH":     colors.HexColor("#C2570A"),
    "MODERATE": colors.HexColor("#92400E"),
    "LOW":      colors.HexColor("#166534"),
}
RISK_BG = {
    "CRITICAL": colors.HexColor("#FEF2F2"),
    "HIGH":     colors.HexColor("#FFF7ED"),
    "MODERATE": colors.HexColor("#FFFBEB"),
    "LOW":      colors.HexColor("#F0FDF4"),
}
RISK_ACCENT = {
    "CRITICAL": colors.HexColor("#DC2626"),
    "HIGH":     colors.HexColor("#EA580C"),
    "MODERATE": colors.HexColor("#D97706"),
    "LOW":      colors.HexColor("#16A34A"),
}

# ── Styles ────────────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()

def _s(name, **kw):
    return ParagraphStyle(name, parent=_styles["Normal"], **kw)

S_SECTION    = _s("sec",  fontName="Helvetica-Bold", fontSize=7.5,  textColor=NAVY,      leading=10,  spaceBefore=8, letterSpacing=1.2)
S_BODY       = _s("body", fontName="Helvetica",      fontSize=9,    textColor=DARK_GREY, leading=14,  alignment=TA_JUSTIFY)
S_META       = _s("meta", fontName="Helvetica",      fontSize=7,    textColor=MID_GREY,  leading=10)
S_CELL       = _s("cell", fontName="Helvetica",      fontSize=8,    textColor=DARK_GREY, leading=11)
S_CELL_H     = _s("ch",   fontName="Helvetica-Bold", fontSize=7.5,  textColor=WHITE,     leading=11,  alignment=TA_CENTER)
S_CELL_B     = _s("cb",   fontName="Helvetica-Bold", fontSize=8,    textColor=DARK_GREY, leading=11)
S_CELL_C     = _s("cc",   fontName="Helvetica",      fontSize=8,    textColor=DARK_GREY, leading=11,  alignment=TA_CENTER)
S_WARN       = _s("warn", fontName="Helvetica-Bold", fontSize=8.5,  textColor=WHITE,     leading=13)
S_LABEL      = _s("lbl",  fontName="Helvetica",      fontSize=7,    textColor=MID_GREY,  leading=9)
S_VALUE      = _s("val",  fontName="Helvetica-Bold", fontSize=10,   textColor=INK,       leading=14)
S_VALUE_RISK = _s("vr",   fontName="Helvetica-Bold", fontSize=10,   textColor=INK,       leading=14,  alignment=TA_CENTER)
S_TIMELINE_N = _s("tln",  fontName="Helvetica-Bold", fontSize=8,    textColor=NAVY,      leading=11)
S_TIMELINE_A = _s("tla",  fontName="Helvetica",      fontSize=8.5,  textColor=DARK_GREY, leading=13,  alignment=TA_JUSTIFY)


def generate_pdf(analysis: dict) -> bytes:
    report    = analysis.get("situation_report", {})
    ml        = analysis.get("ml_prediction",    {})
    region    = analysis.get("region",           "Unknown Region")
    timestamp = datetime.now(timezone.utc).strftime("%d %B %Y  %H:%M UTC")
    risk      = report.get("risk_level", "HIGH").upper()
    rc        = RISK_COLORS .get(risk, DARK_GREY)
    rb        = RISK_BG     .get(risk, LIGHT_GREY)
    ra        = RISK_ACCENT .get(risk, DARK_GREY)

    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    LM = 18 * mm
    RM = 18 * mm
    TM = 30 * mm
    BM = 18 * mm
    CW = PAGE_W - LM - RM          # content width

    # ── Page decorators ──────────────────────────────────────────────────────
    def _draw_page(canvas, doc):
        canvas.saveState()
        # top navy bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - TM, PAGE_W, TM, fill=1, stroke=0)
        # thin risk-accent stripe at very top
        canvas.setFillColor(ra)
        canvas.rect(0, PAGE_H - 1.5*mm, PAGE_W, 1.5*mm, fill=1, stroke=0)
        # wordmark
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(LM, PAGE_H - 11*mm, "DisasterMind")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#93A3B8"))
        canvas.drawString(LM, PAGE_H - 16*mm, "AUTONOMOUS DISASTER RESPONSE INTELLIGENCE")
        # right side
        canvas.setFont("Helvetica-Bold", 6.5)
        canvas.setFillColor(colors.HexColor("#93A3B8"))
        canvas.drawRightString(PAGE_W - RM, PAGE_H - 10*mm, "CONFIDENTIAL — FOR OFFICIAL USE")
        canvas.drawRightString(PAGE_W - RM, PAGE_H - 16*mm, timestamp)
        # footer rule
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(LM, BM - 2*mm, PAGE_W - RM, BM - 2*mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(MID_GREY)
        canvas.drawCentredString(PAGE_W/2, BM - 6*mm,
            f"DisasterMind AI  ·  NDMA Situation Report  ·  {timestamp}")
        canvas.drawRightString(PAGE_W - RM, BM - 6*mm, f"Page {doc.page}")
        canvas.restoreState()

    frame = Frame(LM, BM, CW, PAGE_H - TM - BM, id="main")
    doc   = BaseDocTemplate(buf, pagesize=A4,
                leftMargin=LM, rightMargin=RM,
                topMargin=TM,  bottomMargin=BM)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_draw_page)])

    story = []

    def sp(h=3):  story.append(Spacer(1, h * mm))
    def hr(c=RULE, t=0.4): story.append(HRFlowable(width="100%", thickness=t, color=c, spaceAfter=0))
    def section(title, color=NAVY):
        story.append(Spacer(1, 5*mm))
        # section title with left accent bar via table
        t = Table([[Paragraph(title, _s(f"s{title}", fontName="Helvetica-Bold", fontSize=7.5,
                    textColor=color, leading=10, letterSpacing=1.2))]],
                  colWidths=[CW])
        t.setStyle(TableStyle([
            ("LINEBEFORE",  (0,0),(-1,-1), 3, color),
            ("LEFTPADDING", (0,0),(-1,-1), 8),
            ("TOPPADDING",  (0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("BACKGROUND",  (0,0),(-1,-1), colors.HexColor("#F8FAFF")),
        ]))
        story.append(t)
        sp(2)

    # ════════════════════════════════════════════════════════════════════════
    # §1  Document header
    # ════════════════════════════════════════════════════════════════════════
    sp(2)
    story.append(Paragraph(
        f"SITUATION REPORT — {region.upper()}",
        _s("docH", fontName="Helvetica-Bold", fontSize=15, textColor=INK, leading=20)
    ))
    sp(1)
    story.append(Paragraph(f"Issued: {timestamp}  ·  Classification: FOR OFFICIAL USE ONLY", S_META))
    sp(3)
    hr(t=0.8)
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §2  Risk assessment banner
    # ════════════════════════════════════════════════════════════════════════
    risk_score = report.get("risk_score", "N/A")
    evac       = report.get("evacuation_recommendation", "—")
    pop        = report.get("estimated_affected_population", "—")
    threat     = report.get("primary_threat", "—").upper()

    # Big risk level banner
    banner = Table([
        [
            # left: risk level
            Table([
                [Paragraph("RISK LEVEL", _s("rl_lbl", fontName="Helvetica-Bold", fontSize=6.5,
                           textColor=colors.HexColor("#9E9E9E"), leading=9, letterSpacing=1.5))],
                [Paragraph(risk, _s("rl_val", fontName="Helvetica-Bold", fontSize=26,
                           textColor=rc, leading=30))],
            ], colWidths=[CW*0.45]),
            # divider
            Table([[""]], colWidths=[0.3*mm]),
            # right: score + evac
            Table([[
                Table([
                    [Paragraph("RISK SCORE", _s("rs_lbl", fontName="Helvetica-Bold", fontSize=6.5,
                               textColor=colors.HexColor("#9E9E9E"), leading=9, letterSpacing=1.5))],
                    [Paragraph(f"{risk_score}/10", _s("rs_val", fontName="Helvetica-Bold", fontSize=22,
                               textColor=rc, leading=26))],
                ], colWidths=[CW*0.27]),
                Table([
                    [Paragraph("EVACUATION", _s("ev_lbl", fontName="Helvetica-Bold", fontSize=6.5,
                               textColor=colors.HexColor("#9E9E9E"), leading=9, letterSpacing=1.5))],
                    [Paragraph(evac, _s("ev_val", fontName="Helvetica-Bold", fontSize=12,
                               textColor=NAVY, leading=16))],
                ], colWidths=[CW*0.23]),
            ]], colWidths=[CW*0.27, CW*0.23]),
        ]
    ], colWidths=[CW*0.45, 0.3*mm, CW*0.55])
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), rb),
        ("LINEBEFORE",   (0,0), (0,-1),  4, ra),
        ("LINEBELOW",    (0,-1),(-1,-1), 1, ra),
        ("LEFTPADDING",  (0,0), (-1,-1), 14),
        ("RIGHTPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",  (1,0), (1,-1), 0),
        ("RIGHTPADDING", (1,0), (1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 12),
        ("BOTTOMPADDING",(0,0), (-1,-1), 12),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(banner)
    sp(3)

    # ════════════════════════════════════════════════════════════════════════
    # §3  Key metrics strip (4 cards)
    # ════════════════════════════════════════════════════════════════════════
    def _kv(label, value, vcolor=INK):
        return Table([
            [Paragraph(label, _s(f"kl{label}", fontName="Helvetica", fontSize=6.5,
                        textColor=MID_GREY, leading=9, letterSpacing=0.8))],
            [Paragraph(str(value), _s(f"kv{label}", fontName="Helvetica-Bold", fontSize=11,
                        textColor=vcolor, leading=15))],
        ], colWidths=[(CW/4) - 4*mm])

    cards = Table([[
        _kv("AFFECTED POPULATION", pop),
        _kv("PRIMARY THREAT", threat, rc),
        _kv("FLOOD PROBABILITY", f"{float(ml.get('flood_probability', 0)):.0%}"),
        _kv("ML CONFIDENCE", ml.get("ml_confidence", "—")),
    ]], colWidths=[(CW/4)] * 4)
    cards.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.5, RULE),
        ("INNERGRID",    (0,0), (-1,-1), 0.5, RULE),
        ("TOPPADDING",   (0,0), (-1,-1), 9),
        ("BOTTOMPADDING",(0,0), (-1,-1), 9),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("BACKGROUND",   (0,0), (-1,-1), OFF_WHITE),
    ]))
    story.append(cards)
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §4  ML Validation bar
    # ════════════════════════════════════════════════════════════════════════
    ml_text = (
        f"<b>ML VALIDATED</b>&nbsp;&nbsp;·&nbsp;&nbsp;"
        f"Flood Probability: {float(ml.get('flood_probability', 0)):.0%}&nbsp;&nbsp;·&nbsp;&nbsp;"
        f"Severity: {ml.get('severity_label', '—')}&nbsp;&nbsp;·&nbsp;&nbsp;"
        f"Models: XGBoost + Random Forest Severity Scorer&nbsp;&nbsp;·&nbsp;&nbsp;"
        f"Confidence: {ml.get('ml_confidence', '—')}"
    )
    ml_bar = Table([[Paragraph(ml_text, _s("mlb", fontName="Helvetica", fontSize=8,
                    textColor=ACCENT, leading=12))]])
    ml_bar.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,-1), colors.HexColor("#EEF2FF")),
        ("LINEBEFORE",  (0,0),(-1,-1), 3, ACCENT),
        ("LEFTPADDING", (0,0),(-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1), 12),
        ("TOPPADDING",  (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(ml_bar)
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §5  Situation Summary
    # ════════════════════════════════════════════════════════════════════════
    section("SITUATION SUMMARY")
    summary = report.get("situation_summary", "No summary available.")
    sum_box = Table([[Paragraph(summary, S_BODY)]], colWidths=[CW])
    sum_box.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, RULE),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
        ("RIGHTPADDING", (0,0),(-1,-1), 12),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("BACKGROUND",   (0,0),(-1,-1), WHITE),
    ]))
    story.append(sum_box)
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §6  Priority Rescue Zones
    # ════════════════════════════════════════════════════════════════════════
    zones = report.get("priority_zones", [])
    section("PRIORITY RESCUE ZONES", color=RISK_COLORS.get("HIGH", NAVY))
    if zones:
        urgency_colors = {
            "IMMEDIATE": RISK_COLORS["CRITICAL"],
            "URGENT":    RISK_COLORS["HIGH"],
            "MONITOR":   ACCENT,
        }
        hdr = [S_CELL_H, S_CELL_H, S_CELL_H, S_CELL_H]
        zone_rows = [[
            Paragraph("ZONE",    hdr[0]),
            Paragraph("NAME",    hdr[1]),
            Paragraph("THREAT",  hdr[2]),
            Paragraph("URGENCY", hdr[3]),
        ]]
        for z in zones:
            urg   = z.get("urgency", "MONITOR")
            urg_c = urgency_colors.get(urg, DARK_GREY)
            zone_rows.append([
                Paragraph(str(z.get("zone_id", "")), _s("zid", fontName="Helvetica-Bold", fontSize=8, textColor=NAVY, leading=11, alignment=TA_CENTER)),
                Paragraph(z.get("name",   ""), S_CELL),
                Paragraph(z.get("threat", ""), S_CELL),
                Paragraph(f"<b>{urg}</b>", _s(f"zug{urg}", fontName="Helvetica-Bold", fontSize=8, textColor=urg_c, leading=11, alignment=TA_CENTER)),
            ])
        cw = [CW * r for r in [0.08, 0.37, 0.32, 0.23]]
        zt = Table(zone_rows, colWidths=cw)
        zt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),   NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),  [WHITE, LIGHT_GREY]),
            ("GRID",          (0,0),(-1,-1),  0.4, RULE),
            ("LEFTPADDING",   (0,0),(-1,-1),  7),
            ("RIGHTPADDING",  (0,0),(-1,-1),  7),
            ("TOPPADDING",    (0,0),(-1,-1),  5),
            ("BOTTOMPADDING", (0,0),(-1,-1),  5),
            ("VALIGN",        (0,0),(-1,-1),  "TOP"),
        ]))
        story.append(zt)
    else:
        story.append(Paragraph("No priority zones identified at current risk level.", S_META))
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §7  Resources Required
    # ════════════════════════════════════════════════════════════════════════
    section("RESOURCES REQUIRED")
    res = report.get("resources_required", {})
    res_items = [
        ("Helicopters",      res.get("helicopters",      "—")),
        ("Rescue Boats",     res.get("rescue_boats",     "—")),
        ("NDRF Teams",       res.get("ndrf_teams",       "—")),
        ("Medical Units",    res.get("medical_units",    "—")),
        ("Evacuation Buses", res.get("evacuation_buses", "—")),
        ("Water Tankers",    res.get("water_tankers",    "—")),
    ]
    # 3-column resource grid
    col = CW / 3
    res_rows = []
    for i in range(0, len(res_items), 3):
        row = []
        for k, v in res_items[i:i+3]:
            row.append(Table([
                [Paragraph(k.upper(), _s(f"rk{k}", fontName="Helvetica", fontSize=6.5,
                            textColor=MID_GREY, leading=9, letterSpacing=0.8))],
                [Paragraph(str(v), _s(f"rv{k}", fontName="Helvetica-Bold", fontSize=14,
                            textColor=NAVY, leading=18))],
            ], colWidths=[col - 6*mm]))
        while len(row) < 3:
            row.append(Paragraph("", S_CELL))
        res_rows.append(row)
    res_tbl = Table(res_rows, colWidths=[col]*3)
    res_tbl.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, RULE),
        ("INNERGRID",    (0,0),(-1,-1), 0.5, RULE),
        ("BACKGROUND",   (0,0),(-1,-1), OFF_WHITE),
        ("TOPPADDING",   (0,0),(-1,-1), 9),
        ("BOTTOMPADDING",(0,0),(-1,-1), 9),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
    ]))
    story.append(res_tbl)
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §8  48-Hour Action Timeline
    # ════════════════════════════════════════════════════════════════════════
    section("48-HOUR ACTION TIMELINE")
    timeline = report.get("action_timeline", [])
    if timeline:
        hdr_row = [
            Paragraph("STEP", S_CELL_H),
            Paragraph("TIME WINDOW", S_CELL_H),
            Paragraph("REQUIRED ACTION", S_CELL_H),
        ]
        tl_rows = [hdr_row]
        for i, step in enumerate(timeline, 1):
            bg = WHITE if i % 2 == 0 else LIGHT_GREY
            tl_rows.append([
                Paragraph(str(i), _s(f"tn{i}", fontName="Helvetica-Bold", fontSize=9,
                           textColor=NAVY, leading=13, alignment=TA_CENTER)),
                Paragraph(step.get("hour", step.get("window", "—")),
                          _s(f"tw{i}", fontName="Helvetica-Bold", fontSize=8, textColor=DARK_GREY, leading=12)),
                Paragraph(step.get("action", ""), S_TIMELINE_A),
            ])
        cw2 = [CW * r for r in [0.07, 0.18, 0.75]]
        tl  = Table(tl_rows, colWidths=cw2)
        tl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  NAVY),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_GREY]),
            ("GRID",          (0,0), (-1,-1), 0.4, RULE),
            ("LEFTPADDING",   (0,0), (-1,-1), 7),
            ("RIGHTPADDING",  (0,0), (-1,-1), 7),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("ALIGN",         (0,0), (0,-1),  "CENTER"),
        ]))
        story.append(tl)
    else:
        story.append(Paragraph("No timeline data available.", S_META))
    sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §9  Escalation Risk (conditional)
    # ════════════════════════════════════════════════════════════════════════
    escalation = report.get("escalation_risk", "")
    if escalation:
        section("ESCALATION RISK", color=RISK_COLORS["CRITICAL"])
        esc_bar = Table([[Paragraph(f"WARNING: {escalation}", S_WARN)]], colWidths=[CW])
        esc_bar.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), RISK_COLORS["CRITICAL"]),
            ("LEFTPADDING",  (0,0),(-1,-1), 14),
            ("RIGHTPADDING", (0,0),(-1,-1), 14),
            ("TOPPADDING",   (0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ]))
        story.append(esc_bar)
        sp(4)

    # ════════════════════════════════════════════════════════════════════════
    # §10  Coordination & Road Status
    # ════════════════════════════════════════════════════════════════════════
    agencies   = report.get("coordination_agencies", ["NDMA", "SDMA", "District Collector"])
    road_stat  = report.get("key_roads_status", "Assessment pending")
    section("COORDINATION")
    coord_data = [
        [Paragraph("AGENCIES", _s("ck1", fontName="Helvetica-Bold", fontSize=6.5,
                    textColor=MID_GREY, leading=9, letterSpacing=0.8)),
         Paragraph("ROAD STATUS", _s("ck2", fontName="Helvetica-Bold", fontSize=6.5,
                    textColor=MID_GREY, leading=9, letterSpacing=0.8))],
        [Paragraph(", ".join(agencies), _s("cv1", fontName="Helvetica", fontSize=9,
                    textColor=DARK_GREY, leading=14)),
         Paragraph(road_stat, _s("cv2", fontName="Helvetica", fontSize=9,
                    textColor=DARK_GREY, leading=14))],
    ]
    coord_tbl = Table(coord_data, colWidths=[CW*0.55, CW*0.45])
    coord_tbl.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, RULE),
        ("INNERGRID",    (0,0),(-1,-1), 0.5, RULE),
        ("BACKGROUND",   (0,0),(-1,0),  LIGHT_GREY),
        ("BACKGROUND",   (0,1),(-1,-1), WHITE),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(coord_tbl)
    sp(5)

    # ════════════════════════════════════════════════════════════════════════
    # §11  Footer metadata
    # ════════════════════════════════════════════════════════════════════════
    hr()
    sp(2)
    sources = analysis.get("data_sources", [])
    story.append(Paragraph(
        "DATA SOURCES:  " + "   ·   ".join(sources),
        S_META
    ))
    sp(1)
    story.append(Paragraph(
        "This report is generated autonomously by DisasterMind AI and is intended for use by authorised disaster "
        "management personnel only. Verify all field conditions before mobilising resources.",
        _s("disc", fontName="Helvetica-Oblique", fontSize=7, textColor=MID_GREY, leading=10)
    ))

    doc.build(story)
    return buf.getvalue()
