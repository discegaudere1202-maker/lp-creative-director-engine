from __future__ import annotations
import argparse
import json
from .browser_qa import DEFAULT_WIDTHS, run_browser_qa_sync


def _parse_widths(value: str):
    return [int(x.strip()) for x in value.split(',') if x.strip()]


def main():
    parser = argparse.ArgumentParser(description='Run real-browser responsive QA for an LP HTML file or URL.')
    parser.add_argument('source', help='HTML file path or HTTP(S) URL')
    parser.add_argument('--out-dir', default='qa_artifacts/browser', help='QA output directory')
    parser.add_argument('--widths', type=_parse_widths, default=DEFAULT_WIDTHS,
                        help='Comma-separated viewport widths')
    parser.add_argument('--height', type=int, default=1000)
    parser.add_argument('--screenshot-widths', type=_parse_widths, default=[390,1440],
                        help='Comma-separated widths that should also get full-page screenshots')
    args = parser.parse_args()

    report = run_browser_qa_sync(args.source, args.out_dir, args.widths, args.height, screenshot_widths=args.screenshot_widths)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    raise SystemExit(0 if report.status == 'PASS' else 2)


if __name__ == '__main__':
    main()
