"""Curated candidates grounded only in visible full-page scene crops."""
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data'
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

# Each label describes visible composition, not performance or untested motion.
SEEDS=[
 ('P01-R01','PERSON_AUTHORITY','PERSON_CRAFT_NARRATIVE','Maker portrait and garden work paired with explanatory copy','Establish a named craft authority for considered local work','MEDIA','PERSON_PROOF'),
 ('P01-R01','SERVICE_PRODUCT','GARDEN_SERVICE_MOSAIC','Service categories shown as a photographic tile field','Let visitors self-identify a garden service route','LAYOUT','SERVICE_NAVIGATION'),
 ('P01-R01','CONVERSION_CONTACT','LOCAL_CONTACT_BLOCK','Phone and address presented in an explicit contact block','Make local consultation routes findable','CTA','CONTACT'),
 ('P05-R04','TRUST_NOTICE','DATED_NOTICE_LEDGER','Dated important notices set in a dense chronological list','Surface current conditions and disclosure paths','PROOF','DOCUMENT'),
 ('P05-R04','SERVICE_PRODUCT','BANK_SERVICE_CARDS','Multiple service cards separated by labeled categories','Let different bank needs branch to their own product pages','NAVIGATION','SERVICE_ROUTING'),
 ('P05-R04','CLOSING_NAVIGATION','REGULATED_FOOTER_ROUTES','Dense legal, support and service navigation at the foot','Preserve compliance and self-service paths','NAVIGATION','FOOTER'),
 ('P06-R02','PROBLEM_GUIDANCE','SYMPTOM_TO_CARE_GUIDANCE','Cold or flu concern and care-location question appear as distinct guidance scenes','Reduce uncertainty before choosing a care route','CONVERSION','DECISION_GUIDANCE'),
 ('P06-R02','CONVERSION_CARE','CARE_ROUTE_PANEL','Get Care and Need Help paths presented in adjacent panels','Separate appointment and support intent','CTA','INTENT_ROUTING'),
 ('P06-R02','HUMAN_PROOF','PATIENT_CENTERED_MESSAGE','Care-about-you statement follows practical service routing','Reassure sensitive-state visitors with a human voice','PROOF','HUMAN_AUTHORITY'),
 ('P08-R02','PRODUCT_WORKFLOW_A','WORKFLOW_BY_JOB','Intake/integration and planning workflow sections with product framing','Explain a multi-step software workflow','LAYOUT','PRODUCT_EXPLANATION'),
 ('P08-R02','CONVERSION_CTA','DUAL_SAAS_CTA','Get started and Contact sales share the closing conversion scene','Route self-serve and sales-led buyers','CTA','DECISION_SPLIT'),
 ('P12-R01','INFRASTRUCTURE_TRUST','SCALE_METRICS_PANEL','Currency, volume, uptime and subscription figures grouped as a proof panel','Anchor infrastructure credibility with sourced claims','PROOF','QUANTIFIED'),
 ('P12-R01','CASE_PROOF','BUSINESS_MODEL_EXAMPLES','Businesses of varied sizes shown with example panels','Make the platform scope concrete for multiple buyer types','PROOF','CASE_STUDY'),
 ('P12-R01','TECHNICAL_EXPLANATION','STACK_COMPATIBILITY_SCENE','Technical explanation follows case proof in a dark full-bleed scene','Answer integration-fit questions after showing use cases','LAYOUT','TECHNICAL_PROOF'),
 ('P12-R01','CLOSING_NAVIGATION','ASSISTED_ONBOARDING_FOOTER','Get-started and sales paths reappear before desktop footer navigation','Offer action and orientation at the end of a long page','CTA','CLOSING')]

def main():
 scenes=lines(D/'creative_mechanism_phase2_1_1_fullpage_scenes.jsonl')
 by_id={x['scene_evidence_id']:x for x in scenes}
 refs={x['reference_id']:x for x in csv.DictReader((D/'creative_mechanism_phase2_1_gold_references.csv').open())}
 out=[]
 for n,(ref,role,key,visual,job,category,subcat) in enumerate(SEEDS,1):
  matched={role}
  if ref=='P12-R01' and role=='CASE_PROOF':matched|={'CASE_PROOF_A','CASE_PROOF_B'}
  sources=[x['scene_evidence_id'] for x in scenes if x['reference_id']==ref and x['scene_role'] in matched and x['observation_state']=='OBSERVED']
  assert sources and (len(sources)>=2 or (ref=='P12-R01' and role=='CLOSING_NAVIGATION' and len(sources)==1))
  refset=sorted({by_id[x]['reference_id'] for x in sources})
  agencies={refs[r]['design_agency'] for r in refset}; campaigns={refs[r]['campaign_family'] for r in refset}
  out.append({
   'mechanism_id':f'CM-FULLPAGE-CAND-{n:03d}','mechanism_name':key,'status':'CANDIDATE',
   'category':category,'subcategory':subcat,'purpose':visual,'marketing_job':job,
   'user_effect':'HYPOTHESIS_NOT_OUTCOME_MEASURED','best_for':[refs[ref]['business_archetype']],
   'avoid_when':['Source fact, claim terms, asset rights or mobile visibility unavailable'],
   'best_scene':role,'compatible_archetypes':[refs[ref]['business_archetype']],
   'evidence_authority':'OBSERVED_ORIGINAL_SITE','expression_driver':'NOT_INFERRED_FROM_STYLE',
   'visual_impact':'NOT_RATED','conversion_utility':'NOT_RATED','automation_difficulty':'REVIEW_REQUIRED',
   'html_implementation_difficulty':'REVIEW_REQUIRED','motion_dependency':'NOT_OBSERVED',
   'responsive_risk':'REVIEW_390PX_CROP','performance_risk':'NOT_MEASURED','accessibility_risk':'NOT_FULLY_TESTED',
   'required_media':'Original rights-cleared assets if reused in production',
   'source_scene_evidence_ids':sources,'evidence_count':len(sources),'reference_lps':refset,
   'reference_count':len(refset),'unique_brand_count':len({refs[r]['brand'] for r in refset}),
   'unique_agency_count':'UNKNOWN' if 'UNKNOWN' in agencies else len(agencies),
   'unique_campaign_count':'UNKNOWN' if 'UNKNOWN' in campaigns else len(campaigns),
   'implementation_notes':visual+'; reconstruct the marketing job, not the source composition.',
   'combination_notes':'Combine only after authority, mobile and claim checks; static evidence does not establish motion.',
   'anti_pattern':'Copying a brand scene or treating observed visual claims as verified outcomes.',
   'confidence':'CANDIDATE_SINGLE_BRAND','source_locator':[{'archive_locator':by_id[x]['archive_locator'],'archive_entry':by_id[x]['archive_entry'],'original_url':by_id[x]['original_url']} for x in sources],
   'mobile_rule':'Inspect the linked 390px scene separately; do not infer interactive states.'})
 (D/'creative_mechanism_phase2_1_1_fullpage_mechanisms.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out))
 print({'candidates':len(out),'sources':sum(x['evidence_count'] for x in out)})
if __name__=='__main__':main()
