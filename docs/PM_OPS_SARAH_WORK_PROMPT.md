# Sarah PM Work trigger prompt

When a GitHub pull request in `discegaudere1202-maker/lp-creative-director-engine` is marked **Ready for Review**, read the `pm-ops` metadata block in the PR body and the linked Task Issue. Retrieve the PR head SHA, changed files/diff, matching GitHub Actions runs, artifact names/IDs/digests, and the evidence/reproduction locations. Summarize the technical and QA result in the Task Issue. Keep the status `HOLD — SARAH PM REVIEW PENDING` until Sarah's human review is complete. Do not merge, force-push, alter permissions, or infer visual quality from CI alone.
