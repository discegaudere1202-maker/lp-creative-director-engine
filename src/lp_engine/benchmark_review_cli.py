from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_review import write_review_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an anonymous benchmark review UI from a JSON manifest.")
    parser.add_argument("manifest", help="Input JSON containing candidate and benchmark screenshots")
    parser.add_argument("--out", default="out/blind_review.html", help="Output HTML path")
    parser.add_argument("--seed", type=int, default=0, help="Randomization seed")
    args = parser.parse_args()

    payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = write_review_bundle(payload, args.out, seed=args.seed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
