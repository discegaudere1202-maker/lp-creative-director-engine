"""Live-pilot readiness gate. It never sends or publishes."""
REQUIRED=("freshness","identity","contact","package","safety","rights","qa","screenshot","opportunity")
def evaluate(row):
    checks={k:row.get(k) for k in REQUIRED}; ready=all(v in (True,"PASS","FRESH","STRONG_IMPROVEMENT","IMPROVEMENT","NO_WEB_OPPORTUNITY") for v in checks.values())
    return {"candidate_id":row.get("candidate_id"),"status":"PILOT_READY" if ready else "PILOT_HOLD","checks":checks,"external_send":0,"public_publish":0}
def select(rows): return [evaluate(x) for x in rows]
