"""Produce inspection aids; these sheets do not automatically classify mechanisms."""
import json
import io
from pathlib import Path
import zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ['P01-R03', 'P01-R04'], ['P06-R04', 'P06-R03-REP01'],
    ['P08-R04', 'P12-R03'], ['P13-R01-REP01', 'P13-R02-REP01'],
    ['P16-R01-REP01', 'P16-R05'], ['P18-R04', 'P09-R05'],
    ['P03-R01', 'P03-R03'], ['P05-R01', 'P05-R02-REP01'],
    ['P07-R03', 'P10-R05'], ['P11-R02', 'P11-R04'],
    ['P15-R02', 'P14-R05-REP02'], ['P17-R04', 'P17-R05'],
    ['P20-R03', 'P20-R04'],
]

def main():
    scratch = ROOT.parent / 'd-review'
    registry = json.loads((ROOT / 'data/phase2_2_1a_recovery/archive_registry.json').read_text())
    zips = {r['archive_id']: zipfile.ZipFile(ROOT.parent / 'archive-readback' / (r.get('file_name') or r['filename'])) for r in registry}
    scenes = [json.loads(l) for l in (ROOT / 'data/phase2_2_1a_recovery/scene_evidence.jsonl').read_text().splitlines()]
    ms = [json.loads(l) for l in (ROOT / 'data/creative_mechanism_phase2_2_1_atomic_calibration.jsonl').read_text().splitlines()]
    index = []
    for n, (m, pair) in enumerate(zip(ms, PAIRS)):
        source = m['source_evidence'][0]['reference_id']
        sheet = Image.new('RGB', (1800, 2200), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        draw.text((12, 5), m['mechanism_id'], fill='black')
        for col, rid in enumerate([source] + pair):
            draw.text((col * 600 + 10, 25), rid, fill='black')
            for label, ypos in [('DESKTOP', 50), ('MOBILE', 1080)]:
                ss = [s for s in scenes if s['reference_id'] == rid and s['viewport_label'] == label]
                ss.sort(key=lambda s: (s.get('page_y_range') or [s.get('scene_index', 0)])[0])
                # Show first three recorded scene regions, retaining scene identities for audit.
                for row, s in enumerate(ss[:3]):
                    raw = zips[s['archive_id']].read(s['archive_entry'])
                    im = Image.open(io.BytesIO(raw)).convert('RGB')
                    im.thumbnail((580, 320))
                    y = ypos + row * 340
                    sheet.paste(im, (col * 600 + 10, y))
                    draw.text((col * 600 + 10, y + 321), s['scene_evidence_id'], fill='black')
                index.append({'mechanism_id': m['mechanism_id'], 'reference_id': rid,
                              'viewport': label, 'visually_reviewed_scene_ids': [s['scene_evidence_id'] for s in ss[:3]]})
        sheet.save(scratch / ('candidate-%02d.jpg' % (n + 1)))
    (ROOT / 'data/phase2_2_1d/detailed_review_index.json').write_text(json.dumps(index, indent=2) + '\n')
    for z in zips.values():
        z.close()

if __name__ == '__main__':
    main()
