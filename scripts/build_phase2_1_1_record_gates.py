"""Resolve surviving Gold risks per reference instead of global blocking."""
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data'
KINDS=('DISCOVERY_TRACE','CAPTURE_TARGET','RESPONSIVE_SUBJECT','TEMPORAL_MOTION','ACCESSIBILITY_RUNTIME','CLAIM_TERMS','CROP_SELECTOR')
def build():
 refs=list(csv.DictReader((D/'creative_mechanism_phase2_1_gold_references.csv').open()))
 rows=[]
 for r in refs:
  ref=r['reference_id']
  rules={
   'DISCOVERY_TRACE':(r['discovery_source_class'] not in ('ORIGINAL_SITE_DIRECT',), 'Precise discovery listing URL missing; do not count as independently traced gallery discovery.'),
   'CAPTURE_TARGET':(ref=='P19-R01','Dior captured selector is not the intended LP; keep HOLD until target page is recaptured.'),
   'RESPONSIVE_SUBJECT':(ref in ('P04-R01','P12-R01'),'Airbnb mobile subject differs or Stripe mobile closing is blank; no transfer claim for unseen subject.'),
   'TEMPORAL_MOTION':(ref in ('P02-R01','P08-R02','P12-R01','P14-R01','P20-R01'),'Motion or rich media cannot be judged from stills; motion mechanism and quality remain NOT_OBSERVED.'),
   'ACCESSIBILITY_RUNTIME':(r['industry'] in ('MEDICAL_DENTAL_CLINIC','PUBLIC_NONPROFIT'),'Keyboard/focus/reduced-motion runtime checks incomplete; no accessibility PASS.'),
   'CLAIM_TERMS':(r['industry'] in ('FINANCE_INSURANCE','MEDICAL_DENTAL_CLINIC','BEAUTY_SALON_BODYCARE') or ref in ('P13-R04','P12-R01'),'Claim text is captured, terms and outcome safety are not verified.'),
   'CROP_SELECTOR':(False,'Viewport/full-page pixels and archive crop are authoritative; selector-only hero crop cannot establish a mechanism.')}
  for typ in KINDS:
   applicable,reason=rules[typ]
   rows.append({'reference_id':ref,'issue_type':typ,'applicability':'APPLICABLE' if applicable else 'NOT_APPLICABLE',
                'gate_result':'HOLD_AFFECTED_USE' if applicable else 'NO_GLOBAL_BLOCK',
                'reason':reason,'strong_promotion_allowed':False,'action':'Re-observe affected property before promotion' if applicable else 'Do not infer unobserved property'})
 path=D/'creative_mechanism_phase2_1_1_record_gates.jsonl'
 path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
 print({'records':len(rows),'applicable':sum(x['applicability']=='APPLICABLE' for x in rows)})
if __name__=='__main__':build()
