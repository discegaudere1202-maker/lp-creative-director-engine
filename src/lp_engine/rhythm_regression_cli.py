from __future__ import annotations

import argparse
import json
from pathlib import Path

from .rhythm_regression import compare_section_rhythm


def _load_metrics(path: str, key: str | None = None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if key:
        data = data[key]
    if "section_pixel_metrics" in data:
        data = data["section_pixel_metrics"]
    return data


def main():
    p = argparse.ArgumentParser(description="Advisory regression check for section Pixel Rhythm.")
    p.add_argument("baseline")
    p.add_argument("current")
    p.add_argument("--baseline-key")
    p.add_argument("--current-key")
    p.add_argument("--out")
    args = p.parse_args()

    result = compare_section_rhythm(
        _load_metrics(args.baseline, args.baseline_key),
        _load_metrics(args.current, args.current_key),
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")

    # REVIEW is advisory and deliberately does not fail CI.
    raise SystemExit(0)


if __name__ == "__main__":
    main()
