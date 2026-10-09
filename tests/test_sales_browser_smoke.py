"""Opt-in regression for the existing synthetic sales sample browser path.

CI enables this after installing Chromium. Local unit checks leave the variable
unset: they must not launch a browser or turn mock results into visual evidence.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest

from lp_engine.sales_production import SalesCandidate, WIDTHS, run_sales_stage


@unittest.skipUnless(os.environ.get("LP_RUN_SALES_BROWSER_SMOKE")=="1",
                     "set LP_RUN_SALES_BROWSER_SMOKE=1 with Chromium installed")
class SalesBrowserSmokeTest(unittest.TestCase):
    def test_real_browser_results_are_saved_without_visual_quality_approval(self):
        candidate=SalesCandidate(
            sales_candidate_id="C1", company_name="テスト事業者",
            business_name="テスト事業者", industry="美容", location="福岡",
            official_url="", instagram="https://instagram.com/test", other_sns="",
            phone="", email="", line="", web_status="CHECKED", web_gate="PASS_WEAK_WEB",
            sales_production_ready=True, source="https://instagram.com/test",
            research_timestamp="2026-09-15", service_scope="相談サービス",
            identity_status="強", active_status="確認済み", contact_route="Instagram DM",
            contact_verified=True,
        )
        with tempfile.TemporaryDirectory() as td:
            batch,registry,rows=run_sales_stage([candidate],stage="browser smoke",root=Path(td),concurrency=1)
            self.assertEqual((batch.failed_count,batch.success_count,batch.hold_count),(0,0,1))
            row=rows[0]
            out=Path(row["output_dir"])
            saved_qa=json.loads((out/"qa.json").read_text(encoding="utf-8"))
            browser_report=json.loads((out/"browser"/"browser_qa_report.json").read_text(encoding="utf-8"))
            package=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(row["qa"],saved_qa)
            self.assertEqual(row["qa"]["browser"]["status"],"PASS")
            self.assertEqual(saved_qa["status"],browser_report["status"])
            self.assertEqual(saved_qa["browser"]["widths"],WIDTHS)
            self.assertEqual(row["quality"]["premium_gate"],"NOT_RUN")
            self.assertIsNone(row["quality"]["premium_score"])
            self.assertEqual((package["premium_gate"],package["sales_readiness"]),("NOT_RUN","SALES_HOLD"))
            self.assertIn("browser/390_fullpage.png",package["screenshot_paths"])
            self.assertIn("browser/1440_fullpage.png",package["screenshot_paths"])
            for relative_path in package["screenshot_paths"]:
                self.assertTrue((out/relative_path).is_file(),relative_path)


if __name__=="__main__": unittest.main()
