"""
DisasterMind — Data Fetcher
All external API calls live here. Every function handles its own errors and
never raises — the pipeline receives either real data or safe defaults.
"""

import os
import io
import csv
import json

import httpx
from dotenv import load_dotenv

load_dotenv()

NASA_FIRMS_KEY = os.getenv("NASA_FIRMS_KEY", "")
GEE_PROJECT    = os.getenv("GEE_PROJECT", "")

# Shared async client (reused across calls within one request)
_CLIENT_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


# ─────────────────────────────────────────────────────────────────────────────
# 1. NASA FIRMS — Active fire / thermal anomaly hotspots
# ─────────────────────────────────────────────────────────────────────────────

async def get_firms_hotspots(
    lat_min: float,
    lon_min: float,
    lat_max: float,
    lon_max: float,
    days: int = 3,
) -> str:
    """
    Fetch NASA FIRMS VIIRS/SNPP near-real-time hotspot CSV for the given bbox.

    Returns
    -------
    CSV string (may be empty or header-only if no hotspots detected)
    Empty string on any network / auth error.
    """
    if not NASA_FIRMS_KEY:
        print("[DataFetcher] NASA_FIRMS_KEY not set — returning empty hotspot data")
        return ""

    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv"
        f"/{NASA_FIRMS_KEY}/VIIRS_SNPP_NRT"
        f"/{lon_min},{lat_min},{lon_max},{lat_max}/{days}"
    )

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        print(f"[DataFetcher] FIRMS error: {e}")
        return ""


def parse_hotspot_count(csv_text: str) -> int:
    """Return number of hotspot rows (excluding header) from FIRMS CSV."""
    if not csv_text.strip():
        return 0
    lines = [l for l in csv_text.strip().splitlines() if l.strip()]
    return max(0, len(lines) - 1)  # subtract header row


# ─────────────────────────────────────────────────────────────────────────────
# 2. Open-Meteo — 72-hour weather forecast
# ─────────────────────────────────────────────────────────────────────────────

