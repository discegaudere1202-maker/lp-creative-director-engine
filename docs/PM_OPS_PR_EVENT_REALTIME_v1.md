# PM-OPS-1: GitHub PR Event → Sarah Work Realtime Trigger

Status: `HOLD — SARAH PM REVIEW PENDING`

## Event contract

The GitHub-side signal is the pull-request lifecycle, not a direct push to `main`:

`Task Issue` → `task branch` → `Draft PR` → `Ready for Review` → Sarah PM catch-up

`ready_for_review` is the primary completion signal. `synchronize` (new PR commit), `converted_to_draft`, and `closed` are secondary synchronization signals. The existing hourly condition watch remains the fail-safe for delayed or missed events.

The PR body must contain this machine-readable block:

```html
<!-- pm-ops:
task_issue: 5
task_key: PM-OPS-1
parent_issue: 3
owner: rin
review_owner: sarah
review_state: draft
-->
```

`review_state` is updated with the PR lifecycle (`draft`, `ready_for_review`, `merged`, or `closed`). The contract is fail-closed: a PR event without a linked Task Issue or head SHA cannot become a Sarah signal.

## Realtime GitHub implementation

`.github/workflows/pm_ops_pr_event_realtime.yml` listens to `opened`, `ready_for_review`, `synchronize`, `converted_to_draft`, and `closed`. On the primary and secondary events it:

1. Parses and validates the linkage block.
2. Resolves PR → Task Issue → head SHA.
3. Collects changed files, matching Actions runs, and run artifacts.
4. Posts a catch-up comment to the linked Task Issue using the repository `GITHUB_TOKEN`.
5. Uploads a machine-readable evidence artifact.

The workflow also supports `workflow_dispatch` for a contract check. A scoped push trigger is retained only to publish the implementation result to Issue #5; it is not a replacement for PR events.

## Sarah PM payload

The Issue comment contains the linked Task Issue, PR number/title/status, Final HEAD, changed files, Actions run IDs and conclusions, artifact names/IDs/digests when available, QA summary, and the review location. Sarah must keep the human gate as `HOLD — SARAH PM REVIEW PENDING`; the automation never merges, force-pushes, changes permissions, or declares visual quality.

## ChatGPT Work minimum user action

One time, Shun must connect/approve the GitHub repository in ChatGPT Work with read access to PRs, Actions runs, and artifacts, then enable the Sarah PM trigger using the prompt in `docs/PM_OPS_SARAH_WORK_PROMPT.md`. Codex can implement the GitHub workflow and metadata, but cannot change ChatGPT account permissions, create a Work automation, or approve a connector on the user's behalf.

## E2E boundary

The repository test suite runs a deterministic synthetic lifecycle: `ready_for_review` → `synchronize` → `closed`, and verifies that every event resolves the Task/PR/HEAD relation and produces the expected Sarah payload. A live ChatGPT Work delivery requires the one-time user connector/automation approval above; it is intentionally not claimed as completed here.
