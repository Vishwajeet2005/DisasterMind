import json
from report_generator import generate_pdf

analysis = {
    "region": "Test, State",
    "timestamp": "2026-06-14T00:00:00Z",
    "coordinates": {"lat": 10.0, "lon": 20.0},
    "situation_report": {
        "risk_level": "CRITICAL",
        "risk_score": 9,
        "situation_summary": "System scan identified CRITICAL risk...",
        "primary_threat": "FLOOD",
        "estimated_affected_population": "31K–62K",
        "priority_zones": [],
        "resources_required": {
            "ndrf_teams": 5,
            "rescue_boats": 12,
            "helicopters": 3,
            "medical_units": 6,
            "evacuation_buses": 20,
            "water_tankers": 10
        },
        "action_timeline": [
            { "hour": "0–6 hrs", "action": "Deploy advance team." }
        ],
        "evacuation_recommendation": "MANDATORY",
        "escalation_risk": "Situation may deteriorate rapidly.",
        "coordination_agencies": ["NDMA", "SDMA"],
        "key_roads_status": "Assessment in progress."
    },
    "ml_prediction": {
        "flood_probability": 0.9,
        "severity_label": "CRITICAL",
        "ml_confidence": "HIGH"
    },
    "raw_data": {},
    "data_sources": ["NASA", "Open-Meteo"],
    "processing_time_ms": 0
}

try:
    pdf_bytes = generate_pdf(analysis)
    print(f"SUCCESS: Generated {len(pdf_bytes)} bytes")
except Exception as e:
    import traceback
    traceback.print_exc()
