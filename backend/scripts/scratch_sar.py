import os
import asyncio
from dotenv import load_dotenv
import datetime

load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT", "")

def test_sar():
    import ee
    ee.Initialize(project=GEE_PROJECT)
    
    lon, lat = 77.2090, 28.6139 # Delhi
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000) # 10km buffer
    
    # 1. Flood Extent via Sentinel-1 SAR
    now = datetime.datetime.utcnow()
    date_end = now.strftime('%Y-%m-%d')
    date_start = (now - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
    )
    
    # Check if we have any images
    count = collection.size().getInfo()
    print(f"SAR images found: {count}")
    
    if count > 0:
        # Get the latest image
        image = collection.sort('system:time_start', False).first().select('VV')
        
        # Apply speckle filter (simple smoothing)
        smoothed = image.focal_median(50, 'circle', 'meters')
        
        # Threshold for water (VV backscatter < -16 dB is typically water)
        water = smoothed.lt(-16).rename('water')
        
        # Calculate water area percentage
        water_stats = water.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=100,
            maxPixels=1e9
        ).getInfo()
        
        print("Water ratio:", water_stats)
    else:
        print("No SAR images found in the last 14 days.")
        
if __name__ == "__main__":
    test_sar()
