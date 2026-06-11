import os
import requests
import ee
from typing import Dict, Any

# NASA FIRMS map key. Fallback to 'DEMO_KEY' if not provided in environment.
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "DEMO_KEY")

def get_firms_hotspots(lat_min: float, lon_min: float, lat_max: float, lon_max: float, days: int = 3) -> str:
    """
    Fetch NASA FIRMS VIIRS data.
    Timeout 15s. Returns CSV string or empty string on error.
    """
    try:
        bbox = f"{lon_min},{lat_min},{lon_max},{lat_max}"
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/{bbox}/{days}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching FIRMS hotspots: {e}")
        return ""

def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch Open-Meteo API for precipitation_sum, windspeed_10m_max, weathercode, 
    precipitation_probability_max over 3 days (Asia/Kolkata).
    Returns dict.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,precipitation_sum,windspeed_10m_max,precipitation_probability_max",
            "timezone": "Asia/Kolkata",
            "forecast_days": 3
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return {}

def get_elevation_stats(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch OpenTopoData SRTM90m for a 9-point grid. Calculate avg, min, max elevation.
    Determine flood_risk and landslide_risk.
    """
    try:
        # Create a 3x3 grid around lat/lon (approx 1km offset)
        offset = 0.01
        points = [
            f"{lat},{lon}", f"{lat+offset},{lon}", f"{lat-offset},{lon}",
            f"{lat},{lon+offset}", f"{lat},{lon-offset}",
            f"{lat+offset},{lon+offset}", f"{lat+offset},{lon-offset}",
            f"{lat-offset},{lon+offset}", f"{lat-offset},{lon-offset}"
        ]
        
        locations = "|".join(points)
        url = f"https://api.opentopodata.org/v1/srtm90m?locations={locations}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        elevations = [res.get("elevation", 0) for res in data.get("results", []) if res.get("elevation") is not None]
        
        if not elevations:
            return {"avg": 0, "min": 0, "max": 0, "flood_risk": "UNKNOWN", "landslide_risk": "UNKNOWN"}
            
        avg_elev = sum(elevations) / len(elevations)
        min_elev = min(elevations)
        max_elev = max(elevations)
        
        # Determine risks
        flood_risk = "LOW"
        if avg_elev < 50:
            flood_risk = "HIGH"
        elif avg_elev < 200:
            flood_risk = "MODERATE"
            
        landslide_risk = "LOW"
        if max_elev > 500:
            landslide_risk = "HIGH"
        elif max_elev > 200:
            landslide_risk = "MODERATE"
            
        return {
            "avg": avg_elev,
            "min": min_elev,
            "max": max_elev,
            "flood_risk": flood_risk,
            "landslide_risk": landslide_risk
        }
    except Exception as e:
        print(f"Error fetching elevation stats: {e}")
        return {"avg": 0, "min": 0, "max": 0, "flood_risk": "UNKNOWN", "landslide_risk": "UNKNOWN"}

def get_road_accessibility(lat_min: float, lon_min: float, lat_max: float, lon_max: float) -> Dict[str, Any]:
    """
    Fetch Overpass API for road networks to determine accessibility.
    Timeout 30s. Returns total count and accessibility label.
    """
    try:
        url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        way["highway"~"primary|secondary|tertiary|trunk"]({lat_min},{lon_min},{lat_max},{lon_max});
        out count;
        """
        response = requests.get(url, params={'data': query}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        count = 0
        if "elements" in data:
            for el in data["elements"]:
                if el.get("type") == "count":
                    count += int(el.get("tags", {}).get("ways", 0))
        
        access_label = "POOR"
        if count > 10:
            access_label = "GOOD"
        elif count > 3:
            access_label = "LIMITED"
            
        return {"total_count": count, "accessibility": access_label}
    except Exception as e:
        print(f"Error fetching road accessibility: {e}")
        return {"total_count": 0, "accessibility": "POOR"}

def get_satellite_thumbnail(lat: float, lon: float, date_start: str, date_end: str) -> str:
    """
    Fetch GEE COPERNICUS/S2_SR_HARMONIZED thumbnail URL.
    Returns empty string on failure.
    """
    try:
        if not ee.data.is_initialized():
            ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
            
        point = ee.Geometry.Point([lon, lat])
        image = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                 .filterBounds(point)
                 .filterDate(date_start, date_end)
                 .sort('CLOUDY_PIXEL_PERCENTAGE')
                 .first())
                 
        vis_params = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 3000,
            'dimensions': 512,
            'region': point.buffer(5000) # 5km radius
        }
        
        url = image.getThumbURL(vis_params)
        return url
    except Exception as e:
        print(f"Error fetching satellite thumbnail: {e}")
        return ""
