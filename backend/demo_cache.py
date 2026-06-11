import os
import json
import time

from backend.agent import run_disaster_analysis

REGIONS = [
    {
        "id": "wayanad",
        "name": "Wayanad, Kerala",
        "lat": 11.6854,
        "lon": 76.1320,
        "bbox": [11.5, 75.9, 11.9, 76.3]
    },
    {
        "id": "kamrup",
        "name": "Kamrup, Assam",
        "lat": 26.3161,
        "lon": 91.5984,
        "bbox": [26.1, 91.3, 26.5, 91.8]
    },
    {
        "id": "chamoli",
        "name": "Chamoli, Uttarakhand",
        "lat": 30.2736,
        "lon": 79.3234,
        "bbox": [30.0, 79.1, 30.5, 79.5]
    }
]

def build_demo_cache():
    cache_dir = os.path.join(os.path.dirname(__file__), "demo_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    print("Starting Demo Cache Generation...")
    
    for region in REGIONS:
        print(f"\n--- Processing {region['name']} ---")
        try:
            # Sleep a bit to avoid hitting rate limits on APIs
            time.sleep(2)
            
            payload = run_disaster_analysis(
                region_name=region['name'],
                lat=region['lat'],
                lon=region['lon'],
                bbox=tuple(region['bbox'])
            )
            
            file_path = os.path.join(cache_dir, f"{region['id']}.json")
            with open(file_path, "w") as f:
                json.dump(payload, f, indent=4)
                
            print(f"Saved cache for {region['id']} to {file_path}")
        except Exception as e:
            print(f"Failed to cache {region['id']}: {e}")
            
    print("\nDemo Cache Generation Complete!")

if __name__ == "__main__":
    build_demo_cache()
