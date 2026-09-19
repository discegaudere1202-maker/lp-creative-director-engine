import unittest

from lp_engine.visual_relationship import validate_visual_relationship


class VisualRelationshipTest(unittest.TestCase):
    def test_valid_master_crop_passes(self):
        result = validate_visual_relationship({
            "visual_relation_type": "CROP_FROM_MASTER",
            "main_asset_id": "A01",
            "detail_asset_id": "A01",
            "master_asset_id": "A01",
            "source_crop_rect": {"x": 100, "y": 80, "width": 500, "height": 300},
            "detail_crop_rect": {"x": 100, "y": 80, "width": 500, "height": 300},
            "asset_dimensions": {"A01": (1672, 941)},
        })
        self.assertEqual(result["status"], "PASS")

    def test_crop_from_master_rejects_distinct_asset(self):
        result = validate_visual_relationship({
            "visual_relation_type": "CROP_FROM_MASTER",
            "main_asset_id": "A01", "detail_asset_id": "A03", "master_asset_id": "A01",
            "source_crop_rect": {"x": 0, "y": 0, "width": 300, "height": 200},
            "detail_crop_rect": {"x": 0, "y": 0, "width": 300, "height": 200},
            "asset_dimensions": {"A01": (1672, 941)},
        })
        self.assertEqual(result["status"], "FAIL")

    def test_crop_rectangle_must_be_inside_master(self):
        result = validate_visual_relationship({
            "visual_relation_type": "CROP_FROM_MASTER",
            "main_asset_id": "A01", "detail_asset_id": "A01", "master_asset_id": "A01",
            "source_crop_rect": {"x": 1600, "y": 0, "width": 200, "height": 200},
            "detail_crop_rect": {"x": 0, "y": 0, "width": 200, "height": 200},
            "asset_dimensions": {"A01": (1672, 941)},
        })
        self.assertEqual(result["status"], "FAIL")

    def test_secondary_context_requires_semantic_role(self):
        result = validate_visual_relationship({
            "visual_relation_type": "SECONDARY_CONTEXT",
            "main_asset_id": "A01", "detail_asset_id": "A03",
        })
        self.assertEqual(result["status"], "FAIL")

    def test_secondary_context_with_whole_to_surface_role_passes(self):
        result = validate_visual_relationship({
            "visual_relation_type": "SECONDARY_CONTEXT",
            "main_asset_id": "A01", "detail_asset_id": "A03",
            "semantic_relation": "WHOLE_HOUSE_OBSERVATION → SURFACE_CONDITION",
            "narrative_function": "surface_condition",
            "display_treatment": "editorial_second_photograph",
        })
        self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
