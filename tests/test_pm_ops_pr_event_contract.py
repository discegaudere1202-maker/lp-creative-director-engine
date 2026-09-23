import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_pm_ops_pr_event_contract.py"
spec = importlib.util.spec_from_file_location("pm_ops_contract", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


BODY = """<!-- pm-ops:
task_issue: 5
task_key: PM-OPS-1
parent_issue: 3
owner: rin
review_owner: sarah
review_state: ready_for_review
-->"""


def event(action, *, draft=False, body=BODY):
    return {
        "event_name": "pull_request",
        "action": action,
        "pull_request": {
            "number": 99,
            "title": "PM-OPS test PR",
            "body": body,
            "state": "open",
            "draft": draft,
            "html_url": "https://github.com/example/repo/pull/99",
            "head": {"ref": "codex/pm-ops-test", "sha": "a" * 40},
        },
    }


def test_ready_for_review_is_primary_signal():
    result = module.build_evidence(event("ready_for_review"), "example/repo")
    assert result["status"] == "PASS"
    assert result["event"]["signal"] == "READY_FOR_REVIEW"
    assert result["task"]["issue"] == "5"
    assert result["head"]["sha"] == "a" * 40


def test_secondary_lifecycle_signals_resolve_relation():
    for action, expected in [("synchronize", "COMMIT_UPDATE"), ("closed", "CLOSED"), ("converted_to_draft", "DRAFT")]:
        result = module.build_evidence(event(action), "example/repo")
        assert result["status"] == "PASS"
        assert result["event"]["signal"] == expected
        assert result["relation_urls"]["runs"].endswith("a" * 40)


def test_missing_linkage_is_fail_closed():
    result = module.build_evidence(event("ready_for_review", body="no metadata"), "example/repo")
    assert result["status"] == "FAIL"
    assert "task_issue" in result["missing"]


def test_draft_cannot_emit_ready_signal():
    result = module.build_evidence(event("ready_for_review", draft=True), "example/repo")
    assert result["status"] == "FAIL"
    assert "ready_for_review requires draft=false" in result["missing"]
