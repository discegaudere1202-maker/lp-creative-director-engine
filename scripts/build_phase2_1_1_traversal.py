"""Derive semantic full-page Scene crops for five Gold references from captured pixels.

Source is the successful Phase 2.1 Playwright artifact. Cropping does not invent
content or interaction: each crop is a byte-verifiable subregion of a full-page
screenshot. No new references are discovered.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TARGETS=("P01-R01","P05-R04","P06-R02","P08-R02","P12-R01")
# Inclusive start, exclusive end. Boundaries follow the named headings in the
# stored DOM and are checked against the exact screenshot heights below.
PLAN={
 "P01-R01":{
  "DESKTOP":[("ENTRY",0,780),("TOPICS_TRUST",780,1420),("SERVICE_PRODUCT",1420,2260),("PROOF_NEWS",2260,2900),("PERSON_AUTHORITY",2900,4200),("CONVERSION_CONTACT",4200,5250),("CLOSING_NAVIGATION",5250,5922)],
  "MOBILE":[("ENTRY",0,950),("TOPICS_TRUST",950,2480),("SERVICE_PRODUCT",2480,4440),("PROOF_NEWS",4440,5200),("PERSON_AUTHORITY",5200,6890),("CONVERSION_CONTACT",6890,8650),("CLOSING_NAVIGATION",8650,9703)]},
 "P05-R04":{
  "DESKTOP":[("ENTRY",0,1200),("PRODUCT_OFFER",1200,2120),("SERVICE_PRODUCT",2120,3500),("TRUST_NOTICE",3500,4760),("NEWS",4760,6230),("SUPPORT_PROOF",6230,7100),("CLOSING_NAVIGATION",7100,8126)],
  "MOBILE":[("ENTRY",0,1050),("PRODUCT_OFFER",1050,2450),("SERVICE_PRODUCT",2450,5820),("TRUST_NOTICE",5820,7470),("NEWS",7470,9120),("SUPPORT_PROOF",9120,11150),("CLOSING_NAVIGATION",11150,13276)]},
 "P06-R02":{
  "DESKTOP":[("ENTRY",0,1100),("SERVICE_PATHS",1100,2050),("PROBLEM_GUIDANCE",2050,3450),("CONVERSION_CARE",3450,4300),("HUMAN_PROOF",4300,5700),("TRUST_INFORMATION",5700,6900),("CLOSING_NAVIGATION",6900,8025)],
  "MOBILE":[("ENTRY",0,800),("SERVICE_PATHS",800,2100),("PROBLEM_GUIDANCE",2100,3420),("CONVERSION_CARE",3420,4990),("HUMAN_PROOF",4990,5800),("TRUST_INFORMATION",5800,6700),("CLOSING_NAVIGATION",6700,8345)]},
 "P08-R02":{
  "DESKTOP":[("ENTRY_PRODUCT_UI",0,1590),("PROPOSITION",1590,2670),("PRODUCT_WORKFLOW_A",2670,5140),("PRODUCT_WORKFLOW_B",5140,7640),("UPDATE_TRUST",7640,9000),("CONVERSION_CTA",9000,9520),("CLOSING_NAVIGATION",9520,9960)],
  "MOBILE":[("ENTRY_PRODUCT_UI",0,1070),("PROPOSITION",1070,2250),("PRODUCT_WORKFLOW_A",2250,3410),("PRODUCT_WORKFLOW_B",3410,4730),("CONVERSION_CTA",4730,5050),("CLOSING_NAVIGATION",5050,5876)]},
 "P12-R01":{
  "DESKTOP":[("ENTRY_CLIENT_PROOF",0,920),("SOLUTION_PRODUCT",920,3120),("GUIDED_DECISION",3120,4100),("INFRASTRUCTURE_TRUST",4100,5090),("CASE_PROOF",5090,9700),("TECHNICAL_EXPLANATION",9700,12040),("NEWS_PROOF",12040,13500),("CLOSING_NAVIGATION",13500,15199)],
 "MOBILE":[("ENTRY_CLIENT_PROOF",0,605),("SOLUTION_PRODUCT",605,4800),("INFRASTRUCTURE_TRUST",4800,5600),("CASE_PROOF_A",5600,8720),("CASE_PROOF_B",8720,11940),("TECHNICAL_EXPLANATION",11940,15040),("NEWS_PROOF",15040,18100),("CLOSING_NAVIGATION",18100,20533)]}}

# Semantic roles are expectations, not fabricated page sections. Explicit
# absence and capture gaps remain distinguishable in the coverage ledger.
ROLE_COVERAGE={
 "P01-R01":{"ENTRY":["ENTRY"],"PROPOSITION_SOLUTION":["TOPICS_TRUST"],"SERVICE_PRODUCT":["SERVICE_PRODUCT"],"PROOF_TRUST":["PROOF_NEWS","PERSON_AUTHORITY"],"CONVERSION_CTA":["CONVERSION_CONTACT"],"CLOSING_NAVIGATION":["CLOSING_NAVIGATION"]},
 "P05-R04":{"ENTRY":["ENTRY"],"PROPOSITION_SOLUTION":["PRODUCT_OFFER"],"SERVICE_PRODUCT":["SERVICE_PRODUCT"],"PROOF_TRUST":["TRUST_NOTICE","SUPPORT_PROOF"],"CONVERSION_CTA":["PRODUCT_OFFER"],"CLOSING_NAVIGATION":["CLOSING_NAVIGATION"]},
 "P06-R02":{"ENTRY":["ENTRY"],"PROPOSITION_SOLUTION":["PROBLEM_GUIDANCE"],"SERVICE_PRODUCT":["SERVICE_PATHS"],"PROOF_TRUST":["HUMAN_PROOF","TRUST_INFORMATION"],"CONVERSION_CTA":["CONVERSION_CARE"],"CLOSING_NAVIGATION":["CLOSING_NAVIGATION"]},
 "P08-R02":{"ENTRY":["ENTRY_PRODUCT_UI"],"PROPOSITION_SOLUTION":["PROPOSITION"],"SERVICE_PRODUCT":["PRODUCT_WORKFLOW_A","PRODUCT_WORKFLOW_B"],"PROOF_TRUST":["UPDATE_TRUST"],"CONVERSION_CTA":["CONVERSION_CTA"],"CLOSING_NAVIGATION":["CLOSING_NAVIGATION"]},
 "P12-R01":{"ENTRY":["ENTRY_CLIENT_PROOF"],"PROPOSITION_SOLUTION":["SOLUTION_PRODUCT"],"SERVICE_PRODUCT":["SOLUTION_PRODUCT","TECHNICAL_EXPLANATION"],"PROOF_TRUST":["INFRASTRUCTURE_TRUST","CASE_PROOF_A","CASE_PROOF_B","CASE_PROOF"],"CONVERSION_CTA":["GUIDED_DECISION","CLOSING_NAVIGATION"],"CLOSING_NAVIGATION":["CLOSING_NAVIGATION"]}}

# Direct visual review of crops where the DOM manifest omitted footer text.
PIXEL_FACTS={
 ("P01-R01","DESKTOP","CLOSING_NAVIGATION"):['Dark footer shows photographic garden/service tiles in a grid and a lower row of service/company links.'],
 ("P01-R01","MOBILE","CLOSING_NAVIGATION"):['Dark footer stacks office greenery, landscape, bonsai and Chelsea Flower Show tiles above service, contact and company links.'],
 ("P05-R04","DESKTOP","CLOSING_NAVIGATION"):['Bank footer shows award badges, dense site links and a dark legal/copyright band.'],
 ("P05-R04","MOBILE","CLOSING_NAVIGATION"):['Satisfaction award badges precede a two-column legal/navigation grid and a dark bank disclosure band.'],
 ("P12-R01","DESKTOP","CLOSING_NAVIGATION"):['Ready-to-get-started panel offers account and sales paths above multi-column product and company footer links.']}
PIXEL_DETAILS={
 ("P01-R01","DESKTOP"):('Small white Japanese link text on charcoal','Photographic service cards in a multi-column dark grid','Garden/service thumbnail photographs',[],['Service and company links']),
 ("P01-R01","MOBILE"):('White Japanese service headings and smaller descriptions','Service tiles stacked one per row before link groups','Garden, office greenery and bonsai thumbnail photographs', ['お問い合わせ'],['Service, contact, company and social links']),
 ("P05-R04","DESKTOP"):('Small dark and teal utility text','Awards above compact site-links and dark legal band','Award badge imagery',['Support information'],['Corporate and disclosure navigation']),
 ("P05-R04","MOBILE"):('Centered award captions followed by compact link labels','Single-column award stack, then two-column legal grid','Satisfaction and support award badges',[],['Risk products, privacy policy and site map']),
 ("P12-R01","DESKTOP"):('Large ready-to-get-started heading and small footer labels','CTA block above product/company footer columns','No dominant image in closing crop',['Account start','Contact sales'],['Product and company footer categories'])}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def inside(items, start, end):
 return [x for x in items if x.get("rect",{}).get("w",0)>0 and start <= x["rect"].get("y",-1) < end]

def build(capture, output):
 manifest=json.loads((capture/"capture_manifest.json").read_text())
 records={(r["reference_id"],r["viewport_label"]):r for r in manifest["records"]}
 output.mkdir(parents=True,exist_ok=True)
 rows=[]; coverage=[]
 derived_at=datetime.now(timezone.utc).isoformat()
 for ref in TARGETS:
  for vp in ("DESKTOP","MOBILE"):
   record=records[ref,vp]; pieces=PLAN[ref][vp]
   full=record["screenshots"][1]; img_path=capture/full["screenshot_identifier"]
   assert sha(img_path)==full["content_hash"]
   im=Image.open(img_path)
   assert im.width==record["viewport"]["width"] and im.height==pieces[-1][2]
   assert pieces[0][1]==0 and all(a[2]==b[1] for a,b in zip(pieces,pieces[1:]))
   for i,(role,start,end) in enumerate(pieces,1):
    name=f"{ref}__{vp.lower()}__traversal_{i:02d}_{role.lower()}.jpg"
    crop_path=output/name
    im.crop((0,start,im.width,end)).convert("RGB").save(crop_path,quality=88,optimize=True)
    facts=record["facts"]
    h=inside(facts.get("headings",[]),start,end)
    a=inside(facts.get("actions",[]),start,end)
    media=inside(facts.get("images",[]),start,end)
    # For image-only entry/closing sections, the screenshot region itself is a
    # concrete locator. A reviewer must inspect the crop before mining.
    label=(h[0]["text"][:100] if h else a[0]["text"][:100] if a else role)
    scene_id=f"GOLD-{ref}-{vp}-TRAV-{i:02d}"
    observed=[f"{x['tag']} '{x['text'][:110]}' at y={round(x['rect']['y'])}" for x in h[:5]]
    observed += [f"action '{x['text'][:110]}' at y={round(x['rect']['y'])}" for x in a[:5]]
    # Stripe's mobile tail was a blank lazy-rendered area in the captured
    # pixels; a DOM omission must not be presented as a visible footer.
    blank_tail=(ref=="P12-R01" and vp=="MOBILE" and role=="CLOSING_NAVIGATION")
    if not observed and not blank_tail:observed=PIXEL_FACTS[(ref,vp,role)]
    structure=[f"{x['tag']} {x['text'][:100]} @({round(x['rect']['x'])},{round(x['rect']['y'])})" for x in h[:5]]
    structure += [f"link {x['text'][:100]} @({round(x['rect']['x'])},{round(x['rect']['y'])})" for x in a[:5]]
    if not structure and not blank_tail:structure=[f"Archived {name}: {observed[0]}"]
    rows.append({
      "scene_evidence_id":scene_id,"reference_id":ref,"scene_role":role,"observation_state":"NOT_OBSERVED" if blank_tail else "OBSERVED",
      "viewport_label":vp,"viewport":{"width":im.width,"height":end-start},"page_y_range":[start,end],
      "screenshot_identifier":name,"scene_crop_identifier":name,"content_hash":sha(crop_path),
      "parent_screenshot_identifier":full["screenshot_identifier"],"parent_content_hash":full["content_hash"],
      "captured_at":record["captured_at"],"derived_at":derived_at,
      "original_url":record["original_url"],"final_url":record["final_url"],
      "archive_locator":"ARCHIVE_PENDING","archive_status":"TEMPORARY_CAPTURE",
      "concrete_locator":f"{label} / full-page y={start}:{end}",
      "observed_facts":observed,"visible_structure":[] if blank_tail else structure,
      "typography_observation":[f"{x['tag']} {x['font']} {x['font_size']}: {x['text'][:100]}" for x in h[:3]],
      "layout_observation":f"{im.width}px page region y={start}:{end}; {len(h)} headings, {len(a)} actions",
      "media_observation":[{"alt":x.get("alt"),"src":x.get("src"),"box":x.get("rect")} for x in media[:4]],
      "geometry_observation":f"x=0..{im.width}, y={start}..{end}",
      "rhythm_observation":f"Scene {i}/{len(pieces)}; next boundary at page y={end}",
      "motion_observation":"NOT_OBSERVED_STATIC_PIXEL_CAPTURE",
      "interaction_observation":"NOT_OBSERVED_NO_CLICK_OR_KEYBOARD_TEST",
      "proof_observation":[x["text"][:120] for x in h if any(z in x["text"].lower() for z in ("award","受賞","case","hertz","clinic","trust","評価"))][:4],
      "conversion_observation":[x["text"][:120] for x in a[:4]],
      "navigation_observation":[x["text"][:120] for x in a[:4]],
      "evidence_source_role":"ORIGINAL_LIVE","evidence_source_locator":record["final_url"]+f"#pixel-y-{start}-{end}",
      "score_scope":"FULL_PAGE_STATIC_OBSERVATION_ONLY",
      "missingness_reason":"Blank tail in captured mobile image; footer cannot be verified" if blank_tail else None,
      "media_runtime_status":"PARTIAL_STATIC_CAPTURE_NO_SCROLL_TRIGGER" if ref in ("P08-R02","P12-R01") else "STATIC_CAPTURE_ONLY"})
    if (ref,vp,role) in PIXEL_FACTS:
     typ,layout,med,cta,nav=PIXEL_DETAILS[(ref,vp)]
     rows[-1]['typography_observation']=[typ]
     rows[-1]['layout_observation']=layout+f'; pixel y={start}:{end}'
     rows[-1]['media_observation']=[{'visual_observation':med,'runtime_status':'STATIC_PIXELS_ONLY'}]
     rows[-1]['conversion_observation']=cta
     rows[-1]['navigation_observation']=nav
   roles={x[0] for x in pieces}
   categories={}
   for job,member_roles in ROLE_COVERAGE[ref].items():
    available=[r for r in member_roles if r in roles]
    if not available: state="NOT_APPLICABLE"
    elif ref=="P12-R01" and vp=="MOBILE" and job=="CLOSING_NAVIGATION": state="NOT_OBSERVED"
    else: state="OBSERVED"
    categories[job]={"state":state,"scene_roles":available,
                     "reason":"Captured blank mobile tail" if state=="NOT_OBSERVED" else "No such semantic scene in captured page" if state=="NOT_APPLICABLE" else None}
   coverage.append({"reference_id":ref,"viewport_label":vp,"scene_roles":sorted(roles),"semantic_coverage":categories,
                    "scene_count":len(pieces),"observed_count":len(pieces)-(ref=="P12-R01" and vp=="MOBILE"),
                    "page_coverage":[0,im.height],"motion":"NOT_OBSERVED","interaction":"NOT_OBSERVED"})
 data=ROOT/"data"
 with (data/"creative_mechanism_phase2_1_1_fullpage_scenes.jsonl").open("w") as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n")
 (data/"creative_mechanism_phase2_1_1_traversal_coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"references":len(TARGETS),"viewports":len(coverage),"scenes":len(rows),"crops":len(rows)}))

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--capture-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
 a=p.parse_args();build(a.capture_root,a.output)
