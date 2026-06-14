import urllib.request
url = "https://raw.githubusercontent.com/adarshdivya/indian-districts-census-2011/master/india_census_2011_district.csv"
try:
    urllib.request.urlretrieve(url, "d:/DisasterFlow/disastermind/backend/district_census.csv")
    print("Downloaded district census data")
except Exception as e:
    print(e)
