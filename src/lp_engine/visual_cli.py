from __future__ import annotations
import argparse
import json
from .visual_qa import run_visual_qa_sync


def _parse_widths(value: str):
    return [int(x.strip()) for x in value.split(',') if x.strip()]


def main():
    parser = argparse.ArgumentParser(description='Generate Tier-2 visual QA artifacts.')
    parser.add_argument('source')
    parser.add_argument('--out-dir', default='qa_artifacts/visual')
    parser.add_argument('--widths', type=_parse_widths, default=[390,1440])
    parser.add_argument('--height', type=int, default=1000)
    parser.add_argument('--logo-selector', default='.brand,.logo,[data-qa-brand]')
    parser.add_argument('--max-sections', type=int, default=12)
    args = parser.parse_args()
    report = run_visual_qa_sync(
        args.source, args.out_dir, widths=args.widths, height=args.height,
        logo_selector=args.logo_selector, max_sections=args.max_sections,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    raise SystemExit(0 if report.status == 'PASS' else 2)


if __name__ == '__main__':
    main()
