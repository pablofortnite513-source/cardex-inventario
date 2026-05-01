import sqlite3
db = r"c:\Users\piedr\OneDrive\Desktop\primarias\Primarias\data\kardex.db"
conn = sqlite3.connect(db)
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:", tables)
for t in tables:
    cur2 = conn.execute(f"PRAGMA table_info({t})")
    cols = [(r[1], r[2]) for r in cur2.fetchall()]
    print(f"\n{t}: {cols}")
conn.close()
