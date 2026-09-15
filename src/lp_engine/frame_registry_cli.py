from __future__ import annotations

import argparse
import json
from pathlib import Path

from .frame_registry import FrameRecord, audit_registry


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit screenshot-worthy frame research registry.")
    parser.add_argument("registry", help="Path to a frame registry JSON file")
    parser.add_argument("--out", help="Optional JSON audit output path")
    args = parser.parse_args()

    payload = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    records = [FrameRecord(**row) for row in payload.get("records", [])]
    result = audit_registry(records)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
