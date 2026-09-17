import unittest
from lp_engine.premium_experience import plan_peaks, plan_rhythm, mobile_direction


class PremiumExperienceTest(unittest.TestCase):
    def plan(self):
        return {"scene_plan": [{"scene_id": f"s{i}", "narrative_state": str(i), "visual_authority": "A", "copy_density": "low", "visual_grammar": {"topology": str(i), "media_scale": "standard", "negative_space": "perimeter", "type_scale": "editorial", "dominant_authority": "A"}} for i in range(5)]}

    def test_peak_count_and_non_hero(self):
        peaks = plan_peaks(self.plan())
        self.assertTrue(2 <= len(peaks["peaks"]) <= 4)
        self.assertTrue(any(x["peak_role"] != "hero" for x in peaks["peaks"]))

    def test_rhythm_has_variation(self):
        peaks = plan_peaks(self.plan())
        rhythm = plan_rhythm(self.plan(), peaks)
        self.assertEqual(rhythm["status"], "PASS")
        self.assertGreaterEqual(len(set(x["rhythm_state"] for x in rhythm["sequence"])), 3)

    def test_mobile_peak_is_recomposed(self):
        result = mobile_direction(self.plan()["scene_plan"][1], True)
        self.assertEqual(result["mode"], "temporal_sequence")
        self.assertEqual(result["mobile_peak_variant"], "dedicated")
        self.assertNotEqual(result["mobile_order"], "media-copy")
