"""
DisasterMind — Data Fetcher
All external API calls live here. Every function handles its own errors and
never raises — the pipeline receives either real data or safe defaults.
"""

import os
import io
import csv
import json
import asyncio
import socket

import httpx
import ee
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_http_client = None

load_dotenv()

NASA_FIRMS_KEY = os.getenv("NASA_FIRMS_KEY", "")
GEE_PROJECT    = os.getenv("GEE_PROJECT", "")
GEE_CREDENTIALS= os.getenv("EE_CREDENTIALS_JSON", "")
GEE_INITIALIZED = False

try:
    if GEE_CREDENTIALS:
        from pathlib import Path
        ee_dir = Path.home() / ".config" / "earthengine"
        ee_dir.mkdir(parents=True, exist_ok=True)
        with open(ee_dir / "credentials", "w") as f:
            f.write(GEE_CREDENTIALS)

    _old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(5.0)
    if GEE_PROJECT:
        ee.Initialize(project=GEE_PROJECT)
    else:
        ee.Initialize()
    socket.setdefaulttimeout(_old_timeout)
    GEE_INITIALIZED = True
except Exception as e:
    socket.setdefaulttimeout(_old_timeout)
    print(f"[DataFetcher] Initial GEE init failed: {e}")

# Shared async client (reused across calls within one request)
_CLIENT_TIMEOUT = httpx.Timeout(2.5, connect=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# 1. NASA FIRMS — Active fire / thermal anomaly hotspots
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_all_india_hotspots() -> list[tuple[float, float, float]]:
    """
    Fetch all NASA FIRMS hotspots for South Asia from the public CSV.
    Returns a list of (latitude, longitude, brightness) tuples.
    """
    url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_Asia_24h.csv"
    
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0), limits=httpx.Limits(max_keepalive_connections=50, max_connections=200))

    try:
        r = await _http_client.get(url)
        r.raise_for_status()
        
        hotspots = []
        reader = csv.DictReader(io.StringIO(r.text))
        for row in reader:
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                bright = float(row.get('bright_ti4', 300.0))
                hotspots.append((lat, lon, bright))
            except (ValueError, KeyError):
                continue
        return hotspots
    except Exception as e:
        print(f"[DataFetcher] Bulk FIRMS error: {e}")
        return []


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
            "temperature_2m_max",
        ],
        "forecast_days":                   3,
        "past_days":                       3,
        "timezone":                        "Asia/Kolkata",
    }

    try:
        async with httpx.AsyncClient(timeout=_CLIENT_TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        daily = data.get("daily", {})
        precip_array = daily.get("precipitation_sum", [0])
        # Sum past 3 days + today to get flood-causing accumulated rain, avoiding None values
        accumulated_rain = sum(p for p in precip_array[0:4] if p is not None)

        return {
            "precipitation": [accumulated_rain, precip_array[-2] if len(precip_array) > 1 else 0, precip_array[-1] if len(precip_array) > 0 else 0],
            "wind_speed":    daily.get("windspeed_10m_max", [0, 0, 0]),
            "weather_code":  daily.get("weathercode", [0, 0, 0]),
            "precip_prob":   daily.get("precipitation_probability_max", [0, 0, 0]),
            "temperature":   daily.get("temperature_2m_max", [28.0, 28.0, 28.0]),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[DataFetcher] Weather error: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. OpenTopoData — SRTM 90m elevation grid
# ─────────────────────────────────────────────────────────────────────────────

def _sync_gee_topography(lat: float, lon: float) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)
    dem = ee.Image("USGS/SRTMGL1_003")
    elevation = dem.select('elevation')
    slope = ee.Terrain.slope(elevation)
    
    stats = dem.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True).combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=region, scale=1000, maxPixels=1e9
    ).getInfo()
    
    slope_stats = slope.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=region, scale=1000, maxPixels=1e9
    ).getInfo()

    avg_e = stats.get('elevation_mean', 200.0)
    min_e = stats.get('elevation_min', 100.0)
    max_e = stats.get('elevation_max', 400.0)
    avg_s = slope_stats.get('slope_mean', 2.0)
    max_s = slope_stats.get('slope_max', 15.0)

    # ensure they are floats not None
    avg_e = avg_e if avg_e is not None else 200.0
    min_e = min_e if min_e is not None else 100.0
    max_e = max_e if max_e is not None else 400.0
    avg_s = avg_s if avg_s is not None else 2.0
    max_s = max_s if max_s is not None else 15.0

    return {
        "avg_elevation": round(avg_e, 1),
        "min_elevation": round(min_e, 1),
        "max_elevation": round(max_e, 1),
        "elevation_variance": round(max_e - min_e, 1),
        "avg_slope": round(avg_s, 2),
        "max_slope": round(max_s, 2)
    }

