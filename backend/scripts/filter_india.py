import re
import reverse_geocoder as rg

with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
in_grid = False
grid_cells = []

# Parse the file
for line in lines:
    if 'INDIA_GRID: List[GridCell] =' in line:
        out.append(line)
        in_grid = True
        continue
    
    if in_grid:
        if line.strip() == ']' or line.strip() == '],':
            # End of grid
            in_grid = False
            # Now filter grid_cells
            coords = [(float(c['lat']), float(c['lon'])) for c in grid_cells]
            results = rg.search(coords)
            
            for i, res in enumerate(results):
                # Keep if country code is IN
                if res['cc'] == 'IN' or res['cc'] == 'BT' or res['cc'] == 'NP':
                    # Sometimes borders are slightly off, keeping Bhutan and Nepal just to avoid holes near the border is okay, but user said clip strictly. Let's just do 'IN'
                    pass
                if res['cc'] == 'IN':
                    out.append(grid_cells[i]['line'])
            
            out.append(']\n')
            continue
            
        m = re.search(r'GridCell\("[^"]+",\s*"[^"]+",\s*"[^"]+",\s*([\d\.]+),\s*([\d\.]+)', line)
        if m:
            lat = m.group(1)
            lon = m.group(2)
            grid_cells.append({'lat': lat, 'lon': lon, 'line': line})
            continue
        
    out.append(line)

with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print(f"Filtered grid down to landmass! Kept {len([res for res in rg.search([(float(c['lat']), float(c['lon'])) for c in grid_cells]) if res['cc'] == 'IN'])} cells.")
