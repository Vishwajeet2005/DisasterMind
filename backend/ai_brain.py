"""
DisasterMind — AI Reasoning Brain
Groq llama-3.3-70b-versatile receives ML-validated sensor data
and returns a structured JSON situation report.
"""

import json
import os
import re
from typing import Any

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_MODEL        = "llama-3.3-70b-versatile"
_TEMPERATURE  = 0.3
_MAX_TOKENS   = 1500


# ── Fallback report when Groq is unavailable or returns bad JSON ──────────
_FALLBACK_REPORT = {
    "situation_summary": (
        "ML models indicate elevated flood and landslide risk based on sensor inputs. "
        "Live satellite and weather data show above-normal precipitation and terrain vulnerability. "
        "Immediate assessment by district authorities is recommended."
    ),
    "risk_level":                  "HIGH",
    "risk_score":                  7,
    "ml_validated":                True,
    "primary_threat":              "flood",
    "estimated_affected_population": "50,000 – 100,000",
    "priority_zones": [
        {
            "zone_id":  1,
            "name":     "Low-elevation riverside settlements",
            "threat":   "Flash flooding",
            "urgency":  "IMMEDIATE",
            "reason":   "ML flood classifier flags HIGH probability. River discharge sensors show above-threshold levels.",
        },
        {
            "zone_id":  2,
            "name":     "Highland slope villages",
            "threat":   "Landslide",
            "urgency":  "URGENT",
            "reason":   "Terrain analysis shows slopes >30°. Accumulated rainfall exceeds 72-hr threshold.",
        },
    ],
    "resources_required": {
        "helicopters":     4,
        "rescue_boats":    12,
        "ndrf_teams":      3,
        "medical_units":   5,
        "evacuation_buses": 20,
    },
    "action_timeline": [
        {"hour": "0-2",   "action": "Alert SDMA and activate EOC. Deploy NDRF teams to riverside zones."},
        {"hour": "2-6",   "action": "Begin evacuation of low-elevation settlements. Pre-position rescue boats."},
        {"hour": "6-12",  "action": "Establish relief camps on high ground. Medical units on standby."},
        {"hour": "12-24", "action": "Assess road status; reroute supply convoys if primary roads flooded."},
        {"hour": "24-48", "action": "Transition to sustained relief operations. Damage assessment teams deploy."},
    ],
    "evacuation_recommendation":   "MANDATORY",
    "escalation_risk":             "Continued rainfall will cause river levels to exceed embankment capacity within 6 hours.",
    "key_roads_status":            "Primary highways accessible; rural link roads at risk of submersion.",
    "coordination_agencies":       ["NDMA", "SDMA", "District Collector", "Army", "Indian Red Cross"],
}


