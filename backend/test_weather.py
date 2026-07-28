import asyncio
import json
from models.india_grid import INDIA_GRID
from services.data_fetcher import get_weather_batch
import traceback

async def test():
    try:
        results = []
        batch_size = 50
        for i in range(0, len(INDIA_GRID), batch_size):
            batch = INDIA_GRID[i:i+batch_size]
            lats = [c.lat for c in batch]
            lons = [c.lon for c in batch]
            r = await get_weather_batch(lats, lons)
            results.extend(r)
            
        for idx, r in enumerate(results):
            if "error" in r:
                print(f"Error in batch for cell {INDIA_GRID[idx].cell_id}: {r['error']}")
        
        pen_cell = next((i for i, c in enumerate(INDIA_GRID) if c.cell_id == 'IN_18_75_73_0'), -1)
        if pen_cell != -1:
            print(f"Pen, Raigarh precipitation: {results[pen_cell]}")

    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
