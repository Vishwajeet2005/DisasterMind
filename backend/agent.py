"""
DisasterMind — Autonomous Pipeline Orchestrator
Coordinates all data fetching, ML inference, and AI reasoning
into a single end-to-end analysis run.
"""

import asyncio
import time
from datetime import datetime, timezone

from data_fetcher import (
    get_firms_hotspots,
    get_weather,
    get_elevation_stats,
    get_road_accessibility,
    get_satellite_thumbnail,
    parse_hotspot_count,
)
from ml_layer.predict import predictor
from ai_brain import brain


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

    # ── Step 1 — NASA FIRMS hotspots ─────────────────────────────────────
    print(f"[Agent] Step 1/6: Fetching NASA FIRMS hotspot data...")
    firms_csv = await get_firms_hotspots(lat_min, lon_min, lat_max, lon_max, days=3)
    hotspot_count = parse_hotspot_count(firms_csv)
    print(f"[Agent] → {hotspot_count} active hotspots detected")

    # ── Step 2 — Weather forecast ─────────────────────────────────────────
    print(f"[Agent] Step 2/6: Fetching 72-hour weather forecast...")
    weather_data = await get_weather(lat, lon)
    rainfall = weather_data.get("precipitation", [0, 0, 0])
    print(f"[Agent] → Rainfall D1/D2/D3: {rainfall}")

    # ── Step 3 — Elevation stats ──────────────────────────────────────────
    print(f"[Agent] Step 3/6: Fetching terrain elevation data...")
    elevation_data = await get_elevation_stats(lat, lon)
    print(f"[Agent] → Avg elevation: {elevation_data.get('avg_elevation')}m | "
          f"Flood risk: {elevation_data.get('flood_risk')} | "
          f"Landslide risk: {elevation_data.get('landslide_risk')}")

    # ── Step 4 — Road accessibility ───────────────────────────────────────
    print(f"[Agent] Step 4/6: Fetching road network accessibility...")
    road_data = await get_road_accessibility(lat_min, lon_min, lat_max, lon_max)
    road_count = road_data.get("total_roads", 0)
    print(f"[Agent] → {road_count} roads | Accessibility: {road_data.get('accessibility')}")

    # ── Step 5 — ML prediction layer ──────────────────────────────────────
    print(f"[Agent] Step 5/6: Running ML prediction layer (XGBoost + Random Forest)...")
    sensor_data = {
        "rainfall":          rainfall[0] if rainfall else 0,
        "temperature":       28.0,                                  # open-meteo provides this if requested
        "river_discharge":   hotspot_count * 5.0,                  # proxy
        "water_level":       rainfall[0] / 10.0 if rainfall else 0,
        "elevation":         elevation_data.get("avg_elevation", 200),
        "population_density": 500.0,                               # conservative India average
        "infrastructure":    1.0,
        "historical_floods": 1.0,
        "hotspot_count":     hotspot_count,
        "disaster_type":     2,                                     # flood type code
    }
    ml_prediction = predictor.get_combined_prediction(sensor_data)
    print(f"[Agent] → Flood probability: {ml_prediction['flood_probability']:.1%} | "
          f"Severity: {ml_prediction['severity_label']} | "
          f"Confidence: {ml_prediction['ml_confidence']}")

    # ── Step 6 — AI Brain reasoning ───────────────────────────────────────
    print(f"[Agent] Step 6/6: Running Groq 70b AI reasoning layer...")
    ai_report = brain.analyze_disaster(
        region_name    = region_name,
        firms_data     = firms_csv,
        weather_data   = weather_data,
        elevation_data = elevation_data,
        road_count     = road_count,
        ml_prediction  = ml_prediction,
    )
    risk_level = ai_report.get("risk_level", "UNKNOWN")
    print(f"[Agent] → Risk level: {risk_level} | Score: {ai_report.get('risk_score', 'N/A')}/10")

    # ── Step 7 — GEE satellite thumbnail (non-blocking) ──────────────────
    print(f"[Agent] Fetching satellite thumbnail (non-blocking)...")
    date_end   = now_utc.strftime("%Y-%m-%d")
    date_start_dt = now_utc.replace(day=max(1, now_utc.day - 7))
    date_start = date_start_dt.strftime("%Y-%m-%d")
    try:
        thumbnail_url = await asyncio.wait_for(
            get_satellite_thumbnail(lat, lon, date_start, date_end),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        thumbnail_url = ""
        print("[Agent] Satellite thumbnail timed out — skipping")
    except Exception as e:
        thumbnail_url = ""
        print(f"[Agent] Satellite thumbnail error: {e}")

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
            "roads":         road_data,
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
