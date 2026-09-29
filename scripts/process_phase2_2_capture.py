"""Turn the 95-reference Playwright run into semantic, hash-linked evidence."""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageStat

ROOT=Path(__file__).resolve().parents[1]
JOBS=('ENTRY','PROBLEM_PROPOSITION_SOLUTION','SERVICE_PRODUCT_EXPLANATION','PROOF_TRUST','CONVERSION_CTA','CLOSING_FOOTER_NAVIGATION')
TOKENS={
 'PROBLEM_PROPOSITION_SOLUTION':('problem','challenge','why','solution','introducing','designed to','built for','課題','お悩み','解決','選ばれる','選ぶ理由','私たちの想い','想い','未来へ','ご提案'),
 'SERVICE_PRODUCT_EXPLANATION':('service','product','features','how it works','platform','solution','services','製品','商品','サービス','施工','事業内容','特徴','機能','プラン','できること','メニュー','特長'),
 'PROOF_TRUST':('case','customer','testimonial','review','award','result','numbers','trusted','trust','導入事例','施工事例','実績','お客様の声','受賞','選ばれる理由','認定','保証','品質','数字で見る','導入企業'),
 'CONVERSION_CTA':('contact','get started','book','appointment','apply','sign up','request','price','pricing','quote','お問い合わせ','相談','予約','申し込','資料請求','見積','料金','購入','注文','無料'),
 'CLOSING_FOOTER_NAVIGATION':('footer','privacy','terms','sitemap','会社概要','個人情報','プライバシー','サイトマップ','利用規約','お問い合わせ')}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readj(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def writej(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def norm(s):return re.sub(r'\s+',' ',(s or '').strip().lower())
def get_items(facts,key,lo,hi):return [x for x in facts.get(key,[]) if x.get('rect',{}).get('w',0)>0 and lo<=x.get('rect',{}).get('y',-1)<hi and x.get('text')]
def classify(ref,seg,i,count,height,facts):
 vals=[]
 for x in seg['headings']+seg['actions']+seg['sections']:
  vals.append(x if isinstance(x,str) else x.get('text',''))
 text=' '.join(vals).lower()
 result=[]
 if i==0:result.append('ENTRY')
 for job,toks in TOKENS.items():
  if any(t.lower() in text for t in toks):result.append(job)
 if seg['actions'] and any(any(t.lower() in x.get('text','').lower() for t in TOKENS['CONVERSION_CTA']) for x in seg['actions']):
  if 'CONVERSION_CTA' not in result:result.append('CONVERSION_CTA')
 if facts.get('footer_present') and seg['y0']>=height*.78 and 'CLOSING_FOOTER_NAVIGATION' not in result:result.append('CLOSING_FOOTER_NAVIGATION')
 if i==count-1 and facts.get('footer_present') and 'CLOSING_FOOTER_NAVIGATION' not in result:result.append('CLOSING_FOOTER_NAVIGATION')
 return list(dict.fromkeys(result)) or ['UNCLASSIFIED']

def make_ranges(facts,height):
 heads=[h for h in facts.get('headings',[]) if h.get('tag') in ('h1','h2') and h.get('text') and h.get('rect',{}).get('w',0)>0 and 0<=h['rect'].get('y',-1)<height]
 heads.sort(key=lambda x:(x['rect']['y'],x['tag']))
 anchors=[]
 for h in heads:
  y=max(0,min(height,int(h['rect']['y'])))
  if y<420:continue
  if anchors and y-anchors[-1][0]<380:
   anchors[-1][1].append(h);continue
  anchors.append([y,[h]])
 if len(anchors)<2:
  anchors=[]
  for s in facts.get('sections',[]):
   y=max(0,min(height,int(s.get('rect',{}).get('y',-1))))
   if s.get('text') and s['rect'].get('h',0)>80 and y<height and (not anchors or y-anchors[-1][0]>=500):anchors.append([y,[]])
 starts=sorted(set([0]+[x[0] for x in anchors if x[0]>0 and x[0]<height]))
 if not starts:starts=[0]
 ends=starts[1:]+[height]
 ranges=[]
 for n,(a,b) in enumerate(zip(starts,ends)):
  if b-a<180 and ranges:ranges[-1]['y1']=b;continue
  hs=[h for h in heads if a<=h['rect']['y']<b]
  ranges.append({'index':len(ranges)+1,'y0':a,'y1':b,'headings':hs})
 return ranges or [{'index':1,'y0':0,'y1':height,'headings':heads}]

def process(capture_root:Path, targets_path:Path, output:Path, crop_dir:Path):
 manifest=json.loads((capture_root/'capture_manifest.json').read_text())
 targets=json.loads(targets_path.read_text())
 ids=targets['reference_ids'];assert len(ids)==95 and len(set(ids))==95
 records={(r['reference_id'],r['viewport_label']):r for r in manifest['records']}
 assert len(records)==190
 refs={r['reference_id']:r for r in csv.DictReader((ROOT/'data/creative_mechanism_phase2_pilot_references.csv').open(newline='',encoding='utf-8'))}
 output.mkdir(parents=True,exist_ok=True);crop_dir.mkdir(parents=True,exist_ok=True)
 scenes=[];snapshots=[];coverage=[];masters=[];claims=[];risks=[];runtime=[]
 run_id=manifest.get('run_id','UNKNOWN_RUN')
 for rid in ids:
  ref=refs[rid];view_results={}
  for vp,(width,height) in (('DESKTOP',(1440,1000)),('MOBILE',(390,844))):
   rec=records[rid,vp];view_results[vp]=rec
   facts_for_runtime=rec.get('facts',{})
   runtime.append({'runtime_observation_id':f'P22-RUNTIME-{rid}-{vp}','reference_id':rid,'viewport_label':vp,'captured_at':rec.get('captured_at'),'original_url':rec.get('original_url',ref['url']),'final_url':rec.get('final_url'),'capture_state':rec.get('capture_state'),'video_element_count':facts_for_runtime.get('video_count'),'image_element_count':len(facts_for_runtime.get('images',[])) if isinstance(facts_for_runtime.get('images'),list) else None,'reduced_motion_emulation':'ENABLED_IN_CAPTURE_CONTEXT','site_reduced_motion_response':'NOT_OBSERVED_RUNTIME_NOT_TESTED','motion_quality':'NOT_OBSERVED_STATIC_SCREENSHOTS_ONLY','scroll_jank_observed':'NOT_OBSERVED_NOT_PERFORMANCE_PROFILED','blocking_animation':'NOT_OBSERVED_NOT_RUNTIME_PROFILED','heavy_video':'NOT_DETERMINED_VIDEO_ELEMENT_COUNT_IS_NOT_BYTE_OR_DECODE_COST','keyboard_navigation':'NOT_OBSERVED','focus_visibility':'NOT_OBSERVED','contrast':'NOT_OBSERVED','alt_text_or_media_alternative':'DOM_ALT_ATTRIBUTES_CAPTURED_NOT_ACCESSIBILITY_AUDIT','heading_structure':'DOM_HEADINGS_CAPTURED_NOT_ACCESSIBILITY_AUDIT','performance_metrics':'NOT_MEASURED'} )
   if rec.get('capture_state')!='CAPTURED':
    for job in JOBS:
     scenes.append({'scene_evidence_id':f'P22-{rid}-{vp}-{job}','reference_id':rid,'viewport_label':vp,'observation_state':'NOT_OBSERVED','scene_job':[job],'missingness_reason':rec.get('error','Capture missing'),'capture_record_state':rec.get('capture_state','MISSING'),'original_url':rec.get('original_url',ref['url']),'final_url':rec.get('final_url'),'captured_at':rec.get('captured_at'),'screenshot_identifier':None,'scene_crop_identifier':None,'archive_locator':None,'archive_status':'NOT_CAPTURED','source_scene_evidence_ids':[]})
    coverage.append({'reference_id':rid,'viewport_label':vp,'capture_state':'NOT_OBSERVED','semantic_jobs':{j:{'state':'NOT_OBSERVED','scene_evidence_ids':[]} for j in JOBS}})
    continue
   fullrec=next(x for x in rec['screenshots'] if x['screenshot_identifier'].endswith('__full.jpg'))
   viewrec=next(x for x in rec['screenshots'] if x['screenshot_identifier'].endswith('__viewport.jpg'))
   full_path=capture_root/fullrec['screenshot_identifier'];view_path=capture_root/viewrec['screenshot_identifier']
   assert sha(full_path)==fullrec['content_hash'] and sha(view_path)==viewrec['content_hash']
   im=Image.open(full_path).convert('RGB');actual_h=im.height
   for sr in (fullrec,viewrec):
    snapshots.append({'snapshot_id':f'P22-SNAP-{rid}-{vp}-{Path(sr["screenshot_identifier"]).stem.split("__")[-1]}','reference_id':rid,'viewport_label':vp,'screenshot_identifier':sr['screenshot_identifier'],'content_hash':sr['content_hash'],'captured_at':sr['captured_at'],'viewport':rec['viewport'],'original_url':rec['original_url'],'final_url':rec['final_url'],'archive_status':'PENDING_ARCHIVE','archive_locator':None,'archive_entry':None,'evidence_source_role':'ORIGINAL_LIVE','capture_run_id':run_id,'source_artifact':'GitHub Actions temporary artifact; not primary archive'})
   facts=rec['facts'];ranges=make_ranges(facts,actual_h);mapped=defaultdict(list)
   for seg in ranges:
    lo,hi=seg['y0'],seg['y1'];hs=seg['headings'];head_text=' | '.join(h['text'][:180] for h in hs)
    actions=get_items(facts,'actions',lo,hi);imgs=[x for x in facts.get('images',[]) if lo<=x.get('rect',{}).get('y',-1)<hi]
    sections=get_items(facts,'sections',lo,hi)
    name=f'{rid}__{vp.lower()}__scene_{seg["index"]:03d}.jpg';cp=crop_dir/name
    im.crop((0,lo,im.width,hi)).save(cp,'JPEG',quality=83,optimize=True)
    with Image.open(cp) as crop:std=max(ImageStat.Stat(crop.convert('RGB')).stddev)
    visiblefacts=[f"{h['tag'].upper()}: {h['text'][:300]}" for h in hs]
    visiblefacts += [f"Section text: {s['text'][:800]}" for s in sections[:5]]
    visiblefacts += [f"Action: {a['text'][:200]}" for a in actions[:12]]
    visiblefacts += [f"Image alt: {x.get('alt','')}" for x in imgs[:8] if x.get('alt')]
    state='OBSERVED' if visiblefacts and std>=0.35 else 'NOT_OBSERVED'
    jobs=classify(ref,{'y0':lo,'headings':hs,'actions':actions,'sections':[x.get('text','')[:250] for x in sections]},seg['index']-1,len(ranges),actual_h,facts) if state=='OBSERVED' else []
    sid=f'P22-{rid}-{vp}-SCENE-{seg["index"]:03d}'
    row={'scene_evidence_id':sid,'reference_id':rid,'viewport_label':vp,'viewport':{'width':width,'height':actual_h},'scene_job':jobs,'observation_state':state,'concrete_locator':(head_text or f"Full-page region y={lo}:{hi}")+f"; pixel y={lo}:{hi}",'observed_facts':visiblefacts if state=='OBSERVED' else [],'visible_structure':[f"{h['tag']}:{h['text'][:200]}@y{h['rect']['y']}" for h in hs]+[f"{a['tag']}:{a['text'][:120]}@y{a['rect']['y']}" for a in actions[:20]],'typography_observation':[{'text':h['text'][:140],'font':h.get('font'),'font_size':h.get('font_size')} for h in hs[:5]],'layout_observation':{'pixel_width':width,'page_y_range':[lo,hi],'segment_height':hi-lo,'heading_count':len(hs),'action_count':len(actions),'section_count':len(sections)},'media_observation':[{'alt':x.get('alt'),'src':x.get('src'),'rect':x.get('rect')} for x in imgs[:20]],'geometry_observation':{'page_x_range':[0,width],'page_y_range':[lo,hi]},'rhythm_observation':{'ordinal':seg['index'],'segments':len(ranges),'next_boundary_y':hi},'motion_observation':'NOT_OBSERVED_STATIC_SCREENSHOT','interaction_observation':'NOT_OBSERVED_NO_INTERACTION_TEST','proof_observation':[h['text'] for h in hs if any(w in h['text'].lower() for w in TOKENS['PROOF_TRUST'])],'conversion_observation':[a['text'] for a in actions if any(w.lower() in a['text'].lower() for w in TOKENS['CONVERSION_CTA'])],'navigation_observation':{'nav_landmark_count':facts.get('nav_count'),'specific_link_membership':'NOT_OBSERVED_CAPTURE_SCRIPT_DID_NOT_TAG_NAV_ANCESTOR'},'screenshot_identifier':name,'scene_crop_identifier':name,'content_hash':sha(cp),'parent_screenshot_identifier':fullrec['screenshot_identifier'],'parent_content_hash':fullrec['content_hash'],'captured_at':rec['captured_at'],'original_url':rec['original_url'],'final_url':rec['final_url'],'archive_locator':None,'archive_status':'PENDING_ARCHIVE','archive_entry':None,'evidence_source_role':'ORIGINAL_LIVE','evidence_source_locator':rec['final_url'],'capture_run_id':run_id,'visual_pixel_stddev':round(std,3),'score_status':'NOT_SCORED'}
    scenes.append(row)
    for job in jobs:mapped[job].append(sid)
    # Claims are observations of displayed text only, never proof of truth.
    searchable=' | '.join(visiblefacts)
    if re.search(r'(\d+(?:[.,]\d+)?\s?%|\$\s?\d|¥\s?[\d,]+|before.{0,10}after|ビフォー.{0,8}アフター|改善率|No\.\s?\d|満足度)',searchable,re.I):
     claims.append({'claim_id':f'P22-CLAIM-{rid}-{vp}-{seg["index"]:03d}','reference_id':rid,'scene_evidence_id':sid,'claim_text_or_summary':searchable[:900],'claim_type':'VISIBLE_NUMERIC_OR_OUTCOME_CLAIM','source_locator':f'{rec["final_url"]} / {row["concrete_locator"]}','screenshot_identifier':name,'evidence_status':'VISIBLE_TEXT_ONLY_NOT_VERIFIED','risk_flag':'CLAIM_REVIEW_REQUIRED','claim_truth':'UNKNOWN'})
   semantic={j:{'state':'OBSERVED' if mapped[j] else 'NOT_OBSERVED','scene_evidence_ids':mapped[j], 'reason':None if mapped[j] else 'No positively classified scene in captured DOM/pixels; do not infer absence or create mechanism'} for j in JOBS}
   coverage.append({'reference_id':rid,'viewport_label':vp,'capture_state':'CAPTURED','page_height':actual_h,'scroll_traversal':rec.get('traversal'),'semantic_jobs':semantic})
  masters.append({'reference_id':rid,'slot_id':ref['slot_id'],'brand':ref['brand'],'company':ref['company'],'url':ref['url'],'canonical_url':ref['canonical_url'],'country':ref['country'],'market_scope':ref['market_scope'],'industry':ref['industry'],'business_archetype':ref['business_archetype'],'pool_type':ref['pool_type'],'conversion_goal':ref['conversion_goal'],'discovery_source_class':ref['discovery_source_class'],'discovery_source_url':ref['discovery_source_url'],'evidence_source_roles':ref['evidence_source_roles'],'design_agency':ref['design_agency'],'campaign_family':ref['campaign_family'],'desktop_capture_state':view_results['DESKTOP'].get('capture_state'),'mobile_capture_state':view_results['MOBILE'].get('capture_state'),'desktop_final_url':view_results['DESKTOP'].get('final_url'),'mobile_final_url':view_results['MOBILE'].get('final_url'),'desktop_viewport':'1440x1000','mobile_viewport':'390x844','fullpage_score_status':'NOT_SCORED','strong_hold_reject':'HOLD','original_record_status':'GOLD_BACKFILL' if rid in targets['gold15_backfill'] else 'REMAINING_80','capture_run_id':run_id})
 for name,data in [('creative_mechanism_phase2_2_fullpage_scenes.jsonl',scenes),('creative_mechanism_phase2_2_snapshots.jsonl',snapshots),('creative_mechanism_phase2_2_claims.jsonl',claims),('creative_mechanism_phase2_2_runtime_observations.jsonl',runtime)]:writej(output/name,data)
 for name,data in [('creative_mechanism_phase2_2_traversal_coverage.json',coverage),('creative_mechanism_phase2_2_references.csv',masters)]:
  if name.endswith('.json'): (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  else:
   fields=list(data[0]);
   with (output/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(data)
 print(json.dumps({'references':len(masters),'viewports':len(coverage),'scenes':len(scenes),'observed':sum(s['observation_state']=='OBSERVED' for s in scenes),'not_observed':sum(s['observation_state']=='NOT_OBSERVED' for s in scenes),'claims':len(claims)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture-root',type=Path,required=True);p.add_argument('--targets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--crops',type=Path,required=True)
 a=p.parse_args();process(a.capture_root,a.targets,a.output,a.crops)
