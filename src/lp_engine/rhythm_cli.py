from __future__ import annotations
import argparse
import json
from pathlib import Path
from .rhythm_compare import compare_rhythm, extract_rhythm_features


def main():
    p = argparse.ArgumentParser(description='Analyze/compare pixel-derived vertical rhythm.')
    p.add_argument('a', help='Screenshot A')
    p.add_argument('b', nargs='?', help='Optional screenshot B')
    p.add_argument('--bands', type=int, default=24)
    p.add_argument('--out')
    args = p.parse_args()

    if args.b:
        payload = compare_rhythm(args.a, args.b, bands=args.bands)
    else:
        payload = extract_rhythm_features(args.a, bands=args.bands).to_dict()

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
