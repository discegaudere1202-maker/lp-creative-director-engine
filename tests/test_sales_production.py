import json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from lp_engine.sales_production import SalesCandidate, dedupe, validate_candidate, web_gate_decision, contact_readiness, contamination_audit, process_candidate, run_sales_stage

def c(**kw):
    base=dict(sales_candidate_id="C1",company_name="テスト事業者",business_name="テスト事業者",industry="美容",location="福岡",official_url="",instagram="https://instagram.com/test",other_sns="",phone="",email="",line="",web_status="CHECKED",web_gate="PASS_WEAK_WEB",sales_production_ready=True,source="https://instagram.com/test",research_timestamp="2026-09-15",service_scope="相談サービス",identity_status="強",active_status="確認済み",contact_route="Instagram DM",contact_verified=True)
    base.update(kw); return SalesCandidate(**base)

class SalesProductionContractTest(unittest.TestCase):
    def setUp(self):
        # These tests exercise bookkeeping and local generation, not visual QA.
        browser=patch("lp_engine.sales_production._browser",return_value={"status":"PASS"})
        self.browser=browser.start()
        self.addCleanup(browser.stop)

    def test_master_linkage_and_gate(self):
        x=c(); self.assertEqual(validate_candidate(x),[]); self.assertEqual(web_gate_decision(x),"PASS"); self.assertEqual(contact_readiness(x)["status"],"READY")
    def test_stale_or_identity_mismatch_holds(self):
        self.assertTrue(validate_candidate(c(research_timestamp=""))); self.assertTrue(validate_candidate(c(identity_status="中")))
    def test_web_gate_change_excludes(self):
        self.assertEqual(web_gate_decision(c(web_gate="EXCLUDE_SUFFICIENT_WEB")),"EXCLUDE"); self.assertEqual(web_gate_decision(c(web_gate="HOLD_STRONG_PORTAL")),"HOLD")
    def test_duplicate_protection(self): self.assertEqual(len(dedupe([c(),c()])),1)
    def test_wrong_contact_never_inferred(self):
        x=contact_readiness(c(contact_verified=False)); self.assertEqual(x["status"],"HOLD"); self.assertFalse(x["inferred"])
    def test_email_route_uses_email_instead_of_phone(self):
        result=contact_readiness(c(contact_route="email",email="hello@example.test",phone="090-0000-0000"))
        self.assertEqual(result["status"],"READY")
        self.assertEqual(result["routes"][0]["identifier"],"hello@example.test")
    def test_empty_email_never_uses_phone_as_fallback(self):
        result=contact_readiness(c(contact_route="email",email="",phone="090-0000-0000"))
        self.assertEqual(result["status"],"HOLD")
        self.assertEqual(result["routes"][0]["identifier"],"")
        self.assertFalse(result["inferred"])
    def test_package_isolation_and_engine_linkage(self):
        with tempfile.TemporaryDirectory() as td:
            m,r,rows=run_sales_stage([c(sales_candidate_id="C1",company_name="A社"),c(sales_candidate_id="C2",company_name="B社")],stage="test",root=Path(td),concurrency=1)
            self.assertEqual((m.success_count,m.hold_count,m.failed_count),(0,2,0)); self.assertEqual(len(contamination_audit(r)),0)
            self.assertTrue(all(row["quality"]["premium_gate"]=="NOT_RUN" and row["quality"]["premium_score"] is None for row in rows))
            self.assertEqual(r.items["phase6-sales-test-C1"].project_id,"project_phase6-sales-test_C1"); self.assertEqual(r.items["phase6-sales-test-C2"].project_id,"project_phase6-sales-test_C2")
    def test_external_action_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            m,r,rows=run_sales_stage([c()],stage="test",root=Path(td),concurrency=1)
            manifest=json.loads((Path(rows[0]["output_dir"])/"manifest.json").read_text())
            self.assertFalse(manifest["preview"]["public_deploy"]); self.assertEqual(manifest["external_sales_execution"],0); self.assertEqual(manifest["external_production_publish"],0)
            self.assertEqual((manifest["premium_gate"],manifest["sales_readiness"]),("NOT_RUN","SALES_HOLD"))

    def test_technical_pass_does_not_create_visual_scores_or_sales_approval(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            generation=SimpleNamespace(generation_id="generation-test",output_dir=str(out/"generation"),safety_report={"safety_status":"PASS"},stage_outputs={"creative_strategy":{"layout_profile":"recorded-profile"}})
            with patch("lp_engine.sales_production.run_generation",return_value=generation):
                result=process_candidate(c(),out)
            self.assertEqual(result["safety"]["status"],"PASS")
            self.assertEqual(result["qa"]["browser"]["status"],"PASS")
            self.assertEqual(result["quality"]["premium_gate"],"NOT_RUN")
            self.assertIsNone(result["quality"]["premium_score"])
            self.assertEqual(result["quality"]["axes"],{})
            self.assertEqual(result["quality"]["layout_profile"],"recorded-profile")
            self.assertEqual((result["state"],result["sales_status"]),("HOLD","SALES_HOLD"))
            self.assertEqual(result["sales_package"]["screenshot_paths"],[])
            readiness=json.loads((out/"sales_readiness.json").read_text())
            self.assertEqual(readiness["reasons"],["visual quality not run"])

    def test_excluded_candidate_keeps_exclusion_and_does_not_run_generation(self):
        with tempfile.TemporaryDirectory() as td, patch("lp_engine.sales_production.run_generation") as generation:
            result=process_candidate(c(web_gate="EXCLUDE_SUFFICIENT_WEB"),Path(td))
            generation.assert_not_called()
            self.browser.assert_not_called()
            self.assertEqual((result["state"],result["sales_status"]),("BLOCKED","SALES_EXCLUDED"))
            self.assertEqual(result["quality"]["premium_gate"],"NOT_RUN")
            self.assertIsNone(result["quality"]["premium_score"])

if __name__=="__main__": unittest.main()
