import reverse_geocoder as rg
import json

if __name__ == "__main__":
    lat_centers = [8.25 + 0.25*i for i in range(111)] # 8.25 to 35.75
    lon_centers = [69.75 + 0.25*i for i in range(101)] # 69.75 to 94.75

    coords = []
    for lat in reversed(lat_centers):
        for lon in lon_centers:
            coords.append((lat, lon))

    print("Searching...")
    results = rg.search(coords)

    data = []
    for i, res in enumerate(results):
        lat, lon = coords[i]
        lat_str = str(lat).replace(".", "_")
        lon_str = str(lon).replace(".", "_")
        cid = f"IN_{lat_str}_{lon_str}"
        data.append({
            "cid": cid,
            "lat": lat,
            "lon": lon,
            "admin1": res.get("admin1", ""),
            "admin2": res.get("admin2", ""),
            "cc": res.get("cc", "")
        })

    with open("d:/DisasterFlow/disastermind/backend/geo_dump.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Dumped geo data to geo_dump.json")
