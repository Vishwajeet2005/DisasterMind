import sqlite3

db = r'd:\DisasterFlow\disastermind\backend\disastermind_state.db'
conn = sqlite3.connect(db, timeout=30)

# Enable WAL mode to fix database locking issues under concurrent access
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA busy_timeout=10000')

# Remove ALL injected fake threats - the test cells I injected earlier
# These cell_ids start with IN_21_75_74 (Maharashtra test cells)
conn.execute("DELETE FROM active_threats WHERE cell_id IN ('IN_21_75_74_0', 'IN_21_75_74_25', 'IN_21_75_74_5', 'IN_21_75_73_75')")
conn.execute("DELETE FROM cell_history WHERE cell_id IN ('IN_21_75_74_0', 'IN_21_75_74_25', 'IN_21_75_74_5', 'IN_21_75_73_75') AND risk_level IN ('CRITICAL','HIGH','MODERATE')")

remaining = conn.execute('SELECT cell_id, cell_name, risk_level FROM active_threats').fetchall()
print('Remaining active threats:', remaining)

conn.commit()
conn.close()
print('Done - all fake threats removed, WAL mode enabled')
