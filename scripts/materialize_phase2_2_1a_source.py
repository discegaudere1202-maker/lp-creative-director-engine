"""Decode and verify the repository's pinned original source bundle locally."""
import argparse,base64,hashlib,io,json,tarfile
from pathlib import Path

def main(root,destination):
    root=Path(root);destination=Path(destination)
    manifest=json.loads((root/'data/creative_mechanism_phase2_2_bundle_manifest.json').read_text())
    if manifest['sha256']!='cf710cd8b25657944a5da295af91c21ab491778259390618663cbb3a7719da9f':raise ValueError('unreviewed original bundle')
    parts=[]
    for p in manifest['parts']:
        raw=(root/p['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=p['sha256']:raise ValueError('part mismatch')
        parts.append(raw)
    data=base64.b64decode(b''.join(parts),validate=True)
    if hashlib.sha256(data).hexdigest()!=manifest['sha256']:raise ValueError('bundle mismatch')
    destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
        for entry in manifest['included_files']:
            raw=tar.extractfile(entry['path']).read()
            if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('member mismatch')
            p=destination/entry['path']
            if Path(entry['path']).is_absolute() or '..' in Path(entry['path']).parts:raise ValueError('unsafe member')
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    print('Verified original source bundle: 19 files')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',default='.');p.add_argument('--destination',required=True);a=p.parse_args();main(a.repo_root,a.destination)
