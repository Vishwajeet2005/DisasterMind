import sqlite3
from pathlib import Path

DB_PATH = Path("disastermind_state.db")

try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    threats = conn.execute("SELECT cell_id, cell_name, risk_level, last_updated FROM active_threats").fetchall()
    
    print(f"Total active threats in DB: {len(threats)}")
    for t in threats:
        print(dict(t))
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
