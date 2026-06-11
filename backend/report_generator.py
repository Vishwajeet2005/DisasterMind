import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def generate_pdf(payload: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        textColor=colors.darkred,
        alignment=1, # Center
        spaceAfter=14
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    elements = []
    
    # 1. Header
    elements.append(Paragraph("<b>DISASTERMIND TACTICAL REPORT (CONFIDENTIAL)</b>", title_style))
    elements.append(Paragraph(f"<b>Region:</b> {payload.get('region_name', 'Unknown')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Extract report parts
    report = payload.get('situation_report', {})
    risk_level = str(report.get('risk_level', 'UNKNOWN')).upper()
    
    # 2. Risk level banner
    risk_color = colors.grey
    if risk_level == "CRITICAL":
        risk_color = colors.red
    elif risk_level == "HIGH":
        risk_color = colors.orange
    elif risk_level == "MODERATE":
        risk_color = colors.goldenrod
    elif risk_level == "LOW":
        risk_color = colors.green
        
    risk_table = Table([
        [Paragraph(f"<b>OVERALL RISK LEVEL: {risk_level} (Score: {report.get('risk_score', 0)})</b>", styles['Normal'])]
    ], colWidths=['100%'])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), risk_color),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(risk_table)
    elements.append(Spacer(1, 12))
    
    # 3. ML Validation box
    ml_validated = report.get('ml_validated', False)
    val_text = "<b>VALIDATED BY MACHINE LEARNING</b>" if ml_validated else "<b>HUMAN INTELLIGENCE ONLY (NO ML CONSENSUS)</b>"
    elements.append(Paragraph(val_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # 4. Situation Summary
    elements.append(Paragraph("<b>Situation Summary</b>", heading_style))
    elements.append(Paragraph(str(report.get('situation_summary', 'N/A')), normal_style))
    elements.append(Spacer(1, 12))
    
    # 5. Key metrics row
    elements.append(Paragraph("<b>Key Metrics</b>", heading_style))
    metrics_data = [
        ["Primary Threat", str(report.get('primary_threat', 'N/A'))],
        ["Est. Affected Pop.", str(report.get('estimated_affected_population', 'N/A'))],
        ["Evacuation Rec.", str(report.get('evacuation_recommendation', 'N/A'))],
        ["Road Status", str(report.get('key_roads_status', 'N/A'))]
    ]
    metrics_table = Table(metrics_data, colWidths=['40%', '60%'])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 12))
    
    # 6. Priority Rescue Zones Table
    elements.append(Paragraph("<b>Priority Rescue Zones</b>", heading_style))
    zones = report.get('priority_zones', [])
    if zones:
        zone_data = [["Zone Name", "Reason"]]
        for z in zones:
            zone_data.append([z.get('zone_name', ''), z.get('reason', '')])
        
        zone_table = Table(zone_data, colWidths=['30%', '70%'])
        zone_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(zone_table)
    else:
        elements.append(Paragraph("No specific zones identified.", normal_style))
    elements.append(Spacer(1, 12))
    
    # 7. Resources Table
    elements.append(Paragraph("<b>Resources Required</b>", heading_style))
    resources = report.get('resources_required', [])
    if resources:
        res_text = " • " + "<br/> • ".join(resources)
        elements.append(Paragraph(res_text, normal_style))
    else:
        elements.append(Paragraph("No specific resources requested.", normal_style))
    elements.append(Spacer(1, 12))
    
    # 8. Action Timeline
    elements.append(Paragraph("<b>Action Timeline (48 hrs)</b>", heading_style))
    timeline = report.get('action_timeline', [])
    if timeline:
        time_data = [["Timeframe", "Action"]]
        for t in timeline:
            time_data.append([t.get('timeframe', ''), t.get('action', '')])
            
        time_table = Table(time_data, colWidths=['25%', '75%'])
        time_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(time_table)
    else:
        elements.append(Paragraph("No timeline provided.", normal_style))
    elements.append(Spacer(1, 12))
    
    # 9. Escalation Risk Box
    elements.append(Paragraph("<b>Escalation Risk</b>", heading_style))
    elements.append(Paragraph(str(report.get('escalation_risk', 'Unknown')), normal_style))
    elements.append(Spacer(1, 12))
    
    # 10. Data sources footer
    elements.append(Spacer(1, 20))
    sources = payload.get('data_sources', [])
    sources_text = "<b>Data Sources:</b> " + ", ".join(sources)
    elements.append(Paragraph(sources_text, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
