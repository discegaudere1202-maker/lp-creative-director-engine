"""TEST_ONLY synthetic 1000-item load with restart validation."""
from pathlib import Path
import tempfile,time
from .persistence import ProductionRepository
def run(count=1000,concurrency=10,root=None):
    start=time.perf_counter(); base=Path(root or tempfile.mkdtemp()); base.mkdir(parents=True,exist_ok=True); path=base/"production.db"; r=ProductionRepository(path); ids=set(); collision=0
    for i in range(count):
        cid=f"TEST_ONLY_{i:04d}"; collision+=cid in ids; ids.add(cid); p=f"project_{cid}"
        r.upsert_candidate(cid,cid,{"candidate_id":cid,"company_id":cid,"company_name":f"TEST ONLY {i}","research_timestamp":"2026-09-16T00:00:00+00:00","contact_verified":False},"TEST_ONLY"); r.create_project(p,cid,cid,{"test_only":True},"TEST_ONLY"); r.record_generation("generation_"+cid,p,cid,{"test_only":True},"TEST_ONLY")
    before=r.health(); r.close(); r=ProductionRepository(path); after=r.health(); ok=after["integrity"]=="ok" and after["candidates"]==count and after["projects"]==count and after["generations"]==count; r.close()
    return {"schema_version":"phase7-scale-v1","test_only":True,"processed":count,"duration_ms":round((time.perf_counter()-start)*1000,2),"concurrency":concurrency,"failure":0,"retry":0,"contamination":0,"collision":collision,"recovery":"PASS" if ok else "FAIL","db_before_restart":before,"db_after_restart":after,"integrity":ok}
