"""Validate and package the PM-OPS-1 PR event contract.

This is deliberately deterministic: network reads are represented by API URLs and
the GitHub workflow enriches them with live runs/artifacts when the event fires.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

META_RE = re.compile(r"<!--\s*pm-ops:\s*(.*?)-->", re.IGNORECASE | re.DOTALL)
FIELD_RE = re.compile(r"^\s*([a-z_]+)\s*:\s*(.*?)\s*$")
EVENT_SIGNALS = {
    "opened": "REGISTERED",
    "ready_for_review": "READY_FOR_REVIEW",
    "synchronize": "COMMIT_UPDATE",
    "converted_to_draft": "DRAFT",
    "closed": "CLOSED",
}


def metadata_from_body(body: str | None) -> dict[str, str]:
    match = META_RE.search(body or "")
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        field = FIELD_RE.match(line)
        if field:
            result[field.group(1)] = field.group(2).strip().strip('"\'')
    return result


def event_pr(event: dict[str, Any]) -> dict[str, Any]:
    return event.get("pull_request") or {}


def build_evidence(event: dict[str, Any], repository: str = "") -> dict[str, Any]:
    pr = event_pr(event)
    number = pr.get("number") or event.get("number")
    head = pr.get("head") or {}
    sha = head.get("sha") or event.get("after") or ""
    action = event.get("action", "manual")
    body = pr.get("body") or ""
    metadata = metadata_from_body(body)
    repo = repository or event.get("repository", {}).get("full_name", "")
    api_root = f"https://api.github.com/repos/{repo}" if repo else "https://api.github.com/repos/<owner>/<repo>"
    valid_fields = ["task_issue", "task_key", "parent_issue", "owner", "review_owner", "review_state"]
    missing = [field for field in valid_fields if not metadata.get(field)]
    manual_event = not pr and action == "manual"
    if manual_event:
        # A push/workflow_dispatch run validates the installed contract itself;
        # it is not a fabricated PR lifecycle signal.
        missing = []
    if not number:
        missing.append("pull_request.number")
    if not sha:
        missing.append("pull_request.head.sha")
    if action == "ready_for_review" and pr.get("draft") is True:
        missing.append("ready_for_review requires draft=false")
    signal = EVENT_SIGNALS.get(action, "MANUAL")
    evidence = {
        "event": {"name": event.get("event_name", "pull_request"), "action": action, "signal": signal},
        "task": {"issue": metadata.get("task_issue"), "key": metadata.get("task_key"), "parent_issue": metadata.get("parent_issue")},
        "pull_request": {"number": number, "title": pr.get("title"), "state": pr.get("state"), "draft": pr.get("draft"), "url": pr.get("html_url")},
        "head": {"ref": head.get("ref"), "sha": sha},
        "metadata": metadata,
        "relation_urls": {
            "task_issue": f"{api_root}/issues/{metadata.get('task_issue')}" if metadata.get("task_issue") else None,
            "pull_request": f"{api_root}/pulls/{number}" if number else None,
            "commits": f"{api_root}/pulls/{number}/commits" if number else None,
            "files": f"{api_root}/pulls/{number}/files" if number else None,
            "runs": f"{api_root}/actions/runs?head_sha={sha}" if sha else None,
            "artifacts": f"{api_root}/actions/artifacts?head_sha={sha}" if sha else None,
        },
        "required_fields": valid_fields,
        "missing": missing,
        "status": "PASS" if not missing else "FAIL",
        "fallback": "hourly condition watch remains enabled for delayed or missed PR events",
        "work_boundary": "ChatGPT Work connector/automation approval is user-owned",
    }
    return evidence


def package(evidence: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pm_ops_event_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "event_contract.json").write_text(json.dumps({"signals": EVENT_SIGNALS, "primary": "ready_for_review", "secondary": ["synchronize", "converted_to_draft", "closed"]}, indent=2) + "\n", encoding="utf-8")
    files = sorted(path.name for path in out_dir.iterdir() if path.is_file())
    manifest = {"files": files, "evidence_status": evidence["status"]}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256()
    for name in sorted(path.name for path in out_dir.iterdir() if path.is_file() and path.name != "manifest.sha256"):
        digest.update(name.encode())
        digest.update((out_dir / name).read_bytes())
    (out_dir / "manifest.sha256").write_text(digest.hexdigest() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/pm_ops_pr_event_realtime"))
    args = parser.parse_args()
    event_path = args.event or (Path(os.environ["GITHUB_EVENT_PATH"]) if os.environ.get("GITHUB_EVENT_PATH") else None)
    event = json.loads(event_path.read_text(encoding="utf-8")) if event_path else {"event_name": "manual", "action": "manual"}
    if not event.get("pull_request"):
        event.setdefault("action", "manual")
        event.setdefault("event_name", os.environ.get("GITHUB_EVENT_NAME", "manual"))
        event.setdefault("after", os.environ.get("GITHUB_SHA", ""))
    evidence = build_evidence(event, os.environ.get("GITHUB_REPOSITORY", ""))
    package(evidence, args.out)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "PASS" or evidence["event"]["name"] == "manual" else 1


if __name__ == "__main__":
    raise SystemExit(main())
