import tempfile,unittest
from pathlib import Path
from lp_engine.auth import Principal,authorize
from lp_engine.backup import backup_restore
from lp_engine.persistence import ProductionRepository
from lp_engine.pilot import evaluate
class Phase7BTests(unittest.TestCase):
    def test_backup_restore(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.db"; q=Path(d)/"b.db"; r=ProductionRepository(p); r.upsert_candidate("a","a",{"company_name":"A"}); r.create_project("p","a","a"); r.record_generation("g","p","a"); r.close(); x=backup_restore(p,q); self.assertTrue(x["integrity"]); self.assertEqual(x["before"],x["after"])
    def test_roles_and_isolation(self):
        self.assertFalse(authorize(None,"project.read")); self.assertTrue(authorize(Principal("s","SALES",("p",)),"project.read","p")); self.assertFalse(authorize(Principal("s","SALES",("other",)),"project.read","p")); self.assertFalse(authorize(Principal("s","SALES",("p",)),"release.approve","p"))
    def test_pilot_gate(self):
        self.assertEqual(evaluate({"candidate_id":"x","freshness":"FRESH","identity":True,"contact":True,"package":True,"safety":"PASS","rights":"PASS","qa":"PASS","screenshot":True,"opportunity":"IMPROVEMENT"})["status"],"PILOT_READY")
