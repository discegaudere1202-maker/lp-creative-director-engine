"""Executed browser evidence for the fixed D2C fixture. No inferred PASS on launch failure."""
from __future__ import annotations

import argparse
import functools
import importlib.metadata
import json
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .visual_diff import compare, sha

WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
HEIGHTS = {390: 844, 1440: 900}


def line_break_risks(headings):
    """Classify every rendered heading line, including intermediate orphan lines."""
    risks=[]
    for heading in headings:
        lines=heading['lines']
        for index,line in enumerate(lines):
            if re.fullmatch(r'[\u3040-\u30ff\u3400-\u9fff]{1,2}[、。]?',line.strip()):
                risks.append({'scene':heading['scene'],'tag':heading['tag'],
                              'line_index':index,'line':line,'lines':lines,'reason':'SHORT_ISOLATED_LINE'})
        for chunk in heading.get('split_chunks',[]):
            risks.append({'scene':heading['scene'],'tag':heading['tag'],
                          'chunk':chunk,'lines':lines,'reason':'SEMANTIC_CHUNK_SPLIT'})
    return risks


def server(directory: Path):
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(directory)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f'http://127.0.0.1:{httpd.server_port}'


def measure(page):
    return page.evaluate(r"""() => {
      const d=document.documentElement, W=innerWidth;
      const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
      const hidden=e=>{for(let n=e;n&&n.nodeType===1;n=n.parentElement){const c=getComputedStyle(n);if(n.hidden||c.display==='none'||c.visibility==='hidden'||c.visibility==='collapse')return true}return false};
      const concealed=e=>hidden(e)||!!(e.closest('.faq-a')&&e.closest('.faq-item:not(.open)'))||!!(e.matches('.skip-link')&&!e.matches(':focus'));
      const croppedMedia=e=>e.tagName==='IMG'&&!![...document.querySelectorAll('.hero-media,.concept-media,.product-media,.story-media')].find(p=>p.contains(e)&&['hidden','clip'].includes(getComputedStyle(p).overflowX)&&p.getBoundingClientRect().left>=-1&&p.getBoundingClientRect().right<=W+1);
      const fullyClipped=e=>{
        const r=e.getBoundingClientRect();let left=r.left,right=r.right,top=r.top,bottom=r.bottom;
        for(let n=e.parentElement;n;n=n.parentElement){const c=getComputedStyle(n);
          if(/hidden|clip|scroll|auto/.test(c.overflowX)){const p=n.getBoundingClientRect();left=Math.max(left,p.left);right=Math.min(right,p.right)}
          if(/hidden|clip|scroll|auto/.test(c.overflowY)){const p=n.getBoundingClientRect();top=Math.max(top,p.top);bottom=Math.min(bottom,p.bottom)}
          if(left>=right||top>=bottom)return true;
        }
        return false;
      };
      const scenes=[...document.querySelectorAll('section.section')].map(e=>({id:e.id,box:rect(e),boundaryCount:e.querySelectorAll('.boundary-in').length}));
      const overflow=[...document.body.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect();return !hidden(e)&&!croppedMedia(e)&&r.width>0&&(r.right>W+1||r.left< -1)&&!e.closest('.hero-ghost')}).slice(0,30).map(e=>({tag:e.tagName,cls:e.className?.baseVal||e.className,id:e.id,box:rect(e)}));
      const textNodes=[...document.querySelectorAll('h1,h2,h3,p,a:not(.cta-solid),button,.cta-solid span')];
      const intentionalHidden=textNodes.filter(concealed).map(e=>({text:e.textContent.trim().slice(0,80),tag:e.tagName}));
      const textClips=textNodes.filter(e=>!concealed(e)).filter(e=>{const r=e.getBoundingClientRect();return e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2||r.width<1||fullyClipped(e)}).slice(0,30).map(e=>({text:e.textContent.trim().slice(0,80),box:rect(e)}));
      const headings=[...document.querySelectorAll('h1,h2,h3')].filter(e=>!concealed(e)).map(e=>{
        const lines=new Map(),walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),range=document.createRange();let n;
        while(n=walk.nextNode())for(let i=0;i<n.length;i++){
          const ch=n.textContent[i];if(/\s/.test(ch))continue;
          range.setStart(n,i);range.setEnd(n,i+1);const r=range.getBoundingClientRect();if(r.width<.1||r.height<.1)continue;
          const key=Math.round(r.top/2)*2;lines.set(key,(lines.get(key)||'')+ch);
        }
        const visual=[...lines.entries()].sort((a,b)=>a[0]-b[0]).map(x=>x[1]);
        const split_chunks=[...e.querySelectorAll('.headline-chunk')].filter(chunk=>{
          const r=document.createRange();r.selectNodeContents(chunk);return r.getClientRects().length>1;
        }).map(chunk=>chunk.textContent);
        return {scene:e.closest('section')?.id,tag:e.tagName,lines:visual,split_chunks};
      });
      const images=[...document.images].map(e=>({src:e.getAttribute('src'),complete:e.complete,naturalWidth:e.naturalWidth,naturalHeight:e.naturalHeight,box:rect(e)}));
      const links=[...document.querySelectorAll('a[href]')].filter(e=>e.hash&&e.origin===location.origin&&!document.getElementById(decodeURIComponent(e.hash.slice(1)))).map(e=>e.getAttribute('href'));
      const overlaps=scenes.slice(1).filter((s,i)=>scenes[i].box.bottom > s.box.y+2).map(s=>s.id);
      const boundaryOwners=scenes.filter(s=>s.boundaryCount>1).map(s=>s.id);
      return {width:W,scrollWidth:d.scrollWidth,bodyWidth:document.body.scrollWidth,scenes,overlaps,boundaryOwners,overflow,textClips,intentionalHidden,headings,images,brokenAnchors:links,faqButtons:[...document.querySelectorAll('.faq-q')].length,
        fontStatus:document.fonts.status,animation:getComputedStyle(document.querySelector('.hero-media img')).animationName};
    }""")


