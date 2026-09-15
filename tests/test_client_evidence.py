import unittest

from lp_engine.client_evidence import (
    ClientEvidenceSlot,
    EvidenceSlotKind,
    PhotoDirection,
    SalesStateStrategy,
    evaluate_sales_to_enriched_contract,
)


def photo_direction():
    return PhotoDirection(
        purpose="Show the real owner and working environment without changing the sales-state hierarchy.",
        preferred_orientation="landscape",
        preferred_aspect_ratio="16:10",
        focal_subject="Owner working in the real environment",
        focal_relationship="Owner and work surface both visible",
        shot_distance="mid",
        copy_safe_zone="right 35%",
        light_direction="soft natural side light",
        minimum_resolution_px=1600,
        crop_tolerance="Keep face and hands inside the safe frame at 390px and 1440px.",
        avoid=["strong backlight", "fake staged stock look"],
        mobile_variant="Crop vertically while preserving face, hands and one work object.",
    )


class ClientEvidenceContractTest(unittest.TestCase):
    def test_complete_sales_state_can_be_enriched(self):
        slots = [
            ClientEvidenceSlot(
                id="hero-reality",
                kind=EvidenceSlotKind.HERO_REALITY,
                section_id="hero",
                required_for_delivery=True,
                purpose="Replace the sales-state conceptual authority with authentic owner reality.",
                sales_state_fallback="The sales state uses fact-safe typography and process form with no fake person image.",
                photo_direction=photo_direction(),
                sales_state_strategy=SalesStateStrategy.ABSTRACT_FORM,
                sales_state_complete=True,
                replacement_preserves_hierarchy=True,
            )
        ]
        result = evaluate_sales_to_enriched_contract(slots, required_section_ids=["hero"])
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["premium_ready"])

    def test_testimonial_cannot_be_simulated(self):
        slot = ClientEvidenceSlot(
            id="voice-01",
            kind=EvidenceSlotKind.TESTIMONIAL,
            section_id="proof",
            required_for_delivery=False,
            purpose="Add a verified customer voice if permission is obtained.",
            sales_state_fallback="The section is complete without testimonial content.",
            sales_state_strategy=SalesStateStrategy.ABSTRACT_FORM,
            sales_state_complete=True,
            replacement_preserves_hierarchy=True,
        )
        result = evaluate_sales_to_enriched_contract([slot])
        self.assertEqual(result["status"], "REVIEW")
        self.assertIn(
            "verified-only evidence cannot be simulated in sales state",
            result["slots"][0]["issues"],
        )

    def test_misleading_proxy_is_rejected(self):
        slot = ClientEvidenceSlot(
            id="owner-photo",
            kind=EvidenceSlotKind.OWNER_PORTRAIT,
            section_id="story",
            required_for_delivery=True,
            purpose="Show the actual owner after contract.",
            sales_state_fallback="Uses a generic person photo as if it were the owner.",
            photo_direction=photo_direction(),
            sales_state_strategy=SalesStateStrategy.LICENSED_CONTEXT,
            sales_state_complete=True,
            replacement_preserves_hierarchy=True,
            misleading_proxy=True,
        )
        result = evaluate_sales_to_enriched_contract([slot])
        self.assertEqual(result["status"], "REVIEW")

    def test_future_asset_must_not_rescue_sales_state(self):
        slot = ClientEvidenceSlot(
            id="craft-action",
            kind=EvidenceSlotKind.CRAFT_ACTION,
            section_id="craft",
            required_for_delivery=True,
            purpose="Add authentic craft action after contract.",
            sales_state_fallback="Empty visual area awaiting photography.",
            photo_direction=photo_direction(),
            sales_state_strategy=SalesStateStrategy.HIDDEN,
            sales_state_complete=False,
            replacement_preserves_hierarchy=True,
        )
        result = evaluate_sales_to_enriched_contract([slot])
        self.assertFalse(result["premium_ready"])


if __name__ == "__main__":
    unittest.main()
