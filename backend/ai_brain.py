import os
import json
import re
from groq import Groq
from typing import Dict, Any

class AIBrain:
    def __init__(self):
        # Initialize Groq client using environment variable GROQ_API_KEY automatically
        # Will fail gracefully if API key is not set.
        self.client = None
        try:
            if os.getenv("GROQ_API_KEY"):
                self.client = Groq()
        except Exception as e:
            print(f"Warning: Groq client failed to initialize: {e}")

    def analyze_disaster(self, region_name: str, firms_data: str, weather_data: Dict, 
                         elevation_data: Dict, road_count: int, ml_prediction: Dict) -> Dict[str, Any]:
        if not self.client:
            return self._get_fallback_response()
            
        prompt = f"""
You are DisasterMind, an autonomous disaster response intelligence agent. Analyze the following regional disaster data and provide a highly structured tactical response plan.

Region: {region_name}
ML Prediction: {json.dumps(ml_prediction)}
FIRMS Hotspots: {'Detected (Data omitted for brevity)' if firms_data else 'None'}
Weather Data: {json.dumps(weather_data)[:1000]}
Elevation/Risk Stats: {json.dumps(elevation_data)}
Road Count (Major): {road_count}

You must strictly output a valid JSON object matching the following structure exactly. Do not output anything else. No introductory text. No markdown formatting other than the JSON itself.
{{
    "situation_summary": "<Exactly 3 sentences summarizing the situation>",
    "risk_level": "<LOW/MODERATE/HIGH/CRITICAL>",
    "risk_score": <0-100>,
    "ml_validated": <true/false based on agreement with ML>,
    "primary_threat": "<Main disaster threat>",
    "estimated_affected_population": <Number>,
    "priority_zones": [
        {{"zone_name": "<Name>", "reason": "<Why>"}}
    ],
    "resources_required": ["<Resource1>", "<Resource2>"],
    "action_timeline": [
        {{"timeframe": "0-12hrs", "action": "<Action>..."}},
        {{"timeframe": "12-24hrs", "action": "<Action>..."}},
        {{"timeframe": "24-48hrs", "action": "<Action>..."}}
    ],
    "evacuation_recommendation": "<Clear recommendation>",
    "escalation_risk": "<Probability/Description>",
    "key_roads_status": "<Derived from road count>",
    "coordination_agencies": ["<Agency1>"]
}}
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1500,
            )
            raw_text = response.choices[0].message.content.strip()
            
            # Robust JSON parsing with markdown fence stripping
            clean_text = re.sub(r"^```json\s*", "", raw_text)
            clean_text = re.sub(r"^```\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)
            
            return json.loads(clean_text)
        except Exception as e:
            print(f"Error in AIBrain parsing/API call: {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "situation_summary": "Error parsing AI response or AI service unavailable.",
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "ml_validated": False,
            "primary_threat": "UNKNOWN",
            "estimated_affected_population": 0,
            "priority_zones": [],
            "resources_required": [],
            "action_timeline": [],
            "evacuation_recommendation": "Pending manual analysis",
            "escalation_risk": "UNKNOWN",
            "key_roads_status": "UNKNOWN",
            "coordination_agencies": []
        }

brain = AIBrain()
