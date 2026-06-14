import json
import csv

district_pop = {}
with open("d:/DisasterFlow/disastermind/backend/district_census.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        dname = row['District name'].lower().replace(' ', '')
        pop = int(row['Population'])
        district_pop[dname] = pop

def get_pop(district, state):
    d = district.lower().replace(' ', '').replace('district', '')
    for k, v in district_pop.items():
        if k in d or d in k:
            return max(10, int(v / 4000))  # approx density
    return None

with open("d:/DisasterFlow/disastermind/backend/geo_dump.json", "r") as f:
    geo_data = json.load(f)

found = 0
for g in geo_data:
    if g['cc'] == 'IN' and g['admin2']:
        pop = get_pop(g['admin2'], g['admin1'])
        if pop:
            found += 1

print(f"Matched {found} out of {len([g for g in geo_data if g['cc']=='IN'])} Indian districts.")
