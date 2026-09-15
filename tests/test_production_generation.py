import json
from pathlib import Path

import pytest

from lp_engine.production_generation import run_generation


FIXTURE = Path(__file__).parents[1] / "examples/production/andy_motorcycle/andy_motorcycle_production_input_v1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_production_generation_runs_all_structured_stages(tmp_path):
    result = run_generation(load_fixture(), tmp_path / "andy", generation_id="test-gen-1")

    assert result.production_output_allowed is True
    assert result.safety_report["safety_status"] == "PASS"
    assert set(result.stage_outputs) == {
        "company_understanding",
        "creative_strategy",
        "information_architecture",
        "copy",
        "art_direction",
        "design_tokens",
        "compositions",
        "render_spec",
    }
    assert (tmp_path / "andy" / "index.html").exists()
    manifest = json.loads((tmp_path / "andy" / "generation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["manual_intervention"] == []
    assert manifest["output_status"] == "PRODUCTION_APPROVED"
    assert {item["evidence_id"] for item in manifest["evidence_used"]} == {"andy-e-001", "andy-e-002", "andy-e-003"}
    assert all(item["source"] for item in manifest["evidence_used"])
    html = (tmp_path / "andy" / "index.html").read_text(encoding="utf-8")
    assert not any(marker in html for marker in ("無理な勧誘", "秘密厳守", "完全無料", "No.1", "保証", "決めきらなくても"))


def test_research_mode_is_never_production_approved(tmp_path):
    result = run_generation(load_fixture(), tmp_path / "research", generation_id="research-1", mode="research")
    assert result.production_output_allowed is False
    assert result.manifest["output_status"] == "NOT_PRODUCTION_APPROVED"


def test_third_party_research_evidence_does_not_reach_customer_output(tmp_path):
    result = run_generation(load_fixture(), tmp_path / "andy", generation_id="test-gen-2")
    html = (tmp_path / "andy" / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "andy" / "generation_manifest.json").read_text(encoding="utf-8"))
    assert "10年" not in html
    assert "andy-e-research-001" not in html
    assert "andy-e-research-001" not in {item["evidence_id"] for item in manifest["evidence_used"]}
    assert result.safety_report["hearing_required"] == []


def test_missing_required_objection_fails_closed(tmp_path):
    raw = load_fixture()
    raw["primary_objections"] = ["O1_ABILITY"]
    with pytest.raises(RuntimeError, match="HEARING_REQUIRED"):
        run_generation(raw, tmp_path / "blocked", generation_id="blocked-1")


def test_malformed_evidence_fails_closed(tmp_path):
    raw = load_fixture()
    raw["evidence_ledger"] = [{"evidence_id": "broken"}]
    with pytest.raises(RuntimeError, match="INVALID_INPUT|HEARING_REQUIRED"):
        run_generation(raw, tmp_path / "blocked", generation_id="blocked-2")


def test_renderer_is_generic_for_another_company(tmp_path):
    raw = load_fixture()
    raw["company_id"] = "north-fork-cycles"
    raw["company"] = {
        **raw["company"],
        "company_name": "North Fork Cycles",
        "industry": "自転車修理",
        "service_category": "自転車の修理相談",
        "location": "札幌市中央区",
        "company_truth": "走行状態を聞いてから、修理の入口を考える地域の窓口。",
        "differentiators": ["状態を伝えるところから相談できる。"],
        "contact_channels": {"href": "mailto:hello@example.test", "email": "hello@example.test"},
    }
    for item in raw["evidence_ledger"]:
        item["company_id"] = raw["company_id"]
        item["case_id"] = "north-fork-cycles-production"
        item["source"] = "https://example.test/official"
    result = run_generation(raw, tmp_path / "north-fork", generation_id="generic-1")
    html = (tmp_path / "north-fork" / "index.html").read_text(encoding="utf-8")
    assert result.production_output_allowed is True
    assert "North Fork Cycles" in html
    assert "Andy motorcycle" not in html
    assert "andy.motorcycle.co@gmail.com" not in html
