"""Same-viewport screenshot comparison; metrics are evidence, not human approval."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(expected: Path, actual: Path, output: Path, *, viewport: dict, target_status: str) -> dict:
    """Reject different screenshot geometry; never silently rescale a target."""
    expected, actual, output = Path(expected), Path(actual), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(expected) as e, Image.open(actual) as a:
        e, a = e.convert('RGB'), a.convert('RGB')
        if e.size != a.size:
            result = {'status': 'GEOMETRY_MISMATCH', 'expected_size': e.size, 'actual_size': a.size}
        else:
            diff = ImageChops.difference(e, a)
            histogram = diff.histogram()
            mae = sum((i % 256) * count for i, count in enumerate(histogram)) / (e.width * e.height * 3 * 255)
            changed = sum(1 for px in diff.convert('L').tobytes() if px > 12) / (e.width * e.height)
            # Blur removes some pixel noise while retaining the broad composition.
            e_blur, a_blur = e.filter(ImageFilter.GaussianBlur(8)), a.filter(ImageFilter.GaussianBlur(8))
            broad = ImageChops.difference(e_blur, a_blur)
            broad_mae = sum((i % 256) * count for i, count in enumerate(broad.histogram())) / (e.width * e.height * 3 * 255)
            heat = ImageEnhance.Contrast(diff).enhance(3)
            heat.save(output / 'diff.png')
            side = Image.new('RGB', (e.width * 2, e.height), 'white')
            side.paste(e, (0, 0)); side.paste(a, (e.width, 0))
            side.save(output / 'side-by-side.jpg', quality=90)
            result = {'status': 'MEASURED', 'size': e.size, 'pixel_mae': round(mae, 6), 'changed_fraction_threshold_12': round(changed, 6), 'perceptual_blur_mae': round(broad_mae, 6)}
    result.update({'viewport': viewport, 'target_status': target_status,
                   'expected_sha256': sha(expected), 'actual_sha256': sha(actual),
                   'human_visible_quality': 'PENDING_SHUN_REVIEW'})
    (output / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('expected', type=Path); p.add_argument('actual', type=Path)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--width', type=int, required=True)
    p.add_argument('--height', type=int, required=True)
    p.add_argument('--target-status', default='UNAPPROVED_EXPERIMENT')
    args = p.parse_args()
    print(json.dumps(compare(args.expected, args.actual, args.out,
                             viewport={'width': args.width, 'height': args.height, 'dpr': 1},
                             target_status=args.target_status), ensure_ascii=False))


if __name__ == '__main__':
    main()
