import re

# Read original file
with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'r') as f:
    lines = f.readlines()

existing_cells = {}
for line in lines:
    if 'GridCell(' in line:
        m = re.search(r'GridCell\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*(\[.*\]),\s*(\d+)\)', line)
        if m:
            cid, name, state, lat, lon, lmin, lmax, lnmin, lnmax, risks, pop = m.groups()
            existing_cells[(float(lat), float(lon))] = (cid, name, state, risks, pop)
        
lat_centers = [8.25 + 1.25*i for i in range(23)] # 8.25 to 35.75
lon_centers = [69.75 + 1.25*i for i in range(21)] # 69.75 to 94.75

out = []
# header
for line in lines:
    if 'INDIA_GRID: List[GridCell] =' in line:
        out.append(line)
        break
    out.append(line)

for lat in reversed(lat_centers):
    for lon in lon_centers:
        if (lat, lon) in existing_cells:
            cid, name, state, risks, pop = existing_cells[(lat, lon)]
        else:
            cid = f"IN_{int(lat):02d}{int(lon):02d}"
            name = f"Region {lat:.2f}N {lon:.2f}E"
            state = "India"
            risks = '["flood"]'
            pop = "100"
            
        lat_min = lat - 0.625
        lat_max = lat + 0.625
        lon_min = lon - 0.625
        lon_max = lon + 0.625
        
        new_line = f'    GridCell("{cid}", "{name}", "{state}", {lat:.2f}, {lon:.2f}, {lat_min:.3f}, {lat_max:.3f}, {lon_min:.3f}, {lon_max:.3f}, {risks}, {pop}),\n'
        out.append(new_line)

out.append(']\n')

# tail
tail_start = False
for line in lines:
    if '# ── Fast lookup ──' in line:
        tail_start = True
    if tail_start:
        out.append(line)

with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'w') as f:
    f.writelines(out)

print("Dense 483-cell grid generated!")
