# LP Creative Director Engine v0.5 — Release Notes

更新日: 2026-09-15

## Added
- Advisory Pixel Rhythm regression engine
- `lp-rhythm-regression` CLI
- Stable Section ID contract
- Regression warnings for:
  - large quiet-score shifts
  - large density shifts
  - large transition-energy shifts
  - missing baseline sections
  - unstable/generic section IDs
- CI concurrency: latest run wins per branch

## Principle
Pixel Rhythm must never become a substitute for art direction.
Regression outputs only `STABLE` or `REVIEW` and deliberately never returns creative `FAIL`.

The goal is to detect accidental loss of rhythm, not to make every LP converge on the same rhythm.
Golden Samples may and should have different breathing patterns.
