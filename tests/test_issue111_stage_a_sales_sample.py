import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_issue111_stage_a_sales_sample_qa as issue111


class Issue111StageASalesSampleTest(unittest.TestCase):
    def test_sample_matrix_covers_all_stage_a_categories_with_nine_cases(self):
        matrix = issue111.sample_matrix()
        self.assertEqual(len(matrix), 9)
        counts = {}
        for row in matrix.values():
            counts[row["business_category"]] = counts.get(row["business_category"], 0) + 1
        self.assertEqual(
            counts,
            {
                "skincare_cosmetics_product": 3,
                "hair_salon": 2,
                "barber": 2,
                "pilates_studio": 2,
            },
        )
        self.assertEqual(len(issue111.WIDTHS), 9)
        self.assertEqual(len(matrix) * len(issue111.WIDTHS), 81)

    def test_fixtures_are_explicitly_synthetic_and_family_frozen(self):
        matrix = issue111.sample_matrix()
        company_ids = set()
        reference_ids = set()
        names = set()
        for row in matrix.values():
            fixture = row["fixture"]
            self.assertEqual(fixture["fixture_semantics"], "SYNTHETIC_QA_ONLY_NOT_COMPANY_EVIDENCE")
            self.assertTrue(fixture["creative_family"]["frozen"])
            company_ids.add(fixture["company_id"])
            reference_ids.add(fixture["reference_id"])
            names.add(fixture["company_truth"]["name"]["value"])
        self.assertEqual(len(company_ids), 9)
        self.assertEqual(len(reference_ids), 9)
        self.assertEqual(len(names), 9)

    def test_effective_seed_is_exact_62_floor_and_preserves_block_lists(self):
        seed = issue111.build_effective_stage_a_seed()
        assets = seed["assets"]
        ids = [row["asset_id"] for row in assets]
        self.assertEqual(len(ids), 62)
        self.assertEqual(len(set(ids)), 62)
        counts = {
            category: len({row["asset_id"] for row in assets if category in row["business_category_tags"]})
            for category in issue111.EXPECTED_FLOOR
        }
        self.assertEqual(counts, issue111.EXPECTED_FLOOR)

        sarah = issue111.issue109.ORIGINAL_LOAD_JSON(issue111.issue109.SARAH_CORRECTIONS)
        issue109_corrections = issue111.issue109.ORIGINAL_LOAD_JSON(issue111.issue109_final.CORRECTIONS)
        issue109_return = issue111.issue109.ORIGINAL_LOAD_JSON(issue111.issue109_final.SARAH_RETURN_CORRECTIONS)
        blocked = {
            row["asset_id"]
            for contract in (sarah, issue109_corrections, issue109_return)
            for row in contract["blocked_asset_ids"]
        }
        self.assertFalse(blocked.intersection(ids))

    def test_category_pairs_do_not_change_family_by_identity(self):
        matrix = issue111.sample_matrix()
        families = {}
        for row in matrix.values():
            category = row["business_category"]
            family = row["fixture"]["creative_family"]["family_id"]
            families.setdefault(category, set()).add(family)
        self.assertTrue(all(len(values) == 1 for values in families.values()))


if __name__ == "__main__":
    unittest.main()
