# Issue #135 — D2C Browser Evidence + Visual Diff Harness

## Scope and authority

Fixed fixture: `fixtures/d2c_melt_skin/production_input.json` and its four assets. The comparison file `reference_scene_spec_v1.html` is **an unapproved D2C-006 experiment**, not an approved 1440px Master. Its screenshot is useful for measuring drift between two HTML experiments, but cannot prove Master fidelity. Never relabel an actual screenshot as expected.

Shun visible quality remains `PENDING_SHUN_REVIEW`. The historical 867px-wide MELT SKIN Master cannot be enlarged to a nominal 1440px reference. If an approved, correct 1440px target is unavailable, `visual_diff=HOLD_NO_APPROVED_1440_MASTER` even when the experiment comparison yields metrics.

## Execute

```bash
python3 -m pip install -e .
python3 -m lp_engine.d2c.engine fixtures/d2c_melt_skin/production_input.json --out /tmp/issue135-d2c/dist
python3 -m lp_engine.d2c.browser_visual_qa \
  --dist /tmp/issue135-d2c/dist \
  --out /tmp/issue135-d2c/evidence
python3 -m unittest discover -s tests -p 'test_d2c_visual_diff.py'
```

Browser-only QA requires no reference. Supply `--reference fixtures/d2c_melt_skin/reference_scene_spec_v1.html` only for the explicitly **unapproved experiment comparison**. An absent reference is treated as no target, never as a fatal precondition. Optional `--browser-executable /path/to/approved/chromium` uses an already available system browser. Do not repeatedly download in a restricted environment.

The runner launches a loopback server, then checks separately that Chromium starts and that the actual page can load. A page-level administrator denial stops immediately rather than repeating across nine widths. On an authorized runtime, DPR1, fonts/images, every section, full-page screenshots at all nine widths (320/360/375/390/430/768/1024/1280/1440), per-scene evidence at 390×844 and 1440×900, normal/reduced-motion, keyboard FAQ and visible navigation are measured. Individual width failures are written as `FAIL` with error detail and later widths continue unless the error is an administrator restriction. Hidden CSS elements are recorded separately from visible zero-width/clipped text. The runner records browser version, executable, input/source SHA-256, console/page and HTTP errors, missing images, overflow, clipping and broken anchors. `qa_report.json` updates from actual execution only. Browser launch failure writes `HOLD` plus the exact error, never PASS.

When a reference is provided, `evidence/screenshots/{actual,expected}/<width>/full.png` and `evidence/diffs/<width>/{diff.png,side-by-side.jpg,comparison.json}` are inspectable. Browser-only output has `screenshots/actual` and `visual_diff=HOLD_NO_APPROVED_TARGET`. Per-scene actual/expected images are retained for local correction. Pixel MAE, changed fraction and blurred perceptual MAE are descriptive measures; no threshold automatically awards human fidelity PASS. Different screenshot dimensions yield `GEOMETRY_MISMATCH` instead of resizing either image.

## Correction sequence

Initial measurement → classify measured scene difference as TYPOGRAPHY/MEDIA/LAYOUT/SPACING/BOUNDARY/COLOR/MOTION → create `corrections.json` for only the affected scene → rebuild with `--corrections` → recapture the full viewport matrix → compare before/after metrics and source hashes. Preserve raw initial screenshots. Changing the generated `dist/index.html` alone is not a reproducible correction. Do not crop neighboring scenes to hide boundary errors.

## Current execution restriction (2026-10-01)

In the current Work runtime, official Playwright Chromium download returned a truncated 0 MiB archive and no browser executable is present. Sarah PM's separate environment had Chromium, but loopback page loading returned `net::ERR_BLOCKED_BY_ADMINISTRATOR`. The cloud browser rejected local file URLs under browser security policy. Do not route the local file through another URL, scheme, browser surface or service to bypass a denial. Browser presence and actual page loading are separate gates. The harness can be unit-validated here, while real-browser evidence must execute only in an authorized environment where the actual page is permitted. A blocked run is recorded as HOLD and cannot satisfy the PM stop condition by itself.
