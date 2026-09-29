"""Mine evidence-linked candidates, exact-family dedupe, and bias diagnostics."""
from __future__ import annotations
import argparse,csv,json,re
from collections import Counter,defaultdict
from difflib import SequenceMatcher
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def writej(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in x))
def heading_text(s):
 vals=[]
 for x in s.get('visible_structure',[]):
  if re.match(r'\s*h[1-3][0-9]?\s*[: ]',str(x),re.I):vals.append(str(x))
 for x in s.get('observed_facts',[]):
  m=re.match(r"\s*h[1-3][0-9]?\s+['\"](.+?)['\"]",str(x),re.I)
  if m:vals.append(m.group(1))
 return ' '.join(dict.fromkeys(vals))
PATTERNS=[
 ('METRIC_PROOF_PANEL','PROOF','Quantified proof is grouped in a single semantic scene','Anchor proof with visible quantified brand claims; not verified outcomes',re.compile(r'(\b\d+(?:[.,]\d+)?\s?%|\$\s?\d|¥\s?[\d,]+|\d[,.]?\d*\s?(?:million|billion|customers|users|years|年|件|社|名|%))',re.I)),
 ('CUSTOMER_CASE_PROOF','PROOF','Case, implementation or customer evidence is grouped as a scene','Show application context and evidence at the point of buyer evaluation',re.compile(r'(case stud|customer stor|testimonial|review|導入事例|施工事例|事例紹介|お客様の声|実績|納入実績)',re.I)),
 ('PRICING_COMPARISON','CONVERSION','Price or plan options are presented as a comparison scene','Help the buyer compare a stated price or service tier',re.compile(r'(pricing|price|plans?|料金|価格|費用|プラン|コース)',re.I)),
 ('PROCESS_SEQUENCE','LAYOUT','A named process or sequential steps are shown in one scene','Make service delivery or product setup legible as a sequence',re.compile(r'(how it works|our process|steps? to|step \d|process|flow|ご利用の流れ|施工の流れ|導入の流れ|ステップ|工程)',re.I)),
 ('QUESTION_ANSWER_CLUSTER','PROOF','Frequently asked questions or repeated buyer questions appear together','Resolve repeated objections in a scannable question-and-answer structure',re.compile(r'(frequently asked|\bFAQ\b|よくある質問|質問と回答|Q&A)',re.I)),
 ('MULTI_ITEM_SERVICE_CLUSTER','SERVICE','Multiple service or product items are grouped in one scene','Let the buyer scan service or product alternatives within one category',re.compile(r'(services?|products?|features?|service menu|商品一覧|サービス一覧|事業内容|製品一覧|機能一覧|メニュー)',re.I)),
 ('MULTI_PATH_CTA','CTA','Multiple explicit next-step actions coexist in one scene','Route different buyer readiness states to distinct next steps',re.compile(r'(contact|book|appointment|get started|request|quote|sign up|お問い合わせ|相談|予約|資料請求|見積|購入|申し込)',re.I)),
 ('PRODUCT_UI_EXPLANATION','MEDIA','A product or workflow explanation is paired with interface media','Make a digital product workflow concrete using visible interface evidence',re.compile(r'(dashboard|interface|app screen|product ui|workflow|software|platform|画面|ダッシュボード|アプリ|システム|操作)',re.I)),
 ('TRUST_DISCLOSURE_LIST','PROOF','Disclosure, trust or qualification statements form a repeated list','Make limitations and trust conditions available close to decision points',re.compile(r'(important notice|disclosure|privacy|terms|notice|重要なお知らせ|注意事項|免責|資格|認証|保証)',re.I))]