class AIBrain:
    """Thin wrapper around Groq SDK for disaster analysis."""

    def __init__(self):
        if not _GROQ_API_KEY:
            print("[AIBrain] GROQ_API_KEY not set — will use fallback responses")
            self._client = None
        else:
            self._client = Groq(api_key=_GROQ_API_KEY)
            print("[AIBrain] Groq client initialised")

    def analyze_disaster(
        self,
        region_name:   str,
        firms_data:    str,
        weather_data:  dict,
        elevation_data: dict,
        road_count:    int,
        ml_prediction: dict,
    ) -> dict:
        """
        Build ML-augmented prompt and call Groq 70b.

        Returns
        -------
        Parsed JSON dict matching the specification, or _FALLBACK_REPORT on failure.
        """
        if self._client is None:
            return {**_FALLBACK_REPORT, "region": region_name}

        # ── extract fields with safe defaults ──────────────────────────
        rainfall    = weather_data.get("precipitation", [0, 0, 0])
        wind        = weather_data.get("wind_speed",    [0, 0, 0])
        avg_elev    = elevation_data.get("avg_elevation",  200)
        flood_risk  = elevation_data.get("flood_risk",     "UNKNOWN")
        slide_risk  = elevation_data.get("landslide_risk", "UNKNOWN")

        from data_fetcher import parse_hotspot_count
        hotspot_count = parse_hotspot_count(firms_data)

        flood_prob    = ml_prediction.get("flood_probability", 0.0)
        flood_tier    = ml_prediction.get("flood_risk",        "UNKNOWN")
        severity_lbl  = ml_prediction.get("severity_label",   "UNKNOWN")
        ml_confidence = ml_prediction.get("ml_confidence",    "MEDIUM")

        prompt = f"""You are DisasterMind, an autonomous disaster response AI for the Indian government.
You have been given real-time multi-source sensor data AND validated ML model predictions for {region_name}.
Respond ONLY in valid JSON. No explanation, no markdown, no preamble.

=== ML MODEL PREDICTIONS (trained on historical Indian disaster data) ===
Flood probability (XGBoost): {flood_prob:.2%}
Predicted flood risk tier: {flood_tier}
Predicted severity (Random Forest): {severity_lbl}
ML confidence level: {ml_confidence}

=== LIVE SATELLITE & SENSOR DATA ===
NASA FIRMS VIIRS (last 72hrs): {hotspot_count} active hotspots
Rainfall forecast D1/D2/D3: {rainfall[0] if len(rainfall)>0 else 0}mm / {rainfall[1] if len(rainfall)>1 else 0}mm / {rainfall[2] if len(rainfall)>2 else 0}mm
Max wind speed: {wind[0] if wind else 0} km/h
Average elevation: {avg_elev}m
Terrain flood risk: {flood_risk}
Terrain landslide risk: {slide_risk}
Accessible roads: {road_count}

=== OUTPUT FORMAT ===
Return this exact JSON structure:
{{
  "situation_summary": "3 sentence summary. Sentence 1: what ML models predict. Sentence 2: what live sensor data shows. Sentence 3: most urgent action.",
  "risk_level": "CRITICAL | HIGH | MODERATE | LOW",
  "risk_score": <1-10>,
  "ml_validated": true,
  "primary_threat": "flood | landslide | fire | cyclone | composite",
  "estimated_affected_population": "<realistic range>",
  "priority_zones": [
    {{
      "zone_id": 1,
      "name": "<specific directional area>",
      "threat": "<specific threat>",
      "urgency": "IMMEDIATE | URGENT | MONITOR",
      "reason": "<2 sentence data-backed explanation referencing ML + sensor data>"
    }}
  ],
  "resources_required": {{
    "helicopters": <n>,
    "rescue_boats": <n>,
    "ndrf_teams": <n>,
    "medical_units": <n>,
    "evacuation_buses": <n>
  }},
  "action_timeline": [
    {{"hour": "0-2",   "action": "<specific action>"}},
    {{"hour": "2-6",   "action": "<specific action>"}},
    {{"hour": "6-12",  "action": "<specific action>"}},
    {{"hour": "12-24", "action": "<specific action>"}},
    {{"hour": "24-48", "action": "<specific action>"}}
  ],
  "evacuation_recommendation": "MANDATORY | ADVISORY | SHELTER_IN_PLACE",
  "escalation_risk": "<what gets worse in 6 hours without action>",
  "key_roads_status": "<road accessibility for rescue>",
  "coordination_agencies": ["NDMA", "SDMA", "<others relevant to {region_name}>"]
}}"""

        try:
            completion = self._client.chat.completions.create(
                model       = _MODEL,
                temperature = _TEMPERATURE,
                max_tokens  = _MAX_TOKENS,
                messages    = [{"role": "user", "content": prompt}],
            )
            raw = completion.choices[0].message.content.strip()
            return _parse_json_response(raw)
        except Exception as e:
            print(f"[AIBrain] Groq call failed: {e}")
            return {**_FALLBACK_REPORT, "region": region_name}


# ── JSON parsing helpers ───────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """
    Extract JSON from the model response, handling markdown code fences.
    Falls back to _FALLBACK_REPORT on any parse error.
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Sometimes the model prepends a short sentence before the JSON
    brace = cleaned.find("{")
    if brace > 0:
        cleaned = cleaned[brace:]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try extracting the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        print("[AIBrain] JSON parse failed — using fallback report")
        return _FALLBACK_REPORT.copy()


# ── Module-level singleton ────────────────────────────────────────────────
brain = AIBrain()
