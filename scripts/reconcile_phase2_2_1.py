import argparse,csv,json
from pathlib import Path
from collections import Counter,defaultdict

def load_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def durable(x): return x.get('archive_status')=='DURABLE_VERIFIED' and bool(x.get('archive_locator')) and bool(x.get('archive_entry')) and x.get('archive_entry')!='manifest_subset.json' and bool(x.get('content_hash'))
def main(src,out):
 src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (src/'creative_mechanism_phase2_2_reference_master.csv').open(encoding='utf-8-sig',newline='') as f: master=list(csv.DictReader(f))
 with (src/'creative_mechanism_phase2_2_coverage_matrix.csv').open(encoding='utf-8-sig',newline='') as f: old_matrix=list(csv.DictReader(f))
 snaps=load_jsonl(src/'creative_mechanism_phase2_2_snapshots.jsonl');scenes=load_jsonl(src/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl');fail=load_jsonl(src/'creative_mechanism_phase2_2_capture_failures.jsonl');claims=load_jsonl(src/'creative_mechanism_phase2_2_claim_ledger.jsonl');cands=load_jsonl(src/'creative_mechanism_phase2_2_mechanism_candidates.jsonl');archive=load_jsonl(src/'creative_mechanism_phase2_2_archive_index.jsonl');capture_cov=json.loads((src/'creative_mechanism_phase2_2_capture_coverage.json').read_text())
 ids={x['reference_id'] for x in master};byref=defaultdict(set)
 for x in snaps:
  if not durable(x):continue
  width=(x.get('viewport') or {}).get('width');vp=x.get('viewport_label') or ('DESKTOP' if width==1440 else 'MOBILE' if width==390 else None)
  if vp in ('DESKTOP','MOBILE'):byref[x['reference_id']].add(vp)
 states=Counter(s.get('observation_state','UNKNOWN') for s in scenes)
 both={r for r in ids if {'DESKTOP','MOBILE'}<=byref[r]};desktop=sum('DESKTOP'in byref[r] for r in ids);mobile=sum('MOBILE'in byref[r] for r in ids)
 fullpage={x['reference_id'] for x in capture_cov if x.get('capture_state')=='CAPTURED'}|{'P01-R01','P05-R04','P06-R02','P08-R02','P12-R01'}
 scene_by=defaultdict(list)
 for s in scenes:scene_by[s['reference_id']].append(s)
 failure_refs={x['reference_id'] for x in fail}
 master_out=[]
 for r in master:
  rid=r['reference_id'];ss=scene_by[rid];d='DESKTOP'in byref[rid];m='MOBILE'in byref[rid];traversal=rid in fullpage and any(x.get('observation_state')=='OBSERVED' for x in ss)
  master_out.append(dict(r,desktop_durable_derived=str(d).lower(),mobile_durable_derived=str(m).lower(),both_viewports_durable_derived=str(d and m).lower(),fullpage_traversal_derived=str(traversal).lower(),scene_count_derived=len(ss),observed_scene_count_derived=sum(x.get('observation_state')=='OBSERVED' for x in ss),not_observed_scene_count_derived=sum(x.get('observation_state')=='NOT_OBSERVED' for x in ss),capture_failure_ledger_present=str(rid in failure_refs).lower(),usable_reference_derived=str(d and m and traversal and bool(ss)).lower()))
 usable=sum(x['usable_reference_derived']=='true' for x in master_out)
 agg={'attempted_reference_count':len(ids),'usable_reference_count':usable,'failed_reference_count':len(ids)-usable,'desktop_durable_count':desktop,'mobile_durable_count':mobile,'both_viewports_durable_count':len(both),'snapshot_count':len(snaps),'durable_snapshot_count':sum(durable(x) for x in snaps),'scene_count':len(scenes),'OBSERVED':states['OBSERVED'],'NOT_OBSERVED':states['NOT_OBSERVED'],'NOT_APPLICABLE':states['NOT_APPLICABLE'],'durable_scene_count':sum(x.get('observation_state')=='OBSERVED' and durable(x) for x in scenes),'claim_count':len(claims),'candidate_count':len(cands),'archive_entry_count':len(archive),'source_of_counts':'snapshots + fullpage coverage + scene ledger + claims + candidate ledger + archive index; master receives derived overlay only','phase2600_allowed':False}
 (out/'creative_mechanism_phase2_2_1_aggregate.json').write_text(json.dumps(agg,indent=2,ensure_ascii=False)+'\n')
 with (out/'creative_mechanism_phase2_2_1_reference_master_reconciled.csv').open('w',newline='',encoding='utf-8') as f:
  wr=csv.DictWriter(f,fieldnames=list(master_out[0]));wr.writeheader();wr.writerows(master_out)
 slots=defaultdict(list)
 for r in master:slots[r['slot_id']].append(r)
 old_by_slot={r['slot_id']:int(r.get('both_viewports_durable_count') or 0) for r in old_matrix};rows=[]
 for slot,refs in sorted(slots.items()):
  cellids=[r['reference_id'] for r in refs];first=refs[0];d=sum('DESKTOP'in byref[i] for i in cellids);m=sum('MOBILE'in byref[i] for i in cellids);b=sum({'DESKTOP','MOBILE'}<=byref[i] for i in cellids)
  rows.append({'slot_id':slot,'pool_type':first.get('pool_type',''),'business_archetype':first.get('business_archetype',''),'industry':first.get('industry',''),'market_scope':first.get('market_scope',''),'discovery_source_class':first.get('discovery_source_class',''),'attempted_reference_count':len(refs),'desktop_durable_count':d,'mobile_durable_count':m,'both_viewports_durable_count':b,'failed_reference_count':len(refs)-sum(master_out[next(i for i,x in enumerate(master_out) if x['reference_id']==rid)]['usable_reference_derived']=='true' for rid in cellids),'legacy_matrix_count':old_by_slot.get(slot,0),'aggregate_source':'snapshot ledger joined by reference_id'})
 with (out/'creative_mechanism_phase2_2_1_coverage_matrix.csv').open('w',newline='',encoding='utf-8') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
 # Failure subtype comes only from the stored status/error; missing response bodies remain unknown.
 byerror=defaultdict(set);attempts=Counter()
 for x in fail:
  text=((x.get('error') or '')+' '+str(x.get('http_status') or '')).lower();rid=x['reference_id'];attempts[rid]+=1;status=x.get('http_status')
  if status==403:cat='HTTP_403_ACCESS_DENIED_SUBTYPE_UNKNOWN';rec='STOP_NO_SECURITY_BYPASS; REPLACE_IF_DENIAL_PERSISTS'
  elif status==405:cat='HTTP_405_METHOD_NOT_ALLOWED_BODY_NOT_ARCHIVED';rec='STOP_AND_REPLACE; DO_NOT_PROBE_ALTERNATE_METHODS'
  elif status==429:cat='HTTP_429_RATE_LIMIT_OR_ACCESS_DENIAL_SUBTYPE_UNKNOWN';rec='ONE_DELAYED_NORMAL_RETRY_ONLY_IF_VISIBLE_RESPONSE_IS_NOT_A_CHALLENGE; OTHERWISE_STOP'
  elif status==404:cat='HTTP_404_NOT_FOUND';rec='CHECK_OFFICIAL_CANONICAL_OR_REDIRECT_ONCE_THEN_REPLACE'
  elif status==502:cat='HTTP_502_GATEWAY';rec='ONE_BOUNDED_NORMAL_RETRY_ALLOWED'
  elif 'timeout' in text:cat='TIMEOUT';rec='ONE_FRESH_CONTEXT_RETRY_WITH_BOUNDED_WAIT'
  elif 'http2_protocol_error' in text:cat='HTTP2_PROTOCOL_ERROR';rec='ONE_NORMAL_BROWSER_RETRY; NO_FINGERPRINT_OR_NETWORK_CHANGE'
  elif status==200:cat='HTTP_200_NO_VISIBLE_BODY';rec='ONE_NORMAL_WAIT_AND_SCROLL_RETRY'
  else:cat='OTHER';rec='MANUAL_REVIEW'
  byerror[rid].add((cat,rec))
 outrows=[];by_master={x['reference_id']:x for x in master}
 for rid in sorted(attempts):
  mm=by_master[rid];cat,rec=next(iter(byerror[rid]));retry=(rid=='P01-R05')
  outrows.append({'reference_id':rid,'slot_id':mm['slot_id'],'business_archetype':mm.get('business_archetype'),'industry':mm.get('industry'),'market_scope':mm.get('market_scope'),'discovery_source_class':mm.get('discovery_source_class'),'failure_class':cat,'allowed_recovery':rec,'failed_viewport_attempts':attempts[rid],'recovery_attempted_in_phase2_2_1':retry,'recovery_retry_result':'HTTP_502_REPEATED_IN_CLOUD_BROWSER; NOT_DURABLY_SNAPSHOTTED' if retry else None,'replacement_reference_id':None,'replacement_status':'NOT_STARTED'})
 (out/'creative_mechanism_phase2_2_1_failure_recovery_ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in outrows))
 for name in ('creative_mechanism_phase2_2_1_qa_report.json','creative_mechanism_phase2_2_1_pm_report_summary.json'):
  payload={'status':'BLOCKED_NOT_READY_FOR_PM_REVIEW','phase2600_allowed':False,'aggregate':agg,'gate_results':{'aggregate_reconciliation':'PASS_FOR_DERIVED_OUTPUTS_OLD_ARTIFACTS_NOT_REGENERATED','usable_100':'FAIL','same_cell_replacements':'NOT_STARTED','atomic_candidate_review':'13_PROVISIONAL_VARIANTS','compatibility_validation':'NOT_PASSED_UNKNOWN_EDGES','production_renderability':'NOT_RUN'}}
  (out/name).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
 oldsum=sum(old_by_slot.values());newsum=sum(x['both_viewports_durable_count'] for x in rows)
 if oldsum!=5 or newsum!=desktop:raise SystemExit(f'aggregate mismatch: old matrix {oldsum}; reconciled matrix {newsum}; durable count {desktop}')
 print(json.dumps({'aggregate':agg,'legacy_matrix_sum':oldsum,'corrected_matrix_sum':newsum,'matrix_cells':len(rows),'failure_root_cause_refs':len(outrows),'failed_viewport_attempts':sum(attempts.values()),'fullpage_coverage_reference_count':len(fullpage)},ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args();main(a.source_dir,a.out_dir)
