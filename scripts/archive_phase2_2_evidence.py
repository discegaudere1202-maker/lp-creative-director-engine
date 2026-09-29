"""Build content-addressed archive batches from captures and scene crops."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

def digest(b):return hashlib.sha256(b).hexdigest()
def build(capture:Path,crops:Path,out:Path,targets:Path,batch_size=10):
 manifest=json.loads((capture/'capture_manifest.json').read_text());ids=json.loads(targets.read_text())['reference_ids'];out.mkdir(parents=True,exist_ok=True)
 entries=[];records={(r['reference_id'],r['viewport_label']):r for r in manifest['records']}
 for r in manifest['records']:
  for shot in r.get('screenshots',[]):
   f=capture/shot['screenshot_identifier'];assert digest(f.read_bytes())==shot['content_hash']
   entries.append((r['reference_id'],'capture/'+f.name,f,shot['content_hash']))
 for f in crops.glob('*.jpg'):
  rid=f.name.split('__',1)[0];assert rid in ids
  entries.append((rid,'scene_crops/'+f.name,f,digest(f.read_bytes())))
 registry=[];index=[]
 for start in range(0,len(ids),batch_size):
  subset=ids[start:start+batch_size];batch_no=start//batch_size+1
  local=[x for x in entries if x[0] in subset]
  small={'schema_version':'phase2.2-archive-manifest-v1','capture_run_id':manifest.get('run_id'),'reference_ids':subset,'records':[r for r in manifest['records'] if r['reference_id'] in subset]}
  zip_path=out/f'phase2_2_batch_{batch_no:02d}.zip'
  with ZipFile(zip_path,'w',ZIP_DEFLATED,compresslevel=5) as z:
   z.writestr('manifest_subset.json',json.dumps(small,ensure_ascii=False,separators=(',',':')))
   for rid,member,path,h in sorted(local,key=lambda x:x[1]):z.write(path,member)
  with ZipFile(zip_path) as z:
   for rid,member,path,h in local:assert digest(z.read(member))==h
  archive_sha=digest(zip_path.read_bytes());final=out/f'phase2_2_batch_{batch_no:02d}_sha256-{archive_sha[:12]}.zip';zip_path.rename(final)
  record={'archive_batch':batch_no,'archive_id':f'P22-EVIDENCE-{batch_no:02d}','filename':final.name,'path':str(final),'container_sha256':archive_sha,'entry_count':len(local)+1,'reference_ids':subset,'capture_run_id':manifest.get('run_id'),'backend':'PENDING_LIBRARY','archive_status':'PENDING_ARCHIVE'}
  registry.append(record)
  for rid,member,path,h in local:index.append({'archive_id':record['archive_id'],'archive_batch':batch_no,'reference_id':rid,'archive_entry':member,'content_hash':h,'container_sha256':archive_sha})
 (out/'archive_registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
 (out/'creative_mechanism_phase2_2_archive_index.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in index))
 print(json.dumps({'archives':len(registry),'entries':len(index),'files':[{'name':x['filename'],'bytes':Path(x['path']).stat().st_size,'sha256':x['container_sha256']} for x in registry]}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--crops',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--targets',type=Path,required=True);a=p.parse_args();build(a.capture,a.crops,a.out,a.targets)