def settled(page):
    page.evaluate("""async () => {await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));}""")
    for scene in page.locator('section.section').all():
        scene.scroll_into_view_if_needed(timeout=10000)
    page.evaluate('scrollTo(0,0)')
    page.wait_for_timeout(150)


def first_visible_interactive(page, selector):
    """A hidden mobile header link must not shadow the visible Hero CTA."""
    for item in page.locator(selector).all():
        if item.is_visible() and item.is_enabled():
            return item
    return None


def capture(browser, url, width, height, output, *, reduced=True, scenes=False):
    context=browser.new_context(viewport={'width':width,'height':height}, device_scale_factor=1,
                                reduced_motion='reduce' if reduced else 'no-preference')
    try:
        page=context.new_page(); errors=[]; failed=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.on('console',lambda msg: errors.append('console: '+msg.text) if msg.type=='error' else None)
        page.on('response',lambda response: failed.append(f'{response.status} {response.url}') if response.status>=400 else None)
        page.goto(url,wait_until='networkidle',timeout=30000);settled(page)
        output.mkdir(parents=True,exist_ok=True)
        capture_style='.skip-link:not(:focus){visibility:hidden!important}'
        page.screenshot(path=str(output/'full.png'),full_page=True,animations='disabled',style=capture_style)
        metrics=measure(page)
        metrics['lineBreakRisks']=line_break_risks(metrics['headings'])
        metrics.update({'console_errors':errors,'http_errors':failed,'screenshot_sha256':sha(output/'full.png')})
        faq=page.locator('.faq-q').first
        if faq.count():
            faq.focus();page.keyboard.press('Enter')
            metrics['faq_keyboard_expands']=faq.get_attribute('aria-expanded')=='true'
        else:metrics['faq_keyboard_expands']=None
        first_internal=first_visible_interactive(page,'a[href="#concept"]')
        if first_internal is not None:
            first_internal.click();metrics['navigation_reached_target']=page.evaluate('location.hash')=='#concept'
        else:metrics['navigation_reached_target']=None
        if scenes:
            scene_dir=output/'scenes';scene_dir.mkdir(exist_ok=True)
            for s in page.locator('section.section').all():
                s.screenshot(path=str(scene_dir/(s.get_attribute('id')+'.png')),animations='disabled',style=capture_style)
        return metrics
    finally:context.close()


