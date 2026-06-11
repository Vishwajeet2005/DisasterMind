"""
DisasterMind — ML Inference Layer
Loads both ONNX models and exposes a clean prediction API.
Falls back to calibrated heuristics if ONNX files are missing — the pipeline
must never crash because models haven't been trained yet.
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

FLOOD_MODEL_PATH    = BASE_DIR / "flood_model.onnx"
SEVERITY_MODEL_PATH = BASE_DIR / "severity_model.onnx"

# Label maps
FLOOD_RISK_LABELS    = {0: "LOW", 1: "HIGH"}
SEVERITY_LABELS      = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
CONFIDENCE_LEVELS    = ("HIGH", "MEDIUM", "LOW")


class MLPredictor:
    """
    Thin wrapper around two ONNX inference sessions.

    If either model file is absent (e.g. first run before `train.py`),
    the corresponding predict method falls back to deterministic heuristics
    so the rest of the agent pipeline is unaffected.
    """

    def __init__(self):
        self._flood_session:    Optional[ort.InferenceSession] = None
        self._severity_session: Optional[ort.InferenceSession] = None

        if not ONNX_AVAILABLE:
            print("[MLPredictor] onnxruntime not installed — using heuristic fallback")
            return

        # Load flood model
        if FLOOD_MODEL_PATH.exists():
            try:
                self._flood_session = ort.InferenceSession(
                    str(FLOOD_MODEL_PATH),
                    providers=["CPUExecutionProvider"],
                )
                print(f"[MLPredictor] Loaded flood model: {FLOOD_MODEL_PATH}")
            except Exception as e:
                print(f"[MLPredictor] Failed to load flood model: {e}")
        else:
            print(f"[MLPredictor] flood_model.onnx not found — using heuristics. Run ml_layer/train.py first.")

        # Load severity model
        if SEVERITY_MODEL_PATH.exists():
            try:
                self._severity_session = ort.InferenceSession(
                    str(SEVERITY_MODEL_PATH),
                    providers=["CPUExecutionProvider"],
                )
                print(f"[MLPredictor] Loaded severity model: {SEVERITY_MODEL_PATH}")
            except Exception as e:
                print(f"[MLPredictor] Failed to load severity model: {e}")
        else:
            print(f"[MLPredictor] severity_model.onnx not found — using heuristics. Run ml_layer/train.py first.")

    # ───────────────────────────────────────────────────────────────────────
    # Public prediction methods
    # ───────────────────────────────────────────────────────────────────────

    def predict_flood_risk(
        self,
        rainfall: float,
        temperature: float,
        river_discharge: float,
        water_level: float,
        elevation: float,
        population_density: float,
        infrastructure: float,
        historical_floods: float,
    ) -> dict:
        """
        Binary flood classifier.

        Returns
        -------
        {
          "flood_probability": float (0.0 – 1.0),
          "flood_risk":        "HIGH" | "MODERATE" | "LOW"
        }
        """
        features = np.array(
            [[rainfall, temperature, river_discharge, water_level,
              elevation, population_density, infrastructure, historical_floods]],
            dtype=np.float32,
        )

        if self._flood_session is not None:
            try:
                input_name = self._flood_session.get_inputs()[0].name
                outputs    = self._flood_session.run(None, {input_name: features})

                # outputs[0] → predicted class; outputs[1] → probability map
                proba = float(outputs[1][0][1]) if len(outputs) > 1 else float(outputs[0][0])
                label_idx = int(outputs[0][0])

                flood_risk = _proba_to_risk(proba)
                return {"flood_probability": round(proba, 4), "flood_risk": flood_risk}
            except Exception as e:
                print(f"[MLPredictor] Flood ONNX inference error: {e}")

        # ── Heuristic fallback ──────────────────────────────────────────
        return _heuristic_flood_risk(
            rainfall, elevation, water_level, historical_floods
        )

    def predict_severity(
        self,
        disaster_type: int,
        hotspot_count: int,
        rainfall: float,
        elevation: float,
        population_density: float,
    ) -> dict:
        """
        Multi-class severity scorer.

        Inputs are mapped to the training feature space:
        [disaster_type, total_deaths_proxy, total_affected_proxy, total_damage_proxy, year, month]

        Returns
        -------
        {
          "severity_score": int (0-3),
          "severity_label": "CRITICAL" | "HIGH" | "MODERATE" | "LOW"
        }
        """
        import datetime
        now = datetime.datetime.utcnow()

        # Map proxy features from available sensor signals
        deaths_proxy   = min(hotspot_count * 2.5, 150.0)          # rough proxy
        affected_proxy = population_density * 0.3 * (rainfall / 10.0)
        damage_proxy   = rainfall * elevation / 100.0

        if self._severity_session is not None:
            try:
                # Map inputs exactly as the ONNX schema demands
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
                return {
                    "severity_score": score,
                    "severity_label": SEVERITY_LABELS[score],
                }
            except Exception as e:
                print(f"[MLPredictor] Severity ONNX inference error: {e}")

        # ── Heuristic fallback ──────────────────────────────────────────
        return _heuristic_severity(hotspot_count, rainfall, elevation, population_density)

    def get_combined_prediction(self, sensor_data: dict) -> dict:
        """
        Run both models and return a unified prediction dict.

        Expected keys in sensor_data (all optional — missing → 0)
        -----------------------------------------------------------
        rainfall, temperature, river_discharge, water_level,
        elevation, population_density, infrastructure, historical_floods,
        hotspot_count, disaster_type
        """
        def _g(key, default=0.0):
            return float(sensor_data.get(key) or default)

        # ── flood prediction ──
        flood_result = self.predict_flood_risk(
            rainfall          = _g("rainfall", 50.0),
            temperature       = _g("temperature", 28.0),
            river_discharge   = _g("river_discharge", 100.0),
            water_level       = _g("water_level", 3.0),
            elevation         = _g("elevation", 200.0),
            population_density= _g("population_density", 300.0),
            infrastructure    = _g("infrastructure", 1.0),
            historical_floods = _g("historical_floods", 1.0),
        )

        # ── severity prediction ──
        severity_result = self.predict_severity(
            disaster_type     = int(_g("disaster_type", 2)),  # 2 ≈ flood
            hotspot_count     = int(_g("hotspot_count", 0)),
            rainfall          = _g("rainfall", 50.0),
            elevation         = _g("elevation", 200.0),
            population_density= _g("population_density", 300.0),
        )

        # ── confidence — based on how many real sensor values were provided ──
        provided = sum(1 for k in [
            "rainfall", "temperature", "elevation",
            "water_level", "population_density", "hotspot_count"
        ] if sensor_data.get(k) is not None and sensor_data[k] != 0)
        confidence = CONFIDENCE_LEVELS[max(0, 2 - (provided // 2))]

        return {
            "flood_probability": flood_result["flood_probability"],
            "flood_risk":        flood_result["flood_risk"],
            "severity_score":    severity_result["severity_score"],
            "severity_label":    severity_result["severity_label"],
            "ml_confidence":     confidence,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic fallbacks (deterministic, calibrated for Indian disaster context)
# ─────────────────────────────────────────────────────────────────────────────

def _proba_to_risk(proba: float) -> str:
    if proba >= 0.70:
        return "HIGH"
    elif proba >= 0.45:
        return "MODERATE"
    return "LOW"


def _heuristic_flood_risk(
    rainfall: float,
    elevation: float,
    water_level: float,
    historical_floods: float,
) -> dict:
    score = 0.0
    score += min(rainfall / 200.0, 0.4)          # up to 0.4 from rainfall
    score += max(0, (100.0 - elevation) / 250.0)  # up to 0.4 from low elevation
    score += min(water_level / 10.0, 0.1)
    score += historical_floods * 0.1

    proba = min(round(score, 4), 1.0)
    return {"flood_probability": proba, "flood_risk": _proba_to_risk(proba)}


def _heuristic_severity(
    hotspot_count: int,
    rainfall: float,
    elevation: float,
    population_density: float,
) -> dict:
    score = 0
    if rainfall > 150 or hotspot_count > 20:
        score = 3
    elif rainfall > 80 or hotspot_count > 10:
        score = 2
    elif rainfall > 30 or hotspot_count > 3:
        score = 1

    # Upscale if high elevation (landslide risk) + high density
    if elevation > 500 and population_density > 500 and score < 2:
        score = 2

    return {"severity_score": score, "severity_label": SEVERITY_LABELS[score]}


# ── Module-level singleton ────────────────────────────────────────────────
predictor = MLPredictor()
