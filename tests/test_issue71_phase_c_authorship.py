import json
from lp_engine.phase_c_authorship_correction import (
    AUTHORS,
    PAIR_IDS,
    load_corrected_contracts,
    public_topology_signature,
)
from lp_engine.phase_c_expansion import WIDTHS

def test_issue71_has_eight_authored_references_and_nine_widths():
    rows = load_corrected_contracts()
    assert len(rows) == 8
    assert tuple(WIDTHS) == (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
    assert {row["expected_family"] for row in rows} == set(PAIR_IDS)

def test_same_family_pairs_have_public_structural_difference():
    rows = {row["company_id"]: row for row in load_corrected_contracts()}
    for family, (left, right) in PAIR_IDS.items():
        a, b = public_topology_signature(rows[left]), public_topology_signature(rows[right])
        assert a["family"] == b["family"] == family
        assert a["topology_signature"] != b["topology_signature"]
        assert a["hero_mode"] != b["hero_mode"]
        assert a["core_decision_mode"] != b["core_decision_mode"]
        assert a["closing_mode"] != b["closing_mode"]
        assert a["progression"] != b["progression"]
        assert a["scene_states"] != b["scene_states"]

def test_authorship_is_customer_decision_job_derived_not_lookup():
    for row in load_corrected_contracts():
        payload = json.dumps(row, ensure_ascii=False).lower()
        assert row["public_authorship"]["topology_signature"] in payload
        assert row["authorship_derivation"]["company_lookup"] is False
        assert "company lookup" not in payload
        assert "lookup" not in json.dumps(row["public_authorship"]).lower()

def test_cross_family_and_generation_safety_are_preserved():
    for row in load_corrected_contracts():
        assert row["public_authorship"]["topology_signature"]
        assert row["public_scene_semantics"][0]["source"] == "company_truth + customer_decision_job"
        assert all(item["public_customer_facing"] for item in row["public_scene_semantics"])
