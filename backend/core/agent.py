"""
DisasterMind — Autonomous Pipeline Orchestrator
Coordinates all data fetching, ML inference, and AI reasoning
into a single end-to-end analysis run.
"""

import asyncio
import time
from datetime import datetime, timezone

from services.data_fetcher import (
    fetch_all_india_hotspots,
    get_weather,
    get_gee_topography,
    get_gee_population,
    get_gee_flood_extent,
    get_road_accessibility,
    get_satellite_thumbnail,
    get_river_discharge,
)
from models.ml_layer.predict import get_predictor
from core.ai_brain import brain


async def run_disaster_analysis(
    region_name: str,
    lat: float,
    lon: float,
    bbox: dict,
) -> dict:
    """
    Execute the full 7-step autonomous disaster analysis pipeline.

    Parameters
    ----------
    region_name : Human-readable region e.g. "Wayanad, Kerala"
    lat, lon    : Centre coordinates
    bbox        : {"lat_min", "lat_max", "lon_min", "lon_max"}

    Returns
    -------
    Complete analysis dict (see spec for schema).
    """
    t_start = time.time()
    now_utc = datetime.now(timezone.utc)

    lat_min = bbox["lat_min"]
    lat_max = bbox["lat_max"]
    lon_min = bbox["lon_min"]
    lon_max = bbox["lon_max"]

    print(f"[Agent] Launching massive parallel data fetching pipeline...")
    date_end   = now_utc.strftime("%Y-%m-%d")
    date_start_dt = now_utc.replace(day=max(1, now_utc.day - 7))
    date_start = date_start_dt.strftime("%Y-%m-%d")

    async def safe_thumbnail():
        try:
            return await asyncio.wait_for(get_satellite_thumbnail(lat, lon, date_start, date_end), timeout=5.0)
        except Exception:
            return {"true_color": "", "false_color": ""}

    results = await asyncio.gather(
        fetch_all_india_hotspots(),
        get_weather(lat, lon),
        get_gee_topography(lat, lon),
        get_gee_population(lat, lon),
        get_road_accessibility(lat_min, lon_min, lat_max, lon_max),
        get_river_discharge(lat, lon),
        get_gee_flood_extent(lat, lon),
        safe_thumbnail(),
        return_exceptions=True
    )
    
    def _unwrap(val, default):
        return val if not isinstance(val, Exception) else default

    all_hotspots   = _unwrap(results[0], [])
    weather_data   = _unwrap(results[1], {})
    elevation_data = _unwrap(results[2], {})
    population_data= _unwrap(results[3], {})
    road_data      = _unwrap(results[4], {})
    hydro_data     = _unwrap(results[5], {})
    flood_extent   = _unwrap(results[6], {})
    thumbnail_url  = _unwrap(results[7], {"true_color": "", "false_color": ""})

    hotspot_count = sum(1 for h in all_hotspots if (lat_min - 0.5 <= h[0] <= lat_max + 0.5) and (lon_min - 0.5 <= h[1] <= lon_max + 0.5))
    rainfall = weather_data.get("precipitation", [0, 0, 0])
    road_count = road_data.get("total_roads", 0)
    discharge_list = hydro_data.get("river_discharge", [0.0, 0.0, 0.0])
    discharge = discharge_list[0] if discharge_list and discharge_list[0] is not None else 0.0

    print(f"[Agent] -> {hotspot_count} hotspots, {road_count} roads, {discharge} m^3/s discharge")
    print(f"[Agent] -> Flood extent: {flood_extent.get('recent_flood_ratio', 0):.1%}")

    # ── Step 7 — ML prediction layer ──────────────────────────────────────
    print(f"[Agent] Step 7/8: Running ML prediction layer (XGBoost + Random Forest)...")
    
    # Dynamic OSM infrastructure mapping
    infra_score = min(max(1.0, road_count / 10.0), 10.0)
    temperature = weather_data.get("temperature", [28.0])[0]

    sensor_data = {
        "rainfall":          rainfall[0] if rainfall else 0,
        "temperature":       temperature,
        "river_discharge":   discharge,
        "water_level":       (discharge * 0.01) + (rainfall[0] / 10.0 if rainfall else 0),
        "elevation":         elevation_data.get("avg_elevation", 200),
        "elevation_variance": elevation_data.get("elevation_variance", 300),
        "min_elevation":     elevation_data.get("min_elevation", 100),
        "population_density": population_data.get("population_density", 300.0),
        "infrastructure":    infra_score,
        "historical_floods": population_data.get("historical_floods", 0.0),
        "hotspot_count":     hotspot_count,
        "disaster_type":     2,                                     # flood type code
    }
    ml_prediction = get_predictor().get_combined_prediction(sensor_data)
    print(f"[Agent] -> Flood probability: {ml_prediction['flood_probability']:.1%} | "
          f"Severity: {ml_prediction['severity_label']} | "
          f"Confidence: {ml_prediction['ml_confidence']}")

    # ── Step 8 — AI Brain reasoning ───────────────────────────────────────
    print(f"[Agent] Step 8/8: Running Groq 70b AI reasoning layer...")
    ai_report = brain.analyze_disaster(
        region_name    = region_name,
        hotspot_count  = hotspot_count,
        weather_data   = weather_data,
        elevation_data = elevation_data,
        road_count     = road_count,
        ml_prediction  = ml_prediction,
    )
    risk_level = ai_report.get("risk_level", "UNKNOWN")
    print(f"[Agent] -> Risk level: {risk_level} | Score: {ai_report.get('risk_score', 'N/A')}/10")



    elapsed_ms = int((time.time() - t_start) * 1000)
    print(f"[Agent] Pipeline complete in {elapsed_ms}ms")

    return {
        "region":      region_name,
        "timestamp":   now_utc.isoformat(),
        "coordinates": {"lat": lat, "lon": lon, "bbox": bbox},
        "raw_data": {
            "hotspot_count": hotspot_count,
            "weather":       weather_data,
            "elevation":     elevation_data,
            "sar_flood":     flood_extent,
            "roads":         road_data,
            "hydrology":     hydro_data,
        },
        "ml_prediction":      ml_prediction,
        "satellite_thumbnail": thumbnail_url,
        "situation_report":   ai_report,
        "processing_time_ms": elapsed_ms,
        "data_sources": [
            "NASA FIRMS VIIRS/SNPP Near Real-Time",
            "Open-Meteo Weather Forecast",
            "OpenTopoData SRTM 90m Elevation",
            "OpenStreetMap via Overpass API",
            "Google Earth Engine Sentinel-2",
            "XGBoost Flood Classifier (trained on Indian data)",
            "Random Forest Severity Scorer (trained on Indian data)",
        ],
    }
