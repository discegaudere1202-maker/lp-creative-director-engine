"""Freshness TTL and send-gate contract."""
from datetime import UTC, datetime, timedelta
TTL={"contact":7,"web_status":30,"company_name":90,"identity":90}
def _parse(x):
    try: return datetime.fromisoformat(str(x).replace("Z","+00:00")).astimezone(UTC)
    except (TypeError,ValueError): return None
def status(checked_at, kind="web_status", now=None):
    t=_parse(checked_at)
    if not t: return "UNKNOWN"
    age=(now or datetime.now(UTC))-t; ttl=timedelta(days=TTL.get(kind,30))
    return "FRESH" if timedelta(0)<=age<=ttl else "STALE" if age<=ttl*2 else "RECHECK_REQUIRED"
def check(candidate, now=None):
    checks={k:status(candidate.get("research_timestamp"),k,now) for k in TTL}
    overall="FRESH" if all(x=="FRESH" for x in checks.values()) else "UNKNOWN" if "UNKNOWN" in checks.values() else "RECHECK_REQUIRED"
    return {"status":overall,"checks":checks,"sales_send_ready":False,"reason":"EXTERNAL_SALES_DISABLED","source_timestamp":candidate.get("research_timestamp")}
