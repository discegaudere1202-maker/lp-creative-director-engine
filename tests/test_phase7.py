import tempfile,unittest
from pathlib import Path
from lp_engine.api import ProductionService
from lp_engine.freshness import check
from lp_engine.persistence import ProductionRepository
from lp_engine.scale import run
from lp_engine.web_delta import analyze
class Phase7Tests(unittest.TestCase):
    def test_restart_and_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.db"; r=ProductionRepository(p); r.upsert_candidate("a","a",{"company_name":"A"}); r.create_project("pa","a","a"); r.record_generation("ga","pa","a"); r.close(); r=ProductionRepository(p); self.assertEqual(r.get_generation("ga")["company_id"],"a")
            with self.assertRaises(ValueError): r.record_generation("gb","pa","b")
    def test_api_idempotency(self):
        a=ProductionService(ProductionRepository(":memory:")); a.create_candidate({"candidate_id":"a","company_name":"A"},"c"); self.assertEqual(a.create_candidate({"candidate_id":"a","company_name":"A"},"c").status,201); self.assertEqual(a.create_project("a",key="p").body["project_id"],a.create_project("a","other",key="p").body["project_id"])
    def test_gates(self):
        self.assertFalse(check({"research_timestamp":"2026-09-16T00:00:00+00:00","contact_verified":True})["sales_send_ready"]); self.assertEqual(analyze({k:2 for k in ("clarity","company_specificity","visual_hierarchy","mobile","trust","cta","emotional_pull","conversion")},{k:4 for k in ("clarity","company_specificity","visual_hierarchy","mobile","trust","cta","emotional_pull","conversion")})["status"],"STRONG_IMPROVEMENT")
    def test_load(self):
        x=run(); self.assertTrue(x["integrity"]); self.assertEqual(x["collision"],0); self.assertEqual(x["contamination"],0)
