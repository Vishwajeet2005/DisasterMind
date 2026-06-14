import ee

def get_gee_layers():
    try:
        ee.Initialize(project='ai-disaster-monitor')
    except Exception:
        pass
    
    # DEM
    dem = ee.Image('USGS/SRTMGL1_003')
    dem_vis = {'min': 0, 'max': 3000, 'palette': ['000000', '478F1E', 'A1A424', 'D9BC35', 'C38820', '95511A', '5E2E0A', '59463F', '746F6A', '9E9C99', 'DEDCD9', 'FFFFFF']}
    dem_mapid = dem.getMapId(dem_vis)
    
    # Surface Water
    water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
    water_vis = {'min': 0, 'max': 100, 'palette': ['ffffff', 'ffbbbb', '0000ff']}
    water_mapid = water.getMapId(water_vis)

    # MODIS LST (Land Surface Temperature)
    lst = ee.ImageCollection('MODIS/061/MOD11A1').select('LST_Day_1km').filterDate('2024-01-01', '2024-12-31').median()
    lst_vis = {'min': 13000, 'max': 16500, 'palette': ['040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6', '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef', '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f', 'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d', 'ff0000', 'de0101', 'c21301', 'a71001', '911003']}
    lst_mapid = lst.getMapId(lst_vis)

    return {
        "dem": dem_mapid['tile_fetcher'].urlFormat,
        "water": water_mapid['tile_fetcher'].urlFormat,
        "lst": lst_mapid['tile_fetcher'].urlFormat
    }

print(get_gee_layers())