async def get_gee_topography(lat: float, lon: float) -> dict:
    """Compute exact topography metrics using Google Earth Engine."""
    safe_defaults = {
        "avg_elevation": 200.0, "min_elevation": 100.0, "max_elevation": 400.0,
        "elevation_variance": 300.0, "avg_slope": 2.0, "max_slope": 15.0
    }
    if not GEE_PROJECT:
        return safe_defaults
    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_gee_topography, lat, lon), timeout=10.0)
    except Exception as e:
        return safe_defaults

def _sync_gee_population(lat: float, lon: float) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)
    
    # Population Density
    pop_img = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density").filter(ee.Filter.date('2020-01-01', '2020-12-31')).first()
    pop_stat = pop_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000, maxPixels=1e9).getInfo()
    pop_density = pop_stat.get('population_density', 300.0)
    
    # Historical Floods (JRC Global Surface Water)
    water_img = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select('occurrence')
    water_stat = water_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000, maxPixels=1e9).getInfo()
    flood_occurrence = water_stat.get('occurrence', 0.0)
    
    return {
        "population_density": float(pop_density) if pop_density is not None else 300.0,
        "historical_floods": float(flood_occurrence) / 100.0 if flood_occurrence is not None else 0.0
    }

async def get_gee_population(lat: float, lon: float) -> dict:
    safe_defaults = {"population_density": 300.0, "historical_floods": 0.0}
    if not GEE_PROJECT:
        return safe_defaults
    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_gee_population, lat, lon), timeout=10.0)
    except Exception as e:
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
    [out:json][timeout:8];
    way["highway"~"^(primary|secondary|tertiary|trunk)$"]
       ({lat_min},{lon_min},{lat_max},{lon_max});
    out body;
    """

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=1.0), headers={"User-Agent": "DisasterMind/1.0 (vishwajeetborade@gmail.com)"}) as client:
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
        return {"total_roads": 0, "major_road_names": [], "accessibility": "UNKNOWN"}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Google Earth Engine — Sentinel-2 satellite thumbnail
# ─────────────────────────────────────────────────────────────────────────────

def _sync_satellite_thumbnail(lat: float, lon: float, date_start: str, date_end: str) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    import datetime

    point  = ee.Geometry.Point([lon, lat])
    region = point.buffer(10_000).bounds()

    def _try_fetch(d_start: str, d_end: str, cloud_pct: int):
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(d_start, d_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )
        size = col.size().getInfo()
        if size == 0:
            return None
        image = col.first()
        tc = image.select(["B4", "B3", "B2"]).getThumbURL({
            "min": 0, "max": 3000, "region": region, "dimensions": 512,
        })
        fc = image.select(["B8", "B4", "B3"]).getThumbURL({
            "min": 0, "max": 3000, "region": region, "dimensions": 512,
        })
        return {"true_color": tc or "", "false_color": fc or ""}

    # Progressive cloud threshold: 30 → 60 → 90%
    for cloud_limit in [30, 60, 90]:
        result = _try_fetch(date_start, date_end, cloud_limit)
        if result:
            return result

    # Still nothing? Widen date window to 60 days (handles NE India monsoon gaps)
    now      = datetime.datetime.now(datetime.timezone.utc)
    wide_end = now.strftime('%Y-%m-%d')
    wide_start = (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    for cloud_limit in [60, 90]:
        result = _try_fetch(wide_start, wide_end, cloud_limit)
        if result:
            return result

    return {"true_color": "", "false_color": ""}


async def get_satellite_thumbnail(
    lat: float, lon: float, date_start: str = None, date_end: str = None,
) -> dict:
    """
    Generate Sentinel-2 True Color and False Color thumbnail URLs.
    """
    import datetime
def _sync_gee_topography(lat: float, lon: float) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)
    dem = ee.Image("USGS/SRTMGL1_003")
    elevation = dem.select('elevation')
    slope = ee.Terrain.slope(elevation)
    
    stats = dem.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True).combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=region, scale=1000, maxPixels=1e9
    ).getInfo()
    
    slope_stats = slope.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=region, scale=1000, maxPixels=1e9
    ).getInfo()

    avg_e = stats.get('elevation_mean', 200.0)
    min_e = stats.get('elevation_min', 100.0)
    max_e = stats.get('elevation_max', 400.0)
    avg_s = slope_stats.get('slope_mean', 2.0)
    max_s = slope_stats.get('slope_max', 15.0)

    # ensure they are floats not None
    avg_e = avg_e if avg_e is not None else 200.0
    min_e = min_e if min_e is not None else 100.0
    max_e = max_e if max_e is not None else 400.0
    avg_s = avg_s if avg_s is not None else 2.0
    max_s = max_s if max_s is not None else 15.0

    return {
        "avg_elevation": round(avg_e, 1),
        "min_elevation": round(min_e, 1),
        "max_elevation": round(max_e, 1),
        "elevation_variance": round(max_e - min_e, 1),
        "avg_slope": round(avg_s, 2),
        "max_slope": round(max_s, 2)
    }

async def get_gee_topography(lat: float, lon: float) -> dict:
    """Compute exact topography metrics using Google Earth Engine."""
    safe_defaults = {
        "avg_elevation": 200.0, "min_elevation": 100.0, "max_elevation": 400.0,
        "elevation_variance": 300.0, "avg_slope": 2.0, "max_slope": 15.0
    }
    if not GEE_INITIALIZED:
        return safe_defaults
    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_gee_topography, lat, lon), timeout=10.0)
    except Exception as e:
        return safe_defaults

def _sync_gee_population(lat: float, lon: float) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)
    
    # Population Density
    pop_img = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density").filter(ee.Filter.date('2020-01-01', '2020-12-31')).first()
    pop_stat = pop_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000, maxPixels=1e9).getInfo()
    pop_density = pop_stat.get('population_density', 300.0)
    
    # Historical Floods (JRC Global Surface Water)
    water_img = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select('occurrence')
    water_stat = water_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=1000, maxPixels=1e9).getInfo()
    flood_occurrence = water_stat.get('occurrence', 0.0)
    
    return {
        "population_density": float(pop_density) if pop_density is not None else 300.0,
        "historical_floods": float(flood_occurrence) / 100.0 if flood_occurrence is not None else 0.0
    }

async def get_gee_population(lat: float, lon: float) -> dict:
    safe_defaults = {"population_density": 300.0, "historical_floods": 0.0}
    if not GEE_INITIALIZED:
        return safe_defaults
    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_gee_population, lat, lon), timeout=10.0)
    except Exception as e:
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
    [out:json][timeout:8];
    way["highway"~"^(primary|secondary|tertiary|trunk)$"]
       ({lat_min},{lon_min},{lat_max},{lon_max});
    out body;
    """

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=1.0), headers={"User-Agent": "DisasterMind/1.0 (contact@disastermind.app)"}) as client:
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
        return {"total_roads": 0, "major_road_names": [], "accessibility": "UNKNOWN"}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Google Earth Engine — Sentinel-2 satellite thumbnail
