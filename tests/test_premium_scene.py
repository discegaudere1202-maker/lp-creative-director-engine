import unittest
from lp_engine.premium_scene import build_premium_scene_plan, scene_plan_gates

class PremiumSceneTest(unittest.TestCase):
    def make(self, family="craft"):
        arc=[{"narrative_state":x,"user_emotion":"a","section_purpose":"ENABLE_ACTION" if i==4 else "SHOW_DETAIL","user_question":x,"evidence_required":[] if i==0 else [f"e{i}"],"preferred_composition_grammar":g,"copy_density":"low"} for i,(x,g) in enumerate(zip(("observe","read","hands","change","consult"),("immersive_image","material_detail","process_sequence","asymmetric_editorial","human_dialogue")))]
        return build_premium_scene_plan({"company_id":"synthetic","company_name":"Synthetic","location":"福岡","service_category":"service","company_truth":"truth","customer_state":{"barrier":"uncertainty"}}, {"narrative_arc":arc}, {"cta_progression":[{"stage":"discovery","visible_label":"見る","destination":"#way"},{"stage":"reassurance","visible_label":"知る","destination":"#contact"},{"stage":"action","visible_label":"始める","destination":"#contact"}]}, [{"evidence_id":"e1"}], ["role"])
    def test_schema_and_order(self):
        plan=self.make(); self.assertEqual(plan["schema_version"],"premium_scene_plan_v1"); self.assertEqual([s["narrative_index"] for s in plan["scene_plan"]], list(range(5))); self.assertTrue(all(len(s["visual_grammar"]) >= 11 for s in plan["scene_plan"])); self.assertEqual(scene_plan_gates(plan)["narrative_scene_order_gate"],"PASS")
    def test_deterministic_and_topology(self):
        a,b=self.make(),self.make(); self.assertEqual(a,b); self.assertGreaterEqual(len(set(s["visual_grammar"]["topology"] for s in a["scene_plan"])),3); self.assertEqual(scene_plan_gates(a)["scene_state_delta_gate"],"PASS")
    def test_synthetic_generalization(self):
        plan=self.make("other"); self.assertNotIn("maylynn_paint", json_text(plan))
def json_text(value):
    import json; return json.dumps(value, ensure_ascii=False)
