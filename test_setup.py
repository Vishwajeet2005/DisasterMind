import sys
import os

# Add backend to path so imports work correctly
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ml_layer.predict import predictor
from backend.data_fetcher import (
    get_firms_hotspots,
    get_weather,
    get_elevation_stats,
    get_road_accessibility,
    get_satellite_thumbnail
)

def test_ml_layer():
    print("\n--- Testing ML Layer ---")
    dummy_data = {
        'rainfall': 120.5,
        'temp': 28.0,
        'discharge': 400.0,
        'water_level': 5.0,
        'elevation': 30.0,
        'pop_density': 5000.0,
        'infrastructure': 1.0,
        'history': 1.0,
        'disaster_type': 'Flood',
        'deaths': 15.0,
        'affected': 2000.0,
        'damage': 500.0,
        'year': 2026.0,
        'month': 6.0
    }
    result = predictor.get_combined_prediction(dummy_data)
    print("Combined Prediction Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")

def test_data_fetchers():
    print("\n--- Testing Data Fetchers ---")
    
    lat = 18.5204  # Pune, India
    lon = 73.8567
    
    # Tiny bbox around Pune for tests
    lat_min = lat - 0.1
    lat_max = lat + 0.1
    lon_min = lon - 0.1
    lon_max = lon + 0.1
    
    print("1. Fetching FIRMS Hotspots...")
    firms = get_firms_hotspots(lat_min, lon_min, lat_max, lon_max)
    print(f"   Response length: {len(firms)} characters")
    if firms:
        print(f"   Sample: {firms[:100]}...")
        
    print("\n2. Fetching Weather Data (Open-Meteo)...")
    weather = get_weather(lat, lon)
    if weather and 'daily' in weather:
        print(f"   Keys found: {list(weather['daily'].keys())}")
    else:
        print(f"   Weather data empty or malformed: {weather}")
        
    print("\n3. Fetching Elevation Stats (OpenTopoData)...")
    elevation = get_elevation_stats(lat, lon)
    print(f"   Result: {elevation}")
    
    print("\n4. Fetching Road Accessibility (Overpass API)...")
    roads = get_road_accessibility(lat_min, lon_min, lat_max, lon_max)
    print(f"   Result: {roads}")
    
    print("\n5. Fetching Satellite Thumbnail (GEE)...")
    thumb = get_satellite_thumbnail(lat, lon, '2023-01-01', '2023-12-31')
    print(f"   URL: {thumb if thumb else 'Failed (Likely due to missing GEE auth)'}")

if __name__ == "__main__":
    print("Starting integration test...")
    test_ml_layer()
    test_data_fetchers()
    print("\nTest completed successfully!")
