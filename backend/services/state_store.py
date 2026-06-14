"""
DisasterMind — State Store
SQLite-backed persistent memory for the autonomous monitor.
Tracks risk history per cell, detects worsening trends,
and drives automatic escalation decisions.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict

DB_PATH = Path(__file__).parent.parent / "data" / "disastermind_state.db"
_lock = threading.Lock()

# Risk level numeric mapping (higher = worse)
RISK_NUMERIC = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
RISK_FROM_NUMERIC = {v: k for k, v in RISK_NUMERIC.items()}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads during writes — eliminates "database is locked"
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_db():
    """Create tables if they don't exist, and flush old demo data on restart."""
    with _lock:
        conn = _get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cell_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cell_id     TEXT NOT NULL,
                cell_name   TEXT NOT NULL,
                state       TEXT NOT NULL,
                lat         REAL NOT NULL,
                lon         REAL NOT NULL,
                risk_level  TEXT NOT NULL,
                risk_score  INTEGER NOT NULL,
                flood_prob  REAL,
                hotspots    INTEGER,
                rainfall_d1 REAL,
                severity    TEXT,
                scanned_at  TEXT NOT NULL,
                raw_json    TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_cell_history_cell
                ON cell_history(cell_id, scanned_at DESC);

            CREATE TABLE IF NOT EXISTS active_threats (
                cell_id         TEXT PRIMARY KEY,
                cell_name       TEXT NOT NULL,
                state           TEXT NOT NULL,
                lat             REAL NOT NULL,
                lon             REAL NOT NULL,
                risk_level      TEXT NOT NULL,
                risk_score      INTEGER NOT NULL,
                consecutive_hrs INTEGER DEFAULT 1,
                first_detected  TEXT NOT NULL,
                last_updated    TEXT NOT NULL,
                trend           TEXT DEFAULT 'STABLE',
                alerted         INTEGER DEFAULT 0,
                summary         TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                cell_id    TEXT,
                cell_name  TEXT,
                message    TEXT NOT NULL,
                severity   TEXT DEFAULT 'INFO',
                logged_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS monitor_runs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at    TEXT NOT NULL,
                completed_at  TEXT,
                cells_scanned INTEGER DEFAULT 0,
                threats_found INTEGER DEFAULT 0,
                alerts_sent   INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'RUNNING'
            );
        """)
        conn.commit()
        conn.close()


def clean_old_records(max_history=2000, max_logs=2000, max_runs=100):
    """Delete old records and vacuum to keep DB size constrained."""
    with _lock:
        conn = _get_conn()
        try:
            conn.execute("DELETE FROM cell_history WHERE id NOT IN (SELECT id FROM cell_history ORDER BY id DESC LIMIT ?)", (int(max_history),))
            conn.execute("DELETE FROM agent_log WHERE id NOT IN (SELECT id FROM agent_log ORDER BY id DESC LIMIT ?)", (int(max_logs),))
            conn.execute("DELETE FROM monitor_runs WHERE id NOT IN (SELECT id FROM monitor_runs ORDER BY id DESC LIMIT ?)", (int(max_runs),))
            conn.commit()
            conn.execute("VACUUM")
            print("[StateStore] DB Cleanup & Vacuum completed.")
        except Exception as e:
            print(f"[StateStore] DB Cleanup failed: {e}")
        finally:
            conn.close()



# ── Cell history ──────────────────────────────────────────────────────────────

def record_scan(
    cell_id: str,
    cell_name: str,
    state: str,
    lat: float,
    lon: float,
    risk_level: str,
    risk_score: int,
    flood_prob: float,
    hotspots: int,
    rainfall_d1: float,
    severity: str,
    raw_data: dict,
) -> None:
    """Record a completed cell scan to history."""
    with _lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO cell_history
            (cell_id, cell_name, state, lat, lon, risk_level, risk_score,
             flood_prob, hotspots, rainfall_d1, severity, scanned_at, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            cell_id, cell_name, state, lat, lon,
            risk_level, risk_score, flood_prob, hotspots,
            rainfall_d1, severity,
            datetime.now(timezone.utc).isoformat(),
            json.dumps(raw_data, default=str),
        ))
        conn.commit()
        conn.close()

    _update_active_threat(
        cell_id, cell_name, state, lat, lon,
        risk_level, risk_score, rainfall_d1, hotspots,
    )


def get_cell_history(cell_id: str, limit: int = 24) -> List[dict]:
    """Return last N scan records for a cell."""
    with _lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM cell_history
            WHERE cell_id = ?
            ORDER BY scanned_at DESC
            LIMIT ?
        """, (cell_id, limit)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def get_recent_history(hours: int = 6) -> List[dict]:
    """Return all scans across all cells in the last N hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with _lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM cell_history
            WHERE scanned_at > ?
            ORDER BY scanned_at DESC
        """, (cutoff,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ── Active threat tracking ────────────────────────────────────────────────────

def _update_active_threat(
    cell_id: str,
    cell_name: str,
    state: str,
    lat: float,
    lon: float,
    risk_level: str,
    risk_score: int,
    rainfall_d1: float,
    hotspots: int,
) -> None:
    """
    Upsert active_threats table.
    Increments consecutive_hrs if still active.
    Removes record if risk drops to LOW.
    Computes trend: ESCALATING / STABLE / IMPROVING.
    """
    now = datetime.now(timezone.utc).isoformat()

    with _lock:
        conn = _get_conn()

        if risk_level in ["LOW", "NONE"]:
            conn.execute("DELETE FROM active_threats WHERE cell_id = ?", (cell_id,))
            conn.commit()
            conn.close()
            return

        existing = conn.execute(
            "SELECT * FROM active_threats WHERE cell_id = ?", (cell_id,)
        ).fetchone()

        if existing:
            prev_score = existing["risk_score"]
            trend = (
                "ESCALATING" if risk_score > prev_score
                else "IMPROVING" if risk_score < prev_score
                else "STABLE"
            )
            conn.execute("""
                UPDATE active_threats
                SET risk_level=?, risk_score=?, consecutive_hrs=consecutive_hrs+1,
                    last_updated=?, trend=?, alerted=CASE WHEN ?=? THEN alerted ELSE 0 END
                WHERE cell_id=?
            """, (
                risk_level, risk_score, now, trend,
                risk_level, existing["risk_level"],
                cell_id,
            ))
        else:
            conn.execute("""
                INSERT INTO active_threats
                (cell_id, cell_name, state, lat, lon, risk_level, risk_score,
                 consecutive_hrs, first_detected, last_updated, trend, alerted)
                VALUES (?,?,?,?,?,?,?,1,?,?,?,0)
            """, (
                cell_id, cell_name, state, lat, lon,
                risk_level, risk_score, now, now, "NEW",
            ))

        conn.commit()
        conn.close()


def get_active_threats() -> List[dict]:
    """Return all currently active threat zones, ranked by risk score."""
    with _lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM active_threats
            ORDER BY risk_score DESC, consecutive_hrs DESC
        """).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def get_threat_by_cell(cell_id: str) -> Optional[dict]:
    with _lock:
        conn = _get_conn()
        row = conn.execute(
            "SELECT * FROM active_threats WHERE cell_id = ?", (cell_id,)
        ).fetchone()
        conn.close()
    return dict(row) if row else None


def mark_alerted(cell_id: str) -> None:
    with _lock:
        conn = _get_conn()
        conn.execute(
            "UPDATE active_threats SET alerted=1 WHERE cell_id=?", (cell_id,)
        )
        conn.commit()
        conn.close()


def should_alert(cell_id: str) -> bool:
    """
    Returns True if this cell should trigger a Telegram alert.
    Conditions:
    - Risk is HIGH or CRITICAL
    - Not already alerted at this risk level
    - OR risk has escalated since last alert
    """
    threat = get_threat_by_cell(cell_id)
    if not threat:
        return False
    if threat["risk_level"] not in ("HIGH", "CRITICAL"):
        return False
    if threat["alerted"] == 0:
        return True
    if threat["trend"] == "ESCALATING":
        return True
    if threat["consecutive_hrs"] % 3 == 0 and threat["risk_level"] == "CRITICAL":
        return True
    return False


# ── Trend analysis ────────────────────────────────────────────────────────────

def detect_national_trend() -> dict:
    """
    Analyse the last 6 hours of scans across all cells.
    Returns a national-level trend summary.
    """
    recent = get_recent_history(hours=6)
    if not recent:
        return {"status": "NO_DATA", "active_threats": 0, "escalating": 0}

    threats = get_active_threats()
    escalating = [t for t in threats if t["trend"] == "ESCALATING"]
    critical   = [t for t in threats if t["risk_level"] == "CRITICAL"]
    high       = [t for t in threats if t["risk_level"] == "HIGH"]

    national_status = "NORMAL"
    if len(critical) >= 2 or (len(critical) >= 1 and len(escalating) >= 2):
        national_status = "SEVERE"
    elif len(critical) >= 1 or len(high) >= 3:
        national_status = "ELEVATED"
    elif len(high) >= 1:
        national_status = "WATCH"

    return {
        "status":          national_status,
        "active_threats":  len(threats),
        "critical_count":  len(critical),
        "high_count":      len(high),
        "escalating_count":len(escalating),
        "top_threat":      threats[0]["cell_name"] if threats else None,
        "top_risk_level":  threats[0]["risk_level"] if threats else "LOW",
    }


# ── Agent activity log ────────────────────────────────────────────────────────

def log_agent_event(
    event_type: str,
    message: str,
    cell_id: str = None,
    cell_name: str = None,
    severity: str = "INFO",
) -> None:
    with _lock:
        conn = _get_conn()
        conn.execute("""
            INSERT INTO agent_log (event_type, cell_id, cell_name, message, severity, logged_at)
            VALUES (?,?,?,?,?,?)
        """, (
            event_type, cell_id, cell_name, message, severity,
            datetime.now(timezone.utc).isoformat(),
        ))
        conn.commit()
        conn.close()


def get_agent_log(limit: int = 50) -> List[dict]:
    with _lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM agent_log
            ORDER BY logged_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ── Monitor run tracking ──────────────────────────────────────────────────────

def start_monitor_run() -> int:
    with _lock:
        conn = _get_conn()
        cursor = conn.execute("""
            INSERT INTO monitor_runs (started_at, status)
            VALUES (?, 'RUNNING')
        """, (datetime.now(timezone.utc).isoformat(),))
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
    return run_id


def update_monitor_status(run_id: int, status: str) -> None:
    with _lock:
        conn = _get_conn()
        conn.execute("""
            UPDATE monitor_runs
            SET status=?
            WHERE id=?
        """, (status, run_id))
        conn.commit()
        conn.close()


def complete_monitor_run(
    run_id: int,
    cells_scanned: int,
    threats_found: int,
    alerts_sent: int,
) -> None:
    with _lock:
        conn = _get_conn()
        conn.execute("""
            UPDATE monitor_runs
            SET completed_at=?, cells_scanned=?, threats_found=?,
                alerts_sent=?, status='COMPLETED'
            WHERE id=?
        """, (
            datetime.now(timezone.utc).isoformat(),
            cells_scanned, threats_found, alerts_sent, run_id,
        ))
        conn.commit()
        conn.close()


def get_last_run() -> Optional[dict]:
    with _lock:
        conn = _get_conn()
        row = conn.execute("""
            SELECT * FROM monitor_runs
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        conn.close()
    return dict(row) if row else None


def get_national_heatmap() -> List[dict]:
    """
    Return latest risk reading for every cell that has been scanned.
    Used by frontend to render the India heatmap.
    """
    with _lock:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT ch.*
            FROM cell_history ch
            INNER JOIN (
                SELECT cell_id, MAX(scanned_at) as latest
                FROM cell_history
                GROUP BY cell_id
            ) latest ON ch.cell_id = latest.cell_id
                     AND ch.scanned_at = latest.latest
            ORDER BY ch.risk_score DESC
        """).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# Initialise on import
init_db()
