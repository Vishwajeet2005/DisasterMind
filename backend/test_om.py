import httpx
import asyncio

async def test():
    client = httpx.AsyncClient()
    lats = [52.52] * 100
    lons = [13.41] * 100
    lat_str = ",".join(str(l) for l in lats)
    lon_str = ",".join(str(l) for l in lons)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat_str}&longitude={lon_str}&daily=precipitation_sum&timezone=auto"
    print("URL length:", len(url))
    r = await client.get(url)
    print("Status:", r.status_code)
    try:
        data = r.json()
        if "error" in data:
            print("Error:", data)
        elif isinstance(data, list):
            print("Data length:", len(data))
        else:
            print(data)
    except Exception as e:
        print("Error parsing JSON:", e)

if __name__ == '__main__':
    asyncio.run(test())
