import json, tempfile, unittest
from pathlib import Path
from lp_engine.sales_production import SalesCandidate, dedupe, validate_candidate, web_gate_decision, contact_readiness, contamination_audit, run_sales_stage

def c(**kw):
    base=dict(sales_candidate_id="C1",company_name="テスト事業者",business_name="テスト事業者",industry="美容",location="福岡",official_url="",instagram="https://instagram.com/test",other_sns="",phone="",email="",line="",web_status="CHECKED",web_gate="PASS_WEAK_WEB",sales_production_ready=True,source="https://instagram.com/test",research_timestamp="2026-09-15",service_scope="相談サービス",identity_status="強",active_status="確認済み",contact_route="Instagram DM",contact_verified=True)
    base.update(kw); return SalesCandidate(**base)

class SalesProductionContractTest(unittest.TestCase):
    def test_master_linkage_and_gate(self):
        x=c(); self.assertEqual(validate_candidate(x),[]); self.assertEqual(web_gate_decision(x),"PASS"); self.assertEqual(contact_readiness(x)["status"],"READY")
    def test_stale_or_identity_mismatch_holds(self):
        self.assertTrue(validate_candidate(c(research_timestamp=""))); self.assertTrue(validate_candidate(c(identity_status="中")))
    def test_web_gate_change_excludes(self):
        self.assertEqual(web_gate_decision(c(web_gate="EXCLUDE_SUFFICIENT_WEB")),"EXCLUDE"); self.assertEqual(web_gate_decision(c(web_gate="HOLD_STRONG_PORTAL")),"HOLD")
    def test_duplicate_protection(self): self.assertEqual(len(dedupe([c(),c()])),1)
    def test_wrong_contact_never_inferred(self):
        x=contact_readiness(c(contact_verified=False)); self.assertEqual(x["status"],"HOLD"); self.assertFalse(x["inferred"])
    def test_package_isolation_and_engine_linkage(self):
        with tempfile.TemporaryDirectory() as td:
            m,r,rows=run_sales_stage([c(sales_candidate_id="C1",company_name="A社"),c(sales_candidate_id="C2",company_name="B社")],stage="test",root=Path(td),concurrency=1)
            self.assertEqual(m.success_count,2); self.assertEqual(len(contamination_audit(r)),0)
            self.assertEqual(r.items["phase6-sales-test-C1"].project_id,"project_phase6-sales-test_C1"); self.assertEqual(r.items["phase6-sales-test-C2"].project_id,"project_phase6-sales-test_C2")
    def test_external_action_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            m,r,rows=run_sales_stage([c()],stage="test",root=Path(td),concurrency=1)
            manifest=json.loads((Path(rows[0]["output_dir"])/"manifest.json").read_text())
            self.assertFalse(manifest["preview"]["public_deploy"]); self.assertEqual(manifest["external_sales_execution"],0); self.assertEqual(manifest["external_production_publish"],0)

if __name__=="__main__": unittest.main()
