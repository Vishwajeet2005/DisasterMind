import sys
import os
import reverse_geocoder as rg
from global_land_mask import globe
import numpy as np

if __name__ == '__main__':
    # Bounding box covering all of India (including Andaman and Nicobar)
    lat_min_in = 6.0
    lat_max_in = 36.0
    lon_min_in = 68.0
    lon_max_in = 98.0
    step = 0.25

    lat_centers = np.arange(lat_min_in, lat_max_in + step, step)
    lon_centers = np.arange(lon_min_in, lon_max_in + step, step)

    coords = []
    cells = []

    for lat in lat_centers:
        for lon in lon_centers:
            coords.append((lat, lon))
            
            cid = f"IN_{str(lat).replace('.','_')}_{str(lon).replace('.','_')}"
            name = f"Region {lat:.2f}N {lon:.2f}E"
            lmin = lat - (step/2)
            lmax = lat + (step/2)
            lnmin = lon - (step/2)
            lnmax = lon + (step/2)
            
            cells.append({
                'cid': cid, 'name': name, 'lat': lat, 'lon': lon,
                'lmin': lmin, 'lmax': lmax, 'lnmin': lnmin, 'lnmax': lnmax
            })

    print(f"Total raw cells in bounding box: {len(cells)}")

    # Reverse geocode all centers
    print("Running reverse_geocoder...")
    results = rg.search(coords)

    valid_cells = []

    print("Filtering cells for IN and landmass...")
    for i, res in enumerate(results):
        c = cells[i]
        
        # 1. Must belong to India
        if res['cc'] != 'IN':
            continue
            
        # 2. Must intersect land
        # Check center and 4 corners
        points_to_check = [
            (c['lat'], c['lon']),         # Center
            (c['lmin'], c['lnmin']),      # Bottom-left
            (c['lmax'], c['lnmax']),      # Top-right
            (c['lmin'], c['lnmax']),      # Bottom-right
            (c['lmax'], c['lnmin'])       # Top-left
        ]
        
        touches_land = False
        for plat, plon in points_to_check:
            if globe.is_land(plat, plon):
                touches_land = True
                break
                
        if touches_land:
            # Assign basic risk and state
            state = res.get('admin1', 'India')
            if not state:
                state = 'India'
                
            c['state'] = state
            
            city = res.get('name', '')
            district = res.get('admin2', '')
            if city and district and city != district:
                c['name'] = f"{city}, {district}"
            elif city:
                c['name'] = city
            elif district:
                c['name'] = district
            else:
                c['name'] = f"{state} Region"
                
            # Simple risk heuristic based on location
            risks = []
            if c['lat'] > 28: risks.extend(["landslide", "earthquake"])
            elif c['lat'] < 20 and c['lon'] < 78: risks.extend(["cyclone", "flood"])
            elif c['lat'] < 20 and c['lon'] >= 78: risks.extend(["cyclone"])
            else: risks.extend(["flood", "heatwave"])
            
            c['risks'] = risks
            
            # Realistic Population Density heuristics (per sq km)
            if c['lat'] > 28 and c['lon'] < 81:
                c['pop'] = int(np.random.randint(30, 150))
            elif 24 <= c['lat'] <= 28.5 and 68 <= c['lon'] < 76:
                c['pop'] = int(np.random.randint(50, 250))
            elif 24 <= c['lat'] <= 28 and 76 <= c['lon'] <= 88:
                c['pop'] = int(np.random.randint(800, 1500))
            elif 8 <= c['lat'] < 24 and c['lon'] < 75:
                c['pop'] = int(np.random.randint(500, 1000))
            elif 8 <= c['lat'] <= 22 and 78 <= c['lon'] <= 88:
                c['pop'] = int(np.random.randint(400, 900))
            else:
                c['pop'] = int(np.random.randint(200, 600))
            
            valid_cells.append(c)

    print(f"Generated {len(valid_cells)} perfect land cells for India.")

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'india_grid.py'))

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('from typing import List\n')
        f.write('from dataclasses import dataclass\n\n')
        f.write('@dataclass\n')
        f.write('class GridCell:\n')
        f.write('    cell_id: str\n')
        f.write('    name: str\n')
        f.write('    state: str\n')
        f.write('    lat: float\n')
        f.write('    lon: float\n')
        f.write('    lat_min: float\n')
        f.write('    lat_max: float\n')
        f.write('    lon_min: float\n')
        f.write('    lon_max: float\n')
        f.write('    risk_profile: List[str]\n')
        f.write('    population_density: int\n')
        f.write('    \n')
        f.write('    @property\n')
        f.write('    def bbox(self) -> dict:\n')
        f.write('        return {"lat_min": self.lat_min, "lat_max": self.lat_max, "lon_min": self.lon_min, "lon_max": self.lon_max}\n\n')
        
        f.write('INDIA_GRID: List[GridCell] = [\n')
        for c in valid_cells:
            risks_str = '["' + '", "'.join(c['risks']) + '"]'
            f.write(f'    GridCell("{c["cid"]}", "{c["name"]}", "{c["state"]}", {c["lat"]:.2f}, {c["lon"]:.2f}, {c["lmin"]:.3f}, {c["lmax"]:.3f}, {c["lnmin"]:.3f}, {c["lnmax"]:.3f}, {risks_str}, {c["pop"]}),\n')
        f.write(']\n\n')
        
        f.write('''# ── Fast lookup ───────────────────────────────────────────────────────────────

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
''')

    print("Saved new INDIA_GRID to models/india_grid.py")
