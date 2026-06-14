"""
DisasterMind — Response Planning Engine
Generates actionable post-disaster response plans using Groq 70b.
Takes live sensor data + cell metadata and produces a structured
deployment plan ready for NDRF/SDMA use.
"""

import json
import os
import re
from typing import Optional

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_MODEL        = "llama-3.3-70b-versatile"
_TEMPERATURE  = 0.4
_MAX_TOKENS   = 2000

# ── NDRF Battalion locations (nearest to each zone) ──────────────────────────
NDRF_BATTALIONS = {
    "Kerala":          {"battalion": "4th Battalion", "base": "Arakkonam, TN",  "distance_km": 180},
    "Karnataka":       {"battalion": "4th Battalion", "base": "Arakkonam, TN",  "distance_km": 220},
    "Tamil Nadu":      {"battalion": "4th Battalion", "base": "Arakkonam, TN",  "distance_km": 60},
    "Andhra Pradesh":  {"battalion": "10th Battalion","base": "Vijayawada, AP", "distance_km": 80},
    "Telangana":       {"battalion": "10th Battalion","base": "Vijayawada, AP", "distance_km": 150},
    "Maharashtra":     {"battalion": "3rd Battalion", "base": "Pune, MH",       "distance_km": 60},
    "Gujarat":         {"battalion": "6th Battalion", "base": "Vadodara, GJ",   "distance_km": 90},
    "Rajasthan":       {"battalion": "6th Battalion", "base": "Vadodara, GJ",   "distance_km": 250},
    "Uttar Pradesh":   {"battalion": "9th Battalion", "base": "Patna, BR",      "distance_km": 200},
    "Bihar":           {"battalion": "9th Battalion", "base": "Patna, BR",      "distance_km": 40},
    "Jharkhand":       {"battalion": "9th Battalion", "base": "Patna, BR",      "distance_km": 180},
    "West Bengal":     {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 220},
    "Assam":           {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 30},
    "Meghalaya":       {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 100},
    "Manipur":         {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 220},
    "Nagaland":        {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 240},
    "Mizoram":         {"battalion": "8th Battalion", "base": "Guwahati, AS",   "distance_km": 300},
    "Uttarakhand":     {"battalion": "7th Battalion", "base": "Dehradun, UK",   "distance_km": 50},
    "Himachal Pradesh":{"battalion": "7th Battalion", "base": "Dehradun, UK",   "distance_km": 120},
    "Punjab":          {"battalion": "7th Battalion", "base": "Dehradun, UK",   "distance_km": 200},
    "Odisha":          {"battalion": "5th Battalion", "base": "Bhubaneswar, OD","distance_km": 30},
    "Chhattisgarh":    {"battalion": "5th Battalion", "base": "Bhubaneswar, OD","distance_km": 280},
    "Madhya Pradesh":  {"battalion": "3rd Battalion", "base": "Pune, MH",       "distance_km": 350},
    "J&K":             {"battalion": "2nd Battalion", "base": "Jammu, J&K",     "distance_km": 60},
    "Ladakh":          {"battalion": "2nd Battalion", "base": "Jammu, J&K",     "distance_km": 300},
    "Delhi":           {"battalion": "1st Battalion", "base": "Ghaziabad, UP",  "distance_km": 30},
    "Arunachal Pradesh":{"battalion":"8th Battalion", "base": "Guwahati, AS",   "distance_km": 350},
    "Andaman & Nicobar":{"battalion":"4th Battalion", "base": "Chennai, TN",    "distance_km": 1200},
    "Lakshadweep":     {"battalion": "4th Battalion", "base": "Kochi, KL",      "distance_km": 400},
    "Goa":             {"battalion": "3rd Battalion", "base": "Pune, MH",       "distance_km": 200},
}

FALLBACK_BATTALION = {"battalion": "Nearest Battalion", "base": "State HQ", "distance_km": 200}