# ─────────────────────────────────────────────────────────────────────────────

import math
def get_fallback_satellite_image(lat, lon, zoom=13):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ytile}/{xtile}"

def _sync_satellite_thumbnail(lat: float, lon: float, date_start: str, date_end: str) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    import datetime

    point  = ee.Geometry.Point([lon, lat])
    region = point.buffer(10_000).bounds()

    def _try_fetch(d_start: str, d_end: str, cloud_pct: int):
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(d_start, d_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )
        size = col.size().getInfo()
        if size == 0:
            return None
        image = col.first()
        tc = image.select(["B4", "B3", "B2"]).getThumbURL({
            "min": 0, "max": 3000, "region": region, "dimensions": 512,
        })
        fc = image.select(["B8", "B4", "B3"]).getThumbURL({
            "min": 0, "max": 3000, "region": region, "dimensions": 512,
        })
        return {"true_color": tc or "", "false_color": fc or ""}

    # Progressive cloud threshold: 30 → 60 → 90%
    for cloud_limit in [30, 60, 90]:
        result = _try_fetch(date_start, date_end, cloud_limit)
        if result:
            return result

    # Still nothing? Widen date window to 60 days (handles NE India monsoon gaps)
    now      = datetime.datetime.now(datetime.timezone.utc)
    wide_end = now.strftime('%Y-%m-%d')
    wide_start = (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    for cloud_limit in [60, 90, 101]:
        result = _try_fetch(wide_start, wide_end, cloud_limit)
        if result:
            return result

    # Absolute final fallback: last 1 year, no cloud limit
    year_start = (now - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    result = _try_fetch(year_start, wide_end, 101)
    if result:
        return result

    fallback_url = get_fallback_satellite_image(lat, lon)
    return {"true_color": fallback_url, "false_color": fallback_url}


async def get_satellite_thumbnail(
    lat: float, lon: float, date_start: str = None, date_end: str = None,
) -> dict:
    """
    Generate Sentinel-2 True Color and False Color thumbnail URLs.
    """
    import datetime
    if not date_start or not date_end:
        now = datetime.datetime.now(datetime.timezone.utc)
        date_end = now.strftime('%Y-%m-%d')
        date_start = (now - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
        
    fallback_url = get_fallback_satellite_image(lat, lon)
    if not GEE_INITIALIZED:
        return {"true_color": fallback_url, "false_color": fallback_url}
    try:
        res = await asyncio.wait_for(asyncio.to_thread(_sync_satellite_thumbnail, lat, lon, date_start, date_end), timeout=30.0)
        if not res or not res.get("true_color"):
            return {"true_color": fallback_url, "false_color": fallback_url}
        return res
    except Exception as e:
        print(f"[DataFetcher] S2 Thumbnail ERROR: {e}")
        return {"true_color": fallback_url, "false_color": fallback_url}

# ─────────────────────────────────────────────────────────────────────────────
# 6. Open-Meteo — Global Flood Awareness System (GloFAS)
# ─────────────────────────────────────────────────────────────────────────────

async def get_river_discharge(lat: float, lon: float) -> dict:
    """
    Fetch daily river discharge (m³/s) from Open-Meteo Flood API.

    Returns
    -------
    {
      "river_discharge": [d1, d2, d3],
      "river_discharge_mean": [d1, d2, d3],
      "river_discharge_max": [d1, d2, d3]
    }
    Or {"error": str} on failure.
    """
    url = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["river_discharge", "river_discharge_mean", "river_discharge_max"],
        "forecast_days": 3,
    }

    try:
        async with httpx.AsyncClient(timeout=_CLIENT_TIMEOUT) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        daily = data.get("daily", {})
        return {
            "river_discharge": daily.get("river_discharge", [0.0, 0.0, 0.0]),
            "river_discharge_mean": daily.get("river_discharge_mean", [0.0, 0.0, 0.0]),
            "river_discharge_max": daily.get("river_discharge_max", [0.0, 0.0, 0.0]),
        }
    except Exception as e:
        return {"error": str(e)}

async def get_weather_batch(lats: list[float], lons: list[float]) -> list[dict]:
    """Fetch weather for up to 100 coordinates in a single batch request."""
    if not lats or not lons: return []
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": ",".join(str(lat) for lat in lats),
        "longitude": ",".join(str(lon) for lon in lons),
        "daily": "precipitation_sum,windspeed_10m_max,weathercode,precipitation_probability_max",
        "timezone": "auto",
        "past_days": 3,
        "forecast_days": 3
    }
    
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0), limits=httpx.Limits(max_keepalive_connections=50, max_connections=200))

    for attempt in range(3):
        try:
            r = await _http_client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                data = [data] # Fallback if only 1 coord passed
                
            results = []
            for d in data:
                if "daily" not in d:
                    results.append({"error": "No daily data"})
                    continue
                daily = d["daily"]
                precip_array = daily.get("precipitation_sum", [0])
                accumulated_rain = sum(p for p in precip_array[0:4] if p is not None)

                results.append({
                    "precipitation": [accumulated_rain],
                    "wind_speed":    daily.get("windspeed_10m_max", [0, 0, 0]),
                    "weather_code":  daily.get("weathercode", [0, 0, 0]),
                    "precip_prob":   daily.get("precipitation_probability_max", [0, 0, 0]),
                })
            return results
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"[DataFetcher] Open-Meteo 429 Rate Limit. Degrading weather to 0.")
                return [{"error": "429 Rate Limited"} for _ in lats]
            if attempt < 2:
                await asyncio.sleep(2.0)
                continue
            return [{"error": str(e)} for _ in lats]
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2.0)
                continue
            print(f"[DataFetcher] Batch Weather Error: {e}")
            return [{"error": str(e)} for _ in lats]
            
    return [{"error": "Max retries exceeded"} for _ in lats]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Google Earth Engine — Sentinel-1 SAR Flood Extent
# ─────────────────────────────────────────────────────────────────────────────

def _sync_gee_flood_extent(lat: float, lon: float) -> dict:
    if not GEE_INITIALIZED: raise Exception("GEE not initialized or network unreachable")
    import datetime

    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    date_end = now.strftime('%Y-%m-%d')
    date_start = (now - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
    )
    
    count = collection.size().getInfo()
    if count == 0:
        return {"recent_flood_ratio": 0.0}
        
    image = collection.sort('system:time_start', False).first().select('VV')
    smoothed = image.focal_median(50, 'circle', 'meters')
    water = smoothed.lt(-16).rename('water')
    
    water_stats = water.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    
    return {"recent_flood_ratio": round(water_stats.get('water', 0.0), 3)}

async def get_gee_flood_extent(lat: float, lon: float) -> dict:
    """Compute recent flood extent ratio via Sentinel-1 SAR imagery."""
    if not GEE_INITIALIZED:
        return {"recent_flood_ratio": 0.0}
    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_gee_flood_extent, lat, lon), timeout=10.0)
    except Exception as e:
        return {"recent_flood_ratio": 0.0}
