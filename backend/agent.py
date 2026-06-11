import time
from typing import Dict, Any

from backend.data_fetcher import (
    get_firms_hotspots,
    get_weather,
    get_elevation_stats,
    get_road_accessibility,
    get_satellite_thumbnail
)
from backend.ml_layer.predict import predictor
from backend.ai_brain import brain

def run_disaster_analysis(region_name: str, lat: float, lon: float, bbox: tuple) -> Dict[str, Any]:
    start_time = time.time()
    lat_min, lon_min, lat_max, lon_max = bbox
    
    print("[Agent] Step 1/6: Fetching Data from NASA FIRMS & Weather...")
    firms_data = get_firms_hotspots(lat_min, lon_min, lat_max, lon_max)
    weather_data = get_weather(lat, lon)
    
    print("[Agent] Step 2/6: Fetching Elevation Stats & Road Accessibility...")
    elevation_data = get_elevation_stats(lat, lon)
    roads_data = get_road_accessibility(lat_min, lon_min, lat_max, lon_max)
    road_count = roads_data.get("total_count", 0)
    
    print("[Agent] Step 3/6: Aggregating Data & Constructing ML Payload...")
    
    # Derive simplistic values for the predictor based on actual API data
    rainfall = 0.0
    if weather_data and "daily" in weather_data and "precipitation_sum" in weather_data["daily"]:
        precip_sums = weather_data["daily"]["precipitation_sum"]
        rainfall = sum([p for p in precip_sums if p is not None])
        
    temp = 25.0 # fallback
    
    sensor_data = {
        'rainfall': rainfall,
        'temp': temp,
        'discharge': 0.0,
        'water_level': 0.0,
        'elevation': elevation_data.get("avg", 0.0),
        'pop_density': 1000.0,
        'infrastructure': 1.0 if road_count > 10 else 0.0,
        'history': 1.0 if elevation_data.get("flood_risk") == "HIGH" else 0.0,
        'disaster_type': 'Flood',
        'deaths': 0.0,
        'affected': 0.0,
        'damage': 0.0,
        'year': 2026.0,
        'month': 6.0
    }
    
    print("[Agent] Step 4/6: Running Machine Learning Pipeline...")
    ml_prediction = predictor.get_combined_prediction(sensor_data)
    
    print("[Agent] Step 5/6: Consulting AIBrain (LLM Reasoning Layer)...")
    situation_report = brain.analyze_disaster(
        region_name=region_name,
        firms_data=firms_data,
        weather_data=weather_data,
        elevation_data=elevation_data,
        road_count=road_count,
        ml_prediction=ml_prediction
    )
    
    print("[Agent] Step 6/6: Fetching Satellite Thumbnail & Assembling Payload...")
    # Using generic dates spanning last 30 days for thumbnail
    date_start = "2026-05-01"
    date_end = "2026-06-11"
    satellite_thumbnail = get_satellite_thumbnail(lat, lon, date_start, date_end)
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    payload = {
        "region_name": region_name,
        "coordinates": {"lat": lat, "lon": lon, "bbox": bbox},
        "raw_data": {
            "firms_found": bool(firms_data),
            "weather": weather_data,
            "elevation": elevation_data,
            "roads": roads_data
        },
        "ml_prediction": ml_prediction,
        "satellite_thumbnail": satellite_thumbnail,
        "situation_report": situation_report,
        "processing_time_ms": processing_time_ms,
        "data_sources": [
            "NASA FIRMS (VIIRS)",
            "Open-Meteo",
            "OpenTopoData (SRTM90m)",
            "Overpass API (OSM)",
            "Google Earth Engine",
            "DisasterMind Flood Model (ONNX)",
            "DisasterMind Severity Model (ONNX)"
        ]
    }
    
    return payload
