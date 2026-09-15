import unittest

from lp_engine.frame_registry import FrameRecord, audit_registry, validate_frame


def record(**kw):
    base = dict(
        frame_id="frame-001",
        site_name="Example",
        source_url="https://example.com",
        frame_role="HERO",
        visual_authority=["TYPOGRAPHY"],
        lesson="Company truth directly changes the visual form.",
        transfer_to_sales_sample="Use the causal principle, never the visual styling itself.",
        source_support="Official case study describes the design rationale.",
        visual_verified=True,
        mobile_verified=True,
        mobile_evidence_grade="M2",
        stage="CORE",
    )
    base.update(kw)
    return FrameRecord(**base)


class FrameRegistryTest(unittest.TestCase):
    def test_core_valid(self):
        self.assertEqual(validate_frame(record()), [])

    def test_candidate_not_counted_as_verified(self):
        result = audit_registry([
            record(
                stage="CANDIDATE",
                visual_verified=False,
                mobile_verified=False,
                mobile_evidence_grade="M0",
            )
        ])
        self.assertEqual(result["strict_verified_count"], 0)
        self.assertEqual(result["candidate_count"], 1)

    def test_core_requires_mobile(self):
        issues = validate_frame(record(mobile_verified=False, mobile_evidence_grade="M0"))
        self.assertIn("CORE requires mobile_verified=true", issues)
        self.assertIn("CORE requires mobile evidence grade M2 or M3", issues)

    def test_mobile_verified_requires_m2_or_m3(self):
        issues = validate_frame(record(mobile_evidence_grade="M1"))
        self.assertIn("mobile_verified=true requires mobile evidence grade M2 or M3", issues)

    def test_m3_core_count_is_separate(self):
        result = audit_registry([record(mobile_evidence_grade="M3")])
        self.assertEqual(result["core_count"], 1)
        self.assertEqual(result["core_m2_count"], 0)
        self.assertEqual(result["core_m3_count"], 1)

    def test_duplicate_reviews(self):
        result = audit_registry([record(), record()])
        self.assertEqual(result["status"], "REVIEW")
        self.assertEqual(result["duplicate_ids"], ["frame-001"])


if __name__ == "__main__":
    unittest.main()
