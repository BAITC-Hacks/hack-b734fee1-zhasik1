import json, sqlite3
from datetime import datetime
def init_db(path="qor.db"):
    c=sqlite3.connect(path); c.execute("CREATE TABLE IF NOT EXISTS order_versions (id INTEGER PRIMARY KEY, run_id TEXT, state TEXT, payload TEXT, reason TEXT, created_at TEXT)"); c.commit(); return c
def save_run(conn, run_id, state, payload, reason=""):
    conn.execute("INSERT INTO order_versions(run_id,state,payload,reason,created_at) VALUES(?,?,?,?,?)",(run_id,state,json.dumps(payload,default=str),reason,datetime.utcnow().isoformat()));conn.commit()
def transition(conn, run_id, state, payload, reason=""):
    if state not in {"draft","review","approved","exported"}: raise ValueError("invalid state")
    save_run(conn,run_id,state,payload,reason)
