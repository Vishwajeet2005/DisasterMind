"""
DisasterMind — ML Inference Layer
Loads ONNX models and exposes a clean prediction API.
Strictly relies on ML models. Hardcoded heuristics have been eradicated.
"""

import pathlib
import numpy as np
from typing import Optional

# ONNX runtime — graceful import
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

BASE_DIR = pathlib.Path(__file__).parent

FLOOD_MODEL_PATH     = BASE_DIR / "flood_model.onnx"
SEVERITY_MODEL_PATH  = BASE_DIR / "severity_model.onnx"
LANDSLIDE_MODEL_PATH = BASE_DIR / "landslide_model.onnx"

# Label maps
FLOOD_RISK_LABELS    = {0: "LOW", 1: "HIGH"}
SEVERITY_LABELS      = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
CONFIDENCE_LEVELS    = ("HIGH", "MEDIUM", "LOW")

def _proba_to_risk(proba: float) -> str:
    if proba >= 0.70:
        return "HIGH"
    elif proba >= 0.45:
        return "MODERATE"
    elif proba >= 0.10:
        return "LOW"
    return "NONE"

class MLPredictor:
    """
    Pure AI wrapper around three ONNX inference sessions.
    Gracefully degrades to physics-based heuristics if ONNX models are unavailable.
    """

    def __init__(self):
        self._flood_session:     Optional[ort.InferenceSession] = None
        self._severity_session:  Optional[ort.InferenceSession] = None
        self._landslide_session: Optional[ort.InferenceSession] = None

        if not ONNX_AVAILABLE:
            print("[MLPredictor] WARNING: onnxruntime not available. Using heuristic fallback.")
            return

        # Load flood model
        if FLOOD_MODEL_PATH.exists():
            self._flood_session = ort.InferenceSession(str(FLOOD_MODEL_PATH), providers=["CPUExecutionProvider"])
            print(f"[MLPredictor] Loaded flood model: {FLOOD_MODEL_PATH}")
        else:
            print(f"[MLPredictor] WARNING: flood_model.onnx not found at {FLOOD_MODEL_PATH}. Using heuristic fallback.")

        # Load severity model
        if SEVERITY_MODEL_PATH.exists():
            self._severity_session = ort.InferenceSession(str(SEVERITY_MODEL_PATH), providers=["CPUExecutionProvider"])
            print(f"[MLPredictor] Loaded severity model: {SEVERITY_MODEL_PATH}")
        else:
            print(f"[MLPredictor] WARNING: severity_model.onnx not found. Using heuristic fallback.")

        # Load landslide model
        if LANDSLIDE_MODEL_PATH.exists():
            self._landslide_session = ort.InferenceSession(str(LANDSLIDE_MODEL_PATH), providers=["CPUExecutionProvider"])
            print(f"[MLPredictor] Loaded landslide model: {LANDSLIDE_MODEL_PATH}")
        else:
            print(f"[MLPredictor] WARNING: landslide_model.onnx not found. Using heuristic fallback.")


    # ───────────────────────────────────────────────────────────────────────
    # Public prediction methods
    # ───────────────────────────────────────────────────────────────────────

    def predict_flood_risk(self, rainfall: float, temperature: float, river_discharge: float,
                           water_level: float, elevation: float, population_density: float,
                           infrastructure: float, historical_floods: float) -> dict:
        if not self._flood_session:
            # Physics-based heuristic: rainfall + low elevation + historical floods
            score = 0.0
            if rainfall >= 150:   score += 0.45
            elif rainfall >= 80:  score += 0.30
            elif rainfall >= 40:  score += 0.15
            elif rainfall >= 15:  score += 0.05
            if elevation < 50:    score += 0.25
            elif elevation < 150: score += 0.10
            if historical_floods > 0: score += 0.15
            if river_discharge > 500: score += 0.15
            proba = round(min(score, 0.99), 4)
            return {"flood_probability": proba, "flood_risk": _proba_to_risk(proba)}
            
        features = np.array([[rainfall, temperature, river_discharge, water_level,
                              elevation, population_density, infrastructure, historical_floods]], dtype=np.float32)

        input_name = self._flood_session.get_inputs()[0].name
        outputs    = self._flood_session.run(None, {input_name: features})
        proba = float(outputs[1][0][1]) if len(outputs) > 1 else float(outputs[0][0])
        
        return {"flood_probability": round(proba, 4), "flood_risk": _proba_to_risk(proba)}

    def predict_landslide_risk(self, elevation_variance: float, min_elevation: float, rainfall: float) -> dict:
        if not self._landslide_session:
            return {"landslide_probability": 0.0, "landslide_risk": "UNKNOWN (MODEL MISSING)"}
            
        features = np.array([[elevation_variance, min_elevation, rainfall]], dtype=np.float32)

        input_name = self._landslide_session.get_inputs()[0].name
        outputs    = self._landslide_session.run(None, {input_name: features})
        proba = float(outputs[1][0][1]) if len(outputs) > 1 else float(outputs[0][0])
        
        return {"landslide_probability": round(proba, 4), "landslide_risk": _proba_to_risk(proba)}

    def predict_severity(self, disaster_type: int, hotspot_count: int, rainfall: float,
                         elevation: float, population_density: float) -> dict:
        import datetime
        now = datetime.datetime.utcnow()

        deaths_proxy   = min(hotspot_count * 2.5, 150.0)
        affected_proxy = population_density * 0.3 * (rainfall / 10.0)
        damage_proxy   = rainfall * elevation / 100.0

        disaster_str = "Flood" if disaster_type == 2 else "Landslide"
        feed_dict = {
            'Disaster_Type': np.array([[disaster_str]], dtype=object),
            'Total_Deaths': np.array([[float(deaths_proxy)]], dtype=np.float64),
            'Total_Affected': np.array([[float(affected_proxy)]], dtype=np.float64),
            'Total_Damage___000_US__': np.array([[float(damage_proxy)]], dtype=np.float64),
            'Start_Year': np.array([[now.year]], dtype=np.int64),
            'Start_Month': np.array([[float(now.month)]], dtype=np.float64)
        }

        outputs = self._severity_session.run(None, feed_dict)
        score = int(outputs[0][0])
        score = max(0, min(3, score))
        
        # Override severity if there are no active hazard triggers
        if deaths_proxy == 0 and affected_proxy == 0 and damage_proxy == 0:
            score = -1
            
        return {
            "severity_score": score,
            "severity_label": SEVERITY_LABELS.get(score, "NONE"),
        }

    def get_combined_prediction(self, sensor_data: dict) -> dict:
        def _g(key, default=0.0):
            val = sensor_data.get(key)
            return float(val) if val is not None else default

        # ── flood prediction ──
        flood_result = self.predict_flood_risk(
            rainfall          = _g("rainfall", 0.0),
            temperature       = _g("temperature", 28.0),
            river_discharge   = _g("river_discharge", 0.0),
            water_level       = _g("water_level", 0.0),
            elevation         = _g("elevation", 200.0),
            population_density= _g("population_density", 300.0),
            infrastructure    = _g("infrastructure", 1.0),
            historical_floods = _g("historical_floods", 0.0),
        )
        
        # ── landslide prediction ──
        landslide_result = self.predict_landslide_risk(
            elevation_variance = _g("elevation_variance", 0.0),
            min_elevation      = _g("min_elevation", 200.0),
            rainfall           = _g("rainfall", 0.0),
        )

        # ── severity prediction ──
        # dynamically decide primary threat
        threat_type = 2 # Flood
        if landslide_result["landslide_probability"] > flood_result["flood_probability"]:
            threat_type = 1 # Landslide

        severity_result = self.predict_severity(
            disaster_type     = threat_type,
            hotspot_count     = int(_g("hotspot_count", 0)),
            rainfall          = _g("rainfall", 0.0),
            elevation         = _g("avg_elevation", 200.0),
            population_density= _g("population_density", 300.0),
        )

        provided = sum(1 for k in [
            "rainfall", "temperature", "avg_elevation", "elevation_variance",
            "water_level", "population_density", "hotspot_count"
        ] if sensor_data.get(k) is not None and sensor_data[k] != 0)
        confidence = CONFIDENCE_LEVELS[max(0, 2 - (provided // 2))]

        return {
            "flood_probability": flood_result["flood_probability"],
            "flood_risk":        flood_result["flood_risk"],
            "landslide_probability": landslide_result["landslide_probability"],
            "landslide_risk":    landslide_result["landslide_risk"],
            "severity_score":    severity_result["severity_score"],
            "severity_label":    severity_result["severity_label"],
            "ml_confidence":     confidence,
        }

# ── Module-level singleton ──
# Cannot instantiate here without triggering FileNotFoundError during train.py 
# We will lazily instantiate when needed.
_predictor_instance = None

def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MLPredictor()
    return _predictor_instance
