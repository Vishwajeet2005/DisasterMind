import reverse_geocoder as rg

if __name__ == "__main__":
    lat_centers = [8.25 + 1.25*i for i in range(23)] # 8.25 to 35.75
    lon_centers = [69.75 + 1.25*i for i in range(21)] # 69.75 to 94.75

    coords = []
    cells = []
    for lat in reversed(lat_centers):
        for lon in lon_centers:
            coords.append((lat, lon))
            
            cid = f"IN_{int(lat):02d}{int(lon):02d}"
            name = f"Region {lat:.2f}N {lon:.2f}E"
            lat_min = lat - 0.625
            lat_max = lat + 0.625
            lon_min = lon - 0.625
            lon_max = lon + 0.625
            
            cells.append({
                'cid': cid, 'name': name, 'lat': lat, 'lon': lon,
                'lmin': lat_min, 'lmax': lat_max, 'lnmin': lon_min, 'lnmax': lon_max
            })

    results = rg.search(coords)
    
    # Filter to IN
    filtered_cells = []
    for i, res in enumerate(results):
        if res['cc'] == 'IN':
            filtered_cells.append(cells[i])
            
    print(f"Generated {len(filtered_cells)} cells inside India.")

    out = []
    out.append('from typing import List\n')
    out.append('from dataclasses import dataclass\n\n')
    out.append('@dataclass\n')
    out.append('class GridCell:\n')
    out.append('    cell_id: str\n')
    out.append('    name: str\n')
    out.append('    state: str\n')
    out.append('    lat: float\n')
    out.append('    lon: float\n')
    out.append('    lat_min: float\n')
    out.append('    lat_max: float\n')
    out.append('    lon_min: float\n')
    out.append('    lon_max: float\n')
    out.append('    risk_profile: List[str]\n')
    out.append('    population_density: int\n')
    out.append('    \n')
    out.append('    @property\n')
    out.append('    def bbox(self) -> dict:\n')
    out.append('        return {"lat_min": self.lat_min, "lat_max": self.lat_max, "lon_min": self.lon_min, "lon_max": self.lon_max}\n\n')
    out.append('INDIA_GRID: List[GridCell] = [\n')
    
    for c in filtered_cells:
        out.append(f'    GridCell("{c["cid"]}", "{c["name"]}", "India", {c["lat"]:.2f}, {c["lon"]:.2f}, {c["lmin"]:.3f}, {c["lmax"]:.3f}, {c["lnmin"]:.3f}, {c["lnmax"]:.3f}, ["flood"], 100),\n')
        
    out.append(']\n\n')

    # Add PRIORITY_CELLS
    out.append('''# ── Fast lookup ───────────────────────────────────────────────────────────────

GRID_BY_ID = {cell.cell_id: cell for cell in INDIA_GRID}

def get_cell(cell_id: str) -> GridCell:
    return GRID_BY_ID[cell_id]

def get_cells_by_state(state: str) -> List[GridCell]:
    return [c for c in INDIA_GRID if state.lower() in c.state.lower()]

def get_high_risk_cells(hazard: str) -> List[GridCell]:
    return [c for c in INDIA_GRID if hazard.lower() in [r.lower() for r in c.risk_profile]]

def bbox_for_cell(cell_id: str) -> dict:
    cell = GRID_BY_ID[cell_id]
    return cell.bbox

# ── Triage priority — cells checked first in every scan ──────────────────────
# Ordered by historical disaster frequency × population density

PRIORITY_CELLS = [
    "IN_WAYANAD",    # Landslide hotspot
    "IN_CHAMOLI",    # Glacier burst risk
    "IN_BRAHMAPUTRA",# Annual floods
    "IN_SUNDARBANS", # Cyclone + storm surge
    "IN_2484",       # Kolkata — cyclone corridor
    "IN_1769",       # Mumbai — monsoon floods
    "IN_2781",       # Bihar — Kosi floods
    "IN_2788",       # Guwahati — Brahmaputra floods
    "IN_3075",       # Haridwar — flash floods
    "IN_2278",       # Raipur — central floods
    "IN_2269",       # Kutch — earthquake + cyclone
    "IN_1275",       # Chennai — Bay of Bengal cyclones
    "IN_1069",       # Kerala coast — monsoon + landslide
    "IN_1984",       # Puri — Odisha cyclone track
    "IN_1481",       # Patna — Ganga floods
]

if __name__ == "__main__":
    print(f"Total grid cells: {len(INDIA_GRID)}")
    print(f"Priority cells:   {len(PRIORITY_CELLS)}")
''')

    with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'w', encoding='utf-8') as f:
        f.writelines(out)

    print("Success")
