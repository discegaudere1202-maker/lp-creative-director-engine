"""Package original Gold images and derived traversal crops; pin every byte."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(capture: Path, crops: Path, out: Path, index: Path):
    entries = []
    for root, prefix in ((capture, "capture"), (crops, "traversal")):
        for file in sorted(root.iterdir()):
            if not file.is_file() or (prefix == "traversal" and "__contact" in file.name):
                continue
            entry = f"{prefix}/{file.name}"
            entries.append((entry, file, digest(file.read_bytes())))
    assert len([x for x in entries if x[0].startswith("capture/")]) == 159
    assert len([x for x in entries if x[0].startswith("traversal/")]) == 71
    out.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for name, file, _ in entries:
            archive.write(file, name)
    with ZipFile(out) as archive:
        assert set(archive.namelist()) == {x[0] for x in entries}
        for name, _, sha in entries:
            assert digest(archive.read(name)) == sha
    index.write_text("".join(json.dumps({"archive_entry": name, "content_hash": sha}, sort_keys=True) + "\n"
                             for name, _, sha in entries))
    print(json.dumps({"archive": str(out), "sha256": digest(out.read_bytes()), "entries": len(entries)}))

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--capture",type=Path,required=True)
    p.add_argument("--crops",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--index",type=Path,required=True)
    a=p.parse_args()
    build(a.capture,a.crops,a.out,a.index)
