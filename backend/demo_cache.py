"""
DisasterMind — Demo Cache Generator
Run this BEFORE recording the demo video.
Pre-generates analysis results for all 3 regions so /demo/{region}
returns instantly without any live API calls.

Usage
-----
    cd backend
    python demo_cache.py
    # Creates: demo_cache/wayanad.json, assam.json, uttarakhand.json
"""

import asyncio
import json
import pathlib
import sys

from agent import run_disaster_analysis

CACHE_DIR = pathlib.Path(__file__).parent / "demo_cache"
CACHE_DIR.mkdir(exist_ok=True)

# ── Preset regions (mirrors main.py) ─────────────────────────────────────────
REGIONS = [
    {
        "id":   "wayanad",
        "name": "Wayanad, Kerala",
        "lat":  11.6,
        "lon":  76.0,
        "bbox": {"lat_min": 11.3, "lat_max": 11.9, "lon_min": 75.7, "lon_max": 76.4},
    },
    {
        "id":   "assam",
        "name": "Kamrup, Assam",
        "lat":  26.2,
        "lon":  91.7,
        "bbox": {"lat_min": 25.9, "lat_max": 26.5, "lon_min": 91.4, "lon_max": 92.0},
    },
    {
        "id":   "uttarakhand",
        "name": "Chamoli, Uttarakhand",
        "lat":  30.4,
        "lon":  79.3,
        "bbox": {"lat_min": 30.1, "lat_max": 30.7, "lon_min": 79.0, "lon_max": 79.6},
    },
]


async def _generate_cache(region: dict) -> dict:
    rid    = region["id"]
    output = CACHE_DIR / f"{rid}.json"

    print(f"\n[DemoCache] Generating {rid}...")
    try:
        result = await run_disaster_analysis(
            region_name = region["name"],
            lat         = region["lat"],
            lon         = region["lon"],
            bbox        = region["bbox"],
        )
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        risk = result.get("situation_report", {}).get("risk_level", "?")
        t_ms = result.get("processing_time_ms", "?")
        print(f"[DemoCache] ✓ {rid}.json saved — Risk: {risk} — {t_ms}ms")
        return result
    except Exception as e:
        print(f"[DemoCache] ✗ Failed for {rid}: {e}")
        import traceback; traceback.print_exc()
        return {}


async def main():
    print("[DemoCache] DisasterMind Demo Cache Generator")
    print("[DemoCache] " + "=" * 50)
    print(f"[DemoCache] Target directory: {CACHE_DIR}")

    results = []
    for region in REGIONS:
        r = await _generate_cache(region)
        results.append(r)

    print("\n[DemoCache] " + "=" * 50)
    print("[DemoCache] Summary:")
    for region, result in zip(REGIONS, results):
        status = "✓ CACHED" if result else "✗ FAILED"
        print(f"  {status}  {region['id']}.json")

    failed = sum(1 for r in results if not r)
    if failed:
        print(f"\n[DemoCache] WARNING: {failed} region(s) failed — check API keys in .env")
        sys.exit(1)
    else:
        print("\n[DemoCache] All demo caches ready. Safe to record demo video.")


if __name__ == "__main__":
    asyncio.run(main())
