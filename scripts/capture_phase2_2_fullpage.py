"""Capture selected existing pilot URLs at desktop/mobile and traverse pages.

This script records pixels and DOM facts only. It never scores a page or infers
motion, conversion outcomes, accessibility runtime, or claim truth.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
VIEWPORTS={'DESKTOP':(1440,1000),'MOBILE':(390,844)}
SCHEMA='phase2.2-capture-v1'
CONSENT_ACTIONS={'P04-R01':'必要なCookieのみ','P09-R01':'全て拒否','P10-R02':'Decline all','P16-R03':'Accept All Cookies','P19-R01':'Reject All'}

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def page_facts(page):
 return page.evaluate("""() => {
  const clean=s=>(s||'').replace(/\\s+/g,' ').trim().slice(0,1000);
  const rect=e=>{const r=e.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y+scrollY),w:Math.round(r.width),h:Math.round(r.height)}};
  const items=(sel,limit=500)=>[...document.querySelectorAll(sel)].slice(0,limit).map((e,i)=>({index:i,tag:e.tagName.toLowerCase(),text:clean(e.innerText||e.getAttribute('aria-label')),href:e.href||null,alt:e.getAttribute('alt'),src:e.currentSrc||null,rect:rect(e),font:getComputedStyle(e).fontFamily,font_size:getComputedStyle(e).fontSize})).filter(x=>x.text||x.alt||x.src);
  return {title:document.title,document_url:location.href,inner_width:innerWidth,inner_height:innerHeight,scroll_width:document.documentElement.scrollWidth,scroll_height:document.documentElement.scrollHeight,headings:items('h1,h2,h3'),sections:items('main section,main article,main [data-section],body>main>div',250),actions:items('a,button',500),images:items('main img,img',500),visible_text:clean(document.body?.innerText).slice(0,2000),has_main:!!document.querySelector('main'),video_count:document.querySelectorAll('video').length,prefers_reduced_motion:matchMedia('(prefers-reduced-motion: reduce)').matches,footer_present:!!document.querySelector('footer'),nav_count:document.querySelectorAll('nav').length};
 }""")

def scroll_to_load(page,max_steps=160):
 heights=[];y=0
 for _ in range(max_steps):
  height=page.evaluate('document.documentElement.scrollHeight')
  heights.append(height)
  step=max(500,int(page.evaluate('innerHeight')*.78))
  if y>=height:break
  y=min(height,y+step)
  page.evaluate('(y)=>window.scrollTo(0,y)',y)
  page.wait_for_timeout(130)
 page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)')
 page.wait_for_timeout(350)
 final=page.evaluate('document.documentElement.scrollHeight')
 page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(200)
 return {'scroll_samples':len(heights),'height_samples':heights,'final_height':final}

def capture(out:Path,targets_path:Path):
 out.mkdir(parents=True,exist_ok=True)
 selected=json.loads(targets_path.read_text())['reference_ids']
 rows={r['reference_id']:r for r in csv.DictReader((ROOT/'data/creative_mechanism_phase2_pilot_references.csv').open(newline='',encoding='utf-8'))}
 if len(selected)!=len(set(selected)) or not set(selected)<=set(rows):raise ValueError('Target IDs duplicate or outside approved 100-reference Pilot')
 report={'schema_version':SCHEMA,'created_at':now(),'selection':selected,'records':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True)
  try:
   for ix,rid in enumerate(selected,1):
    r=rows[rid]
    for vp,(width,height) in VIEWPORTS.items():
     context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,locale='ja-JP',reduced_motion='reduce')
     page=context.new_page();page.set_default_timeout(10000)
     rec={'reference_id':rid,'viewport_label':vp,'viewport':{'width':width,'height':height},'original_url':r['url'],'capture_state':'MISSING','captured_at':now(),'evidence_source_role':'ORIGINAL_LIVE','motion_observation':'NOT_OBSERVED_STATIC_CAPTURE','interaction_observation':'NOT_OBSERVED_NO_RUNTIME_TEST'}
     try:
      response=page.goto(r['url'],wait_until='domcontentloaded',timeout=30000)
      page.wait_for_timeout(1100)
      facts=page_facts(page)
      denied=bool(response and response.status>=400) or any(s in facts['title'].lower() for s in ('access denied','forbidden','error 403'))
      if denied or facts['inner_width']!=width or not (facts['headings'] or len(facts['visible_text'])>60):
       rec.update({'final_url':page.url,'http_status':response.status if response else None,'facts':facts,'error':'HTTP denied/error, viewport mismatch or no visible content'})
      else:
       # Consent is only changed via explicit visible text buttons; action logged.
       label=CONSENT_ACTIONS.get(rid)
       for label in ((label,) if label else ()):
        button=page.get_by_text(label,exact=True).first
        if button.count() and button.is_visible():
         try:button.click(timeout=1500);rec['consent_action']=label;page.wait_for_timeout(250);break
         except Exception:pass
       traversal=scroll_to_load(page)
       facts=page_facts(page)
       page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(150)
       viewport=out/f'{rid}__{vp.lower()}__viewport.jpg';full=out/f'{rid}__{vp.lower()}__full.jpg'
       page.screenshot(path=str(viewport),type='jpeg',quality=72,full_page=False,timeout=30000)
       page.screenshot(path=str(full),type='jpeg',quality=64,full_page=True,timeout=90000)
       rec.update({'final_url':page.url,'http_status':response.status if response else None,'facts':facts,'traversal':traversal,'capture_state':'CAPTURED','page_height':facts['scroll_height'],'horizontal_overflow_px':max(0,facts['scroll_width']-width),'screenshots':[
        {'screenshot_identifier':p.name,'content_hash':sha(p),'captured_at':rec['captured_at'],'viewport':{'width':width,'height':height},'archive_status':'TEMPORARY_CAPTURE'} for p in (viewport,full)]})
     except Exception as exc:
      rec.update({'final_url':page.url,'error':f'{type(exc).__name__}: {str(exc)[:300]}'})
     finally:
      report['records'].append(rec);context.close()
      print(f'[{ix}/{len(selected)}] {rid} {vp} {rec["capture_state"]} {rec.get("error","")[:100]}',flush=True)
  finally:browser.close()
 (out/'capture_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 n=sum(x['capture_state']=='CAPTURED' for x in report['records'])
 print(json.dumps({'captured':n,'records':len(report['records']),'selected':len(selected)}))
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--targets',type=Path,required=True)
 a=p.parse_args();capture(a.output,a.targets)
