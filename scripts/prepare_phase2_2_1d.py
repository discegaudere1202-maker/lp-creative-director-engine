"""Read back pinned corpus archives and build local visual review sheets."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main(archives, scratch):
    data = ROOT / 'data/phase2_2_1a_recovery'
    out = ROOT / 'data/phase2_2_1d'
    out.mkdir(exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    registry = json.loads((data / 'archive_registry.json').read_text())
    zips = {}
    checks = []
    for a in registry:
        p = archives / (a.get('file_name') or a['filename'])
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != a['container_sha256']:
            raise ValueError('ARCHIVE_HASH_MISMATCH:' + a['archive_id'])
        zips[a['archive_id']] = zipfile.ZipFile(p)
        checks.append({'archive_id': a['archive_id'], 'library_file_id': a['library_file_id'],
                       'container_sha256': actual, 'member_count': len(zips[a['archive_id']].namelist()),
                       'result': 'PASS'})
    with (data / 'reference_master.csv').open() as f:
        master = [r for r in csv.DictReader(f) if r['active_in_recovered_corpus'].lower() == 'true']
    active = {r['reference_id'] for r in master}
    snapshots = [s for s in rows(data / 'snapshots.jsonl') if s['reference_id'] in active]
    scenes = [s for s in rows(data / 'scene_evidence.jsonl') if s['reference_id'] in active]
    members = {}
    for s in snapshots + scenes:
        key = (s['archive_id'], s['archive_entry'])
        if key not in members:
            raw = zips[key[0]].read(key[1])
            if hashlib.sha256(raw).hexdigest() != s['content_hash']:
                raise ValueError('MEMBER_HASH_MISMATCH:' + str(key))
            members[key] = {'archive_id': key[0], 'archive_member': key[1],
                            'sha256': s['content_hash'], 'result': 'PASS'}
        elif members[key]['sha256'] != s['content_hash']:
            raise ValueError('CONFLICTING_MEMBER_HASH')
    views = {}
    for r in master:
        rid = r['reference_id']
        views[rid] = {}
        for label in ('DESKTOP', 'MOBILE'):
            candidates = [s for s in snapshots if s['reference_id'] == rid and s['viewport_label'] == label]
            candidates.sort(key=lambda s: ('viewport' not in s.get('screenshot_identifier', s['archive_entry']), s['archive_entry']))
            s = candidates[0]
            raw = zips[s['archive_id']].read(s['archive_entry'])
            image = Image.open(io.BytesIO(raw)).convert('RGB')
            image.crop((0, 0, image.width, min(image.height, 1050 if label == 'DESKTOP' else 1500))).save(scratch / (rid + '-' + label + '.jpg'))
            views[rid][label] = s
    for batch in range(10):
        subset = master[batch * 10:(batch + 1) * 10]
        sheet = Image.new('RGB', (1600, 1750), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        for i, r in enumerate(subset):
            x = (i % 2) * 800
            y = (i // 2) * 350
            draw.text((x + 8, y + 4), r['reference_id'] + ' ' + r['canonical_url'], fill='black')
            for label, offset, width in [('DESKTOP', 8, 548), ('MOBILE', 568, 220)]:
                img = Image.open(scratch / (r['reference_id'] + '-' + label + '.jpg'))
                img.thumbnail((width, 310))
                sheet.paste(img, (x + offset, y + 30))
        sheet.save(scratch / ('corpus-%02d.jpg' % (batch + 1)))
    report = {'source_commit': 'b3d4607277c3e13a24505e70b94bf3ec03b67362',
              'active_reference_count': len(master), 'archive_checks': checks,
              'verified_member_count': len(members), 'members': list(members.values()),
              'snapshots': len(snapshots), 'scenes': len(scenes),
              'reference_views': views, 'phase2600_allowed': False}
    (out / 'corpus_readback.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('members', 'reference_views', 'archive_checks')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--archives', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    a = p.parse_args()
    main(a.archives, a.scratch)