def main(scene_path,ref_path,out):
 scenes=lines(scene_path)
 with ref_path.open(newline='',encoding='utf-8') as f:refs={r['reference_id']:r for r in csv.DictReader(f)}
 evidence=defaultdict(list)
 for s in scenes:
  if s.get('observation_state')!='OBSERVED':continue
  if s.get('archive_status')!='DURABLE_VERIFIED' or not s.get('archive_locator') or not s.get('scene_crop_identifier'):continue
  text=' '.join(s.get('observed_facts',[])).lower()
  media=s.get('media_observation',[]);job=s.get('scene_job',[])
  for family,cat,purpose,marketing,rx in PATTERNS:
   heads=heading_text(s);hh=heads.lower();struct=' '.join(map(str,s.get('visible_structure',[]))).lower()
   if family=='CUSTOMER_CASE_PROOF' and not re.search(r'(case stud(?:y|ies)|customer stor(?:y|ies)|testimonial|customer review|導入事例|施工事例|お客様の声|顧客の声|事例紹介)',hh,re.I):continue
   if family=='METRIC_PROOF_PANEL' and (not re.search(r'(by the numbers|numbers|数字で見る|実績)',hh,re.I) or len(re.findall(r'(?:\d+(?:[.,]\d+)?\s?%|\d[,.]?\d*\s?(?:million|billion|customers|users|years|年|件|社|名))',text,re.I))<2):continue
   if family=='PRICING_COMPARISON' and not re.search(r'(pricing|料金プラン|料金表|価格表|費用一覧)',hh,re.I):continue
   if family=='PROCESS_SEQUENCE' and not re.search(r'(how it works|our process|steps? to|step-by-step|ご利用の流れ|施工の流れ|導入の流れ|ご利用手順|作業工程)',hh,re.I):continue
   if family=='QUESTION_ANSWER_CLUSTER' and not re.search(r'(\bfaq\b|frequently asked questions|よくある質問|q\s*&\s*a)',hh,re.I):continue
   if family=='MULTI_ITEM_SERVICE_CLUSTER' and (not re.search(r'(service menu|services|products|features|商品一覧|サービス一覧|事業内容|製品一覧|機能一覧|メニュー)',hh,re.I) or len(media)<3):continue
   if family=='MULTI_PATH_CTA':
    cta_labels=[x.strip() for x in re.findall(r'(?:a|button):([^@]+)@',struct) if re.search(r'(contact|book|appointment|request|quote|consult|sign up|get started|find|search|explore|お問い合わせ|無料相談|相談|予約|申し込|資料請求|見積|購入|探す)',x,re.I)]
    sj=s.get('scene_job') or []
    if isinstance(sj,str):sj=[sj]
    if len(set(cta_labels))<2 or 'CONVERSION_CTA' not in sj:continue
   if family=='PRODUCT_UI_EXPLANATION' and not re.search(r'(dashboard|interface|app screen|product ui|画面構成|管理画面|ダッシュボード)',hh,re.I):continue
   if family=='TRUST_DISCLOSURE_LIST' and (not re.search(r'(important notice|disclosure|privacy|terms|notice|重要なお知らせ|注意事項|免責|資格|認証|保証)',hh,re.I) or len(s.get('visible_structure',[]))<4):continue
   if not rx.search(text):continue
   evidence[family].append(s)
 candidates=[];refs_by_id=refs
 for family,src in sorted(evidence.items()):
  src=sorted({x['scene_evidence_id']:x for x in src}.values(),key=lambda x:x['scene_evidence_id'])
  rids=sorted({x['reference_id'] for x in src});brands={refs_by_id[r]['brand'] for r in rids}
  cat,purpose,marketing=next((x[1],x[2],x[3]) for x in PATTERNS if x[0]==family)
  archetypes=sorted({refs_by_id[r]['business_archetype'] for r in rids});markets=sorted({refs_by_id[r]['market_scope'] for r in rids})
  candidates.append({'mechanism_id':'CM-P22-'+family,'mechanism_name':family,'status':'CANDIDATE','candidate_confidence':'HEURISTIC_NEEDS_PIXEL_REVIEW','category':cat,'subcategory':'PHASE_2_2_OBSERVED_SCENE_STRUCTURE','purpose':purpose,'marketing_job':marketing,'user_effect':'HYPOTHESIS_NOT_PERFORMANCE_EVIDENCE','best_for':archetypes,'avoid_when':['Evidence text does not match the buyer job','Claim, asset rights or mobile behavior unresolved'],'best_scene':sorted({j for s in src for j in (s.get('scene_job') or [])}),'compatible_archetypes':archetypes,'evidence_authority':'UNKNOWN','expression_driver':'UNKNOWN','visual_impact':'NOT_RATED','conversion_utility':'NOT_RATED','automation_difficulty':'NOT_RATED','html_implementation_difficulty':'NOT_RATED','motion_dependency':'NOT_OBSERVED','responsive_risk':'REVIEW_390PX_SCENE','performance_risk':'NOT_MEASURED','accessibility_risk':'NOT_RUNTIME_TESTED','required_media':'Reference-specific assets must be independently rights-cleared','source_scene_evidence_ids':[s['scene_evidence_id'] for s in src],'evidence_count':len(src),'reference_lps':rids,'reference_count':len(rids),'unique_brand_count':len(brands),'brand_count':len(brands),'unique_agency_count':'UNKNOWN' if any(refs_by_id[r]['design_agency']=='UNKNOWN' for r in rids) else len({refs_by_id[r]['design_agency'] for r in rids}),'unique_campaign_count':'UNKNOWN' if any(refs_by_id[r]['campaign_family']=='UNKNOWN' for r in rids) else len({refs_by_id[r]['campaign_family'] for r in rids}),'market_scope':markets,'implementation_notes':'Rule mined from text/structure and linked scene crops; visually inspect every cited crop before reusing this definition.','combination_notes':'No compatibility is inferred from presence. Pairing requires independent review.','anti_pattern':'Treating a heuristic label as verified creative effect or performance improvement.','reference_scene_details':[{'scene_evidence_id':s['scene_evidence_id'],'locator':s['concrete_locator'],'archive_locator':s.get('archive_locator'),'archive_entry':s.get('archive_entry'),'original_url':s.get('original_url')} for s in src],'source_scene_scope':'OBSERVED_ONLY','promotion_allowed':False,'template_resemblance_risk':'NOT_ASSESSED'})
 # Dedupe detector-level exact family keys; keep possible variants as review edges.
 dup=[]
 for c in candidates:dup.append({'candidate_id':c['mechanism_id'],'consolidated_family_id':c['mechanism_id'],'dedupe_decision':'EXACT_RULE_FAMILY','evidence_count':c['evidence_count'],'reference_count':c['reference_count'],'brand_count':c['brand_count'],'manual_visual_review_required':True})
 variant=[]
 for i,a in enumerate(candidates):
  for b in candidates[i+1:]:
   if a['category']!=b['category']:continue
   ratio=SequenceMatcher(None,a['mechanism_name'],b['mechanism_name']).ratio()
   if ratio>=.35 or a['category']==b['category']:
    variant.append({'left':a['mechanism_id'],'right':b['mechanism_id'],'relation':'POSSIBLE_VARIANT_REVIEW','name_similarity':round(ratio,3),'auto_merge':False})
 # Pre-existing records are kept frozen and listed separately from newly mined mechanisms.
 old=lines(ROOT/'data/creative_mechanism_phase2_1_gold_mechanisms.jsonl')
 old15=lines(ROOT/'data/creative_mechanism_phase2_1_1_fullpage_mechanisms.jsonl')
 provisional=lines(ROOT/'data/creative_mechanism_phase2_1_legacy_candidate_review.jsonl')
 for m in old+old15:assert m['status']=='CANDIDATE'
 assert all(x['status']=='PROVISIONAL_FROM_PHASE2' for x in provisional)
 writej(out/'creative_mechanism_phase2_2_mechanism_candidates.jsonl',candidates)
 writej(out/'creative_mechanism_phase2_2_duplicate_map.jsonl',dup+variant)
 writej(out/'creative_mechanism_phase2_2_frozen_legacy_candidates.jsonl',old+old15+provisional)
 # Co-occurrence is deliberately not a compatibility judgment.
 co=defaultdict(set)
 for c in candidates:
  for rid in c['reference_lps']:co[rid].add(c['mechanism_id'])
 edges=[]
 for rid,keys in co.items():
  keys=sorted(keys)
  for i,k in enumerate(keys):
   for other in keys[i+1:]:edges.append({'reference_id':rid,'mechanism_a':k,'mechanism_b':other,'relation':'CO_OBSERVED_ON_SAME_REFERENCE','compatibility_state':'NOT_ASSESSED','compatible':None})
 writej(out/'creative_mechanism_phase2_2_cooccurrence_not_compatibility.jsonl',edges)
 print(json.dumps({'new_candidate_families':len(candidates),'source_scene_instances':sum(x['evidence_count'] for x in candidates),'duplicate_map_rows':len(dup)+len(variant),'frozen_legacy_count':len(old)+len(old15)+len(provisional),'cooccurrence_pairs':len(edges)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scenes',type=Path,required=True);p.add_argument('--references',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.scenes,a.references,a.out)
