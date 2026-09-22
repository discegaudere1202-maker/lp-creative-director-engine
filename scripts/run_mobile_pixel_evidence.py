"""Reproducible, non-evaluative mobile benchmark capture and DOM evidence.

This research-only tool records public pages; it does not copy source/assets or
assign design quality. It is intentionally outside the production engine.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "mobile_pixel_evidence_round3fm2e"
VIEWPORTS = ((390, 844), (375, 812), (320, 720))
DESKTOP = (1440, 960)
SCENES = (("hero", 0.0), ("early", 0.12), ("material", 0.30), ("middle", 0.52), ("late", 0.76), ("final_cta", 0.92), ("ending", 1.0))

# Public first-party pages; related pages of one brand remain separate, explicit cases.
CASES = [
    {"case_id": "sanu_2nd_home", "url": "https://www.sa-nu.com/", "brand": "SANU", "desktop_reference": True, "motion_candidate": True},
    {"case_id": "sanu_stay_booking", "url": "https://stay.sa-nu.com/", "brand": "SANU", "desktop_reference": False, "motion_candidate": True},
    {"case_id": "yoom_main_lp", "url": "https://lp.yoom.fun/", "brand": "Yoom", "desktop_reference": True, "motion_candidate": True},
    {"case_id": "yoom_flowbot", "url": "https://lp.yoom.fun/features/flowbot", "brand": "Yoom", "desktop_reference": False, "motion_candidate": True},
    {"case_id": "findy_corporate", "url": "https://findy.co.jp/", "brand": "Findy", "desktop_reference": True, "motion_candidate": True},
    {"case_id": "findy_recruit", "url": "https://recruit.findy.co.jp/", "brand": "Findy", "desktop_reference": False, "motion_candidate": True},
    {"case_id": "ai_model_brand", "url": "https://www.ai-model.jp/", "brand": "AI model", "desktop_reference": True, "motion_candidate": True},
    {"case_id": "ai_model_careers", "url": "https://www.ai-model.jp/careers/", "brand": "AI model", "desktop_reference": False, "motion_candidate": False},
    {"case_id": "timee_corporate", "url": "https://corp.timee.co.jp/", "brand": "Timee", "desktop_reference": True, "motion_candidate": True},
    {"case_id": "timee_recruit_special", "url": "https://corp.timee.co.jp/special-recruit/", "brand": "Timee", "desktop_reference": False, "motion_candidate": True},
    {"case_id": "kaiho_bank", "url": "https://www.kaiho-bank.co.jp/", "brand": "Okinawa Kaiho Bank", "desktop_reference": True, "motion_candidate": False},
]

DOM_EVIDENCE = r"""() => {
 const rect = e => { const r=e.getBoundingClientRect(); return {x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height),top:Math.round(r.top),bottom:Math.round(r.bottom)} };
 const visible = e => {const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
 const textOf = e => (e.innerText||e.textContent||'').replace(/\s+/g,' ').trim();
 const headings=[...document.querySelectorAll('h1,h2,h3,[role=heading]')].filter(visible).slice(0,160).map(e=>{
   const range=document.createRange();range.selectNodeContents(e);const rects=[...range.getClientRects()];
   return {tag:e.tagName,text:textOf(e).slice(0,240),box:rect(e),line_count:rects.length,explicit_br:e.querySelectorAll('br').length,lines:[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).filter(Boolean)};
 });
 const ctas=[...document.querySelectorAll('a,button,[role=button]')].filter(visible).map(e=>({text:textOf(e).slice(0,160),href:e.href||null,box:rect(e),position:getComputedStyle(e).position,display:getComputedStyle(e).display})).filter(x=>/相談|予約|申込|申し込|資料|問い合わせ|お問い合わせ|contact|book|reserve|entry|応募|無料|始める|登録|ログイン|口座|商品|サービス/i.test(x.text+' '+(x.href||''))).slice(0,120);
 const sampled=[...document.querySelectorAll('body *')].slice(0,1800);
 const sticky=sampled.filter(visible).filter(e=>['fixed','sticky'].includes(getComputedStyle(e).position)).slice(0,80).map(e=>({tag:e.tagName,text:textOf(e).slice(0,100),box:rect(e),position:getComputedStyle(e).position,z_index:getComputedStyle(e).zIndex}));
 const sections=[...document.querySelectorAll('main section,main article,body>section,body>main>div,section')].filter(visible).slice(0,100).map((e,i)=>{const s=getComputedStyle(e),imgs=[...e.querySelectorAll('img,video,picture source')].slice(0,12).map(m=>({tag:m.tagName,src:m.currentSrc||m.src||m.getAttribute('src')||m.getAttribute('srcset'),box:rect(m),object_fit:getComputedStyle(m).objectFit,object_position:getComputedStyle(m).objectPosition}));return {index:i,tag:e.tagName,id:e.id||null,class_name:String(e.className||'').slice(0,180),box:rect(e),background_color:s.backgroundColor,background_image:s.backgroundImage,background_position:s.backgroundPosition,background_size:s.backgroundSize,background_blend_mode:s.backgroundBlendMode,opacity:s.opacity,filter:s.filter,images:imgs,video_count:e.querySelectorAll('video').length,overlay_candidates:[...e.querySelectorAll('*')].filter(x=>{const c=getComputedStyle(x);return c.position==='absolute'&&(/gradient/i.test(c.backgroundImage)||Number(c.opacity)<1)}).length};});
 const videos=[...document.querySelectorAll('video')].map(v=>({src:v.currentSrc||v.src,poster:v.poster,autoplay:v.autoplay,muted:v.muted,loop:v.loop,box:rect(v)}));
 const animations=sampled.filter(visible).map(e=>{const s=getComputedStyle(e);return {tag:e.tagName,cls:String(e.className||'').slice(0,90),animation:s.animationName,duration:s.animationDuration,transition:s.transitionDuration,transform:s.transform,position:s.position,box:rect(e)}}).filter(x=>x.animation!=='none'||(x.duration!=='0s'&&x.duration!=='0.0s')).slice(0,80);
 return {url:location.href,title:document.title,document:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,viewport_width:innerWidth,viewport_height:innerHeight,overflow_px:Math.max(0,document.documentElement.scrollWidth-innerWidth)},hero_dom:{text:textOf(document.querySelector('header')||document.body).slice(0,1200),headings:headings.slice(0,5)},headings,cta_data:ctas,sticky_fixed_data:sticky,background_data:sections,media_data:videos,animation_css_data:animations};
}"""


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", value.casefold()).strip("_")


async def page_snapshot(page: Any) -> dict[str, Any]:
    return await page.evaluate(DOM_EVIDENCE)


async def capture_viewport(browser: Any, case: dict[str, Any], width: int, height: int, case_dir: Path) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    failed_requests: list[dict[str, str]] = []
    context = await browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1, is_mobile=width < 600, has_touch=width < 600, reduced_motion="reduce")
    page = await context.new_page()
    page.on("pageerror", lambda error: errors.append({"type": "pageerror", "message": str(error)[:500]}))
    page.on("console", lambda message: errors.append({"type": "console_error", "message": message.text[:500]}) if message.type == "error" else None)
    page.on("requestfailed", lambda request: failed_requests.append({"url": request.url[:600], "failure": str(request.failure)[:300]}))
    started = time.monotonic()
    load_state = "NO"
    notes: list[str] = []
    try:
        response = await page.goto(case["url"], wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(1800)
        load_state = "YES" if response and response.ok else "NO"
        if not response:
            notes.append("navigation returned no main-document response")
        elif not response.ok:
            notes.append(f"main document HTTP {response.status}")
        try:
            await page.wait_for_function("!document.fonts || document.fonts.status === 'loaded'", timeout=3500)
        except Exception:
            notes.append("font readiness exceeded 3.5s; capture retained with live fallback state")
        max_scroll = await page.evaluate("Math.max(0,document.documentElement.scrollHeight-innerHeight)")
        scene_records = []
        scene_names = ("hero", "early", "material", "middle", "late", "final_cta", "ending") if width == 390 else ("hero", "late", "final_cta", "ending") if width == 375 else ("hero", "ending")
        for scene_name, fraction in SCENES:
            if scene_name not in scene_names:
                continue
            y = round(max_scroll * fraction)
            await page.evaluate("y => window.scrollTo(0,y)", y)
            await page.wait_for_timeout(350)
            filename = f"mobile_{width}_{scene_name}.png"
            await page.screenshot(path=str(case_dir / filename), full_page=False, animations="disabled", timeout=30000)
            snapshot = await page_snapshot(page)
            scene_records.append({"scene": scene_name, "scroll_y": y, "screenshot": filename, "headings_in_dom_order": snapshot["headings"][:25], "cta_data": snapshot["cta_data"], "sticky_fixed_data": snapshot["sticky_fixed_data"], "background_data": snapshot["background_data"][:30], "media_data": snapshot["media_data"], "document": snapshot["document"]})
        await page.evaluate("window.scrollTo(0,0)")
        await page.wait_for_timeout(200)
        if width == 390:
            await page.screenshot(path=str(case_dir / f"mobile_{width}_full.png"), full_page=True, animations="disabled", timeout=30000)
        first = await page_snapshot(page)
        return {"viewport":{"width":width,"height":height},"page_loaded":load_state,"http_status":response.status if response else None,"duration_seconds":round(time.monotonic()-started,2),"screenshots":[x["screenshot"] for x in scene_records]+([f"mobile_{width}_full.png"] if width==390 else []),"hero_dom":first["hero_dom"],"headline_break_data":[{"text":h["text"],"explicit_br":h["explicit_br"],"line_count":h["line_count"],"box":h["box"]} for h in first["headings"] if h["tag"]=="H1"],"document":first["document"],"cta_data":first["cta_data"],"sticky_fixed_data":first["sticky_fixed_data"],"background_data":first["background_data"],"media_data":first["media_data"],"animation_css_data":first["animation_css_data"],"scene_captures":scene_records,"runtime_errors":errors,"failed_requests":failed_requests,"runtime_notes":notes,"capture_limitations":[]}
    except Exception as exc:  # per-case timeout/block must not destroy the complete batch
        notes.append(f"capture exception: {type(exc).__name__}: {str(exc)[:500]}")
        return {"viewport":{"width":width,"height":height},"page_loaded":load_state,"duration_seconds":round(time.monotonic()-started,2),"screenshots":[],"runtime_errors":errors,"failed_requests":failed_requests,"runtime_notes":notes,"capture_limitations":["No complete browser evidence for this viewport; no visual inference substituted."]}
    finally:
        await context.close()


async def capture_desktop(browser: Any, case: dict[str, Any], case_dir: Path) -> dict[str, Any]:
    context = await browser.new_context(viewport={"width":DESKTOP[0],"height":DESKTOP[1]},device_scale_factor=1)
    page = await context.new_page()
    try:
        response=await page.goto(case["url"],wait_until="domcontentloaded",timeout=45000)
        await page.wait_for_timeout(1800)
        result=await page_snapshot(page)
        names=[]
        for name,fraction in (("hero",0.0),("middle",0.52),("ending",1.0)):
            y=await page.evaluate("f => Math.round(Math.max(0,document.documentElement.scrollHeight-innerHeight)*f)",fraction)
            await page.evaluate("y=>window.scrollTo(0,y)",y);await page.wait_for_timeout(250)
            filename=f"desktop_1440_{name}.png";await page.screenshot(path=str(case_dir/filename),full_page=False,animations="disabled",timeout=30000);names.append(filename)
        return {"viewport":{"width":DESKTOP[0],"height":DESKTOP[1]},"page_loaded":"YES" if response and response.ok else "NO","http_status":response.status if response else None,"screenshots":names,"hero_dom":result["hero_dom"],"headline_break_data":[{"text":h["text"],"explicit_br":h["explicit_br"],"line_count":h["line_count"],"box":h["box"]} for h in result["headings"] if h["tag"]=="H1"],"document":result["document"],"background_data":result["background_data"],"media_data":result["media_data"],"cta_data":result["cta_data"],"sticky_fixed_data":result["sticky_fixed_data"],"animation_css_data":result["animation_css_data"]}
    except Exception as exc:
        return {"viewport":{"width":DESKTOP[0],"height":DESKTOP[1]},"page_loaded":"NO","screenshots":[],"runtime_notes":[f"capture exception: {type(exc).__name__}: {str(exc)[:500]}"],"capture_limitations":["No desktop comparison was captured."]}
    finally:
        await context.close()


def classify_mobile_motion(mobile: dict[str, Any], desktop: dict[str, Any] | None) -> dict[str, Any]:
    mobile_has = bool(mobile.get("media_data") or mobile.get("animation_css_data"))
    if not mobile_has:
        status = "UNKNOWN" if not mobile.get("page_loaded") == "YES" else "REMOVED"
    elif mobile.get("media_data"):
        status = "PRESENT"
    else:
        status = "PRESENT" if mobile.get("animation_css_data") else "UNKNOWN"
    comparison = "not_compared"
    if desktop:
        dm = bool(desktop.get("media_data") or desktop.get("animation_css_data"))
        mm = bool(mobile.get("media_data") or mobile.get("animation_css_data"))
        comparison = "SIMPLIFIED_OR_REMOVED_ON_MOBILE" if dm and not mm else "PRESENT_BOTH" if dm and mm else "NO_DESKTOP_MOTION_SIGNAL"
    return {"status":status,"desktop_comparison":comparison,"observed_triggers":["scroll scene samples"],"evidence_only":True,"limitations":["Computed CSS and media inventory cannot prove which animation visibly plays; no creative interpretation made."]}


async def main_async() -> int:
    if "--manifest-only" in sys.argv:
        if not OUT.is_dir():
            raise SystemExit(f"evidence directory not found: {OUT}")
        files = []
        for path in sorted(OUT.rglob("*")):
            if path.is_file() and path.name != "artifact_manifest.json":
                files.append({"path":path.relative_to(OUT).as_posix(),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        write_json(OUT/"artifact_manifest.json",{"schema_version":"mobile_pixel_evidence_files_v1","generated_at":datetime.now(timezone.utc).isoformat(),"files":files})
        print(f"manifest refreshed: {len(files)} files")
        return 0
    from playwright.async_api import async_playwright
    OUT.mkdir(parents=True,exist_ok=True)
    generated=datetime.now(timezone.utc).isoformat()
    case_results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        capture_environment={"python":platform.python_version(),"playwright_python":importlib.metadata.version("playwright"),"chromium":browser.version,"os":platform.platform()}
        for case in CASES:
            case_dir=OUT/case["case_id"];case_dir.mkdir(parents=True,exist_ok=True)
            result={**case,"capture_timestamp":generated,"viewports":{},"desktop_reference":None,"source_host":urlparse(case["url"]).netloc}
            for width,height in VIEWPORTS:
                result["viewports"][str(width)]=await capture_viewport(browser,case,width,height,case_dir)
            if case["desktop_reference"]:
                result["desktop_reference"]=await capture_desktop(browser,case,case_dir)
            mobile_390=result["viewports"].get("390",{})
            result["motion_data"]=classify_mobile_motion(mobile_390,result["desktop_reference"])
            result["late_page_data"]={"late_captures":[entry for v in result["viewports"].values() for entry in v.get("scene_captures",[]) if entry["scene"] in ("late","final_cta","ending")],"observed_page_height_390":mobile_390.get("document",{}).get("height")}
            result["capture_limitations"]=["Viewport capture is a current live-site snapshot; content and consent state may vary.","No source code or page assets are redistributed; screenshots and measured DOM facts only."]
            write_json(case_dir/"case_evidence.json",result)
            case_results.append(result)
            print(f"{case['case_id']}: {sum(v.get('page_loaded')=='YES' for v in result['viewports'].values())}/3 mobile widths loaded",flush=True)
        await browser.close()
    unavailable=[{"case_id":c["case_id"],"url":c["url"],"unavailable_viewports":[int(width) for width,data in c["viewports"].items() if data.get("page_loaded")!="YES"],"notes":[note for data in c["viewports"].values() for note in data.get("runtime_notes",[])]} for c in case_results if any(data.get("page_loaded")!="YES" for data in c["viewports"].values())]
    manifest={"schema_version":"mobile_pixel_evidence_manifest_v1","research_round":"Round 3F-M2E","generated_at":generated,"tool":"Playwright Chromium","capture_environment":capture_environment,"viewport_targets":[{"width":w,"height":h} for w,h in VIEWPORTS],"case_count":len(case_results),"cases":[{"case_id":c["case_id"],"source_url":c["url"],"screenshot_count":sum(len(v.get("screenshots",[])) for v in c["viewports"].values())+len((c.get("desktop_reference") or {}).get("screenshots",[])),"evidence_json":f"{c['case_id']}/case_evidence.json"} for c in case_results]}
    write_json(OUT/"capture_manifest.json",manifest)
    write_json(OUT/"unavailable_cases.json",unavailable)
    limitations={"items":["Live pages may change after capture.","Cookie/consent overlays are recorded when visible; no consent choices are submitted.","Canvas, cross-origin embedded content, lazy media, and hover-only states may not be fully measurable.","Computed animation inventory does not establish perceived motion; motion status remains an evidence proxy.","No aesthetic or Re-Art-Direction decisions are made by this tool.","The supplied initial priority list does not uniquely identify which Findy product, and 'AI model' is interpreted as ai-model.jp; those identity assumptions are recorded in each case URL."]}
    write_json(OUT/"capture_limitations.json",limitations)
    summary={"schema_version":"mobile_pixel_evidence_summary_v1","attempted_cases":len(case_results),"successfully_captured_cases":sum(all(v.get("page_loaded")=="YES" for v in c["viewports"].values()) for c in case_results),"390px_count":sum(c["viewports"]["390"].get("page_loaded")=="YES" for c in case_results),"375px_count":sum(c["viewports"]["375"].get("page_loaded")=="YES" for c in case_results),"320px_count":sum(c["viewports"]["320"].get("page_loaded")=="YES" for c in case_results),"desktop_reference_count":sum(bool(c.get("desktop_reference") and c["desktop_reference"].get("page_loaded")=="YES") for c in case_results),"hero_capture_count":sum(any(x in v.get("screenshots",[]) for x in ("mobile_390_hero.png","mobile_375_hero.png","mobile_320_hero.png")) for c in case_results for v in c["viewports"].values()),"late_page_capture_count":sum(1 for c in case_results for v in c["viewports"].values() for x in v.get("scene_captures",[]) if x["scene"] in ("late","final_cta","ending")),"unavailable_case_count":len(unavailable),"research_decisions":"NOT_MADE","kanade_review_ready":sum(c["viewports"]["390"].get("page_loaded")=="YES" and c["viewports"]["375"].get("page_loaded")=="YES" for c in case_results)>=10}
    write_json(OUT/"viewport_summary.json",summary)
    files=[]
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name!="artifact_manifest.json":
            files.append({"path":path.relative_to(OUT).as_posix(),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(OUT/"artifact_manifest.json",{"schema_version":"mobile_pixel_evidence_files_v1","generated_at":generated,"files":files})
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary["390px_count"]>=10 and summary["375px_count"]>=10 else 1


if __name__=="__main__":
    raise SystemExit(asyncio.run(main_async()))
