import os
import sys

# Add backend to path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.india_grid import INDIA_GRID
from global_land_mask import globe

print(f"Original grid size: {len(INDIA_GRID)} cells")

land_cells = []
for cell in INDIA_GRID:
    # globe.is_land returns True if the point is on land
    if globe.is_land(cell.lat, cell.lon):
        land_cells.append(cell)

print(f"Filtered grid size: {len(land_cells)} cells (removed {len(INDIA_GRID) - len(land_cells)} ocean cells)")

# Now write back to models/india_grid.py
out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'india_grid.py'))

with open(out_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
in_grid = False

for line in lines:
    if 'INDIA_GRID: List[GridCell] =' in line:
        out.append(line)
        in_grid = True
        
        # Write all land cells
        for c in land_cells:
            # We need to format the risk_profile list properly
            risks_str = '["' + '", "'.join(c.risk_profile) + '"]'
            out.append(f'    GridCell("{c.cell_id}", "{c.name}", "{c.state}", {c.lat:.2f}, {c.lon:.2f}, {c.lat_min:.3f}, {c.lat_max:.3f}, {c.lon_min:.3f}, {c.lon_max:.3f}, {risks_str}, {c.population_density}),\n')
            
        continue
        
    if in_grid:
        if line.strip() == ']' or line.strip() == '],':
            in_grid = False
            out.append(']\n')
        continue
        
    out.append(line)

with open(out_path, 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Ocean clipping complete. Successfully updated models/india_grid.py")