def is_environment_block(exc):
    message=str(exc)
    return any(code in message for code in ('ERR_BLOCKED_BY_ADMINISTRATOR','ERR_BLOCKED_BY_CLIENT','ERR_ACCESS_DENIED'))


def run(dist: Path, reference: Path | None, out: Path, browser_executable: Path | None = None):
    from playwright.sync_api import sync_playwright
    dist,out=Path(dist).resolve(),Path(out).resolve()
    reference=Path(reference).resolve() if reference is not None and Path(reference).is_file() else None
    browser_executable=Path(browser_executable).resolve() if browser_executable else None
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((dist/'production_manifest.json').read_text())
    input_hashes={'html_sha256':sha(dist/'index.html'),'reference_sha256':sha(reference) if reference else None,
                  'asset_sha256':{str(p.relative_to(dist)):sha(p) for p in sorted((dist/'assets').rglob('*')) if p.is_file()}}
    report={'fixture_status':manifest['fixture_status'],'reference_status':'UNAPPROVED_SCENE_SPEC_V1_EXPERIMENT' if reference else 'NO_APPROVED_TARGET',
            'inputs':input_hashes,'viewport_contract':{'widths':WIDTHS,'heights':HEIGHTS,'dpr':1},
            'browser_gate':'HOLD','visual_diff':'HOLD_NO_APPROVED_TARGET',
            'human_visible_quality':'PENDING_SHUN_REVIEW','width_results':{},'comparisons':{},'blockers':[]}
    actual_server,actual_url=server(dist)
    ref_server,ref_url=server(reference.parent) if reference else (None,None)
    try:
        with sync_playwright() as p:
            try: browser=p.chromium.launch(headless=True,**({'executable_path':str(browser_executable)} if browser_executable else {}))
            except Exception as exc:
                report['blockers'].append({'code':'BROWSER_LAUNCH_FAILED','detail':str(exc)[:1200]})
                return report
            report['environment']={'browser':'chromium','browser_version':browser.version,
                                   'playwright_version':importlib.metadata.version('playwright'),
                                   'executable_path':str(browser_executable or p.chromium.executable_path)}
            # One authorized page-read preflight. An administrator block stops all widths immediately.
            preflight=browser.new_page(viewport={'width':390,'height':844})
            try:
                preflight.goto(actual_url+'/index.html',wait_until='domcontentloaded',timeout=15000)
                if preflight.locator('section.section').count()!=len(manifest['scenes']):
                    raise RuntimeError('PREFLIGHT_SCENE_COUNT_MISMATCH')
                report['environment']['page_load']='PASS'
            except Exception as exc:
                report['blockers'].append({'code':'PAGE_LOAD_RESTRICTED' if is_environment_block(exc) else 'PAGE_PREFLIGHT_FAILED','detail':str(exc)[:1200]})
                report['environment']['page_load']='FAIL'
                preflight.close();browser.close()
                return report
            preflight.close()
            for width in WIDTHS:
                height=HEIGHTS.get(width,900)
                dest=out/'screenshots'/'actual'/str(width)
                result={'viewport':{'width':width,'height':height,'dpr':1},'status':'NOT_RUN','findings':[]}
                try:
                    actual=capture(browser,actual_url+'/index.html',width,height,dest,scenes=width in HEIGHTS)
                except Exception as exc:
                    result.update({'status':'FAIL','findings':['CAPTURE_FAILED'],'error':str(exc)[:1200]})
                    report['width_results'][str(width)]=result
                    if is_environment_block(exc):
                        report['blockers'].append({'code':'PAGE_LOAD_RESTRICTED','width':width,'detail':str(exc)[:1200]})
                        break
                    continue
                result['status']='MEASURED'
                result['actual']=actual
                if actual['scrollWidth']>width+1 or actual['overflow']:result['findings'].append('HORIZONTAL_OVERFLOW')
                if actual['textClips']:result['findings'].append('TEXT_CLIPPING')
                if actual['lineBreakRisks']:result['findings'].append('LINE_BREAK_VIOLATION')
                if actual['console_errors'] or actual['http_errors']:result['findings'].append('BROWSER_ERROR')
                if actual['brokenAnchors']:result['findings'].append('BROKEN_ANCHOR')
                if actual['overlaps']:result['findings'].append('SECTION_OVERLAP')
                if actual['boundaryOwners']:result['findings'].append('BOUNDARY_MULTIPLE_OWNERS')
                if actual['faq_keyboard_expands'] is False:result['findings'].append('FAQ_KEYBOARD')
                if actual['navigation_reached_target'] is False:result['findings'].append('NAVIGATION')
                if actual['navigation_reached_target'] is None:result['findings'].append('VISIBLE_NAVIGATION_TARGET_MISSING')
                if any(i['naturalWidth']==0 for i in actual['images']):result['findings'].append('MISSING_IMAGE')
                if len(actual['scenes'])!=len(manifest['scenes']):result['findings'].append('SCENE_COUNT')
                if reference and width in HEIGHTS:
                    try:
                        expected=capture(browser,ref_url+'/'+reference.name,width,height,out/'screenshots'/'expected'/str(width),scenes=True)
                        result['expected_experiment']=expected
                        report['comparisons'][str(width)]=compare(out/'screenshots'/'expected'/str(width)/'full.png',dest/'full.png',out/'diffs'/str(width),viewport=result['viewport'],target_status='UNAPPROVED_SCENE_SPEC_V1_EXPERIMENT')
                    except Exception as exc:
                        report['comparisons'][str(width)]={'status':'REFERENCE_CAPTURE_FAILED','detail':str(exc)[:1200]}
                report['width_results'][str(width)]=result
            if report['width_results'].get('390',{}).get('status')=='MEASURED' and not report['blockers']:
                try:
                    normal=capture(browser,actual_url+'/index.html',390,844,out/'screenshots'/'motion-normal',reduced=False)
                    reduced=report['width_results']['390']['actual']
                    report['motion']={'normal_animation':normal['animation'],'reduced_animation':reduced['animation'],
                                      'reduced_motion_respected':reduced['animation']=='none',
                                      'normal_errors':normal['console_errors']}
                    if not report['motion']['reduced_motion_respected']:
                        report['width_results']['390']['findings'].append('REDUCED_MOTION')
                except Exception as exc:
                    report['motion']={'status':'FAIL','detail':str(exc)[:1200]}
                    report['width_results']['390']['findings'].append('MOTION_CAPTURE_FAILED')
            if not report['blockers'] and len(report['width_results'])==len(WIDTHS):
                report['browser_gate']='FAIL' if any(v['findings'] for v in report['width_results'].values()) else 'PASS'
            browser.close()
    finally:
        actual_server.shutdown();actual_server.server_close()
        if ref_server:ref_server.shutdown();ref_server.server_close()
        (out/'browser_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        qa_path=dist/'qa_report.json'
        qa=json.loads(qa_path.read_text());qa['browser_gate']=report['browser_gate'];qa['visual_diff']=report['visual_diff'];qa['human_visible_quality']='PENDING_SHUN_REVIEW';qa['browser_evidence']=str(out/'browser_qa.json')
        qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2))
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--dist',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--browser-executable',type=Path)
    a=p.parse_args(); r=run(a.dist,a.reference,a.out,a.browser_executable)
    print(json.dumps({'browser_gate':r['browser_gate'],'visual_diff':r['visual_diff'],'blockers':r['blockers']},ensure_ascii=False))


if __name__=='__main__':main()
