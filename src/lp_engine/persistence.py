"""SQLite reference persistence for production entities."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import UTC, datetime
import json, sqlite3

SCHEMA_VERSION = "phase7-sqlite-v1"
def now(): return datetime.now(UTC).isoformat()

class ProductionRepository:
    def __init__(self, path=":memory:"):
        self.path=str(path); self.db=sqlite3.connect(self.path, check_same_thread=False); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON"); self.migrate()
    @contextmanager
    def tx(self):
        try: yield self.db; self.db.commit()
        except Exception: self.db.rollback(); raise
    def migrate(self):
        with self.tx() as d:
            d.executescript("""
            CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS candidates(candidate_id TEXT PRIMARY KEY, company_id TEXT UNIQUE NOT NULL, company_name TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS projects(project_id TEXT PRIMARY KEY, candidate_id TEXT UNIQUE NOT NULL REFERENCES candidates(candidate_id), company_id TEXT NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS generations(generation_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id), company_id TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts(artifact_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id), company_id TEXT NOT NULL, kind TEXT NOT NULL, digest TEXT, immutable INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, correlation_id TEXT NOT NULL, candidate_id TEXT, project_id TEXT, generation_id TEXT, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            """); d.execute("INSERT OR IGNORE INTO schema_migrations VALUES (?,?)",(SCHEMA_VERSION,now()))
    def _row(self, table, key, value):
        r=self.db.execute(f"SELECT * FROM {table} WHERE {key}=?",(value,)).fetchone()
        if not r: raise KeyError("NOT_FOUND")
        x=dict(r); x["payload"]=json.loads(x["payload"]); return x
    def upsert_candidate(self, candidate_id, company_id, payload, status="QUEUED"):
        if not candidate_id or not company_id: raise ValueError("INVALID_INPUT")
        t=now()
        with self.tx() as d: d.execute("INSERT INTO candidates VALUES(?,?,?,?,?,?,?) ON CONFLICT(candidate_id) DO UPDATE SET payload=excluded.payload,status=excluded.status,updated_at=excluded.updated_at",(candidate_id,company_id,payload.get("company_name",company_id),json.dumps(payload,ensure_ascii=False),status,t,t))
        return self._row("candidates","candidate_id",candidate_id)
    def create_project(self, project_id, candidate_id, company_id, payload=None, state="NEW"):
        t=now()
        with self.tx() as d:
            c=d.execute("SELECT company_id FROM candidates WHERE candidate_id=?",(candidate_id,)).fetchone()
            if not c: raise KeyError("NOT_FOUND")
            if c["company_id"]!=company_id: raise ValueError("CONFLICT_CROSS_COMPANY")
            d.execute("INSERT OR IGNORE INTO projects VALUES(?,?,?,?,?,?,?)",(project_id,candidate_id,company_id,state,json.dumps(payload or {}),t,t))
        return self._row("projects","project_id",project_id)
    def record_generation(self, generation_id, project_id, company_id, payload=None, status="QUEUED"):
        with self.tx() as d:
            p=d.execute("SELECT company_id FROM projects WHERE project_id=?",(project_id,)).fetchone()
            if not p: raise KeyError("NOT_FOUND")
            if p["company_id"]!=company_id: raise ValueError("CONFLICT_CROSS_COMPANY")
            d.execute("INSERT OR IGNORE INTO generations VALUES(?,?,?,?,?,?)",(generation_id,project_id,company_id,status,json.dumps(payload or {}),now()))
        return self._row("generations","generation_id",generation_id)
    def artifact(self, artifact_id, project_id, company_id, kind, digest, payload=None, immutable=False):
        with self.tx() as d:
            p=d.execute("SELECT company_id FROM projects WHERE project_id=?",(project_id,)).fetchone()
            if not p: raise KeyError("NOT_FOUND")
            if p["company_id"]!=company_id: raise ValueError("CONFLICT_CROSS_COMPANY")
            d.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?,?,?,?,?)",(artifact_id,project_id,company_id,kind,digest,int(immutable),json.dumps(payload or {}),now()))
        return self._row("artifacts","artifact_id",artifact_id)
    def audit(self, correlation_id, event_type, payload, candidate_id=None, project_id=None, generation_id=None):
        with self.tx() as d: d.execute("INSERT INTO audit_events(correlation_id,candidate_id,project_id,generation_id,event_type,payload,created_at) VALUES(?,?,?,?,?,?,?)",(correlation_id,candidate_id,project_id,generation_id,event_type,json.dumps(payload),now()))
    def get_candidate(self,x): return self._row("candidates","candidate_id",x)
    def get_project(self,x): return self._row("projects","project_id",x)
    def get_generation(self,x): return self._row("generations","generation_id",x)
    def health(self): return {"schema_version":SCHEMA_VERSION,"integrity":self.db.execute("PRAGMA integrity_check").fetchone()[0],**{k:self.db.execute(f"SELECT COUNT(*) FROM {k}").fetchone()[0] for k in ("candidates","projects","generations","artifacts")}}
    def close(self): self.db.close()
