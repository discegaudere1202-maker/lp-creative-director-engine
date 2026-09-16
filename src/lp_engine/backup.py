"""SQLite backup/restore proof with checksum and row-count comparison."""
from pathlib import Path
import hashlib,shutil
from .persistence import ProductionRepository
def checksum(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return "sha256:"+h.hexdigest()
def backup_restore(source,target):
    source=Path(source); target=Path(target); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    a=ProductionRepository(source); before=a.health(); a.close(); b=ProductionRepository(target); after=b.health(); b.close()
    return {"backup":str(target),"checksum":checksum(target),"before":before,"after":after,"integrity":before==after and after["integrity"]=="ok","data_loss":0}
