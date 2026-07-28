"""
DisasterMind — Autonomous National Monitor
APScheduler-powered loop that scans all ~70 India grid cells
every hour without any human trigger.

Pipeline per cell:
  1. NASA FIRMS triage (fast — checks hotspot count)
  2. Open-Meteo rainfall (fast)
  3. If flagged → full analysis (elevation, ML, AI brain)
  4. Record to state store
  5. Fire Telegram alert if threshold crossed

The monitor runs as a background thread launched by FastAPI lifespan.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models.india_grid import INDIA_GRID, PRIORITY_CELLS, GridCell
from services.data_fetcher import (
    get_weather,
    get_gee_topography,
    get_road_accessibility,
)
from models.ml_layer.predict import get_predictor
from core.ai_brain import brain
from services.state_store import (
    record_scan,
    get_active_threats,
    should_alert,
    mark_alerted,
    log_agent_event,
    start_monitor_run,
    update_monitor_status,
    complete_monitor_run,
    detect_national_trend,
    clean_old_records,
)
from core.alert_queue import enqueue_cell_alert, enqueue_national_summary
from core.alerter import test_connection
from services.logger import log_request, log_error
import redis
import os

# Redis connection for distributed locking — reads REDIS_URL env var (works on Render)
# Falls back to localhost for local Docker development
try:
    _REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(_REDIS_URL, socket_timeout=5, decode_responses=True)
    redis_client.ping()
    print(f"[Monitor] Redis connected for distributed locking")
except Exception as e:
    print(f"[Monitor] Warning: Redis unavailable for locking: {e}")
    redis_client = None

# ── Triage thresholds ────────────────────────────────────────────────────────
TRIAGE_HOTSPOT_MIN  = 3      # FIRMS hotspots to flag a cell
TRIAGE_RAINFALL_MIN = 15.0   # mm of accumulated rain to flag a cell
TRIAGE_ALWAYS_SCAN  = set(PRIORITY_CELLS)  # always deep-scan these regardless

# ── Scheduler instance (module-level singleton) ───────────────────────────────
scheduler = AsyncIOScheduler(timezone="UTC")
_monitor_running = False


# ── Triage pass — fast check to decide if full scan is needed ─────────────────

async def _triage_cell(cell: GridCell, weather: dict, hotspots: int) -> dict:
    """
    Quick check: FIRMS + Open-Meteo.
    Returns triage result dict.
    """
    rainfall = weather.get("precipitation", [0, 0, 0])
    rain_d1 = rainfall[0] if rainfall else 0.0

    flagged = (
        hotspots >= TRIAGE_HOTSPOT_MIN
        or rain_d1 >= TRIAGE_RAINFALL_MIN
    )

    return {
        "cell": cell,
        "flagged": flagged,
        "hotspots": hotspots,
        "rain_d1": rain_d1,
    }


# ── Full deep analysis for a flagged cell ────────────────────────────────────

async def _deep_scan_cell(cell: GridCell, hotspots: int, rain_d1: float) -> dict:
    """
    Full pipeline for a flagged cell.
    Returns structured result with risk level.
    """
    # Google Earth Engine Suite
    from services.data_fetcher import get_gee_flood_extent, get_gee_population, get_satellite_thumbnail
    try:
        elev, flood_ext, pop, sat = await asyncio.gather(
            get_gee_topography(cell.lat, cell.lon),
            get_gee_flood_extent(cell.lat, cell.lon),
            get_gee_population(cell.lat, cell.lon),
            get_satellite_thumbnail(cell.lat, cell.lon),
            return_exceptions=True
        )
        if isinstance(elev, Exception): elev = {"avg_elevation": 200, "flood_risk": "MODERATE", "landslide_risk": "MODERATE"}
        if isinstance(flood_ext, Exception): flood_ext = {"recent_flood_ratio": 0.0}
        if isinstance(pop, Exception): pop = {"population_density": cell.population_density, "historical_floods": 0.0}
        if isinstance(sat, Exception): sat = {"true_color": "", "false_color": ""}
    except Exception:
        elev = {"avg_elevation": 200, "flood_risk": "MODERATE", "landslide_risk": "MODERATE"}
        flood_ext = {"recent_flood_ratio": 0.0}
        pop = {"population_density": cell.population_density, "historical_floods": 0.0}
        sat = {"true_color": "", "false_color": ""}

    # Roads
    try:
        roads = await get_road_accessibility(
            cell.lat_min, cell.lon_min, cell.lat_max, cell.lon_max
        )
        road_count = roads.get("total_roads", 0)
    except Exception:
        road_count = 0

    # ML prediction
    try:
        ml = get_predictor().get_combined_prediction({
            "rainfall":          rain_d1,
            "temperature":       30.0,
            "river_discharge":   hotspots * 5.0,
            "water_level":       rain_d1 / 10.0,
            "elevation":         elev.get("avg_elevation", 200),
            "population_density": cell.population_density,
            "infrastructure":    1.0,
            "historical_floods": 1.0,
            "hotspot_count":     hotspots,
            "disaster_type":     2,
        })
    except Exception as e:
        print(f"[Monitor] ML Prediction error for {cell.name}: {e}")
        ml = {
            "flood_probability": 0.0,
            "flood_risk": "NONE",
            "severity_label": "NONE",
            "ml_confidence": "LOW",
        }

    # AI Brain — only for HIGH/CRITICAL to save API calls
    flood_prob = ml.get("flood_probability", 0)
    severity   = ml.get("severity_label", "MODERATE")

    # If Earth Engine Sentinel-1 SAR detects anomalous water > 2% of the region area, drastically boost the ML flood probability
    sar_ratio = flood_ext.get("recent_flood_ratio", 0.0)
    if sar_ratio > 0.02:
        # Boost flood prob based on how much of the grid cell is actually underwater right now
        flood_prob = max(flood_prob, min(1.0, sar_ratio * 15))
        severity = "CRITICAL"
        
    # Determine risk level from ML before calling Groq
    risk_level = _compute_risk_level(
        flood_prob, hotspots, rain_d1,
        elev.get("flood_risk", "MODERATE"),
        cell.risk_profile,
    )

    ai_report  = {}
    risk_score = {"LOW": 2, "MODERATE": 5, "HIGH": 7, "CRITICAL": 9}.get(risk_level, 5)

    if risk_level in ("HIGH", "CRITICAL"):
        try:
            weather_data = {"precipitation": [rain_d1, rain_d1*0.8, rain_d1*0.6]}
            ai_report = await asyncio.to_thread(
                brain.analyze_disaster,
                region_name    = cell.name,
                hotspot_count  = hotspots,
                weather_data   = weather_data,
                elevation_data = elev,
                road_count     = road_count,
                ml_prediction  = ml,
            )
            risk_score = ai_report.get("risk_score", risk_score)
        except Exception as e:
            print(f"[Monitor] AI brain error for {cell.name}: {e}")

    return {
        "cell":       cell,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "flood_prob": flood_prob,
        "hotspots":   hotspots,
        "rain_d1":    rain_d1,
        "severity":   severity,
        "ml":         ml,
        "ai_report":  ai_report,
        "elevation":  elev,
        "road_count": road_count,
        "gee_flood":  flood_ext,
        "gee_population": pop,
        "satellite":  sat,
    }


def _compute_risk_level(
    flood_prob: float,
    hotspots: int,
    rainfall: float,
    terrain_flood_risk: str,
    risk_profile: List[str],
) -> str:
    """
    Deterministic risk level from multiple signals.
    Fast — no LLM needed.
    """
    score = 0

    # Flood probability from ML
    if flood_prob >= 0.80: score += 4
    elif flood_prob >= 0.60: score += 3
    elif flood_prob >= 0.40: score += 2
    elif flood_prob >= 0.20: score += 1

    # Hotspot activity
    if hotspots >= 30: score += 3
    elif hotspots >= 15: score += 2
    elif hotspots >= 5: score += 1

    # Rainfall
    if rainfall >= 150: score += 3
    elif rainfall >= 80: score += 2
    elif rainfall >= 40: score += 1

    # Terrain points removed. Static geography shouldn't trigger LIVE alerts. 
    # The ML model already factors elevation into flood_prob anyway.

    if score >= 9:   return "CRITICAL"
    elif score >= 6: return "HIGH"
    elif score >= 3: return "MODERATE"
    elif score >= 1: return "LOW"
    else:            return "NONE"


# ── Main national scan ────────────────────────────────────────────────────────

async def run_national_scan():
    """
    Full autonomous national scan.
    Called by APScheduler every hour.
    """
    global _monitor_running
    if _monitor_running:
        print("[Monitor] Scan already running in this process — skipping")
        return

    # Distributed lock to prevent multiple gunicorn workers from running simultaneous scans
    lock_key = "disastermind:scan_lock"
    if redis_client:
        # Try to acquire lock for 45 minutes (scan should finish well before this)
        acquired = redis_client.set(lock_key, "running", nx=True, ex=2700)
        if not acquired:
            print("[Monitor] Scan already running in another worker — skipping")
            return

    _monitor_running = True
    t_start = time.time()
    run_id  = start_monitor_run()
    now_str = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    print(f"\n[Monitor] {'='*60}")
    print(f"[Monitor] National scan started — {now_str}")
    print(f"[Monitor] Grid cells: {len(INDIA_GRID)}")
    print(f"[Monitor] {'='*60}")

    log_agent_event(
        "SCAN_START",
        f"National scan initiated — scanning {len(INDIA_GRID)} cells across India",
        severity="INFO",
    )

    cells_scanned = 0
    threats_found = 0
    alerts_sent   = 0

    try:
        from services.data_fetcher import fetch_all_india_hotspots, get_weather_batch
        from services.state_store import _get_conn, _lock
        
        # Wipe stale state before starting a new cycle
        with _lock:
            conn = _get_conn()
            conn.execute("DELETE FROM cell_history")
            conn.execute("DELETE FROM active_threats")
            conn.commit()
            conn.close()
            print("[Monitor] Wiped stale DB state for fresh cycle")
        
        print(f"\n[Monitor] {'='*60}")
        print(f"[Monitor] PHASE 1: TRIAGE PASS STARTED")
        print(f"[Monitor] Fetching bulk NASA FIRMS dataset for South Asia...")
        all_hotspots = await fetch_all_india_hotspots()
        print(f"[Monitor] Scanning {len(INDIA_GRID)} grid cells across India...")
        print(f"[Monitor] {'='*60}\n")
        
        log_agent_event("SCAN_START", f"PHASE 1: Triage Pass Started ({len(INDIA_GRID)} cells)", severity="INFO")
        
        flagged_results = []

        batch_size = 100
        for i in range(0, len(INDIA_GRID), batch_size):
            batch = INDIA_GRID[i:i+batch_size]
            
            # 1. Batch fetch weather for 50 cells — stays within Open-Meteo rate limits
            lats = [c.lat for c in batch]
            lons = [c.lon for c in batch]
            weather_results_batch = await get_weather_batch(lats, lons)
            
            # 2. Process triage using the pre-fetched weather and hotspots
            tasks = []
            for idx, cell in enumerate(batch):
                count = sum(1 for h in all_hotspots if (cell.lat_min - 0.02 <= h[0] <= cell.lat_max + 0.02) and (cell.lon_min - 0.02 <= h[1] <= cell.lon_max + 0.02))
                tasks.append(_triage_cell(cell, weather_results_batch[idx] if idx < len(weather_results_batch) else {}, count))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(15.0)
            for r in results:
                if isinstance(r, Exception):
                    continue
                cells_scanned += 1
                if r["flagged"]:
                    flagged_results.append(r)
                else:
                    cell = r["cell"]
                    record_scan(
                        cell_id=cell.cell_id,
                        cell_name=cell.name,
                        state=cell.state,
                        lat=cell.lat,
                        lon=cell.lon,
                        risk_level="NONE",
                        risk_score=0,
                        flood_prob=0.0,
                        hotspots=r.get("hotspots", 0),
                        rainfall_d1=r.get("rain_d1", 0.0),
                        severity="NONE",
                        raw_data={"ml": None, "elevation": {}, "road_count": 0}
                    )
            status_str = f"Phase 1: Triage Pass (Batch {(i//batch_size)+1}/{len(INDIA_GRID)//batch_size + 1}) — {cells_scanned} cells scanned"
            print(f"[Monitor] {status_str}")
            update_monitor_status(run_id, status_str)
            if (i // batch_size) % 20 == 0 or i == 0:
                log_agent_event("SCAN_PROGRESS", status_str, severity="INFO")
            await asyncio.sleep(1.0)  # respect Open-Meteo free tier rate limit

        flagged_count = len(flagged_results)
        print(f"[Monitor] Triage complete — {cells_scanned} cells checked, {flagged_count} flagged")

        log_agent_event(
            "TRIAGE_COMPLETE",
            f"Triage: {cells_scanned} cells scanned, {flagged_count} flagged for deep analysis",
            severity="INFO",
        )

        if flagged_count == 0:
            log_agent_event(
                "ALL_CLEAR",
                "No elevated risk zones detected across India",
                severity="INFO",
            )
            complete_monitor_run(run_id, cells_scanned, 0, 0)
            if redis_client:
                redis_client.delete("disastermind:scan_lock")
            _monitor_running = False
            return

        # ── Phase 2: Deep scan flagged cells ─────────────────────────────────
        print(f"\n[Monitor] {'='*60}")
        print(f"[Monitor] PHASE 1 COMPLETE")
        print(f"[Monitor] {'='*60}")
        
        status_str = f"Phase 2: Deep Scan Started ({flagged_count} flagged cells)"
        print(f"\n[Monitor] {'='*60}")
        print(f"[Monitor] {status_str}")
        print(f"[Monitor] {'='*60}\n")
        update_monitor_status(run_id, status_str)
        log_agent_event("SCAN_START", status_str, severity="INFO")

        # Priority cells first
        priority = [r for r in flagged_results if r["cell"].cell_id in TRIAGE_ALWAYS_SCAN]
        others   = [r for r in flagged_results if r["cell"].cell_id not in TRIAGE_ALWAYS_SCAN]
        ordered  = priority + others

        async def process_cell(triage):
            nonlocal threats_found, alerts_sent
            cell = triage["cell"]
            try:
                result = await _deep_scan_cell(
                    cell,
                    triage["hotspots"],
                    triage["rain_d1"],
                )

                risk_level = result["risk_level"]
                ai         = result.get("ai_report", {})

                # Record to state store
                record_scan(
                    cell_id    = cell.cell_id,
                    cell_name  = cell.name,
                    state      = cell.state,
                    lat        = cell.lat,
                    lon        = cell.lon,
                    risk_level = risk_level,
                    risk_score = result["risk_score"],
                    flood_prob = result["flood_prob"],
                    hotspots   = result["hotspots"],
                    rainfall_d1= result["rain_d1"],
                    severity   = result["severity"],
                    raw_data   = {
                        "ml": result["ml"],
                        "elevation": result["elevation"],
                        "road_count": result["road_count"],
                    },
                )

                if risk_level in ("HIGH", "CRITICAL"):
                    threats_found += 1
                    log_agent_event(
                        f"THREAT_{risk_level}",
                        f"{cell.name} ({cell.state}) — {risk_level} | "
                        f"Hotspots: {result['hotspots']} | "
                        f"Rain: {result['rain_d1']:.0f}mm | "
                        f"Flood prob: {result['flood_prob']:.0%}",
                        cell_id   = cell.cell_id,
                        cell_name = cell.name,
                        severity  = risk_level,
                    )
                    print(f"[Monitor] ⚠ {risk_level}: {cell.name} — "
                          f"hotspots={result['hotspots']} rain={result['rain_d1']:.0f}mm")

                    # Fire Telegram alert if needed
                    if should_alert(cell.cell_id):
                        from services.state_store import get_threat_by_cell
                        threat = get_threat_by_cell(cell.cell_id)
                        await enqueue_cell_alert({
                            "cell_name":       cell.name,
                            "state":           cell.state,
                            "risk_level":      risk_level,
                            "risk_score":      result["risk_score"],
                            "trend":           threat.get("trend", "NEW") if threat else "NEW",
                            "consecutive_hrs": threat.get("consecutive_hrs", 1) if threat else 1,
                            "flood_prob":      result["flood_prob"],
                            "hotspot_count":   result["hotspots"],
                            "rainfall_d1":     result["rain_d1"],
                            "summary":         ai.get("situation_summary", ""),
                            "escalation_risk": ai.get("escalation_risk", ""),
                            "lat":             cell.lat,
                            "lon":             cell.lon,
                        })
                        mark_alerted(cell.cell_id)
                        alerts_sent += 1
                        log_agent_event(
                                "ALERT_SENT",
                                f"Telegram alert dispatched for {cell.name}",
                                cell_id   = cell.cell_id,
                                cell_name = cell.name,
                                severity  = "ALERT",
                            )
                else:
                    print(f"[Monitor] ✓ {risk_level}: {cell.name}")

            except Exception as e:
                log_error_msg = f"Deep scan failed for {cell.name}: {str(e)}"
                print(f"[Monitor] ERROR: {log_error_msg}")
                log_agent_event(
                    "SCAN_ERROR",
                    log_error_msg,
                    cell_id   = cell.cell_id,
                    cell_name = cell.name,
                    severity  = "ERROR",
                )

        await asyncio.gather(*[process_cell(t) for t in ordered])

        # ── Phase 3: National summary ────────────────────────────────────────
        elapsed = time.time() - t_start
        trend   = detect_national_trend()

        await enqueue_national_summary({
            "active_threats":   trend["active_threats"],
            "critical_count":   trend["critical_count"],
            "high_count":       trend["high_count"],
            "escalating_count": trend["escalating_count"],
            "top_threat":       trend["top_threat"],
            "cells_scanned":    cells_scanned,
            "scan_duration_s":  elapsed,
        })

        complete_monitor_run(run_id, cells_scanned, threats_found, alerts_sent)

        log_agent_event(
            "SCAN_COMPLETE",
            f"Scan complete — {cells_scanned} cells, {threats_found} threats, "
            f"{alerts_sent} alerts | {elapsed:.1f}s",
            severity="INFO",
        )

        print(f"\n[Monitor] Scan complete in {elapsed:.1f}s")
        print(f"[Monitor] Threats: {threats_found} | Alerts: {alerts_sent}")
        print(f"[Monitor] National status: {trend['status']}")

    except Exception as e:
        print(f"[Monitor] FATAL scan error: {e}")
        import traceback; traceback.print_exc()
        log_agent_event("SCAN_FATAL", str(e), severity="ERROR")
        complete_monitor_run(run_id, cells_scanned, threats_found, alerts_sent)
    finally:
        if redis_client:
            redis_client.delete("disastermind:scan_lock")
        _monitor_running = False


# ── Scheduler management ──────────────────────────────────────────────────────

def start_scheduler():
    """
    Start the APScheduler.
    Runs full national scan every hour.
    Also fires an immediate scan 30s after startup.
    """
    if scheduler.running:
        return

    # Hourly full scan
    scheduler.add_job(
        run_national_scan,
        "interval",
        hours=12,
        id="national_scan",
        replace_existing=True,
        max_instances=1,
    )

    # Daily DB Cleanup
    scheduler.add_job(
        clean_old_records,
        "interval",
        days=1,
        id="db_cleanup",
        replace_existing=True,
        max_instances=1,
    )

    # Immediate first scan after 30s (gives server time to fully start)
    scheduler.add_job(
        run_national_scan,
        "date",
        run_date=None,         # will be set dynamically at runtime
        id="startup_scan",
        replace_existing=True,
    )

    scheduler.start()
    print("[Monitor] Scheduler started — national scan every 60 minutes")

    # Trigger initial scan
    asyncio.ensure_future(_delayed_startup_scan())


async def _delayed_startup_scan():
    """Wait 30s then fire the first scan."""
    await asyncio.sleep(30)
    print("[Monitor] Running startup scan...")
    await run_national_scan()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Monitor] Scheduler stopped")


def get_scheduler_status() -> dict:
    return {
        "running":        scheduler.running,
        "monitor_active": _monitor_running,
        "next_scan":      str(scheduler.get_job("national_scan").next_run_time)
                          if scheduler.get_job("national_scan") else None,
    }
