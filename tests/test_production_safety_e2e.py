import json
import unittest
from pathlib import Path

from lp_engine.loader import from_dict
from lp_engine.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "P02": ("consultation", "O3_PROCESS"),
    "P09": ("quote_request", "O6_COST"),
    "P10": ("consultation", "O3_PROCESS"),
    "MORIBITO": ("visit", "O3_PROCESS"),
    "INDEPENDENT_KOKORO_SEITAI": ("reservation", "O3_PROCESS"),
}


def production_evidence(case_id, objection):
    return {
        "evidence_id": f"E2E-{case_id}",
        "company_id": case_id,
        "case_id": case_id,
        "evidence_type": "SERVICE_PROCESS",
        "evidence_strength": "E3_OPERATIONAL",
        "target_objections": [objection],
        "claim": f"公式情報で確認された{case_id}のサービス工程。",
        "source": "https://example.com/official",
        "source_type": "official_company_site",
        "verification_status": "VERIFIED",
        "verification_date": "2026-09-16",
        "usage_status": "PRODUCTION_ELIGIBLE",
        "placement_candidates": ["MIDDLE", "CTA_ZONE"],
        "rights_status": "NOT_APPLICABLE",
        "hearing_required": False,
        "blocking_status": "NON_BLOCKING",
        "notes": "Synthetic E2E fixture; not a client claim or live conversion result.",
    }


class ProductionSafetyE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "examples/mahora_v2.json").read_text(encoding="utf-8"))
        cls.args = from_dict(data)

    def test_five_cases_produce_traceable_manifests(self):
        for case_id, (goal, objection) in CASES.items():
            with self.subTest(case_id=case_id):
                report = run_pipeline(*self.args, mode="production", evidence_safety={
                    "conversion_goal": goal,
                    "primary_objections": [objection],
                    "evidence_ledger": [production_evidence(case_id, objection)],
                })
                self.assertTrue(report.production_output_allowed)
                self.assertEqual(report.safety_scope, "NONE")
                self.assertEqual(report.evidence_manifest[0]["evidence_id"], f"E2E-{case_id}")
                self.assertEqual(report.evidence_manifest[0]["source"], "https://example.com/official")

    def test_five_negative_runs_never_emit_production_manifest(self):
        bad_inputs = {
            "P02": {"requested_claims": ["秘密厳守"]},
            "P09": {"requested_claims": ["完全無料"]},
            "P10": {"requested_claims": ["必ず結果が出る"]},
            "MORIBITO": {"evidence_ledger": [production_evidence("MORIBITO", "O3_PROCESS").copy()]},
            "INDEPENDENT_KOKORO_SEITAI": {"evidence_ledger": [production_evidence("INDEPENDENT_KOKORO_SEITAI", "O3_PROCESS").copy()]},
        }
        bad_inputs["MORIBITO"]["evidence_ledger"][0]["rights_status"] = "UNKNOWN"
        bad_inputs["INDEPENDENT_KOKORO_SEITAI"]["evidence_ledger"][0]["source"] = ""
        for case_id, (goal, objection) in CASES.items():
            with self.subTest(case_id=case_id):
                default = {
                    "conversion_goal": goal,
                    "primary_objections": [objection],
                    "evidence_ledger": [production_evidence(case_id, objection)],
                }
                default.update(bad_inputs[case_id])
                report = run_pipeline(*self.args, mode="production", evidence_safety=default)
                manifest_claims = {item["claim"] for item in report.evidence_manifest}
                if case_id in {"P09", "MORIBITO", "INDEPENDENT_KOKORO_SEITAI"}:
                    self.assertFalse(report.production_output_allowed)
                    self.assertEqual(report.evidence_manifest, [])
                else:
                    self.assertTrue(report.production_output_allowed)
                    self.assertNotIn(default["requested_claims"][0], manifest_claims)
                    self.assertEqual(report.safety_scope, "CLAIM_BLOCK")

    def test_report_output_status_distinguishes_research(self):
        report = run_pipeline(*self.args, mode="research", evidence_safety={
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [production_evidence("RESEARCH", "O3_PROCESS")],
        })
        payload = report.to_dict()
        self.assertEqual(payload["output_status"], "NOT_PRODUCTION_APPROVED")
        self.assertFalse(payload["production_output_allowed"])


if __name__ == "__main__":
    unittest.main()
