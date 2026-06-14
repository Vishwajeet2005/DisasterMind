import re

lat_centers = [8.25, 10.75, 13.25, 15.75, 18.25, 20.75, 23.25, 25.75, 28.25, 30.75, 33.25, 35.75]
lon_centers = [69.75, 72.25, 74.75, 77.25, 79.75, 82.25, 84.75, 87.25, 89.75, 92.25, 94.75]

def snap(val, centers):
    return min(centers, key=lambda c: abs(c - val))

with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'r') as f:
    lines = f.readlines()

out = []
seen = set()

for line in lines:
    if 'GridCell(' in line:
        m = re.search(r'GridCell\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*(\[.*\]),\s*(\d+)\)', line)
        if m:
            cid, name, state, lat, lon, _, _, _, _, risks, pop = m.groups()
            lat = float(lat)
            lon = float(lon)
            
            # Snap to grid
            new_lat = snap(lat, lat_centers)
            new_lon = snap(lon, lon_centers)
            
            # Prevent exact duplicates by nudging
            while (new_lat, new_lon) in seen:
                if new_lon + 2.5 <= 96.0:
                    new_lon += 2.5
                else:
                    new_lat -= 2.5
                    
            seen.add((new_lat, new_lon))
            
            lat_min = new_lat - 1.25
            lat_max = new_lat + 1.25
            lon_min = new_lon - 1.25
            lon_max = new_lon + 1.25
            
            new_line = f'    GridCell("{cid}", "{name}", "{state}", {new_lat:.2f}, {new_lon:.2f}, {lat_min:.2f}, {lat_max:.2f}, {lon_min:.2f}, {lon_max:.2f}, {risks}, {pop}),\n'
            out.append(new_line)
        else:
            out.append(line)
    else:
        out.append(line)

with open(r'd:\DisasterFlow\disastermind\backend\india_grid.py', 'w') as f:
    f.writelines(out)

print("Fixed grid!")
