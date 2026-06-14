import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT", "")

def test_gee():
    if not GEE_PROJECT:
        print("GEE_PROJECT not set")
        return
    import ee
    ee.Initialize(project=GEE_PROJECT)
    
    lon, lat = 77.2090, 28.6139 # Delhi
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000) # 10km buffer
    
    dem = ee.Image("USGS/SRTMGL1_003")
    elevation = dem.select('elevation')
    slope = ee.Terrain.slope(elevation)
    
    # Calculate stats
    stats = dem.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True
        ).combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        ),
        geometry=region,
        scale=90,
        maxPixels=1e9
    )
    
    slope_stats = slope.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.max(),
            sharedInputs=True
        ),
        geometry=region,
        scale=90,
        maxPixels=1e9
    )
    
    print("Elevation Stats:", stats.getInfo())
    print("Slope Stats:", slope_stats.getInfo())

if __name__ == "__main__":
    test_gee()