# ── Fallback response plan ─────────────────────────────────────────────────────
def _fallback_plan(cell_name: str, state: str, risk_level: str, population: float, primary_hazard: str = "flood", ml_prob: float = 0.0) -> dict:
    multiplier = {"CRITICAL": 1.0, "HIGH": 0.5, "MODERATE": 0.1, "LOW": 0.01, "NONE": 0.0}.get(risk_level, 0.0)
    # Even in a CRITICAL disaster, only about 5% of the total population in the 625 sq km cell needs *immediate* physical rescue and relief camps.
    affected = int(population * 625 * multiplier * 0.05)
    if risk_level == "NONE":
        affected = 0
        situation_str = f"DisasterMind autonomous scan has predicted a {ml_prob:.1%} probability of a {primary_hazard.upper()} event in {cell_name}, {state}. The area is currently SAFE."
        pop_str = "0 estimated"
    else:
        if risk_level != "NONE" and ml_prob < 0.1:
            situation_str = f"DisasterMind autonomous scan has detected active environmental threats (heavy rainfall or fire hotspots) in {cell_name}, {state}, triggering a {risk_level} risk status. Immediate coordinated response required."
        else:
            situation_str = f"DisasterMind autonomous scan has predicted a {ml_prob:.1%} probability of a {primary_hazard.upper()} event in {cell_name}, {state}, resulting in a {risk_level} risk status. Immediate coordinated response required."
        pop_str = f"{affected//1000}K–{int(affected*1.5)//1000}K estimated"
        
    return {
        "situation_overview": situation_str,
        "affected_population": pop_str,
        "ndrf_deployment": {
            "battalion":     NDRF_BATTALIONS.get(state, FALLBACK_BATTALION)["battalion"],
            "base_location": NDRF_BATTALIONS.get(state, FALLBACK_BATTALION)["base"],
            "eta_hours":     round(NDRF_BATTALIONS.get(state, FALLBACK_BATTALION)["distance_km"] / 60, 1),
            "teams_required": 3 if risk_level == "CRITICAL" else 2,
        },
        "resources": {
            "rescue_boats":     {"CRITICAL": 12, "HIGH": 6, "MODERATE": 2, "LOW": 0, "NONE": 0}.get(risk_level, 0) if primary_hazard in ["flood", "cyclone"] else 0,
            "helicopters":      {"CRITICAL": 4, "HIGH": 2, "MODERATE": 0, "LOW": 0, "NONE": 0}.get(risk_level, 0),
            "medical_units":    {"CRITICAL": 8, "HIGH": 4, "MODERATE": 2, "LOW": 1, "NONE": 0}.get(risk_level, 0),
            "evacuation_buses": {"CRITICAL": 30, "HIGH": 15, "MODERATE": 5, "LOW": 0, "NONE": 0}.get(risk_level, 0),
            "relief_camps":     {"CRITICAL": 6, "HIGH": 3, "MODERATE": 1, "LOW": 0, "NONE": 0}.get(risk_level, 0),
            "water_tankers":    {"CRITICAL": 10, "HIGH": 5, "MODERATE": 2, "LOW": 0, "NONE": 0}.get(risk_level, 0),
        },
        "evacuation_zones": [
            {"zone": "A", "area": "Low-elevation river settlements", "priority": "IMMEDIATE", "route": "Primary highway to high ground"},
            {"zone": "B", "area": "Hillside residential areas",     "priority": "URGENT",    "route": "State highway via alternate route"},
            {"zone": "C", "area": "Agricultural flatlands",         "priority": "MONITOR",   "route": "District road network"},
        ],
        "action_timeline": [
            {"window": "0–2 hrs",  "action": "Alert SDMA and activate EOC. Deploy NDRF advance team."},
            {"window": "2–6 hrs",  "action": "Begin evacuation of Zone A. Pre-position rescue boats at river access points."},
            {"window": "6–12 hrs", "action": "Establish relief camps on high ground. Medical units operational."},
            {"window": "12–24 hrs","action": "Sustained rescue operations. Supply convoy deployment."},
            {"window": "24–72 hrs","action": "Damage assessment. Transition to relief and recovery operations."},
        ],
        "supply_requirements": {
            "food_packets":    int(affected * 1.5) if risk_level != "NONE" else 0,
            "water_litres":    affected * 3 if risk_level != "NONE" else 0,
            "medicine_kits":   max(affected // 50, 5) if risk_level != "NONE" else 0,
            "tarpaulins":      max(affected // 15, 10) if risk_level != "NONE" else 0,
            "blankets":        max(affected // 4, 20) if risk_level != "NONE" else 0,
        },
        "coordination_agencies": ["NDMA", "SDMA", "District Collector", "NDRF", "Indian Army", "Indian Red Cross", "State Police"],
        "communication_plan":    "Activate Emergency Operations Centre. Establish satellite communication for areas with network outage. Deploy HAM radio operators.",
        "hospitals_on_standby":  [f"District Hospital {state}", f"Medical College Hospital {state}"],
        "do_not": [
            "Do not use flooded roads for evacuation",
            "Do not shelter in ground floor structures in flood zones",
            "Do not approach landslide-affected slopes",
        ],
    }


class ResponsePlanner:
    def __init__(self):
        if not _GROQ_API_KEY:
            print("[ResponsePlanner] GROQ_API_KEY not set — using fallback plans")
            self._client = None
        else:
            self._client = Groq(api_key=_GROQ_API_KEY)

    def generate_plan(
        self,
        cell_name:        str,
        state:            str,
        risk_level:       str,
        risk_score:       int,
        flood_prob:       float,
        hotspot_count:    int,
        rainfall_d1:      float,
        elevation_data:   dict,
        road_data:        dict,
        population_density: float,
        risk_profile:     list,
        ml_prediction:    dict,
        consecutive_hrs:  int = 1,
        trend:            str = "STABLE",
    ) -> dict:
        """
        Generate a full post-disaster response plan.
        Returns structured JSON ready for UI rendering.
        """
        primary_hazard = risk_profile[0] if risk_profile else "flood"
        ml_prob = ml_prediction.get(f"{primary_hazard}_probability", flood_prob) if isinstance(ml_prediction, dict) else flood_prob
        
        if self._client is None:
            return _fallback_plan(cell_name, state, risk_level, population_density, primary_hazard, ml_prob)

        _clean_state = state.strip().title() if state else ""
        ndrf = NDRF_BATTALIONS.get(_clean_state, FALLBACK_BATTALION)
        
        # Security: Prevent basic prompt injection from malformed or malicious cell names
        safe_cell_name = str(cell_name).replace('\n', ' ')[:100]
        
        multiplier = {"CRITICAL": 1.0, "HIGH": 0.5, "MODERATE": 0.1, "LOW": 0.01, "NONE": 0.0}.get(risk_level, 0.0)
        # Apply the same 5% realistic displacement factor so the LLM doesn't hallucinate millions of supplies
        affected_low  = int(population_density * 625 * multiplier * 0.05)
        affected_high = int(population_density * 625 * 1.5 * multiplier * 0.05)
        
        if risk_level == "NONE":
            affected_low = 0
            affected_high = 0
        else:
            if affected_low < 10: affected_low = 10
            if affected_high < 20: affected_high = 20
        hazards = ", ".join(risk_profile) if risk_profile else "flood, landslide"
        avg_elev = elevation_data.get("avg_elevation", 200)
        road_count = road_data.get("total_roads", 0) if isinstance(road_data, dict) else 0
        road_access = road_data.get("accessibility", "LIMITED") if isinstance(road_data, dict) else "LIMITED"

        risk_context = {
            "CRITICAL": "MAXIMUM ALERT — Multi-agency mandatory evacuation. All resources mobilised. Civilian casualties possible if not acted on immediately.",
            "HIGH":     "ELEVATED ALERT — Partial evacuation advisory. Pre-position NDRF teams. Monitor for rapid escalation.",
            "MODERATE": "WATCH STATUS — Standby alert. Pre-deploy medical units. No evacuation yet but prepare routes and shelter.",
            "LOW":      "ADVISORY — Routine monitoring. Inform local administration. No immediate deployment required.",
        }.get(risk_level, "WATCH STATUS")

        hazard_actions = {
            "flood":     "focus on river monitoring, boat deployment, and low-lying area evacuation",
            "fire":      "focus on firebreaks, community evacuation, and respiratory medical support",
            "landslide": "focus on slope monitoring, road closures, and hillside settlement evacuation",
            "cyclone":   "focus on coastal evacuation, storm shelter activation, and power infrastructure protection",
            "drought":   "focus on water rationing, livestock support, and crop loss assessment",
            "earthquake":"focus on SAR (search and rescue), structural assessment, and trauma medical care",
        }.get(primary_hazard, "focus on general emergency response and population protection")

        if risk_level == "NONE":
            sit_prompt = f'"situation_overview": "<2-sentence briefing stating that {safe_cell_name} is currently SAFE, mentioning the {ml_prob:.0%} probability of {primary_hazard} and that ZERO response is required>",'
            pop_prompt = f'"affected_population": "0 estimated",'
        else:
            sit_prompt = f'"situation_overview": "<2-sentence threat briefing for District Collector of {safe_cell_name}, explicitly predicting the {primary_hazard} disaster with {ml_prob:.1%} probability and {risk_level} status>",'
            pop_prompt = f'"affected_population": "<realistic range based on {population_density}/km2>",'

        prompt = f"""You are DisasterMind, the autonomous disaster response AI for the Government of India NDMA.
Generate a UNIQUE, SPECIFIC response plan for the following confirmed threat cell.

STRICT OUTPUT RULES:
- Respond ONLY in valid JSON. No explanation, no markdown, no preamble, no code fences.
- DO NOT use any emojis, symbols, or unicode icons anywhere in your response.
- All text must be plain English only.
- Every value must be specific to THIS cell — do not use generic or template language.

=== CELL IDENTIFICATION ===
Cell: {safe_cell_name}, {state}
Coordinates: Lat {elevation_data.get('lat', 'N/A')}, Lon {elevation_data.get('lon', 'N/A')}
Primary hazard type: {primary_hazard}
Known risk profile: {hazards}

=== LIVE THREAT DATA ===
Risk Level: {risk_level} ({risk_score}/10)
Threat status: {risk_context}
Active for: {consecutive_hrs} consecutive hours | Trend: {trend}
Flood probability (ML): {flood_prob:.0%}
NASA FIRMS fire hotspots (72hr): {hotspot_count}
Rainfall forecast D+1: {rainfall_d1:.0f} mm
Average terrain elevation: {avg_elev}m above sea level
Road network: {road_count} roads | Accessibility: {road_access}
Population density: {population_density}/km2
Estimated affected population: {affected_low//1000}K to {affected_high//1000}K

=== NEAREST NDRF RESOURCES ===
Battalion: {ndrf['battalion']}
Base location: {ndrf['base']}
ETA by road: approximately {round(ndrf['distance_km']/60, 1)} hours

=== PLANNING DIRECTIVE ===
For this {risk_level} {primary_hazard} scenario in {safe_cell_name}:
- {hazard_actions}
- Scale all resource numbers proportional to risk level {risk_level} and population {population_density}/km2
- Action timeline must reflect {primary_hazard} response priorities, not generic flood response
- Evacuation zones must be geographically specific to {safe_cell_name}, {state} terrain
- Hospitals must be realistic for {state} state, near {safe_cell_name}
- Do-not rules must be specific to {primary_hazard} hazard type

{{
  {sit_prompt}
  {pop_prompt}
  "ndrf_deployment": {{
    "battalion": "{ndrf['battalion']}",
    "base_location": "{ndrf['base']}",
    "eta_hours": {round(ndrf['distance_km']/60, 1)},
    "teams_required": <integer scaled to {risk_level}>,
    "advance_team_action": "<specific first action on arrival for {primary_hazard} scenario>"
  }},
  "resources": {{
    "rescue_boats": <integer, strictly 0 unless {primary_hazard} is flood or cyclone>,
    "helicopters": <integer scaled to {risk_level}>,
    "medical_units": <integer>,
    "evacuation_buses": <integer scaled to affected population>,
    "relief_camps": <integer>,
    "water_tankers": <integer>
  }},
  "evacuation_zones": [
    {{
      "zone": "A",
      "area": "<specific {safe_cell_name} locality most at risk from {primary_hazard}>",
      "priority": "IMMEDIATE",
      "population": "<estimate>",
      "route": "<named road or direction from {safe_cell_name}>"
    }},
    {{
      "zone": "B",
      "area": "<second most at risk area>",
      "priority": "URGENT",
      "population": "<estimate>",
      "route": "<route>"
    }},
    {{
      "zone": "C",
      "area": "<monitoring zone>",
      "priority": "MONITOR",
      "population": "<estimate>",
      "route": "<route>"
    }}
  ],
  "action_timeline": [
    {{"window": "0-2 hrs",   "action": "<{primary_hazard}-specific immediate action for {risk_level}>"}},
    {{"window": "2-6 hrs",   "action": "<specific action>"}},
    {{"window": "6-12 hrs",  "action": "<specific action>"}},
    {{"window": "12-24 hrs", "action": "<specific action>"}},
    {{"window": "24-72 hrs", "action": "<recovery and assessment action>"}}
  ],
  "supply_requirements": {{
    "food_packets": <integer>,
    "water_litres": <integer>,
    "medicine_kits": <integer>,
    "tarpaulins": <integer>,
    "blankets": <integer>
  }},
  "coordination_agencies": ["NDMA", "SDMA", "<{state}-specific agencies>"],
  "communication_plan": "<specific comms strategy for {cell_name} terrain and {primary_hazard} conditions>",
  "hospitals_on_standby": ["<real or realistic hospital name near {cell_name}, {state}>", "<second hospital>"],
  "do_not": [
    "<critical safety rule specific to {primary_hazard}>",
    "<critical safety rule specific to {primary_hazard}>",
    "<critical safety rule specific to {primary_hazard}>"
  ]
}}"""


        try:
            completion = self._client.chat.completions.create(
                model       = _MODEL,
                temperature = _TEMPERATURE,
                max_tokens  = _MAX_TOKENS,
                messages    = [{"role": "user", "content": prompt}],
            )
            raw = completion.choices[0].message.content.strip()
            return _parse_json(raw) or _fallback_plan(cell_name, state, risk_level, population_density)
        except Exception as e:
            print(f"[ResponsePlanner] Groq error: {e}")
            return _fallback_plan(cell_name, state, risk_level, population_density)


def _parse_json(raw: str) -> Optional[dict]:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    brace = cleaned.find("{")
    if brace > 0:
        cleaned = cleaned[brace:]
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


# Module-level singleton
planner = ResponsePlanner()
