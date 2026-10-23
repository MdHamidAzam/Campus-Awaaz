"""See what is stored in the database (no extra software needed).
   python scripts/show_db.py            -> table list with row counts
   python scripts/show_db.py users      -> rows of one table (password hashes hidden)"""
import sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import DB_PATH

if not DB_PATH.exists(): sys.exit(f"Database not created yet: {DB_PATH}\nStart the backend once (uvicorn app.main:app) and it will be created.")
c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row
print("Database file:", DB_PATH)
if len(sys.argv) < 2:
    for (t,) in c.execute("select name from sqlite_master where type='table' order by name"):
        print(f"  {t:<8} {c.execute(f'select count(*) from {t}').fetchone()[0]} rows")
else:
    t = sys.argv[1]
    for r in c.execute(f"select * from {t} order by rowid desc limit 50"):
        print({k: ('***' if k in ('h', 'salt', 'token') else r[k]) for k in r.keys()})
