import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.eligibility import ExistingSiteBaseline, AssetReality, assess_sales_eligibility


class EligibilityTest(unittest.TestCase):
    def test_no_site_is_sales_candidate(self):
        result = assess_sales_eligibility(
            ExistingSiteBaseline(has_site=False),
            AssetReality(business_asset_strength=4, accessible_asset_strength=4),
        )
        self.assertEqual(result.status, "SALES_CANDIDATE")

    def test_strong_existing_site_is_benchmark_only(self):
        baseline = ExistingSiteBaseline(
            has_site=True,
            visual_design=8,
            brand_specificity=9,
            authentic_assets=9,
            message_clarity=7,
            trust_evidence=7,
            mobile_ux=7,
            conversion_path=6,
        )
        result = assess_sales_eligibility(
            baseline,
            AssetReality(business_asset_strength=9, accessible_asset_strength=3),
        )
        self.assertEqual(result.status, "BENCHMARK_ONLY")
        self.assertEqual(result.asset_classification, "ACCESS_CONSTRAINT_NOT_ASSET_POOR")

    def test_weak_existing_site_requires_specific_gaps(self):
        baseline = ExistingSiteBaseline(
            has_site=True,
            visual_design=3,
            brand_specificity=3,
            authentic_assets=4,
            message_clarity=3,
            trust_evidence=3,
            mobile_ux=2,
            conversion_path=2,
        )
        review = assess_sales_eligibility(
            baseline,
            AssetReality(business_asset_strength=5, accessible_asset_strength=5),
            improvement_gaps=["mobile navigation is difficult"],
        )
        self.assertEqual(review.status, "REVIEW")

        eligible = assess_sales_eligibility(
            baseline,
            AssetReality(business_asset_strength=5, accessible_asset_strength=5),
            improvement_gaps=[
                "mobile navigation is difficult",
                "primary inquiry path is unclear",
            ],
        )
        self.assertEqual(eligible.status, "SALES_CANDIDATE")

    def test_strong_site_can_only_be_explicit_redesign_challenge(self):
        baseline = ExistingSiteBaseline(
            has_site=True,
            visual_design=8,
            brand_specificity=8,
            authentic_assets=8,
            message_clarity=8,
            trust_evidence=7,
            mobile_ux=7,
            conversion_path=7,
        )
        result = assess_sales_eligibility(
            baseline,
            AssetReality(business_asset_strength=8, accessible_asset_strength=8),
            explicit_redesign_challenge=True,
        )
        self.assertEqual(result.status, "REDESIGN_CHALLENGE")


if __name__ == "__main__":
    unittest.main()
