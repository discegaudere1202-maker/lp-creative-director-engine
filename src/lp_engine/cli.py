from __future__ import annotations
import argparse
import json
from .utils import load_json, save_json
from .loader import from_dict
from .pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Run premium LP creative-direction gates against a project spec."
    )
    parser.add_argument("spec", help="Path to a JSON project spec")
    parser.add_argument("--out", help="Optional JSON report path")
    args = parser.parse_args()

    data = load_json(args.spec)
    profile, concept, sections, motions, screenshots = from_dict(data)
    report = run_pipeline(profile, concept, sections, motions, screenshots)
    payload = report.to_dict()

    if args.out:
        save_json(args.out, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