async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetch 3-day forecast from Open-Meteo (free, no key required).

    Returns
    -------
    {
      "precipitation":  [d1_mm, d2_mm, d3_mm],
      "wind_speed":     [d1_kmh, d2_kmh, d3_kmh],
      "weather_code":   [d1, d2, d3],
      "precip_prob":    [d1_pct, d2_pct, d3_pct],
    }
    Or {"error": str} on failure.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":                        lat,
        "longitude":                       lon,
        "daily":                           [
            "precipitation_sum",
            "windspeed_10m_max",
            "weathercode",
            "precipitation_probability_max",
        ],
        "forecast_days":                   3,
        "timezone":                        "Asia/Kolkata",
    }

    try:
        async with httpx.AsyncClient(timeout=_CLIENT_TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        daily = data.get("daily", {})
        return {
            "precipitation": daily.get("precipitation_sum", [0, 0, 0]),
            "wind_speed":    daily.get("windspeed_10m_max", [0, 0, 0]),
            "weather_code":  daily.get("weathercode", [0, 0, 0]),
            "precip_prob":   daily.get("precipitation_probability_max", [0, 0, 0]),
        }
    except Exception as e:
        print(f"[DataFetcher] Weather error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. OpenTopoData — SRTM 90m elevation grid
# ─────────────────────────────────────────────────────────────────────────────

async def get_elevation_stats(lat: float, lon: float) -> dict:
    """
    Sample a 3×3 grid of elevation points centred on (lat, lon) at ±0.1° spacing.

    Returns
    -------
    {
      "avg_elevation":    float (metres),
      "min_elevation":    float,
      "max_elevation":    float,
      "flood_risk":       "HIGH" | "MODERATE" | "LOW",
      "landslide_risk":   "HIGH" | "MODERATE" | "LOW",
    }
    Safe defaults returned on error.
    """
    offsets  = [-0.1, 0.0, 0.1]
    locations = "|".join(
        f"{round(lat + dy, 4)},{round(lon + dx, 4)}"
        for dy in offsets
        for dx in offsets
    )
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={locations}"

    safe_defaults = {
        "avg_elevation": 200.0,
        "min_elevation": 100.0,
        "max_elevation": 400.0,
        "flood_risk":    "MODERATE",
        "landslide_risk": "MODERATE",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            r = await client.get(url)
            r.raise_for_status()
            results = r.json().get("results", [])

        elevations = [
            pt["elevation"] for pt in results
            if pt.get("elevation") is not None
        ]
        if not elevations:
            return safe_defaults

        avg_e = round(sum(elevations) / len(elevations), 1)
        min_e = round(min(elevations), 1)
        max_e = round(max(elevations), 1)

        flood_risk    = "HIGH" if min_e < 50  else "MODERATE" if min_e < 200  else "LOW"
        landslide_risk = "HIGH" if max_e > 500 else "MODERATE" if max_e > 200 else "LOW"

        return {
            "avg_elevation":  avg_e,
            "min_elevation":  min_e,
            "max_elevation":  max_e,
            "flood_risk":     flood_risk,
            "landslide_risk": landslide_risk,
        }
    except Exception as e:
        print(f"[DataFetcher] Elevation error: {e}")
        return safe_defaults


# ─────────────────────────────────────────────────────────────────────────────
# 4. Overpass / OpenStreetMap — Road network accessibility
# ─────────────────────────────────────────────────────────────────────────────

async def get_road_accessibility(
    lat_min: float,
    lon_min: float,
    lat_max: float,
    lon_max: float,
) -> dict:
    """
    Query Overpass API for major roads in the bbox.

    Returns
    -------
    {
      "total_roads":      int,
      "major_road_names": [str, ...],
      "accessibility":    "GOOD" | "LIMITED" | "POOR",
    }
    """
    overpass_query = f"""
    [out:json][timeout:25];
    way["highway"~"^(primary|secondary|tertiary|trunk)$"]
       ({lat_min},{lon_min},{lat_max},{lon_max});
    out body;
    """

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            r = await client.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": overpass_query},
            )
            r.raise_for_status()
            elements = r.json().get("elements", [])

        road_names = []
        for el in elements:
            name = el.get("tags", {}).get("name")
            if name and name not in road_names:
                road_names.append(name)

        total = len(elements)
        accessibility = "GOOD" if total > 10 else "LIMITED" if total > 3 else "POOR"

        return {
            "total_roads":      total,
            "major_road_names": road_names[:10],   # cap at 10 for prompt brevity
            "accessibility":    accessibility,
        }
    except Exception as e:
        print(f"[DataFetcher] Road accessibility error: {e}")
        return {"total_roads": 0, "major_road_names": [], "accessibility": "UNKNOWN"}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Google Earth Engine — Sentinel-2 satellite thumbnail
# ─────────────────────────────────────────────────────────────────────────────

async def get_satellite_thumbnail(
    lat: float,
    lon: float,
    date_start: str,
    date_end: str,
) -> str:
    """
    Generate a Sentinel-2 thumbnail URL via Google Earth Engine Python API.
    Requires GEE authentication (service account or gcloud auth).

    Returns
    -------
    Thumbnail URL string, or "" on any error.
    """
    if not GEE_PROJECT:
        print("[DataFetcher] GEE_PROJECT not set — skipping satellite thumbnail")
        return ""

    try:
        import ee  # earthengine-api

        ee.Initialize(project=GEE_PROJECT)

        point  = ee.Geometry.Point([lon, lat])
        region = point.buffer(25_000).bounds()  # 25 km buffer

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        image = collection.first()
        if image is None:
            return ""

        url = image.select(["B4", "B3", "B2"]).getThumbURL({
            "min":    0,
            "max":    3000,
            "region": region,
            "dimensions": 512,
        })
        return url or ""
    except Exception as e:
        print(f"[DataFetcher] GEE thumbnail error: {e}")
        return ""
