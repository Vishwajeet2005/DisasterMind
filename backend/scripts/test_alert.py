import asyncio
import sys
sys.path.append(r'd:\DisasterFlow\disastermind\backend')

from alerter import send_alert

async def test():
    result = await send_alert(
        cell_name       = "Ratnagiri, Maharashtra",
        state           = "Maharashtra",
        risk_level      = "HIGH",
        risk_score      = 7,
        trend           = "ESCALATING",
        consecutive_hrs = 2,
        flood_prob      = 0.72,
        hotspot_count   = 4,
        rainfall_d1     = 88.5,
        summary         = "DisasterMind autonomous scan has flagged elevated flood risk in Ratnagiri. Heavy rainfall forecast exceeding 88mm in the next 24 hours with elevated FIRMS hotspot activity. ML model predicts 72% flood probability.",
        escalation_risk = "Risk trend is ESCALATING — conditions may worsen within 6 hours if rainfall continues.",
        lat             = 17.0,
        lon             = 73.3,
    )
    print("Alert sent successfully!" if result else "Alert FAILED — check token/chat ID")

asyncio.run(test())
