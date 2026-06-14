import urllib.request
import csv

url = "https://raw.githubusercontent.com/nishusharma1608/India-Census-2011-Analysis/master/india-districts-census-2011.csv"
urllib.request.urlretrieve(url, "d:/DisasterFlow/disastermind/backend/district_census.csv")

# Now read the csv and dump just District -> Density mapping
district_pop = {}

with open("d:/DisasterFlow/disastermind/backend/district_census.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # We need District name. Let's see what the columns are first.
        pass

print(reader.fieldnames)
