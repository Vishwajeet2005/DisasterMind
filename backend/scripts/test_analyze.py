import httpx
import time
import json
import asyncio

async def test_analyze():
    print("Sending POST request to /analyze...")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "http://localhost:8000/analyze",
                json={
                    "region_name": "Test Region",
                    "lat": 10.0,
                    "lon": 76.0,
                    "bbox": {
                        "lat_min": 9.5,
                        "lat_max": 10.5,
                        "lon_min": 75.5,
                        "lon_max": 76.8
                    }
                }
            )
        elapsed = time.time() - start
        print(f"Request finished in {elapsed:.2f} seconds. Status code: {resp.status_code}")
        data = resp.json()
        print(f"Thumbnails: {data.get('satellite_thumbnail')}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_analyze())
